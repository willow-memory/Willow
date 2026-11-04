// kernel.rs: kernel.py in Rust. Rust 1.47 or later, the standard library
// only, no crates (checked on Rust 1.47.0 from 2020, and on Rust 1.97).
//
//   cargo build --release            # ports/rust/target/release/kernel
//   kernel init    --box DIR --pile FOLDER --key FILE [--words FILE]
//   kernel bite    --box DIR "your words"
//   kernel propose --box DIR --file ROWS.jsonl
//   kernel seal    --box DIR proposal:<sha256>
//   kernel decline --box DIR proposal:<sha256>
//   kernel verify  --box DIR
//   kernel out     --box DIR
//   kernel vectors CASES.json RESULTS.json
//
// The fifth port, following the Go port (../go/kernel.go) function for
// function, which follows Java's. Held to ../cases.json by ../compare.py,
// byte for byte and both ways (a box written here verifies under kernel.py,
// and the reverse).
//
// What the standard library lacks is written here, small and checked by the
// vectors: SHA-256 and HMAC (RFC 4231's own cases are among them), a JSON
// reader and writer that match Python's, base64, and an exact rational for
// the rank's scores (a sum of fractions compared by cross-multiplying whole
// numbers, never a float). The kernel's four patterns are the same scanners
// every port has, since Rust's regex has no backreference and is a crate
// anyway. Python's decisions are read from kernel_tables.json, which gen.py
// reads out of Python, so this compiler's Unicode never decides a word. The
// tables are found at $KERNEL_TABLES, else kernel_tables.json in the working
// directory, else vectors/kernel_tables.json four folders above the built
// binary (target/release/kernel under ports/rust/).
//
// Text is handled as code points (Vec<char>), as Python handles str. An
// integer in a record row is kept as its own digits, so a row holding one
// wider than this machine's words still canonicalises and hashes as it did.
//
// On Linux and macOS the writer takes flock on the record, the lock kernel.py
// takes, so this port and kernel.py keep out of each other's way when they
// write one box. On Windows there is none.
//
// Exit codes, the kernel's: 0 a human said it, 42 not enough information to
// say a human said this was true, 2 refused.

// what clippy would have instead is newer than the toolchains this is held
// to (`is_multiple_of`, `is_some_and`), or the cfg blocks' own return
#![allow(
    clippy::manual_is_multiple_of,
    clippy::unnecessary_map_or,
    clippy::needless_return,
    unknown_lints
)]

use std::cmp::Ordering;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process;

const ALIVE: i32 = 0;
const ESCALATE: i32 = 42;
const REFUSED: i32 = 2;

type Res<T> = Result<T, String>;

fn io_err(e: std::io::Error) -> String {
    e.to_string()
}

// ── JSON: Python's json.loads in, the kernel's canon out ─────────────────────

/// A JSON object as Python's dict holds it: keys in the order they came, a
/// repeated key keeping its place and taking the last value.
#[derive(Clone, Debug, Default)]
struct Obj {
    keys: Vec<String>,
    vals: HashMap<String, Value>,
}

impl Obj {
    fn new() -> Obj {
        Obj::default()
    }

    fn set(&mut self, k: &str, v: Value) {
        if !self.vals.contains_key(k) {
            self.keys.push(k.to_string());
        }
        self.vals.insert(k.to_string(), v);
    }

    fn get(&self, k: &str) -> Option<&Value> {
        self.vals.get(k)
    }

    fn has(&self, k: &str) -> bool {
        self.vals.contains_key(k)
    }

    fn del(&mut self, k: &str) {
        if self.vals.remove(k).is_some() {
            self.keys.retain(|x| x != k);
        }
    }

    fn str(&self, k: &str) -> Option<&str> {
        match self.get(k) {
            Some(Value::Str(s)) => Some(s),
            _ => None,
        }
    }

    fn list(&self, k: &str) -> &[Value] {
        match self.get(k) {
            Some(Value::List(v)) => v,
            _ => &[],
        }
    }

    fn obj(&self, k: &str) -> Option<&Obj> {
        match self.get(k) {
            Some(Value::Obj(o)) => Some(o),
            _ => None,
        }
    }
}

/// A JSON value. An integer keeps its digits (Python's int has no width); a
/// float is read and never used, since no row and no case holds one.
#[derive(Clone, Debug)]
enum Value {
    Null,
    Bool(bool),
    Int(String),
    Float,
    Str(String),
    List(Vec<Value>),
    Obj(Obj),
}

fn s(x: &str) -> Value {
    Value::Str(x.to_string())
}

fn int(n: i64) -> Value {
    Value::Int(n.to_string())
}

fn obj(kv: &[(&str, Value)]) -> Obj {
    let mut o = Obj::new();
    for (k, v) in kv {
        o.set(k, v.clone());
    }
    o
}

impl Value {
    fn as_str(&self) -> Option<&str> {
        match self {
            Value::Str(s) => Some(s),
            _ => None,
        }
    }

    /// The integer as this machine counts, when it is one and fits.
    fn as_int(&self) -> Option<i128> {
        match self {
            Value::Int(d) => d.parse::<i128>().ok(),
            _ => None,
        }
    }

    fn is_int(&self) -> bool {
        matches!(self, Value::Int(_))
    }
}

struct Parser {
    s: Vec<char>,
    i: usize,
}

/// json.loads: whitespace " \t\n\r" around, one value, nothing after.
fn loads(text: &str) -> Res<Value> {
    let mut p = Parser {
        s: text.chars().collect(),
        i: 0,
    };
    p.ws();
    let v = p.value()?;
    p.ws();
    if p.i != p.s.len() {
        return Err("extra data".into());
    }
    Ok(v)
}

fn is_dec(c: char) -> bool {
    c.is_ascii_digit()
}

fn is_hex(c: char) -> bool {
    c.is_ascii_hexdigit()
}

impl Parser {
    fn at(&self, i: usize) -> char {
        if i < self.s.len() {
            self.s[i]
        } else {
            '\0'
        }
    }

    fn ws(&mut self) {
        while self.i < self.s.len() && " \t\n\r".contains(self.s[self.i]) {
            self.i += 1;
        }
    }

    fn starts(&self, lit: &str) -> bool {
        lit.chars()
            .enumerate()
            .all(|(k, c)| self.i + k < self.s.len() && self.s[self.i + k] == c)
    }

    fn value(&mut self) -> Res<Value> {
        if self.i >= self.s.len() {
            return Err("expecting value".into());
        }
        match self.s[self.i] {
            '{' => return self.object(),
            '[' => return self.array(),
            '"' => return self.string().map(Value::Str),
            _ => {}
        }
        let lits: [(&str, Value); 6] = [
            ("null", Value::Null),
            ("true", Value::Bool(true)),
            ("false", Value::Bool(false)),
            ("NaN", Value::Float),
            ("Infinity", Value::Float),
            ("-Infinity", Value::Float),
        ];
        for (lit, v) in lits.iter() {
            if self.starts(lit) {
                self.i += lit.chars().count();
                return Ok(v.clone());
            }
        }
        self.number()
    }

    /// `(-?(?:0|[1-9][0-9]*))(\.[0-9]+)?([eE][-+]?[0-9]+)?`
    fn number(&mut self) -> Res<Value> {
        let start = self.i;
        let mut j = self.i;
        if self.at(j) == '-' {
            j += 1;
        }
        if self.at(j) == '0' {
            j += 1;
        } else if ('1'..='9').contains(&self.at(j)) {
            while is_dec(self.at(j)) {
                j += 1;
            }
        } else {
            return Err("expecting value".into());
        }
        let whole = j;
        if self.at(j) == '.' && is_dec(self.at(j + 1)) {
            j += 1;
            while is_dec(self.at(j)) {
                j += 1;
            }
        }
        if self.at(j) == 'e' || self.at(j) == 'E' {
            let mut k = j + 1;
            if self.at(k) == '+' || self.at(k) == '-' {
                k += 1;
            }
            if is_dec(self.at(k)) {
                while is_dec(self.at(k)) {
                    k += 1;
                }
                j = k;
            }
        }
        self.i = j;
        let text: String = self.s[start..j].iter().collect();
        if j == whole {
            // int("-0") is 0
            return Ok(Value::Int(if text == "-0" {
                "0".to_string()
            } else {
                text
            }));
        }
        text.parse::<f64>()
            .map(|_| Value::Float)
            .map_err(|_| "bad number".to_string())
    }

    fn object(&mut self) -> Res<Value> {
        self.i += 1;
        let mut out = Obj::new();
        self.ws();
        if self.at(self.i) == '}' {
            self.i += 1;
            return Ok(Value::Obj(out));
        }
        loop {
            self.ws();
            if self.at(self.i) != '"' {
                return Err("expecting key".into());
            }
            let k = self.string()?;
            self.ws();
            if self.at(self.i) != ':' {
                return Err("expecting :".into());
            }
            self.i += 1;
            self.ws();
            let v = self.value()?;
            out.set(&k, v);
            self.ws();
            match self.at(self.i) {
                ',' => self.i += 1,
                '}' => {
                    self.i += 1;
                    return Ok(Value::Obj(out));
                }
                _ => return Err("expecting , or }".into()),
            }
        }
    }

    fn array(&mut self) -> Res<Value> {
        self.i += 1;
        let mut out = Vec::new();
        self.ws();
        if self.at(self.i) == ']' {
            self.i += 1;
            return Ok(Value::List(out));
        }
        loop {
            self.ws();
            out.push(self.value()?);
            self.ws();
            match self.at(self.i) {
                ',' => self.i += 1,
                ']' => {
                    self.i += 1;
                    return Ok(Value::List(out));
                }
                _ => return Err("expecting , or ]".into()),
            }
        }
    }

    fn hex4(&self, i: usize) -> Res<u32> {
        if i + 4 > self.s.len() {
            return Err("bad \\u escape".into());
        }
        let t: String = self.s[i..i + 4].iter().collect();
        u32::from_str_radix(&t, 16).map_err(|_| "bad \\u escape".to_string())
    }

    fn string(&mut self) -> Res<String> {
        self.i += 1; // the opening quote
        let mut b = String::new();
        loop {
            if self.i >= self.s.len() {
                return Err("unterminated string".into());
            }
            let c = self.s[self.i];
            self.i += 1;
            if c == '"' {
                return Ok(b);
            }
            if (c as u32) < 0x20 {
                return Err("invalid control character".into());
            }
            if c != '\\' {
                b.push(c);
                continue;
            }
            if self.i >= self.s.len() {
                return Err("unterminated escape".into());
            }
            let e = self.s[self.i];
            self.i += 1;
            match e {
                '"' | '\\' | '/' => b.push(e),
                'b' => b.push('\u{8}'),
                'f' => b.push('\u{c}'),
                'n' => b.push('\n'),
                'r' => b.push('\r'),
                't' => b.push('\t'),
                'u' => {
                    let mut u = self.hex4(self.i)?;
                    self.i += 4;
                    // a surrogate pair is one code point, as Python's json reads it
                    if (0xD800..=0xDBFF).contains(&u)
                        && self.at(self.i) == '\\'
                        && self.at(self.i + 1) == 'u'
                    {
                        let lo = self.hex4(self.i + 2)?;
                        if (0xDC00..=0xDFFF).contains(&lo) {
                            u = 0x10000 + ((u - 0xD800) << 10) + (lo - 0xDC00);
                            self.i += 6;
                        }
                    }
                    b.push(std::char::from_u32(u).unwrap_or('\u{FFFD}'));
                }
                _ => return Err("invalid escape".into()),
            }
        }
    }
}

/// Family A, json.dumps(sort_keys=True, separators=(",", ":"),
/// ensure_ascii=False). No floats: the kernel's rows never hold one, and a
/// port must not invent repr(float).
fn canon(v: &Value) -> Res<String> {
    let mut b = String::new();
    dump(v, &mut b, true, false, false)?;
    Ok(b)
}

/// json.dumps(o, sort_keys=sort) with Python's default separators and
/// ensure_ascii=True: kernel.json and the proposal files.
fn dumps_default(v: &Value, sort: bool) -> String {
    let mut b = String::new();
    dump(v, &mut b, sort, true, true).unwrap_or_default();
    b
}

/// json.dumps(doc, ensure_ascii=False): what the person reads.
fn dumps_spaced_utf8(v: &Value) -> String {
    let mut b = String::new();
    dump(v, &mut b, false, true, false).unwrap_or_default();
    b
}

fn dump(v: &Value, b: &mut String, sort: bool, spaced: bool, ascii: bool) -> Res<()> {
    let (comma, colon) = if spaced { (", ", ": ") } else { (",", ":") };
    match v {
        Value::Null => b.push_str("null"),
        Value::Bool(x) => b.push_str(if *x { "true" } else { "false" }),
        Value::Int(d) => b.push_str(d),
        Value::Float => return Err("canon refuses a float".into()),
        Value::Str(x) => quote(x, b, ascii),
        Value::List(xs) => {
            b.push('[');
            for (i, x) in xs.iter().enumerate() {
                if i > 0 {
                    b.push_str(comma);
                }
                dump(x, b, sort, spaced, ascii)?;
            }
            b.push(']');
        }
        Value::Obj(o) => {
            let mut keys = o.keys.clone();
            if sort {
                keys.sort(); // byte order of UTF-8 is code point order, as Python sorts str
            }
            b.push('{');
            for (i, k) in keys.iter().enumerate() {
                if i > 0 {
                    b.push_str(comma);
                }
                quote(k, b, ascii);
                b.push_str(colon);
                dump(&o.vals[k], b, sort, spaced, ascii)?;
            }
            b.push('}');
        }
    }
    Ok(())
}

fn quote(x: &str, b: &mut String, ascii: bool) {
    b.push('"');
    for c in x.chars() {
        match c {
            '"' => b.push_str("\\\""),
            '\\' => b.push_str("\\\\"),
            '\n' => b.push_str("\\n"),
            '\r' => b.push_str("\\r"),
            '\t' => b.push_str("\\t"),
            '\u{8}' => b.push_str("\\b"),
            '\u{c}' => b.push_str("\\f"),
            _ => {
                let u = c as u32;
                if u < 0x20 || (ascii && u > 0x7e) {
                    if u > 0xFFFF {
                        // ensure_ascii writes an astral character as its surrogate pair
                        let w = u - 0x10000;
                        b.push_str(&format!(
                            "\\u{:04x}\\u{:04x}",
                            0xD800 + (w >> 10),
                            0xDC00 + (w & 0x3FF)
                        ));
                    } else {
                        b.push_str(&format!("\\u{:04x}", u));
                    }
                } else {
                    b.push(c);
                }
            }
        }
    }
    b.push('"');
}

/// str(o) for what a record row can hold.
fn py_str(v: &Value) -> String {
    match v {
        Value::Null => "None".into(),
        Value::Bool(x) => (if *x { "True" } else { "False" }).into(),
        Value::Str(x) => x.clone(),
        Value::Int(d) => d.clone(),
        _ => canon(v).unwrap_or_default(),
    }
}

/// repr(o), for the out-of-place break.
fn py_repr(v: &Value) -> String {
    match v {
        Value::Str(x) => format!("'{}'", x),
        _ => py_str(v),
    }
}

// ── SHA-256 and HMAC, the standard library has neither ───────────────────────

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

/// SHA-256 (FIPS 180-4), as every other port gets from its library.
fn sha256(data: &[u8]) -> [u8; 32] {
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let mut msg = data.to_vec();
    let bits = (data.len() as u64).wrapping_mul(8);
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bits.to_be_bytes());
    for block in msg.chunks(64) {
        let mut w = [0u32; 64];
        for (t, word) in block.chunks(4).enumerate() {
            w[t] = u32::from_be_bytes([word[0], word[1], word[2], word[3]]);
        }
        for t in 16..64 {
            let s0 = w[t - 15].rotate_right(7) ^ w[t - 15].rotate_right(18) ^ (w[t - 15] >> 3);
            let s1 = w[t - 2].rotate_right(17) ^ w[t - 2].rotate_right(19) ^ (w[t - 2] >> 10);
            w[t] = w[t - 16]
                .wrapping_add(s0)
                .wrapping_add(w[t - 7])
                .wrapping_add(s1);
        }
        let (mut a, mut bb, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
        for t in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ (!e & g);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[t])
                .wrapping_add(w[t]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & bb) ^ (a & c) ^ (bb & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = bb;
            bb = a;
            a = t1.wrapping_add(t2);
        }
        for (i, x) in [a, bb, c, d, e, f, g, hh].iter().enumerate() {
            h[i] = h[i].wrapping_add(*x);
        }
    }
    let mut out = [0u8; 32];
    for (i, x) in h.iter().enumerate() {
        out[i * 4..i * 4 + 4].copy_from_slice(&x.to_be_bytes());
    }
    out
}

fn hex(d: &[u8]) -> String {
    d.iter().map(|b| format!("{:02x}", b)).collect()
}

fn unhex(s: &str) -> Res<Vec<u8>> {
    let b = s.as_bytes();
    if b.len() % 2 != 0 {
        return Err("odd hex".into());
    }
    (0..b.len() / 2)
        .map(|i| u8::from_str_radix(&s[2 * i..2 * i + 2], 16).map_err(|_| "bad hex".to_string()))
        .collect()
}

fn sha256hex(data: &[u8]) -> String {
    hex(&sha256(data))
}

fn h256(text: &str) -> String {
    sha256hex(text.as_bytes())
}

/// HMAC-SHA-256 (RFC 2104); the vectors hold it to RFC 4231's cases.
fn hmac_hex(key: &[u8], msg: &[u8]) -> String {
    let mut k = if key.len() > 64 {
        sha256(key).to_vec()
    } else {
        key.to_vec()
    };
    k.resize(64, 0);
    let mut inner: Vec<u8> = k.iter().map(|b| b ^ 0x36).collect();
    inner.extend_from_slice(msg);
    let mut outer: Vec<u8> = k.iter().map(|b| b ^ 0x5c).collect();
    outer.extend_from_slice(&sha256(&inner));
    sha256hex(&outer)
}

/// HMAC-SHA-256 under their key, over the act ("seal", or "decline" for a
/// No), a unit separator, the subject; and, for a seal that names the
/// question it answers, another separator and that question's key.
fn proof(key: &[u8], subject: &str, act: &str, asked: Option<&str>) -> String {
    let mut msg = format!("{}\u{1f}{}", act, subject);
    if let Some(a) = asked {
        msg.push('\u{1f}');
        msg.push_str(a);
    }
    hmac_hex(key, msg.as_bytes())
}

fn base64_decode(s: &str) -> Res<Vec<u8>> {
    let mut out = Vec::new();
    let mut acc: u32 = 0;
    let mut bits = 0;
    for c in s.chars() {
        let v = match c {
            'A'..='Z' => c as u32 - 'A' as u32,
            'a'..='z' => c as u32 - 'a' as u32 + 26,
            '0'..='9' => c as u32 - '0' as u32 + 52,
            '+' => 62,
            '/' => 63,
            '=' | '\n' | '\r' => continue,
            _ => return Err("bad base64".into()),
        };
        acc = (acc << 6) | v;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push(((acc >> bits) & 0xff) as u8);
        }
    }
    Ok(out)
}

// ── the tables: Python's decisions, read out of Python ──────────────────────

struct Ranges {
    lo: Vec<u32>,
    hi: Vec<u32>,
}

impl Ranges {
    fn from(v: &[Value]) -> Ranges {
        let mut r = Ranges {
            lo: vec![],
            hi: vec![],
        };
        for x in v {
            if let Value::List(pair) = x {
                r.lo.push(pair[0].as_int().unwrap_or(0) as u32);
                r.hi.push(pair[1].as_int().unwrap_or(0) as u32);
            }
        }
        r
    }

    fn has(&self, c: char) -> bool {
        let c = c as u32;
        let (mut a, mut z) = (0i64, self.lo.len() as i64 - 1);
        while a <= z {
            let m = ((a + z) / 2) as usize;
            if c < self.lo[m] {
                z = m as i64 - 1;
            } else if c > self.hi[m] {
                a = m as i64 + 1;
            } else {
                return true;
            }
        }
        false
    }
}

struct Tables {
    word: Ranges,
    space: Ranges,
    digit: Ranges,
    cased: Ranges,
    ignorable: Ranges,
    lower: HashMap<char, String>,
    line_breaks: HashSet<char>,
    html5: HashMap<String, String>,
    invalid_charrefs: HashMap<u64, String>,
    invalid_codepoints: HashSet<u32>,
    ccc: HashMap<char, i64>,
    decomp: HashMap<char, Vec<char>>,
    compose: HashMap<(char, char), char>,
    tag_fold: HashMap<char, HashSet<char>>,
    tag_backref: HashMap<char, HashSet<(char, char)>>,
    genesis: String,
    top: usize,
    sniff: usize,
    max_file: u64,
    max_chunk: usize,
    echo_run: usize,
    hold_num: usize,
    hold_den: usize,
    function: HashSet<String>,
    make: HashSet<String>,
    row_keys: HashSet<String>,
    next: HashMap<String, String>,
}

static mut TABLES: *const Tables = std::ptr::null();
static mut VERSION: *const String = std::ptr::null();

fn t() -> &'static Tables {
    unsafe { &*TABLES }
}

fn version() -> &'static str {
    unsafe { &*VERSION }
}

fn ch(v: &Value) -> char {
    std::char::from_u32(v.as_int().unwrap_or(0) as u32).unwrap_or('\0')
}

fn string_set(v: &[Value]) -> HashSet<String> {
    v.iter()
        .filter_map(|x| x.as_str().map(String::from))
        .collect()
}

fn load_tables(path: &str) -> Res<Tables> {
    let raw = fs::read_to_string(path).map_err(|e| format!("{}: {}", path, e))?;
    let doc = loads(&raw)?;
    let tb = match doc {
        Value::Obj(o) => o,
        _ => return Err("the tables are not an object".into()),
    };
    let sigma = tb.obj("sigma").ok_or("no sigma")?;
    let nfc = tb.obj("nfc").ok_or("no nfc")?;
    let kc = tb.obj("kernel").ok_or("no kernel")?;
    let n = |k: &str| kc.get(k).and_then(|v| v.as_int()).unwrap_or(0);
    let hold = kc.list("HOLD");
    let mut tables = Tables {
        word: Ranges::from(tb.list("word")),
        space: Ranges::from(tb.list("space")),
        digit: Ranges::from(tb.list("digit")),
        cased: Ranges::from(sigma.list("cased")),
        ignorable: Ranges::from(sigma.list("case_ignorable")),
        lower: HashMap::new(),
        line_breaks: tb.list("line_breaks").iter().map(ch).collect(),
        html5: HashMap::new(),
        invalid_charrefs: HashMap::new(),
        invalid_codepoints: tb
            .list("invalid_codepoints")
            .iter()
            .map(|v| v.as_int().unwrap_or(0) as u32)
            .collect(),
        ccc: HashMap::new(),
        decomp: HashMap::new(),
        compose: HashMap::new(),
        tag_fold: HashMap::new(),
        tag_backref: HashMap::new(),
        genesis: kc.str("GENESIS").unwrap_or("").to_string(),
        top: n("TOP") as usize,
        sniff: n("SNIFF") as usize,
        max_file: n("MAX_FILE") as u64,
        max_chunk: n("MAX_CHUNK") as usize,
        echo_run: n("ECHO_RUN") as usize,
        hold_num: hold[0].as_int().unwrap_or(1) as usize,
        hold_den: hold[1].as_int().unwrap_or(2) as usize,
        function: string_set(kc.list("FUNCTION")),
        make: string_set(kc.list("MAKE")),
        row_keys: string_set(kc.list("ROW_KEYS")),
        next: HashMap::new(),
    };
    for (k, v) in &tb.obj("lower").ok_or("no lower")?.vals {
        if let (Ok(n), Some(l)) = (k.parse::<u32>(), v.as_str()) {
            if let Some(c) = std::char::from_u32(n) {
                tables.lower.insert(c, l.to_string());
            }
        }
    }
    for (k, v) in &tb.obj("html5").ok_or("no html5")?.vals {
        tables
            .html5
            .insert(k.clone(), v.as_str().unwrap_or("").to_string());
    }
    for (k, v) in &tb
        .obj("invalid_charrefs")
        .ok_or("no invalid_charrefs")?
        .vals
    {
        tables.invalid_charrefs.insert(
            k.parse::<u64>().unwrap_or(0),
            v.as_str().unwrap_or("").to_string(),
        );
    }
    for (k, v) in &nfc.obj("ccc").ok_or("no ccc")?.vals {
        if let Some(c) = k.parse::<u32>().ok().and_then(std::char::from_u32) {
            tables.ccc.insert(c, v.as_int().unwrap_or(0) as i64);
        }
    }
    for (k, v) in &nfc.obj("decomp").ok_or("no decomp")?.vals {
        if let (Some(c), Value::List(xs)) = (k.parse::<u32>().ok().and_then(std::char::from_u32), v)
        {
            tables.decomp.insert(c, xs.iter().map(ch).collect());
        }
    }
    for x in nfc.list("compose") {
        if let Value::List(p) = x {
            tables.compose.insert((ch(&p[0]), ch(&p[1])), ch(&p[2]));
        }
    }
    for (k, v) in &kc.obj("NEXT").ok_or("no NEXT")?.vals {
        tables
            .next
            .insert(k.clone(), v.as_str().unwrap_or("").to_string());
    }
    for (k, v) in &tb.obj("tag_fold").ok_or("no tag_fold")?.vals {
        if let (Some(c), Value::List(xs)) = (k.chars().next(), v) {
            tables.tag_fold.insert(c, xs.iter().map(ch).collect());
        }
    }
    for (k, v) in &tb.obj("tag_backref").ok_or("no tag_backref")?.vals {
        if let (Some(c), Value::List(xs)) = (k.chars().next(), v) {
            let mut ps = HashSet::new();
            for x in xs {
                if let Value::List(p) = x {
                    ps.insert((ch(&p[0]), ch(&p[1])));
                }
            }
            tables.tag_backref.insert(c, ps);
        }
    }
    Ok(tables)
}

// ── str, as Python has it ───────────────────────────────────────────────────

fn cps(s: &str) -> Vec<char> {
    s.chars().collect()
}

fn length(s: &str) -> usize {
    s.chars().count()
}

/// str.lower: the table, and U+03A3 by CPython's final-sigma context.
fn lower(s: &str) -> String {
    let a = cps(s);
    let mut b = String::with_capacity(s.len());
    for (i, &c) in a.iter().enumerate() {
        if c == '\u{3A3}' {
            b.push(if final_sigma(&a, i) { 'ς' } else { 'σ' });
        } else if let Some(l) = t().lower.get(&c) {
            b.push_str(l);
        } else {
            b.push(c);
        }
    }
    b
}

fn final_sigma(a: &[char], i: usize) -> bool {
    let mut j = i as i64 - 1;
    while j >= 0 && t().ignorable.has(a[j as usize]) {
        j -= 1;
    }
    if j < 0 || !t().cased.has(a[j as usize]) {
        return false;
    }
    let mut j = i + 1;
    while j < a.len() && t().ignorable.has(a[j]) {
        j += 1;
    }
    j == a.len() || !t().cased.has(a[j])
}

fn ccc(c: char) -> i64 {
    *t().ccc.get(&c).unwrap_or(&0)
}

fn cp(c: char) -> u32 {
    c as u32
}

fn chr(u: u32) -> char {
    std::char::from_u32(u).unwrap_or('\u{FFFD}')
}

/// unicodedata.normalize("NFC"): decompose, put marks in canonical order,
/// compose, by gen.py's tables, so this compiler's Unicode never decides.
fn nfc(a: &[char]) -> Vec<char> {
    let mut d: Vec<char> = Vec::with_capacity(a.len());
    for &c in a {
        let u = cp(c);
        if (0xAC00..=0xD7A3).contains(&u) {
            let s = u - 0xAC00;
            d.push(chr(0x1100 + s / 588));
            d.push(chr(0x1161 + s % 588 / 28));
            if s % 28 != 0 {
                d.push(chr(0x11A7 + s % 28));
            }
        } else if let Some(x) = t().decomp.get(&c) {
            d.extend_from_slice(x);
        } else {
            d.push(c);
        }
    }
    for i in 1..d.len() {
        let mut j = i;
        while j > 0 && ccc(d[j]) != 0 && ccc(d[j - 1]) > ccc(d[j]) {
            d.swap(j - 1, j);
            j -= 1;
        }
    }
    let mut out: Vec<char> = Vec::with_capacity(d.len());
    let mut st: i64 = -1;
    for &c in &d {
        let cc = ccc(c);
        if st >= 0 {
            let last = ccc(out[out.len() - 1]);
            if out.len() as i64 - 1 == st || (last != 0 && last < cc) {
                let si = st as usize;
                let s = cp(out[si]);
                let u = cp(c);
                if (0x1100..0x1113).contains(&s) && (0x1161..0x1176).contains(&u) {
                    out[si] = chr(0xAC00 + ((s - 0x1100) * 21 + u - 0x1161) * 28);
                    continue;
                }
                if (0xAC00..=0xD7A3).contains(&s)
                    && (s - 0xAC00) % 28 == 0
                    && (0x11A8..=0x11C2).contains(&u)
                {
                    out[si] = chr(s + u - 0x11A7);
                    continue;
                }
                if let Some(&p) = t().compose.get(&(out[si], c)) {
                    out[si] = p;
                    continue;
                }
            }
        }
        if cc == 0 {
            st = out.len() as i64;
        }
        out.push(c);
    }
    out
}

/// str.strip() == ""
fn blank(s: &str) -> bool {
    s.chars().all(|c| t().space.has(c))
}

/// str.strip()
fn strip(s: &str) -> String {
    let a = cps(s);
    let (mut i, mut j) = (0, a.len());
    while i < j && t().space.has(a[i]) {
        i += 1;
    }
    while j > i && t().space.has(a[j - 1]) {
        j -= 1;
    }
    a[i..j].iter().collect()
}

/// str.splitlines(): "\r\n" is one break; no terminators kept.
fn splitlines(s: &str) -> Vec<String> {
    let a = cps(s);
    let mut out = Vec::new();
    let (mut start, mut i) = (0, 0);
    while i < a.len() {
        let c = a[i];
        if t().line_breaks.contains(&c) {
            out.push(a[start..i].iter().collect());
            i += if c == '\r' && i + 1 < a.len() && a[i + 1] == '\n' {
                2
            } else {
                1
            };
            start = i;
        } else {
            i += 1;
        }
    }
    if start < a.len() {
        out.push(a[start..].iter().collect());
    }
    out
}

fn take(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

// ── words and the bite key ──────────────────────────────────────────────────

fn words(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for c in nfc(&cps(&lower(text))) {
        if t().word.has(c) {
            cur.push(c);
        } else if !cur.is_empty() {
            out.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

fn bite_key(text: &str) -> Option<String> {
    let ws = words(text);
    if ws.is_empty() {
        None
    } else {
        Some(h256(&ws.join(" ")))
    }
}

fn subject_of(prop: &Obj) -> Res<String> {
    let mut four = Obj::new();
    for k in &["path", "data", "cites", "claim"] {
        four.set(k, prop.get(k).cloned().unwrap_or(Value::Null));
    }
    Ok(format!("proposal:{}", h256(&canon(&Value::Obj(four))?)))
}

// ── the scanners: the kernel's regular expressions, by hand ─────────────────

/// Python's \w: a word character or "_".
fn is_w(c: char) -> bool {
    c == '_' || t().word.has(c)
}

fn at(a: &[char], i: usize) -> char {
    if i < a.len() {
        a[i]
    } else {
        '\0'
    }
}

/// " " and one newline for each the match held: line numbers still point home.
fn kept(a: &[char], from: usize, to: usize) -> String {
    let n = a[from..to].iter().filter(|&&c| c == '\n').count();
    format!(" {}", "\n".repeat(n))
}

/// `<(script|style)\b.*?</\1\s*>|<!--.*?-->` under re.S | re.I, at i (a "<"):
/// the name folds as re.I folds it (tag_fold); the closing name equals the
/// opening one as re.I's backreference compares (tag_backref).
fn hidden_at(a: &[char], i: usize) -> Option<usize> {
    for name in &["script", "style"] {
        let nm = cps(name);
        let n = nm.len();
        let mut ok = i + 1 + n <= a.len();
        for k in 0..n {
            if !ok {
                break;
            }
            ok = t().tag_fold[&nm[k]].contains(&a[i + 1 + k]);
        }
        if !ok {
            continue;
        }
        let e = i + 1 + n;
        if e < a.len() && is_w(a[e]) {
            continue; // \b
        }
        let mut k = e;
        while k + 1 < a.len() {
            if a[k] == '<' && a[k + 1] == '/' {
                let mut same = k + 2 + n <= a.len();
                for x in 0..n {
                    if !same {
                        break;
                    }
                    same = t().tag_backref[&nm[x]].contains(&(a[i + 1 + x], a[k + 2 + x]));
                }
                if same {
                    let mut p = k + 2 + n;
                    while p < a.len() && t().space.has(a[p]) {
                        p += 1;
                    }
                    if p < a.len() && a[p] == '>' {
                        return Some(p + 1);
                    }
                }
            }
            k += 1;
        }
    }
    if at(a, i + 1) == '!' && at(a, i + 2) == '-' && at(a, i + 3) == '-' {
        let mut k = i + 4;
        while k + 2 < a.len() {
            if a[k] == '-' && a[k + 1] == '-' && a[k + 2] == '>' {
                return Some(k + 3);
            }
            k += 1;
        }
    }
    None
}

fn hidden(text: &str) -> String {
    let a = cps(text);
    let mut b = String::new();
    let mut i = 0;
    while i < a.len() {
        let m = if a[i] == '<' { hidden_at(&a, i) } else { None };
        if let Some(m) = m {
            b.push_str(&kept(&a, i, m));
            i = m;
        } else {
            b.push(a[i]);
            i += 1;
        }
    }
    b
}

/// `<[^>]*>`
fn tags(text: &str) -> String {
    let a = cps(text);
    let mut b = String::new();
    let mut i = 0;
    while i < a.len() {
        if a[i] == '<' {
            if let Some(q) = (i + 1..a.len()).find(|&k| a[k] == '>') {
                b.push_str(&kept(&a, i, q + 1));
                i = q + 1;
                continue;
            }
        }
        b.push(a[i]);
        i += 1;
    }
    b
}

fn name_stop(c: char) -> bool {
    "\t\n\u{c} <&#;".contains(c)
}

/// html.unescape: `&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)`.
fn unescape(s: &str) -> String {
    if !s.contains('&') {
        return s.to_string();
    }
    let a = cps(s);
    let mut b = String::new();
    let mut i = 0;
    while i < a.len() {
        if a[i] != '&' {
            b.push(a[i]);
            i += 1;
            continue;
        }
        let mut j = i + 1;
        if at(&a, j) == '#' {
            if is_dec(at(&a, j + 1)) {
                j += 1;
                while j < a.len() && is_dec(a[j]) {
                    j += 1;
                }
            } else if (at(&a, j + 1) == 'x' || at(&a, j + 1) == 'X') && is_hex(at(&a, j + 2)) {
                j += 2;
                while j < a.len() && is_hex(a[j]) {
                    j += 1;
                }
            } else {
                b.push('&');
                i += 1;
                continue;
            }
        } else {
            while j < a.len() && j - (i + 1) < 32 && !name_stop(a[j]) {
                j += 1;
            }
            if j == i + 1 {
                b.push('&');
                i += 1;
                continue;
            }
        }
        if at(&a, j) == ';' {
            j += 1;
        }
        b.push_str(&charref(&a[i + 1..j]));
        i = j;
    }
    b
}

fn charref(s: &[char]) -> String {
    if s[0] == '#' {
        let is_x = s[1] == 'x' || s[1] == 'X';
        let mut digits: Vec<char> = if is_x {
            s[2..].to_vec()
        } else {
            s[1..].to_vec()
        };
        while digits.last() == Some(&';') {
            digits.pop();
        }
        let mut k = 0;
        while k + 1 < digits.len() && digits[k] == '0' {
            k += 1;
        }
        let digits: String = digits[k..].iter().collect();
        let radix = if is_x { 16 } else { 10 };
        let over =
            digits.len() > 8 || u64::from_str_radix(&digits, radix).map_or(true, |n| n > 0x10FFFF);
        if over {
            return "\u{FFFD}".into();
        }
        let n = u64::from_str_radix(&digits, radix).unwrap_or(0);
        if let Some(v) = t().invalid_charrefs.get(&n) {
            return v.clone();
        }
        if (0xD800..=0xDFFF).contains(&n) {
            return "\u{FFFD}".into();
        }
        if t().invalid_codepoints.contains(&(n as u32)) {
            return String::new();
        }
        return chr(n as u32).to_string();
    }
    let whole: String = s.iter().collect();
    if let Some(v) = t().html5.get(&whole) {
        return v.clone();
    }
    let mut x = s.len() - 1;
    while x > 1 {
        let head: String = s[..x].iter().collect();
        if let Some(v) = t().html5.get(&head) {
            let tail: String = s[x..].iter().collect();
            return format!("{}{}", v, tail);
        }
        x -= 1;
    }
    format!("&{}", whole)
}

fn html_text(text: &str) -> String {
    unescape(&tags(&hidden(text)))
}

const KEYWORDS: [&str; 6] = ["def", "function", "sub", "class", "func", "fn"];

fn ident_head(c: char) -> bool {
    c == '_' || c.is_ascii_alphabetic()
}

fn ident_tail(c: char) -> bool {
    ident_head(c) || is_dec(c)
}

/// re.findall of `\b(?:def|function|sub|class|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)`.
fn defines(text: &str) -> Vec<String> {
    let a = cps(text);
    let mut out = Vec::new();
    let mut p = 0;
    'outer: while p < a.len() {
        if p == 0 || !is_w(a[p - 1]) {
            for kw in KEYWORDS.iter() {
                let kr = cps(kw);
                let mut k = 0;
                while k < kr.len() && at(&a, p + k) == kr[k] {
                    k += 1;
                }
                if k < kr.len() {
                    continue;
                }
                let mut q = p + kr.len();
                let s0 = q;
                while q < a.len() && t().space.has(a[q]) {
                    q += 1;
                }
                if q == s0 || !(q < a.len() && ident_head(a[q])) {
                    continue;
                }
                let start = q;
                while q < a.len() && ident_tail(a[q]) {
                    q += 1;
                }
                out.push(a[start..q].iter().collect());
                p = q;
                continue 'outer;
            }
        }
        p += 1;
    }
    out
}

/// How many times `\bname\b` occurs (name is an identifier: \w all through).
fn named(text: &str, name: &str) -> usize {
    let (a, b) = (cps(text), cps(name));
    let (mut n, mut p) = (0, 0);
    while p + b.len() <= a.len() {
        let mut k = 0;
        while k < b.len() && a[p + k] == b[k] {
            k += 1;
        }
        if k == b.len()
            && (p == 0 || !is_w(a[p - 1]))
            && (p + b.len() == a.len() || !is_w(a[p + b.len()]))
        {
            n += 1;
            p += b.len();
        } else {
            p += 1;
        }
    }
    n
}

// ── word forms, holds, echo ─────────────────────────────────────────────────

/// kernel.py's stem: an English word's plain form; only words of ASCII letters.
fn stem(w: &str) -> String {
    if w.len() < 3 || !w.bytes().all(|c| c.is_ascii_alphabetic()) {
        return w.to_string();
    }
    let mut s = w.to_string();
    let n = s.len();
    if n > 4 && (s.ends_with("ies") || s.ends_with("ied")) {
        s = format!("{}y", &s[..n - 3]);
    } else if n > 4 && s.ends_with("ing") {
        s.truncate(n - 3);
    } else if n > 3 && s.ends_with("ed") {
        s.truncate(n - 2);
    } else if n > 3 && s.ends_with('s') && !s.ends_with("ss") {
        s.truncate(n - 1);
    }
    let n = s.len();
    let b = s.as_bytes();
    if n > 3 && b[n - 1] == b[n - 2] && !"aeiouls".contains(b[n - 1] as char) {
        s.truncate(n - 1);
    }
    let n = s.len();
    if n > 2 && s.ends_with('e') {
        s.truncate(n - 1);
    }
    s
}

/// Words, and each one's plain form.
fn forms(ws: &[String]) -> HashSet<String> {
    let mut out = HashSet::new();
    for w in ws {
        out.insert(w.clone());
        out.insert(stem(w));
    }
    out
}

fn holds(w: &str, toks: &HashSet<String>) -> bool {
    if toks.contains(w) || toks.contains(&stem(w)) {
        return true;
    }
    if length(w) < 4 || !w.chars().any(|c| t().digit.has(c)) {
        return false;
    }
    toks.iter().any(|tk| tk.ends_with(w) || tk.starts_with(w))
}

fn echo(bite: &str, text: &str) -> bool {
    let (ws, ts) = (words(bite), words(text));
    let n = ws.len().min(t().echo_run);
    if n < 3 {
        return false;
    }
    let runs: HashSet<String> = (0..=ts.len().saturating_sub(n))
        .filter(|&i| i + n <= ts.len())
        .map(|i| ts[i..i + n].join(" "))
        .collect();
    (0..=ws.len() - n).any(|i| runs.contains(&ws[i..i + n].join(" ")))
}

// ── the pile ────────────────────────────────────────────────────────────────

#[derive(Clone)]
struct Chunk {
    path: String,
    line: usize,
    text: String,
    id: String,
}

impl Chunk {
    fn new(path: &str, line: usize, text: String) -> Chunk {
        let id = h256(&text);
        Chunk {
            path: path.to_string(),
            line,
            text,
            id,
        }
    }

    fn json(&self) -> Value {
        Value::Obj(obj(&[
            ("path", s(&self.path)),
            ("line", int(self.line as i64)),
            ("text", s(&self.text)),
            ("id", s(&self.id)),
        ]))
    }
}

/// Path.rglob("*"): every entry under dir, as its parts; a link to a folder
/// is listed, never entered.
fn walk(dir: &Path, parts: &[String], out: &mut Vec<Vec<String>>) {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for e in entries.flatten() {
        let name = e.file_name().to_string_lossy().into_owned();
        let mut mine = parts.to_vec();
        mine.push(name.clone());
        out.push(mine.clone());
        if e.file_type().map_or(false, |ft| ft.is_dir()) {
            walk(&dir.join(&name), &mine, out);
        }
    }
}

fn suffix(name: &str) -> &str {
    match name.rfind('.') {
        Some(i) if i > 0 && i < name.len() - 1 => &name[i..],
        _ => "",
    }
}

fn chunks(pile: &str) -> Vec<Chunk> {
    let mut all = Vec::new();
    walk(Path::new(pile), &[], &mut all);
    all.sort(); // part by part, the shorter first: as Python sorts paths
    let mut out = Vec::new();
    for rel in &all {
        let mut p = PathBuf::from(pile);
        for part in rel {
            p.push(part);
        }
        let st = match fs::metadata(&p) {
            Ok(st) => st,
            Err(_) => continue,
        };
        if !st.is_file() || rel.iter().any(|part| part.starts_with('.')) || st.len() > t().max_file
        {
            continue;
        }
        let raw = match fs::read(&p) {
            Ok(r) => r,
            Err(_) => continue,
        };
        if raw.iter().take(t().sniff).any(|&b| b == 0) {
            continue;
        }
        let mut text = match String::from_utf8(raw) {
            Ok(x) => x,
            Err(_) => continue,
        };
        let suf = lower(suffix(&rel[rel.len() - 1]));
        if suf == ".html" || suf == ".htm" {
            text = html_text(&text);
        }
        let rel_path = rel.join("/");
        let mut lines = splitlines(&text);
        lines.push(String::new());
        let mut para: Vec<String> = Vec::new();
        let (mut start, mut size) = (1, 0);
        for (i0, line) in lines.iter().enumerate() {
            let i = i0 + 1;
            if !para.is_empty() && (blank(line) || size + length(line) > t().max_chunk) {
                out.push(Chunk::new(&rel_path, start, para.join("\n")));
                para.clear();
                size = 0;
            }
            if !blank(line) {
                if para.is_empty() {
                    start = i;
                }
                para.push(take(line, t().max_chunk));
                size += length(&para[para.len() - 1]) + 1;
            }
        }
    }
    out
}

// ── dates ───────────────────────────────────────────────────────────────────

/// How many ASCII digits run from i.
fn digits(tx: &[char], i: usize) -> usize {
    let mut j = i;
    while j < tx.len() && is_dec(tx[j]) {
        j += 1;
    }
    j - i
}

fn date(y: &str, m: &str, d: &str) -> String {
    let mut ok = (y.starts_with("19") || y.starts_with("20"))
        && ("01"..="12").contains(&m)
        && ("01"..="31").contains(&d);
    if ok && m == "02" {
        let n: u32 = y.parse().unwrap_or(0);
        ok = d <= if n % 4 == 0 && (n % 100 != 0 || n % 400 == 0) { "29" } else { "28" };
    } else if ok && ["04", "06", "09", "11"].contains(&m) {
        ok = d <= "30";
    }
    if ok {
        format!("{}{}{}", y, m, d)
    } else {
        String::new()
    }
}

/// kernel.py's _day_month: a/b/y read only when it can't be misread.
fn day_month(a: &str, b: &str, y: &str) -> String {
    let x: i64 = a.parse().unwrap_or(0);
    let z: i64 = b.parse().unwrap_or(0);
    if x == z || (x > 12 && z <= 12) {
        return date(y, &format!("{:02}", z), &format!("{:02}", x));
    }
    if z > 12 && x <= 12 {
        return date(y, &format!("{:02}", x), &format!("{:02}", z));
    }
    String::new()
}

/// How many characters from i are an http(s) address, or 0.
fn web_address(tx: &[char], i: usize) -> usize {
    for scheme in &["http://", "https://"] {
        let sr = cps(scheme);
        if i + sr.len() <= tx.len() && tx[i..i + sr.len()] == sr[..] {
            let mut j = i + sr.len();
            while j < tx.len() && !t().space.has(tx[j]) {
                j += 1;
            }
            return j - i;
        }
    }
    0
}

/// kernel.py's newest: the latest date written in text, as YYYYMMDD, or "".
fn newest(text: &str) -> String {
    let tx = cps(text);
    let sub = |a: usize, b: usize| -> String {
        let b = b.min(tx.len());
        if a > b {
            String::new()
        } else {
            tx[a..b].iter().collect()
        }
    };
    let mut best = String::new();
    let mut i = 0;
    while i < tx.len() {
        let url = web_address(&tx, i);
        if url > 0 {
            i += url;
            continue;
        }
        let mut n = digits(&tx, i);
        if n == 0 {
            i += 1;
            continue;
        }
        let mut got = String::new();
        if n == 8 {
            got = date(&sub(i, i + 4), &sub(i + 4, i + 6), &sub(i + 6, i + 8));
        } else if n == 4 && sub(i + 4, i + 5) == "-" && digits(&tx, i + 5) == 2 {
            if sub(i + 7, i + 8) == "-" && digits(&tx, i + 8) == 2 {
                got = date(&sub(i, i + 4), &sub(i + 5, i + 7), &sub(i + 8, i + 10));
                if !got.is_empty() {
                    n = 10;
                }
            }
        } else if n <= 2 && (sub(i + n, i + n + 1) == "/" || sub(i + n, i + n + 1) == ".") {
            let sep = sub(i + n, i + n + 1);
            let m = digits(&tx, i + n + 1);
            let j = i + n + 1 + m;
            if (1..=2).contains(&m) && sub(j, j + 1) == sep && digits(&tx, j + 1) == 4 {
                got = day_month(&sub(i, i + n), &sub(i + n + 1, j), &sub(j + 1, j + 5));
                if !got.is_empty() {
                    n = j + 5 - i;
                }
            }
        }
        if got > best {
            best = got;
        }
        i += n;
    }
    best
}

/// kernel.py's dates: each chunk's date, carried down its file; 0 for none.
fn dates(pile: &[Chunk]) -> Vec<i64> {
    let mut out = Vec::with_capacity(pile.len());
    let mut path: Option<&str> = None;
    let mut cur = String::new();
    for c in pile {
        if path != Some(c.path.as_str()) {
            path = Some(&c.path);
            cur = newest(&c.path);
        }
        let tdate = newest(&c.text);
        if tdate > cur {
            cur = tdate;
        }
        out.push(if cur.is_empty() {
            0
        } else {
            cur.parse().unwrap_or(0)
        });
    }
    out
}

// ── an exact rational, for the rank's scores ─────────────────────────────────

/// A whole number of any size, little-endian base 2^32: enough for adding
/// fractions and comparing them by cross-multiplying, which is all a score needs.
#[derive(Clone, Debug)]
struct Big(Vec<u32>);

impl Big {
    fn from(n: u64) -> Big {
        let mut b = Big(vec![n as u32, (n >> 32) as u32]);
        b.trim();
        b
    }

    fn trim(&mut self) {
        while self.0.len() > 1 && *self.0.last().unwrap() == 0 {
            self.0.pop();
        }
    }

    fn add(&self, o: &Big) -> Big {
        let n = self.0.len().max(o.0.len());
        let mut out = Vec::with_capacity(n + 1);
        let mut carry = 0u64;
        for i in 0..n {
            let a = *self.0.get(i).unwrap_or(&0) as u64;
            let b = *o.0.get(i).unwrap_or(&0) as u64;
            let sum = a + b + carry;
            out.push(sum as u32);
            carry = sum >> 32;
        }
        out.push(carry as u32);
        let mut r = Big(out);
        r.trim();
        r
    }

    fn mul(&self, o: &Big) -> Big {
        let mut out = vec![0u32; self.0.len() + o.0.len()];
        for (i, &a) in self.0.iter().enumerate() {
            let mut carry = 0u64;
            for (j, &b) in o.0.iter().enumerate() {
                let cur = out[i + j] as u64 + a as u64 * b as u64 + carry;
                out[i + j] = cur as u32;
                carry = cur >> 32;
            }
            let mut k = i + o.0.len();
            while carry > 0 {
                let cur = out[k] as u64 + carry;
                out[k] = cur as u32;
                carry = cur >> 32;
                k += 1;
            }
        }
        let mut r = Big(out);
        r.trim();
        r
    }

    fn cmp(&self, o: &Big) -> Ordering {
        if self.0.len() != o.0.len() {
            return self.0.len().cmp(&o.0.len());
        }
        for i in (0..self.0.len()).rev() {
            if self.0[i] != o.0[i] {
                return self.0[i].cmp(&o.0[i]);
            }
        }
        Ordering::Equal
    }
}

#[derive(Clone, Debug)]
struct Rat {
    n: Big,
    d: Big,
}

impl Rat {
    fn zero() -> Rat {
        Rat {
            n: Big::from(0),
            d: Big::from(1),
        }
    }

    fn plus_unit(&self, den: u64) -> Rat {
        let d = Big::from(den);
        Rat {
            n: self.n.mul(&d).add(&self.d),
            d: self.d.mul(&d),
        }
    }

    fn cmp(&self, o: &Rat) -> Ordering {
        self.n.mul(&o.d).cmp(&o.n.mul(&self.d))
    }
}

// ── rank and look ───────────────────────────────────────────────────────────

type Alias = HashMap<String, Vec<String>>;

/// A case's words list, as the vectors hold it ({} when it has none).
fn alias_of(m: &Obj) -> Alias {
    let mut out = Alias::new();
    if let Some(a) = m.obj("alias") {
        for k in &a.keys {
            out.insert(
                k.clone(),
                a.list(k)
                    .iter()
                    .filter_map(|x| x.as_str().map(String::from))
                    .collect(),
            );
        }
    }
    out
}

/// Their word holds where it, or a word their list reads it as, does.
fn held_by(w: &str, toks: &HashSet<String>, al: &Alias) -> bool {
    holds(w, toks)
        || al
            .get(w)
            .map_or(false, |xs| xs.iter().any(|x| holds(x, toks)))
}

fn toks(c: &Chunk) -> HashSet<String> {
    let mut both = words(&c.text);
    both.extend(words(&c.path)); // a folder's name is the person's word too
    forms(&both)
}

/// dict.fromkeys(words) less FUNCTION: each content word once, in order.
fn unique_words(ws: &[String]) -> Vec<String> {
    let mut seen = HashSet::new();
    let mut want = Vec::new();
    for w in ws {
        if seen.insert(w.clone()) && !t().function.contains(w) {
            want.push(w.clone());
        }
    }
    want
}

fn rank(pile: &[Chunk], bite: &str, al: &Alias) -> Vec<Chunk> {
    let want = unique_words(&words(bite));
    if want.is_empty() {
        return vec![];
    }
    let when = dates(pile);
    let mut held: Vec<(usize, HashSet<String>, i64)> = Vec::new();
    for (k, c) in pile.iter().enumerate() {
        let tk = toks(c);
        let h: HashSet<String> = want
            .iter()
            .filter(|w| held_by(w, &tk, al))
            .cloned()
            .collect();
        if h.len() * t().hold_den >= t().hold_num * want.len() {
            held.push((k, h, when[k]));
        }
    }
    let mut df: HashMap<&str, u64> = HashMap::new();
    for w in &want {
        df.insert(
            w,
            held.iter().filter(|(_, h, _)| h.contains(w)).count() as u64,
        );
    }
    let mut copies: HashMap<&str, usize> = HashMap::new();
    for c in pile {
        *copies.entry(&c.id).or_insert(0) += 1;
    }
    let mut rows: Vec<(Rat, usize, i64)> = Vec::new();
    for (k, h, d) in &held {
        if h.is_empty() {
            continue;
        }
        let mut sc = Rat::zero();
        for w in h {
            sc = sc.plus_unit(df[w.as_str()]);
        }
        rows.push((sc, *k, *d));
    }
    rows.sort_by(|x, y| {
        let (cx, cy) = (&pile[x.1], &pile[y.1]);
        y.0.cmp(&x.0)
            // what was said once before what is said every week
            .then(copies[cx.id.as_str()].cmp(&copies[cy.id.as_str()]))
            .then(y.2.cmp(&x.2))
            .then(cx.path.cmp(&cy.path))
            // a log grows downward: on one date, the later line is the newer one
            .then(if x.2 != 0 {
                cy.line.cmp(&cx.line)
            } else {
                cx.line.cmp(&cy.line)
            })
    });
    let mut out = Vec::new();
    let mut shown = HashSet::new(); // one id, one place
    for (_, k, _) in &rows {
        if out.len() == t().top {
            break;
        }
        if shown.insert(pile[*k].id.clone()) {
            out.push(pile[*k].clone());
        }
    }
    out
}

fn hint(why: String, where_: Option<String>, next: Option<&str>) -> Value {
    let mut m = Obj::new();
    m.set("why", Value::Str(why));
    if let Some(w) = where_ {
        m.set("where", Value::Str(w));
    }
    if let Some(n) = next {
        m.set("next", s(n));
    }
    Value::Obj(m)
}

fn look(pile: &[Chunk], bite: &str, served: &[&Chunk], al: &Alias) -> Vec<Value> {
    let mut out = Vec::new();
    let ws = words(bite);
    let want = unique_words(&ws);
    if want.is_empty() {
        out.push(hint(
            "every word is a common one: name the thing you mean".into(),
            None,
            None,
        ));
    }
    let mut every = HashSet::new();
    for c in pile {
        every.extend(toks(c));
    }
    let absent: Vec<&String> = want.iter().filter(|w| !held_by(w, &every, al)).collect();
    for w in &want {
        // said, so a match their list made is never taken for theirs
        if holds(w, &every) {
            continue;
        }
        let read: Vec<&str> = al
            .get(w.as_str())
            .map(|xs| {
                xs.iter()
                    .filter(|x| holds(x, &every))
                    .map(String::as_str)
                    .collect()
            })
            .unwrap_or_default();
        if !read.is_empty() {
            out.push(hint(
                format!("read {} as {}, from your words list", w, read.join(", ")),
                None,
                None,
            ));
        }
    }
    if !absent.is_empty() {
        let names: Vec<&str> = absent.iter().map(|x| x.as_str()).collect();
        out.push(hint(
            format!("no file in your folder has {}", names.join(", ")),
            Some("it may be called something else there".into()),
            Some(&t().next["other words"]),
        ));
    }
    for c in served {
        let mut seen = HashSet::new();
        for name in defines(&c.text) {
            if !seen.insert(name.clone()) {
                continue;
            }
            let mut uses: Vec<&str> = pile
                .iter()
                // `d is not c`: a served chunk is a copy of the pile's, so its place says which it is
                .filter(|d| !(d.path == c.path && d.line == c.line) && named(&d.text, &name) > 0)
                .map(|d| d.path.as_str())
                .collect();
            if named(&c.text, &name) > 1 {
                uses.push(&c.path);
            }
            uses.sort();
            uses.dedup();
            let where_ = if uses.is_empty() {
                "nothing else in your folder names it".to_string()
            } else {
                format!("also named in {}", uses.join(", "))
            };
            out.push(hint(
                format!("{} is defined at {}:{}", name, c.path, c.line),
                Some(where_),
                Some(&t().next["unused"]),
            ));
        }
    }
    if !ws.is_empty() && t().make.contains(&ws[0]) {
        out.push(hint(
            "this asks for something made".into(),
            None,
            Some(&t().next["made"]),
        ));
    }
    out
}

// ── the door ────────────────────────────────────────────────────────────────

fn door(prop: Option<&Value>, served: &HashSet<String>) -> Option<&'static str> {
    let p = match prop {
        Some(Value::Obj(p))
            if p.keys.len() == 4 && ["path", "data", "cites", "claim"].iter().all(|k| p.has(k)) =>
        {
            p
        }
        _ => return Some("a row is exactly {path, data, cites, claim}"),
    };
    match p.str("path") {
        Some(path)
            if !path.is_empty()
                && !path.starts_with('/')
                && !path.starts_with('\\')
                && !path.split('/').any(|x| x == "..") => {}
        _ => return Some("a path is plain and relative, inside the box"),
    }
    let cites = match (p.get("data"), p.get("cites")) {
        (Some(Value::Str(_)), Some(Value::List(c))) => c,
        _ => return Some("data is text and cites a list"),
    };
    match p.str("claim") {
        Some(c) if !blank(c) => {}
        _ => return Some("a claim says why"),
    }
    for c in cites {
        match c.as_str() {
            Some(x) if served.contains(x) => {}
            _ => return Some("a cite that the last bite didn't serve"),
        }
    }
    None
}

// ── the record ──────────────────────────────────────────────────────────────

#[derive(Default)]
struct Record {
    rows: Vec<Obj>,
    breaks: Vec<String>,
}

fn read_bytes(raw: Vec<u8>) -> Res<Record> {
    let mut r = Record::default();
    let data = String::from_utf8(raw).map_err(|_| "the record is not UTF-8".to_string())?;
    if !data.is_empty() && !data.ends_with('\n') {
        r.breaks
            .push("torn tail: the last line is unterminated; a human looks first".into());
        return Ok(r);
    }
    let mut prev = t().genesis.clone();
    let lines: Vec<&str> = if data.is_empty() {
        vec![]
    } else {
        data[..data.len() - 1].split('\n').collect()
    };
    for (i, line) in lines.iter().enumerate() {
        let m = match loads(line) {
            Ok(Value::Obj(m)) if t().row_keys.iter().all(|k| m.has(k)) => m,
            _ => {
                r.breaks
                    .push(format!("line {}: garbled, not a record row", i));
                continue;
            }
        };
        let mut body = m.clone();
        body.del("hash");
        let hash = canon(&Value::Obj(body))
            .map(|c| h256(&c))
            .unwrap_or_default();
        let n = m.get("n").cloned().unwrap_or(Value::Null);
        if m.str("prev") != Some(prev.as_str()) || m.str("hash") != Some(hash.as_str()) {
            r.breaks.push(format!("row {}: chain broken", py_str(&n)));
        }
        if !n.is_int() || n.as_int() != Some(r.rows.len() as i128) {
            r.breaks.push(format!(
                "row {}: out of place, it is row {}",
                py_repr(&n),
                r.rows.len()
            ));
        }
        prev = m.get("hash").map(py_str).unwrap_or_default();
        r.rows.push(m);
    }
    Ok(r)
}

/// The record read as kernel.py reads it: without a lock.
fn read_record(path: &Path) -> Res<Record> {
    match fs::read(path) {
        Ok(raw) => read_bytes(raw),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Record::default()),
        Err(e) => Err(io_err(e)),
    }
}

#[cfg(unix)]
fn lock_file(f: &File) -> Res<()> {
    use std::os::unix::io::AsRawFd;
    extern "C" {
        fn flock(fd: i32, op: i32) -> i32;
    }
    const LOCK_EX: i32 = 2;
    // the lock kernel.py takes: a blocking exclusive flock on the record
    if unsafe { flock(f.as_raw_fd(), LOCK_EX) } != 0 {
        return Err("the record could not be locked".into());
    }
    Ok(())
}

#[cfg(not(unix))]
fn lock_file(_f: &File) -> Res<()> {
    Ok(()) // no flock there, and kernel.py's Windows lock is its own
}

fn append_row(box_: &Path, ts: &str, kind: &str, who: &str, fields: &Obj) -> Res<Obj> {
    let path = box_.join("record.jsonl");
    let mut f = OpenOptions::new()
        .read(true)
        .append(true)
        .create(true)
        .open(&path)
        .map_err(io_err)?;
    lock_file(&f)?;
    let mut raw = Vec::new();
    f.read_to_end(&mut raw).map_err(io_err)?; // the true tail, read under the lock
    let r = read_bytes(raw)?;
    if !r.breaks.is_empty() {
        return Err(r.breaks.join("; "));
    }
    let sealed_row = kind == "seal" && who == "human";
    let mut row = obj(&[
        ("n", int(r.rows.len() as i64)),
        ("kind", s(kind)),
        ("who", s(who)),
        ("family", s("kernel")),
        (
            "standing",
            s(if sealed_row { "sealed" } else { "unattested" }),
        ),
        ("version", s(version())),
        ("ts", s(ts)),
    ]);
    let mut rest = fields.clone();
    row.set("where", rest.get("where").cloned().unwrap_or(Value::Null));
    rest.del("where");
    for k in &rest.keys {
        row.set(k, rest.vals[k].clone());
    }
    let prev = r
        .rows
        .last()
        .and_then(|x| x.get("hash").cloned())
        .unwrap_or_else(|| s(&t().genesis));
    row.set("prev", prev);
    let hash = h256(&canon(&Value::Obj(row.clone()))?);
    row.set("hash", Value::Str(hash));
    f.write_all(format!("{}\n", canon(&Value::Obj(row.clone()))?).as_bytes())
        .map_err(io_err)?;
    f.sync_all().map_err(io_err)?;
    drop(f);
    if r.rows.is_empty() {
        // the new name survives a crash; a file system that can't sync a folder: as kernel.py without O_DIRECTORY
        if let Ok(d) = File::open(box_) {
            let _ = d.sync_all();
        }
    }
    Ok(row)
}

// ── the box: theirs ─────────────────────────────────────────────────────────

fn config(box_: &Path) -> Res<Obj> {
    let raw = fs::read_to_string(box_.join("kernel.json")).map_err(io_err)?;
    match loads(&raw)? {
        Value::Obj(o) => Ok(o),
        _ => Err("kernel.json is not an object".into()),
    }
}

/// Lexically normalized: "." dropped, ".." folded, as Go's Clean and Java's normalize.
fn normalize(p: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for c in p.components() {
        match c {
            Component::ParentDir => {
                if !out.pop() {
                    out.push("..");
                }
            }
            Component::CurDir => {}
            other => out.push(other.as_os_str()),
        }
    }
    out
}

/// Path.resolve(): absolute, links resolved as far as the path exists.
fn resolved(p: &str) -> PathBuf {
    let abs = match std::env::current_dir() {
        Ok(cwd) => normalize(&cwd.join(p)),
        Err(_) => normalize(Path::new(p)),
    };
    let mut probe = abs.clone();
    let mut tail: Vec<std::ffi::OsString> = Vec::new();
    while fs::symlink_metadata(&probe).is_err() {
        match (probe.file_name(), probe.parent()) {
            (Some(name), Some(parent)) => {
                tail.insert(0, name.to_os_string());
                probe = parent.to_path_buf();
            }
            _ => break,
        }
    }
    let mut real = fs::canonicalize(&probe).unwrap_or(probe);
    for t in tail {
        real.push(t);
    }
    real
}

fn inside(p: &str, box_: &str) -> bool {
    let a = resolved(p);
    let b = resolved(box_);
    a == b || a.starts_with(&b)
}

fn py_err(e: &std::io::Error) -> &'static str {
    match e.kind() {
        std::io::ErrorKind::NotFound => "FileNotFoundError",
        std::io::ErrorKind::PermissionDenied => "PermissionError",
        _ => "OSError",
    }
}

/// `path.stat().st_mode & 0o077` on POSIX; nothing elsewhere.
fn mode_beyond_owner(path: &str) -> Result<bool, std::io::Error> {
    let st = fs::metadata(path)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        return Ok(st.permissions().mode() & 0o077 != 0);
    }
    #[cfg(not(unix))]
    {
        let _ = st;
        Ok(false)
    }
}

fn read_key(path: &str, box_: &str) -> Result<Vec<u8>, String> {
    if inside(path, box_) {
        return Err("the key can't live inside the box".into());
    }
    match mode_beyond_owner(path) {
        Err(e) => return Err(format!("the key could not be read: {}", py_err(&e))),
        Ok(true) => {
            return Err(format!(
                "{} is readable beyond its owner; chmod 600 it",
                path
            ))
        }
        Ok(false) => {}
    }
    let raw = fs::read(path).map_err(|e| format!("the key could not be read: {}", py_err(&e)))?;
    let text = String::from_utf8(raw)
        .map_err(|_| "the key could not be read: UnicodeDecodeError".to_string())?;
    unhex(&strip(&text)).map_err(|_| "the key could not be read: ValueError".to_string())
}

/// kernel.py's parse_words: their words list as {their word: the folder's
/// words}, in the order they came, or why not.
fn parse_words(text: &str) -> Result<Vec<(String, Vec<String>)>, String> {
    let mut out: Vec<(String, Vec<String>)> = Vec::new();
    for (n0, line) in splitlines(text).iter().enumerate() {
        let st = strip(line);
        if st.is_empty() || st.starts_with('#') {
            continue;
        }
        let (left, right, eq) = match st.find('=') {
            Some(i) => (&st[..i], &st[i + 1..], true),
            None => (st.as_str(), "", false),
        };
        let theirs: Vec<Vec<String>> = right.split(',').map(words).collect();
        let lw = words(left);
        if !eq || lw.len() != 1 || theirs.iter().any(|x| x.len() != 1) {
            return Err(format!(
                "words list line {}: one word = one or more words, a comma between",
                n0 + 1
            ));
        }
        let her = &lw[0];
        if !out.iter().any(|(k, _)| k == her) {
            out.push((her.clone(), vec![]));
        }
        let mine = &mut out.iter_mut().find(|(k, _)| k == her).unwrap().1;
        for tk in theirs {
            if &tk[0] != her && !mine.contains(&tk[0]) {
                mine.push(tk[0].clone());
            }
        }
    }
    let mut res = Vec::new();
    for (k, mut v) in out {
        if v.is_empty() {
            continue;
        }
        v.sort();
        res.push((k, v));
    }
    Ok(res)
}

fn alias_from(list: &[(String, Vec<String>)]) -> Alias {
    list.iter().cloned().collect()
}

fn alias_json(list: &[(String, Vec<String>)]) -> Value {
    let mut o = Obj::new();
    for (k, v) in list {
        o.set(k, Value::List(v.iter().map(|x| s(x)).collect()));
    }
    Value::Obj(o)
}

/// kernel.py's read_words: (the list, its SHA-256), or why not, kept like the key.
fn read_words(path: &str, box_: &str) -> Result<(Alias, String), String> {
    if inside(path, box_) {
        return Err("the words list can't live inside the box".into());
    }
    match mode_beyond_owner(path) {
        Err(e) => return Err(format!("the words list could not be read: {}", py_err(&e))),
        Ok(true) => {
            return Err(format!(
                "{} is readable beyond its owner; chmod 600 it",
                path
            ))
        }
        Ok(false) => {}
    }
    let raw =
        fs::read(path).map_err(|e| format!("the words list could not be read: {}", py_err(&e)))?;
    let text = String::from_utf8(raw.clone())
        .map_err(|_| "the words list could not be read: UnicodeDecodeError".to_string())?;
    let parsed = parse_words(&text)?;
    Ok((alias_from(&parsed), sha256hex(&raw)))
}

fn refuse(msg: &str) -> i32 {
    eprintln!("{}", msg);
    REFUSED
}

#[cfg(unix)]
fn random_bytes(n: usize) -> Res<Vec<u8>> {
    let mut out = vec![0u8; n];
    File::open("/dev/urandom")
        .and_then(|mut f| f.read_exact(&mut out))
        .map_err(io_err)?;
    Ok(out)
}

#[cfg(windows)]
fn random_bytes(n: usize) -> Res<Vec<u8>> {
    #[link(name = "bcrypt")]
    extern "system" {
        fn BCryptGenRandom(h: *mut std::ffi::c_void, buf: *mut u8, len: u32, flags: u32) -> i32;
    }
    let mut out = vec![0u8; n];
    // BCRYPT_USE_SYSTEM_PREFERRED_RNG
    if unsafe { BCryptGenRandom(std::ptr::null_mut(), out.as_mut_ptr(), n as u32, 2) } != 0 {
        return Err("no random bytes".into());
    }
    Ok(out)
}

#[cfg(not(any(unix, windows)))]
fn random_bytes(_n: usize) -> Res<Vec<u8>> {
    Err("no random bytes on this platform".into())
}

fn create_key(key: &str, hex_key: &str) -> Res<()> {
    let mut o = OpenOptions::new();
    o.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        o.mode(0o600);
    }
    let mut f = o.open(key).map_err(io_err)?;
    f.write_all(format!("{}\n", hex_key).as_bytes())
        .map_err(io_err)
}

fn init_box(box_: &str, pile: &str, key: &str, ts: &str, wl: Option<&str>) -> Res<i32> {
    let bp = Path::new(box_);
    if bp.join("record.jsonl").exists() {
        return Ok(refuse("refused: this box already has a record"));
    }
    if !fs::metadata(pile).map_or(false, |st| st.is_dir()) {
        return Ok(refuse(&format!("refused: {} is not a folder", pile)));
    }
    if inside(key, box_) {
        return Ok(refuse("refused: the key can't live inside the box"));
    }
    if let Some(w) = wl {
        if let Err(why) = read_words(w, box_) {
            return Ok(refuse(&format!("refused: {}", why)));
        }
    }
    if fs::symlink_metadata(key).is_err() {
        if let Some(parent) = Path::new(key).parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent).map_err(io_err)?;
            }
        }
        create_key(key, &hex(&random_bytes(32)?))?;
    }
    fs::create_dir_all(bp).map_err(io_err)?;
    let mut cfg = obj(&[
        (
            "pile",
            Value::Str(resolved(pile).to_string_lossy().into_owned()),
        ),
        (
            "key",
            Value::Str(resolved(key).to_string_lossy().into_owned()),
        ),
    ]);
    if let Some(w) = wl {
        cfg.set(
            "words",
            Value::Str(resolved(w).to_string_lossy().into_owned()),
        );
    }
    fs::write(
        bp.join("kernel.json"),
        format!("{}\n", dumps_default(&Value::Obj(cfg.clone()), true)),
    )
    .map_err(io_err)?;
    let pile_sha = h256(cfg.str("pile").unwrap_or(""));
    let row = append_row(
        bp,
        ts,
        "boot",
        "kernel",
        &obj(&[("loop", s("open")), ("pile_sha256", Value::Str(pile_sha))]),
    )?;
    let hash = row.str("hash").unwrap_or("");
    println!(
        "ready: record started, row {} {}",
        py_str(row.get("n").unwrap_or(&Value::Null)),
        &hash[..16.min(hash.len())]
    );
    Ok(ALIVE)
}

// ── the loop ────────────────────────────────────────────────────────────────

/// A dict of rows by subject: a later row for the same subject takes the
/// place of the first, as Python's dict does.
#[derive(Default)]
struct BySubject {
    order: Vec<String>,
    rows: HashMap<String, Obj>,
}

impl BySubject {
    fn put(&mut self, subj: &str, r: Obj) {
        if !self.rows.contains_key(subj) {
            self.order.push(subj.to_string());
        }
        self.rows.insert(subj.to_string(), r);
    }

    fn has(&self, subj: &str) -> bool {
        self.rows.contains_key(subj)
    }
}

fn eq_ct(a: &str, b: &str) -> bool {
    // hmac.compare_digest: the same time whatever differs
    let (a, b) = (a.as_bytes(), b.as_bytes());
    let mut diff = (a.len() ^ b.len()) as u8;
    for i in 0..a.len().min(b.len()) {
        diff |= a[i] ^ b[i];
    }
    diff == 0
}

/// Each proposal a seal row holds, by subject, only while its proof holds
/// under the person's key. With act "decline", the same for the person's No.
fn sealed(box_: &str, rows: &[Obj], act: &str) -> Res<BySubject> {
    let cfg = config(Path::new(box_))?;
    let key = read_key(cfg.str("key").unwrap_or(""), box_).ok();
    let mut out = BySubject::default();
    for r in rows {
        let key = match (&key, r.str("kind")) {
            (Some(k), Some(kind)) if kind == act => k,
            _ => continue,
        };
        let subj = r.get("subject").map(py_str).unwrap_or_default();
        let asked = if act == "seal" && r.has("bite_key") {
            match r.str("bite_key") {
                Some(a) => Some(a),
                None => continue,
            }
        } else {
            None
        };
        let want = proof(key, &subj, act, asked);
        let got = r.get("proof").map(py_str).unwrap_or_else(|| "None".into());
        if eq_ct(&want, &got) {
            out.put(&subj, r.clone());
        }
    }
    Ok(out)
}

fn refused_breaks(r: &Record) -> bool {
    if r.breaks.is_empty() {
        return false;
    }
    eprintln!("refused:\n  {}", r.breaks.join("\n  "));
    true
}

fn prop_file(box_: &Path, subj: &str) -> PathBuf {
    box_.join("proposals").join(format!("{}.json", &subj[9..]))
}

/// The question a proposal was last made under, from the record: the bite its
/// last passing proposal row names (before row `before`, if given). None when
/// the record names none.
fn proposed_under(rows: &[Obj], subj: &str, before: Option<i128>) -> Option<String> {
    let mut last: Option<&Obj> = None;
    for r in rows {
        if let Some(b) = before {
            if r.get("n").and_then(Value::as_int).map_or(true, |n| n >= b) {
                break;
            }
        }
        if r.str("kind") == Some("proposal")
            && r.str("subject") == Some(subj)
            && r.str("verdict") == Some("pass")
        {
            last = Some(r);
        }
    }
    let i = last?.get("bite_row")?;
    let i = if i.is_int() { i.as_int()? } else { return None };
    if i < 0 || i >= rows.len() as i128 {
        return None;
    }
    let b = &rows[i as usize];
    if b.str("kind") != Some("bite") {
        return None;
    }
    b.str("bite_key").map(String::from)
}

/// What a seal stands on: Ok((the proposal, the question it was sealed for)),
/// or Err(why not).
fn standing(
    box_: &Path,
    rows: &[Obj],
    subj: &str,
    seal: &Obj,
) -> Result<(Obj, String), &'static str> {
    let missing = "is missing or can't be read";
    let raw = fs::read_to_string(prop_file(box_, subj)).map_err(|_| missing)?;
    let prop = match loads(&raw) {
        Ok(Value::Obj(p)) if ["path", "data", "cites", "claim"].iter().all(|k| p.has(k)) => p,
        _ => return Err(missing),
    };
    let same = subject_of(&prop).map_err(|_| missing)? == subj;
    if !same {
        return Err("is not the bytes that were sealed");
    }
    let key = if seal.has("bite_key") {
        seal.str("bite_key").map(String::from)
    } else {
        proposed_under(rows, subj, seal.get("n").and_then(Value::as_int))
    };
    match key {
        Some(k) => Ok((prop, k)),
        None => Err("was made under no question the record names"),
    }
}

fn record(box_: &str) -> Res<Record> {
    read_record(&Path::new(box_).join("record.jsonl"))
}

fn bite(box_: &str, text: &str, ts: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if refused_breaks(&r) {
        return Ok(REFUSED);
    }
    let key = match bite_key(text) {
        Some(k) => k,
        None => return Ok(refuse("refused: a bite with no words")),
    };
    let good = sealed(box_, &r.rows, "seal")?;
    for subj in &good.order {
        // a sealed answer for these words, first
        if let Ok((prop, asked)) = standing(bp, &r.rows, subj, &good.rows[subj]) {
            if asked == key {
                append_row(
                    bp,
                    ts,
                    "bite",
                    "kernel",
                    &obj(&[
                        ("bite_key", s(&key)),
                        ("answered_by", s(subj)),
                        ("served", Value::List(vec![])),
                    ]),
                )?;
                let doc = obj(&[
                    ("state", s("sealed")),
                    ("answer", prop.get("data").cloned().unwrap_or(Value::Null)),
                    ("by", s(subj)),
                ]);
                println!("{}", dumps_default(&Value::Obj(doc), false));
                return Ok(ALIVE);
            }
        }
    }
    let cfg = config(bp)?;
    let mut al = Alias::new();
    let mut listed = Obj::new();
    if cfg.has("words") {
        match read_words(&cfg.get("words").map(py_str).unwrap_or_default(), box_) {
            Ok((got, sha)) => {
                al = got;
                listed.set("words_sha256", Value::Str(sha));
            }
            Err(why) => return Ok(refuse(&format!("refused: {}", why))),
        }
    }
    let pile = chunks(&cfg.get("pile").map(py_str).unwrap_or_default());
    let served = rank(&pile, text, &al);
    let mut refs = Vec::new();
    let mut answers: Vec<&Chunk> = Vec::new();
    for c in &served {
        let e = echo(text, &c.text);
        refs.push(obj(&[
            ("id", s(&c.id)),
            ("where", Value::Str(format!("{}:{}", c.path, c.line))),
            ("echo", Value::Bool(e)),
        ]));
        if !e {
            answers.push(c);
        }
    }
    let mut row = obj(&[
        ("bite_key", s(&key)),
        (
            "served",
            Value::List(refs.iter().map(|x| Value::Obj(x.clone())).collect()),
        ),
    ]);
    for k in &listed.keys {
        row.set(k, listed.vals[k].clone());
    }
    append_row(bp, ts, "bite", "kernel", &row)?;
    let state = if !answers.is_empty() {
        "populated"
    } else if !refs.is_empty() {
        "echo"
    } else {
        "empty"
    };
    let mut doc = obj(&[("state", s(state)), ("bite_key", s(&key))]);
    let shown: Vec<Value> = served
        .iter()
        .zip(refs.iter())
        .map(|(c, r)| {
            let mut m = r.clone();
            m.set("text", s(&c.text));
            Value::Obj(m)
        })
        .collect();
    doc.set("served", Value::List(shown));
    let for_look: Vec<&Chunk> = if answers.is_empty() {
        vec![]
    } else {
        served.iter().collect()
    };
    let hints = look(&pile, text, &for_look, &al);
    if !hints.is_empty() {
        doc.set("look", Value::List(hints)); // printed for them; the record keeps no words
    }
    println!("{}", dumps_spaced_utf8(&Value::Obj(doc)));
    Ok(if answers.is_empty() { ESCALATE } else { ALIVE })
}

fn propose(box_: &str, lines: &[String], ts: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if refused_breaks(&r) {
        return Ok(REFUSED);
    }
    let last = match r.rows.iter().rev().find(|x| x.str("kind") == Some("bite")) {
        Some(l) => l,
        None => return Ok(refuse("refused: propose answers a bite; bite first")),
    };
    let served: HashSet<String> = last
        .list("served")
        .iter()
        .filter_map(|x| match x {
            Value::Obj(m) => m.get("id").map(py_str),
            _ => None,
        })
        .collect();
    for (i, line) in lines.iter().enumerate() {
        let prop = loads(line).ok();
        match door(prop.as_ref(), &served) {
            None => {
                let p = match prop {
                    Some(Value::Obj(p)) => p,
                    _ => unreachable!(),
                };
                let subj = subject_of(&p)?;
                if let Err(e) = fs::create_dir(bp.join("proposals")) {
                    if e.kind() != std::io::ErrorKind::AlreadyExists {
                        return Err(io_err(e));
                    }
                }
                let mut kept = p.clone();
                kept.set(
                    "bite_key",
                    last.get("bite_key").cloned().unwrap_or(Value::Null),
                );
                fs::write(
                    prop_file(bp, &subj),
                    dumps_default(&Value::Obj(kept), false),
                )
                .map_err(io_err)?;
                append_row(
                    bp,
                    ts,
                    "proposal",
                    "kernel",
                    &obj(&[
                        ("subject", s(&subj)),
                        ("verdict", s("pass")),
                        ("bite_row", last.get("n").cloned().unwrap_or(Value::Null)),
                    ]),
                )?;
                println!("pass  {}  waiting on your seal", subj);
            }
            Some(why) => {
                append_row(
                    bp,
                    ts,
                    "proposal",
                    "kernel",
                    &obj(&[
                        ("verdict", s("refused")),
                        ("line", int(i as i64)),
                        ("why", s(why)),
                    ]),
                )?;
                println!("refused  line {}: {}", i, why);
            }
        }
    }
    // Passing the door is not acceptance: nothing propose reads is an answer
    // until the person seals it (CONST-0-1).
    Ok(ESCALATE)
}

fn is_proposal(rows: &[Obj], subj: &str) -> bool {
    rows.iter()
        .any(|r| r.str("kind") == Some("proposal") && r.str("subject") == Some(subj))
}

fn seal(box_: &str, subj: &str, ts: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if refused_breaks(&r) {
        return Ok(REFUSED);
    }
    if !is_proposal(&r.rows, subj) {
        return Ok(refuse(&format!(
            "refused: {} is not a proposal in this box",
            subj
        )));
    }
    let no = sealed(box_, &r.rows, "decline")?;
    if no.has(subj) {
        return Ok(refuse(&format!(
            "refused: you declined {} at row {}",
            subj,
            py_str(no.rows[subj].get("n").unwrap_or(&Value::Null))
        )));
    }
    let cfg = config(bp)?;
    let key = match read_key(&cfg.get("key").map(py_str).unwrap_or_default(), box_) {
        Ok(k) => k,
        Err(why) => return Ok(refuse(&format!("refused: {}", why))),
    };
    let raw = fs::read_to_string(prop_file(bp, subj)).map_err(io_err)?;
    let prop = match loads(&raw)? {
        Value::Obj(p) if subject_of(&p)? == subj => p, // approved bytes are proposed bytes (CONST-0-4)
        _ => {
            return Ok(refuse(
                "refused: the proposal's bytes changed since it was proposed",
            ))
        }
    };
    let asked = match proposed_under(&r.rows, subj, None) {
        // the question this is the answer to
        Some(a) => a,
        None => {
            return Ok(refuse(&format!(
                "refused: the record names no question {} was made under",
                subj
            )))
        }
    };
    let pf = proof(&key, subj, "seal", Some(&asked));
    append_row(
        bp,
        ts,
        "seal",
        "human",
        &obj(&[
            ("subject", s(subj)),
            ("bite_key", s(&asked)),
            ("proof", Value::Str(pf)),
        ]),
    )?;
    let rel =
        normalize(&Path::new("written").join(prop.get("path").map(py_str).unwrap_or_default()));
    let out = bp.join(&rel);
    if let Some(parent) = out.parent() {
        fs::create_dir_all(parent).map_err(io_err)?;
    }
    fs::write(&out, prop.get("data").map(py_str).unwrap_or_default()).map_err(io_err)?;
    let shown: Vec<String> = rel
        .components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect();
    println!("sealed {}; written to {}", subj, shown.join("/"));
    Ok(ALIVE)
}

fn decline(box_: &str, subj: &str, ts: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if refused_breaks(&r) {
        return Ok(REFUSED);
    }
    if !is_proposal(&r.rows, subj) {
        return Ok(refuse(&format!(
            "refused: {} is not a proposal in this box",
            subj
        )));
    }
    for (act, said) in &[("seal", "sealed"), ("decline", "declined")] {
        let done = sealed(box_, &r.rows, act)?;
        if done.has(subj) {
            return Ok(refuse(&format!(
                "refused: you {} {} at row {}",
                said,
                subj,
                py_str(done.rows[subj].get("n").unwrap_or(&Value::Null))
            )));
        }
    }
    let cfg = config(bp)?;
    let key = match read_key(&cfg.get("key").map(py_str).unwrap_or_default(), box_) {
        Ok(k) => k,
        Err(why) => return Ok(refuse(&format!("refused: {}", why))),
    };
    let pf = proof(&key, subj, "decline", None);
    append_row(
        bp,
        ts,
        "decline",
        "human",
        &obj(&[("subject", s(subj)), ("proof", Value::Str(pf))]),
    )?;
    println!("declined {}; it won't be offered again", subj);
    Ok(ALIVE)
}

fn verify(box_: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if !r.breaks.is_empty() {
        println!("{}", r.breaks.join("\n"));
        return Ok(REFUSED);
    }
    let good = sealed(box_, &r.rows, "seal")?;
    let no = sealed(box_, &r.rows, "decline")?;
    let n_of = |row: &Obj| py_str(row.get("n").unwrap_or(&Value::Null));
    let subj_of = |row: &Obj| row.get("subject").map(py_str).unwrap_or_default();
    let forged: Vec<String> = r
        .rows
        .iter()
        .filter(|x| x.str("kind") == Some("seal") && !good.has(&subj_of(x)))
        .map(n_of)
        .collect();
    let nos: Vec<String> = r
        .rows
        .iter()
        .filter(|x| x.str("kind") == Some("decline") && !no.has(&subj_of(x)))
        .map(n_of)
        .collect();
    let mut drifted: Vec<(String, &str)> = Vec::new();
    for subj in &good.order {
        let why = match standing(bp, &r.rows, subj, &good.rows[subj]) {
            Err(why) => Some(why),
            Ok((prop, _)) => {
                let named = proposed_under(&r.rows, subj, None);
                let v = prop.get("bite_key"); // missing reads as None, as dict.get does
                let same = match (v, &named) {
                    (None, None) => true,
                    (Some(Value::Null), None) => true,
                    (Some(Value::Str(a)), Some(b)) => a == b,
                    _ => false,
                };
                if same {
                    None
                } else {
                    Some("names another question than the record")
                }
            }
        };
        if let Some(why) = why {
            drifted.push((subj.clone(), why));
        }
    }
    for (subj, why) in &drifted {
        println!(
            "the chain holds; {} is sealed, but its proposal file {}",
            subj, why
        );
    }
    if !forged.is_empty() {
        println!(
            "the chain holds; seal rows [{}] don't prove under your key",
            forged.join(", ")
        );
    }
    if !nos.is_empty() {
        println!(
            "the chain holds; decline rows [{}] don't prove under your key",
            nos.join(", ")
        );
    }
    if !forged.is_empty() || !nos.is_empty() || !drifted.is_empty() {
        return Ok(ESCALATE);
    }
    println!(
        "the chain holds: {} rows, {} sealed",
        r.rows.len(),
        good.order.len()
    );
    Ok(ALIVE)
}

fn out(box_: &str, ts: &str) -> Res<i32> {
    let bp = Path::new(box_);
    let r = record(box_)?;
    if refused_breaks(&r) {
        return Ok(REFUSED);
    }
    let good = sealed(box_, &r.rows, "seal")?;
    let no = sealed(box_, &r.rows, "decline")?;
    let waiting: Vec<String> = r
        .rows
        .iter()
        .filter(|x| x.str("kind") == Some("proposal") && x.str("verdict") == Some("pass"))
        .map(|x| x.get("subject").map(py_str).unwrap_or_default())
        .filter(|sj| !good.has(sj) && !no.has(sj))
        .collect();
    let tip = r
        .rows
        .last()
        .and_then(|x| x.get("hash").cloned())
        .unwrap_or_else(|| s(&t().genesis));
    append_row(
        bp,
        ts,
        "out",
        "kernel",
        &obj(&[("waiting", int(waiting.len() as i64)), ("tip", tip)]),
    )?;
    for sj in &waiting {
        println!("waiting on your seal: {}", sj);
    }
    println!(
        "{} rows; {} sealed; {} waiting",
        r.rows.len() + 1,
        good.order.len(),
        waiting.len()
    );
    Ok(if waiting.is_empty() { ALIVE } else { ESCALATE })
}

// ── the vectors: every case, answered, for compare.py ───────────────────────

fn opt(v: Option<String>) -> Value {
    v.map(Value::Str).unwrap_or(Value::Null)
}

fn vectors(cases: &str, results: &str) -> Res<i32> {
    let raw = fs::read_to_string(cases).map_err(io_err)?;
    let doc = match loads(&raw)? {
        Value::Obj(o) => o,
        _ => return Err("cases.json is not an object".into()),
    };
    let c = doc.obj("cases").ok_or("no cases")?;
    let mut out = Obj::new();
    let o = |m: &Value| -> Obj {
        match m {
            Value::Obj(x) => x.clone(),
            _ => Obj::new(),
        }
    };
    let one = |k: &str, v: Value| Value::Obj(obj(&[(k, v)]));

    let mut canon_out = Vec::new();
    for m in c.list("canon") {
        let cn = canon(o(m).get("in").unwrap_or(&Value::Null))?;
        canon_out.push(Value::Obj(obj(&[
            ("canon", s(&cn)),
            ("sha256", Value::Str(h256(&cn))),
        ])));
    }
    out.set("canon", Value::List(canon_out));

    let mut words_out = Vec::new();
    for m in c.list("words") {
        let m = o(m);
        let tx = m.str("text").unwrap_or("");
        let ws = Value::List(words(tx).iter().map(|w| s(w)).collect());
        words_out.push(Value::Obj(obj(&[
            ("words", ws),
            ("bite_key", opt(bite_key(tx))),
        ])));
    }
    out.set("words", Value::List(words_out));

    let hm = c.obj("hmac").ok_or("no hmac")?;
    let mut rfc = Vec::new();
    for m in hm.list("rfc4231") {
        let m = o(m);
        rfc.push(one(
            "mac",
            Value::Str(hmac_hex(
                &unhex(m.str("key").unwrap_or(""))?,
                &unhex(m.str("msg").unwrap_or(""))?,
            )),
        ));
    }
    let mut seals = Vec::new();
    for m in hm.list("seal") {
        let m = o(m);
        let asked = m.str("asked");
        seals.push(one(
            "proof",
            Value::Str(proof(
                &unhex(m.str("key").unwrap_or(""))?,
                m.str("subject").unwrap_or(""),
                "seal",
                asked,
            )),
        ));
    }
    out.set(
        "hmac",
        Value::Obj(obj(&[
            ("rfc4231", Value::List(rfc)),
            ("seal", Value::List(seals)),
        ])),
    );

    out.set(
        "html",
        Value::List(
            c.list("html")
                .iter()
                .map(|m| one("out", Value::Str(html_text(o(m).str("in").unwrap_or("")))))
                .collect(),
        ),
    );

    let mut holds_out = Vec::new();
    for m in c.list("holds") {
        let m = o(m);
        let tk: HashSet<String> = m
            .list("toks")
            .iter()
            .filter_map(|x| x.as_str().map(String::from))
            .collect();
        holds_out.push(one(
            "out",
            Value::Bool(holds(m.str("w").unwrap_or(""), &tk)),
        ));
    }
    out.set("holds", Value::List(holds_out));

    out.set(
        "echo",
        Value::List(
            c.list("echo")
                .iter()
                .map(|m| {
                    let m = o(m);
                    one(
                        "out",
                        Value::Bool(echo(
                            m.str("bite").unwrap_or(""),
                            m.str("text").unwrap_or(""),
                        )),
                    )
                })
                .collect(),
        ),
    );

    let tmp = std::env::temp_dir().join(format!(
        "kernel-vectors-{}-{}",
        process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0)
    ));
    fs::create_dir_all(&tmp).map_err(io_err)?;
    let made = (|| -> Res<(Vec<Vec<Chunk>>, Vec<Value>)> {
        let mut piles = Vec::new();
        let mut chunks_out = Vec::new();
        for (n, m) in c.list("chunks").iter().enumerate() {
            let root = tmp.join(format!("pile{}", n));
            fs::create_dir_all(&root).map_err(io_err)?;
            for f in o(m).list("pile") {
                let fm = o(f);
                let mut p = root.clone();
                for part in fm.list("parts") {
                    p.push(part.as_str().unwrap_or(""));
                }
                if let Some(parent) = p.parent() {
                    fs::create_dir_all(parent).map_err(io_err)?;
                }
                let body = if let Some(b64) = fm.str("b64") {
                    base64_decode(b64)?
                } else {
                    let n = fm.get("n").and_then(Value::as_int).unwrap_or(0) as usize;
                    format!(
                        "{}{}",
                        fm.str("repeat").unwrap_or("").repeat(n),
                        fm.str("then").unwrap_or("")
                    )
                    .into_bytes()
                };
                fs::write(&p, body).map_err(io_err)?;
            }
            let ch = chunks(&root.to_string_lossy());
            chunks_out.push(one(
                "chunks",
                Value::List(ch.iter().map(Chunk::json).collect()),
            ));
            piles.push(ch);
        }
        Ok((piles, chunks_out))
    })();
    let _ = fs::remove_dir_all(&tmp);
    let (piles, chunks_out) = made?;
    out.set("chunks", Value::List(chunks_out));

    let mut rank_out = Vec::new();
    for m in c.list("rank") {
        let m = o(m);
        let pile = &piles[m.get("pile").and_then(Value::as_int).unwrap_or(0) as usize];
        let ids: Vec<Value> = rank(pile, m.str("bite").unwrap_or(""), &alias_of(&m))
            .iter()
            .map(|x| s(&x.id))
            .collect();
        rank_out.push(one("ids", Value::List(ids)));
    }
    out.set("rank", Value::List(rank_out));

    out.set(
        "newest",
        Value::List(
            c.list("newest")
                .iter()
                .map(|m| one("newest", Value::Str(newest(o(m).str("text").unwrap_or("")))))
                .collect(),
        ),
    );

    let mut wordlist_out = Vec::new();
    for m in c.list("wordlist") {
        let (al, why) = match parse_words(o(m).str("text").unwrap_or("")) {
            Ok(list) => (alias_json(&list), Value::Null),
            Err(why) => (Value::Obj(Obj::new()), Value::Str(why)),
        };
        wordlist_out.push(Value::Obj(obj(&[("alias", al), ("why", why)])));
    }
    out.set("wordlist", Value::List(wordlist_out));

    out.set(
        "stem",
        Value::List(
            c.list("stem")
                .iter()
                .map(|m| one("stem", Value::Str(stem(o(m).str("w").unwrap_or("")))))
                .collect(),
        ),
    );

    let mut look_out = Vec::new();
    for m in c.list("look") {
        let m = o(m);
        let pile = &piles[m.get("pile").and_then(Value::as_int).unwrap_or(0) as usize];
        let served: Vec<&Chunk> = m
            .list("served")
            .iter()
            .map(|x| &pile[x.as_int().unwrap_or(0) as usize])
            .collect();
        look_out.push(one(
            "look",
            Value::List(look(
                pile,
                m.str("bite").unwrap_or(""),
                &served,
                &alias_of(&m),
            )),
        ));
    }
    out.set("look", Value::List(look_out));

    let mut door_out = Vec::new();
    for m in c.list("door") {
        let m = o(m);
        let prop = loads(m.str("line").unwrap_or("")).ok();
        let served: HashSet<String> = m
            .list("served")
            .iter()
            .filter_map(|x| x.as_str().map(String::from))
            .collect();
        door_out.push(one(
            "why",
            opt(door(prop.as_ref(), &served).map(String::from)),
        ));
    }
    out.set("door", Value::List(door_out));

    let mut subj_out = Vec::new();
    for m in c.list("subject") {
        let p = o(m).obj("prop").cloned().unwrap_or_default();
        subj_out.push(one("subject", Value::Str(subject_of(&p)?)));
    }
    out.set("subject", Value::List(subj_out));

    fs::write(results, format!("{}\n", canon(&Value::Obj(out))?)).map_err(io_err)?;
    Ok(ALIVE)
}

// ── the command line ────────────────────────────────────────────────────────

/// UTC, as strftime("%Y-%m-%dT%H:%M:%SZ") writes it: the civil date from the
/// epoch's days, no library.
fn now() -> String {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0) as i64;
    let (days, rem) = (secs.div_euclid(86400), secs.rem_euclid(86400));
    let (h, m, sec) = (rem / 3600, rem % 3600 / 60, rem % 60);
    // Howard Hinnant's civil_from_days
    let z = days + 719468;
    let era = z.div_euclid(146097);
    let doe = z.rem_euclid(146097);
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let mo = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if mo <= 2 { y + 1 } else { y };
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", y, mo, d, h, m, sec)
}

const USAGE: &str = "kernel.py: answers questions from your own files. Python 3.9+, stdlib only.
    python kernel.py init    --box DIR --pile FOLDER --key FILE [--words FILE]
    python kernel.py bite    --box DIR \"your question\"
    python kernel.py propose --box DIR --file SUGGESTIONS.jsonl
    python kernel.py seal    --box DIR proposal:<sha256>
    python kernel.py decline --box DIR proposal:<sha256>
    python kernel.py verify  --box DIR
    python kernel.py out     --box DIR
    python kernel.py test";

fn tables_path() -> String {
    if let Ok(p) = std::env::var("KERNEL_TABLES") {
        if !p.is_empty() {
            return p;
        }
    }
    if Path::new("kernel_tables.json").exists() {
        return "kernel_tables.json".into();
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            return dir
                .join("..")
                .join("..")
                .join("..")
                .join("..")
                .join("vectors")
                .join("kernel_tables.json")
                .to_string_lossy()
                .into_owned();
        }
    }
    "kernel_tables.json".into()
}

/// The SHA-256 of this binary, as kernel.py's VERSION is of its file.
fn self_version() -> String {
    std::env::current_exe()
        .ok()
        .and_then(|exe| fs::read(exe).ok())
        .map(|raw| sha256hex(&raw))
        .unwrap_or_else(|| t().genesis.clone())
}

fn run(argv: &[String]) -> Res<i32> {
    let tables = load_tables(&tables_path())?;
    unsafe {
        TABLES = Box::into_raw(Box::new(tables));
    }
    let v = self_version();
    unsafe {
        VERSION = Box::into_raw(Box::new(v));
    }
    if argv.first().map(String::as_str) == Some("vectors") {
        if argv.len() != 3 {
            return Ok(refuse("vectors CASES.json RESULTS.json"));
        }
        return vectors(&argv[1], &argv[2]);
    }
    let verb = argv.first().cloned().unwrap_or_default();
    let mut opts: HashMap<&str, String> = HashMap::new();
    let mut args: Vec<&str> = Vec::new();
    let mut i = 1;
    while i < argv.len() {
        let a = argv[i].as_str();
        match a {
            "--box" | "--pile" | "--key" | "--file" | "--now" | "--words" => {
                let val = if i + 1 < argv.len() {
                    i += 1;
                    argv[i].clone()
                } else {
                    String::new()
                };
                opts.insert(a, val);
            }
            _ => args.push(a),
        }
        i += 1;
    }
    let opt_ = |k: &str| opts.get(k).cloned().unwrap_or_default();
    let box_ = opt_("--box");
    if box_.is_empty() {
        return Ok(refuse(USAGE));
    }
    let mut ts = opt_("--now");
    if ts.is_empty() {
        ts = now();
    }
    if verb == "init" && !opt_("--pile").is_empty() && !opt_("--key").is_empty() && args.is_empty()
    {
        let wl = opt_("--words");
        return init_box(
            &box_,
            &opt_("--pile"),
            &opt_("--key"),
            &ts,
            if wl.is_empty() { None } else { Some(&wl) },
        );
    }
    if !Path::new(&box_).join("kernel.json").exists() {
        return Ok(refuse("refused: not a kernel box; init first"));
    }
    match verb.as_str() {
        "bite" if args.len() == 1 => bite(&box_, args[0], &ts),
        "propose" if !opt_("--file").is_empty() && args.is_empty() => {
            let raw = fs::read(opt_("--file")).map_err(io_err)?;
            let text =
                String::from_utf8(raw).map_err(|_| "the suggestions are not UTF-8".to_string())?;
            propose(&box_, &splitlines(&text), &ts)
        }
        "seal" if args.len() == 1 && args[0].starts_with("proposal:") => seal(&box_, args[0], &ts),
        "decline" if args.len() == 1 && args[0].starts_with("proposal:") => {
            decline(&box_, args[0], &ts)
        }
        "verify" if args.is_empty() => verify(&box_),
        "out" if args.is_empty() => out(&box_, &ts),
        _ => Ok(refuse(USAGE)),
    }
}

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let code = match run(&argv) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("refused: {}", e);
            REFUSED
        }
    };
    let _ = std::io::stdout().flush();
    process::exit(code);
}
