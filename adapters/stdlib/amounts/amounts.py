"""amounts.py: every sum of money in your files, with its date and its line.

    python adapters/stdlib/amounts/amounts.py --box DIR

Every line of your folder that writes a sum with its currency, oldest first:

    2026-03-14  £54.85    car/mot.txt:3        MOT test £54.85
    2026-05-02  €725      letters/may.md:1     my half €725 (paid May 2024)
    undated     $20       notes.md:9           Found $20 in a coat pocket.

A sum is a number written with its currency: a symbol before it ($20,
£1,840.00, € 45, US$9.50), a code before it (EUR 100), or a code or
"lei" after it (45.50 USD, 200 lei). The number may group thousands with
commas and give pence after a dot. A number written any other way is not
read at all, rather than guessed: 100,00 and 1.995 name no sum here, and a
bare number is never money.

A line's date is the latest it says, read as the kernel reads one (its
`newest`: 11/03/2026, either way round, is never guessed). A line that says
none takes the nearest date written above it in its file, and says which
line; one with neither takes the date its file is named for, and says so.
Sums no date reaches come last, marked "undated": your files don't say when.

It only reads. Exit codes, the kernel's: 0 sums found; 42 none in your
folder; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: a number as a sum writes one: thousands grouped with commas, pence after
#: a dot; what follows must not read as more of a number
NUMBER = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?(?![.,]?\d)"
#: the currency codes read, before the number as written, after it any case
CODES = frozenset(
    "USD EUR GBP JPY CHF CAD AUD NZD CNY INR RON PLN SEK NOK DKK CZK "
    "HUF BRL MXN ZAR TRY KRW UAH ILS".split()
)
MONEY = re.compile(
    rf"\b[A-Z]{{1,2}}[$£€¥₹] ?{NUMBER}"
    rf"|[$£€¥₹] ?{NUMBER}"
    rf"|\b(?P<before>[A-Z]{{3}}) ?{NUMBER}"
    rf"|(?<![\w.,]){NUMBER} ?(?P<after>[A-Za-z]{{3}})\b"
)


def sums(line: str) -> list[str]:
    """The sums a line writes, in its order: each MONEY match whose code, when
    it is a code that names the currency, is one the list has ("lei" after the
    number too, as Teodora's recipes price things)."""
    out = []
    for m in MONEY.finditer(line):
        if m.group("before") and m.group("before") not in CODES:
            continue
        after = m.group("after")
        if after and after.upper() not in CODES and after.lower() != "lei":
            continue
        out.append(m.group())
    return out


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def found(pile: list[dict]) -> list[dict]:
    """A row per sum: the date that reaches it (the line's own, else the
    nearest above in its file, else its file's name, each saying so), the sum
    as written, and its line. Dated rows oldest first, undated after, each by
    file, line and place in the line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, src, filed = "", 0, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            for k, amount in enumerate(sums(line)):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above, f"date from line {src}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "amount": amount,
                            "path": path, "line": n, "k": k,
                            "text": line.strip()})  # fmt: skip
            if said:
                above, src = said, n
    return sorted(
        out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"], r["k"])
    )


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def show(rows: list[dict]) -> list[str]:
    wa = max(len(r["amount"]) for r in rows)
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        where = f"{r['path']}:{r['line']}"
        tail = f"  ({r['note']})" if r["note"] else ""
        out.append(
            f"{day(r['when']):<10}  {r['amount']:<{wa}}  {where:<{wp}}"
            f"  {r['text'][:120]}{tail}"
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
    rows = found(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not rows:
        print("No sums of money in your folder.")
        return kernel.ESCALATE
    for line in show(rows):
        print(line)
    undated = sum(r["when"] == "" for r in rows)
    print(f"{len(rows)} sums: {len(rows) - undated} dated, {undated} undated")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
