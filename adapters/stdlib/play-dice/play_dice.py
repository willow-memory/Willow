"""play_dice.py: dice rolled on the record, every roll checkable. Python 3.9+.

    python adapters/stdlib/play-dice/play_dice.py --box DIR roll DICE [--now TS]
    python adapters/stdlib/play-dice/play_dice.py --box DIR said DICE FACES [--now TS]
    python adapters/stdlib/play-dice/play_dice.py --box DIR check

`roll` throws DICE (2d6, 1d20+3, 1d8+1d6) and writes one `roll` row through
the kernel's own append: the dice, each die's face, the total, and the seed.

    2d6+1: 4 + 6 + 1 = 11   (row 12)

The seed is the record's tip, the hash of the row before, with the dice
written after it: no one picks it, and it's fixed the moment the row before
is written. The faces come from willow-bot's seeded stream,
`sha256-stream/v1` (onescript/stream.py): SHA-256 over the seed and a
counter, read by rejection so no face is likelier than another, the same on
every Python.

`said` keeps a roll thrown with real dice, as the person says it: FACES are
the faces they read, one for each die, in order (`4,6` for 2d6). It is a
`roll` row like any other, but its generator is `said` and it has no seed:
nothing on the record chose it, and nothing can throw it again. Its
honesty is the table watching, not a seed, and it says so ("as said").

    2d6: 4 + 6 = 10, as said   (row 13)

`check` throws every roll on the record again from its row: its seed must be
the hash of the row before it, and the faces must be what that seed gives.
A said roll is held to its dice instead: one face for each die, each on it,
and the total theirs. Every roll holds, or the first that doesn't is named.
A roll can't be changed after the fact; a seeded one can be thrown again, by
anyone, from the record. A caller that holds its rolls to seeds alone (a
game where a said roll would let a player pick their dice) asks
`check(rows)`, which refuses a said roll; one that takes them asks
`check(rows, said=True)`.

Exit codes, the kernel's: 0 rolled, said, or every roll holds; 2 refused:
dice it can't read, faces that aren't theirs, a record that doesn't verify,
or a roll that doesn't hold.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "roll"
GENERATOR = "sha256-stream/v1"
SAID = "said"  # a roll thrown with real dice, kept as the person said it
TERM = re.compile(r"([+-]?)\s*(?:(\d*)d(\d+)|(\d+))", re.I)
MAX_DICE, MAX_SIDES = 100, 1000


class Stream:
    """willow-bot's onescript/stream.py Stream: SHA-256 over seed || counter
    (8 bytes, big-endian), the first four bytes a u32; below() by rejection."""

    def __init__(self, seed: bytes):
        self.seed, self.n = seed, 0

    def u32(self) -> int:
        d = hashlib.sha256(self.seed + self.n.to_bytes(8, "big")).digest()
        self.n += 1
        return int.from_bytes(d[:4], "big")

    def below(self, k: int) -> int:
        cap = (1 << 32) - (1 << 32) % k
        while (x := self.u32()) >= cap:
            pass
        return x % k

    def die(self, sides: int) -> int:
        return self.below(sides) + 1


def parse(dice: str) -> tuple[list[tuple[int, int, int]], int]:
    """([(sign, count, sides)], constant); ValueError if it isn't dice."""
    text = re.sub(r"\s*([+-])\s*", r"\1", dice.strip())  # spaces only around + and -
    if not text or TERM.sub("", text) or re.search(r"\s", text):
        raise ValueError(f"{dice!r} isn't dice notation: 2d6, 1d20+3, 1d8+1d6")
    terms, const, pos = [], 0, 0
    for m in TERM.finditer(text):
        if m.start() != pos or (pos and not m.group(1)):
            raise ValueError(f"{dice!r} isn't dice notation: 2d6, 1d20+3, 1d8+1d6")
        pos = m.end()
        sign = -1 if m.group(1) == "-" else 1
        if m.group(4):
            const += sign * int(m.group(4))
            continue
        count, sides = int(m.group(2) or 1), int(m.group(3))
        if not (1 <= count <= MAX_DICE and 2 <= sides <= MAX_SIDES):
            raise ValueError(
                f"{count}d{sides}: up to {MAX_DICE} dice of 2 to {MAX_SIDES} sides"
            )
        terms.append((sign, count, sides))
    if not terms:
        raise ValueError(f"{dice!r} rolls no dice")
    return terms, const


def throw(dice: str, tip: str) -> dict:
    """The faces and total for `play-dice` seeded by `tip`: the same every time."""
    terms, const = parse(dice)
    rng = Stream(f"{tip}:{dice}".encode())
    faces = [
        [sign * rng.die(sides) for _ in range(count)] for sign, count, sides in terms
    ]
    total = sum(sum(f) for f in faces) + const
    return {"dice": dice, "seed": tip, "generator": GENERATOR, "faces": faces,
            "add": const, "total": total}  # fmt: skip


def told(dice: str, faces: str) -> dict:
    """A roll thrown with real dice: FACES as read, "4,6" or "4 6", one for
    each die of DICE, in order; ValueError if they aren't those dice's faces."""
    terms, const = parse(dice)
    try:
        read = [int(x) for x in re.split(r"[\s,]+", faces.strip()) if x]
    except ValueError:
        raise ValueError(f"{faces!r} isn't faces: numbers, like 4,6") from None
    if len(read) != sum(count for _, count, _ in terms):
        raise ValueError(f"{dice} is {sum(c for _, c, _ in terms)} dice: say one face for each, like 4,6")  # fmt: skip
    got, it = [], iter(read)
    for sign, count, sides in terms:
        group = [next(it) for _ in range(count)]
        bad = [f for f in group if not 1 <= f <= sides]
        if bad:
            raise ValueError(f"{bad[0]} isn't a face of a d{sides}: 1 to {sides}")
        got.append([sign * f for f in group])
    total = sum(sum(f) for f in got) + const
    return {"dice": dice, "generator": SAID, "faces": got, "add": const, "total": total}  # fmt: skip


def said(row: dict) -> str:
    parts = [str(f) if f >= 0 else f"({f})" for group in row["faces"] for f in group]
    if row["add"]:
        parts.append(str(row["add"]) if row["add"] > 0 else f"({row['add']})")
    tail = ", as said" if row.get("generator") == SAID else ""
    return f"{row['dice']}: {' + '.join(parts)} = {row['total']}{tail}"


def check(rows: list[dict], said: bool = False) -> tuple[int, str | None]:
    """(how many rolls hold, why the first that doesn't fails, or None). A
    said roll is held to its dice, and refused unless SAID: where only seeds
    count, one would be a roll somebody picked."""
    held = 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        if r.get("generator") == SAID:
            if not said:
                return held, f"row {r['n']}: a roll said, not thrown, where only seeded rolls count"  # fmt: skip
            try:
                again = told(r["dice"], ",".join(str(abs(f)) for g in r.get("faces", []) for f in g))  # fmt: skip
            except (ValueError, KeyError, TypeError) as e:
                return held, f"row {r['n']}: {e}"
            if (again["faces"], again["total"], again["add"]) != (r.get("faces"), r.get("total"), r.get("add")):  # fmt: skip
                return held, f"row {r['n']}: its faces aren't its dice's, or don't add up to its total"  # fmt: skip
            held += 1
            continue
        before = rows[r["n"] - 1]["hash"] if r["n"] else kernel.GENESIS
        if r.get("seed") != before:
            return held, f"row {r['n']}: its seed isn't the hash of the row before it"
        try:
            again = throw(r["dice"], r["seed"])
        except (ValueError, KeyError) as e:
            return held, f"row {r['n']}: {e}"
        if (again["faces"], again["total"]) != (r.get("faces"), r.get("total")):
            return held, f"row {r['n']}: its faces aren't what its seed gives"
        held += 1
    return held, None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or not (
        args == ["check"]
        or (len(args) == 2 and args[0] == "roll")
        or (len(args) == 3 and args[0] == "said")
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    if args == ["check"]:
        held, why = check(rows, said=True)
        if why:
            print(f"refused: {why} ({held} before it held)", file=sys.stderr)
            return kernel.REFUSED
        told_ = sum(1 for r in rows if r["kind"] == KIND and r.get("generator") == SAID)
        print(f"{held} roll{'s' if held != 1 else ''} on the record; every one holds." + (f" {told_} of them said, kept as said." if told_ else ""))  # fmt: skip
        return kernel.ALIVE
    try:
        if args[0] == "said":
            got = told(args[1], args[2])
        else:
            got = throw(args[1], rows[-1]["hash"] if rows else kernel.GENESIS)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    row = kernel.append(box, opts.get("--now") or kernel.now(), KIND, who="dice", **got)
    print(f"{said(got)}   (row {row['n']})")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
