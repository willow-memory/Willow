"""coming_up.py: dates written in your files that fall in the next few days.

    python adapters/stdlib/coming-up/coming_up.py --box DIR [--days N] [--now TS]

Every line of your folder that holds a date between today and N days from
now (14 by default), soonest first: appointments, renewals, deadlines, the
`next:` in a log, a calendar's events.

    2026-10-28  calendar.ics:812       DTSTART;VALUE=DATE:20261028  SUMMARY:Tune: Ybarra
    2026-10-31  work/insurance.txt:4   Your cover ends on 31/10/2026 unless renewed.

A line that is little more than its date (a calendar's start line) is shown
with the next line of its passage that says something. A date is read the way the kernel reads one for "newest first" (its `newest`):
2026-10-28, 20261028, and 28/10/2026 or 10.28.2026 only when it can't be read
the other way round; 11/03/2026 is never guessed. A line with several dates
counts by its latest.

It only reads. Exit codes, the kernel's: 0 something is coming up; 42 nothing
in that window; 2 refused.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def ymd(d: str) -> date:
    return date(int(d[:4]), int(d[4:6]), int(d[6:8]))


def bare(line: str) -> bool:
    """A line that is little more than its date: what follows its last colon
    (a field's value, as in a calendar's DTSTART;VALUE=DATE:20261028) has
    fewer than two words that aren't numbers."""
    value = line.rsplit(":", 1)[-1]
    return len([w for w in kernel.words(value) if not w.isdigit()]) < 2


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def dated_lines(pile: list[dict]):
    """(date, place, line) for every line of the pile that holds a date. A
    line that is little more than its date is followed by the next line that
    says something (a calendar event's SUMMARY), up to three lines on and
    never past a blank line."""
    for path, rows in file_lines(pile).items():
        for k, (n, line) in enumerate(rows):
            d = kernel.newest(line)
            if not d:
                continue
            try:
                day = ymd(d)
            except ValueError:  # 2026-02-31 reads as a date's shape, not a day
                continue
            text = line.strip()
            if bare(text):
                for j in range(k + 1, min(k + 4, len(rows))):
                    if rows[j][0] != rows[j - 1][0] + 1:
                        break  # a blank line between: another paragraph
                    after = rows[j][1]
                    if not kernel.newest(after) and not bare(after):
                        text = f"{text}  {after.strip()}"
                        break
            yield day, f"{path}:{n}", text


def coming(pile: list[dict], today: date, days: int) -> list[tuple]:
    end = today + timedelta(days=days)
    return sorted({x for x in dated_lines(pile) if today <= x[0] <= end})


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days", "14")
    if not opts.get("--box") or args or not days.isdigit():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    today = ymd((opts.get("--now") or kernel.now())[:10].replace("-", ""))
    hits = coming(kernel.chunks(Path(kernel.config(box)["pile"])), today, int(days))
    if not hits:
        print(f"Nothing dated between {today} and {today + timedelta(days=int(days))}.")
        return kernel.ESCALATE
    width = max(len(p) for _, p, _ in hits)
    for d, place, line in hits:
        print(f"{d}  {place:<{width}}  {line[:120]}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
