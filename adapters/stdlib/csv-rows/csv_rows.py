r"""csv_rows.py: CSV and TSV tables as one passage per row. Python 3.9+.

    python adapters/stdlib/csv-rows/csv_rows.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .csv and .tsv files (hidden folders and files skipped) and
writes each data row as one passage, every value beside its column's header,
with a blank line between rows:

    Surname,Forename,Townland,Age        ->   row 2: Surname: Considine; Forename: Honora; Townland: Caherfeenick; Age: 52
    Considine,Honora,Caherfeenick,52

N in "row N" is the line of the source file the row starts on (a quoted value
holding newlines starts on its first line), so a passage is found again in the
table by its number. An empty cell is left out. A cell beyond the header is
"column K", as is a header cell that is blank. A row whose passage would pass
the kernel's MAX_CHUNK is cut at a cell (or, for one long cell, at a space)
into lines that each start "row N, continued", so nothing is cut off.

The delimiter: a .tsv is read by tabs. For a .csv, the first line that isn't a
note decides: the one of comma, tab, semicolon and pipe that cuts it into the
most cells, a tie going to the first in that order; a line none of them cuts is
one column. Nothing else is tried.

The header: the first line that isn't a note, unless one of its cells is a
number or a date (digits with only + - . , / : between them), as in a bank
export with no header; then every row is data and each cell is "column K".
Lines before it whose first cell starts with "#" are notes, kept as "line N:"
with their text.

The text must be UTF-8, with or without a byte-order mark; anything else is
skipped and counted, never decoded by guess. So is a table with no data row (a
header alone, or nothing) and one Python's csv module can't read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import csv
import io
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

DELIMITERS = (",", "\t", ";", "|")
NUMBER = re.compile(r"[+-]?\d+(?:[.,/:-]\d+)*")


def _note(line: str) -> bool:
    return line.lstrip().lstrip('"').startswith("#")


def delimiter(line: str, tsv: bool) -> str:
    """The delimiter of a table whose first line (not a note) is `line`."""
    if tsv:
        return "\t"
    best, most = ",", 1
    for d in DELIMITERS:
        cells = len(next(csv.reader([line], delimiter=d), []))
        if cells > most:
            best, most = d, cells
    return best


def _clean(value: str) -> str:
    return " ".join(value.split())


def _lines(n: int, pairs: list[str]) -> list[str]:
    """Row `n`'s pairs as lines of at most MAX_CHUNK characters."""
    head, more = f"row {n}: ", f"row {n}, continued: "
    out: list[str] = []
    line = head
    for pair in pairs:
        joined = pair if line in (head, more) else "; " + pair
        if len(line) + len(joined) <= kernel.MAX_CHUNK:
            line += joined
            continue
        if line not in (head, more):
            out.append(line)
            line = more
        lo = pair.find(": ") + 2  # a header is never parted from its value
        while len(line) + len(pair) > kernel.MAX_CHUNK:  # one cell too long
            room = kernel.MAX_CHUNK - len(line)
            cut = pair.rfind(" ", lo, room + 1)
            cut = cut if cut >= lo else room
            out.append(line + pair[:cut].rstrip())
            pair, line, lo = pair[cut:].lstrip(), more, 1
        line += pair
    if line not in (head, more):
        out.append(line)
    return out


def convert(data: bytes, tsv: bool = False) -> str | None:
    """The passages of one table, or None when it has no data row."""
    lines = io.StringIO(data.decode("utf-8-sig"), newline="").readlines()
    first = next((i for i, x in enumerate(lines) if x.strip() and not _note(x)), None)
    if first is None:
        return None
    passages = [
        f"line {i + 1}: {_clean(x)}" for i, x in enumerate(lines[:first]) if x.strip()
    ]
    sep = delimiter(lines[first], tsv)
    table = io.StringIO("".join(lines[first:]), newline="")
    reader = csv.reader(table, delimiter=sep, strict=True)
    header: list[str] | None = None
    rows = 0
    for row in reader:
        n = first + 1 + rows
        rows = reader.line_num
        if not any(cell.strip() for cell in row):
            continue
        if header is None:
            header = [_clean(h) for h in row]
            if not any(NUMBER.fullmatch(h) for h in header):
                continue
            header = []
        names = [header[k] if k < len(header) else "" for k in range(len(row))]
        pairs = [
            f"{name or f'column {k + 1}'}: {_clean(cell)}"
            for k, (name, cell) in enumerate(zip(names, row))
            if cell.strip()
        ]
        passages.append("\n".join(_lines(n, pairs)))
    if not any(p.startswith("row ") for p in passages):
        return None
    return "\n\n".join(passages) + "\n"


EXTS = (".csv", ".tsv")
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: csv_rows.py mirror --from FOLDER --to MIRROR"


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
            text = convert(path.read_bytes(), path.name.lower().endswith(".tsv"))
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
