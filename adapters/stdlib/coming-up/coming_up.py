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

A date that repeats comes up on each repeat in the window, not only its
first: a calendar event with a rule (the calendar reader's `repeats:` line,
or a raw file's `RRULE:`) and a birthday (`birthday:`, or a card's `BDAY:`):

    2026-10-30  Contacts/contacts.vcf.txt:68  birthday: 1957-10-30  (every year)
    2026-11-03  Calendar/Home.ics.txt:44      2022-11-03  Car rego due  (yearly, from this date)

A rule's FREQ (yearly, monthly, weekly, daily), its INTERVAL, UNTIL and COUNT
are kept to. A rule that names days within its period (BYDAY, BYMONTHDAY
and the like) isn't counted out, rather than counted wrong: its first date
still shows as written. A rule belongs to its event's start: a raw file's
DTSTART line, else the first line of its paragraph, as the calendar reader
writes it.

It only reads. Exit codes, the kernel's: 0 something is coming up; 42 nothing
in that window; 2 refused.
"""

from __future__ import annotations

import calendar
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def ymd(d: str) -> date:
    return date(int(d[:4]), int(d[4:6]), int(d[6:8]))


#: a rule, as the calendar reader writes it or as a raw .ics holds it
RULE = re.compile(r"^\s*(?:repeats:\s*|RRULE:)(?P<rule>FREQ=\S+)", re.IGNORECASE)
#: a birthday, as the calendar reader writes it or as a raw .vcf holds it
BIRTHDAY = re.compile(r"^\s*(?:birthday:\s*|BDAY[^:]*:)", re.IGNORECASE)
#: where a rule stops looking up for its date: a blank line, or another event
EDGE = re.compile(r"^\s*(?:$|BEGIN:VEVENT|END:VEVENT)", re.IGNORECASE)
COUNTED = {"FREQ", "INTERVAL", "UNTIL", "COUNT", "WKST"}
STEPS = {"YEARLY": 12, "MONTHLY": 1, "WEEKLY": 7, "DAILY": 1}


def shifted(start: date, freq: str, k: int) -> date | None:
    """The kth repeat of `start`: k years or months on (None when that month
    hasn't the day, as a 31st or a 29 February), or k weeks or days on."""
    if freq in ("WEEKLY", "DAILY"):
        return start + timedelta(days=k * STEPS[freq])
    months = start.month - 1 + k * STEPS[freq]
    y, m = start.year + months // 12, months % 12 + 1
    if start.day > calendar.monthrange(y, m)[1]:
        return None
    return date(y, m, start.day)


def repeats(start: date, rule: str, today: date, end: date) -> list[date]:
    """Each date of the rule from `start` that falls between today and end;
    [] for a rule this doesn't count out (a BY part, a FREQ it doesn't know)."""
    parts = dict(p.split("=", 1) for p in rule.upper().split(";") if "=" in p)
    freq = parts.get("FREQ", "")
    if freq not in STEPS or set(parts) - COUNTED:
        return []
    interval = parts.get("INTERVAL", "1")
    step = int(interval) if interval.isdigit() and int(interval) > 0 else 1
    count = int(parts["COUNT"]) if parts.get("COUNT", "").isdigit() else None
    until = (
        ymd(parts["UNTIL"][:8]) if re.match(r"\d{8}", parts.get("UNTIL", "")) else None
    )
    out, k, made = [], 0, 0
    while True:
        day = shifted(start, freq, k * step)
        k += 1
        if day is None:
            continue  # a month without that day: no repeat, and none counted
        made += 1
        if (count is not None and made > count) or (until and day > until) or day > end:
            return out
        if day >= today:
            out.append(day)


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


def shown(rows: list[tuple[int, str]], k: int) -> str:
    """Row k as it's shown: a line that is little more than its date is
    followed by the next line that says something (a calendar event's
    SUMMARY), up to three lines on and never past a blank line; a rule says
    when, not what, so it is passed over."""
    text = rows[k][1].strip()
    if bare(text):
        for j in range(k + 1, min(k + 4, len(rows))):
            if rows[j][0] != rows[j - 1][0] + 1:
                break  # a blank line between: another paragraph
            after = rows[j][1]
            if not kernel.newest(after) and not bare(after) and not RULE.match(after):
                return f"{text}  {after.strip()}"
    return text


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
            yield day, f"{path}:{n}", shown(rows, k)


def repeating(pile: list[dict], today: date, end: date):
    """(date, place, line) for each repeat of a repeating date in the window:
    a rule's dated line above it, and every birthday."""
    for path, rows in file_lines(pile).items():
        for k, (n, line) in enumerate(rows):
            if BIRTHDAY.match(line) and (d := kernel.newest(line)):
                rule, at, text = "FREQ=YEARLY", n, f"{line.strip()}  (every year)"
            elif m := RULE.match(line):
                rule, at, text = m.group("rule"), None, ""
                above = []  # the event's rows above the rule, nearest first
                for j in range(k - 1, max(k - 13, -1), -1):
                    if EDGE.match(rows[j][1]) or rows[j][0] != rows[j + 1][0] - 1:
                        break
                    above.append(j)
                # its start: a raw file's DTSTART, else the paragraph's first line
                starts = [j for j in above if rows[j][1].upper().startswith("DTSTART")]
                head = starts[0] if starts else (above[-1] if above else None)
                if head is None or not (d := kernel.newest(rows[head][1])):
                    continue
                at, text = rows[head][0], shown(rows, head)
            else:
                continue
            try:
                start = ymd(d)
            except ValueError:
                continue
            for day in repeats(start, rule, today, end):
                if day != start:  # the first is already a dated line
                    yield day, f"{path}:{at}", text


def coming(pile: list[dict], today: date, days: int) -> list[tuple]:
    end = today + timedelta(days=days)
    once = {x for x in dated_lines(pile) if today <= x[0] <= end}
    return sorted(once | set(repeating(pile, today, end)))


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
