r"""takeout.py: Google Takeout's My Activity and YouTube history as dated lines. Python 3.9+.

    python adapters/stdlib/takeout/takeout.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json and .html files that are a My Activity export (hidden
folders and files skipped; any other JSON or HTML skipped and counted) and
writes each activity as one dated line, in the file's own order:

    2024-03-03 10:15 Search: Searched for leek soup

    2024-03-02 19:40 YouTube: Watched Leek and potato soup, channel: Soup Kitchen

Takeout writes the same shape for every product: `My Activity/<Product>/
MyActivity.json` (or `.html`), and YouTube's `history/watch-history` and
`search-history`, as JSON or HTML. A JSON file is a list of activities, each
with a `header` (the product), a `title` ("Searched for ..."), a `time` and
`subtitles` (a watch's channel); an HTML file is the same in `outer-cell`
blocks, a `header-cell` naming the product and a `content-cell` holding the
title, the channel and the date. A file is told by what it holds, not by its
name.

The time is the file's: a JSON `time` is in UTC, written to the minute. An
HTML date is written in the account's own time zone and language; an English
one ("Mar 3, 2024, 10:15:22 AM GMT", or "3 Mar 2024, 10:15:22 GMT") is
written to the minute, with its zone after it unless that is GMT or UTC. A
date in another language, or one that doesn't read in full, is kept as
written in brackets ("[3 mars 2024, 10:15:22 UTC]"), never guessed, and an
activity with no date at all says "[no date]".

A watch's channel follows its title; any other activity's subtitles follow in
brackets, and its details ("From Google Ads") in square brackets. Links,
`products`, `activityControls` and places (`locationInfos`) are not copied.

Each activity is its own passage, with a blank line between: the kernel
serves a passage that holds half of a question's words, so "when did I
search for leek soup" is answered by the one line that holds the search and
its date, never by a run of other searches that happens to hold "soup".

Each file is written to MIRROR at the same relative path with `.txt` added.
A mirror bigger than the kernel reads from one file (`kernel.MAX_FILE`, 1 MB),
as years of YouTube history are, is cut between activities into parts it can:
`NAME.txt`, then `NAME.part2.txt` and on. Parts a shorter earlier run left
behind are removed. FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MONTHS = {
    m: i
    for i, names in enumerate(
        (
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ),
        1,
    )
    for m in names
}
ZONE = r"(?P<zone>[A-Z]{2,5}(?:[+-]\d{1,2}(?::\d{2})?)?)"
CLOCK = r"(?P<h>\d{1,2}):(?P<mi>\d{2})(?::\d{2})?"
#: "Mar 3, 2024, 10:15:22 AM GMT" (US English) and
#: "3 Mar 2024, 10:15:22 GMT" (British English)
US = re.compile(
    rf"(?P<mon>[A-Za-z]+)\.? (?P<d>\d{{1,2}}), (?P<y>\d{{4}}),? {CLOCK} ?(?P<ap>[AaPp]\.?[Mm]\.?) {ZONE}"
)
GB = re.compile(
    rf"(?P<d>\d{{1,2}}) (?P<mon>[A-Za-z]+)\.? (?P<y>\d{{4}}),? {CLOCK} {ZONE}"
)
ISO = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]00:?00)"
)


def clean(text: object) -> str:
    """A text with its runs of whitespace (no-break and thin spaces too) made one space."""
    return " ".join(text.split()) if isinstance(text, str) else ""


def stamp(y: int, mo: int, d: int, h: int, mi: int) -> str | None:
    try:
        return datetime(y, mo, d, h, mi).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return None


def json_when(raw: object) -> str:
    """A JSON `time` as "YYYY-MM-DD HH:MM" (UTC), else as written."""
    text = clean(raw)
    if not text:
        return "[no date]"
    m = ISO.fullmatch(text)
    got = m and stamp(*(int(g) for g in m.groups()))
    return got or f"[{text}]"


def html_when(raw: str) -> str:
    """An HTML date line to the minute, with its zone unless UTC; else as written."""
    text = clean(raw)
    if not text:
        return "[no date]"
    m = US.fullmatch(text) or GB.fullmatch(text)
    mo = m and MONTHS.get(m.group("mon").lower())
    if not m or not mo:
        return f"[{text}]"
    h = int(m.group("h"))
    if "ap" in m.groupdict():
        if not 1 <= h <= 12:
            return f"[{text}]"
        h = h % 12 + (12 if m.group("ap")[0] in "Pp" else 0)
    got = stamp(int(m.group("y")), mo, int(m.group("d")), h, int(m.group("mi")))
    if not got:
        return f"[{text}]"
    zone = m.group("zone")
    return got if zone in ("GMT", "UTC") else f"{got} {zone}"


def line(
    when: str, product: str, title: str, subs: list[str], details: list[str]
) -> str:
    """One activity: its time, its product, its title, its channel or subtitles."""
    text = title or "(no title)"
    if subs and text.startswith("Watched "):
        text += ", channel: " + "; ".join(subs)
    elif subs:
        text += " (" + "; ".join(subs) + ")"
    if details:
        text += " [" + "; ".join(details) + "]"
    return f"{when} {product or '(no product)'}: {text}"


def from_json(data: bytes) -> list[str] | None:
    """A My Activity JSON file's lines, or None when it isn't one."""
    try:
        items = json.loads(data.decode("utf-8-sig"))
    except ValueError:
        return None
    if not isinstance(items, list) or not items:
        return None
    if not all(
        isinstance(it, dict) and "header" in it and "title" in it for it in items
    ):
        return None
    out = []
    for it in items:
        product = clean(it.get("header"))
        if not product and isinstance(it.get("products"), list) and it["products"]:
            product = clean(it["products"][0])
        names = []
        for key in ("subtitles", "details"):
            got = it.get(key) if isinstance(it.get(key), list) else []
            names.append(
                [n for s in got if isinstance(s, dict) and (n := clean(s.get("name")))]
            )
        out.append(
            line(json_when(it.get("time")), product, clean(it.get("title")), *names)
        )
    return out


class Cells(HTMLParser):
    """The `outer-cell` blocks of a My Activity page: for each, its header, its
    body's lines (split at <br>) and its caption's lines, a bold label as
    "\x00label"."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[dict] = []
        self.stack: list[str | None] = []  # each open div's part, or None

    def part(self) -> str | None:
        return next((p for p in reversed(self.stack) if p), None)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "div":
            cls = (dict(attrs).get("class") or "").split()
            role = None
            if "outer-cell" in cls:
                self.cells.append({"header": "", "body": "", "caption": ""})
                role = "outer"
            elif self.cells and "header-cell" in cls:
                role = "header"
            elif self.cells and "content-cell" in cls:
                if "mdl-typography--caption" in cls:
                    role = "caption"
                elif "mdl-typography--text-right" not in cls:
                    role = "body"
            self.stack.append(role)
        elif tag == "br" and self.part() in ("body", "caption", "header"):
            self.cells[-1][self.part()] += "\n"
        elif tag == "b" and self.part() == "caption":
            self.cells[-1]["caption"] += "\n\x00"

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.stack:
            self.stack.pop()
        elif tag == "b" and self.part() == "caption":
            self.cells[-1]["caption"] += "\n"

    def handle_data(self, data: str) -> None:
        if self.part() in ("body", "caption", "header"):  # a line ends only at <br>
            self.cells[-1][self.part()] += data.replace("\n", " ").replace("\r", " ")


def lines_of(text: str) -> list[str]:
    return [t for t in (clean(x) for x in text.split("\n")) if t and t != "\x00"]


def from_html(data: bytes) -> list[str] | None:
    """A My Activity HTML page's lines, or None when it isn't one."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    if "outer-cell" not in text or "content-cell" not in text:
        return None
    page = Cells()
    page.feed(text)
    page.close()
    out = []
    for cell in page.cells:
        body = lines_of(cell["body"])
        if not body:
            continue
        title, *rest = body
        when = html_when(rest.pop()) if rest else "[no date]"
        details, label = [], ""
        for t in lines_of(cell["caption"]):
            if t.startswith("\x00"):
                label = t[1:].strip().rstrip(":")
            elif label == "Details":
                details.append(t)
        product = " ".join(lines_of(cell["header"]))
        out.append(line(when, product, title, rest, details))
    return out or None


def convert(data: bytes, name: str) -> str | None:
    """The mirror of one file, each activity a passage, or None when it isn't one."""
    got = from_json(data) if name.lower().endswith(".json") else from_html(data)
    return "\n\n".join(got) + "\n" if got else None


EXTS = (".json", ".html", ".htm")
ERRORS = (OSError, UnicodeDecodeError, ValueError, RecursionError)

USAGE = "usage: takeout.py mirror --from FOLDER --to MIRROR"


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


def parts(text: str, limit: int = kernel.MAX_FILE) -> list[str]:
    """`text` cut between its passages into pieces of at most `limit` bytes as
    UTF-8. A single passage longer than that is shortened to fit, never split."""
    out: list[str] = []
    piece: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        para = para.strip("\n") + "\n\n"
        raw = len(para.encode("utf-8"))
        if raw > limit:
            para = para.encode("utf-8")[: limit - 2].decode("utf-8", "ignore") + "\n\n"
            raw = len(para.encode("utf-8"))
        if piece and size + raw > limit:
            out.append("".join(piece)[:-1])
            piece, size = [], 0
        piece.append(para)
        size += raw
    if piece:
        out.append("".join(piece)[:-1])
    return out


def _part_name(name: str, n: int) -> str:
    return f"{name}.txt" if n == 1 else f"{name}.part{n}.txt"


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes(), path.name)
            if text is None:
                skipped += 1
                continue
            folder = dst.joinpath(rel.parent)
            folder.mkdir(parents=True, exist_ok=True)
            pieces = parts(text)
            for n, piece in enumerate(pieces, 1):
                (folder / _part_name(rel.name, n)).write_bytes(piece.encode("utf-8"))
            n = len(pieces) + 1
            while (folder / _part_name(rel.name, n)).is_file():
                (folder / _part_name(rel.name, n)).unlink()
                n += 1
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
