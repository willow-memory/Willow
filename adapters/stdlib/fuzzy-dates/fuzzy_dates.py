"""fuzzy_dates.py: dates that admit doubt, read with their doubt kept, in EDTF.

    python adapters/stdlib/fuzzy-dates/fuzzy_dates.py --box DIR

A family history says "about 1880", a letter "sometime in March", a label
"the 1990s". The kernel's dates are exact days, so these say nothing to it;
this reads them with the doubt kept, in EDTF (ISO 8601-2, the library
world's format for exactly this), each with the phrase as written and where:

    1880~      about 1880             family/gran.md:4
    188X       the early 1880s        family/gran.md:9
    1944-21    spring 1944            letters/war.md:2
    XXXX-03    sometime in March      notes.md:7
    1880/1885  between 1880 and 1885  family/tree.md:3
    ../1900    before 1900            family/tree.md:8

The grammar is words, small and said in full, and nothing else is guessed:

- about, around, circa, c., roughly or approximately, then a month and
  year or a year: `1880~`, `1972-03~` (approximate);
- maybe, possibly or perhaps, then a year: `1880?` (uncertain);
- a decade, the 1880s, with or without early, mid or late: `188X`;
- spring, summer, autumn, fall or winter, then a year: EDTF's seasons,
  `1944-21` to `1944-24`;
- before or after a year: `../1900`, `1950/..`;
- between one year and another, or from one to another: `1880/1885`;
- sometime in a month: `XXXX-03` for a year unsaid, `1972-03` with one.

A year is four digits, 1000 to 2999, so a price or a page number never
reads as one. Early, mid and late stay in the phrase, not the EDTF: the
decade is what the format can carry. Exact dates are the kernel's job
(`newest`), not this one's, and a plain "March 1972" admits no doubt to
keep.

It only reads. Exit codes, the kernel's: 0 fuzzy dates found; 42 none; 2
refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MONTHS = {m: i + 1 for i, m in enumerate(
    "january february march april may june july august september october "
    "november december".split()
)}  # fmt: skip
for _m, _i in list(MONTHS.items()):
    MONTHS[_m[:3]] = _i
SEASONS = {"spring": 21, "summer": 22, "autumn": 23, "fall": 23, "winter": 24}
YEAR = r"(?P<year>[12]\d{3})(?!\d)"
MONTH = r"(?P<month>" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b"
SHAPES = [
    ("about", re.compile(
        rf"\b(?:about|around|circa|c\.|roughly|approximately)\s+(?:{MONTH}\s+)?{YEAR}",
        re.IGNORECASE)),
    ("maybe", re.compile(rf"\b(?:maybe|possibly|perhaps)\s+{YEAR}", re.IGNORECASE)),
    ("decade", re.compile(
        r"\b(?:(?:early|mid|late)[\s-]+)?(?:the\s+)?(?P<year>[12]\d{2}0)s\b",
        re.IGNORECASE)),
    ("season", re.compile(
        rf"\b(?P<season>spring|summer|autumn|fall|winter)(?:\s+of)?\s+{YEAR}",
        re.IGNORECASE)),
    ("before", re.compile(rf"\bbefore\s+{YEAR}", re.IGNORECASE)),
    ("after", re.compile(rf"\bafter\s+{YEAR}", re.IGNORECASE)),
    ("between", re.compile(
        rf"\b(?:between|from)\s+{YEAR}\s+(?:and|to|until)\s+(?P<year2>[12]\d{{3}})(?!\d)",
        re.IGNORECASE)),
    ("sometime", re.compile(
        rf"\bsometime\s+in\s+{MONTH}(?:\s+{YEAR})?", re.IGNORECASE)),
]  # fmt: skip


def edtf(kind: str, m: re.Match) -> str:
    """The match's EDTF: the doubt kept, and nothing added."""
    got = m.groupdict()
    year = got.get("year") or ""
    if kind == "about":
        month = got.get("month")
        return f"{year}-{MONTHS[month.lower()]:02}~" if month else f"{year}~"
    if kind == "maybe":
        return f"{year}?"
    if kind == "decade":
        return f"{year[:3]}X"
    if kind == "season":
        return f"{year}-{SEASONS[got['season'].lower()]}"
    if kind == "before":
        return f"../{year}"
    if kind == "after":
        return f"{year}/.."
    if kind == "between":
        return f"{year}/{got['year2']}"
    month = f"{MONTHS[got['month'].lower()]:02}"
    return f"{year}-{month}" if year else f"XXXX-{month}"


def found(pile: list[dict]) -> list[tuple[str, str, str, int]]:
    """(EDTF, the phrase as written, path, line) for every fuzzy date, by
    file, line and place in the line; overlapping readings keep the first."""
    out = []
    for c in pile:
        for i, line in enumerate(c["text"].splitlines()):
            hits = []
            for kind, shape in SHAPES:
                for m in shape.finditer(line):
                    hits.append((m.start(), m.end(), edtf(kind, m), m.group()))
            kept, used = [], set()
            for start, end, read, phrase in sorted(hits):
                if not used & set(range(start, end)):
                    kept.append((read, " ".join(phrase.split()), c["path"],
                                 c["line"] + i))  # fmt: skip
                    used |= set(range(start, end))
            out += kept
    return out


def show(rows: list[tuple[str, str, str, int]]) -> list[str]:
    we = max(len(r[0]) for r in rows)
    wp = max(len(r[1]) for r in rows)
    out = [
        f"{read:<{we}}  {phrase:<{wp}}  {path}:{n}" for read, phrase, path, n in rows
    ]
    out.append(f"{len(rows)} fuzzy date{'s' if len(rows) != 1 else ''},"
               " the doubt kept")  # fmt: skip
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
    rows = found(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not rows:
        print("No date of your folder admits doubt in words this reads.")
        return kernel.ESCALATE
    for line in show(rows):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
