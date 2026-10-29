"""mood.py: the mood scores you write in a journal, over weeks and months.

    python adapters/stdlib/mood/mood.py --box DIR [--by week]

The lines of your files that give a mood a score, gathered by month (or by
week) with the average, the lowest and highest day, and the change from the
period before:

    2026-02  avg 6.4  12 days  low 3 on 2026-02-09, high 9 on 2026-02-20
    2026-03  avg 7.1  14 days  low 4 on 2026-03-02, high 9 on 2026-03-28  up 0.7
    2 months, 26 days

**A score** is a line that says "mood" and a number straight after it: "mood:
7", "Mood 7/10", "mood - 4 out of 5". The number is out of 10 unless the line
gives another top (/5, out of 100); it is shown on a scale of 10, and a number
over its top is not read. A day with several scores counts as their average.
A line's day is the latest date it says, else the nearest date written above
it in its file, else the date its file is named for; a line no day reaches is
not counted.

Nothing is diagnosed, flagged or told to anyone: these are the numbers you
wrote, added up, on this machine. `--by week` groups by ISO week. Oldest
first. It only reads. Exit codes, the kernel's: 0 scores found; 42 none; 2
refused.
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

SCORE = re.compile(
    r"\bmood\b[^\d\n]{0,12}?(?<![\d.])(\d+(?:\.\d+)?)(?:\s*(?:/|out of)\s*(\d+(?:\.\d+)?))?(?![\d/])",
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


def score_of(line: str) -> float | None:
    """The mood a line scores, on a scale of 10, or None."""
    m = SCORE.search(line)
    if not m:
        return None
    got, top = float(m.group(1)), float(m.group(2) or 10)
    if top <= 0 or got > top:
        return None
    return got * 10 / top


def days_of(pile: list[dict]) -> dict[str, float]:
    """{YYYYMMDD: the day's average score}."""
    seen: dict[str, list[float]] = {}
    for day, _path, _n, line in entries(pile):
        s = score_of(line)
        if s is not None:
            seen.setdefault(day, []).append(s)
    return {d: sum(v) / len(v) for d, v in seen.items()}


def period(day: str, by: str) -> str:
    if by == "week":
        y, w, _ = date(int(day[:4]), int(day[4:6]), int(day[6:])).isocalendar()
        return f"{y}-W{w:02d}"
    return f"{day[:4]}-{day[4:6]}"


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(days: dict[str, float], by: str) -> list[str]:
    groups: dict[str, list[str]] = {}
    for d in sorted(days):
        groups.setdefault(period(d, by), []).append(d)
    out, prev = [], None
    for key, ds in groups.items():
        avg = sum(days[d] for d in ds) / len(ds)
        low = min(ds, key=lambda d: (days[d], d))
        high = max(ds, key=lambda d: (days[d], -int(d)))
        change = ""
        if prev is not None:
            diff = round(avg, 1) - round(prev, 1)
            change = (
                "  same"
                if abs(diff) < 0.05
                else f"  {'up' if diff > 0 else 'down'} {abs(diff):.1f}"
            )
        out.append(
            f"{key}  avg {avg:.1f}  {len(ds)} day{'s' if len(ds) != 1 else ''}"
            f"  low {days[low]:g} on {dash(low)}, high {days[high]:g} on {dash(high)}{change}"
        )
        prev = avg
    n = len(groups)
    unit = by
    out.append(
        f"{n} {unit}{'s' if n != 1 else ''}, {len(days)} day{'s' if len(days) != 1 else ''}"
    )
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--by"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    by = opts.get("--by", "month")
    if not opts.get("--box") or args or by not in ("month", "week"):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    days = days_of(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not days:
        print("No line of your folder gives a mood a score.")
        return kernel.ESCALATE
    print("\n".join(show(days, by)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
