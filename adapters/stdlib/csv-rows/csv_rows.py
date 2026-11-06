r"""csv_rows.py: CSV and TSV tables as one passage per row. Python 3.9+.

    python adapters/stdlib/csv-rows/csv_rows.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .csv and .tsv files (hidden folders and files skipped) and
writes the header row once, as the first passage, then each data row as one
passage of its values, with a blank line between rows:

    Surname,Forename,Townland,Age        ->   [1] Surname; Forename; Townland; Age
    Considine,Honora,Caherfeenick,52     ->   [2] Considine; Honora; Caherfeenick; 52

The number in brackets is the line of the source file the row starts on (a
quoted value holding newlines starts on its first line), so a passage is found
again in the table by it. An empty cell keeps its place ("a; ; c") so each
value stays under its header; empty cells at the end of a row are dropped. A
row whose passage would pass the kernel's MAX_CHUNK is cut at a cell (or, for
one long cell, at a space) into lines that each start with the same number, so
nothing is cut off.

No word is written in every passage, not even the table's own headers: the
kernel serves a passage holding half a question's words, so a word in every
row would let "religion of Seamus" be answered by a row with no Seamus in it.

The delimiter: a .tsv is read by tabs. For a .csv, the first line that isn't a
note decides: the one of comma, tab, semicolon and pipe that cuts it into the
most cells, a tie going to the first in that order; a line none of them cuts is
one column. Nothing else is tried.

The header: the first line that isn't a note, unless one of its cells is a
number or a date (digits with only + - . , / : between them), as in a bank
export with no header; then every row is data.
Lines before it whose first cell starts with "#" are notes, kept with their
line number in brackets.

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
import json
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


def _lines(n: int, cells: list[str]) -> list[str]:
    """Row `n`'s cells as lines of at most MAX_CHUNK characters."""
    head = f"[{n}] "
    out: list[str] = []
    line, bare = head, True
    for cell in cells:
        joined = cell if bare else "; " + cell
        if len(line) + len(joined) <= kernel.MAX_CHUNK:
            line, bare = line + joined, False
            continue
        if not bare:
            out.append(line)
            line = head
        while len(line) + len(cell) > kernel.MAX_CHUNK:  # one cell too long
            room = kernel.MAX_CHUNK - len(line)
            cut = cell.rfind(" ", 1, room + 1)
            cut = cut if cut > 0 else room
            out.append(line + cell[:cut].rstrip())
            cell, line = cell[cut:].lstrip(), head
        line, bare = line + cell, False
    if not bare:
        out.append(line)
    return out


def convert(data: bytes, tsv: bool = False) -> str | None:
    """The passages of one table, or None when it has no data row."""
    found = placed(data, tsv)
    return "\n\n".join(p for p, _, _ in found) + "\n" if found else None


def placed(data: bytes, tsv: bool = False) -> list[tuple[str, int, int]]:
    """Each passage, with the first and last of the file's lines it holds: a
    row with a quoted cell can run over several. None when no data row."""
    lines = io.StringIO(data.decode("utf-8-sig"), newline="").readlines()
    first = next((i for i, x in enumerate(lines) if x.strip() and not _note(x)), None)
    if first is None:
        return []
    passages = [
        (f"[{i + 1}] {_clean(x)}", i + 1, i + 1)
        for i, x in enumerate(lines[:first])
        if x.strip()
    ]
    sep = delimiter(lines[first], tsv)
    table = io.StringIO("".join(lines[first:]), newline="")
    reader = csv.reader(table, delimiter=sep, strict=True)
    header = False
    rows = 0
    found = False
    for row in reader:
        n = first + 1 + rows
        rows = reader.line_num
        cells = [_clean(cell) for cell in row]
        while cells and not cells[-1]:
            cells.pop()
        if not cells:
            continue
        passages.append(("\n".join(_lines(n, cells)), n, first + rows))
        if not header:
            header = True
            if not any(NUMBER.fullmatch(c) for c in cells):
                continue
        found = True
    return passages if found else []


def places(found: list[tuple[str, int, int]]) -> dict[str, str]:
    """The mirror contract's places (adapters/stdlib/ci/README.md): each
    passage's mirror line, a blank line between passages, to its row's
    lines in the file."""
    out, line = {}, 1
    for text, a, b in found:
        out[str(line)] = f"line {a}" if a == b else f"lines {a}-{b}"
        line += text.count("\n") + 2
    return out


def write_places(dst: Path, rel: str, found: dict[str, str]) -> None:
    """The map, hidden beside the mirror, where the kernel never reads."""
    out = dst / ".places" / (rel + ".txt.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {"source": rel, "places": found}
    out.write_bytes((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))


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


# differs on purpose: convert needs to know a .tsv
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            found = placed(path.read_bytes(), path.name.lower().endswith(".tsv"))
            if not found:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(
                ("\n\n".join(p for p, _, _ in found) + "\n").encode("utf-8")
            )
            write_places(dst, rel.as_posix(), places(found))
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
