r"""org.py: Org-mode files as plain lines, line for line. Python 3.9+.

    python adapters/stdlib/org/org.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .org and .org_archive files (hidden folders and files
skipped) and writes each as the plain lines it holds, with Org's markup put
into words. The mirror has the same number of lines as the source and each
line is the source's line, so a passage found in the mirror is on that line of
the .org file:

    ** TODO [#A] Ring the vet  :home:pets:    ->   TODO [#A] Ring the vet :home:pets:
    SCHEDULED: <2024-03-05 Tue 09:00 +1w>     ->   SCHEDULED: 2024-03-05 09:00 +1w
    | Bean | 2024-04-02 | 3 |                 ->   Bean; 2024-04-02; 3

It adds no word of its own: a word written into passage after passage is
half of any two-word question, and would answer one about something the
folder doesn't hold. So the source's own words stay as written (TODO,
SCHEDULED, CLOCK, a property's name, a checkbox) and only Org's markup comes
off: stars, drawer and block marker lines, a timestamp's brackets and day
name, a link's brackets, emphasis markers where Org reads them as markup. A
heading with only headings under it is said once, on the headline below it
("Home › TODO Ring the vet"), so each part of an outline is its own passage.
A table's row is its cells, and its header moves down onto the rule under it,
so it begins the passage of its rows. Kept as written: source,
example and fixed-width lines. Blank: a table's rules and formulas, comments,
a comment block, and every #+ line but the title, subtitle, author, date, file
tags and a caption, and the ID and CUSTOM_ID properties (link targets).

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with nothing to say, or that cannot be read, is
skipped and counted.

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

HEADLINE = re.compile(r"^(\*+)\s+(.*?)\s*$")
TAGS = re.compile(r"\s+(:(?:[\w@#%]+:)+)$")
KEYWORD = re.compile(r"^\s*#\+(\w+):\s*(.*?)\s*$")
KEPT = ("title", "subtitle", "author", "date", "filetags", "caption")
BEGIN = re.compile(r"^\s*#\+begin_(\w+)", re.I)
VERBATIM_BLOCKS = {"src", "example"}
BLANK_BLOCKS = {"comment", "export", "html", "latex"}  # the last two: older Org
DRAWER = re.compile(r"^\s*:([\w-]+):\s*$")
PROPERTY = re.compile(r"^\s*:([\w-]+?)\+?:(?:\s+(.*?))?\s*$")
#: a link's target, not something said: org-roam puts an ID in every note,
#: and pandoc a CUSTOM_ID under every heading
LINK_IDS = {"ID", "CUSTOM_ID"}
DESCRIPTION = re.compile(r"^(\s*[-+]\s+)(.*?)\s+::(?:\s+|$)")

DAY = r"(?:\s+[^\s\d>\]+.-][^\s\d>\]]*)?"  # a day's name, in any language
STAMP = (r"[<\[](\d{4}-\d{2}-\d{2})" + DAY + r"(?:\s+(\d{1,2}:\d{2})(?:-(\d{1,2}:\d{2}))?)?"
         r"((?:\s+(?:\.\+|\+\+|\+|--?)\d+[hdwmy](?:/\d+[hdwmy])?)*)\s*[>\]]")  # fmt: skip
TIMESTAMP = re.compile(STAMP)
RANGE = re.compile(STAMP + "--" + STAMP)
LINK = re.compile(r"\[\[((?:[^\]\\]|\\.)+)\](?:\[([^\]]*)\])?\]")
OPENS = re.compile(
    r"\[\[(?:[^\]\\]|\\.)+\]\[(?=[^\]]*$)"
)  # a description going on below
CLOSES = re.compile(r"^([^\[]*?)\]\]")  # the end of one begun above
ANGLE_LINK = re.compile(r"<((?:https?|mailto|file|ftp):[^\s<>]+)>")
URL = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+")
FOOTNOTE = re.compile(r"\[fn:([^\]:]*)(?::([^\]]*))?\]")
TARGET = re.compile(r"<<<?([^<>\n]+?)>>>?")
MARKERS = "*/_=~+"
PRE = r"(?:(?<=^)|(?<=[\s\-({'\"]))"
POST = r"(?=$|[\s\-.,;:!?')}\"\[\\])"


def emphasis(marker: str) -> re.Pattern:
    m = re.escape(marker)
    return re.compile(PRE + m + r"([^\s" + m + r"](?:[^" + m + r"\n]*?[^\s" + m + r"])?)" + m + POST)  # fmt: skip


EMPHASIS = {m: emphasis(m) for m in MARKERS}


def stamp(day: str, start: str | None, end: str | None, rep: str | None) -> str:
    """One timestamp without its brackets or day's name: the date, the time
    or the times, and a repeater or warning as written."""
    out = day + (f" {start}" if start else "") + (f" to {end}" if end else "")
    return out + (" " + " ".join(rep.split()) if rep and rep.strip() else "")


def a_range(m: re.Match) -> str:
    first, second = stamp(*m.group(1, 2, 3, 4)), stamp(*m.group(5, 6, 7, 8))
    if m.group(1) == m.group(5) and m.group(6) and not m.group(7):  # one day, two times
        second = stamp(m.group(6), None, None, m.group(8))
    return f"{first} to {second}"


def dates(text: str) -> str:
    text = RANGE.sub(a_range, text)
    return TIMESTAMP.sub(lambda m: stamp(*m.groups()), text)


def inline(text: str) -> str:
    """One line's Org markup taken off: links, timestamps, footnotes, targets
    and emphasis. Verbatim and code are taken as written, and a web address
    is never read as emphasis. Runs of spaces become one."""
    held: list[str] = []

    def hold(s: str) -> str:
        held.append(s)
        return f"\0{len(held) - 1}\0"

    def link(m: re.Match) -> str:
        if m.group(2) is not None:
            return m.group(2)
        target = m.group(1).replace("\\]", "]").replace("\\[", "[")
        target = re.sub(r"^file:", "", target)
        return hold(target.lstrip("*#") if target[:1] in "*#" else target)

    indent = text[: len(text) - len(text.lstrip())]
    for marker in "=~":
        text = EMPHASIS[marker].sub(lambda m: hold(m.group(1)), text)
    text = LINK.sub(link, LINK.sub(link, text))  # twice: an image as a description
    text = CLOSES.sub(r"\1", OPENS.sub("", text))
    text = ANGLE_LINK.sub(lambda m: hold(m.group(1)), text)
    text = URL.sub(lambda m: hold(m.group(0)), text)
    text = dates(text)
    text = FOOTNOTE.sub(lambda m: f"({m.group(2)})" if m.group(2) else f"[{m.group(1)}]", text)  # fmt: skip
    text = TARGET.sub(r"\1", text)
    for marker in "*/_+":
        text = EMPHASIS[marker].sub(r"\1", text)
    text = re.sub(r"\s*\\\\\s*$", "", text)
    while "\0" in text:
        text = re.sub(r"\0(\d+)\0", lambda m: held[int(m.group(1))], text)
    text = " ".join(text.split())
    return indent + text if text else ""


def headline(rest: str) -> str:
    """A headline's text after its stars: its keyword, priority and cookie
    as written, its title's markup taken off, its tags as written."""
    m = TAGS.search(" " + rest)
    tags = m.group(1) if m else ""
    title = inline((" " + rest)[: m.start()] if m else rest)
    return f"{title} {tags}".strip()


def cells(row: str) -> list[str]:
    row = row.strip()
    if row.endswith("|"):
        row = row[:-1]
    return [inline(c.strip()) for c in row[1:].split("|")]


def table(rows: list[str]) -> list[str]:
    """A table's lines, each row's cells joined by "; ", an empty cell left
    out, and its rules blank. A header (the first row, when a rule is under
    it) moves down onto that rule, so it begins the passage its rows are in."""
    rule = [r.strip().startswith("|-") for r in rows]
    out = [
        "" if r else "; ".join(c for c in cells(row) if c) for r, row in zip(rule, rows)
    ]
    if len(rows) > 1 and not rule[0] and rule[1]:
        out[0], out[1] = "", out[0]
    return out


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    lines = text.split("\n")
    out: list[str] = []
    block = drawer = ""
    above: list[str] = []  # headings moved onto the headline under them
    i = 0
    while i < len(lines):
        raw = lines[i]
        bare = raw.strip()
        low = bare.lower()
        if block:
            if low.startswith("#+end_" + block):
                block = ""
                out.append("")
            elif block in BLANK_BLOCKS:
                out.append("")
            elif block in VERBATIM_BLOCKS:
                out.append(raw.rstrip())
            else:
                out.append(inline(bare))
        elif drawer:
            if low == ":end:":
                drawer = ""
                out.append("")
            elif drawer == "properties" and PROPERTY.match(raw):
                key, value = PROPERTY.match(raw).groups()
                value = "" if key.upper() in LINK_IDS else inline(value or "")
                out.append(f"{key}: {value}" if value else "")
            else:
                out.append(line(raw))
        elif HEADLINE.match(raw):
            stars, rest = HEADLINE.match(raw).groups()
            said = headline(rest)
            nxt = HEADLINE.match(lines[i + 1]) if i + 1 < len(lines) else None
            if nxt and len(nxt.group(1)) > len(stars):
                above.append(said)  # said once, on the headline under it
                out.append("")
            else:
                out.append(" › ".join([a for a in above if a] + [said]) if said else "")
                above = []
        elif BEGIN.match(raw):
            block = BEGIN.match(raw).group(1).lower()
            out.append("")
        elif low.startswith(("#+begin:", "#+end:")):  # a dynamic block's markers
            out.append("")
        elif DRAWER.match(raw) and low != ":end:":
            drawer = DRAWER.match(raw).group(1).lower()
            out.append("")
        elif bare.startswith("|"):
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            out.extend(table(lines[i:j]))
            i = j
            continue
        else:
            out.append(line(raw))
        i += 1
    result = "\n".join(out)
    return result.rstrip("\n") + "\n" if result.strip() else None


def line(raw: str) -> str:
    """A line of a section, outside any block, property or table."""
    bare = raw.strip()
    m = KEYWORD.match(raw)
    if m:
        word = m.group(1).lower()
        return f"{word}: {inline(m.group(2))}" if word in KEPT and m.group(2) else ""
    if bare == "#" or bare.startswith("# "):
        return ""
    if bare == ":" or bare.startswith(": "):
        return bare[2:]
    m = DESCRIPTION.match(raw)
    if m:
        return f"{m.group(1)}{inline(m.group(2))}: {inline(raw[m.end() :].strip())}".rstrip()  # fmt: skip
    return inline(raw.rstrip())


EXTS = (".org", ".org_archive")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: org.py mirror --from FOLDER --to MIRROR"


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
