"""habits.py: streaks from the lines you write each day, and what you missed.

    python adapters/stdlib/habits/habits.py --box DIR

The short lines your files write day after day — walked the dog, no sugar,
practised — gathered into habits, each with its days, its runs and its
misses:

     212 days  longest run 44  ends on 12  walked the dog  (2026-01-02 to 2026-10-22; missed 38, last 2026-10-10)
      31 days  longest run 31  ends on 31  no sugar  (2026-09-22 to 2026-10-22; missed none)
    2 habits, written on 4 days or more

**What makes a habit.** The same short line on four or more distinct days. A
line is read as its words, in order, case and punctuation aside, with any
word holding a digit dropped, so "2026-03-01 Ran 5k" and "ran" tick the same
habit; one to six such words, since a sentence of more than six is prose,
not a tick. A line you wrote has a lowercase letter in it: one that shouts
throughout (a statement's WOOLWORTHS), one whose first word carries a
field's mark (a calendar's DTSTART;TZID=..., a note's tags:), and one that
opens as markup never tick. A line's day is the latest date it says, read as
the kernel reads one, else the nearest date written above it in its file,
else the date its file is named for; a line no day reaches ticks nothing.

**Runs and misses are plain counting.** A run is consecutive calendar days.
"Ends on" is the run the habit's last day closes, however long ago that was:
no clock is consulted, so the same folder gives the same bytes, and whether
a streak is alive today is yours to say, looking at its last day. The missed
days are the gaps between a habit's first day and its last, with the most
recent named; days before you started and after you stopped aren't misses.

Habits come most days first. It only reads. Exit codes, the kernel's: 0
habits found; 42 none on four days or more; 2 refused.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

DAYS = 4  # distinct days a line needs before it's a habit
CEILING = 6  # words; a longer line is prose, not a tick


def key_of(line: str) -> str:
    """The line as a habit ticks it: its words in order, any holding a digit
    dropped, one to six of them, else "". A line you wrote has a lowercase
    letter in it; one that shouts throughout (a calendar's DTSTART, a
    statement's WOOLWORTHS) is a machine's, and one opening as a field
    ("tags: daily") is a file's furniture; neither ticks."""
    bare = line.strip()
    first = bare.split(" ", 1)[0] if bare else ""
    if not any(c.islower() for c in bare) or any(c in ":;=<" for c in first):
        return ""
    ws = [w for w in kernel.words(line) if not any(c.isdigit() for c in w)]
    return " ".join(ws) if 1 <= len(ws) <= CEILING else ""


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def ticks(pile: list[dict]) -> dict[str, set[str]]:
    """{habit key: the days it was written}, for keys on DAYS days or more.
    A line's day is the latest it says, else the nearest above in its file,
    else its file's name; a line no day reaches ticks nothing."""
    out: dict[str, set[str]] = {}
    for path, rows in file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for _, line in rows:
            said = kernel.newest(line)
            day = said or above or filed
            key = key_of(line)
            if key and day:
                out.setdefault(key, set()).add(day)
            if said:
                above = said
    return {k: days for k, days in out.items() if len(days) >= DAYS}


def runs_of(days: set[str]) -> list[int]:
    """The lengths of the runs of consecutive calendar days, in day order."""
    out, last = [], None
    for d in sorted(date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in days):
        if last is not None and d - last == timedelta(days=1):
            out[-1] += 1
        else:
            out.append(1)
        last = d
    return out


def missed(days: set[str]) -> tuple[int, str]:
    """(how many days of the habit's span are gaps, the most recent one)."""
    got = sorted(date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in days)
    count = (got[-1] - got[0]).days + 1 - len(got)
    if not count:
        return 0, ""
    last = next(
        got[i + 1] - timedelta(days=1)
        for i in range(len(got) - 2, -1, -1)
        if (got[i + 1] - got[i]).days > 1
    )
    return count, last.isoformat()


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(found: dict[str, set[str]]) -> list[str]:
    rows = sorted(found.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    out = []
    for key, days in rows:
        runs = runs_of(days)
        count, last = missed(days)
        gaps = f"missed {count}, last {last}" if count else "missed none"
        out.append(
            f"{len(days):>4} days  longest run {max(runs)}  ends on {runs[-1]}"
            f"  {key}  ({day(min(days))} to {day(max(days))}; {gaps})"
        )
    out.append(f"{len(rows)} habit{'s' if len(rows) != 1 else ''},"
               f" written on {DAYS} days or more")  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = ticks(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print(f"No line of your folder is written on {DAYS} days or more.")
        return kernel.ESCALATE
    for line in show(found):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
