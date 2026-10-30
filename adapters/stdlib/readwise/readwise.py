r"""readwise.py: Readwise's highlights export: every highlight with its book or article, and your note. Python 3.9+.

    python adapters/stdlib/readwise/readwise.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .csv files that are a Readwise export (a header with `Highlight`
and `Book Title`; hidden folders and files skipped; any other CSV skipped and
counted) and writes each highlight, oldest first, as a dated line:

    2024-03-02  The Hobbit by J.R.R. Tolkien, loc 120: "In a hole in the ground there lived a hobbit."  (note: the best opening)  [fantasy]
    2024-03-04  Staking tomatoes by Ana Lopez: "Tie the stem loosely."

The line is the day highlighted, the title and author, the location when the
export gives one (page, location or time), your highlight in quotation marks,
your note on it in brackets, and its tags. Whitespace is collapsed. A highlight
with no text but a note is written as the note alone. The Amazon book id, the
colour and the other columns are not copied.

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


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    s = words(v)
    return s[:10] if re.match(r"\d{4}-\d{2}-\d{2}", s) else ""


def convert(data: bytes) -> str | None:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    head = reader.fieldnames or []
    if "Highlight" not in head or "Book Title" not in head:
        return None
    rows = []
    for r in reader:
        text, note, title = (
            words(r.get("Highlight")),
            words(r.get("Note")),
            words(r.get("Book Title")),
        )
        if not (text or note):
            continue
        author = words(r.get("Book Author"))
        where = (
            f"{words(r.get('Location Type')) or 'loc'} {words(r['Location'])}".strip()
            if words(r.get("Location"))
            else ""
        )
        source = (
            title
            + (f" by {author}" if author else "")
            + (f", {where}" if where else "")
        )
        tags = [t.strip() for t in words(r.get("Tags")).split(",") if t.strip()]
        said = f'"{text}"' if text else ""
        bits = [
            f"{source}: {said}".rstrip(": ") if source else said,
            f"(note: {note})" if note and text else note if note else "",
            f"[{', '.join(tags)}]" if tags else "",
        ]
        when = day(r.get("Highlighted at"))
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

USAGE = "usage: readwise.py mirror --from FOLDER --to MIRROR"


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
