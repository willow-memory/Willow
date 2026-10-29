"""home_upkeep.py: home upkeep: the boiler service, the filters, the gutters,
what's due and when it was last done.

    python adapters/stdlib/home-upkeep/home_upkeep.py --box DIR [--now TS]

The lines of your files that say a job done to the house, one row for each
kind of job:

    smoke alarm  last 2026-05-01  2 times   -           due 2026-11-01 (in 3 days)
    boiler       last 2025-11-20  3 times   £240.00     due 2026-11-20 (in 22 days)
    gutters      last 2025-04-12  1 time    £90.00      no due date written
    3 kinds of job, 6 entries

**What counts.** A line that says a kind of job and a day, and is about a
home: the line or the path of its file says house, home, flat, boiler,
furnace, gutter, chimney, smoke, roof, drain, septic, pest, hvac or heating
(so a car's oil filter is not the house's). The kinds are boiler (boiler,
furnace, hvac), gutters, chimney (chimney, flue, sweep), smoke alarm
(smoke alarm, smoke detector, carbon monoxide), roof, drains (drain, septic),
pest (pest, termite, rodent) and, last, filters (filter); a line is the first
kind it names. "Heating on or off" in a chat is not a job, so heating is only
a sign that a line is about the house.

Cost, the day a line is about, and what's due are read as the
[car](../car/) add-on reads them: the amount with a £, $ or € sign, totalled
for each sign; the latest date before any "due"; and a due date only from a
date after "due" or an interval the line writes ("every 12 months", "yearly",
"six-monthly"). A kind with neither says "no due date written"; none is
guessed. Soonest due first, measured from --now (an ISO timestamp, the
kernel's kind; today if not given).

It only reads. Exit codes, the kernel's: 0 jobs found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "car"))
import car  # noqa: E402

HOME = {
    "boiler": r"boilers?|furnace|hvac",
    "gutters": r"gutters?",
    "chimney": r"chimneys?|flue|sweep(?:ing)?",
    "smoke alarm": r"smoke alarms?|smoke detectors?|carbon monoxide",
    "roof": r"roof(?:ing)?",
    "drains": r"drains?|septic",
    "pest": r"pests?|termites?|rodents?",
    "filters": r"filters?",
}
CONTEXT = re.compile(
    r"\b(?:house|home|flat|boiler|furnace|gutters?|chimney|smoke|roof|drains?|septic|pests?|hvac|heating)\b",
    re.I,
)


def main(argv: list[str]) -> int:
    return car.cli(
        argv,
        __doc__.split("\n\n")[1].splitlines()[0],
        HOME,
        context=CONTEXT,
        none="No line of your folder says a job done to the house.",
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
