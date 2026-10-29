"""livestock.py: each animal's births, treatments and sales, from your farm
records. Python 3.9+.

    python adapters/stdlib/livestock/livestock.py --box DIR

The lines of your farm notes about one animal at a time, gathered by animal:

    #412     born 2025-04-10  treated 1 time, last 2026-02-02  alive
    Daisy    born 2024-03-02  treated 3 times, last 2026-05-01  sold 2026-09-15 (1,200.00)
    #388     born not written  treated 0 times  died 2026-01-20
    3 animals: 1 alive, 1 sold, 1 died

**What counts.** A line, on a day, about livestock (the line or the path of its
file says cow, calf, heifer, bull, steer, ewe, lamb, ram, sheep, goat, kid, pig,
sow, boar, piglet, horse, mare, foal, hen, flock, herd, paddock, farm or tag)
that names an animal and says a birth (born, calved, lambed, kidded, farrowed,
foaled, hatched), a treatment (treated, vaccinated, wormed, drenched, dosed,
injected) or an end (sold, culled, slaughtered, died). The animal is the tag
("tag 412", "ear tag 412", "#412"), else the name the line starts with, after
any date ("Daisy: treated for mastitis"). A line naming no animal is left out:
a herd's drench is not any one animal's.

**An animal's story** is its latest birth line, its treatments counted with the
last, and its latest end: sold, culled, slaughtered (all "sold" or "culled",
named as written) or died. An amount with a sign on an end line (a sale's price)
is shown after it. An animal with no end is alive as far as the notes say.
Tags first, then names.

Nothing here is advice and no withdrawal period is worked out: the vet and the
label say that. It only reads. Exit codes, the kernel's: 0 animals found; 42 none;
2 refused.
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

CONTEXT = re.compile(
    r"\b(?:cows?|cattle|calf|calves|heifers?|bulls?|steers?|ewes?|lambs?|rams?|sheep|goats?|kids?|pigs?|sows?|boars?|piglets?|horses?|mares?|foals?|hens?|flock|herd|paddock|farm|tags?)\b",
    re.I,
)
KINDS = (  # an end beats a birth beats a treatment, in the order a line is read
    ("end", re.compile(r"\b(?P<w>sold|culled|slaughtered|died)\b", re.I)),
    (
        "birth",
        re.compile(r"\b(?:born|calved|lambed|kidded|farrowed|foaled|hatched)\b", re.I),
    ),
    (
        "treat",
        re.compile(r"\b(?:treated|vaccinated|wormed|drenched|dosed|injected)\b", re.I),
    ),
)
TAG = re.compile(r"(?:\b(?:ear )?tags?\s*#?|#)(\d+)\b", re.I)
LEAD = re.compile(
    r"^\s*[-*•]?\s*(?:[\d./-]+\s+)?([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*[:\-–]"
)
NOT_NAMES = {"note", "notes", "farm", "herd", "flock", "vet", "today", "cow", "ewe", "sold", "subject", "from", "to", "re"}  # fmt: skip
MONEY = re.compile(r"(?<![\w.])([£$€]?\s?\d[\d,]*\.\d{2})(?![\d])")


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says, else the nearest above it in its file, else its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def animal_of(line: str) -> str:
    """The animal a line is about: its tag as #412, else the name it starts with."""
    m = TAG.search(line)
    if m:
        return f"#{m.group(1)}"
    m = LEAD.search(line)
    if m and m.group(1).lower() not in NOT_NAMES:
        return m.group(1)
    return ""


def herd(pile: list[dict]) -> dict[str, dict]:
    """{animal: {birth, treats: [days], end: (day, word, price)}}."""
    out: dict[str, dict] = {}
    for day, path, _n, line in entries(pile):
        if not CONTEXT.search(path + " " + line):
            continue
        who = animal_of(line)
        kind = next((k for k, rx in KINDS if rx.search(line)), "")
        if not who or not kind:
            continue
        rec = out.setdefault(who, {"birth": "", "treats": [], "end": None})
        if kind == "birth":
            rec["birth"] = max(rec["birth"], day)
        elif kind == "treat":
            rec["treats"].append(day)
        else:
            word = dict(KINDS)["end"].search(line).group("w").lower()
            price = MONEY.search(line)
            if rec["end"] is None or day >= rec["end"][0]:
                rec["end"] = (
                    day,
                    word,
                    price.group(1).replace(" ", "") if price else "",
                )
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(got: dict) -> list[str]:
    order = sorted(got, key=lambda k: (0, int(k[1:])) if k.startswith("#") else (1, k))
    w = max(len(k) for k in order)
    out, tally = [], {"alive": 0, "sold": 0, "culled": 0, "slaughtered": 0, "died": 0}
    for k in order:
        r = got[k]
        born = f"born {dash(r['birth'])}" if r["birth"] else "born not written"
        n = len(r["treats"])
        treated = f"treated {n} time{'s' if n != 1 else ''}" + (
            f", last {dash(max(r['treats']))}" if n else ""
        )
        if r["end"]:
            day, word, price = r["end"]
            end = f"{word} {dash(day)}" + (f" ({price})" if price else "")
            tally[word] += 1
        else:
            end = "alive"
            tally["alive"] += 1
        out.append(f"{k:<{w}}  {born}  {treated}  {end}")
    bits = [f"{v} {k}" for k, v in tally.items() if v]
    n = len(order)
    out.append(f"{n} animal{'s' if n != 1 else ''}: {', '.join(bits)}")
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
    got = herd(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not got:
        print(
            "No line of your folder says a birth, a treatment or an end for a named animal."
        )
        return kernel.ESCALATE
    print("\n".join(show(got)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
