"""books.py: your Kindle highlights and your epub books, as plain text the kernel reads.

    python adapters/stdlib/books/books.py mirror --from FOLDER --to MIRROR

Walks FOLDER for two kinds of file, skipping hidden folders and files:

- a Kindle `My Clippings.txt` (the name in any capitalisation). Each highlight
  or note becomes one paragraph. Books are sorted by title; each book's entries
  keep their order in the file:

      2024-03-03  Book Title (Author), page 12
      The highlighted words, exactly as Kindle saved them.

  A bookmark has no text, so it is skipped. A highlight whose "Added on" date
  cannot be read is written as `undated` rather than dropped.

- an .epub file. Its text, in spine (reading) order, with scripts and styles
  dropped and each block element as its own paragraph. The first line names
  the book:

      book: TITLE by AUTHOR

Each one is written to MIRROR at the same relative path with `.txt` added:
`kindle/My Clippings.txt` becomes `MIRROR/kindle/My Clippings.txt.txt`. FOLDER
is only read. Originals are never modified and nothing is written inside it.
A file that cannot be parsed is skipped and counted, never a crash.

    wrote 3 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of your highlights and books.
"""

from __future__ import annotations

import html.parser
import os
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: books.py mirror --from FOLDER --to MIRROR"
DIVIDER = re.compile(r"={10,}")
META = re.compile(r"^- Your (Highlight|Note|Bookmark)\b")
ADDED = re.compile(r"Added on (.+?)\s*$")
PAGE = re.compile(r"\bon page (\S+)")
LOCATION = re.compile(r"\bLocation ([\d-]+)")
DATE_FORMATS = (
    "%A, %d %B %Y %H:%M:%S",  # Sunday, 3 March 2024 10:15:22
    "%A, %B %d, %Y %I:%M:%S %p",  # Sunday, March 3, 2024 10:15:22 AM
    "%A, %B %d, %Y %H:%M:%S",  # Sunday, March 3, 2024 10:15:22
)
BLOCK = frozenset(
    "address article aside blockquote br dd div dl dt figcaption footer h1 h2 h3 "
    "h4 h5 h6 header hr li ol p pre section table td th title tr ul".split()
)
SKIP = frozenset({"script", "style"})


class Unreadable(Exception):
    """An epub whose structure does not hold together (no OPF, a spine item
    missing from the manifest). Counted as skipped, like any unparseable file."""


def clippings_text(raw: bytes) -> str | None:
    """The mirror text for a Kindle clippings file, or None if no entry in it
    has the Kindle shape at all (it is not a clippings file)."""
    entries = []
    block: list[str] = []
    for line in raw.decode("utf-8-sig").splitlines() + ["=" * 10]:
        if DIVIDER.fullmatch(line.strip()):
            entry = _entry(block)
            if entry:
                entries.append(entry)
            block = []
        else:
            block.append(line)
    if not entries:
        return None
    kept = [e for e in entries if e["kind"] != "Bookmark" and e["text"]]
    if not kept:
        return "No highlights in this file.\n"
    by_book: dict[str, list[dict]] = {}
    for e in kept:
        by_book.setdefault(e["book"], []).append(e)
    out = []
    for book in sorted(by_book):
        for e in by_book[book]:
            where = ""
            if e["page"]:
                where = f", page {e['page']}"
            elif e["location"]:
                where = f", location {e['location']}"
            out.append(f"{e['date'] or 'undated'}  {book}{where}\n{e['text']}\n\n")
    return "".join(out)


def _entry(block: list[str]) -> dict | None:
    """One clippings entry: title line, meta line, blank, text. None if the
    block is not one."""
    lines = [ln.strip() for ln in block]
    nonblank = [i for i, ln in enumerate(lines) if ln]
    if len(nonblank) < 2:
        return None
    meta = META.match(lines[nonblank[1]])
    if not meta:
        return None
    meta_line = lines[nonblank[1]]
    added = ADDED.search(meta_line)
    page = PAGE.search(meta_line)
    location = LOCATION.search(meta_line)
    text = "\n".join(ln for ln in lines[nonblank[1] + 1 :] if ln)
    return {
        "kind": meta.group(1),
        "book": lines[nonblank[0]],
        "date": _iso(added.group(1)) if added else None,
        "page": page.group(1) if page else "",
        "location": location.group(1) if location else "",
        "text": text,
    }


def _iso(added: str) -> str | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(added, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


class _Paragraphs(html.parser.HTMLParser):
    """Text of an XHTML document, one paragraph per block element. Script and
    style content is dropped; whitespace inside a paragraph is collapsed."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paras: list[str] = []
        self.buf: list[str] = []
        self.skip = 0

    def _flush(self) -> None:
        text = " ".join("".join(self.buf).split())
        if text:
            self.paras.append(text)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag in BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK:
            self._flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def close(self):
        super().close()
        self._flush()


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def epub_text(path: Path) -> str:
    """The book's text in spine order, under a `book:` line. Raises
    Unreadable, or a zip/XML/IO error, if the file is not a usable epub."""
    with zipfile.ZipFile(path) as z:
        container = ET.fromstring(z.read("META-INF/container.xml"))
        roots = [
            el.get("full-path")
            for el in container.iter()
            if _local(el.tag) == "rootfile"
        ]
        if not roots or not roots[0]:
            raise Unreadable("no rootfile in container.xml")
        opf_path = roots[0]
        opf = ET.fromstring(z.read(opf_path))
        opf_dir = posixpath.dirname(opf_path)
        titles = [
            (el.text or "").strip() for el in opf.iter() if _local(el.tag) == "title"
        ]
        authors = [
            (el.text or "").strip() for el in opf.iter() if _local(el.tag) == "creator"
        ]
        manifest = {
            el.get("id"): el.get("href")
            for el in opf.iter()
            if _local(el.tag) == "item"
        }
        spine = [el.get("idref") for el in opf.iter() if _local(el.tag) == "itemref"]
        paras: list[str] = []
        for idref in spine:
            href = manifest.get(idref)
            if not href:
                raise Unreadable(f"spine item {idref!r} is not in the manifest")
            name = posixpath.normpath(posixpath.join(opf_dir, unquote(href)))
            parser = _Paragraphs()
            parser.feed(z.read(name).decode("utf-8"))
            parser.close()
            paras.extend(parser.paras)
    title = next((t for t in titles if t), path.stem)
    authors = [a for a in authors if a]
    by = f" by {', '.join(authors)}" if authors else ""
    return f"book: {title}{by}\n\n" + "".join(p + "\n\n" for p in paras)


def _sources(folder: Path) -> list[Path]:
    """Clippings files and epubs under `folder`, sorted by relative path.
    Hidden folders and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith("."):
                continue
            p = Path(dirpath) / name
            lower = name.lower()
            if (lower == "my clippings.txt" or lower.endswith(".epub")) and p.is_file():
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
            if path.name.lower().endswith(".epub"):
                text = epub_text(path)
            else:
                text = clippings_text(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except (
            OSError,
            UnicodeDecodeError,
            KeyError,
            RuntimeError,
            NotImplementedError,
            ET.ParseError,
            zipfile.BadZipFile,
            Unreadable,
        ):
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
