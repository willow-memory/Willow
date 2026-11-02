// kernel.go: kernel.py in Go. Go 1.15 or later, the standard library only
// (checked on Go 1.15.15 from 2020, and on Go 1.24).
//
//	go build -o out/kernel .
//	out/kernel init    --box DIR --pile FOLDER --key FILE [--words FILE]
//	out/kernel bite    --box DIR "your words"
//	out/kernel propose --box DIR --file ROWS.jsonl
//	out/kernel seal    --box DIR proposal:<sha256>
//	out/kernel decline --box DIR proposal:<sha256>
//	out/kernel verify  --box DIR
//	out/kernel out     --box DIR
//	out/kernel vectors CASES.json RESULTS.json
//
// The fourth port, following Java's shape (../java/Kernel.java) line by
// line, with the scanners all three ports share. Held to ../cases.json by
// ../compare.py, byte for byte and both ways (a box written here verifies
// under kernel.py, and the reverse).
//
// The kernel's four patterns are scanners here, not Go's regexp: RE2 has no
// backreference and no lookbehind, and the vectors need both. What Python
// decides that Go decides differently is not retyped here. It is loaded from
// kernel_tables.json, which gen.py reads out of Python: which code points are
// word characters, what each lowercases to (and the final-sigma context),
// what str.strip / str.splitlines / str.isdigit count, the HTML5 entities and
// html.unescape's invalid-reference tables, NFC, and the kernel's constants.
// So this Go's Unicode version never decides a word. The tables are found at
// $KERNEL_TABLES, else kernel_tables.json in the working directory, else
// vectors/kernel_tables.json three folders above the built binary (built
// into ports/go/out/).
//
// Text is handled as code points ([]rune), as Python handles str: a length
// or a cut at the chunk cap counts characters, never bytes or UTF-16 units.
//
// On Linux and macOS the writer takes flock on the record, the lock kernel.py
// takes, so this port and kernel.py keep out of each other's way when they
// write one box (flock_unix.go). On Windows there is none.
//
// Exit codes, the kernel's: 0 a human said it, 42 not enough information to
// say a human said this was true, 2 refused.
package main

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io/ioutil"
	"math"
	"math/big"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const (
	ALIVE    = 0
	ESCALATE = 42
	REFUSED  = 2
)

// ── JSON: Python's json.loads in, the kernel's canon out ─────────────────────

// Obj is a JSON object as Python's dict holds it: keys in the order they
// came, a repeated key keeping its place and taking the last value.
type Obj struct {
	keys []string
	vals map[string]interface{}
}

func newObj() *Obj { return &Obj{vals: map[string]interface{}{}} }

func obj(kv ...interface{}) *Obj {
	o := newObj()
	for i := 0; i < len(kv); i += 2 {
		o.Set(kv[i].(string), kv[i+1])
	}
	return o
}

func (o *Obj) Set(k string, v interface{}) {
	if _, ok := o.vals[k]; !ok {
		o.keys = append(o.keys, k)
	}
	o.vals[k] = v
}

func (o *Obj) Get(k string) (interface{}, bool) {
	v, ok := o.vals[k]
	return v, ok
}

func (o *Obj) Has(k string) bool { _, ok := o.vals[k]; return ok }

func (o *Obj) Del(k string) {
	if _, ok := o.vals[k]; !ok {
		return
	}
	delete(o.vals, k)
	for i, x := range o.keys {
		if x == k {
			o.keys = append(o.keys[:i:i], o.keys[i+1:]...)
			break
		}
	}
}

func (o *Obj) Copy() *Obj {
	c := newObj()
	for _, k := range o.keys {
		c.Set(k, o.vals[k])
	}
	return c
}

func (o *Obj) Keys() []string { return append([]string(nil), o.keys...) }

type parser struct {
	s []rune
	i int
}

// loads is json.loads: whitespace " \t\n\r" around, one value, nothing after.
// Objects are *Obj, arrays []interface{}, integers *big.Int, other numbers
// float64, null nil.
func loads(text string) (v interface{}, err error) {
	defer func() {
		if r := recover(); r != nil {
			v, err = nil, fmt.Errorf("%v", r)
		}
	}()
	p := &parser{s: []rune(text)}
	p.ws()
	v = p.value()
	p.ws()
	if p.i != len(p.s) {
		panic("extra data")
	}
	return v, nil
}

func (p *parser) ws() {
	for p.i < len(p.s) && strings.ContainsRune(" \t\n\r", p.s[p.i]) {
		p.i++
	}
}

func (p *parser) at(i int) rune {
	if i < len(p.s) {
		return p.s[i]
	}
	return -1
}

func (p *parser) starts(lit string) bool {
	for k, c := range []rune(lit) {
		if p.at(p.i+k) != c {
			return false
		}
	}
	return true
}

func (p *parser) value() interface{} {
	if p.i >= len(p.s) {
		panic("expecting value")
	}
	switch p.s[p.i] {
	case '{':
		return p.object()
	case '[':
		return p.array()
	case '"':
		return p.str()
	}
	for _, lit := range []struct {
		s string
		v interface{}
	}{
		{"null", nil}, {"true", true}, {"false", false},
		{"NaN", math.NaN()}, {"Infinity", math.Inf(1)}, {"-Infinity", math.Inf(-1)},
	} {
		if p.starts(lit.s) {
			p.i += len([]rune(lit.s))
			return lit.v
		}
	}
	return p.number()
}

func isDec(c rune) bool { return c >= '0' && c <= '9' }

func isHex(c rune) bool { return isDec(c) || (c >= 'A' && c <= 'F') || (c >= 'a' && c <= 'f') }

// number is `(-?(?:0|[1-9][0-9]*))(\.[0-9]+)?([eE][-+]?[0-9]+)?`.
func (p *parser) number() interface{} {
	start := p.i
	j := p.i
	if p.at(j) == '-' {
		j++
	}
	if p.at(j) == '0' {
		j++
	} else if p.at(j) >= '1' && p.at(j) <= '9' {
		for isDec(p.at(j)) {
			j++
		}
	} else {
		panic("expecting value")
	}
	whole := j
	if p.at(j) == '.' && isDec(p.at(j+1)) {
		j++
		for isDec(p.at(j)) {
			j++
		}
	}
	if p.at(j) == 'e' || p.at(j) == 'E' {
		k := j + 1
		if p.at(k) == '+' || p.at(k) == '-' {
			k++
		}
		if isDec(p.at(k)) {
			for isDec(p.at(k)) {
				k++
			}
			j = k
		}
	}
	p.i = j
	text := string(p.s[start:j])
	if j == whole {
		n, ok := new(big.Int).SetString(text, 10)
		if !ok {
			panic("bad number")
		}
		return n
	}
	f, err := strconv.ParseFloat(text, 64)
	if err != nil && !errors.Is(err, strconv.ErrRange) {
		panic("bad number")
	}
	return f
}

func (p *parser) object() *Obj {
	p.i++
	out := newObj()
	p.ws()
	if p.at(p.i) == '}' {
		p.i++
		return out
	}
	for {
		p.ws()
		if p.at(p.i) != '"' {
			panic("expecting key")
		}
		k := p.str()
		p.ws()
		if p.at(p.i) != ':' {
			panic("expecting :")
		}
		p.i++
		p.ws()
		out.Set(k, p.value())
		p.ws()
		if p.at(p.i) == ',' {
			p.i++
			continue
		}
		if p.at(p.i) == '}' {
			p.i++
			return out
		}
		panic("expecting , or }")
	}
}

func (p *parser) array() []interface{} {
	p.i++
	out := []interface{}{}
	p.ws()
	if p.at(p.i) == ']' {
		p.i++
		return out
	}
	for {
		p.ws()
		out = append(out, p.value())
		p.ws()
		if p.at(p.i) == ',' {
			p.i++
			continue
		}
		if p.at(p.i) == ']' {
			p.i++
			return out
		}
		panic("expecting , or ]")
	}
}

func (p *parser) hex4(i int) rune {
	if i+4 > len(p.s) {
		panic("bad \\u escape")
	}
	n, err := strconv.ParseUint(string(p.s[i:i+4]), 16, 32)
	if err != nil {
		panic("bad \\u escape")
	}
	return rune(n)
}

func (p *parser) str() string {
	p.i++ // the opening quote
	var b []rune
	for {
		if p.i >= len(p.s) {
			panic("unterminated string")
		}
		c := p.s[p.i]
		p.i++
		if c == '"' {
			return string(b)
		}
		if c < 0x20 {
			panic("invalid control character")
		}
		if c != '\\' {
			b = append(b, c)
			continue
		}
		if p.i >= len(p.s) {
			panic("unterminated escape")
		}
		e := p.s[p.i]
		p.i++
		switch e {
		case '"', '\\', '/':
			b = append(b, e)
		case 'b':
			b = append(b, '\b')
		case 'f':
			b = append(b, '\f')
		case 'n':
			b = append(b, '\n')
		case 'r':
			b = append(b, '\r')
		case 't':
			b = append(b, '\t')
		case 'u':
			u := p.hex4(p.i)
			p.i += 4
			// a surrogate pair is one code point, as Python's json reads it
			if u >= 0xD800 && u <= 0xDBFF && p.at(p.i) == '\\' && p.at(p.i+1) == 'u' {
				lo := p.hex4(p.i + 2)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					u = 0x10000 + (u-0xD800)<<10 + (lo - 0xDC00)
					p.i += 6
				}
			}
			b = append(b, u)
		default:
			panic("invalid escape")
		}
	}
}

// canon is family A, json.dumps(sort_keys=True, separators=(",", ":"),
// ensure_ascii=False). No floats: the kernel's rows never hold one, and a
// port must not invent repr(float).
func canon(o interface{}) string {
	var b strings.Builder
	dump(o, &b, true, false)
	return b.String()
}

// dumpsDefault is json.dumps(o, sort_keys=sort) with Python's default
// separators and ensure_ascii=True: kernel.json and the proposal files.
func dumpsDefault(o interface{}, sortKeys bool) string {
	var b strings.Builder
	dumpSpaced(o, &b, sortKeys, true)
	return b.String()
}

// dumpsSpacedUtf8 is json.dumps(doc, ensure_ascii=False): what the person reads.
func dumpsSpacedUtf8(o interface{}) string {
	var b strings.Builder
	dumpSpaced(o, &b, false, false)
	return b.String()
}

func dump(o interface{}, b *strings.Builder, sortKeys, ascii bool) {
	switch v := o.(type) {
	case nil:
		b.WriteString("null")
	case bool:
		if v {
			b.WriteString("true")
		} else {
			b.WriteString("false")
		}
	case *big.Int:
		b.WriteString(v.String())
	case int:
		b.WriteString(strconv.Itoa(v))
	case int64:
		b.WriteString(strconv.FormatInt(v, 10))
	case string:
		quote(v, b, ascii)
	case []interface{}:
		b.WriteByte('[')
		for i, x := range v {
			if i > 0 {
				b.WriteByte(',')
			}
			dump(x, b, sortKeys, ascii)
		}
		b.WriteByte(']')
	case *Obj:
		keys := v.Keys()
		if sortKeys {
			sort.Strings(keys) // byte order of UTF-8 is code point order, as Python sorts str
		}
		b.WriteByte('{')
		for i, k := range v.keys {
			if sortKeys {
				k = keys[i]
			}
			if i > 0 {
				b.WriteByte(',')
			}
			quote(k, b, ascii)
			b.WriteByte(':')
			dump(v.vals[k], b, sortKeys, ascii)
		}
		b.WriteByte('}')
	default:
		panic(fmt.Sprintf("canon refuses %T", o))
	}
}

func dumpSpaced(o interface{}, b *strings.Builder, sortKeys, ascii bool) {
	switch v := o.(type) {
	case []interface{}:
		b.WriteByte('[')
		for i, x := range v {
			if i > 0 {
				b.WriteString(", ")
			}
			dumpSpaced(x, b, sortKeys, ascii)
		}
		b.WriteByte(']')
	case *Obj:
		keys := v.Keys()
		if sortKeys {
			sort.Strings(keys)
		}
		b.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				b.WriteString(", ")
			}
			quote(k, b, ascii)
			b.WriteString(": ")
			dumpSpaced(v.vals[k], b, sortKeys, ascii)
		}
		b.WriteByte('}')
	default:
		dump(o, b, sortKeys, ascii)
	}
}

func quote(s string, b *strings.Builder, ascii bool) {
	b.WriteByte('"')
	for _, c := range s {
		switch c {
		case '"':
			b.WriteString("\\\"")
		case '\\':
			b.WriteString("\\\\")
		case '\n':
			b.WriteString("\\n")
		case '\r':
			b.WriteString("\\r")
		case '\t':
			b.WriteString("\\t")
		case '\b':
			b.WriteString("\\b")
		case '\f':
			b.WriteString("\\f")
		default:
			if c < 0x20 || (ascii && c > 0x7e) {
				if c > 0xFFFF { // ensure_ascii writes an astral character as its surrogate pair
					u := c - 0x10000
					fmt.Fprintf(b, "\\u%04x\\u%04x", 0xD800+(u>>10), 0xDC00+(u&0x3FF))
				} else {
					fmt.Fprintf(b, "\\u%04x", c)
				}
			} else {
				b.WriteRune(c)
			}
		}
	}
	b.WriteByte('"')
}

// pyStr is str(o) for what a record row can hold.
func pyStr(o interface{}) string {
	switch v := o.(type) {
	case nil:
		return "None"
	case bool:
		if v {
			return "True"
		}
		return "False"
	case string:
		return v
	case *big.Int:
		return v.String()
	}
	return canon(o)
}

// pyRepr is repr(o), for the out-of-place break.
func pyRepr(o interface{}) string {
	if s, ok := o.(string); ok {
		return "'" + s + "'"
	}
	return pyStr(o)
}

func asInt(o interface{}) (int64, bool) {
	switch v := o.(type) {
	case *big.Int:
		if v.IsInt64() {
			return v.Int64(), true
		}
		return 0, true // an integer, only not one this machine indexes with
	case int:
		return int64(v), true
	case int64:
		return v, true
	}
	return 0, false
}

func bigOf(n int) *big.Int { return big.NewInt(int64(n)) }

// ── hashing and the seal ────────────────────────────────────────────────────

func sha256hex(data []byte) string {
	d := sha256.Sum256(data)
	return hex.EncodeToString(d[:])
}

func h256(text string) string { return sha256hex([]byte(text)) }

func hmacHex(key, msg []byte) string {
	m := hmac.New(sha256.New, key)
	m.Write(msg)
	return hex.EncodeToString(m.Sum(nil))
}

// proof is HMAC-SHA-256 under their key, over the act ("seal", or "decline"
// for a No), a unit separator, the subject; and, for a seal that names the
// question it answers, another separator and that question's key.
func proof(key []byte, subject, act string, asked *string) string {
	msg := act + "\x1f" + subject
	if asked != nil {
		msg += "\x1f" + *asked
	}
	return hmacHex(key, []byte(msg))
}

// ── the tables: Python's decisions, read out of Python ──────────────────────

type ranges struct{ lo, hi []int32 }

func newRanges(v interface{}) ranges {
	var r ranges
	for _, x := range v.([]interface{}) {
		pair := x.([]interface{})
		r.lo = append(r.lo, int32(toInt(pair[0])))
		r.hi = append(r.hi, int32(toInt(pair[1])))
	}
	return r
}

func (r ranges) has(c rune) bool {
	a, z := 0, len(r.lo)-1
	for a <= z {
		m := (a + z) / 2
		if c < rune(r.lo[m]) {
			z = m - 1
		} else if c > rune(r.hi[m]) {
			a = m + 1
		} else {
			return true
		}
	}
	return false
}

func toInt(v interface{}) int {
	n, _ := asInt(v)
	return int(n)
}

type cpPair struct{ a, b rune }

var (
	WORD, SPACE, DIGIT, CASED, IGNORABLE ranges
	LOWER                                map[rune]string
	LINE_BREAKS, INVALID_CODEPOINTS      map[rune]bool
	HTML5                                map[string]string
	INVALID_CHARREFS                     map[int64]string
	CCC                                  map[rune]int
	DECOMP                               map[rune][]rune
	COMPOSE                              map[cpPair]rune
	TAG_FOLD                             map[rune]map[rune]bool
	TAG_BACKREF                          map[rune]map[cpPair]bool
	GENESIS                              string
	TOP, SNIFF, MAX_FILE, MAX_CHUNK      int
	ECHO_RUN, HOLD_NUM, HOLD_DEN         int
	FUNCTION, MAKE, ROW_KEYS             map[string]bool
	NEXT                                 map[string]string
	VERSION                              string
)

func stringSet(v interface{}) map[string]bool {
	out := map[string]bool{}
	for _, x := range v.([]interface{}) {
		out[x.(string)] = true
	}
	return out
}

func get(o *Obj, k string) interface{} {
	v, _ := o.Get(k)
	return v
}

func loadTables(path string) error {
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		return err
	}
	doc, err := loads(string(raw))
	if err != nil {
		return err
	}
	t := doc.(*Obj)
	WORD = newRanges(get(t, "word"))
	SPACE = newRanges(get(t, "space"))
	DIGIT = newRanges(get(t, "digit"))
	sigma := get(t, "sigma").(*Obj)
	CASED = newRanges(get(sigma, "cased"))
	IGNORABLE = newRanges(get(sigma, "case_ignorable"))
	LOWER = map[rune]string{}
	for k, v := range get(t, "lower").(*Obj).vals {
		n, _ := strconv.Atoi(k)
		LOWER[rune(n)] = v.(string)
	}
	LINE_BREAKS = map[rune]bool{}
	for _, x := range get(t, "line_breaks").([]interface{}) {
		LINE_BREAKS[rune(toInt(x))] = true
	}
	HTML5 = map[string]string{}
	for k, v := range get(t, "html5").(*Obj).vals {
		HTML5[k] = v.(string)
	}
	INVALID_CHARREFS = map[int64]string{}
	for k, v := range get(t, "invalid_charrefs").(*Obj).vals {
		n, _ := strconv.ParseInt(k, 10, 64)
		INVALID_CHARREFS[n] = v.(string)
	}
	INVALID_CODEPOINTS = map[rune]bool{}
	for _, x := range get(t, "invalid_codepoints").([]interface{}) {
		INVALID_CODEPOINTS[rune(toInt(x))] = true
	}
	nfcT := get(t, "nfc").(*Obj)
	CCC = map[rune]int{}
	for k, v := range get(nfcT, "ccc").(*Obj).vals {
		n, _ := strconv.Atoi(k)
		CCC[rune(n)] = toInt(v)
	}
	DECOMP = map[rune][]rune{}
	for k, v := range get(nfcT, "decomp").(*Obj).vals {
		n, _ := strconv.Atoi(k)
		var d []rune
		for _, x := range v.([]interface{}) {
			d = append(d, rune(toInt(x)))
		}
		DECOMP[rune(n)] = d
	}
	COMPOSE = map[cpPair]rune{}
	for _, x := range get(nfcT, "compose").([]interface{}) {
		p := x.([]interface{})
		COMPOSE[cpPair{rune(toInt(p[0])), rune(toInt(p[1]))}] = rune(toInt(p[2]))
	}
	kc := get(t, "kernel").(*Obj)
	GENESIS = get(kc, "GENESIS").(string)
	TOP = toInt(get(kc, "TOP"))
	SNIFF = toInt(get(kc, "SNIFF"))
	MAX_FILE = toInt(get(kc, "MAX_FILE"))
	MAX_CHUNK = toInt(get(kc, "MAX_CHUNK"))
	ECHO_RUN = toInt(get(kc, "ECHO_RUN"))
	hold := get(kc, "HOLD").([]interface{})
	HOLD_NUM, HOLD_DEN = toInt(hold[0]), toInt(hold[1])
	FUNCTION = stringSet(get(kc, "FUNCTION"))
	MAKE = stringSet(get(kc, "MAKE"))
	ROW_KEYS = stringSet(get(kc, "ROW_KEYS"))
	NEXT = map[string]string{}
	for k, v := range get(kc, "NEXT").(*Obj).vals {
		NEXT[k] = v.(string)
	}
	TAG_FOLD = map[rune]map[rune]bool{}
	for k, v := range get(t, "tag_fold").(*Obj).vals {
		cs := map[rune]bool{}
		for _, x := range v.([]interface{}) {
			cs[rune(toInt(x))] = true
		}
		TAG_FOLD[[]rune(k)[0]] = cs
	}
	TAG_BACKREF = map[rune]map[cpPair]bool{}
	for k, v := range get(t, "tag_backref").(*Obj).vals {
		ps := map[cpPair]bool{}
		for _, x := range v.([]interface{}) {
			pr := x.([]interface{})
			ps[cpPair{rune(toInt(pr[0])), rune(toInt(pr[1]))}] = true
		}
		TAG_BACKREF[[]rune(k)[0]] = ps
	}
	return nil
}

// ── str, as Python has it ───────────────────────────────────────────────────

func cps(s string) []rune { return []rune(s) }

func length(s string) int { return utf8.RuneCountInString(s) }

// lower is str.lower: the table, and U+03A3 by CPython's final-sigma context.
func lower(s string) string {
	a := cps(s)
	var b strings.Builder
	for i, c := range a {
		if c == 0x03A3 {
			if finalSigma(a, i) {
				b.WriteString("ς")
			} else {
				b.WriteString("σ")
			}
		} else if l, ok := LOWER[c]; ok {
			b.WriteString(l)
		} else {
			b.WriteRune(c)
		}
	}
	return b.String()
}

func finalSigma(a []rune, i int) bool {
	j := i - 1
	for j >= 0 && IGNORABLE.has(a[j]) {
		j--
	}
	if j < 0 || !CASED.has(a[j]) {
		return false
	}
	j = i + 1
	for j < len(a) && IGNORABLE.has(a[j]) {
		j++
	}
	return j == len(a) || !CASED.has(a[j])
}

func ccc(c rune) int { return CCC[c] }

// nfc is unicodedata.normalize("NFC"): decompose, put marks in canonical
// order, compose, by gen.py's tables, so this Go's Unicode version never
// decides.
func nfc(a []rune) []rune {
	d := make([]rune, 0, len(a))
	for _, c := range a {
		if c >= 0xAC00 && c <= 0xD7A3 {
			s := c - 0xAC00
			d = append(d, 0x1100+s/588, 0x1161+s%588/28)
			if s%28 != 0 {
				d = append(d, 0x11A7+s%28)
			}
		} else if x, ok := DECOMP[c]; ok {
			d = append(d, x...)
		} else {
			d = append(d, c)
		}
	}
	for i := 1; i < len(d); i++ {
		for j := i; j > 0 && ccc(d[j]) != 0 && ccc(d[j-1]) > ccc(d[j]); j-- {
			d[j-1], d[j] = d[j], d[j-1]
		}
	}
	out := make([]rune, 0, len(d))
	st := -1
	for _, c := range d {
		cc := ccc(c)
		if st >= 0 {
			last := ccc(out[len(out)-1])
			if len(out)-1 == st || (last != 0 && last < cc) {
				s := out[st]
				if s >= 0x1100 && s < 0x1113 && c >= 0x1161 && c < 0x1176 {
					out[st] = 0xAC00 + ((s-0x1100)*21+c-0x1161)*28
					continue
				}
				if s >= 0xAC00 && s <= 0xD7A3 && (s-0xAC00)%28 == 0 && c >= 0x11A8 && c <= 0x11C2 {
					out[st] = s + c - 0x11A7
					continue
				}
				if p, ok := COMPOSE[cpPair{s, c}]; ok {
					out[st] = p
					continue
				}
			}
		}
		if cc == 0 {
			st = len(out)
		}
		out = append(out, c)
	}
	return out
}

// blank is str.strip() == "".
func blank(s string) bool {
	for _, c := range s {
		if !SPACE.has(c) {
			return false
		}
	}
	return true
}

// strip is str.strip().
func strip(s string) string {
	a := cps(s)
	i, j := 0, len(a)
	for i < j && SPACE.has(a[i]) {
		i++
	}
	for j > i && SPACE.has(a[j-1]) {
		j--
	}
	return string(a[i:j])
}

// splitlines is str.splitlines(): "\r\n" is one break; no terminators kept.
func splitlines(s string) []string {
	out := []string{}
	a := cps(s)
	start, i := 0, 0
	for i < len(a) {
		c := a[i]
		if LINE_BREAKS[c] {
			out = append(out, string(a[start:i]))
			if c == '\r' && i+1 < len(a) && a[i+1] == '\n' {
				i += 2
			} else {
				i++
			}
			start = i
		} else {
			i++
		}
	}
	if start < len(a) {
		out = append(out, string(a[start:]))
	}
	return out
}

func take(s string, n int) string {
	a := cps(s)
	if len(a) <= n {
		return s
	}
	return string(a[:n])
}

// ── words and the bite key ──────────────────────────────────────────────────

func words(text string) []string {
	out := []string{}
	var cur []rune
	for _, c := range nfc(cps(lower(text))) {
		if WORD.has(c) {
			cur = append(cur, c)
		} else if len(cur) > 0 {
			out = append(out, string(cur))
			cur = cur[:0]
		}
	}
	if len(cur) > 0 {
		out = append(out, string(cur))
	}
	return out
}

func biteKey(text string) *string {
	ws := words(text)
	if len(ws) == 0 {
		return nil
	}
	k := h256(strings.Join(ws, " "))
	return &k
}

func subjectOf(prop *Obj) string {
	four := newObj()
	for _, k := range []string{"path", "data", "cites", "claim"} {
		four.Set(k, get(prop, k))
	}
	return "proposal:" + h256(canon(four))
}

// ── the scanners: the kernel's regular expressions, by hand ─────────────────

// isW is Python's \w: a word character or "_".
func isW(c rune) bool { return c == '_' || WORD.has(c) }

func at(a []rune, i int) rune {
	if i < len(a) {
		return a[i]
	}
	return -1
}

// kept is " " and one newline for each the match held: line numbers still point home.
func kept(a []rune, from, to int) string {
	n := 0
	for i := from; i < to; i++ {
		if a[i] == '\n' {
			n++
		}
	}
	return " " + strings.Repeat("\n", n)
}

// hiddenAt matches `<(script|style)\b.*?</\1\s*>|<!--.*?-->` under re.S |
// re.I, at i (a "<"): the name folds as re.I folds it (tag_fold); the closing
// name equals the opening one as re.I's backreference compares (tag_backref).
func hiddenAt(a []rune, i int) int {
	for _, name := range []string{"script", "style"} {
		nm := []rune(name)
		n := len(nm)
		ok := i+1+n <= len(a)
		for k := 0; ok && k < n; k++ {
			ok = TAG_FOLD[nm[k]][a[i+1+k]]
		}
		if !ok {
			continue
		}
		e := i + 1 + n
		if e < len(a) && isW(a[e]) {
			continue // \b
		}
		for k := e; k+1 < len(a); k++ {
			if a[k] != '<' || a[k+1] != '/' {
				continue
			}
			same := k+2+n <= len(a)
			for x := 0; same && x < n; x++ {
				same = TAG_BACKREF[nm[x]][cpPair{a[i+1+x], a[k+2+x]}]
			}
			if !same {
				continue
			}
			p := k + 2 + n
			for p < len(a) && SPACE.has(a[p]) {
				p++
			}
			if p < len(a) && a[p] == '>' {
				return p + 1
			}
		}
	}
	if at(a, i+1) == '!' && at(a, i+2) == '-' && at(a, i+3) == '-' {
		for k := i + 4; k+2 < len(a); k++ {
			if a[k] == '-' && a[k+1] == '-' && a[k+2] == '>' {
				return k + 3
			}
		}
	}
	return -1
}

func hidden(text string) string {
	a := cps(text)
	var b strings.Builder
	i := 0
	for i < len(a) {
		m := -1
		if a[i] == '<' {
			m = hiddenAt(a, i)
		}
		if m >= 0 {
			b.WriteString(kept(a, i, m))
			i = m
		} else {
			b.WriteRune(a[i])
			i++
		}
	}
	return b.String()
}

// tags is `<[^>]*>`.
func tags(text string) string {
	a := cps(text)
	var b strings.Builder
	i := 0
	for i < len(a) {
		if a[i] == '<' {
			q := -1
			for k := i + 1; k < len(a); k++ {
				if a[k] == '>' {
					q = k
					break
				}
			}
			if q >= 0 {
				b.WriteString(kept(a, i, q+1))
				i = q + 1
				continue
			}
		}
		b.WriteRune(a[i])
		i++
	}
	return b.String()
}

func nameStop(c rune) bool { return strings.ContainsRune("\t\n\f <&#;", c) }

// unescape is html.unescape: `&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)`.
func unescape(s string) string {
	if !strings.ContainsRune(s, '&') {
		return s
	}
	a := cps(s)
	var b strings.Builder
	i := 0
	for i < len(a) {
		if a[i] != '&' {
			b.WriteRune(a[i])
			i++
			continue
		}
		j := i + 1
		if at(a, j) == '#' {
			if isDec(at(a, j+1)) {
				j++
				for j < len(a) && isDec(a[j]) {
					j++
				}
			} else if (at(a, j+1) == 'x' || at(a, j+1) == 'X') && isHex(at(a, j+2)) {
				j += 2
				for j < len(a) && isHex(a[j]) {
					j++
				}
			} else {
				b.WriteByte('&')
				i++
				continue
			}
		} else {
			for j < len(a) && j-(i+1) < 32 && !nameStop(a[j]) {
				j++
			}
			if j == i+1 {
				b.WriteByte('&')
				i++
				continue
			}
		}
		if at(a, j) == ';' {
			j++
		}
		b.WriteString(charref(a[i+1 : j]))
		i = j
	}
	return b.String()
}

func charref(s []rune) string {
	if s[0] == '#' {
		isX := s[1] == 'x' || s[1] == 'X'
		digits := s[1:]
		base := 10
		if isX {
			digits = s[2:]
			base = 16
		}
		for len(digits) > 0 && digits[len(digits)-1] == ';' {
			digits = digits[:len(digits)-1]
		}
		num, _ := new(big.Int).SetString(string(digits), base)
		if num.Cmp(big.NewInt(0x10FFFF)) > 0 {
			return "�"
		}
		n := num.Int64()
		if v, ok := INVALID_CHARREFS[n]; ok {
			return v
		}
		if n >= 0xD800 && n <= 0xDFFF {
			return "�"
		}
		if INVALID_CODEPOINTS[rune(n)] {
			return ""
		}
		return string(rune(n))
	}
	if v, ok := HTML5[string(s)]; ok {
		return v
	}
	for x := len(s) - 1; x > 1; x-- {
		if v, ok := HTML5[string(s[:x])]; ok {
			return v + string(s[x:])
		}
	}
	return "&" + string(s)
}

func htmlText(text string) string { return unescape(tags(hidden(text))) }

var KEYWORDS = []string{"def", "function", "sub", "class", "func", "fn"}

func identHead(c rune) bool { return c == '_' || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') }

func identTail(c rune) bool { return identHead(c) || isDec(c) }

// defines is re.findall of `\b(?:def|function|sub|class|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)`.
func defines(text string) []string {
	a := cps(text)
	out := []string{}
	p := 0
outer:
	for p < len(a) {
		if p == 0 || !isW(a[p-1]) {
			for _, kw := range KEYWORDS {
				kr := []rune(kw)
				k := 0
				for k < len(kr) && at(a, p+k) == kr[k] {
					k++
				}
				if k < len(kr) {
					continue
				}
				q := p + len(kr)
				s0 := q
				for q < len(a) && SPACE.has(a[q]) {
					q++
				}
				if q == s0 || !(q < len(a) && identHead(a[q])) {
					continue
				}
				start := q
				for q < len(a) && identTail(a[q]) {
					q++
				}
				out = append(out, string(a[start:q]))
				p = q
				continue outer
			}
		}
		p++
	}
	return out
}

// named is how many times `\bname\b` occurs (name is an identifier: \w all through).
func named(text, name string) int {
	a, b := cps(text), cps(name)
	n, p := 0, 0
	for p+len(b) <= len(a) {
		k := 0
		for k < len(b) && a[p+k] == b[k] {
			k++
		}
		if k == len(b) && (p == 0 || !isW(a[p-1])) && (p+len(b) == len(a) || !isW(a[p+len(b)])) {
			n++
			p += len(b)
		} else {
			p++
		}
	}
	return n
}

// ── word forms, holds, echo ─────────────────────────────────────────────────

// stem is kernel.py's: an English word's plain form; only words of ASCII letters.
func stem(w string) string {
	if len(w) < 3 {
		return w
	}
	for i := 0; i < len(w); i++ {
		c := w[i]
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) {
			return w
		}
	}
	s := w
	n := len(s)
	if n > 4 && (strings.HasSuffix(s, "ies") || strings.HasSuffix(s, "ied")) {
		s = s[:n-3] + "y"
	} else if n > 4 && strings.HasSuffix(s, "ing") {
		s = s[:n-3]
	} else if n > 3 && strings.HasSuffix(s, "ed") {
		s = s[:n-2]
	} else if n > 3 && strings.HasSuffix(s, "s") && !strings.HasSuffix(s, "ss") {
		s = s[:n-1]
	}
	n = len(s)
	if n > 3 && s[n-1] == s[n-2] && !strings.ContainsRune("aeiouls", rune(s[n-1])) {
		s = s[:n-1]
		n--
	}
	if n > 2 && strings.HasSuffix(s, "e") {
		s = s[:n-1]
	}
	return s
}

// forms is words, and each one's plain form.
func forms(ws []string) map[string]bool {
	out := map[string]bool{}
	for _, w := range ws {
		out[w] = true
		out[stem(w)] = true
	}
	return out
}

func holds(w string, toks map[string]bool) bool {
	if toks[w] || toks[stem(w)] {
		return true
	}
	if length(w) < 4 {
		return false
	}
	digit := false
	for _, c := range w {
		digit = digit || DIGIT.has(c)
	}
	if !digit {
		return false
	}
	for t := range toks {
		if strings.HasSuffix(t, w) || strings.HasPrefix(t, w) {
			return true
		}
	}
	return false
}

func echo(bite, text string) bool {
	ws, ts := words(bite), words(text)
	n := len(ws)
	if ECHO_RUN < n {
		n = ECHO_RUN
	}
	if n < 3 {
		return false
	}
	runs := map[string]bool{}
	for i := 0; i+n <= len(ts); i++ {
		runs[strings.Join(ts[i:i+n], " ")] = true
	}
	for i := 0; i+n <= len(ws); i++ {
		if runs[strings.Join(ws[i:i+n], " ")] {
			return true
		}
	}
	return false
}

// ── the pile ────────────────────────────────────────────────────────────────

type Chunk struct {
	path, text, id string
	line           int
}

func newChunk(path string, line int, text string) *Chunk {
	return &Chunk{path: path, line: line, text: text, id: h256(text)}
}

func (c *Chunk) json() *Obj {
	return obj("path", c.path, "line", bigOf(c.line), "text", c.text, "id", c.id)
}

// walk is Path.rglob("*"): every entry under dir, as its parts; a link to a
// folder is listed, never entered.
func walk(dir string, parts []string, out *[][]string) {
	entries, err := ioutil.ReadDir(dir)
	if err != nil {
		return
	}
	for _, e := range entries {
		mine := append(append([]string(nil), parts...), e.Name())
		*out = append(*out, mine)
		if e.IsDir() {
			walk(filepath.Join(dir, e.Name()), mine, out)
		}
	}
}

// byParts sorts as Python sorts paths: part by part, the shorter first.
func byParts(a, b []string) bool {
	for i := 0; i < len(a) && i < len(b); i++ {
		if a[i] != b[i] {
			return a[i] < b[i]
		}
	}
	return len(a) < len(b)
}

func suffix(name string) string {
	i := strings.LastIndex(name, ".")
	if i > 0 && i < len(name)-1 {
		return name[i:]
	}
	return ""
}

func chunks(pile string) []*Chunk {
	var all [][]string
	walk(pile, nil, &all)
	sort.SliceStable(all, func(i, j int) bool { return byParts(all[i], all[j]) })
	out := []*Chunk{}
	for _, rel := range all {
		p := filepath.Join(append([]string{pile}, rel...)...)
		st, err := os.Stat(p)
		if err != nil || !st.Mode().IsRegular() {
			continue
		}
		hid := false
		for _, part := range rel {
			hid = hid || strings.HasPrefix(part, ".")
		}
		if hid {
			continue
		}
		if st.Size() > int64(MAX_FILE) {
			continue
		}
		raw, err := ioutil.ReadFile(p)
		if err != nil {
			continue
		}
		head := raw
		if len(head) > SNIFF {
			head = head[:SNIFF]
		}
		if strings.IndexByte(string(head), 0) >= 0 || !utf8.Valid(raw) {
			continue
		}
		text := string(raw)
		suf := lower(suffix(rel[len(rel)-1]))
		if suf == ".html" || suf == ".htm" {
			text = htmlText(text)
		}
		relPath := strings.Join(rel, "/")
		lines := append(splitlines(text), "")
		var para []string
		start, size := 1, 0
		for i := 1; i <= len(lines); i++ {
			line := lines[i-1]
			if len(para) > 0 && (blank(line) || size+length(line) > MAX_CHUNK) {
				out = append(out, newChunk(relPath, start, strings.Join(para, "\n")))
				para, size = nil, 0
			}
			if !blank(line) {
				if len(para) == 0 {
					start = i
				}
				para = append(para, take(line, MAX_CHUNK))
				size += length(para[len(para)-1]) + 1
			}
		}
	}
	return out
}

// ── dates ───────────────────────────────────────────────────────────────────

// digits is how many ASCII digits run from i.
func digits(t []rune, i int) int {
	j := i
	for j < len(t) && t[j] >= '0' && t[j] <= '9' {
		j++
	}
	return j - i
}

func date(y, m, d string) string {
	ok := (strings.HasPrefix(y, "19") || strings.HasPrefix(y, "20")) &&
		m >= "01" && m <= "12" && d >= "01" && d <= "31"
	if ok {
		return y + m + d
	}
	return ""
}

// dayMonth is kernel.py's _day_month: a/b/y read only when it can't be misread.
func dayMonth(a, b, y string) string {
	x, _ := strconv.Atoi(a)
	z, _ := strconv.Atoi(b)
	if x == z || (x > 12 && z <= 12) {
		return date(y, fmt.Sprintf("%02d", z), fmt.Sprintf("%02d", x))
	}
	if z > 12 && x <= 12 {
		return date(y, fmt.Sprintf("%02d", x), fmt.Sprintf("%02d", z))
	}
	return ""
}

// webAddress is how many characters from i are an http(s) address, or 0.
func webAddress(t []rune, i int) int {
	for _, scheme := range []string{"http://", "https://"} {
		sr := []rune(scheme)
		ok := i+len(sr) <= len(t)
		for k := 0; ok && k < len(sr); k++ {
			ok = t[i+k] == sr[k]
		}
		if ok {
			j := i + len(sr)
			for j < len(t) && !SPACE.has(t[j]) {
				j++
			}
			return j - i
		}
	}
	return 0
}

// newest is kernel.py's: the latest date written in t, as YYYYMMDD, or "".
func newest(text string) string {
	t := cps(text)
	best := ""
	i := 0
	for i < len(t) {
		if url := webAddress(t, i); url > 0 {
			i += url
			continue
		}
		n := digits(t, i)
		if n == 0 {
			i++
			continue
		}
		got := ""
		sub := func(a, b int) string {
			if b > len(t) {
				b = len(t)
			}
			if a > b {
				return ""
			}
			return string(t[a:b])
		}
		if n == 8 {
			got = date(sub(i, i+4), sub(i+4, i+6), sub(i+6, i+8))
		} else if n == 4 && sub(i+4, i+5) == "-" && digits(t, i+5) == 2 {
			if sub(i+7, i+8) == "-" && digits(t, i+8) == 2 {
				got = date(sub(i, i+4), sub(i+5, i+7), sub(i+8, i+10))
				if got != "" {
					n = 10
				}
			}
		} else if n <= 2 && (sub(i+n, i+n+1) == "/" || sub(i+n, i+n+1) == ".") {
			sep := sub(i+n, i+n+1)
			m := digits(t, i+n+1)
			j := i + n + 1 + m
			if m >= 1 && m <= 2 && sub(j, j+1) == sep && digits(t, j+1) == 4 {
				got = dayMonth(sub(i, i+n), sub(i+n+1, j), sub(j+1, j+5))
				if got != "" {
					n = j + 5 - i
				}
			}
		}
		if got > best {
			best = got
		}
		i += n
	}
	return best
}

// dates is kernel.py's: each chunk's date, carried down its file; 0 for none.
func dates(pile []*Chunk) []int64 {
	out := make([]int64, len(pile))
	path, cur := "\x00none", ""
	for i, c := range pile {
		if c.path != path {
			path, cur = c.path, newest(c.path)
		}
		if t := newest(c.text); t > cur {
			cur = t
		}
		if cur == "" {
			out[i] = 0
		} else {
			out[i], _ = strconv.ParseInt(cur, 10, 64)
		}
	}
	return out
}

// ── rank and look ───────────────────────────────────────────────────────────

type alias map[string][]string

// aliasOf is a case's words list, as the vectors hold it ({} when it has none).
func aliasOf(m *Obj) alias {
	out := alias{}
	if a, ok := get(m, "alias").(*Obj); ok {
		for _, k := range a.keys {
			var v []string
			for _, x := range a.vals[k].([]interface{}) {
				v = append(v, x.(string))
			}
			out[k] = v
		}
	}
	return out
}

// heldBy: their word holds where it, or a word their list reads it as, does.
func heldBy(w string, toks map[string]bool, al alias) bool {
	if holds(w, toks) {
		return true
	}
	for _, x := range al[w] {
		if holds(x, toks) {
			return true
		}
	}
	return false
}

func toks(c *Chunk) map[string]bool {
	return forms(append(words(c.text), words(c.path)...))
}

// uniqueWords is dict.fromkeys(words) less FUNCTION: each content word once, in order.
func uniqueWords(ws []string) []string {
	seen := map[string]bool{}
	var want []string
	for _, w := range ws {
		if !seen[w] && !FUNCTION[w] {
			want = append(want, w)
		}
		seen[w] = true
	}
	return want
}

type scored struct {
	score *big.Rat
	c     *Chunk
	d     int64
}

func rank(pile []*Chunk, bite string, al alias) []*Chunk {
	want := uniqueWords(words(bite))
	if len(want) == 0 {
		return []*Chunk{}
	}
	var heldC []*Chunk
	var heldH []map[string]bool
	var heldD []int64
	when := dates(pile)
	for k, c := range pile {
		tk := toks(c)
		h := map[string]bool{}
		for _, w := range want {
			if heldBy(w, tk, al) {
				h[w] = true
			}
		}
		if len(h)*HOLD_DEN >= HOLD_NUM*len(want) {
			heldC = append(heldC, c)
			heldH = append(heldH, h)
			heldD = append(heldD, when[k])
		}
	}
	df := map[string]int64{}
	for _, w := range want {
		for _, h := range heldH {
			if h[w] {
				df[w]++
			}
		}
	}
	var rows []scored
	for i, h := range heldH {
		if len(h) == 0 {
			continue
		}
		s := new(big.Rat)
		for w := range h {
			s.Add(s, big.NewRat(1, df[w]))
		}
		rows = append(rows, scored{s, heldC[i], heldD[i]})
	}
	copies := map[string]int{}
	for _, c := range pile {
		copies[c.id]++
	}
	sort.SliceStable(rows, func(i, j int) bool {
		x, y := rows[i], rows[j]
		if c := x.score.Cmp(y.score); c != 0 {
			return c > 0
		}
		// what was said once before what is said every week
		if copies[x.c.id] != copies[y.c.id] {
			return copies[x.c.id] < copies[y.c.id]
		}
		if x.d != y.d {
			return x.d > y.d
		}
		if x.c.path != y.c.path {
			return x.c.path < y.c.path
		}
		// a log grows downward: on one date, the later line is the newer one
		if x.d != 0 {
			return x.c.line > y.c.line
		}
		return x.c.line < y.c.line
	})
	out := []*Chunk{}
	shown := map[string]bool{} // one id, one place
	for _, s := range rows {
		if len(out) == TOP {
			break
		}
		if !shown[s.c.id] {
			shown[s.c.id] = true
			out = append(out, s.c)
		}
	}
	return out
}

func hint(why string, where, next *string) *Obj {
	m := obj("why", why)
	if where != nil {
		m.Set("where", *where)
	}
	if next != nil {
		m.Set("next", *next)
	}
	return m
}

func str(s string) *string { return &s }

func look(pile []*Chunk, bite string, served []*Chunk, al alias) []interface{} {
	out := []interface{}{}
	ws := words(bite)
	want := uniqueWords(ws)
	if len(want) == 0 {
		out = append(out, hint("every word is a common one: name the thing you mean", nil, nil))
	}
	every := map[string]bool{}
	for _, c := range pile {
		for t := range toks(c) {
			every[t] = true
		}
	}
	var absent []string
	for _, w := range want {
		if !heldBy(w, every, al) {
			absent = append(absent, w)
		}
	}
	for _, w := range want { // said, so a match their list made is never taken for theirs
		if holds(w, every) {
			continue
		}
		var read []string
		for _, x := range al[w] {
			if holds(x, every) {
				read = append(read, x)
			}
		}
		if len(read) > 0 {
			out = append(out, hint("read "+w+" as "+strings.Join(read, ", ")+", from your words list", nil, nil))
		}
	}
	if len(absent) > 0 {
		out = append(out, hint("no file in your folder has "+strings.Join(absent, ", "),
			str("it may be called something else there"), str(NEXT["other words"])))
	}
	for _, c := range served {
		seen := map[string]bool{}
		for _, name := range defines(c.text) {
			if seen[name] {
				continue
			}
			seen[name] = true
			uses := map[string]bool{}
			for _, d := range pile {
				if d != c && named(d.text, name) > 0 {
					uses[d.path] = true
				}
			}
			if named(c.text, name) > 1 {
				uses[c.path] = true
			}
			var sorted []string
			for u := range uses {
				sorted = append(sorted, u)
			}
			sort.Strings(sorted)
			where := "nothing else in your folder names it"
			if len(sorted) > 0 {
				where = "also named in " + strings.Join(sorted, ", ")
			}
			out = append(out, hint(name+" is defined at "+c.path+":"+strconv.Itoa(c.line), &where, str(NEXT["unused"])))
		}
	}
	if len(ws) > 0 && MAKE[ws[0]] {
		out = append(out, hint("this asks for something made", nil, str(NEXT["made"])))
	}
	return out
}

// ── the door ────────────────────────────────────────────────────────────────

func door(prop interface{}, served map[string]bool) *string {
	p, ok := prop.(*Obj)
	if !ok || len(p.keys) != 4 || !p.Has("path") || !p.Has("data") || !p.Has("cites") || !p.Has("claim") {
		return str("a row is exactly {path, data, cites, claim}")
	}
	path, ok := get(p, "path").(string)
	bad := !ok || path == "" || strings.HasPrefix(path, "/") || strings.HasPrefix(path, "\\")
	if !bad {
		for _, part := range strings.Split(path, "/") {
			bad = bad || part == ".."
		}
	}
	if bad {
		return str("a path is plain and relative, inside the box")
	}
	_, dataOk := get(p, "data").(string)
	cites, citesOk := get(p, "cites").([]interface{})
	if !dataOk || !citesOk {
		return str("data is text and cites a list")
	}
	claim, ok := get(p, "claim").(string)
	if !ok || blank(claim) {
		return str("a claim says why")
	}
	for _, c := range cites {
		s, ok := c.(string)
		if !ok || !served[s] {
			return str("a cite that the last bite didn't serve")
		}
	}
	return nil
}

// ── the record ──────────────────────────────────────────────────────────────

type Read struct {
	rows   []*Obj
	breaks []string
}

func readBytes(raw []byte) (*Read, error) {
	r := &Read{}
	if !utf8.Valid(raw) {
		return nil, errors.New("the record is not UTF-8")
	}
	data := string(raw)
	if data != "" && !strings.HasSuffix(data, "\n") {
		r.breaks = append(r.breaks, "torn tail: the last line is unterminated; a human looks first")
		return r, nil
	}
	prev := GENESIS
	var lines []string
	if data != "" {
		lines = strings.Split(data[:len(data)-1], "\n")
	}
	for i, line := range lines {
		row, err := loads(line)
		m, ok := row.(*Obj)
		if err != nil || !ok {
			m = nil
		}
		if m != nil {
			for k := range ROW_KEYS {
				if !m.Has(k) {
					m = nil
					break
				}
			}
		}
		if m == nil {
			r.breaks = append(r.breaks, "line "+strconv.Itoa(i)+": garbled, not a record row")
			continue
		}
		body := m.Copy()
		body.Del("hash")
		hash := ""
		func() {
			defer func() { recover() }()
			hash = h256(canon(body))
		}()
		p, _ := get(m, "prev").(string)
		h, hOk := get(m, "hash").(string)
		if p != prev || !hOk || hash != h {
			r.breaks = append(r.breaks, "row "+pyStr(get(m, "n"))+": chain broken")
		}
		n, isInt := get(m, "n").(*big.Int)
		if !isInt || n.Cmp(bigOf(len(r.rows))) != 0 {
			r.breaks = append(r.breaks, "row "+pyRepr(get(m, "n"))+": out of place, it is row "+strconv.Itoa(len(r.rows)))
		}
		r.rows = append(r.rows, m)
		prev = pyStr(get(m, "hash"))
	}
	return r, nil
}

// readRecord reads the record as kernel.py reads it: without a lock.
func readRecord(path string) (*Read, error) {
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &Read{}, nil
		}
		return nil, err
	}
	return readBytes(raw)
}

func appendRow(box, ts, kind, who string, fields *Obj) (*Obj, error) {
	path := filepath.Join(box, "record.jsonl")
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0o666)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	if err := lockFile(f); err != nil {
		return nil, err
	}
	raw, err := ioutil.ReadAll(f) // the true tail, read under the lock
	if err != nil {
		return nil, err
	}
	r, err := readBytes(raw)
	if err != nil {
		return nil, err
	}
	if len(r.breaks) > 0 {
		return nil, errors.New(strings.Join(r.breaks, "; "))
	}
	sealedRow := kind == "seal" && who == "human"
	standing := "unattested"
	if sealedRow {
		standing = "sealed"
	}
	row := obj("n", bigOf(len(r.rows)), "kind", kind, "who", who, "family", "kernel",
		"standing", standing, "version", VERSION, "ts", ts)
	rest := fields.Copy()
	row.Set("where", get(rest, "where"))
	rest.Del("where")
	for _, k := range rest.keys {
		row.Set(k, rest.vals[k])
	}
	if len(r.rows) > 0 {
		row.Set("prev", get(r.rows[len(r.rows)-1], "hash"))
	} else {
		row.Set("prev", GENESIS)
	}
	row.Set("hash", h256(canon(row)))
	if _, err := f.WriteString(canon(row) + "\n"); err != nil {
		return nil, err
	}
	if err := f.Sync(); err != nil {
		return nil, err
	}
	if len(r.rows) == 0 { // the new name survives a crash
		if d, err := os.Open(box); err == nil {
			d.Sync() // a file system that can't sync a folder: as kernel.py without O_DIRECTORY
			d.Close()
		}
	}
	return row, nil
}

// ── the box: theirs ─────────────────────────────────────────────────────────

func config(box string) (*Obj, error) {
	raw, err := ioutil.ReadFile(filepath.Join(box, "kernel.json"))
	if err != nil {
		return nil, err
	}
	v, err := loads(string(raw))
	if err != nil {
		return nil, err
	}
	o, ok := v.(*Obj)
	if !ok {
		return nil, errors.New("kernel.json is not an object")
	}
	return o, nil
}

// resolved is Path.resolve(): absolute, links resolved as far as the path exists.
func resolved(p string) string {
	abs, err := filepath.Abs(p)
	if err != nil {
		return p
	}
	probe := abs
	var tail []string
	for {
		if _, err := os.Lstat(probe); err == nil {
			break
		}
		parent := filepath.Dir(probe)
		if parent == probe {
			break
		}
		tail = append([]string{filepath.Base(probe)}, tail...)
		probe = parent
	}
	real, err := filepath.EvalSymlinks(probe)
	if err != nil {
		real = probe
	}
	return filepath.Join(append([]string{real}, tail...)...)
}

func inside(p, box string) bool {
	a, b := resolved(p), resolved(box)
	if !strings.HasSuffix(b, string(filepath.Separator)) {
		b += string(filepath.Separator)
	}
	return a+string(filepath.Separator) == b || strings.HasPrefix(a, b)
}

func pyErr(err error) string {
	if os.IsNotExist(err) {
		return "FileNotFoundError"
	}
	if os.IsPermission(err) {
		return "PermissionError"
	}
	return "OSError"
}

// modeBeyondOwner is `path.stat().st_mode & 0o077` on POSIX; nothing elsewhere.
func modeBeyondOwner(path string) (bool, error) {
	st, err := os.Stat(path)
	if err != nil {
		return false, err
	}
	return posix && st.Mode().Perm()&0o077 != 0, nil
}

func readKey(path, box string) ([]byte, *string) {
	if inside(path, box) {
		return nil, str("the key can't live inside the box")
	}
	open, err := modeBeyondOwner(path)
	if err != nil {
		return nil, str("the key could not be read: " + pyErr(err))
	}
	if open {
		return nil, str(path + " is readable beyond its owner; chmod 600 it")
	}
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, str("the key could not be read: " + pyErr(err))
	}
	if !utf8.Valid(raw) {
		return nil, str("the key could not be read: UnicodeDecodeError")
	}
	key, err := hex.DecodeString(strip(string(raw)))
	if err != nil {
		return nil, str("the key could not be read: ValueError")
	}
	return key, nil
}

// parseWords is kernel.py's: their words list as {their word: the folder's
// words}, or why not.
func parseWords(text string) (*Obj, *string) {
	out := newObj()
	for n, line := range splitlines(text) {
		s := strip(line)
		if s == "" || strings.HasPrefix(s, "#") {
			continue
		}
		eq := strings.Index(s, "=")
		left, right := s, ""
		if eq >= 0 {
			left, right = s[:eq], s[eq+1:]
		}
		var theirs [][]string
		for _, x := range strings.Split(right, ",") {
			theirs = append(theirs, words(x))
		}
		bad := eq < 0 || len(words(left)) != 1
		for _, t := range theirs {
			bad = bad || len(t) != 1
		}
		if bad {
			return newObj(), str("words list line " + strconv.Itoa(n+1) + ": one word = one or more words, a comma between")
		}
		her := words(left)[0]
		mine, _ := get(out, her).([]string)
		if !out.Has(her) {
			out.Set(her, []string{})
		}
		for _, t := range theirs {
			have := false
			for _, m := range mine {
				have = have || m == t[0]
			}
			if t[0] != her && !have {
				mine = append(mine, t[0])
			}
		}
		out.Set(her, mine)
	}
	res := newObj()
	for _, k := range out.keys {
		v := out.vals[k].([]string)
		if len(v) == 0 {
			continue
		}
		v = append([]string(nil), v...)
		sort.Strings(v)
		res.Set(k, v)
	}
	return res, nil
}

func aliasFromObj(o *Obj) alias {
	out := alias{}
	for _, k := range o.keys {
		out[k] = o.vals[k].([]string)
	}
	return out
}

func aliasJSON(o *Obj) *Obj {
	out := newObj()
	for _, k := range o.keys {
		var v []interface{}
		for _, x := range o.vals[k].([]string) {
			v = append(v, x)
		}
		if v == nil {
			v = []interface{}{}
		}
		out.Set(k, v)
	}
	return out
}

// readWords is kernel.py's: (the list, its SHA-256, why not), kept like the key.
func readWords(path, box string) (alias, string, *string) {
	if inside(path, box) {
		return nil, "", str("the words list can't live inside the box")
	}
	open, err := modeBeyondOwner(path)
	if err != nil {
		return nil, "", str("the words list could not be read: " + pyErr(err))
	}
	if open {
		return nil, "", str(path + " is readable beyond its owner; chmod 600 it")
	}
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, "", str("the words list could not be read: " + pyErr(err))
	}
	if !utf8.Valid(raw) {
		return nil, "", str("the words list could not be read: UnicodeDecodeError")
	}
	parsed, why := parseWords(string(raw))
	if why != nil {
		return nil, "", why
	}
	return aliasFromObj(parsed), sha256hex(raw), nil
}

func refuse(msg string) int {
	fmt.Fprintln(os.Stderr, msg)
	return REFUSED
}

func initBox(box, pile, key, ts string, wl *string) (int, error) {
	if _, err := os.Stat(filepath.Join(box, "record.jsonl")); err == nil {
		return refuse("refused: this box already has a record"), nil
	}
	if st, err := os.Stat(pile); err != nil || !st.IsDir() {
		return refuse("refused: " + pile + " is not a folder"), nil
	}
	if inside(key, box) {
		return refuse("refused: the key can't live inside the box"), nil
	}
	if wl != nil {
		if _, _, why := readWords(*wl, box); why != nil {
			return refuse("refused: " + *why), nil
		}
	}
	if _, err := os.Lstat(key); err != nil {
		if err := os.MkdirAll(filepath.Dir(key), 0o777); err != nil {
			return 0, err
		}
		k := make([]byte, 32)
		if _, err := rand.Read(k); err != nil {
			return 0, err
		}
		f, err := os.OpenFile(key, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
		if err != nil {
			return 0, err
		}
		f.WriteString(hex.EncodeToString(k) + "\n")
		f.Close()
	}
	if err := os.MkdirAll(box, 0o777); err != nil {
		return 0, err
	}
	cfg := obj("pile", resolved(pile), "key", resolved(key))
	if wl != nil {
		cfg.Set("words", resolved(*wl))
	}
	if err := ioutil.WriteFile(filepath.Join(box, "kernel.json"), []byte(dumpsDefault(cfg, true)+"\n"), 0o666); err != nil {
		return 0, err
	}
	row, err := appendRow(box, ts, "boot", "kernel", obj("loop", "open", "pile_sha256", h256(get(cfg, "pile").(string))))
	if err != nil {
		return 0, err
	}
	fmt.Println("ready: record started, row " + pyStr(get(row, "n")) + " " + get(row, "hash").(string)[:16])
	return ALIVE, nil
}

// ── the loop ────────────────────────────────────────────────────────────────

// bySubject is a dict of rows by subject: a later row for the same subject
// takes the place of the first, as Python's dict does.
type bySubject struct {
	order []string
	rows  map[string]*Obj
}

func (b *bySubject) put(s string, r *Obj) {
	if _, ok := b.rows[s]; !ok {
		b.order = append(b.order, s)
	}
	b.rows[s] = r
}

func (b *bySubject) has(s string) bool { _, ok := b.rows[s]; return ok }

// sealed is each proposal a seal row holds, by subject, only while its proof
// holds under the person's key. With act "decline", the same for the No.
func sealed(box string, rows []*Obj, act string) (*bySubject, error) {
	cfg, err := config(box)
	if err != nil {
		return nil, err
	}
	keyPath, _ := get(cfg, "key").(string)
	key, _ := readKey(keyPath, box)
	out := &bySubject{rows: map[string]*Obj{}}
	for _, r := range rows {
		if get(r, "kind") != act || key == nil {
			continue
		}
		subj := ""
		if r.Has("subject") {
			subj = pyStr(get(r, "subject"))
		}
		var asked *string
		if act == "seal" && r.Has("bite_key") {
			s, ok := get(r, "bite_key").(string)
			if !ok {
				continue
			}
			asked = &s
		}
		want := proof(key, subj, act, asked)
		got := "None"
		if r.Has("proof") {
			got = pyStr(get(r, "proof"))
		}
		if subtle.ConstantTimeCompare([]byte(want), []byte(got)) == 1 {
			out.put(pyStr(get(r, "subject")), r)
		}
	}
	return out, nil
}

func refusedBreaks(r *Read) bool {
	if len(r.breaks) == 0 {
		return false
	}
	fmt.Fprintln(os.Stderr, "refused:\n  "+strings.Join(r.breaks, "\n  "))
	return true
}

func propFile(box, subj string) string {
	return filepath.Join(box, "proposals", subj[9:]+".json")
}

// proposedUnder is the question a proposal was last made under, from the
// record: the bite its last passing proposal row names (before row `before`,
// if not negative). nil when the record names none.
func proposedUnder(rows []*Obj, subj string, before int64) *string {
	var last *Obj
	for _, r := range rows {
		if n, _ := asInt(get(r, "n")); before >= 0 && n >= before {
			break
		}
		if get(r, "kind") == "proposal" && get(r, "subject") == subj && get(r, "verdict") == "pass" {
			last = r
		}
	}
	if last == nil {
		return nil
	}
	i, ok := get(last, "bite_row").(*big.Int)
	if !ok || i.Sign() < 0 || i.Cmp(bigOf(len(rows))) >= 0 {
		return nil
	}
	b := rows[i.Int64()]
	if get(b, "kind") != "bite" {
		return nil
	}
	if key, ok := get(b, "bite_key").(string); ok {
		return &key
	}
	return nil
}

// standing is what a seal stands on: (the proposal, the question it was sealed
// for, nil), or (nil, nil, why not).
func standing(box string, rows []*Obj, subj string, seal *Obj) (*Obj, *string, *string) {
	raw, err := ioutil.ReadFile(propFile(box, subj))
	if err != nil {
		return nil, nil, str("is missing or can't be read")
	}
	v, err := loads(string(raw))
	prop, ok := v.(*Obj)
	if err != nil || !ok {
		return nil, nil, str("is missing or can't be read")
	}
	for _, k := range []string{"path", "data", "cites", "claim"} {
		if !prop.Has(k) {
			return nil, nil, str("is missing or can't be read")
		}
	}
	same := false
	func() {
		defer func() {
			if recover() != nil {
				prop = nil
			}
		}()
		same = subjectOf(prop) == subj
	}()
	if prop == nil {
		return nil, nil, str("is missing or can't be read")
	}
	if !same {
		return nil, nil, str("is not the bytes that were sealed")
	}
	var key *string
	if seal.Has("bite_key") {
		if s, ok := get(seal, "bite_key").(string); ok {
			key = &s
		}
	} else {
		n, _ := asInt(get(seal, "n"))
		key = proposedUnder(rows, subj, n)
	}
	if key == nil {
		return nil, nil, str("was made under no question the record names")
	}
	return prop, key, nil
}

func record(box string) (*Read, error) { return readRecord(filepath.Join(box, "record.jsonl")) }

func bite(box, text, ts string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if refusedBreaks(r) {
		return REFUSED, nil
	}
	key := biteKey(text)
	if key == nil {
		return refuse("refused: a bite with no words"), nil
	}
	good, err := sealed(box, r.rows, "seal")
	if err != nil {
		return 0, err
	}
	for _, subj := range good.order { // a sealed answer for these words, first
		prop, asked, why := standing(box, r.rows, subj, good.rows[subj])
		if why == nil && *asked == *key {
			if _, err := appendRow(box, ts, "bite", "kernel", obj("bite_key", *key, "answered_by", subj, "served", []interface{}{})); err != nil {
				return 0, err
			}
			fmt.Println(dumpsDefault(obj("state", "sealed", "answer", get(prop, "data"), "by", subj), false))
			return ALIVE, nil
		}
	}
	cfg, err := config(box)
	if err != nil {
		return 0, err
	}
	al := alias{}
	listed := newObj()
	if cfg.Has("words") {
		got, sha, why := readWords(pyStr(get(cfg, "words")), box)
		if why != nil {
			return refuse("refused: " + *why), nil
		}
		al = got
		listed.Set("words_sha256", sha)
	}
	pile := chunks(pyStr(get(cfg, "pile")))
	served := rank(pile, text, al)
	refs := []interface{}{}
	var answers []*Chunk
	for _, c := range served {
		e := echo(text, c.text)
		refs = append(refs, obj("id", c.id, "where", c.path+":"+strconv.Itoa(c.line), "echo", e))
		if !e {
			answers = append(answers, c)
		}
	}
	row := obj("bite_key", *key, "served", refs)
	for _, k := range listed.keys {
		row.Set(k, listed.vals[k])
	}
	if _, err := appendRow(box, ts, "bite", "kernel", row); err != nil {
		return 0, err
	}
	state := "empty"
	if len(answers) > 0 {
		state = "populated"
	} else if len(refs) > 0 {
		state = "echo"
	}
	doc := obj("state", state, "bite_key", *key)
	shown := []interface{}{}
	for i, c := range served {
		m := refs[i].(*Obj).Copy()
		m.Set("text", c.text)
		shown = append(shown, m)
	}
	doc.Set("served", shown)
	var forLook []*Chunk
	if len(answers) > 0 {
		forLook = served
	}
	if hints := look(pile, text, forLook, al); len(hints) > 0 {
		doc.Set("look", hints) // printed for them; the record keeps no words
	}
	fmt.Println(dumpsSpacedUtf8(doc))
	if len(answers) > 0 {
		return ALIVE, nil
	}
	return ESCALATE, nil
}

func propose(box string, lines []string, ts string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if refusedBreaks(r) {
		return REFUSED, nil
	}
	var last *Obj
	for i := len(r.rows) - 1; i >= 0; i-- {
		if get(r.rows[i], "kind") == "bite" {
			last = r.rows[i]
			break
		}
	}
	if last == nil {
		return refuse("refused: propose answers a bite; bite first"), nil
	}
	served := map[string]bool{}
	if sv, ok := get(last, "served").([]interface{}); ok {
		for _, s := range sv {
			if m, ok := s.(*Obj); ok {
				served[pyStr(get(m, "id"))] = true
			}
		}
	}
	for i, line := range lines {
		prop, err := loads(line)
		if err != nil {
			prop = nil
		}
		why := door(prop, served)
		if why == nil {
			p := prop.(*Obj)
			subj := subjectOf(p)
			if err := os.Mkdir(filepath.Join(box, "proposals"), 0o777); err != nil && !os.IsExist(err) {
				return 0, err
			}
			kept := p.Copy()
			kept.Set("bite_key", get(last, "bite_key"))
			if err := ioutil.WriteFile(propFile(box, subj), []byte(dumpsDefault(kept, false)), 0o666); err != nil {
				return 0, err
			}
			if _, err := appendRow(box, ts, "proposal", "kernel", obj("subject", subj, "verdict", "pass", "bite_row", get(last, "n"))); err != nil {
				return 0, err
			}
			fmt.Println("pass  " + subj + "  waiting on your seal")
		} else {
			if _, err := appendRow(box, ts, "proposal", "kernel", obj("verdict", "refused", "line", bigOf(i), "why", *why)); err != nil {
				return 0, err
			}
			fmt.Println("refused  line " + strconv.Itoa(i) + ": " + *why)
		}
	}
	// Passing the door is not acceptance: nothing propose reads is an answer
	// until the person seals it (CONST-0-1).
	return ESCALATE, nil
}

func isProposal(rows []*Obj, subj string) bool {
	for _, row := range rows {
		if get(row, "kind") == "proposal" && get(row, "subject") == subj {
			return true
		}
	}
	return false
}

func seal(box, subj, ts string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if refusedBreaks(r) {
		return REFUSED, nil
	}
	if !isProposal(r.rows, subj) {
		return refuse("refused: " + subj + " is not a proposal in this box"), nil
	}
	no, err := sealed(box, r.rows, "decline")
	if err != nil {
		return 0, err
	}
	if no.has(subj) {
		return refuse("refused: you declined " + subj + " at row " + pyStr(get(no.rows[subj], "n"))), nil
	}
	cfg, err := config(box)
	if err != nil {
		return 0, err
	}
	key, why := readKey(pyStr(get(cfg, "key")), box)
	if key == nil {
		return refuse("refused: " + *why), nil
	}
	raw, err := ioutil.ReadFile(propFile(box, subj))
	if err != nil {
		return 0, err
	}
	v, err := loads(string(raw))
	if err != nil {
		return 0, err
	}
	prop, ok := v.(*Obj)
	if !ok || subjectOf(prop) != subj { // approved bytes are proposed bytes (CONST-0-4)
		return refuse("refused: the proposal's bytes changed since it was proposed"), nil
	}
	asked := proposedUnder(r.rows, subj, -1) // the question this is the answer to
	if asked == nil {
		return refuse("refused: the record names no question " + subj + " was made under"), nil
	}
	if _, err := appendRow(box, ts, "seal", "human", obj("subject", subj, "bite_key", *asked, "proof", proof(key, subj, "seal", asked))); err != nil {
		return 0, err
	}
	out := filepath.Join(box, "written", pyStr(get(prop, "path")))
	if err := os.MkdirAll(filepath.Dir(out), 0o777); err != nil {
		return 0, err
	}
	if err := ioutil.WriteFile(out, []byte(pyStr(get(prop, "data"))), 0o666); err != nil {
		return 0, err
	}
	rel, _ := filepath.Rel(box, out)
	fmt.Println("sealed " + subj + "; written to " + filepath.ToSlash(rel))
	return ALIVE, nil
}

func decline(box, subj, ts string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if refusedBreaks(r) {
		return REFUSED, nil
	}
	if !isProposal(r.rows, subj) {
		return refuse("refused: " + subj + " is not a proposal in this box"), nil
	}
	for _, act := range []struct{ act, said string }{{"seal", "sealed"}, {"decline", "declined"}} {
		done, err := sealed(box, r.rows, act.act)
		if err != nil {
			return 0, err
		}
		if done.has(subj) {
			return refuse("refused: you " + act.said + " " + subj + " at row " + pyStr(get(done.rows[subj], "n"))), nil
		}
	}
	cfg, err := config(box)
	if err != nil {
		return 0, err
	}
	key, why := readKey(pyStr(get(cfg, "key")), box)
	if key == nil {
		return refuse("refused: " + *why), nil
	}
	if _, err := appendRow(box, ts, "decline", "human", obj("subject", subj, "proof", proof(key, subj, "decline", nil))); err != nil {
		return 0, err
	}
	fmt.Println("declined " + subj + "; it won't be offered again")
	return ALIVE, nil
}

func joinInts(xs []string) string { return "[" + strings.Join(xs, ", ") + "]" }

func verify(box string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if len(r.breaks) > 0 {
		fmt.Println(strings.Join(r.breaks, "\n"))
		return REFUSED, nil
	}
	good, err := sealed(box, r.rows, "seal")
	if err != nil {
		return 0, err
	}
	var forged []string
	for _, row := range r.rows {
		if get(row, "kind") == "seal" && !good.has(pyStr(get(row, "subject"))) {
			forged = append(forged, pyStr(get(row, "n")))
		}
	}
	no, err := sealed(box, r.rows, "decline")
	if err != nil {
		return 0, err
	}
	var nos []string
	for _, row := range r.rows {
		if get(row, "kind") == "decline" && !no.has(pyStr(get(row, "subject"))) {
			nos = append(nos, pyStr(get(row, "n")))
		}
	}
	var drifted [][2]string
	for _, subj := range good.order {
		prop, _, why := standing(box, r.rows, subj, good.rows[subj])
		if why == nil {
			named := proposedUnder(r.rows, subj, -1)
			v := get(prop, "bite_key") // missing reads as None, as dict.get does
			s, isStr := v.(string)
			same := (v == nil && named == nil) || (isStr && named != nil && s == *named)
			if !same {
				why = str("names another question than the record")
			}
		}
		if why != nil {
			drifted = append(drifted, [2]string{subj, *why})
		}
	}
	for _, d := range drifted {
		fmt.Println("the chain holds; " + d[0] + " is sealed, but its proposal file " + d[1])
	}
	if len(forged) > 0 {
		fmt.Println("the chain holds; seal rows " + joinInts(forged) + " don't prove under your key")
	}
	if len(nos) > 0 {
		fmt.Println("the chain holds; decline rows " + joinInts(nos) + " don't prove under your key")
	}
	if len(forged) > 0 || len(nos) > 0 || len(drifted) > 0 {
		return ESCALATE, nil
	}
	fmt.Println("the chain holds: " + strconv.Itoa(len(r.rows)) + " rows, " + strconv.Itoa(len(good.order)) + " sealed")
	return ALIVE, nil
}

func out(box, ts string) (int, error) {
	r, err := record(box)
	if err != nil {
		return 0, err
	}
	if refusedBreaks(r) {
		return REFUSED, nil
	}
	good, err := sealed(box, r.rows, "seal")
	if err != nil {
		return 0, err
	}
	no, err := sealed(box, r.rows, "decline")
	if err != nil {
		return 0, err
	}
	var waiting []string
	for _, row := range r.rows {
		if get(row, "kind") == "proposal" && get(row, "verdict") == "pass" {
			s := pyStr(get(row, "subject"))
			if !good.has(s) && !no.has(s) {
				waiting = append(waiting, s)
			}
		}
	}
	var tip interface{} = GENESIS
	if len(r.rows) > 0 {
		tip = get(r.rows[len(r.rows)-1], "hash")
	}
	if _, err := appendRow(box, ts, "out", "kernel", obj("waiting", bigOf(len(waiting)), "tip", tip)); err != nil {
		return 0, err
	}
	for _, s := range waiting {
		fmt.Println("waiting on your seal: " + s)
	}
	fmt.Println(strconv.Itoa(len(r.rows)+1) + " rows; " + strconv.Itoa(len(good.order)) + " sealed; " + strconv.Itoa(len(waiting)) + " waiting")
	if len(waiting) > 0 {
		return ESCALATE, nil
	}
	return ALIVE, nil
}

// ── the vectors: every case, answered, for compare.py ───────────────────────

func list(o *Obj, k string) []interface{} { return get(o, k).([]interface{}) }

func strOrNil(s *string) interface{} {
	if s == nil {
		return nil
	}
	return *s
}

func unhex(s string) []byte {
	b, err := hex.DecodeString(s)
	if err != nil {
		panic(err)
	}
	return b
}

func vectors(casesPath, results string) (int, error) {
	raw, err := ioutil.ReadFile(casesPath)
	if err != nil {
		return 0, err
	}
	doc, err := loads(string(raw))
	if err != nil {
		return 0, err
	}
	c := get(doc.(*Obj), "cases").(*Obj)
	out := newObj()

	canonOut := []interface{}{}
	for _, o := range list(c, "canon") {
		s := canon(get(o.(*Obj), "in"))
		canonOut = append(canonOut, obj("canon", s, "sha256", h256(s)))
	}
	out.Set("canon", canonOut)

	wordsOut := []interface{}{}
	for _, o := range list(c, "words") {
		t := get(o.(*Obj), "text").(string)
		ws := []interface{}{}
		for _, w := range words(t) {
			ws = append(ws, w)
		}
		wordsOut = append(wordsOut, obj("words", ws, "bite_key", strOrNil(biteKey(t))))
	}
	out.Set("words", wordsOut)

	hm := get(c, "hmac").(*Obj)
	rfc, seals := []interface{}{}, []interface{}{}
	for _, o := range list(hm, "rfc4231") {
		m := o.(*Obj)
		rfc = append(rfc, obj("mac", hmacHex(unhex(get(m, "key").(string)), unhex(get(m, "msg").(string)))))
	}
	for _, o := range list(hm, "seal") {
		m := o.(*Obj)
		var asked *string
		if m.Has("asked") {
			asked = str(get(m, "asked").(string))
		}
		seals = append(seals, obj("proof", proof(unhex(get(m, "key").(string)), get(m, "subject").(string), "seal", asked)))
	}
	out.Set("hmac", obj("rfc4231", rfc, "seal", seals))

	htmlOut := []interface{}{}
	for _, o := range list(c, "html") {
		htmlOut = append(htmlOut, obj("out", htmlText(get(o.(*Obj), "in").(string))))
	}
	out.Set("html", htmlOut)

	holdsOut := []interface{}{}
	for _, o := range list(c, "holds") {
		m := o.(*Obj)
		tk := map[string]bool{}
		for _, t := range list(m, "toks") {
			tk[t.(string)] = true
		}
		holdsOut = append(holdsOut, obj("out", holds(get(m, "w").(string), tk)))
	}
	out.Set("holds", holdsOut)

	echoOut := []interface{}{}
	for _, o := range list(c, "echo") {
		m := o.(*Obj)
		echoOut = append(echoOut, obj("out", echo(get(m, "bite").(string), get(m, "text").(string))))
	}
	out.Set("echo", echoOut)

	var piles [][]*Chunk
	chunksOut := []interface{}{}
	tmp, err := ioutil.TempDir("", "kernel-vectors")
	if err != nil {
		return 0, err
	}
	defer os.RemoveAll(tmp)
	for n, o := range list(c, "chunks") {
		root := filepath.Join(tmp, "pile"+strconv.Itoa(n))
		if err := os.MkdirAll(root, 0o777); err != nil {
			return 0, err
		}
		for _, f := range list(o.(*Obj), "pile") {
			fm := f.(*Obj)
			p := root
			for _, part := range list(fm, "parts") {
				p = filepath.Join(p, part.(string))
			}
			if err := os.MkdirAll(filepath.Dir(p), 0o777); err != nil {
				return 0, err
			}
			var body []byte
			if fm.Has("b64") {
				body, err = base64.StdEncoding.DecodeString(get(fm, "b64").(string))
				if err != nil {
					return 0, err
				}
			} else {
				body = []byte(strings.Repeat(get(fm, "repeat").(string), toInt(get(fm, "n"))) + get(fm, "then").(string))
			}
			if err := ioutil.WriteFile(p, body, 0o666); err != nil {
				return 0, err
			}
		}
		ch := chunks(root)
		piles = append(piles, ch)
		js := []interface{}{}
		for _, x := range ch {
			js = append(js, x.json())
		}
		chunksOut = append(chunksOut, obj("chunks", js))
	}
	out.Set("chunks", chunksOut)

	rankOut := []interface{}{}
	for _, o := range list(c, "rank") {
		m := o.(*Obj)
		ids := []interface{}{}
		for _, x := range rank(piles[toInt(get(m, "pile"))], get(m, "bite").(string), aliasOf(m)) {
			ids = append(ids, x.id)
		}
		rankOut = append(rankOut, obj("ids", ids))
	}
	out.Set("rank", rankOut)

	newestOut := []interface{}{}
	for _, o := range list(c, "newest") {
		newestOut = append(newestOut, obj("newest", newest(get(o.(*Obj), "text").(string))))
	}
	out.Set("newest", newestOut)

	wordlistOut := []interface{}{}
	for _, o := range list(c, "wordlist") {
		al, why := parseWords(get(o.(*Obj), "text").(string))
		wordlistOut = append(wordlistOut, obj("alias", aliasJSON(al), "why", strOrNil(why)))
	}
	out.Set("wordlist", wordlistOut)

	stemOut := []interface{}{}
	for _, o := range list(c, "stem") {
		stemOut = append(stemOut, obj("stem", stem(get(o.(*Obj), "w").(string))))
	}
	out.Set("stem", stemOut)

	lookOut := []interface{}{}
	for _, o := range list(c, "look") {
		m := o.(*Obj)
		pile := piles[toInt(get(m, "pile"))]
		var served []*Chunk
		for _, x := range list(m, "served") {
			served = append(served, pile[toInt(x)])
		}
		lookOut = append(lookOut, obj("look", look(pile, get(m, "bite").(string), served, aliasOf(m))))
	}
	out.Set("look", lookOut)

	doorOut := []interface{}{}
	for _, o := range list(c, "door") {
		m := o.(*Obj)
		prop, err := loads(get(m, "line").(string))
		if err != nil {
			prop = nil
		}
		served := map[string]bool{}
		for _, s := range list(m, "served") {
			served[s.(string)] = true
		}
		doorOut = append(doorOut, obj("why", strOrNil(door(prop, served))))
	}
	out.Set("door", doorOut)

	subjOut := []interface{}{}
	for _, o := range list(c, "subject") {
		subjOut = append(subjOut, obj("subject", subjectOf(get(o.(*Obj), "prop").(*Obj))))
	}
	out.Set("subject", subjOut)

	if err := ioutil.WriteFile(results, []byte(canon(out)+"\n"), 0o666); err != nil {
		return 0, err
	}
	return ALIVE, nil
}

// ── the command line ────────────────────────────────────────────────────────

func now() string { return time.Now().UTC().Format("2006-01-02T15:04:05Z") }

const USAGE = `kernel.py: answers questions from your own files. Python 3.9+, stdlib only.
    python kernel.py init    --box DIR --pile FOLDER --key FILE [--words FILE]
    python kernel.py bite    --box DIR "your question"
    python kernel.py propose --box DIR --file SUGGESTIONS.jsonl
    python kernel.py seal    --box DIR proposal:<sha256>
    python kernel.py decline --box DIR proposal:<sha256>
    python kernel.py verify  --box DIR
    python kernel.py out     --box DIR
    python kernel.py test`

func tablesPath() string {
	if p := os.Getenv("KERNEL_TABLES"); p != "" {
		return p
	}
	if _, err := os.Stat("kernel_tables.json"); err == nil {
		return "kernel_tables.json"
	}
	if exe, err := os.Executable(); err == nil {
		return filepath.Join(filepath.Dir(exe), "..", "..", "..", "vectors", "kernel_tables.json")
	}
	return "kernel_tables.json"
}

// selfVersion is the SHA-256 of this binary, as kernel.py's VERSION is of its file.
func selfVersion() string {
	exe, err := os.Executable()
	if err != nil {
		return GENESIS
	}
	raw, err := ioutil.ReadFile(exe)
	if err != nil {
		return GENESIS
	}
	return sha256hex(raw)
}

func run(argv []string) (int, error) {
	if err := loadTables(tablesPath()); err != nil {
		return 0, err
	}
	VERSION = selfVersion()
	if len(argv) >= 1 && argv[0] == "vectors" {
		if len(argv) != 3 {
			return refuse("vectors CASES.json RESULTS.json"), nil
		}
		return vectors(argv[1], argv[2])
	}
	verb := ""
	if len(argv) > 0 {
		verb = argv[0]
	}
	opts := map[string]string{}
	var args []string
	for i := 1; i < len(argv); i++ {
		a := argv[i]
		switch a {
		case "--box", "--pile", "--key", "--file", "--now", "--words":
			if i+1 < len(argv) {
				i++
				opts[a] = argv[i]
			} else {
				opts[a] = ""
			}
		default:
			args = append(args, a)
		}
	}
	if opts["--box"] == "" {
		return refuse(USAGE), nil
	}
	box, ts := opts["--box"], opts["--now"]
	if ts == "" {
		ts = now()
	}
	if verb == "init" && opts["--pile"] != "" && opts["--key"] != "" && len(args) == 0 {
		var wl *string
		if opts["--words"] != "" {
			wl = str(opts["--words"])
		}
		return initBox(box, opts["--pile"], opts["--key"], ts, wl)
	}
	if _, err := os.Stat(filepath.Join(box, "kernel.json")); err != nil {
		return refuse("refused: not a kernel box; init first"), nil
	}
	switch {
	case verb == "bite" && len(args) == 1:
		return bite(box, args[0], ts)
	case verb == "propose" && opts["--file"] != "" && len(args) == 0:
		raw, err := ioutil.ReadFile(opts["--file"])
		if err != nil {
			return 0, err
		}
		if !utf8.Valid(raw) {
			return 0, errors.New("the suggestions are not UTF-8")
		}
		return propose(box, splitlines(string(raw)), ts)
	case verb == "seal" && len(args) == 1 && strings.HasPrefix(args[0], "proposal:"):
		return seal(box, args[0], ts)
	case verb == "decline" && len(args) == 1 && strings.HasPrefix(args[0], "proposal:"):
		return decline(box, args[0], ts)
	case verb == "verify" && len(args) == 0:
		return verify(box)
	case verb == "out" && len(args) == 0:
		return out(box, ts)
	}
	return refuse(USAGE), nil
}

func main() {
	code, err := run(os.Args[1:])
	if err != nil {
		fmt.Fprintln(os.Stderr, "refused: "+err.Error())
		code = REFUSED
	}
	os.Exit(code)
}
