"""attendance.py: attendance for a class, club or group, from your register,
by person or by week.

    python adapters/stdlib/attendance/attendance.py --box DIR [--by week]

The lines of your register that say who was there:

    Ben   7 of 10  70%  (3 absent, 1 late)  last absent 2026-03-12
    Ana   9 of 10  90%  (1 absent, 2 late)  last absent 2026-03-04
    2 people, 20 marks

**A mark** is a line, on a day, in one of two shapes: a status and a list of
names ("Absent: Ben, Cy"; "Present: Ana and Dee"; "Late - Eve"), or a name and
a status ("Ana present"; "Ben: absent"; "Cy - late"). Names start with a
capital (one or two words). Statuses: present (present, attended), late,
and absent (absent, away, sick, missed, excused); beside a name only present,
attended, late, absent, sick and excused are read, so "Click away" is no mark.
Late counts as there. A
person marked twice on a day has the later mark. A line's day is the latest
date it says, else the nearest date written above it in its file, else the
date its file is named for; a line no day reaches is not counted.

Each person shows the days they were there out of the days they were marked,
the percentage, how many were absent or late, and the last day absent. Lowest
attendance first. With --by week each ISO week shows the marks made, oldest
first:

    2026-W10  present 14, late 1, absent 2  (17 marks)

Nothing is graded or reported to anyone. It only reads. Exit codes, the
kernel's: 0 marks found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

STATUS = {
    "present": "present", "attended": "present",
    "late": "late",
    "absent": "absent", "away": "absent", "sick": "absent", "missed": "absent", "excused": "absent",
}  # fmt: skip
WORD = "|".join(STATUS)
SAID = "present|attended|late|absent|sick|excused"  # beside a name: "Click away" is no mark
NAME = r"[A-Z][\w'’-]*(?: [A-Z][\w'’-]*)?"
LEAD = r"^\s*[-*•]?\s*(?:[\d./-]+\s+)?"
LISTED = re.compile(rf"{LEAD}((?i:{WORD}))\s*[:\-–]\s*(.+?)\s*$")
NAMED = re.compile(rf"{LEAD}({NAME})\s*[:\-–]?\s*((?i:{SAID}))\b")
SPLIT = re.compile(r"\s*(?:,|;|&|\band\b)\s*")


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


def marks_of(line: str) -> list[tuple[str, str]]:
    """[(name, status)] a line gives."""
    m = LISTED.match(line)
    if m:
        status = STATUS[m.group(1).lower()]
        names = [
            re.sub(r"\s*\(.*?\)", "", n).strip(" .") for n in SPLIT.split(m.group(2))
        ]
        return [(n, status) for n in names if re.fullmatch(NAME, n)]
    m = NAMED.match(line)
    if m and m.group(1).lower() not in STATUS:
        return [(m.group(1), STATUS[m.group(2).lower()])]
    return []


def register(pile: list[dict]) -> dict[tuple[str, str], str]:
    """{(name, day): status}, a later mark on the same day replacing an earlier."""
    out: dict[tuple[str, str], str] = {}
    for day, _path, _n, line in entries(pile):
        for name, status in marks_of(line):
            out[(name, day)] = status
    return out


def marks(n: int) -> str:
    return f"{n} mark{'s' if n != 1 else ''}"


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def by_person(reg: dict) -> list[str]:
    people: dict[str, dict[str, str]] = {}
    for (name, day), status in reg.items():
        people.setdefault(name, {})[day] = status
    rows = []
    for name, days in people.items():
        total = len(days)
        there = sum(s != "absent" for s in days.values())
        absent = sorted(d for d, s in days.items() if s == "absent")
        late = sum(s == "late" for s in days.values())
        rows.append((there / total, name, total, there, len(absent), late, absent))
    rows.sort(key=lambda r: (r[0], r[1]))
    w = max(len(r[1]) for r in rows)
    out = []
    for frac, name, total, there, nab, late, absent in rows:
        bits = [f"{nab} absent"] + ([f"{late} late"] if late else [])
        out.append(
            f"{name:<{w}}  {there} of {total}  {round(frac * 100)}%  ({', '.join(bits)})"
            + (f"  last absent {dash(absent[-1])}" if absent else "")
        )
    out.append(
        f"{len(rows)} {'person' if len(rows) == 1 else 'people'}, {marks(len(reg))}"
    )
    return out


def by_week(reg: dict) -> list[str]:
    weeks: dict[str, dict[str, int]] = {}
    for (_name, day), status in reg.items():
        y, w, _ = date(int(day[:4]), int(day[4:6]), int(day[6:])).isocalendar()
        got = weeks.setdefault(f"{y}-W{w:02d}", {"present": 0, "late": 0, "absent": 0})
        got[status] += 1
    out = []
    for key in sorted(weeks):
        g = weeks[key]
        out.append(
            f"{key}  present {g['present']}, late {g['late']}, absent {g['absent']}"
            f"  ({marks(sum(g.values()))})"
        )
    out.append(f"{len(weeks)} week{'s' if len(weeks) != 1 else ''}, {marks(len(reg))}")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--by"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    by = opts.get("--by", "person")
    if not opts.get("--box") or args or by not in ("person", "week"):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    reg = register(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not reg:
        print("No line of your folder marks anyone present or absent.")
        return kernel.ESCALATE
    print("\n".join(by_week(reg) if by == "week" else by_person(reg)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
