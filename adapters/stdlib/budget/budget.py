"""budget.py: spending against the budget you wrote down, month by month, from
your statements. Python 3.9+.

    python adapters/stdlib/budget/budget.py --box DIR

You write a budget in your own words, one line for each category; your
statements' lines are matched to the categories by the words you gave:

    Budget: groceries £400 a month (tesco, aldi, coles)

and the months are held against it:

    groceries  budget 400.00 a month
      2026-02    312.40 of 400.00   78%  under by 87.60
      2026-03    455.10 of 400.00  114%  over by 55.10
    transport  budget 120.00 a month
      2026-03     96.00 of 120.00   80%  under by 24.00
    2 categories, 1 month over budget

**The budget** is a line that says "budget", then the category (one or two
words: groceries, eating out), then an amount, and may say "a month", "per
month", "monthly" or "/month" and the words that mark the category's spending in
brackets. With no brackets, the category's own words are the markers. A later
budget line for the same category replaces an earlier one. Budgets are monthly
only.

**The spending** is any other line that says its own date, with an amount (a
number with cents, or a sum with a currency sign), and one of a category's
markers as a whole word, any case: "2026-03-04,TESCO STORES 3241,-45.20" is
groceries. Its first amount counts, whichever way the sign points. The same day,
words and amount in two files are one payment. A line that matches two categories
counts for the first budget written. A line that matches none is left out, and
the number of them is not guessed at.

Months with spending are shown, oldest first. Nothing is scolded or advised, and
a month is over budget only by arithmetic. It only reads. Exit codes, the
kernel's: 0 a budget found; 42 none; 2 refused.
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

BUDGET = re.compile(
    r"\bbudget\b\s*(?:for\b)?\s*[:\-–]?\s*([A-Za-z]+(?: [A-Za-z]+)?)\s+[£$€]?\s*(\d[\d,]*(?:\.\d{1,2})?)(?P<rest>.*)",
    re.I,
)
MONTHLY = re.compile(
    r"(?:\b(?:a|per|each) month\b|\bmonthly\b|/\s*month\b|/\s*mo\b)", re.I
)
BRACKETS = re.compile(r"\(([^)]*)\)")
AMOUNT = re.compile(
    r"(?<![\d.,])(?:[£$€]\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{2}))?|(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2}))(?![\d.])"
)
DATE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line that says its own date, the
    latest it says: a statement's row has one."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        for n, line in rows:
            day = kernel.newest(line)
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def normal(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def amount_of(line: str) -> float | None:
    """The first sum a line writes, as a number: with a sign, or to the cent."""
    m = AMOUNT.search(DATE.sub(" ", line))
    if not m:
        return None
    whole, cents = (
        (m.group(1), m.group(2)) if m.group(1) is not None else (m.group(3), m.group(4))
    )
    return float(f"{whole.replace(',', '')}.{cents or '00'}")


def budgets(pile: list[dict]) -> dict[str, dict]:
    """{category: {amount, markers}} from the budget lines, a later one replacing an earlier."""
    found: dict[str, tuple[str, dict]] = {}
    for day, _path, _n, line in entries(pile):
        m = BUDGET.search(line)
        if not m:
            continue
        rest = m.group("rest")
        if not (MONTHLY.search(rest) or MONTHLY.search(line)):
            continue
        category = normal(m.group(1))
        inside = BRACKETS.search(rest)
        marks = (
            [normal(w) for w in inside.group(1).split(",")] if inside else [category]
        )
        marks = [w for w in marks if w] or [category]
        if category not in found or day >= found[category][0]:
            found[category] = (
                day,
                {
                    "amount": float(m.group(2).replace(",", "")),
                    "markers": marks,
                    "day": day,
                },
            )
    return {c: v for c, (_d, v) in sorted(found.items(), key=lambda kv: kv[1][0])}


def spending(pile: list[dict], plan: dict[str, dict]) -> dict[str, dict[str, float]]:
    """{category: {YYYYMM: spent}} for lines that match a category's markers."""
    seen: set[tuple[str, str, float]] = set()
    out: dict[str, dict[str, float]] = {}
    for day, _path, _n, line in entries(pile):
        if BUDGET.search(line):
            continue
        value = amount_of(line)
        if value is None:
            continue
        padded = f" {normal(line)} "
        key = (day, normal(line), value)
        if key in seen:
            continue
        for category, p in plan.items():
            if any(f" {w} " in padded for w in p["markers"]):
                seen.add(key)
                months = out.setdefault(category, {})
                months[day[:6]] = months.get(day[:6], 0.0) + value
                break
    return out


def show(plan: dict[str, dict], spent: dict[str, dict[str, float]]) -> list[str]:
    out, over = [], 0
    for category, p in plan.items():
        out.append(f"{category}  budget {p['amount']:.2f} a month")
        for month, total in sorted(spent.get(category, {}).items()):
            pct = round(100 * total / p["amount"]) if p["amount"] else 0
            diff = p["amount"] - total
            verdict = f"under by {diff:.2f}" if diff >= 0 else f"over by {-diff:.2f}"
            over += diff < 0
            out.append(
                f"  {month[:4]}-{month[4:]}  {total:>8.2f} of {p['amount']:.2f}  {pct:>3}%  {verdict}"
            )
    n = len(plan)
    out.append(
        f"{n} categor{'ies' if n != 1 else 'y'}, {over} month{'s' if over != 1 else ''} over budget"
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
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    plan = budgets(pile)
    if not plan:
        print(
            'No line of your folder is a budget: "Budget: groceries £400 a month (tesco, aldi)".'
        )
        return kernel.ESCALATE
    print("\n".join(show(plan, spending(pile, plan))))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
