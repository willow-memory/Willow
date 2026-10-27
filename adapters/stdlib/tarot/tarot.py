"""tarot.py: a seeded tarot draw on the record, replayable by anyone with it.

    python adapters/stdlib/tarot/tarot.py --box DIR draw [N] [--now TS]
    python adapters/stdlib/tarot/tarot.py --box DIR check

`draw` deals N cards (three unasked) from the full deck of 78, each upright
or reversed, and writes one `draw` row through the kernel's own append:

    1. The Moon, reversed
    2. Six of Cups
    3. The Tower
    (row 9; replayable from its seed by anyone)

The seed is the record's tip, the hash of the row before: no one picks it,
and it is fixed the moment that row is written. The cards come from
willow-bot's seeded stream (sha256-stream/v1), dealt without replacement by
rejection, a coin from the same stream turning each; the same seed deals
the same spread on any machine, which is the whole of the trick.

`check` deals every draw on the record again from its row: its seed must be
the hash of the row before it, and its cards must be what that seed deals.
Every draw holds, or the first that doesn't is named. A draw can't be
changed after the fact; it can be dealt again, by anyone, from the record.

What the cards mean is yours: this deals them honestly and says nothing
about them, and the deck is the standard 78, named in full. Exit codes, the
kernel's: 0 dealt, or every draw holds; 42 never; 2 refused: a count the
deck hasn't, a record that doesn't verify, or a draw that doesn't hold.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "draw"
GENERATOR = "sha256-stream/v1"
MAJORS = (
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot", "Strength",
    "The Hermit", "Wheel of Fortune", "Justice", "The Hanged Man", "Death",
    "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World",
)  # fmt: skip
RANKS = ("Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Page", "Knight", "Queen", "King")  # fmt: skip
SUITS = ("Wands", "Cups", "Swords", "Pentacles")
DECK = MAJORS + tuple(f"{r} of {s}" for s in SUITS for r in RANKS)


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


def deal(count: int, tip: str) -> dict:
    """The spread `tip` deals: `count` cards without replacement, each
    upright or reversed by a coin from the same stream; the same every
    time."""
    rng = Stream(f"{tip}:tarot".encode())
    left = list(DECK)
    cards = []
    for _ in range(count):
        name = left.pop(rng.below(len(left)))
        cards.append([name, rng.below(2) == 1])
    return {"count": count, "seed": tip, "generator": GENERATOR, "cards": cards}


def said(row: dict) -> str:
    return "\n".join(
        f"{i}. {name}{', reversed' if turned else ''}"
        for i, (name, turned) in enumerate(row["cards"], 1)
    )


def check(rows: list[dict]) -> tuple[int, str | None]:
    """(how many draws hold, why the first that doesn't fails, or None)."""
    held = 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        before = rows[r["n"] - 1]["hash"] if r["n"] else kernel.GENESIS
        if r.get("seed") != before:
            return held, f"row {r['n']}: its seed isn't the hash of the row before it"
        if not isinstance(r.get("count"), int) or not 1 <= r["count"] <= len(DECK):
            return held, f"row {r['n']}: a count the deck hasn't"
        again = deal(r["count"], r["seed"])
        if again["cards"] != r.get("cards"):
            return held, f"row {r['n']}: its cards aren't what its seed deals"
        held += 1
    return held, None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    drawing = args == ["draw"] or (len(args) == 2 and args[0] == "draw")
    if not opts.get("--box") or not (drawing or args == ["check"]):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused: the record doesn't verify:", *breaks, sep="\n  ",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if args == ["check"]:
        held, why = check(rows)
        if why:
            print(f"refused: {why} ({held} before it held)", file=sys.stderr)
            return kernel.REFUSED
        print(f"{held} draw{'s' if held != 1 else ''} on the record; every one holds.")
        return kernel.ALIVE
    count = args[1] if len(args) == 2 else "3"
    if not count.isdigit() or not 1 <= int(count) <= len(DECK):
        print(f"refused: the deck deals 1 to {len(DECK)} cards, not {count!r}",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    got = deal(int(count), rows[-1]["hash"] if rows else kernel.GENESIS)
    row = kernel.append(box, opts.get("--now") or kernel.now(), KIND, who="tarot",
                        **got)  # fmt: skip
    print(said(got))
    print(f"(row {row['n']}; replayable from its seed by anyone)")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
