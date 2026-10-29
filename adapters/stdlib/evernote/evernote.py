r"""evernote.py: Evernote's .enex export files: each note as plain text. Python 3.9+.

    python adapters/stdlib/evernote/evernote.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .enex files (hidden folders and files skipped) and writes each
note as a paragraph with its title, dates and tags, then its text:

    note: Allotment plan (notebook: Garden)
    created: 2024-03-03 10:15; updated: 2024-03-05 08:00
    tags: garden, plots
    from: Ada Example, https://example.org/plots
    attachments: plan.pdf, photo.jpg

    Plot 14 gets the beans.
    [x] Order seed
    [ ] Fix the gate

The notebook is the export file's name, since a .enex file is one notebook (or
a selection). The note's body is Evernote's own markup read as text: paragraphs
and line breaks kept, list items as "- ", checkboxes as [ ] and [x], and an
attachment named but not read. Dates are Evernote's UTC times written as
YYYY-MM-DD HH:MM. Notes are in the file's order; a file with several notes
gives several paragraphs.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no note, or that cannot be read, is skipped
and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import html.parser
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BLOCK = {
    "div",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "pre",
    "blockquote",
    "ul",
    "ol",
    "table",
    "hr",
}


class _Text(html.parser.HTMLParser):
    """An ENML body as text: blocks as lines, lists as dashes, todos as boxes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK or tag == "br":
            self.out.append("\n")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in ("td", "th"):
            self.out.append(" ")
        elif tag == "en-todo":
            self.out.append("[x] " if dict(attrs).get("checked") == "true" else "[ ] ")

    def handle_endtag(self, tag):
        if tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.out).split("\n")]
        return "\n".join(line for line in lines if line)


def when(value: str | None) -> str:
    v = (value or "").strip()
    return (
        f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[9:11]}:{v[11:13]}"
        if len(v) >= 13 and v[8:9] == "T"
        else v
    )


def body(enml: str) -> str:
    parser = _Text()
    parser.feed(re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", enml))
    parser.close()
    return parser.text()


def convert(data: bytes, notebook: str = "") -> str | None:
    root = ET.fromstring(data)
    blocks = []
    for note in root.iter("note"):
        get = lambda tag: (note.findtext(tag) or "").strip()  # noqa: E731
        attrs = note.find("note-attributes")
        author = (attrs.findtext("author") or "").strip() if attrs is not None else ""
        source = (
            (attrs.findtext("source-url") or "").strip() if attrs is not None else ""
        )
        files = [
            (r.findtext("resource-attributes/file-name") or "").strip()
            for r in note.findall("resource")
        ]
        lines = [
            f"note: {get('title') or '(untitled)'}"
            + (f" (notebook: {notebook})" if notebook else "")
        ]
        dates = "; ".join(
            x
            for x in (
                f"created: {when(get('created'))}" if get("created") else "",
                f"updated: {when(get('updated'))}" if get("updated") else "",
            )
            if x
        )
        if dates:
            lines.append(dates)
        tags = [
            t.text.strip() for t in note.findall("tag") if t.text and t.text.strip()
        ]
        if tags:
            lines.append("tags: " + ", ".join(tags))
        if author or source:
            lines.append("from: " + ", ".join(x for x in (author, source) if x))
        if any(files):
            lines.append("attachments: " + ", ".join(f for f in files if f))
        text = body(get("content")) if get("content") else ""
        blocks.append("\n".join(lines) + ("\n\n" + text if text else ""))
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".enex",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: evernote.py mirror --from FOLDER --to MIRROR"


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
            text = convert(path.read_bytes(), path.stem)
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
