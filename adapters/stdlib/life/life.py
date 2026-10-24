"""life.py: Conway's Game of Life, played on the record. Python 3.9+.

    python adapters/stdlib/life/life.py --box DIR play [--seed TEXT] [--size N]
        [--density PCT] [--generations N] [--rule B3/S23] [--now TS]
    python adapters/stdlib/life/life.py --box DIR check

The most deterministic game there is: no players and no dice, so the first
board fixes every later one. `play` draws a first board (a square soup of
--size cells a side, 16 unless said, each alive at --density percent, 35
unless said) from willow-bot's seeded stream, `sha256-stream/v1`, seeded by
--seed or, without one, by the record's tip, so no one picks it. It runs
--generations steps (64 unless said, at most 500) on an unbounded plane and
writes one `life` row through the kernel's own append: the seed, the rule,
and for every generation its population, where the pattern sits, and the
SHA-256 of the board, then how it ended:

    dies         nothing left
    still        the same board, in place (period 1)
    oscillator   back to an earlier board, in place, every P generations
    spaceship    back to an earlier board, moved, every P generations
    running      no board repeated within the generations played

A board's hash is of its live cells written from the top-left live cell, so
one shape has one hash wherever it sits; that's how a spaceship is known.
`check` plays every `life` row again from its own seed and rule, and the
first generation that doesn't match is named.

The game is willow-bot's life (onescript/life.py), which writes the same
rows through its table; this writes them through the kernel's append.

Exit codes, the kernel's: 0 played, or every game holds; 2 refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "life"
GENERATOR = "sha256-stream/v1"
RULE = re.compile(r"^B([0-8]*)/S([0-8]*)$")
MAX_GENERATIONS, MAX_SIZE = 500, 64


class Stream:
    """willow-bot's onescript/stream.py Stream (see the dice add-on)."""

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


def rule_of(text: str) -> tuple[frozenset, frozenset]:
    m = RULE.match(text)
    if not m:
        raise ValueError(f"{text!r} isn't a Life-like rule, B3/S23 for instance")
    return frozenset(map(int, m.group(1))), frozenset(map(int, m.group(2)))


def soup(seed: bytes, size: int, density: int) -> set[tuple[int, int]]:
    rng = Stream(seed)
    return {
        (x, y) for y in range(size) for x in range(size) if rng.below(100) < density
    }


def step(board: set, birth: frozenset, survive: frozenset) -> set:
    counts: dict[tuple[int, int], int] = {}
    for x, y in board:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    c = (x + dx, y + dy)
                    counts[c] = counts.get(c, 0) + 1
    return {
        c for c, n in counts.items() if (n in survive if c in board else n in birth)
    }


def shape(board: set) -> tuple[str, int, int]:
    """(the hash of the board from its top-left live cell, that cell's x, y)."""
    if not board:
        return hashlib.sha256(b"").hexdigest()[:16], 0, 0
    x0, y0 = min(x for x, _ in board), min(y for _, y in board)
    cells = ";".join(f"{x - x0},{y - y0}" for x, y in sorted(board))
    return hashlib.sha256(cells.encode()).hexdigest()[:16], x0, y0


def run(board: set, generations: int, rule: str) -> tuple[list, str, int]:
    """(each generation's [population, x, y, hash], fate, period)."""
    birth, survive = rule_of(rule)
    steps, seen, fate, period = [], {}, "running", 0
    for g in range(generations + 1):
        h, x, y = shape(board)
        steps.append([len(board), x, y, h])
        if not board:
            fate = "dies"
            break
        if h in seen:
            first = seen[h]
            period = g - first
            moved = (x, y) != tuple(steps[first][1:3])
            fate = "spaceship" if moved else ("still" if period == 1 else "oscillator")
            break
        seen[h] = g
        if g < generations:
            board = step(board, birth, survive)
    return steps, fate, period


def play(seed: bytes, size: int, density: int, generations: int, rule: str) -> dict:
    steps, fate, period = run(soup(seed, size, density), generations, rule)
    return {"seed": seed.hex(), "generator": GENERATOR, "size": size, "density": density,
            "rule": rule, "generations": generations, "steps": steps,
            "fate": fate, "period": period}  # fmt: skip


def check(rows: list[dict]) -> tuple[int, str | None]:
    held = 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        try:
            again = play(
                bytes.fromhex(r["seed"]),
                r["size"],
                r["density"],
                r["generations"],
                r["rule"],
            )
        except (ValueError, KeyError, TypeError) as e:
            return held, f"row {r['n']}: {e}"
        for g, (a, b) in enumerate(zip(again["steps"], r.get("steps", []))):
            if a != b:
                return held, f"row {r['n']}: generation {g} isn't what the rule makes"
        if (again["steps"], again["fate"], again["period"]) != (
            r.get("steps"),
            r.get("fate"),
            r.get("period"),
        ):
            return held, f"row {r['n']}: how it ended isn't what the rule makes"
        held += 1
    return held, None


def picture(seed: bytes, game: dict) -> str:
    """The last board, drawn, at most 40 cells a side."""
    birth, survive = rule_of(game["rule"])
    board = soup(seed, game["size"], game["density"])
    for _ in range(len(game["steps"]) - 1):
        board = step(board, birth, survive)
    if not board:
        return "(empty)"
    x0, y0 = min(x for x, _ in board), min(y for _, y in board)
    w = min(40, max(x for x, _ in board) - x0 + 1)
    h = min(40, max(y for _, y in board) - y0 + 1)
    return "\n".join(
        "".join("#" if (x0 + i, y0 + j) in board else "." for i in range(w))
        for j in range(h)
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in (
            "--box",
            "--now",
            "--seed",
            "--size",
            "--density",
            "--generations",
            "--rule",
        ):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args not in (["play"], ["check"]):
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
        held, why = check(rows)
        if why:
            print(f"refused: {why} ({held} before it held)", file=sys.stderr)
            return kernel.REFUSED
        print(f"{held} game{'s' if held != 1 else ''} on the record; every one holds.")
        return kernel.ALIVE
    try:
        size, density = int(opts.get("--size", "16")), int(opts.get("--density", "35"))
        generations = int(opts.get("--generations", "64"))
        rule = opts.get("--rule", "B3/S23")
        rule_of(rule)
        if not (
            1 <= size <= MAX_SIZE
            and 0 <= density <= 100
            and 0 <= generations <= MAX_GENERATIONS
        ):
            raise ValueError(
                f"size 1 to {MAX_SIZE}, density 0 to 100, generations 0 to {MAX_GENERATIONS}"
            )
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    text = opts.get("--seed") or (rows[-1]["hash"] if rows else kernel.GENESIS)
    seed = hashlib.sha256(text.encode()).digest()
    game = play(seed, size, density, generations, rule)
    row = kernel.append(
        box, opts.get("--now") or kernel.now(), KIND, who="life", **game
    )
    last = game["steps"][-1]
    period = f", every {game['period']} generations" if game["period"] > 1 else ""
    print(picture(seed, game))
    print(f"\n{game['fate']}{period}: {last[0]} alive after {len(game['steps']) - 1} "
          f"generations   (row {row['n']})")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
