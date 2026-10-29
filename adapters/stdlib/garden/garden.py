"""garden.py: what you planted, where and when, and how it did, season by
season.

    python adapters/stdlib/garden/garden.py --box DIR

The lines of your garden notes that say something went in, or came out:

    2026
      tomatoes  planted 2026-04-12 (bed 2)  harvested 14 times, 2026-07-20 to 2026-09-30
      beans     planted 2026-05-01 (the fence)  not harvested yet
    2025
      tomatoes  planted 2025-04-20 (bed 1)  harvested 9 times, 2025-07-28 to 2025-09-12
    3 plantings in 2 seasons

**What counts.** A line, on a day, that is about a garden (the line or the path
of its file says garden, allotment, greenhouse, bed, plot, veg, orchard or
soil) and says a planting (planted, plant, sowed, sow, sown, transplanted,
potted) or a harvest (harvested, harvest, picked, pulled, cut). What follows the
verb up to a place word or a comma is the plant, without a leading amount
("2kg", "first", "some", "the"): "harvested 2kg tomatoes from bed 2" is
tomatoes. The place is what follows "in", "into", "at" or "on" for a planting, in the
brackets of its line: "planted beans in the greenhouse" is (the greenhouse). The
day is the line's latest date, else the nearest date written above it in its
file, else the date its file is named for.

**A season** is the year of the planting. Each plant's first planting that year
is shown with its place, then its harvests that year (count, first and last
day), or "not harvested yet". A harvest with no planting that year is shown
under that year as "harvested ... (no planting written)": perennials and last
year's crop are not forgotten. Newest season first.

Nothing is advised or predicted. It only reads. Exit codes, the kernel's: 0
something found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

PLANT = re.compile(
    r"\b(?:plant(?:ed)?|sow(?:ed|n)?|transplanted|potted(?: on)?)\s+(.+)", re.I
)
HARVEST = re.compile(r"\b(?:harvest(?:ed)?|picked|pulled|cut)\s+(.+)", re.I)
CONTEXT = re.compile(
    r"\b(?:gardens?|allotments?|greenhouses?|beds?|plots?|veg|orchards?|soil)\b", re.I
)
STOP = re.compile(
    r"\s+(?:in|at|on|by|from|near|into|along|for|under|and)\s+|[,.;(]", re.I
)
PLACE = re.compile(r"\b(?:in|into|at|on)\s+(.+?)\s*(?:[,.;(]|$)", re.I)
AMOUNT = re.compile(
    r"^(?:(?:\d+(?:\.\d+)?\s*(?:kg|g|lbs?|oz|x|punnets?|plants?|rows? of|seeds? of|bags? of)?|first|some|the|a|an|more|our|my|new)\s+)+",
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


def what(rest: str) -> str:
    """The plant an object phrase names: its words before a place, without an amount."""
    if re.match(
        r"(?:in|into|at|on|by|from|near|along|for|under|and)\s", rest.strip(), re.I
    ):
        return ""
    head = STOP.split(rest, maxsplit=1)[0]
    return " ".join(AMOUNT.sub("", head.strip()).lower().split())


def place_of(rest: str) -> str:
    m = PLACE.search(rest)
    return " ".join(m.group(1).split()) if m else ""


def seasons(pile: list[dict]) -> dict[str, dict[str, dict]]:
    """{year: {plant: {planted: (day, place), harvests: [days]}}}."""
    out: dict = {}
    for day, path, _n, line in entries(pile):
        if not CONTEXT.search(path + " " + line):
            continue
        year = day[:4]
        m = PLANT.search(line)
        if m and (plant := what(m.group(1))):
            rec = out.setdefault(year, {}).setdefault(
                plant, {"planted": None, "harvests": []}
            )
            if rec["planted"] is None or day < rec["planted"][0]:
                rec["planted"] = (day, place_of(m.group(1)))
            continue
        m = HARVEST.search(line)
        if m and (plant := what(m.group(1))):
            out.setdefault(year, {}).setdefault(
                plant, {"planted": None, "harvests": []}
            )["harvests"].append(day)
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(got: dict) -> list[str]:
    out, n = [], 0
    for year in sorted(got, reverse=True):
        out.append(year)
        plants = got[year]
        w = max(len(p) for p in plants)
        for plant in sorted(
            plants,
            key=lambda p: (
                plants[p]["planted"] is None,
                plants[p]["planted"] or ("", ""),
                p,
            ),
        ):
            rec = plants[plant]
            h = sorted(rec["harvests"])
            if rec["planted"]:
                n += 1
                day, place = rec["planted"]
                head = f"planted {dash(day)}" + (f" ({place})" if place else "")
            else:
                head = "(no planting written)"
            if h:
                tail = f"harvested {len(h)} time{'s' if len(h) != 1 else ''}, {dash(h[0])} to {dash(h[-1])}"
            else:
                tail = "not harvested yet"
            out.append(f"  {plant:<{w}}  {head}  {tail}")
    out.append(
        f"{n} planting{'s' if n != 1 else ''} in {len(got)} season{'s' if len(got) != 1 else ''}"
    )
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    got = seasons(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not got:
        print("No line of your folder says something planted or harvested in a garden.")
        return kernel.ESCALATE
    print("\n".join(show(got)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
