r"""markdown.py: Markdown files as plain text, line for line. Python 3.9+.

    python adapters/stdlib/markdown/markdown.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .md and .markdown files (hidden folders and files skipped)
and writes each as the text it shows, with the markup taken off. The mirror
has the same number of lines as the source and each line is the source's
line, so a passage found in the mirror is on that line of the .md file:

    ## Tomatoes                          ->   Tomatoes
    | APMA | passed | 71% |              ->   APMA; passed; 71%
    - [x] pay the **gas** bill           ->   - [x] pay the gas bill
    See [the shop](https://x.example).   ->   See the shop (https://x.example).

Front matter (YAML between `---` lines, or TOML between `+++` lines) is kept
as its values, keys off; a list that runs to the end of the block is joined
onto its key's line. A heading is its text. A table is its header row once,
moved onto the separator's line so it starts the passage holding the rows,
then each row as its cells joined by "; ". Emphasis, code backticks, HTML tags and
comments, escapes and footnote markers are taken off; a link is its text,
with an outside address after it; an image is its alt text; a wikilink is the
text it shows. A task keeps its [ ] or [x]. A fenced code block is
kept as written. Fence lines, table separators, rules, setext underlines and
reference definitions are blank, so the numbering holds.

Each file is written to MIRROR at the same relative path with `.txt` added,
and its map of places beside it, hidden, as the mirror contract says
(adapters/stdlib/ci/README.md): `MIRROR/.places/<path>.txt.json`, each
passage's line, which is the source's own, or the header's and the
separator's for a table's first passage. FOLDER is only read. A file with no text after reading, or that cannot be
read, is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SEP = " › "  # between a page and its heading in a wikilink
# a stand-in for text already settled (a code span, an escaped character),
# so later rules don't touch it: private-use characters never typed
HOLD_OPEN, HOLD_CLOSE = "\ue000", "\ue001"
HELD = re.compile(HOLD_OPEN + r"(\d+)" + HOLD_CLOSE)

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})")
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
RULE = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?\s*$")
LIST = re.compile(r"^\s*(?:([-*+])|(\d{1,9})([.)]))[ \t]+")
TASK = re.compile(r"^\[([ xX])\][ \t]+")
QUOTE = re.compile(r"^\s{0,3}>[ \t]?")
REF_DEF = re.compile(
    r"^ {0,3}\[([^\]^][^\]]*)\]:\s*<?(\S+?)>?(?:\s+[\"'(].*[\"')])?\s*$"
)
FOOT_DEF = re.compile(r"^ {0,3}\[\^([^\]]+)\]:\s?(.*)$")
#: an HTML comment, closed by --> or by --!> as browsers also close one
COMMENT = re.compile(r"<!--.*?--!?>", re.S)
COMMENT_END = re.compile(r"--!?>")
TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>")
BREAK_TAG = re.compile(r"<br\s*/?>", re.I)
CODE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
ESCAPE = re.compile(r"\\([!-/:-@\[-`{-~])")
AUTOLINK = re.compile(
    r"<((?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^\s<>]+)|(?:[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+))>"
)
# link text may hold one level of brackets: [see [this]](url)
TEXT = r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]"
TAIL = r"\(\s*<?([^\s()<>]*(?:\([^\s()]*\)[^\s()<>]*)*)>?(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
IMAGE = re.compile(r"!\[([^\[\]]*)\]" + TAIL)  # first: a badge is an image in a link
INLINE_LINK = re.compile(TEXT + TAIL)
REF_LINK = re.compile(r"!?" + TEXT + r"\[([^\]]*)\]")
SHORT_REF = re.compile(r"!?\[([^\]\[^]+)\](?!\(|:)")
WIKI = re.compile(r"!?\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
FOOT_REF = re.compile(r"\[\^[^\]\s]+\]")
STRIKE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
STRONG_STAR = re.compile(r"\*\*(?=[^\s*])(.+?)(?<=[^\s*])\*\*")
STRONG_UNDER = re.compile(
    r"(?<![A-Za-z0-9_])__(?=[^\s_])(.+?)(?<=[^\s_])__(?![A-Za-z0-9_])"
)
EM_STAR = re.compile(r"(?<![A-Za-z0-9*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![A-Za-z0-9*])")
EM_UNDER = re.compile(r"(?<![A-Za-z0-9_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![A-Za-z0-9_])")
# bold or a strike that opens on one line and closes on another: the half
# left on each line once the pairs are gone
OPENS = re.compile(r"(?:(?<=\s)|^)(?:\*\*|__|~~)(?=[^\s*_~])")
CLOSES = re.compile(r"(?<=[^\s*_~])(?:\*\*|__|~~)(?=[\s.,;:!?)]|$)")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _flow(value: str) -> str:
    """A YAML or TOML value as words: quotes off, a [a, b] list as a, b."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return ", ".join(_unquote(v) for v in value[1:-1].split(",") if v.strip())
    return _unquote(value)


def front_matter(lines: list[str]) -> int:
    """How many lines the front matter takes at the top (0 if none): a `---`
    or `+++` line first, and the same line again to close it (YAML may also
    close with `...`)."""
    if not lines or lines[0].rstrip() not in ("---", "+++"):
        return 0
    fence = lines[0].rstrip()
    ends = (fence, "...") if fence == "---" else (fence,)
    for i in range(1, len(lines)):
        if lines[i].rstrip() in ends:
            return i + 1
    return 0


def matter_lines(block: list[str], toml: bool) -> list[str]:
    """Front matter's inner lines as their values, one for one. The keys go:
    a key such as date or tags heads every note, so a passage holding only
    it would answer a question about anything with that word in it."""
    out: list[str] = []
    for i, raw in enumerate(block):
        line = raw.strip()
        if not line or line.startswith("#"):
            out.append("")
            continue
        if toml:
            m = re.match(r"^\[+\s*([^\]]+?)\s*\]+$", line)
            k, eq, v = line.partition("=")
            out.append(m.group(1) if m else _flow(v) if eq else line)
            continue
        if line.startswith("-"):
            out.append(_flow(line[1:]))
            continue
        m = re.match(r"^([^:\s][^:]*?)\s*:(?:\s+(.*))?$", line)
        value = _flow(m.group(2) or "") if m else line
        rest = block[i + 1 :]
        n = 0
        while n < len(rest) and rest[n].strip().startswith("-"):
            n += 1
        if m and not value and n and n == len(rest):
            # a list that runs to the closing fence: joined onto its key's
            # line, the item lines blank beside the blank fence, so the
            # block stays one passage
            out.append(", ".join(_flow(r.strip()[1:]) for r in rest))
            out.extend("" for _ in rest)
            break
        out.append(value)
    return out


def inline(text: str, refs: dict[str, str]) -> str:
    """One line's inline markup taken off, its words kept."""
    held: list[str] = []

    def hold(s: str) -> str:
        held.append(s)
        return f"{HOLD_OPEN}{len(held) - 1}{HOLD_CLOSE}"

    text = CODE.sub(lambda m: hold(m.group(2).strip() or m.group(2)), text)
    text = ESCAPE.sub(lambda m: hold(m.group(1)), text)
    text = AUTOLINK.sub(lambda m: hold(m.group(1)), text)
    text = COMMENT.sub("", text)
    text = BREAK_TAG.sub(" ", text)
    text = TAG.sub("", text)
    text = WIKI.sub(
        lambda m: (m.group(2) or m.group(1).replace("#", SEP)).strip(), text
    )
    text = FOOT_REF.sub("", text)

    def link(m: re.Match) -> str:
        shown, url = m.group(1), m.group(2)
        if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url) or url == shown:
            return shown  # a link within the folder: the file is there to find
        return f"{shown} ({url})"

    text = IMAGE.sub(r"\1", text)
    text = INLINE_LINK.sub(link, text)

    def ref(m: re.Match) -> str:
        label = (m.group(2) or m.group(1)).strip().lower()
        return m.group(1) if label in refs else m.group(0)

    text = REF_LINK.sub(ref, text)
    text = SHORT_REF.sub(
        lambda m: m.group(1) if m.group(1).strip().lower() in refs else m.group(0), text
    )
    for rule in (STRIKE, STRONG_STAR, STRONG_UNDER, EM_STAR, EM_UNDER):
        text = rule.sub(r"\1", text)
    text = CLOSES.sub("", OPENS.sub("", text))
    text = html.unescape(text)
    while HELD.search(text):  # a held span may hold another (an escape in code)
        text = HELD.sub(lambda m: held[int(m.group(1))], text)
    return " ".join(text.split())


def cells(row: str) -> list[str]:
    """A table row's cells: split at each unescaped |, the outer ones dropped."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def _is_table_start(lines: list[str], i: int) -> bool:
    return (
        i + 1 < len(lines)
        and "|" in lines[i]
        and "|" in lines[i + 1] + lines[i]
        and bool(TABLE_SEP.match(lines[i + 1]))
        and "-" in lines[i + 1]
        and ("|" in lines[i + 1] or lines[i].strip().startswith("|"))
    )


def _paragraph_line(line: str) -> bool:
    """A line that could be a setext heading's text."""
    return bool(line.strip()) and not (
        LIST.match(line) or QUOTE.match(line) or ATX.match(line) or FENCE.match(line)
        or RULE.match(line) or line.startswith(("    ", "\t"))
    )  # fmt: skip


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    out: list[str] = [""] * len(lines)

    top = front_matter(lines)
    if top:
        out[1 : top - 1] = matter_lines(lines[1 : top - 1], lines[0].startswith("+"))

    # reference definitions, found first: a link may come before its target
    refs: dict[str, str] = {}
    fence = ""
    for line in lines[top:]:
        m = FENCE.match(line)
        if m and (
            not fence or m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence)
        ):
            fence = "" if fence else m.group(2)
            continue
        d = REF_DEF.match(line)
        if not fence and d:
            refs[d.group(1).strip().lower()] = d.group(2)

    fence = ""
    table = False
    comment = False
    i = top
    while i < len(lines):
        raw = lines[i]
        m = FENCE.match(raw)
        if fence:
            if (
                m
                and m.group(2)[0] == fence[0]
                and len(m.group(2)) >= len(fence)
                and not raw[m.end() :].strip()
            ):
                fence = ""
            else:
                out[i] = raw.rstrip()  # code, as written
            i += 1
            continue
        if m and not comment:
            fence, table = m.group(2), False
            i += 1
            continue

        line = raw
        if comment:  # inside a <!-- comment --> that began on a line above
            end = COMMENT_END.search(line)
            if end is None:
                i += 1
                continue
            comment, line = False, line[end.end() :]
        line = COMMENT.sub("", line)
        if "<!--" in line:
            comment, line = True, line[: line.index("<!--")]

        if table:  # inside a table's body: a row is its cells
            if "|" in line and line.strip():
                out[i] = "; ".join(
                    v for v in (inline(c, refs) for c in cells(line)) if v
                )
                i += 1
                continue
            table = False
        if _is_table_start(lines, i) and not comment:
            # the header once, on the separator's line, so it starts the
            # passage that holds the rows; its own line stays blank
            out[i + 1] = "; ".join(
                h for h in (inline(c, refs) for c in cells(line)) if h
            )
            table = True
            i += 2
            continue

        if i + 1 < len(lines) and SETEXT.match(lines[i + 1]) and _paragraph_line(line):
            out[i] = inline(line, refs)
            i += 2  # the underline stays blank
            continue
        if RULE.match(line) or REF_DEF.match(line):
            i += 1
            continue
        h = ATX.match(line)
        if h:
            out[i] = inline(h.group(2) or "", refs)
            i += 1
            continue
        out[i] = block_line(line, refs)
        i += 1
    result = "\n".join(out)
    return result.rstrip("\n") + "\n" if result.strip() else None


def block_line(line: str, refs: dict[str, str]) -> str:
    """A line of prose: quote markers, list markers and a hard break off."""
    while QUOTE.match(line):
        line = QUOTE.sub("", line, count=1)
    if line.rstrip().endswith("\\") and not line.rstrip().endswith("\\\\"):
        line = line.rstrip()[:-1]
    f = FOOT_DEF.match(line)
    if f:
        return f"{f.group(1)}: {inline(f.group(2), refs)}".rstrip()
    m = LIST.match(line)
    if not m:
        return inline(line, refs)
    rest = line[m.end() :]
    mark = f"{m.group(2)}." if m.group(2) else "-"
    t = TASK.match(rest)
    if t:
        mark += f" [{t.group(1)}]"  # as written: no word is added
        rest = rest[t.end() :]
    return f"{mark} {inline(rest, refs)}".rstrip()


EXTS = (".md", ".markdown")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: markdown.py mirror --from FOLDER --to MIRROR"


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


def places(text: str, source: list[str]) -> dict[str, str]:
    """The mirror contract's places: the line each passage starts on is the
    source's same line, but a table's header, moved onto its separator's
    line, came from the line above it too."""
    lines = text.splitlines()
    out = {}
    for i, s in enumerate(lines, 1):
        if s.strip() and (i == 1 or not lines[i - 2].strip()):
            moved = i >= 2 and _is_table_start(source, i - 2)
            out[str(i)] = f"lines {i - 1}-{i}" if moved else f"line {i}"
    return out


def write_places(dst: Path, rel: str, found: dict[str, str]) -> None:
    """The map, hidden beside the mirror, where the kernel never reads."""
    out = dst / ".places" / (rel + ".txt.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {"source": rel, "places": found}
    out.write_bytes((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            data = path.read_bytes()
            text = convert(data)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
            source = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            write_places(dst, rel.as_posix(), places(text, source.split("\n")))
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
