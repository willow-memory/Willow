r"""letterboxd.py: Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines. Python 3.9+.

    python adapters/stdlib/letterboxd/letterboxd.py mirror --from FOLDER --to MIRROR

Walks FOLDER for the CSV files of a Letterboxd export (diary.csv, ratings.csv,
reviews.csv, watched.csv, watchlist.csv: a header with `Name` and `Letterboxd
URI`; hidden folders and files skipped; any other CSV skipped and counted) and
writes each row, oldest first, as a dated line:

    2024-03-02  watched Heat (1995)  4.5/5  rewatch  [crime, night]
    2024-03-04  rated Alien (1979)  5/5
    2024-03-09  watched Paddington 2 (2017)  4/5  Funnier than it has any right to be.

A row with a `Watched Date` is "watched" (the date it was watched, not the day it
was logged); one with a rating and no watched date is "rated"; the others are
"listed" (the watchlist, the watched list). The rating is out of five as
Letterboxd gives it. A review follows as written, whitespace collapsed; tags go
in brackets. Letterboxd's own web address for the film is not copied.

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
    if "Name" not in head or "Letterboxd URI" not in head:
        return None
    rows = []
    for r in reader:
        name = words(r.get("Name"))
        if not name:
            continue
        watched = day(r.get("Watched Date"))
        when = watched or day(r.get("Date"))
        verb = (
            "watched"
            if "Watched Date" in head and watched
            else "rated"
            if stars(r.get("Rating"))
            else "listed"
        )
        title = name + (f" ({words(r['Year'])})" if words(r.get("Year")) else "")
        tags = [t.strip() for t in words(r.get("Tags")).split(",") if t.strip()]
        bits = [
            f"{verb} {title}",
            stars(r.get("Rating")),
            "rewatch" if words(r.get("Rewatch")).lower() == "yes" else "",
            words(r.get("Review")),
            f"[{', '.join(tags)}]" if tags else "",
        ]
        rows.append(
            (
                when,
                "  ".join(x for x in ([when] if when else []) + [b for b in bits if b]),
            )
        )
    return (
        "\n".join(t for _w, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".csv",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: letterboxd.py mirror --from FOLDER --to MIRROR"


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
