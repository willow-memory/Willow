"""debts.py: who owes whom, from the IOUs in your notes and messages, cited.

    python adapters/stdlib/debts/debts.py --box DIR

Every line of your folder that speaks of money owed, oldest first, each with
its date, the sum it names, and where it is:

    2023-04-17  $10   chats/mags.txt:3   Terry says Gerry owes him $10 from the footy
    2025-02-28  £100  chats/teo.txt:9    first £100 back, thank you again x
    undated     -     notes.md:4         I still owe Dev for the mixer

A line speaks of money owed when it says one of the owing words — owe, owes,
owed, owing, IOU, repay and its forms, paid back, pay back — or says lent or
borrowed with a sum of money on the same line. The sum is read as the
amounts add-on reads one (a number written with its currency, never a bare
number); a line that names none shows a dash: the debt is written, the
amount is the line's to say. Things lent and returned — the drill, the cake
pan — are [lending](../lending/)'s; money is this one's.

**Nothing is netted.** Who owes whom is what each line says, in its own
words: a "paid back" line is listed beside the debt it answers, dated, and
whether anything still stands is your files' story to finish, not a balance
this invents. Every line stays, each cited, so the story can be checked.

A line's date is the latest it says, read as the kernel reads one (its
`newest`; 11/03/2026, either way round, is never guessed); a line that says
none takes the nearest date written above it in its file, else the date its
file is named for, and the listing says which. Undated lines come last.

It only reads. Exit codes, the kernel's: 0 debts spoken of; 42 none; 2
refused.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

AMOUNTS = Path(__file__).resolve().parents[1] / "amounts" / "amounts.py"
_spec = importlib.util.spec_from_file_location("willow_amounts_for_debts", AMOUNTS)
amounts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(amounts)

#: the owing words; lent and borrowed join them only with a sum on the line
OWING = re.compile(r"\b(?:owes?|owed|owing|iou|repay\w*|paid back|pays? back"
                   r"|paying back)\b", re.IGNORECASE)  # fmt: skip
LENT = re.compile(r"\b(?:lends?|lent|loaned|borrows?|borrowed|borrowing)\b",
                  re.IGNORECASE)  # fmt: skip


def speaks_of_debt(line: str) -> bool:
    """Whether the line speaks of money owed: an owing word, or lent or
    borrowed with a sum of money on the same line (a lent drill is
    lending's)."""
    if OWING.search(line):
        return True
    return bool(LENT.search(line)) and bool(amounts.sums(line))


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def found(pile: list[dict]) -> list[dict]:
    """A row per line that speaks of money owed, dated by its line, the
    nearest date above it in its file, or its file's name, each saying so;
    dated rows oldest first, undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, filed = None, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            if speaks_of_debt(line):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above[0], f"date from line {above[1]}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                sums = amounts.sums(line)
                out.append({"when": when, "note": note, "path": path, "line": n,
                            "sum": sums[0] if sums else "-",
                            "text": line.strip()})  # fmt: skip
            if said:
                above = (said, n)
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def show(rows: list[dict]) -> list[str]:
    ws = max(len(r["sum"]) for r in rows)
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        where = f"{r['path']}:{r['line']}"
        tail = f"  ({r['note']})" if r["note"] else ""
        out.append(f"{day(r['when']):<10}  {r['sum']:<{ws}}  {where:<{wp}}"
                   f"  {r['text'][:110]}{tail}")  # fmt: skip
    summed = sum(r["sum"] != "-" for r in rows)
    undated = sum(r["when"] == "" for r in rows)
    one = len(rows) == 1
    out.append(f"{len(rows)} line{'' if one else 's'} speak{'s' if one else ''}"
               f" of debts: {summed} with a sum, {undated} undated")  # fmt: skip
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
        print("No line of your folder speaks of money owed.")
        return kernel.ESCALATE
    for line in show(rows):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
