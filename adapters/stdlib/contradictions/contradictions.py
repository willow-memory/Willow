"""contradictions.py: two passages that disagree about the same date or amount.

    python adapters/stdlib/contradictions/contradictions.py --box DIR

Every pair of lines in your folder that say the same thing in the same words
but state a different date, or a different amount of the same unit, shown
side by side, each with its file and line. Neither is picked, and nothing is
rewritten: which one is right is yours to say.

    DATE    wedding, dinner
            mail/ana.txt:2  2026-06-19  Reminder: the wedding dinner is on 19/06/2026.
            plans.md:3      2026-06-12  The wedding dinner is on 2026-06-12.

Two lines say the same thing when every word of the shorter one is in the
longer one, and that is at least half the longer one's words: words here
leaving out small words (the kernel's), the date or amount itself, units,
months and weekdays. It takes two such words: one is a label ("Date:"), not
a subject. A date is the kernel's own reading (`newest`), which never
guesses a day from a month; a date that starts a line is when it was
written, not what it says, and a line with two dates, or two different
amounts of one unit, isn't read for them. Two lines written on different
days (a stamp, a date heading above, a file named for the day) are a log's
entries, or a plan changed: they are counted, and left alone.

It only reads. Exit codes, the kernel's: 0 found some; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: an amount's unit as written, read as one unit: "$40" and "40 dollars" are
#: one, so they can disagree; "40 kg" and "40 lb" never are
UNITS = {
    "$": "$", "usd": "$", "dollar": "$", "dollars": "$",
    "€": "€", "eur": "€", "euro": "€", "euros": "€",
    "£": "£", "gbp": "£", "¥": "¥", "jpy": "¥", "yen": "¥",
    "%": "%", "percent": "%",
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg",
    "kilograms": "kg", "g": "g", "gram": "g", "grams": "g",
    "lb": "lb", "lbs": "lb", "oz": "oz",
    "km": "km", "kilometre": "km", "kilometres": "km", "kilometer": "km",
    "kilometers": "km", "cm": "cm", "mm": "mm",
    "mi": "mi", "mile": "mi", "miles": "mi", "ft": "ft", "foot": "ft", "feet": "ft",
    "l": "l", "litre": "l", "litres": "l", "liter": "l", "liters": "l", "ml": "ml",
    "hour": "hour", "hours": "hour", "hr": "hour", "hrs": "hour",
    "min": "minute", "mins": "minute", "minute": "minute", "minutes": "minute",
    "day": "day", "days": "day", "week": "week", "weeks": "week",
    "month": "month", "months": "month", "year": "year", "years": "year",
    "yr": "year", "yrs": "year",
}  # fmt: skip
NUM = r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
#: "$1,200" or "£40.50"; never "$5k" or "$1.2 million", which this can't weigh
BEFORE = re.compile(
    rf"(?P<cur>[$€£¥])\s?{NUM}(?![\d]|[,.]\d)"
    r"(?!\s?(?:k|m|bn|million|billion|thousand)\b)",
    re.I,
)
#: "40 kg", "6 hours", "12%", "1200 USD"; a number run on from another
#: ("5-10 kg", "1/2 cup") is left alone
AFTER = re.compile(rf"(?<![\w.,/$€£¥-]){NUM}\s?(?P<unit>%|[A-Za-z]+\b)")
NAMES = set(
    "january february march april may june july august september october"
    " november december jan feb mar apr jun jul aug sep sept oct nov dec monday"
    " tuesday wednesday thursday friday saturday sunday".split()
)
LEAD = re.compile(r"^\s*(?:[-*+>#]+\s*|\d+[.)]\s+|\[[ xX]\]\s*)*")
MIN_WORDS = 2  # "Date: ..." or "Rent is $900": one word is a label, not a subject


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def stated(text: str) -> tuple[str, str]:
    """(its stamp, the one date it states), by the kernel's reading: a date
    that starts the line is its stamp, when it was written, not what it
    says; two dates is no one date."""
    toks = LEAD.sub("", text).split()
    stamp = kernel.newest(toks[0]) if toks else ""
    got = {d for t in toks[bool(stamp) :] if (d := kernel.newest(t))}
    return stamp, got.pop() if len(got) == 1 else ""


def amounts(text: str) -> dict[str, tuple[Decimal, str]]:
    """Each unit the line states one amount of: unit -> (value, as written)."""
    seen: dict[str, list[tuple[Decimal, str]]] = {}
    for m in BEFORE.finditer(text):
        seen.setdefault(m["cur"], []).append((Decimal(m["num"].replace(",", "")), m[0]))
    for m in AFTER.finditer(text):
        if (u := UNITS.get(m["unit"].lower())) is not None:
            val = Decimal(m["num"].replace(",", ""))
            seen.setdefault(u, []).append((val, m[0]))
    return {
        u: xs[0] for u, xs in seen.items() if len({v.normalize() for v, _ in xs}) == 1
    }


def subject(text: str) -> list[str]:
    """The line's own words, as written, in order: no small words, no
    numbers, units, months or weekdays."""
    out: list[str] = []
    for w in kernel.words(text):
        if w in kernel.FUNCTION or w in UNITS or w in NAMES or len(w) < 2:
            continue
        if any(c.isdigit() for c in w) or w in out:
            continue
        out.append(w)
    return out


def passages(pile: list[dict]) -> list[dict]:
    """Every line stating a date or an amount, with what it's about."""
    out, path, on = [], None, ""
    for c in pile:
        if c["path"] != path:  # a file named for a day was written that day
            path, on = c["path"], kernel.newest(c["path"])
        for i, text in enumerate(c["text"].splitlines()):
            (stamp, said), amt, ws = stated(text), amounts(text), subject(text)
            if stamp and not ws and not said and not amt:
                on = stamp  # a log's date heading covers the lines under it
                continue
            if not said and not amt:
                continue
            out.append({"path": c["path"], "line": c["line"] + i, "text": text.strip(),
                        "date": said, "amounts": amt, "words": ws, "on": stamp or on,
                        "stems": {kernel.stem(w) for w in ws}})  # fmt: skip
    return out


def same(a: dict, b: dict) -> bool:
    """Whether two lines say the same thing: every word of the shorter is in
    the longer, and that is at least half the longer's (the kernel's HOLD)."""
    short, long_ = sorted((a["stems"], b["stems"]), key=len)
    return (
        len(short) >= MIN_WORDS
        and short <= long_
        and len(short) >= kernel.HOLD * len(long_)
    )


def disagreements(found: list[dict]) -> tuple[list[dict], int]:
    """Each pair that says the same thing and states a different date, or a
    different amount of one unit, and how many pairs saying the same thing
    were written on different days, left alone: a log's entries, or a plan
    changed, which this can't tell from a mistake. Neither side is picked."""
    has: dict[str, set[int]] = {}
    for i, a in enumerate(found):
        for w in a["stems"]:
            has.setdefault(w, set()).add(i)
    # the longer of a pair holds every word of the shorter: look only there
    near = set()
    for i, a in enumerate(found):
        if a["stems"]:
            both = set.intersection(*(has[w] for w in a["stems"]))
            near |= {(min(i, j), max(i, j)) for j in both if j != i}
    out, apart = [], 0
    for i, j in sorted(near):
        a, b = found[i], found[j]
        if not same(a, b):
            continue
        if a["on"] and b["on"] and a["on"] != b["on"]:
            apart += 1
            continue
        about = min((a, b), key=lambda x: len(x["stems"]))["words"]
        if a["date"] and b["date"] and a["date"] != b["date"]:
            sides = [(a, day(a["date"])), (b, day(b["date"]))]
            out.append({"kind": "DATE", "about": about, "sides": sides})
        for u in sorted(a["amounts"].keys() & b["amounts"].keys()):
            (va, wa), (vb, wb) = a["amounts"][u], b["amounts"][u]
            if va.normalize() != vb.normalize():
                out.append(
                    {"kind": "AMOUNT", "about": about, "sides": [(a, wa), (b, wb)]}
                )
    return out, apart


def show(x: dict) -> list[str]:
    where = [f"{p['path']}:{p['line']}" for p, _ in x["sides"]]
    w = max(map(len, where))
    v = max(len(val) for _, val in x["sides"])
    rows = [f"{x['kind']:<7} {', '.join(x['about'])}"]
    for (p, val), at in zip(x["sides"], where):
        rows.append(f"{'':<7} {at:<{w}}  {val:<{v}}  {p['text'][:100]}")
    return rows


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = passages(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print("Nothing in your folder states a date or an amount this can read.")
        return kernel.ESCALATE
    pairs, apart = disagreements(found)
    read = f"{len(found)} line{'s' * (len(found) != 1)} with a date or an amount read"
    if apart:
        read += (
            f", {apart} pair{'s' * (apart != 1)} written on different days left alone"
        )
    if not pairs:
        print(f"No two lines saying the same thing disagree; {read}.")
        return kernel.ESCALATE
    for x in pairs:
        print("\n".join(show(x)))
    n = len(pairs)
    print(f"{n} disagreement{'s' * (n != 1)}, {read}; neither side is picked.")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
