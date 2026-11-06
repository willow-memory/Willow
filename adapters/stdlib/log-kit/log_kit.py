"""log_kit.py: the engine the logs share. Python 3.9+, stdlib only.

    python adapters/stdlib/log-kit/log_kit.py --box DIR --words WORD[,WORD...] [--by PERIOD]

Every log here reads the same way: the lines of your notes, each with the day
it falls on, the ones holding its words, a value or a kind for each, grouped
by a period. This is that, once, so a log is a short spec, not a program:

    SPEC = {
        "name": "food-log",
        "kinds": {"breakfast": ["breakfast"], "lunch": ["lunch"], "dinner": ["dinner", "supper"]},
        "summary": "lines",
        "by": "day",
        "none": "No line of your folder says what you ate.",
    }
    sys.exit(log_kit.run(SPEC, sys.argv[1:], __doc__))

A line's day is the latest date it says, else the nearest date written above
it in its file, else the date its file is named for; a line no day reaches is
not counted. A spec names what a line must hold (`words`, or a kind's words,
matched whole and case aside), what it is (`kinds`, the first whose word it
holds), what it is worth (`value`, a function of the line, or None), and how
each period is summed up:

- `lines`: each line under its period, its kind and where it is;
- `total`: the values added, in the spec's `unit`, with the lines counted;
- `average`: a day's values averaged, then each period's average, its
  lowest and highest day, and the change from the period before.

Run on its own, it is a log of any words: `--words run,ran,jog` gives every
line holding one, by month unless `--by` says day, week or year. Oldest
first. It only reads. Exit codes, the kernel's: 0 lines found; 42 none; 2
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

PERIODS = ("day", "week", "month", "year")
SPEC = {
    "name": "log-kit",
    "summary": "lines",
    "by": "month",
    "bys": PERIODS,
    "none": "No line of your folder holds those words.",
}


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


def holds(line: str, words: list[str]) -> bool:
    """Whether the line holds one of the words, whole and case aside."""
    return any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", line, re.I) for w in words)


def kind_of(line: str, kinds: dict[str, list[str]]) -> str | None:
    """The first kind whose word the line holds, or None."""
    return next((k for k, ws in kinds.items() if holds(line, ws)), None)


def gather(
    pile: list[dict], spec: dict
) -> list[tuple[str, str, int, str, str, float | None]]:
    """(day, path, line, text, kind, value) for each line the spec counts: it
    holds one of its words or a kind's, and has a value when it asks for one."""
    words, kinds, value = (
        spec.get("words") or [],
        spec.get("kinds") or {},
        spec.get("value"),
    )
    out = []
    for day, path, n, line in entries(pile):
        kind = kind_of(line, kinds) if kinds else None
        if (words or kinds) and not (holds(line, words) or kind):
            continue
        got = value(line) if value else None
        if value and got is None:
            continue
        out.append((day, path, n, line, kind or "", got))
    return out


def period(day: str, by: str) -> str:
    if by == "week":
        y, w, _ = date(int(day[:4]), int(day[4:6]), int(day[6:])).isocalendar()
        return f"{y}-W{w:02d}"
    if by == "day":
        return dash(day)
    if by == "year":
        return day[:4]
    return f"{day[:4]}-{day[4:6]}"


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n != 1 else ''}"


def averages(days: dict[str, float], by: str) -> list[str]:
    """Each period's average of its days', its lowest and highest day, and
    the change from the period before; then how many periods and days."""
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
            change = "  same" if abs(diff) < 0.05 else f"  {'up' if diff > 0 else 'down'} {abs(diff):.1f}"  # fmt: skip
        out.append(
            f"{key}  avg {avg:.1f}  {plural(len(ds), 'day')}"
            f"  low {days[low]:g} on {dash(low)}, high {days[high]:g} on {dash(high)}{change}"
        )
        prev = avg
    out.append(f"{plural(len(groups), by)}, {plural(len(days), 'day')}")
    return out


def totals(found: list, by: str, unit: str) -> list[str]:
    """Each period's values added, in `unit`, and its lines; then the whole."""
    groups: dict[str, list[float]] = {}
    for day, *_, value in sorted(found):
        groups.setdefault(period(day, by), []).append(value)
    out = [
        f"{key}  {sum(vs):g} {unit}  {plural(len(vs), 'line')}"
        for key, vs in groups.items()
    ]
    whole = sum(v for vs in groups.values() for v in vs)
    out.append(f"{plural(len(groups), by)}, {whole:g} {unit} in all")
    return out


def lines(found: list, by: str) -> list[str]:
    """Each period, then its lines: kind, where, the line itself."""
    out, last, width = [], None, max((len(k) for *_, k, _ in found), default=0)
    for day, path, n, text, kind, _ in sorted(found):
        key = period(day, by)
        if key != last:
            out.append(key)
            last = key
        tag = f"{kind:<{width}}  " if width else ""
        out.append(f"  {tag}{path}:{n}  {text}")
    periods = len({period(d, by) for d, *_ in found})
    out.append(f"{plural(periods, by)}, {plural(len(found), 'line')}")
    return out


def summary(found: list, spec: dict, by: str) -> list[str]:
    how = spec.get("summary", "lines")
    if how == "average":
        seen: dict[str, list[float]] = {}
        for day, *_, value in found:
            seen.setdefault(day, []).append(value)
        return averages({d: sum(v) / len(v) for d, v in seen.items()}, by)
    if how == "total":
        return totals(found, by, spec.get("unit", ""))
    return lines(found, by)


def run(spec: dict, argv: list[str], doc: str) -> int:
    """A log's command line: --box DIR [--by PERIOD], and --words for a spec
    that takes them from it (log-kit's own). `doc` is the log's docstring,
    whose second paragraph's first line is its usage."""
    takes = (
        ("--box", "--by", "--words")
        if spec.get("words") == "--words"
        else ("--box", "--by")
    )
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in takes and a not in opts:
            opts[a] = next(it, "")
        else:
            args.append(a)
    by = opts.get("--by", spec.get("by", "month"))
    words = [w.strip() for w in opts.get("--words", "").split(",") if w.strip()]
    if (not opts.get("--box") or args or by not in spec.get("bys", ("month", "week"))
            or ("--words" in takes and not words)):  # fmt: skip
        print(doc.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if "--words" in takes:
        spec = {**spec, "words": words}
    found = gather(kernel.chunks(Path(kernel.config(box)["pile"])), spec)
    if not found:
        print(spec["none"])
        return kernel.ESCALATE
    print("\n".join(summary(found, spec, by)))
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    return run({**SPEC, "words": "--words"}, argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
