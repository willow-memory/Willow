"""milestones.py: your child's firsts, words and heights, from your notes, by
age. Python 3.9+.

    python adapters/stdlib/milestones/milestones.py --box DIR --born YYYY-MM-DD [--name NAME]

The lines of your notes about a child's firsts and measurements, each with the
child's age on that day:

    0y 2m 3d   2026-03-02  first smile  (notes/baby.md:4)
    0y 6m 1d   2026-07-14  sat up on her own  (notes/baby.md:19)
    1y 0m 5d   2027-01-09  first steps  (notes/baby.md:40)
    1y 0m 5d   2027-01-09  height 74 cm, weight 9.6 kg  (notes/baby.md:41)
    4 milestones

**What counts.** A line, on a day on or after --born, that is about a child
(the line or the path of its file says baby, bub, toddler, child, kid, son,
daughter, milestone, newborn or infant, or names --name) and says a first
("first word", "first steps", "first tooth", "first smile", "first day", "first
haircut", and the like) or a milestone (rolled over, sat up, crawled, pulled up,
walked, waved, clapped, babbled, slept through) or a measurement (height,
length or weight, with a number and a unit: 74 cm, 9.6 kg, 20 lb 4 oz). A
line's day is the latest date it says, else the nearest date written above it
in its file, else the date its file is named for.

**Age** is whole years, whole months and days since --born, counted on the
calendar: born on the 31st, a month later is the last day of the next month.
Oldest first. Nothing is compared to anyone else's child, no chart, no norm:
this is your own record of when things happened. It only reads. Exit codes,
the kernel's: 0 milestones found; 42 none; 2 refused (a bad command line, --born
not a date).
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

ABOUT = re.compile(
    r"\b(?:baby|bubs?|toddler|child|kids?|son|daughter|milestones?|newborn|infant)\b",
    re.I,
)
FIRST = re.compile(
    r"\bfirst (?:words?|steps?|tooth|teeth|smile|laugh|crawl|walk|day|haircut|bath|solids?|food|birthday|swim|christmas|word)\b",
    re.I,
)
DID = re.compile(
    r"\b(?:rolled over|sat up|sits up|crawled|crawling|pulled (?:herself|himself|themselves) up|walked|walking|waved|clapped|babbled|slept through)\b",
    re.I,
)
MEASURE = re.compile(
    r"\b(?:height|length|weight)\b[^.;\n]{0,20}?\d+(?:\.\d+)?\s*(?:cm|mm|m|kg|g|lbs?|oz|in|inches|ft)\b",
    re.I,
)


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


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    first = date(y, m + 1, 1)
    nxt = date(y + (m + 1) // 12, (m + 1) % 12 + 1, 1)
    return first + timedelta(days=min(d.day, (nxt - first).days) - 1)


def age(born: date, day: date) -> tuple[int, int, int]:
    """(years, months, days) from born to day, on the calendar."""
    months = (day.year - born.year) * 12 + day.month - born.month
    if add_months(born, months) > day:
        months -= 1
    return months // 12, months % 12, (day - add_months(born, months)).days


def milestones(pile: list[dict], born: date, name: str = "") -> list[dict]:
    out = []
    about = re.compile(r"\b" + re.escape(name) + r"\b") if name else None
    for day, path, n, line in entries(pile):
        d = date(int(day[:4]), int(day[4:6]), int(day[6:]))
        if d < born or not (
            FIRST.search(line) or DID.search(line) or MEASURE.search(line)
        ):
            continue
        if ABOUT.search(path + " " + line) or (about and about.search(line)):
            out.append(
                {"day": d, "where": f"{path}:{n}", "line": " ".join(line.split())}
            )
    return sorted(out, key=lambda m: (m["day"], m["where"]))


def parse_date(text: str) -> date | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date(int(text[:4]), int(text[5:7]), int(text[8:]))
    except ValueError:
        return None


def show(found: list[dict], born: date) -> list[str]:
    out = []
    for m in found:
        y, mo, d = age(born, m["day"])
        text = m["line"] if len(m["line"]) <= 90 else m["line"][:89] + "…"
        out.append(f"{f'{y}y {mo}m {d}d':<10} {m['day']}  {text}  ({m['where']})")
    n = len(found)
    out.append(f"{n} milestone{'s' if n != 1 else ''}")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--born", "--name"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    born = parse_date(opts.get("--born", ""))
    if not opts.get("--box") or args or born is None or opts.get("--name") == "":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = milestones(
        kernel.chunks(Path(kernel.config(box)["pile"])), born, opts.get("--name", "")
    )
    if not found:
        print(
            "No line of your folder is about a child's first or a measurement on or after the birth."
        )
        return kernel.ESCALATE
    print("\n".join(show(found, born)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
