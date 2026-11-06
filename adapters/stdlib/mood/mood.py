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
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB / "log-kit"))
import log_kit  # noqa: E402

SCORE = re.compile(
    r"\bmood\b[^\d\n]{0,12}?(?<![\d.])(\d+(?:\.\d+)?)(?:\s*(?:/|out of)\s*(\d+(?:\.\d+)?))?(?![\d/])",
    re.I,
)


def score_of(line: str) -> float | None:
    """The mood a line scores, on a scale of 10, or None."""
    m = SCORE.search(line)
    if not m:
        return None
    got, top = float(m.group(1)), float(m.group(2) or 10)
    if top <= 0 or got > top:
        return None
    return got * 10 / top


#: mood, as log-kit reads it: a line's score, a day's average, by month or week
SPEC = {
    "name": "mood",
    "value": score_of,
    "summary": "average",
    "by": "month",
    "bys": ("month", "week"),
    "none": "No line of your folder gives a mood a score.",
}
period = log_kit.period


def days_of(pile: list[dict]) -> dict[str, float]:
    """{YYYYMMDD: the day's average score}."""
    seen: dict[str, list[float]] = {}
    for day, *_, value in log_kit.gather(pile, SPEC):
        seen.setdefault(day, []).append(value)
    return {d: sum(v) / len(v) for d, v in seen.items()}


def main(argv: list[str]) -> int:
    return log_kit.run(SPEC, argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
