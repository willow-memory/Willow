"""subscriptions.py: what you pay for every month, found in your statements
and emails, and when each renews. Python 3.9+.

    python adapters/stdlib/subscriptions/subscriptions.py --box DIR

A payment that comes round on a calendar is a subscription whether or not
anyone called it one. This finds the lines of your files that pay the same
thing again and again, on a rhythm:

    Netflix com     15.99  monthly  last 2026-03-05  next about 2026-04-05  (5 payments)
    Gym             29.00  monthly  last 2026-03-01  next about 2026-04-01  (8 payments, was 25.00)
    Dropbox        119.88  yearly   last 2025-11-02  next about 2026-11-02  (2 payments)
    3 subscriptions: about 52.95 a month, 172.80 a year

**What counts.** A line that says its own date (a statement's row does; a
sentence under an email's header does not, and a date is not borrowed from
above), with an amount written to the cent
(15.99, -15.99, £1,240.50, $9.00), and some words saying what it was for. The
words are the line's letters without its dates, its numbers, and the stock words
of a statement (card, purchase, payment, debit, visa, direct, eftpos, pos, ref,
transaction), the first three kept: "NETFLIX.COM  -15.99  card purchase" is
"netflix com". The same words on the same day in two files are one payment.

**A rhythm** is every gap between a thing's payment days being about a month
(26 to 35 days) for three payments or more, or about a year (355 to 375 days) for
two or more. Anything else, however often it is paid, is not called a
subscription: a coffee bought on Fridays and then not for a month is a habit,
not a plan. The amount is the latest paid; an earlier different amount is said
("was 25.00"). "Next about" is the last day plus a month or a year; it is a
guess at when to look, not a promise from anyone.

Dearest first by what it costs in a year. Nothing is cancelled, and nothing
is claimed to be a subscription that your files do not show paid on a rhythm.
A line does not say which way money went, so a deposit that comes round (a
wage, a refund) is found as well as a payment. Amounts are shown without their currency sign, as they stand in the line; two
currencies are not added. It only reads. Exit codes, the kernel's: 0
subscriptions found; 42 none; 2 refused.
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

AMOUNT = re.compile(
    r"(?<![\d.,])([£$€]?)\s?-?(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2})(?![\d.])"
)
DATE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")
STOCK = {"card", "purchase", "payment", "debit", "visa", "direct", "eftpos", "pos", "ref", "transaction", "the", "and", "for", "pty", "ltd", "co", "com", "www"}  # fmt: skip
MONTH = (26, 35)  # days between two monthly payments
YEAR = (355, 375)
MONTHLY_MIN, YEARLY_MIN = 3, 2


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line that says its own date, the
    latest it says: a statement's row has one; a sentence under a dated email
    header does not, and is not a payment."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        for n, line in rows:
            day = kernel.newest(line)
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def what(line: str) -> str:
    """The words a line says it was for: its letters, less dates and numbers
    and a statement's stock words, the first three."""
    text = AMOUNT.sub(" ", DATE.sub(" ", line))
    words = [
        w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOCK and len(w) > 1
    ]
    return " ".join(words[:3])


def paid(line: str) -> str:
    """The first amount a line writes to the cent, as 15.99; "" when none."""
    m = AMOUNT.search(line)
    return f"{int(m.group(2).replace(',', ''))}.{m.group(3)}" if m else ""


def to_date(day: str) -> date:
    return date(int(day[:4]), int(day[4:6]), int(day[6:]))


def payments(pile: list[dict]) -> dict[str, dict[str, str]]:
    """{words: {day: amount}} for every dated line that pays something."""
    out: dict[str, dict[str, str]] = {}
    for day, _path, _n, line in entries(pile):
        key, amount = what(line), paid(line)
        if key and amount:
            out.setdefault(key, {})[day] = amount
    return out


def rhythm(days: list[str]) -> str:
    """'monthly', 'yearly' or '' for a thing's payment days."""
    ds = [to_date(d) for d in sorted(days)]
    gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
    if len(ds) >= MONTHLY_MIN and all(MONTH[0] <= g <= MONTH[1] for g in gaps):
        return "monthly"
    if len(ds) >= YEARLY_MIN and all(YEAR[0] <= g <= YEAR[1] for g in gaps):
        return "yearly"
    return ""


def found(pile: list[dict]) -> list[dict]:
    out = []
    for key, by_day in payments(pile).items():
        kind = rhythm(list(by_day))
        if not kind:
            continue
        days = sorted(by_day)
        last = to_date(days[-1])
        now = by_day[days[-1]]
        before = next((by_day[d] for d in reversed(days[:-1]) if by_day[d] != now), "")
        nxt = last + timedelta(days=30 if kind == "monthly" else 365)
        out.append({
            "what": key, "amount": now, "kind": kind, "last": last, "next": nxt,
            "count": len(days), "was": before,
            "year": float(now) * (12 if kind == "monthly" else 1),
        })  # fmt: skip
    return sorted(out, key=lambda s: (-s["year"], s["what"]))


def show(subs: list[dict]) -> list[str]:
    w = max(len(s["what"]) for s in subs)
    out = []
    for s in subs:
        extra = f", was {s['was']}" if s["was"] else ""
        out.append(
            f"{s['what']:<{w}}  {s['amount']:>8}  {s['kind']:<7}  last {s['last']}  next about {s['next']}"
            f"  ({s['count']} payments{extra})"
        )
    month = sum(float(s["amount"]) for s in subs if s["kind"] == "monthly")
    year = sum(s["year"] for s in subs)
    n = len(subs)
    out.append(
        f"{n} subscription{'s' if n != 1 else ''}: about {month:.2f} a month, {year:.2f} a year"
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
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    subs = found(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not subs:
        print("No payment in your folder comes round on a monthly or yearly rhythm.")
        return kernel.ESCALATE
    print("\n".join(show(subs)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
