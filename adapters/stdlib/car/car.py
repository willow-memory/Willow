"""car.py: your car's services, repairs and inspection dates, from receipts and
notes: what's due, and what it cost.

    python adapters/stdlib/car/car.py --box DIR [--now TS]

The lines of your files that say a job done to the car, one row for each kind
of job:

    mot        last 2025-11-10  2 times  £108.00   due 2026-11-10 (in 12 days)
    service    last 2026-01-15  3 times  £420.50   due 2027-01-15 (in 78 days)
    tyres      last 2024-06-02  1 time   £310.00   no due date written
    3 kinds of job, 6 entries

**What counts.** A line that says a kind of job and a day, and is about a
vehicle: the line or the path of its file says car, vehicle, van, ute, truck,
motor, garage, auto, engine, odometer, MOT, rego, tyre or brake. (A tuning
log's "service visit" is not the car's; a service history kept in a folder called van is.) The kinds are
mot (MOT, inspection, roadworthy, rego, registration, safety check), tyres,
brakes, battery, repair (repair, repaired, fixed, replaced) and, last,
service (service, serviced, oil change, oil + filter). A line is the first
kind it names, so "oil + filter, battery" is the battery's. A
line's day is the latest date it says before any "due", else the nearest date
written above it in its file, else the date its file is named for; a line no
day reaches is not counted.

**What it cost** is the amount with a currency sign on the line (£ $ €); each
sign is totalled on its own and never converted.

**What's due** is only what you wrote: a date after "due" ("next service due
2027-01-15"), else the last day plus an interval the line says ("every 12
months", "every 2 years", "every 6 weeks", "annual", "yearly", "six-monthly").
An interval written once holds for the later jobs of that kind until a later
line writes another.
A kind with neither says "no due date written"; none is guessed from how
often you did it. Due dates are measured from --now (an ISO timestamp, the
kernel's kind; today if not given): soonest first, then the rest.

It only reads. Exit codes, the kernel's: 0 jobs found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

CAR = {
    "mot": r"mot|inspection|roadworthy|rego|registration|safety check",
    "tyres": r"tyres?|tires?",
    "brakes": r"brakes?",
    "battery": r"batter(?:y|ies)",
    "repair": r"repair(?:ed|s)?|fixed|replaced",
    "service": r"service[ds]?|oil change|oil \+ filter|oil and filter",
}
CAR_CONTEXT = re.compile(
    r"\b(?:cars?|vehicles?|vans?|ute|trucks?|motors?|garage|auto|engine|odometer|mot|rego|tyres?|tires?|brakes?)\b",
    re.I,
)
DUE = re.compile(r"\bdue\b.*", re.I)
MONEY = re.compile(r"([£$€])\s*(\d[\d,]*(?:\.\d{1,2})?)")
EVERY = re.compile(
    r"\bevery\s+(?:(\d+|a|one|two|three|four|six|twelve)\s*[- ]?)?(week|month|year)s?\b",
    re.I,
)
WORDS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "six": 6, "twelve": 12}
NAMED = (
    (re.compile(r"\b(?:annual(?:ly)?|yearly)\b", re.I), (12, "month")),
    (re.compile(r"\bsix[- ]?monthly\b", re.I), (6, "month")),
    (re.compile(r"(?<![-\w])monthly\b", re.I), (1, "month")),
    (re.compile(r"\bweekly\b", re.I), (1, "week")),
)


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says before any "due", else the nearest above it in its file, else
    its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(DUE.sub("", line))
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def to_date(day: str) -> date:
    return date(int(day[:4]), int(day[4:6]), int(day[6:]))


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    first = date(y, m + 1, 1)
    nxt = date(y + (m + 1) // 12, (m + 1) % 12 + 1, 1)
    return first + timedelta(days=min(d.day, (nxt - first).days) - 1)


def interval_of(line: str) -> tuple[int, str] | None:
    """(how many, 'month' or 'week') the line says the job comes round, or None."""
    found = [(m.start(), (WORDS.get((m.group(1) or "a").lower()) or int(m.group(1)), m.group(2).lower()))
             for m in EVERY.finditer(line)]  # fmt: skip
    for rx, (n, unit) in NAMED:
        found += [(m.start(), (n, unit)) for m in rx.finditer(line)]
        line = rx.sub(
            lambda m: " " * len(m.group()), line
        )  # six-monthly is not monthly
    if not found:
        return None
    n, unit = max(found)[1]
    if unit == "year":
        n, unit = n * 12, "month"
    return (n, unit) if n > 0 else None


def explicit_due(line: str) -> str:
    m = DUE.search(line)
    return kernel.newest(m.group(0)) if m else ""


def register(pile: list[dict], kinds: dict[str, str], who=None, context=None) -> dict:
    """{(who, kind): {days, cost, interval, due, last line}} from the pile. With a
    context, a line counts only when it or its file's path matches it: a
    "service" in a tuning log is not the car's."""
    rxs = {k: re.compile(r"\b(?:" + v + r")\b", re.I) for k, v in kinds.items()}
    out: dict = {}
    for day, path, n, line in entries(pile):
        kind = next((k for k, rx in rxs.items() if rx.search(line)), None)
        if kind is None or (context and not context.search(path + " " + line)):
            continue
        rec = out.setdefault(
            (who(line) if who else "", kind),
            {"days": [], "cost": {}, "interval": None, "due": "", "at": ""},
        )
        rec["days"].append(day)
        for sign, amt in MONEY.findall(line):
            rec["cost"][sign] = rec["cost"].get(sign, 0.0) + float(amt.replace(",", ""))
        if day >= max(rec["days"]):
            iv, due = interval_of(line), explicit_due(line)
            rec["interval"] = iv or rec["interval"]
            rec["due"] = due or rec["due"]
            rec["at"] = f"{path}:{n}"
    return out


def due_date(rec: dict) -> date | None:
    """The date the job is due: what a line said, else last + the interval."""
    if rec["due"]:
        return to_date(rec["due"])
    if rec["interval"]:
        n, unit = rec["interval"]
        last = to_date(max(rec["days"]))
        return add_months(last, n) if unit == "month" else last + timedelta(weeks=n)
    return None


def when(due: date, today: date) -> str:
    d = (due - today).days
    if d == 0:
        return "due today"
    plural = "s" if abs(d) != 1 else ""
    return f"in {d} day{plural}" if d > 0 else f"overdue {-d} day{plural}"


def money(cost: dict) -> str:
    return " + ".join(f"{s}{v:,.2f}" for s, v in sorted(cost.items())) or "-"


def show(found: dict, today: date, plural_kind: str = "kinds of job") -> list[str]:
    rows = []
    for (who, kind), rec in found.items():
        due = due_date(rec)
        rows.append((due is None, due or date.max, who, kind, rec, due))
    rows.sort(key=lambda r: r[:4])
    wk = max(len(r[3]) for r in rows)
    ww = max(len(r[2]) for r in rows)
    out = []
    for _, _, who, kind, rec, due in rows:
        n = len(rec["days"])
        tail = f"due {due} ({when(due, today)})" if due else "no due date written"
        head = f"{who:<{ww}}  " if ww else ""
        out.append(
            f"{head}{kind:<{wk}}  last {max(rec['days'])[:4]}-{max(rec['days'])[4:6]}-{max(rec['days'])[6:]}"
            f"  {str(n) + (' time' if n == 1 else ' times'):<8}  {money(rec['cost']):<10}  {tail}"
        )
    entries_n = sum(len(r[4]["days"]) for r in rows)
    out.append(
        f"{len(rows)} {plural_kind}, {entries_n} {'entry' if entries_n == 1 else 'entries'}"
    )
    return out


def cli(
    argv: list[str],
    usage: str,
    kinds: dict[str, str],
    who=None,
    context=None,
    label: str = "kinds of job",
    none: str = "No line of your folder says a job done to the car.",
) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(usage, file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    if not re.match(r"\d{4}-\d{2}-\d{2}", ts):
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = register(
        kernel.chunks(Path(kernel.config(box)["pile"])), kinds, who, context
    )
    if not found:
        print(none)
        return kernel.ESCALATE
    print("\n".join(show(found, today, label)))
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    return cli(argv, __doc__.split("\n\n")[1].splitlines()[0], CAR, context=CAR_CONTEXT)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
