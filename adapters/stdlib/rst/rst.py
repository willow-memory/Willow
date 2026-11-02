r"""rst.py: reStructuredText files as plain prose, line for line. Python 3.9+.

    python adapters/stdlib/rst/rst.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .rst and .rest files (hidden folders and files skipped) and
writes each as the text it shows, with the markup taken off. The mirror has
the same number of lines as the source and each line is the source's line, so
a passage found in the mirror is on that line of the .rst file:

    Tides                              ->   Tides
    =====                              ->
    .. note:: Bring a coat.            ->   note: Bring a coat.
    See `the shop <https://x.example>`_.  ->   See the shop (https://x.example).
    | 128  | 0.01 sec. |               ->   128; 0.01 sec.

A section title is its own text; its over- and underline rows are blank. An
admonition says what it is ("note:", "warning:"), and a version note its
directive's name ("versionadded 3.2"). A code block, a `::` literal block
and a doctest are kept as written, the marker blank and a line ending in `::`
keeping one colon. An image or figure keeps its alt text and a figure its
caption. Contents, toctree, include, raw, index, comments, link targets,
substitution definitions and a directive's options are blank. A link is its
text, with an outside address after it; a role, a literal and emphasis are
their text; a substitution is its replacement; a footnote reference is
dropped and a footnote reads "[1] text". A field reads "author: Ada". A
table's header row and each body row are their cells, joined by "; ", on
the row's first line; its borders are blank. Backslash escapes are read.

Nothing is added that would repeat from passage to passage: no title above
a title, no header beside each value. A word on every passage would answer
any question that names it.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no text after reading, or that cannot be
read, is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

# a stand-in for text already settled (a literal, an escaped character), so
# later rules don't touch it: private-use characters never typed
HOLD_OPEN, HOLD_CLOSE = "", ""
HELD = re.compile(HOLD_OPEN + r"(\d+)" + HOLD_CLOSE)

ADORN = re.compile(r"^([!-/:-@\[-`{-~])\1+$")
EXPLICIT = re.compile(r"^\.\.(?:\s+(.*))?$")
DIRECTIVE = re.compile(r"^([A-Za-z0-9][\w.+-]*(?::[\w.+-]+)*)::(?:\s+(.*))?$")
FOOTNOTE = re.compile(r"^\[(#[\w.-]*|\*|\d+|[A-Za-z][\w.-]*)\](?:\s+(.*))?$")
OPTION = re.compile(r"^:([\w][\w .-]*):(?:\s+(.*))?$")
FIELD = re.compile(r"^:([^:`\s][^:`]*?):(?:\s+(.*))?$")
BULLET = re.compile(r"^[-*+•‣⁃]\s+")
GRID_BORDER = re.compile(r"^\+(?:[-=]+\+)+$")
SIMPLE_BORDER = re.compile(r"^=+(?: +=+)+$")
SPAN_ROW = re.compile(r"^[- ]+$")

LITERAL = re.compile(r"``(.+?)``(?!`)")
ESCAPE = re.compile(r"\\(.)")
ROLE = re.compile(r":([A-Za-z][\w+.-]*(?::[\w+.-]+)*):`([^`]+)`")
ROLE_AFTER = re.compile(r"`([^`]+)`:([A-Za-z][\w+.-]*(?::[\w+.-]+)*):")
EMBED = re.compile(r"`([^`<]*?)\s*<([^<>`]+)>`(?:__?)?")
INLINE_TARGET = re.compile(r"_`([^`]+)`")
NAMED = re.compile(r"`([^`]+)`(?:__?)?")
FOOT_REF = re.compile(r"\s*\[(?:#[\w.-]*|\*|\d+|[A-Za-z][\w.-]*)\]_(?!\w)")
SUB_REF = re.compile(r"\|(?=\S)([^|`]+?)(?<=\S)\|(?:__?)?")
BARE_REF = re.compile(r"(?<![\w`])([A-Za-z0-9@][\w.+@-]*?)(__?)(?!\w)")
STRONG = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
EM = re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])")
# a link or role that opens on one line and closes on the next: the half
# left on each line once the whole ones are read
TAIL_EMBED = re.compile(r"(^|\s)([^`\s][^`]*?)?\s*<([^<>\s]+)>`(?:__?)?(?!\w)")
TAIL = re.compile(r"^(\s*)([^`]+?)`(?:__?|:[\w:+.-]+:)?(?!\w)")
OPEN = re.compile(r"(?:\s|^)(?::[\w:+.-]+:)?`(?=\S[^`]*$)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

ADMONITIONS = {
    "note": "note",
    "warning": "warning",
    "tip": "tip",
    "hint": "hint",
    "important": "important",
    "caution": "caution",
    "danger": "danger",
    "error": "error",
    "attention": "attention",
    "seealso": "seealso",
    "todo": "to do",
}
# a version note says its directive's own name: the one word nobody asks with
VERSIONS = ("versionadded", "versionchanged", "deprecated", "versionremoved")
VERBATIM = {"code-block", "code", "sourcecode", "doctest", "testcode",
            "testoutput", "testsetup", "testcleanup", "parsed-literal",
            "productionlist", "highlight-block"}  # fmt: skip
BLANK = {"toctree", "contents", "include", "raw", "index", "meta", "highlight",
         "literalinclude", "sectnum", "section-numbering", "target-notes",
         "header", "footer", "default-role", "role", "title", "math",
         "currentmodule", "tabularcolumns", "automodule", "autoclass",
         "autofunction", "automethod", "autoattribute", "autodata",
         "autoexception", "autosummary", "graphviz", "digraph", "only-latex"}  # fmt: skip
CONTAINER = {"only", "ifconfig", "container", "compound", "tabs", "tab-set",
             "class", "cssclass", "rst-class"}  # fmt: skip
PROSE_ARGS = {"admonition", "rubric", "topic", "sidebar", "table", "list-table",
              "csv-table", "glossary", "centered", "tab", "tab-item",
              "epigraph", "highlights", "pull-quote"}  # fmt: skip


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _key(name: str) -> str:
    return " ".join(name.strip("`").split()).lower()


class Doc:
    """What a file says once, used wherever it is named: its substitutions,
    and its link targets."""

    def __init__(self, lines: list[str]):
        self.subs: dict[str, str] = {}
        self.targets: set[str] = set()
        for i, raw in enumerate(lines):
            s = raw.strip()
            m = re.match(r"^\.\.\s+_(`[^`]+`|[^:`]+):", s)
            if m:
                self.targets.add(_key(m.group(1)))
            if re.match(r"^(?:\.\.\s+__:|__\s)", s):
                self.targets.add("__")
            m = re.match(r"^\.\.\s+\|([^|]+)\|\s+([\w-]+)::\s*(.*)$", s)
            if not m:
                continue
            name, kind, args = m.groups()
            body = []
            for nxt in lines[i + 1 :]:
                if not nxt.strip() or _indent(nxt) <= _indent(raw):
                    break
                body.append(nxt.strip())
            if kind == "replace":
                self.subs[name] = inline(" ".join([args, *body]), None)
            elif kind == "image":
                alt = [o for o in body if o.startswith(":alt:")]
                self.subs[name] = alt[0][5:].strip() if alt else ""
            elif kind == "unicode":
                self.subs[name] = _unicode(args)


def _unicode(args: str) -> str:
    out = []
    for tok in args.split(".. ")[0].split():
        m = re.match(r"^(?:0x|x|\\x|U\+|u|\\u|&#x)([0-9A-Fa-f]+);?$", tok)
        if m:
            out.append(chr(int(m.group(1), 16)))
        elif tok.isdigit():
            out.append(chr(int(tok)))
        else:
            out.append(tok)
    return "".join(out)


def inline(text: str, doc: Doc | None) -> str:
    """One line's inline markup taken off, its words kept."""
    held: list[str] = []

    def hold(s: str) -> str:
        held.append(s)
        return f"{HOLD_OPEN}{len(held) - 1}{HOLD_CLOSE}"

    def role(name: str, body: str) -> str:
        short = name.split(":")[-1].lower()
        if short == "math":
            return ""
        if short in ("rfc", "pep") and re.match(r"^\d+(#.*)?$", body):
            return hold(f"{short.upper()} {body.split('#')[0]}")
        m = re.match(r"^(.*?\S)\s*<([^<>]*)>$", body)
        if m:
            return hold(m.group(1))
        body = body.lstrip("!")
        if body.startswith("~"):
            body = body[1:].split(".")[-1]
        return hold(body)

    def link(m: re.Match) -> str:
        shown, url = " ".join(m.group(1).split()), m.group(2).strip()
        if url.endswith("_") and not url.endswith("\\_"):
            return hold(shown or url[:-1])  # an alias of a target: its name
        if shown and SCHEME.match(url) and url != shown:
            return hold(f"{shown} ({url})")
        return hold(shown or url)

    subs = doc.subs if doc else {}
    targets = doc.targets if doc else set()
    text = LITERAL.sub(lambda m: hold(m.group(1)), text)
    text = re.sub(r"\\ ", "", text)
    text = ESCAPE.sub(lambda m: hold(m.group(1)), text)
    text = ROLE.sub(lambda m: role(m.group(1), m.group(2)), text)
    text = ROLE_AFTER.sub(lambda m: role(m.group(2), m.group(1)), text)
    text = EMBED.sub(link, text)
    text = INLINE_TARGET.sub(lambda m: hold(m.group(1)), text)
    text = NAMED.sub(lambda m: hold(" ".join(m.group(1).split())), text)
    text = FOOT_REF.sub("", text)

    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name in subs:
            return hold(subs[name])
        low = {k.lower(): v for k, v in subs.items()}
        return hold(low[name.lower()]) if name.lower() in low else m.group(0)

    text = SUB_REF.sub(sub, text)

    def bare(m: re.Match) -> str:
        known = "__" in targets if m.group(2) == "__" else _key(m.group(1)) in targets
        return m.group(1) if known else m.group(0)

    text = BARE_REF.sub(bare, text)
    text = STRONG.sub(r"\1", text)
    text = EM.sub(r"\1", text)

    def tail(m: re.Match) -> str:
        shown, url = (m.group(2) or "").strip(), m.group(3)
        if shown and SCHEME.match(url):
            return f"{m.group(1)}{shown} ({url})"
        if SCHEME.match(url):
            return f"{m.group(1)}({url})"
        return f"{m.group(1)}{shown or url}"

    text = TAIL_EMBED.sub(tail, text)
    if text.count("`") == 1:
        text = OPEN.sub(" ", text) if OPEN.search(text) else TAIL.sub(r"\1\2", text)
    while HELD.search(text):  # a held span may hold another (an escape in a role)
        text = HELD.sub(lambda m: held[int(m.group(1))], text)
    return " ".join(text.split())


def _body_end(lines: list[str], i: int, ind: int) -> int:
    """Where an indented block under line i ends (exclusive), trailing
    blank lines left out."""
    j = i + 1
    while j < len(lines) and (not lines[j].strip() or _indent(lines[j]) > ind):
        j += 1
    while j > i + 1 and not lines[j - 1].strip():
        j -= 1
    return j


def _dedent(lines: list[str]) -> list[str]:
    base = min((_indent(x) for x in lines if x.strip()), default=0)
    return [x[base:] for x in lines]


def _cells(line: str, cols: list[tuple[int, int]]) -> list[str] | None:
    """A simple table's line cut at its columns, or None where text runs
    across the gap between two (a cell that spans)."""
    out = []
    for k, (s, e) in enumerate(cols):
        if k + 1 < len(cols):
            nxt = cols[k + 1][0]
            if line[e:nxt].strip():
                return None
            out.append(line[s:nxt].strip())
        else:
            out.append(line[s:].strip())
    return out


def _row(values: list[str], doc: Doc) -> str:
    """A row's values, in order. A header is written once, on its own row,
    never beside each value: a word on every row would answer any question
    that names it."""
    return "; ".join(v for v in (inline(x, doc) for x in values) if v)


def simple_table(rows: list[str], doc: Doc) -> list[str]:
    """A simple table's lines: borders blank, each other line its cells."""
    base = _indent(rows[0])
    rows = [r[base:] for r in rows]
    cols = [(m.start(), m.end()) for m in re.finditer(r"=+", rows[0])]
    out = [""] * len(rows)
    for k, line in enumerate(rows):
        if not line.strip() or SIMPLE_BORDER.match(line) or SPAN_ROW.match(line):
            continue
        cells = _cells(line, cols)
        out[k] = _row(cells, doc) if cells is not None else inline(line.strip(), doc)
    return out


def grid_table(rows: list[str], doc: Doc) -> list[str]:
    """A grid table's lines: borders blank, each row's cells on its first
    line, a cell's lines joined. A row whose cells don't line up with the
    columns (one spans two) keeps each line's text on that line."""
    base = _indent(rows[0])
    rows = [r[base:] for r in rows]
    bounds = [k for k, ch in enumerate(rows[0]) if ch == "+"]
    out = [""] * len(rows)
    groups: list[list[int]] = []
    cur: list[int] = []
    for k, r in enumerate(rows):
        if (
            GRID_BORDER.match(r)
            and [n for n, ch in enumerate(r) if ch == "+"] == bounds
        ):
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(k)
    for lines in groups:
        if all(
            len(rows[k]) > bounds[-1] and all(rows[k][b] == "|" for b in bounds)
            for k in lines
        ):
            cells = [
                " ".join(rows[k][a + 1 : b].strip() for k in lines)
                for a, b in zip(bounds, bounds[1:])
            ]
            out[lines[0]] = _row(cells, doc)
            continue
        for k in lines:
            parts = [p.strip() for p in re.split(r"[|+]", rows[k])]
            out[k] = _row([p for p in parts if not re.match(r"^[-=]*$", p)], doc)
    return out


def directive(
    name: str, args: str, body: list[str], doc: Doc
) -> tuple[str, list[str], set[int]]:
    """A directive's own line and its body's lines."""
    name = name.lower()
    short = name.split(":")[-1]
    opts: dict[str, str] = {}
    out = [""] * len(body)
    k = 0
    while k < len(body) and body[k].strip():  # options, up to the first blank line
        m = OPTION.match(body[k].strip())
        if not m:
            break
        opts[m.group(1).lower()] = (m.group(2) or "").strip()
        k += 1
    rest = body[k:]
    verb: set[int] = set()
    if short in BLANK or name in BLANK:
        return "", out, verb
    if short in VERBATIM:
        for n, line in enumerate(_dedent(rest)):
            if short == "parsed-literal" and line.strip():  # its links read
                line = line[: _indent(line)] + inline(line, doc)
            out[k + n] = line.rstrip()
            if line.strip():
                verb.add(k + n)
        return "", out, verb
    if short in ("image", "figure"):
        head = inline(opts.get("alt", ""), doc)
        if short == "figure":
            sub, subverb = block(_dedent(rest), doc)
            out[k:] = sub
            verb = {k + n for n in subverb}
        return head, out, verb
    sub, subverb = block(_dedent(rest), doc)
    out[k:] = sub
    verb = {k + n for n in subverb}
    if short in ADMONITIONS or short in VERSIONS:
        if short in VERSIONS:
            version, _, more = args.partition(" ")
            label = f"{short} {version}".strip()
            head = f"{label}: {inline(more, doc)}" if more.strip() else label
            return head, out, verb
        label = ADMONITIONS[short] + ":"
        if args.strip():
            return f"{label} {inline(args, doc)}", out, verb
        first = next((n for n, x in enumerate(out) if x), None)
        if first is not None and first not in verb:
            out[first] = f"{label} {out[first]}"
            return "", out, verb
        return label, out, verb
    if short in CONTAINER:
        return "", out, verb
    if short in PROSE_ARGS:
        return inline(args, doc), out, verb
    return " ".join(args.split()), out, verb  # a signature: as written


def block(lines: list[str], doc: Doc) -> tuple[list[str], set[int]]:
    """Lines of reStructuredText as their text, one for one, and which of
    them are kept as written (code)."""
    lines = list(lines)
    n = len(lines)
    out = [""] * n
    verb: set[int] = set()
    items: set[int] = set()  # bullet items, read as their text indented
    i = 0
    literal_under: int | None = None  # a line ended in `::`: its indent
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        ind = _indent(line)
        if literal_under is not None:
            under, literal_under = literal_under, None
            if ind > under:
                end = _body_end(lines, i - 1, under)
                for k, text in enumerate(_dedent(lines[i:end])):
                    out[i + k] = text
                    if text.strip():
                        verb.add(i + k)
                i = end
                continue
        nxt = lines[i + 1] if i + 1 < n else ""
        # a title with an overline and an underline
        if (
            ADORN.match(s)
            and i + 2 < n
            and nxt.strip()
            and not ADORN.match(nxt.strip())
            and lines[i + 2].strip()
            and lines[i + 2].strip()[0] == s[0]
            and ADORN.match(lines[i + 2].strip())
        ):
            out[i + 1] = inline(nxt.strip(), doc)
            i += 3
            continue
        # a title with an underline
        if (
            ind == 0
            and nxt.strip()
            and _indent(nxt) == 0
            and ADORN.match(nxt.strip())
            and not ADORN.match(s)
            and (len(nxt.strip()) >= 4 or len(nxt.strip()) >= len(s))
            and (i == 0 or not lines[i - 1].strip())
        ):
            out[i] = inline(s, doc)
            i += 2
            continue
        if ADORN.match(s) and len(s) >= 4:  # a transition
            i += 1
            continue
        if GRID_BORDER.match(s):
            end = i + 1
            while end < n and lines[end].strip()[:1] in ("+", "|"):
                end += 1
            out[i:end] = grid_table(lines[i:end], doc)
            i = end
            continue
        if SIMPLE_BORDER.match(s):
            end, seen = None, 1
            for j in range(i + 1, n):
                if SIMPLE_BORDER.match(lines[j].strip()):
                    seen += 1
                    if j + 1 == n or not lines[j + 1].strip():
                        end = j + 1
                        break
            if end is not None and seen >= 2:
                out[i:end] = simple_table(lines[i:end], doc)
                i = end
                continue
        m = EXPLICIT.match(s)
        if m:
            rest = (m.group(1) or "").strip()
            if not rest and (i + 1 == n or not nxt.strip()):
                i += 1  # an empty comment
                continue
            end = _body_end(lines, i, ind)
            body = lines[i + 1 : end]
            d = DIRECTIVE.match(rest)
            f = FOOTNOTE.match(rest)
            if d and not rest.startswith(("_", "|")):
                head, sub, subverb = directive(d.group(1), d.group(2) or "", body, doc)
                out[i] = head
                out[i + 1 : end] = sub
                verb |= {i + 1 + k for k in subverb}
            elif f:
                label = f.group(1).lstrip("#*")
                label = f"[{label}]" if label else ""
                out[i] = f"{label} {inline(f.group(2) or '', doc)}".strip()
                sub, subverb = block(_dedent(body), doc)
                out[i + 1 : end] = sub
                verb |= {i + 1 + k for k in subverb}
            # else a link target, a substitution or a comment: blank
            i = end
            continue
        if re.match(r"^__\s", s):  # an anonymous link target
            i = _body_end(lines, i, ind)
            continue
        if s.startswith(">>>"):  # a doctest, as written, to its blank line
            while i < n and lines[i].strip():
                out[i] = lines[i].strip()
                verb.add(i)
                i += 1
            continue
        b = BULLET.match(s)
        if b:  # its text read as a block indented past the bullet, then "- "
            lines[i] = " " * (ind + b.end()) + s[b.end() :]
            items.add(i)
            continue
        text = s
        if s.endswith("::"):
            literal_under = ind
            if s == "::" or s[-3:-2].isspace():
                text = s[:-2].rstrip()
            else:
                text = s[:-1]
        f = FIELD.match(text)
        if f:
            value = inline(f.group(2) or "", doc)
            out[i] = f"{inline(f.group(1), doc).lower()}: {value}".rstrip()
        elif re.match(r"^\|(\s|$)", text):  # a line block
            out[i] = inline(text[1:], doc)
        else:
            out[i] = inline(text, doc)
        i += 1
    for k in items:
        if out[k] and k not in verb:
            out[k] = "- " + out[k]
    return out, verb


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    lines = [x.expandtabs(8).rstrip() for x in text.split("\n")]
    out, _ = block(lines, Doc(lines))
    result = "\n".join(out)
    return result.rstrip("\n") + "\n" if result.strip() else None


EXTS = (".rst", ".rest")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: rst.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
