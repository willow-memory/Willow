r"""hurdat2.py: NOAA's hurricane track file (HURDAT2), one passage per track row, the storm's name and id on every one. Python 3.9+.

    python adapters/stdlib/hurdat2/hurdat2.py mirror --from FOLDER --to MIRROR

HURDAT2 names a storm once, on a header line, and the track rows under it
are numbers and codes:

    AL152017,              MARIA,     68,
    20170920, 1015, L, HU, 18.0N,  65.9W, 135,  920, ...

so a question naming "Maria" finds none of Maria's rows. Here each storm is
a header passage, then each row a passage that starts with the storm's name
and id, with a blank line between passages:

    [52489] MARIA AL152017; 68 track rows, 2017-09-16 to 2017-10-02; each row: date time UTC; status; record; position; wind kt; pressure mb

    [52490] MARIA AL152017; 2017-09-16 12:00; tropical depression; ; 12.2N 49.7W; 30; 1006

    [52627] MARIA AL152017; 2017-09-20 10:15; hurricane; landfall; 18.0N 65.9W; 135; 920

The number in brackets is the line of the source file, so a passage is found
again in it. The labels ("wind kt") are written once, on the header, never
in a row: the kernel serves a passage holding half a question's words, so a
label in every row would let a question about something the file lacks be
answered by an unrelated row. An unnamed storm (NHC's UNNAMED) is its id.

Two codes are written as the words NHC's format document gives them: the
status (HU hurricane, TS tropical storm, TD tropical depression, EX
extratropical cyclone, SD subtropical depression, SS subtropical storm, LO
low, WV tropical wave, DB disturbance) and the record identifier (L
landfall, P minimum pressure, I peak intensity, C closest approach, S status
change, G genesis, W maximum wind, T additional track point); a code that
isn't one of those is kept as written. Position, wind (knots) and pressure
(millibars) are copied as written; a missing value (-99, -999) is an empty
cell. The wind-radii columns are not carried.

A file is read only if it is UTF-8 and its first line is a storm header and
every header's count of rows is the rows that follow it; anything else is
skipped and counted, never repaired. A mirror file holds at most 900,000
bytes, cut between storms (the kernel reads no more than a megabyte of a
file), so a long file is written as NAME.part0.txt, NAME.part1.txt, and so
on. FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

HEADER = re.compile(r"([A-Z]{2}\d{6}),\s*([^,]*?)\s*,\s*(\d+),\s*")
ROW = re.compile(r"(\d{8}),\s*(\d{4}),")
STATUS = {
    "TD": "tropical depression", "TS": "tropical storm", "HU": "hurricane",
    "EX": "extratropical cyclone", "SD": "subtropical depression",
    "SS": "subtropical storm", "LO": "low", "WV": "tropical wave",
    "DB": "disturbance",
}  # fmt: skip
RECORD = {
    "L": "landfall", "P": "minimum pressure", "I": "peak intensity",
    "C": "closest approach", "S": "status change", "G": "genesis",
    "W": "maximum wind", "T": "additional track point",
}  # fmt: skip
PART = 900_000  # bytes of a mirror file: under the kernel's megabyte

EXT = ".txt"
USAGE = "usage: hurdat2.py mirror --from FOLDER --to MIRROR"


def _day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def storms(text: str) -> list[tuple[str, list[tuple[int, str]]]] | None:
    """The file's storms as (header passage, [(line, row passage)]) placed by
    line, or None when it is not a HURDAT2 file this reads: a first line that
    is no header, a count that isn't the rows that follow, a row that isn't
    one."""
    lines = text.splitlines()
    out: list[tuple[str, int, list[tuple[int, str]]]] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        head = HEADER.fullmatch(lines[i].strip())
        if not head:
            return None
        sid, name, count = head.group(1), head.group(2), int(head.group(3))
        who = sid if not name or name.upper() == "UNNAMED" else f"{name} {sid}"
        rows = []
        for k in range(1, count + 1):
            if i + k >= len(lines):
                return None
            cells = [c.strip() for c in lines[i + k].split(",")]
            if len(cells) < 8 or not ROW.match(lines[i + k].strip()):
                return None
            d, t, ident, status, lat, lon, wind, pres = cells[:8]
            cell = [
                f"{_day(d)} {t[:2]}:{t[2:]}",
                STATUS.get(status, status),
                RECORD.get(ident, ident),
                f"{lat} {lon}".strip(),
                "" if wind in ("-99", "") else wind,
                "" if pres in ("-999", "") else pres,
            ]
            while cell and not cell[-1]:
                cell.pop()
            rows.append((i + k + 1, f"{who}; " + "; ".join(cell), d))
        if not rows:
            return None
        first, last = _day(rows[0][2]), _day(rows[-1][2])
        label = (
            "each row: date time UTC; status; record; position; wind kt; pressure mb"
        )
        n = len(rows)
        word = "track row" if n == 1 else "track rows"
        header = f"{who}; {n} {word}, {first} to {last}; {label}"
        out.append((header, i + 1, [(ln, f"[{ln}] {p}") for ln, p, _ in rows]))
        i += count + 1
    if not out:
        return None
    return [(f"[{ln}] {h}", rows) for h, ln, rows in out]


def parts(
    found: list[tuple[str, list[tuple[int, str]]]],
) -> list[list[tuple[str, int]]]:
    """The passages, each with its source line, grouped into mirror files of
    at most PART bytes, cut between storms."""
    out: list[list[tuple[str, int]]] = []
    cur: list[tuple[str, int]] = []
    size = 0
    for head, rows in found:
        group = [(head, int(head[1 : head.index("]")]))] + [(p, ln) for ln, p in rows]
        need = sum(len(p.encode("utf-8")) + 2 for p, _ in group)
        if cur and size + need > PART:
            out.append(cur)
            cur, size = [], 0
        cur += group
        size += need
    if cur:
        out.append(cur)
    return out


def places(part: list[tuple[str, int]]) -> dict[str, str]:
    """The mirror contract's places (adapters/stdlib/ci/README.md): each
    passage's mirror line to its line in the file."""
    return {str(2 * i + 1): f"line {ln}" for i, (_, ln) in enumerate(part)}


def write_places(dst: Path, rel: str, source: str, found: dict[str, str]) -> None:
    out = dst / ".places" / (rel + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {"source": source, "places": found}
    out.write_bytes((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXT) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped); a
    .txt that is not a HURDAT2 file this reads is skipped."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            found = storms(path.read_bytes().decode("utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            found = None
        if not found:
            skipped += 1
            continue
        grouped = parts(found)
        for k, part in enumerate(grouped):
            name = rel.name + (f".part{k}" if len(grouped) > 1 else "") + ".txt"
            target = dst.joinpath(rel.parent, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("\n\n".join(p for p, _ in part) + "\n").encode("utf-8"))
            write_places(
                dst, rel.parent.joinpath(name).as_posix(), rel.as_posix(), places(part)
            )
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
