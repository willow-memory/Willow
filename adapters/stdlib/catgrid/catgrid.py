"""catgrid.py: a cat in every row, column and colour region, played on the record. Python 3.9+.

    python adapters/stdlib/catgrid/catgrid.py --box DIR play [--seed TEXT]
        [--size N] [--moves A1,B3,...] [--now TS]
    python adapters/stdlib/catgrid/catgrid.py --box DIR check

A board is N squares a side (5 unless said, 4 to 8) cut into N connected
colour regions. The answer puts one cat in every row, every column and every
region, no two touching, even at a corner, and the board is built so that
answer is the only one. Rows are letters and columns numbers: A1 is the corner.

`play` builds the board from willow-bot's seeded stream, `sha256-stream/v1`,
seeded by --seed or, without one, by the record's tip, so no one picks it.
--moves are the cats you try, in order. A cat on the answer stays; a cat off
it costs one of three hearts and is not placed. Three lost, or every cat
placed, ends the game, and a move after that is refused. Without --moves it
writes the board still open. It prints the board and writes one `catgrid` row
through the kernel's own append: the seed, the size, the regions, each move
and whether it was right, and how it ended (won, lost or open).

`check` builds every board on the record again from its own seed and plays
its moves again: the regions, and every move's verdict, must be what the
seed gives. The first that isn't is named. The answer is never written to
the row; it is what the seed and the one-answer search give.

Exit codes, the kernel's: 0 played, or every game holds; 2 refused: a
size or move it can't use, a record that doesn't verify, or a game that
doesn't hold.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "catgrid"
GENERATOR = "sha256-stream/v1"
MIN_SIZE, MAX_SIZE, DEFAULT_SIZE = 4, 8, 5  # 2x2 and 3x3 have no placement at all
HEARTS = 3
DRAWS, REPAIRS = 300, 200
CELL = re.compile(r"^([A-Z])([1-9][0-9]*)$")


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

    def pick(self, items: list):
        return items[self.below(len(items))]

    def shuffled(self, items) -> list:
        out = list(items)
        for i in range(len(out) - 1, 0, -1):  # Fisher-Yates, drawn from the stream
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out


def solutions(n: int, regions: list):
    """Every placement, as the cat's column in each row; no two cats touch."""
    cols: list[int] = []

    def go(row: int):
        if row == n:
            yield tuple(cols)
            return
        for c in range(n):
            if c in cols or (cols and abs(c - cols[-1]) < 2):
                continue
            if any(
                regions[r * n + cols[r]] == regions[row * n + c] for r in range(row)
            ):
                continue
            cols.append(c)
            yield from go(row + 1)
            cols.pop()

    yield from go(0)


def placement(n: int, rng: Stream) -> tuple[int, ...]:
    """One cat in every row and column, none touching, columns tried in drawn order."""
    cols: list[int] = []

    def go(row: int) -> bool:
        if row == n:
            return True
        for c in rng.shuffled(range(n)):
            if c not in cols and (not cols or abs(c - cols[-1]) >= 2):
                cols.append(c)
                if go(row + 1):
                    return True
                cols.pop()
        return False

    go(0)
    return tuple(cols)


def neighbours(i: int, n: int) -> list[int]:
    r, c = divmod(i, n)
    return [rr * n + cc for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= rr < n and 0 <= cc < n]  # fmt: skip


def grow(n: int, cols: tuple, rng: Stream) -> list[int]:
    """Each cat starts a region; a drawn region takes a drawn bordering cell until none is left."""
    region = [0] * (n * n)
    for r, c in enumerate(cols):
        region[r * n + c] = r + 1
    for _ in range(n * n - n):
        frontier: dict[int, set] = {}
        for i, owner in enumerate(region):
            if owner:
                for j in neighbours(i, n):
                    if not region[j]:
                        frontier.setdefault(owner, set()).add(j)
        owner = rng.pick(sorted(frontier))
        region[rng.pick(sorted(frontier[owner]))] = owner
    return region


def connected(region: list, n: int, owner: int) -> bool:
    cells = [i for i, o in enumerate(region) if o == owner]
    seen, todo = {cells[0]}, [cells[0]]
    while todo:
        for j in neighbours(todo.pop(), n):
            if region[j] == owner and j not in seen:
                seen.add(j)
                todo.append(j)
    return len(seen) == len(cells)


def repair(n: int, cols: tuple, region: list, rng: Stream) -> bool:
    """Move cells to a bordering region until `cols` is the only answer."""
    cats = {r * n + c for r, c in enumerate(cols)}
    for _ in range(REPAIRS):
        other = next((s for s in solutions(n, region) if s != cols), None)
        if other is None:
            return True
        moves = sorted(
            {(r * n + c, region[j]) for r, c in enumerate(other) if r * n + c not in cats
             for j in neighbours(r * n + c, n) if region[j] != region[r * n + c]}
        )  # fmt: skip
        for i, to in rng.shuffled(moves):
            was = region[i]
            region[i] = to
            if connected(region, n, was):
                break
            region[i] = was
        else:
            return False
    return False


def canonical(region: list) -> list[int]:
    """Region ids 1..n in order of first appearance, so one shape is one list."""
    seen: dict[int, int] = {}
    return [seen.setdefault(o, len(seen) + 1) for o in region]


def board(seed: bytes, n: int) -> tuple[list[int], tuple[int, ...]]:
    """(regions, answer) for (seed, n): the same every time, with one answer."""
    if not MIN_SIZE <= n <= MAX_SIZE:
        raise ValueError(
            f"size {MIN_SIZE} to {MAX_SIZE}: no 2x2 or 3x3 board has a placement"
        )
    rng = Stream(seed)
    for _ in range(DRAWS):
        cols = placement(n, rng)
        region = grow(n, cols, rng)
        if repair(n, cols, region, rng):
            return canonical(region), cols
    raise ValueError(f"no {n}x{n} board with one answer in {DRAWS} draws")


def address(r: int, c: int) -> str:
    return f"{chr(65 + r)}{c + 1}"


def cell(text: str, n: int) -> tuple[int, int]:
    m = CELL.match(text)
    if not m or ord(m.group(1)) - 65 >= n or int(m.group(2)) > n:
        raise ValueError(
            f"{text!r} isn't a cell on this board (A1 to {address(n - 1, n - 1)})"
        )
    return ord(m.group(1)) - 65, int(m.group(2)) - 1


def game(seed: bytes, n: int, moves: list[str]) -> dict:
    """Play `moves` on the board `seed` gives: each verdict, the hearts left, how it ended."""
    regions, answer = board(seed, n)
    placed: dict[tuple[int, int], bool] = {}
    hearts, verdicts, over = HEARTS, [], False
    for m in moves:
        if over:
            raise ValueError(f"{m}: the game is already over; no more moves")
        r, c = cell(m, n)
        if (r, c) in placed:
            raise ValueError(f"{m} already holds a cat")
        right = answer[r] == c
        verdicts.append("right" if right else "wrong")
        if right:
            placed[(r, c)] = True
        else:
            hearts -= 1
        over = hearts == 0 or len(placed) == n
    status = "lost" if hearts == 0 else "won" if len(placed) == n else "open"
    return {"generator": GENERATOR, "size": n, "regions": regions, "moves": list(moves),
            "verdicts": verdicts, "hearts": hearts, "status": status}  # fmt: skip


def picture(n: int, g: dict) -> str:
    """The board, one letter per colour region, a cat where one was rightly placed."""
    cats = {cell(m, n) for m, v in zip(g["moves"], g["verdicts"]) if v == "right"}
    return "\n".join(
        " ".join(
            "@" if (r, c) in cats else chr(96 + g["regions"][r * n + c])
            for c in range(n)
        )
        for r in range(n)
    )


def check(rows: list[dict]) -> tuple[int, str | None]:
    """(how many games hold, why the first that doesn't fails, or None)."""
    held = 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        before = rows[r["n"] - 1]["hash"] if r["n"] else kernel.GENESIS
        if r.get("by") == "tip" and r.get("seed") != before:
            return held, f"row {r['n']}: its seed isn't the hash of the row before it"
        try:
            again = game(seed_of(r["seed"]), r["size"], r["moves"])
        except (ValueError, KeyError, TypeError) as e:
            return held, f"row {r['n']}: {e}"
        for key in ("regions", "verdicts", "hearts", "status"):
            if again[key] != r.get(key):
                return held, f"row {r['n']}: its {key} aren't what its seed gives"
        held += 1
    return held, None


def seed_of(text: str) -> bytes:
    return hashlib.sha256(text.encode()).digest()


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--seed", "--size", "--moves"):
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
    by = "given" if opts.get("--seed") else "tip"
    text = opts.get("--seed") or (rows[-1]["hash"] if rows else kernel.GENESIS)
    try:
        n = int(opts.get("--size", DEFAULT_SIZE))
        moves = [m for m in opts.get("--moves", "").split(",") if m]
        g = game(seed_of(text), n, moves)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    row = kernel.append(
        box,
        opts.get("--now") or kernel.now(),
        KIND,
        who="catgrid",
        seed=text,
        by=by,
        **g,
    )
    print(picture(n, g))
    print(f"\n{g['status']}: {g['hearts']} heart{'s' if g['hearts'] != 1 else ''} left, "
          f"{g['verdicts'].count('right')} of {n} cats placed   (row {row['n']})")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
