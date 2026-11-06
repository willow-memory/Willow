"""food_log.py: what you ate, from your notes, by day.

    python adapters/stdlib/food-log/food_log.py --box DIR [--by day|week|month]

Every line of your files that says a meal or that you ate, under its day,
with the meal it names and where it is:

    2026-03-02
      breakfast  diary/march.md:12  Breakfast: porridge and honey.
      lunch      diary/march.md:13  Lunch was leek soup at Ana's.
    2026-03-03
      dinner     diary/march.md:20  Supper: the rest of the soup.
    2 days, 3 lines

A meal is breakfast, brunch, lunch, dinner (or supper) or a snack, the first
the line names; a line that says only "ate", "eaten" or "eating" is listed
with no meal. A line's day is the latest date it says, else the nearest date
written above it in its file, else the date its file is named for; a line no
day reaches is not listed.

Nothing is counted, scored or judged: these are lines that name a meal, put
in order, on this machine. A school newsletter's "breakfast club" names one
too, so a folder holding mail lists it. It is a spec for log-kit, the engine the logs
share. Oldest first. It only reads. Exit codes, the kernel's: 0 lines found;
42 none; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB / "log-kit"))
import log_kit  # noqa: E402

#: food, as log-kit reads it: the meal a line names, or that it says you ate
SPEC = {
    "name": "food-log",
    "words": ["ate", "eaten", "eating"],
    "kinds": {
        "breakfast": ["breakfast", "breakfasts"],
        "brunch": ["brunch"],
        "lunch": ["lunch", "lunches"],
        "dinner": ["dinner", "dinners", "supper", "suppers"],
        "snack": ["snack", "snacks"],
    },
    "summary": "lines",
    "by": "day",
    "bys": ("day", "week", "month"),
    "none": "No line of your folder says what you ate.",
}


def main(argv: list[str]) -> int:
    return log_kit.run(SPEC, argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
