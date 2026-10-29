"""warranties.py: receipts and warranties: when the dishwasher's cover ends,
and where its receipt is.

    python adapters/stdlib/warranties/warranties.py --box DIR [--now TS]

The lines of your files that give a thing a warranty or guarantee, with the
day the cover ends and the receipt, soonest to end first:

    Dishwasher  ends 2026-03-02 (in 124 days)  bought 2024-03-02  receipt: kitchen/receipts.md:3
    Kettle      ended 2026-01-10 (279 days ago)  bought 2025-01-10  receipt: not found
    2 warranties

**What counts.** A line that says warranty, guarantee or guaranteed and names
a thing at its start ("Dishwasher, bought 2024-03-02, 2 year warranty"; "Fridge:
warranty until 2027-05-01"; "2025-01-10 Kettle - 1 year guarantee"). The thing
is the words before the first comma, colon, dash, bracket or word like
"bought", "extended" or "warranty".

**When the cover ends** is the date the line says after "until", "till",
"expires", "ends", "valid to" or "through"; else the day bought plus the
length the line says (2 year, 18 months, three years). The day bought is the
date after "bought", "purchased" or "from", else the line's own day, read as the
kernel reads one (its `newest`), else the nearest date written above it in its
file, else the date its file is named for. A line with no way to place the end
is not listed; a day such as 06/12/2024, which reads either way round, is never
guessed, so a certificate that gives only that is not listed either.

**Where its receipt is** is what the line says after "receipt" ("receipt:
red folder"), else a file of yours whose path names a receipt and the thing
(`receipts/dishwasher.pdf.txt`, say); else "not found". Nothing is guessed from
how the words look.

When a thing has several lines the latest one counts. Measured from --now (an
ISO timestamp, the kernel's kind; today if not given). It only reads. Exit
codes, the kernel's: 0 warranties found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "car"))
import car  # noqa: E402
import kernel  # noqa: E402

COVER = re.compile(r"\b(?:warrant(?:y|ies)|guarantee[ds]?)\b", re.I)
ITEM = re.compile(
    r"^\s*[-*•]?\s*(?:[\d./-]+\s+)?([A-Za-z][\w &'’/]{1,40}?)\s*(?=[:,–—(]| - |\s+(?:bought|purchased|extended|warrant|guarantee)|$)",
    re.I,
)
UNTIL = re.compile(
    r"\b(?:until|till|expires?|expiry|ends?|valid to|through)\b[^\d]{0,6}(.*)", re.I
)
BOUGHT = re.compile(r"\b(?:bought|purchased|from)\b(.*)", re.I)
LENGTH = re.compile(
    r"\b(\d+|one|two|three|four|five|ten)[- ]?(year|yr|month|mo)s?\b", re.I
)
RECEIPT = re.compile(r"\breceipts?\b[\s:\-–]*(?:in|at|is|are)?\s*(.+)", re.I)
NUMS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10}


def dated(text: str) -> date | None:
    d = kernel.newest(text)
    return car.to_date(d) if d else None


def end_of(line: str, day: str) -> tuple[date | None, date | None]:
    """(the day bought, the day the cover ends) the line gives; None for what it doesn't."""
    stated = UNTIL.search(line)
    end = dated(re.split(r"[,;()]", stated.group(1))[0]) if stated else None
    head = line[: stated.start()] if stated else line
    b = BOUGHT.search(head)
    bought = dated(re.split(r"[,;()]", b.group(1))[0]) if b else None
    bought = bought or dated(head) or (car.to_date(day) if not end else None)
    if end:
        return bought, end
    m = LENGTH.search(line)
    if not m or not bought:
        return bought, None
    n = int(NUMS.get(m.group(1).lower()) or m.group(1))
    if m.group(2).lower() in ("year", "yr"):
        n *= 12
    return bought, car.add_months(bought, n)


def named(line: str) -> str:
    m = ITEM.match(line)
    return " ".join(m.group(1).split()) if m else ""


def receipt_for(item: str, line: str, where: str, paths: list[str]) -> str:
    said = RECEIPT.search(line)
    if said:
        return said.group(1).strip(" .;") or where
    words = [w for w in re.findall(r"[a-z]{4,}", item.lower())]
    for p in sorted(paths):
        low = p.lower()
        if "receipt" in low and any(w in low for w in words):
            return p
    return "not found"


def warranties(pile: list[dict]) -> dict:
    """{item: (ends, bought, receipt, where)} the latest line for each thing."""
    paths = sorted({c["path"] for c in pile})
    best: dict = {}
    for day, path, n, line in car.entries(pile):
        if not COVER.search(line):
            continue
        item = named(line)
        bought, end = end_of(line, day)
        if not item or end is None:
            continue
        key = item.lower()
        if key not in best or day >= best[key][0]:
            best[key] = (
                day,
                item,
                end,
                bought,
                receipt_for(item, line, f"{path}:{n}", paths),
                f"{path}:{n}",
            )
    return {v[1]: v[2:] for v in best.values()}


def show(found: dict, today: date) -> list[str]:
    rows = sorted(found.items(), key=lambda kv: (kv[1][0], kv[0]))
    w = max(len(k) for k in found)
    out = []
    for item, (end, bought, receipt, _where) in rows:
        d = (end - today).days
        if d >= 0:
            span = "in %d day%s" % (d, "s" if d != 1 else "") if d else "today"
            ends = f"ends {end} ({span})"
        else:
            ends = f"ended {end} ({-d} day{'s' if d != -1 else ''} ago)"
        out.append(
            f"{item:<{w}}  {ends}"
            + (f"  bought {bought}" if bought else "")
            + f"  receipt: {receipt}"
        )
    n = len(rows)
    out.append(f"{n} warrant{'ies' if n != 1 else 'y'}")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    ts = opts.get("--now") or kernel.now()
    if not opts.get("--box") or args or not re.match(r"\d{4}-\d{2}-\d{2}", ts):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
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
    found = warranties(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print("No line of your folder gives a thing a warranty with a day it ends.")
        return kernel.ESCALATE
    print("\n".join(show(found, today)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
