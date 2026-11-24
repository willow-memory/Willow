"""carry_sheet.py: what characters carry, use up, and come through, from night to night, on the record. Python 3.9+.

    python adapters/stdlib/carry-sheet/carry_sheet.py --box DIR write --names NAMES LINE [--now TS]
    python adapters/stdlib/carry-sheet/carry_sheet.py --box DIR sheet [--name NAME]

The person running the game writes it in plain words, one change a line, the
way the table says it:

    Tamsin finds a rope        Oro uses the rope
    Oro picks up a lantern     Tamsin gives away the lantern
    Oro is hurt by a club      Oro is healed

The name is one of NAMES (commas between them), first; the word after it
says what changed (carry, spend, hurt or heal); the rest is the thing, or
how. `write` keeps each change as a `table-carry` row and prints that
character's sheet as it stands; a line it can't read is refused and nothing
is written. `sheet` reads every row about a character in order, so a sheet
carries over between nights: nothing is taken off the record, a thing used
is a later row, and a wound lasts until a line says they're healed. A thing
is matched by its words, an article or a plural aside, so "uses the ropes"
spends "a rope". With no --name, every character the record has a change for.

Exit codes, the kernel's: 0 done; 2 refused, with why.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "lines-veils"))
import kernel  # noqa: E402
import lines_veils  # noqa: E402

KIND, WHO = "table-carry", "carry-sheet"
GAIN = ("finds", "found", "gets", "got", "picks up", "picked up", "takes", "took", "gains", "is given", "buys", "bought", "carries")  # fmt: skip
LOSE = ("uses up", "used up", "uses", "used", "loses", "lost", "spends", "spent", "drops", "dropped", "gives away", "gave away", "breaks", "broke")  # fmt: skip
HURT = ("is hurt", "gets hurt", "got hurt", "is wounded", "is poisoned", "is cursed")
HEAL = ("is healed", "heals", "healed", "is better", "is fine", "rests")
THE = re.compile(r"^(?:a|an|the|some|her|his|their|its|one)(?:\s+|$)", re.IGNORECASE)
USAGE = __doc__.split("\n\n")[1]


def refuse(why: str) -> int:
    print(f"carry-sheet: {why}", file=sys.stderr)
    return kernel.REFUSED


def read(line: str, names: list[str]) -> dict | None:
    """{char, change (carry, spend, hurt, heal), what} from a line, or None
    when it doesn't start with one of NAMES and a word this knows."""
    s = line.strip().rstrip(".!")
    for name in sorted(names, key=len, reverse=True):
        if s.lower().startswith(name.lower() + " "):
            rest = s[len(name) :].strip()
            for change, verbs in (("hurt", HURT), ("heal", HEAL), ("spend", LOSE), ("carry", GAIN)):  # fmt: skip
                for v in sorted(verbs, key=len, reverse=True):
                    if rest.lower() == v or rest.lower().startswith(v + " "):
                        what = rest[len(v) :].strip()  # as written; matched without its article  # fmt: skip
                        if change in ("carry", "spend") and not THE.sub("", what):
                            return None
                        return {"char": name, "change": change, "what": what}
    return None


def same_thing(a: str, b: str) -> bool:
    """Two names for a thing, the same but for an article or a plural."""
    wa, wb = lines_veils.words(THE.sub("", a)), lines_veils.words(THE.sub("", b))
    return len(wa) == len(wb) and all(lines_veils.same(x, y) for x, y in zip(wa, wb))  # fmt: skip


def sheet(rows: list[dict], name: str) -> tuple[list[str], list[str]]:
    """(what NAME carries now, how they're hurt now), from every row in order."""
    carrying: list[str] = []
    hurt: list[str] = []
    for r in rows:
        if r["kind"] != KIND or r.get("char", "").lower() != name.lower():
            continue
        if r["change"] == "carry":
            carrying.append(r["what"])
        elif r["change"] == "spend":
            hit = next((c for c in carrying if same_thing(c, r["what"])), None)
            if hit is not None:
                carrying.remove(hit)
        elif r["change"] == "hurt":
            hurt.append(r["what"])
        elif r["change"] == "heal":
            hurt = []
    return carrying, hurt


def said(name: str, carrying: list[str], hurt: list[str]) -> str:
    """One line a table reads aloud, or "" when there's nothing to say."""
    bits = []
    if carrying:
        bits.append("carries " + ", ".join(carrying))
    if hurt:
        how = "; ".join(h for h in hurt if h)
        bits.append("is still hurt" + (f" ({how})" if how else ""))
    return f"{name} " + " and ".join(bits) if bits else ""


def characters(rows: list[dict]) -> list[str]:
    """Every character the record has a change for, in the order first met."""
    return list(dict.fromkeys(r["char"] for r in rows if r["kind"] == KIND and r.get("char")))  # fmt: skip


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--names", "--name", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    cmd = args[0] if args else ""
    ok = (cmd == "write" and len(args) == 2 and opts.get("--names") and "--name" not in opts) or (cmd == "sheet" and len(args) == 1 and "--names" not in opts and opts.get("--name", "x"))  # fmt: skip
    if not opts.get("--box") or not ok:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    if cmd == "write":
        names = [n.strip() for n in opts["--names"].split(",") if n.strip()]
        got = read(args[1], names)
        if got is None:
            return refuse(f"{args[1]!r} isn't a line this reads: one of {', '.join(names)}, then what changed (finds, uses, is hurt, is healed), then the thing")  # fmt: skip
        row = kernel.append(
            box, opts.get("--now") or kernel.now(), KIND, who=WHO, **got
        )
        rows.append(row)
        now = said(got["char"], *sheet(rows, got["char"]))
        print((now or f"{got['char']} carries nothing and isn't hurt") + f"   (row {row['n']})")  # fmt: skip
        return kernel.ALIVE
    names = [opts["--name"]] if "--name" in opts else characters(rows)
    lines = [said(n, *sheet(rows, n)) for n in names]
    for n, line in zip(names, lines):
        print(line or f"{n} carries nothing and isn't hurt")
    if not names:
        print("no one's sheet is on the record")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
