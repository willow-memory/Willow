"""contradictions.py: two passages that disagree about the same date or amount.

    python adapters/stdlib/contradictions/contradictions.py --box DIR

Every pair of lines in your folder that say the same thing in the same words
but state a different date, or a different amount of the same unit, shown
side by side, each with its file and line. Neither is picked, and nothing is
rewritten: which one is right is yours to say.

    DATE    wedding, dinner
            mail/ana.txt:2  2026-06-19  Reminder: the wedding dinner is on 19/06/2026.
            plans.md:3      2026-06-12  The wedding dinner is on 2026-06-12.

Two lines say the same thing when they share at least half the shorter
one's words, and at least two: words here leaving out small words (the
kernel's), the date or amount itself, units, months and weekdays, and any
word that's everywhere (on more than one dated line in 500, and more than
10), which is about nothing in particular. One shared
word is a label ("Date:"), not a subject. Records of one kind are left alone
and counted: files named alike but numbered differently (two invoices, two
tax years), a subject said in the same words on three lines or more (a
form's field, a table's rows), and two items one after the other in a list
(the nearside tyre and the offside). A date is the kernel's own reading (`newest`), which never
guesses a day from a month; a date that starts a line is when it was
written, not what it says, and a line with two dates, or two different
amounts of one unit, isn't read for them. Two lines written on different
days (a stamp, a date heading above, a file named for the day) are a log's
entries, or a plan changed: they are counted, and left alone.

Only prose is read: a line of code or data is a value, not a claim, so a
file by its name a program's or a data file's (.py, .json, .csv and
the like), a fenced code block in Markdown, and a table's row (a line split
by two or more `|` or tabs) are left out, and counted.

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
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")  # a list's item: "- ", "* ", "2. "
LEAD = re.compile(r"^\s*(?:[-*+>#]+\s*|\d+[.)]\s+|\[[ xX]\]\s*)*")
#: a file of code or data, by its name: its lines are values, not claims
CODE = set(
    ".py .pyi .js .mjs .cjs .ts .tsx .jsx .go .rs .java .kt .kts .scala .c .h .cc"
    " .cpp .hpp .cs .rb .php .pl .swift .m .lua .r .jl .sh .bash .zsh .fish .ps1"
    " .bat .cmd .sql .json .jsonl .ndjson .yaml .yml .toml .ini .cfg .conf .lock"
    " .csv .tsv .xml .svg .drawio .css .scss .gradle .mk .cmake .tf .proto .ipynb".split()
)
FENCE = re.compile(r"^\s*(```|~~~)")
MIN_WORDS = 2  # "Date: ..." or "Rent is $900": one word is a label, not a subject
DIGITS = re.compile(r"\d+")
#: a subject said in the same words on this many lines is a form's field
#: ("Total due:" on every invoice) or a table's rows, not a claim made twice
FIELD = 3
#: a word on more than one dated line in COMMON, and on more than FLOOR lines,
#: is no subject: in a folder of repositories "willow" or "kernel" is on
#: thousands, and two lines sharing it are about nothing in particular. Left
#: in, every such pair was a candidate (9.5 million over 14 repositories,
#: 371,125 "disagreements", over two minutes); a small folder keeps every word
COMMON, FLOOR = 500, 10


def kin(a: str, b: str) -> bool:
    """Two files named alike but numbered differently, INV-2026-012.txt and
    INV-2026-015.txt, or one tax year's summary and the next: records of one
    kind, each with its own date and amount, not two accounts of one thing."""
    return a != b and DIGITS.sub("#", a) == DIGITS.sub("#", b)


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


def tabled(text: str) -> bool:
    """A table's row: split by two or more pipes or tabs, not a sentence."""
    return text.count("|") >= 2 or text.count("\t") >= 2


def passages(pile: list[dict]) -> tuple[list[dict], int]:
    """Every line of prose stating a date or an amount, with what it's
    about; and how many such lines were left out as code, data or a table's
    row."""
    out, path, on, fenced, code, skipped = [], None, "", False, False, 0
    for c in pile:
        if c["path"] != path:  # a file named for a day was written that day
            path, on = c["path"], kernel.newest(c["path"])
            fenced, code = False, Path(path).suffix.lower() in CODE
        for i, text in enumerate(c["text"].splitlines()):
            if FENCE.match(text):
                fenced = not fenced
                continue
            if code or fenced:
                if stated(text)[1] or amounts(text):
                    skipped += 1
                continue
            (stamp, said), amt, ws = stated(text), amounts(text), subject(text)
            if stamp and not ws and not said and not amt:
                on = stamp  # a log's date heading covers the lines under it
                continue
            if not said and not amt:
                continue
            if tabled(text):
                skipped += 1
                continue
            out.append({"path": c["path"], "line": c["line"] + i, "text": text.strip(),
                        "item": bool(ITEM.match(text)),
                        "date": said, "amounts": amt, "words": ws, "on": stamp or on,
                        "stems": {kernel.stem(w) for w in ws}})  # fmt: skip
    return out, skipped


def same(a: dict, b: dict) -> bool:
    """Whether two lines say the same thing: they share at least half the
    shorter one's words (the kernel's HOLD), and at least two of them."""
    short, long_ = sorted((a["stems"], b["stems"]), key=len)
    both = len(short & long_)
    return both >= MIN_WORDS and both >= kernel.HOLD * len(short)


def everywhere(found: list[dict]) -> set[str]:
    """The words on more than one line in COMMON, and on more than FLOOR
    lines: no subject, since two lines holding one are about nothing in
    particular."""
    seen: dict[str, int] = {}
    for a in found:
        for w in a["stems"]:
            seen[w] = seen.get(w, 0) + 1
    return {w for w, n in seen.items() if n > max(len(found) / COMMON, FLOOR)}


def disagreements(found: list[dict]) -> tuple[list[dict], int, int]:
    """Each pair that says the same thing and states a different date, or a
    different amount of one unit, and how many pairs saying the same thing
    were written on different days, left alone: a log's entries, or a plan
    changed, which this can't tell from a mistake; and how many were records
    of one kind, left alone the same way: in files named alike (`kin`), a
    subject said in the same words on `FIELD` lines or more, or two items one
    after the other in a list (the nearside tyre and the offside). Neither
    side is picked."""
    common = everywhere(found)
    found = [{**a, "stems": a["stems"] - common} for a in found]
    has: dict[str, set[int]] = {}
    for i, a in enumerate(found):
        for w in a["stems"]:
            has.setdefault(w, set()).add(i)
    # a pair says the same thing only if it shares a word: look only there
    near = {
        (i, j) for i, a in enumerate(found) for w in a["stems"] for j in has[w] if j > i
    }
    said: dict[frozenset, int] = {}
    for a in found:
        said[frozenset(a["stems"])] = said.get(frozenset(a["stems"]), 0) + 1
    out, apart, kinds = [], 0, 0
    for i, j in sorted(near):
        a, b = found[i], found[j]
        if not same(a, b):
            continue
        if a["on"] and b["on"] and a["on"] != b["on"]:
            apart += 1
            continue
        listed = (
            a["path"] == b["path"]
            and abs(a["line"] - b["line"]) == 1
            and a["item"]
            and b["item"]
        )
        if (
            listed
            or kin(a["path"], b["path"])
            or FIELD <= max(said[frozenset(a["stems"])], said[frozenset(b["stems"])])
        ):
            kinds += 1
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
    return out, apart, kinds


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
    found, skipped = passages(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print("Nothing in your folder states a date or an amount this can read.")
        return kernel.ESCALATE
    pairs, apart, kinds = disagreements(found)
    read = f"{len(found)} line{'s' * (len(found) != 1)} with a date or an amount read"
    if skipped:
        read += f", {skipped} of code, data or a table left out"
    if kinds:
        read += f", {kinds} pair{'s' * (kinds != 1)} in records of one kind left alone"
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
