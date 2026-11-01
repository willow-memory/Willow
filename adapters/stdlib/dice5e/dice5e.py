"""dice5e.py: full tabletop dice notation rolled on the record, every roll
checkable. Python 3.9+.

    python adapters/stdlib/dice5e/dice5e.py --box DIR roll DICE [--now TS]
    python adapters/stdlib/dice5e/dice5e.py --box DIR check

DICE is dice's notation (2d6, 1d20+3, 1d8+1d6) plus keeping: 4d6kh3 keeps
the highest three of four, 2d20kl1 the lowest one, and `adv` and `dis` are
2d20kh1 and 2d20kl1, so `adv+5` is a d20 at advantage plus five.

    4d6kh3: [6, 2, 5, 3] keep 6 + 5 + 3 = 14   (row 12)

The faces come from dice's seeded stream (sha256-stream/v1), seeded the same
way: the record's tip, the hash of the row before, with the dice written
after it. No one picks the seed. Every die is drawn, kept or not, so the
dropped ones are on the record too; among equal faces the first is kept.

Each roll is one `roll5e` row through the kernel's own append. `check`
throws every one again from its row, as dice's `check` does for its own.

Exit codes, the kernel's: 0 rolled, or every roll holds; 2 refused: dice it
can't read, a record that doesn't verify, or a roll that doesn't hold.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "dice"))
import dice  # noqa: E402
import kernel  # noqa: E402

KIND = "roll5e"
SHORT = {"adv": "2d20kh1", "dis": "2d20kl1"}
TERM = re.compile(r"([+-]?)(?:(\d*)d(\d+)(?:k([hl])(\d+))?|(\d+))", re.I)
BAD = "isn't dice notation: 4d6kh3, 2d20kl1, adv+5, 1d8+1d6"


def parse(text: str) -> tuple[list[tuple[int, int, int, str, int]], int]:
    """([(sign, count, sides, keep 'h' or 'l' or '', how many kept)], constant);
    ValueError if it isn't dice."""
    t = re.sub(r"\s*([+-])\s*", r"\1", text.strip().lower())
    t = re.sub(r"\b(adv|dis)\b", lambda m: SHORT[m.group(1)], t)
    if not t or TERM.sub("", t):
        raise ValueError(f"{text!r} {BAD}")
    terms, const, pos = [], 0, 0
    for m in TERM.finditer(t):
        if m.start() != pos or (pos and not m.group(1)):
            raise ValueError(f"{text!r} {BAD}")
        pos = m.end()
        sign = -1 if m.group(1) == "-" else 1
        if m.group(6):
            const += sign * int(m.group(6))
            continue
        count, sides = int(m.group(2) or 1), int(m.group(3))
        if not (1 <= count <= dice.MAX_DICE and 2 <= sides <= dice.MAX_SIDES):
            raise ValueError(f"{count}d{sides}: up to {dice.MAX_DICE} dice of 2 to "
                             f"{dice.MAX_SIDES} sides")  # fmt: skip
        keep, k = (m.group(4) or ""), int(m.group(5) or count)
        if not 1 <= k <= count:
            raise ValueError(f"{count}d{sides}k{keep}{k}: keep 1 to {count}")
        terms.append((sign, count, sides, keep, k))
    if not terms:
        raise ValueError(f"{text!r} rolls no dice")
    return terms, const


def kept(faces: list[int], keep: str, k: int) -> list[int]:
    """Which faces count, by place: the highest (or lowest) k, the first of
    equal faces first, in the order they were drawn."""
    if not keep:
        return list(range(len(faces)))
    order = sorted(
        range(len(faces)), key=lambda i: (-faces[i] if keep == "h" else faces[i], i)
    )
    return sorted(order[:k])


def throw(text: str, tip: str) -> dict:
    """The faces, the kept ones and the total for `text` seeded by `tip`."""
    terms, const = parse(text)
    rng = dice.Stream(f"{tip}:{text}".encode())
    faces, keeps, total = [], [], const
    for sign, count, sides, keep, k in terms:
        got = [rng.die(sides) for _ in range(count)]
        mine = kept(got, keep, k)
        faces.append(got)
        keeps.append(mine)
        total += sign * sum(got[i] for i in mine)
    return {"dice": text, "seed": tip, "generator": dice.GENERATOR,
            "faces": faces, "kept": keeps, "add": const, "total": total}  # fmt: skip


def said(row: dict) -> str:
    """4d6kh3: [6, 2, 5, 3] keep 6 + 5 + 3 = 14; a term taken away is "- (...)"."""
    terms, _ = parse(row["dice"])
    out = ""
    for n, ((sign, _c, _s, keep, _k), got, mine) in enumerate(
        zip(terms, row["faces"], row["kept"])
    ):
        part = " + ".join(str(got[i]) for i in mine)
        if keep:
            part = f"{got} keep {part}"
        if sign < 0:
            out += f" - ({part})" if n else f"-({part})"
        else:
            out += f" + {part}" if n else part
    if row["add"]:
        out += f" + {row['add']}" if row["add"] > 0 else f" - {-row['add']}"
    return f"{row['dice']}: {out} = {row['total']}"


def check(rows: list[dict]) -> tuple[int, str | None]:
    """(how many rolls hold, why the first that doesn't fails, or None)."""
    held = 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        before = rows[r["n"] - 1]["hash"] if r["n"] else kernel.GENESIS
        if r.get("seed") != before:
            return held, f"row {r['n']}: its seed isn't the hash of the row before it"
        try:
            again = throw(r["dice"], r["seed"])
        except (ValueError, KeyError) as e:
            return held, f"row {r['n']}: {e}"
        mine = (r.get("faces"), r.get("kept"), r.get("total"))
        if (again["faces"], again["kept"], again["total"]) != mine:
            return held, f"row {r['n']}: its faces aren't what its seed gives"
        held += 1
    return held, None


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            args.append(a)
    if not opts.get("--box") or any(not v for v in opts.values()):
        return usage()
    if args != ["check"] and (len(args) != 2 or args[0] != "roll"):
        return usage()
    if args == ["check"] and "--now" in opts:
        return usage()
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    if args == ["check"]:
        held, why = check(rows)
        if why:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
        print(f"{held} rolls on the record; every one holds.")
        return kernel.ALIVE
    try:
        roll = throw(args[1], rows[-1]["hash"] if rows else kernel.GENESIS)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    row = kernel.append(box, opts.get("--now") or kernel.now(), KIND, who="dice5e",
                        **roll)  # fmt: skip
    print(f"{said(row)}   (row {row['n']})")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
