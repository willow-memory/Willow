r"""goodreads.py: Goodreads and StoryGraph exports: the books you've read, when, and what you thought. Python 3.9+.

    python adapters/stdlib/goodreads/goodreads.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .csv files that are a library export from Goodreads
(`goodreads_library_export.csv`, with `Title` and `Exclusive Shelf` columns) or
StoryGraph (`Title` and `Read Status`; hidden folders and files skipped; any other
CSV skipped and counted) and writes each book, oldest first, as a dated line:

    2024-03-02  read The Hobbit by J.R.R. Tolkien  4/5  A comfort read. [fantasy, favourites]
    2024-03-09  reading Dune by Frank Herbert
    2023-12-01  to read Piranesi by Susanna Clarke

The date is when you finished it (Goodreads' Date Read, StoryGraph's Last Date
Read); a book you have not finished takes the day it was added. The verb is the
shelf: read, reading, or to read. The rating is out of five (a 0 is no rating),
your review follows as written with whitespace collapsed, and shelves or tags
go in brackets. Dates are read as Goodreads writes them (2024/03/02) and as
StoryGraph does (2024/03/02 or 2024-03-02). Private notes, ISBNs, page counts
and the rest are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

VERBS = {
    "read": "read",
    "currently-reading": "reading",
    "currently reading": "reading",
    "to-read": "to read",
    "to read": "to read",
    "did-not-finish": "gave up on",
    "dnf": "gave up on",
}


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    m = re.match(r"(\d{4})[/-](\d{2})[/-](\d{2})", words(v))
    return "-".join(m.groups()) if m else ""


def stars(v: object) -> str:
    s = words(v)
    try:
        x = float(s)
    except ValueError:
        return ""
    return f"{x:g}/5" if 0 < x <= 5 else ""


def convert(data: bytes) -> str | None:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    head = reader.fieldnames or []
    shelf_col = (
        "Exclusive Shelf"
        if "Exclusive Shelf" in head
        else "Read Status"
        if "Read Status" in head
        else ""
    )
    if "Title" not in head or not shelf_col:
        return None
    rows = []
    for r in reader:
        title = words(r.get("Title"))
        if not title:
            continue
        shelf = words(r.get(shelf_col)).lower()
        verb = VERBS.get(shelf, shelf or "listed")
        done = day(r.get("Date Read")) or day(r.get("Last Date Read"))
        when = (
            done
            if verb in ("read", "gave up on") and done
            else day(r.get("Date Added")) or done
        )
        author = words(r.get("Author")) or words(r.get("Authors"))
        shelves = [
            s.strip()
            for s in (words(r.get("Bookshelves")) or words(r.get("Tags"))).split(",")
            if s.strip()
        ]
        bits = [
            f"{verb} {title}" + (f" by {author}" if author else ""),
            stars(r.get("My Rating") or r.get("Star Rating")),
            words(r.get("My Review")) or words(r.get("Review")),
            f"[{', '.join(shelves)}]" if shelves else "",
        ]
        rows.append(
            (when, "  ".join(([when] if when else []) + [b for b in bits if b]))
        )
    return (
        "\n".join(t for _w, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".csv",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: goodreads.py mirror --from FOLDER --to MIRROR"


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
