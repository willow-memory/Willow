"""mileage.py: miles driven for work, from your trips and notes, by tax year.

    python adapters/stdlib/mileage/mileage.py --box DIR [--year-start MM-DD]

The lines of your files that say a drive and how far, totalled for each tax
year, work and other apart:

    tax year 2026-04-06 to 2027-04-05
         412 miles  for work  (9 trips)
          58 miles  other  (2 trips)
    tax year 2025-04-06 to 2026-04-05
         138 km  for work  (3 trips)
    14 trips in 2 tax years

**What counts.** A line that says a drive (drove, driven, drive, trip,
mileage, journey, travelled) and a distance: 12 miles, 8.5 mi, 130 km, 1,240
miles. The distances on one line add; a line counts once. A line about the
odometer is a reading, not a trip, and is left out. A line is "for work" when
it also says work, business, client, site, job, delivery or deliveries;
otherwise it is "other". Miles and kilometres are never added together: each
is totalled on its own.

**The tax year** starts on --year-start (MM-DD, 01-01 unless told: the
calendar year). For a year that starts on 6 April, pass 04-06. A line's day
is the latest date it says, read as the kernel reads one (its `newest`),
else the nearest date written above it in its file, else the date its file is
named for; a line no day reaches is not counted.

Newest year first. Nothing is claimed or filed for you: these are the
totals your own notes add up to. It only reads. Exit codes, the kernel's: 0
trips found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

DRIVE = re.compile(
    r"\b(?:drove|driven|drive|driving|trip|mileage|journey|travell?ed)\b", re.I
)
WORK = re.compile(r"\b(?:work|business|clients?|site|job|deliver(?:y|ies))\b", re.I)
ODO = re.compile(r"\b(?:odometer|odo)\b", re.I)
DIST = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(miles?|mi|kilomet(?:re|er)s?|km)\b", re.I)


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says, else the nearest above it in its file, else its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def distances(line: str) -> dict[str, float]:
    """{unit: how far} the line says, miles and km kept apart."""
    out: dict[str, float] = {}
    for num, unit in DIST.findall(line):
        u = "miles" if unit.lower().startswith("mi") else "km"
        out[u] = out.get(u, 0.0) + float(num.replace(",", ""))
    return out


def start_of(day: str, mmdd: tuple[int, int]) -> date:
    """The first day of the tax year a YYYYMMDD day falls in."""
    d = date(int(day[:4]), int(day[4:6]), int(day[6:]))
    year = d.year if (d.month, d.day) >= mmdd else d.year - 1
    return date(year, *mmdd)


def tally(pile: list[dict], mmdd: tuple[int, int] = (1, 1)) -> dict:
    """{year start: {(unit, 'work'|'other'): [how far, trips]}}."""
    out: dict = {}
    for day, _path, _n, line in entries(pile):
        if not DRIVE.search(line) or ODO.search(line):
            continue
        kind = "work" if WORK.search(line) else "other"
        for unit, far in distances(line).items():
            got = out.setdefault(start_of(day, mmdd), {}).setdefault(
                (unit, kind), [0.0, 0]
            )
            got[0] += far
            got[1] += 1
    return out


def show(found: dict, mmdd: tuple[int, int]) -> list[str]:
    out, trips = [], 0
    for start in sorted(found, reverse=True):
        end = date(start.year + 1, *mmdd) - timedelta(days=1)
        out.append(f"tax year {start} to {end}")
        for (unit, kind), (far, n) in sorted(
            found[start].items(),
            key=lambda kv: (kv[0][0] != "miles", kv[0][1] != "work"),
        ):
            label = "for work" if kind == "work" else "other"
            out.append(
                f"{round(far, 2):>12g} {unit}  {label}  ({n} trip{'s' if n != 1 else ''})"
            )
            trips += n
    out.append(
        f"{trips} trip{'s' if trips != 1 else ''} in {len(found)} tax year{'s' if len(found) != 1 else ''}"
    )
    return out


def month_day(text: str) -> tuple[int, int] | None:
    if not re.fullmatch(r"\d{2}-\d{2}", text):
        return None
    try:
        d = datetime.strptime("2001-" + text, "%Y-%m-%d")
    except ValueError:
        return None
    return d.month, d.day


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--year-start"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    mmdd = month_day(opts.get("--year-start", "01-01"))
    if not opts.get("--box") or args or mmdd is None:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = tally(kernel.chunks(Path(kernel.config(box)["pile"])), mmdd)
    if not found:
        print("No line of your folder says a drive and how far.")
        return kernel.ESCALATE
    print("\n".join(show(found, mmdd)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
