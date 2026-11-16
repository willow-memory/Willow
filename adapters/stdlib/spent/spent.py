"""spent.py: how much you spent on one thing in a year, the money-out lines that say it added up, each cited so you can check it. Python 3.9+.

    python adapters/stdlib/spent/spent.py --box DIR [--now TS] [--year calendar|financial[:MM]] "how much did we spend on electricity this year"

No one passage says what a year of electricity came to: it is a sum over
the lines of your statements. This finds the lines that spent money on what
you named, adds them up, and lists every line it added, with its file and
line number, so each can be checked.

    spent: electricity (energy, origin)
    period: calendar 2026, 2026-01-01 to 2026-10-24 (so far)
    2026-01-25  446.06  Bank/FY25-26.csv:94  25/01/2026,"-446.06","BPAY ORIGIN ENERGY 6631094"
    2026-04-25  479.80  Bank/FY25-26.csv:61  25/04/2026,"-479.80","BPAY ORIGIN ENERGY 6631094"
    total: 925.86 in 2 payments

**The words** are the question's words, less the stock words the kernel
never counts, the words that only say it is a sum (spend, spent, pay, paid,
total, cost, money), and the words that say the period (this year, last
year, financial, fiscal, fy, calendar). A line is counted only when it holds
all of them, the way the kernel holds a word (its `holds`, so a plural
counts), and through the box's words list (`held_by`: "electricity = energy,
origin" lets a line that says ORIGIN ENERGY hold it). Not half of them, as
the kernel serves a passage: a total with one line that never said the thing
is a wrong total. A line is judged on its own words, never its file's name.

**Which lines.** A line that says its own date (the kernel's `newest`; never
borrowed from above; a date that reads both ways is never guessed) and writes
an amount to the cent (45.20, -45.20, $9.00, £1,240.50). It is money out when
the amount is written with a minus before it (as a statement writes it), or
sits in a money-out column of a statement whose header names one (Debit,
Paid out, Money out, Withdrawals). A plus is money in and never added. An
amount written with no sign is not added either: some banks write money in
unsigned, and an email's "45.20" is only a price, so it is listed apart as
"unsigned" for you to judge. So are a line holding the words and a minus
with no date it can read, and a line dated after --now (not spent yet). The
total is only what is written as money out.

**The period.** With "this year" or "last year" in the question (or --year
given, which says what a year is: `calendar`, the default, or `financial`,
which starts on 1 July, or `financial:MM` for another start month, `financial:4`
for April; the UK's tax year starts on the 6th and is not that) the lines
counted are that year's. "financial year", "fiscal year" and "fy" in the
question say financial. With neither, every date counts. The period is always
printed. A year not yet over is counted to --now.

**The same payment** on the same day, for the same amount and currency, in
two files (a statement and its copy, a bank's CSV and the same rows pasted
into a note) is one payment when the two lines say the same words, or share
a word besides the ones asked for: counted once, the other file named
beside it. Two equal lines in one file are two payments, and two places that
share only what you asked for ("cafe") are two.

Amounts keep their currency: £, $ and € are each totalled on their own, and
an amount with no sign is a currency of its own (said so when there is more
than one); they are never added together. It only reads. Exit codes, the kernel's: 0 some money out was
found; 42 none; 2 refused.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import date, timedelta
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
MINUS = "-\u2212"  # a hyphen-minus and the minus sign
AMOUNT = re.compile(
    r"(?<![\d.])([+\-−]?)([£$€]?)\s?([+\-−]?)"
    r"(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2})(?![\d.])"
)
DATE = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")
STOCK = {"card", "purchase", "payment", "debit", "visa", "direct", "eftpos", "pos", "ref", "transaction", "the", "and", "for", "pty", "ltd", "co", "com", "www"}  # fmt: skip
#: words that say it is a sum or a period, not what it was spent on
SAYS_SUM = {"spend", "spends", "spent", "spending", "pay", "pays", "paid", "paying", "total", "cost", "costs", "money", "altogether", "so", "far"}  # fmt: skip
SAYS_PERIOD = {"this", "last", "year", "financial", "fiscal", "fy", "calendar"}
#: money out and money in columns of a statement's header, as bank reads them
OUT_IN = (("debit", "credit"), ("paid out", "paid in"), ("money out", "money in"), ("withdrawals", "deposits"))  # fmt: skip
START = 7  # a financial year starts on 1 July unless --year says otherwise


def to_date(day: str) -> date:
    return date(int(day[:4]), int(day[4:6]), int(day[6:]))


def amount_of(text: str) -> tuple[str, str, int] | None:
    """(which way, currency sign, cents) of the first amount a text writes to
    the cent. Which way is "out" (a minus), "in" (a plus) or "" (no sign at
    all). A minus glued to a word or number ("INV-100.00") is a hyphen."""
    m = AMOUNT.search(text)
    if not m:
        return None
    s1, cur, s2, whole, cents = m.groups()
    sign = s2 or s1
    if s1 and not s2 and text[: m.start(1)][-1:].isalnum():
        sign = ""
    way = "out" if sign and sign in MINUS else "in" if sign else ""
    return way, cur, int(whole.replace(",", "")) * 100 + int(cents)


def header_of(first: str) -> tuple[int, int] | None:
    """(the money-out column, the money-in column) when a file's first line
    is a statement's header naming a pair of them."""
    try:
        cells = [c.strip().lower() for c in next(csv.reader([first]))]
    except (csv.Error, StopIteration):
        return None
    for out, got in OUT_IN:
        if out in cells and got in cells:
            return cells.index(out), cells.index(got)
    return None


def row_amount(line: str, cols: tuple[int, int] | None) -> tuple[str, str, int] | None:
    """(way, currency, cents) for one line: the money-out column's cell when
    the statement has such columns and the row fits them, else the first
    amount the line writes."""
    if cols:
        try:
            cells = next(csv.reader([line]))
        except (csv.Error, StopIteration):
            cells = []
        if len(cells) > max(cols):
            out, got = amount_of(cells[cols[0]]), amount_of(cells[cols[1]])
            if out:  # a plus in the money-out column says nothing it can trust
                return ("out", out[1], out[2]) if out[0] != "in" else None
            return ("in", got[1], got[2]) if got else None
    return amount_of(line)


def what(line: str) -> set[str]:
    """The words a line says it was for, less its dates, amounts and stock words."""
    text = AMOUNT.sub(" ", DATE.sub(" ", line.lower()))
    return {w for w in re.findall(r"[a-z]+", text) if w not in STOCK and len(w) > 2}


def wanted(question: str) -> tuple[list[str], str, bool]:
    """(the words a line must hold, "this" or "last" or "", whether the
    question says a financial year) for a question."""
    ws = kernel.words(question)
    which, financial = "", any(w in ("financial", "fiscal", "fy") for w in ws)
    for i, w in enumerate(ws):
        if w in ("this", "last") and not which:
            rest = ws[i + 1 : i + 3]
            if (
                rest[:1] == ["fy"]
                or (
                    rest[:1] in (["financial"], ["fiscal"], ["calendar"])
                    and rest[1:2] == ["year"]
                )
                or rest[:1] == ["year"]
            ):
                which = w
    keep = []
    for w in ws:
        if w not in kernel.FUNCTION and w not in SAYS_SUM | SAYS_PERIOD and w not in keep:  # fmt: skip
            keep.append(w)
    return keep, which, financial


def period(
    now: date, which: str, financial: bool, start: int
) -> tuple[str, date, date]:
    """(its name, its first day, its last day) of this or last year."""
    if not financial or start == 1:
        y = now.year - (which == "last")
        return f"calendar {y}", date(y, 1, 1), date(y, 12, 31)
    y = (now.year if now.month >= start else now.year - 1) - (which == "last")
    first, after = date(y, start, 1), date(y + 1, start, 1)
    name = f"financial year {y}-{(y + 1) % 100:02d}, starting {first.day} {first:%B}"
    return name, first, after - timedelta(days=1)


def holding(line: str, want: list[str], alias: dict) -> bool:
    toks = kernel.forms(kernel.words(line))
    return all(kernel.held_by(w, toks, alias) for w in want)


def money(cents: int, cur: str) -> str:
    return f"{cur}{cents // 100:,}.{cents % 100:02d}"


def gather(pile: list[dict], want: list[str], alias: dict) -> list[dict]:
    """Every line that holds the words and writes an amount, in file and line
    order: {day, path, n, text, way, cur, cents}."""
    out = []
    for path, rows in sorted(habits.file_lines(pile).items()):
        cols = header_of(rows[0][1]) if rows else None
        for n, line in rows:
            text = line.strip()
            got = row_amount(text, cols) if text else None
            if got and holding(text, want, alias):
                out.append({"day": kernel.newest(text), "path": path, "n": n, "text": text, "way": got[0], "cur": got[1], "cents": got[2]})  # fmt: skip
    return out


def once(rows: list[dict], want: list[str]) -> list[dict]:
    """The payments, each once: a line is another file's copy of a payment
    when it has the same day, amount and currency, and says the same thing
    (the same words, or a word besides the ones asked for in common), and
    the payment isn't already from its file."""
    pays: list[dict] = []
    for r in sorted(rows, key=lambda r: (r["day"], r["path"], r["n"])):
        r["words"] = what(r["text"])
        for p in pays:
            if (p["day"], p["cents"], p["cur"]) == (r["day"], r["cents"], r["cur"]) and r["path"] not in p["files"] and (p["words"] == r["words"] or (p["words"] & r["words"]) - set(want)):  # fmt: skip
                p["files"].add(r["path"])
                p["also"].append(f"{r['path']}:{r['n']}")
                break
        else:
            pays.append({**r, "files": {r["path"]}, "also": []})
    return pays


def report(
    pile: list[dict], question: str, now: date, year: str, alias: dict
) -> tuple[list[str], int]:
    want, which, financial = wanted(question)
    if not want:
        return ["name what it was spent on: no word of the question says it"], kernel.REFUSED  # fmt: skip
    kind, _, mm = year.partition(":")
    financial = financial or kind == "financial"
    start = int(mm) if mm else START
    if which or year:
        name, first, last = period(now, which or "this", financial, start)
        scope = f"{name}, {first} to {min(last, now)}" + (" (so far)" if last > now else "")  # fmt: skip
    else:
        first, last, scope = date.min, date.max, f"every date, up to {now}"
    said = ", ".join(want)
    alias_said = "; ".join(f"{w} = {', '.join(alias[w])}" for w in want if w in alias)
    out = [f"spent: {said}" + (f" ({alias_said})" if alias_said else ""), f"period: {scope}"]  # fmt: skip
    rows = gather(pile, want, alias)
    pays, left = [], {"unsigned": [], "undated": [], "later": []}
    for r in rows:
        if r["way"] == "in":
            continue
        if not r["day"]:
            if r["way"] == "out":
                left["undated"].append(r)
            continue
        d = to_date(r["day"])
        if r["way"] == "":
            if first <= d <= now and d <= last:
                left["unsigned"].append(r)
        elif d > now and first <= d <= last:
            left["later"].append(r)
        elif first <= d <= min(last, now):
            pays.append(r)
    pays = once(pays, want)
    for p in pays:
        also = f"  (also {', '.join(p['also'])})" if p["also"] else ""
        out.append(f"{p['day'][:4]}-{p['day'][4:6]}-{p['day'][6:]}  {money(p['cents'], p['cur'])}  {p['path']}:{p['n']}  {p['text']}{also}")  # fmt: skip
    totals: dict[str, list[int]] = {}
    for p in pays:
        totals.setdefault(p["cur"], []).append(p["cents"])
    many = len(totals) > 1
    for cur in sorted(totals):
        n = len(totals[cur])
        label = " (no currency sign)" if many and not cur else ""
        out.append(f"total: {money(sum(totals[cur]), cur)} in {n} payment{'s' if n != 1 else ''}{label}")  # fmt: skip
    if many:
        out.append("currencies are never added together")
    if not pays:
        out.append(f"No money-out line in this period holds all of: {said}.")
    for key, why in (
        ("unsigned", "it is written with no sign (money in, or only a price)"),
        ("undated", "it is money out with no date it can read"),
        ("later", f"it is dated after {now}, not spent yet"),
    ):
        for r in left[key]:
            out.append(f"  not added, {why}: {r['path']}:{r['n']}  {r['text']}")
    return out, kernel.ALIVE if pays else kernel.ESCALATE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--year"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    year = opts.get("--year", "")
    kind, _, mm = year.partition(":")
    if (
        not opts.get("--box")
        or len(args) != 1
        or (year and kind not in ("calendar", "financial"))
        or (mm and (kind != "financial" or not mm.isdigit() or not 1 <= int(mm) <= 12))
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    day = kernel.newest(opts.get("--now") or kernel.now())
    if not day:
        print("refused: --now has no date it can read", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg, alias = kernel.config(box), {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    lines, code = report(kernel.chunks(Path(cfg["pile"])), args[0], to_date(day), year, alias)  # fmt: skip
    print("\n".join(lines), file=sys.stderr if code == kernel.REFUSED else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
