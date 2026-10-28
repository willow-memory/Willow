"""pile_sweep.py: the passage size measured, not guessed. Your box's own
questions asked at several sizes, and the size that finds the most of their
answers named. Python 3.9+.

    python adapters/stdlib/pile-sweep/pile_sweep.py --box DIR --questions FILE
        [--sizes 200,350,500,800,1200]

The kernel cuts a folder into passages of at most `MAX_CHUNK` characters
(500). Smaller passages answer more exactly; larger ones hold more of a
question's words. Which is better for your folder is a question your own
answers can settle.

The answers are pile-gold's: the passages your sealed answers cite, for the
questions in FILE that have one (read as pile-gold and scan read them). A
passage's id changes with its size, so each is taken where it stands now, as
its file and its lines, and at each size an answer is found when a passage
in the top five overlaps those lines. Each size is asked by the kernel's own
rank and by pile-rank:

     size  kernel              pile-rank
      200  2 of 4, 21 lines    3 of 4, 24 lines
      500  3 of 4, 38 lines    3 of 4, 41 lines    <- the kernel's
      800  3 of 4, 55 lines    4 of 4, 60 lines
    best for the kernel: 500; for pile-rank: 800

"lines" is how many lines the top five held, over every question: a larger
passage overlaps more, and costs more to read. The best size finds the most;
among equals, the fewest lines; then the kernel's own.

Each size is read with the kernel's `MAX_CHUNK` set to it, in this process
only, and put back after; kernel.py is never changed. It writes nothing:
not the record, not the kernel. Seals are read through the kernel, never the
key. Exit codes, the kernel's: 0 swept; 42 no question in FILE has a sealed
answer still in the folder; 2 refused (a bad command line, not a box, a
broken record, or a FILE that can't be read).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-gold"))
sys.path.insert(0, str(HERE.parent / "pile-rank"))
sys.path.insert(0, str(HERE.parent / "scan"))
import kernel  # noqa: E402
import pile_gold  # noqa: E402
import pile_rank  # noqa: E402
import scan  # noqa: E402

SIZES = (200, 350, 500, 800, 1200)
SMALLEST = 50  # characters: a passage smaller than this is a few words


def span(c: dict) -> tuple[str, int, int]:
    """A passage's file and its first and last lines: a passage is one run of
    lines with no blank one inside."""
    return c["path"], c["line"], c["line"] + len(c["text"].splitlines()) - 1


def overlaps(a: tuple[str, int, int], b: tuple[str, int, int]) -> bool:
    return a[0] == b[0] and a[1] <= b[2] and b[1] <= a[2]


def at_size(folder: Path, size: int) -> list[dict]:
    """The folder's passages as the kernel reads them with `MAX_CHUNK` = size,
    the kernel's own value put back after."""
    was = kernel.MAX_CHUNK
    kernel.MAX_CHUNK = size
    try:
        return kernel.chunks(folder)
    finally:
        kernel.MAX_CHUNK = was


def sweep(
    folder: Path, asked: list[tuple[str, list]], sizes: list[int], alias: dict
) -> dict[int, dict[str, tuple[int, int]]]:
    """{size: {rank: (answers found, lines read)}} over the questions, each
    with its answers' spans."""
    out = {}
    for size in sizes:
        pile = at_size(folder, size)
        ranker = pile_rank.Ranker(pile)
        got = {"kernel": [0, 0], "pile-rank": [0, 0]}
        for q, spans in asked:
            served = {
                "kernel": kernel.rank(pile, q, alias, top=pile_gold.AT),
                "pile-rank": [c for c, *_ in ranker.rank(q, pile_gold.AT)],
            }
            for k, cs in served.items():
                held = [span(c) for c in cs]
                got[k][0] += sum(any(overlaps(s, h) for h in held) for s in spans)
                got[k][1] += sum(h[2] - h[1] + 1 for h in held)
        out[size] = {k: (f, n) for k, (f, n) in got.items()}
    return out


def best(table: dict[int, dict[str, tuple[int, int]]], k: str) -> int:
    """The size that finds the most for rank `k`; then the fewest lines; then
    the kernel's own size; then the smaller."""
    return min(
        table,
        key=lambda s: (-table[s][k][0], table[s][k][1], s != kernel.MAX_CHUNK, s),
    )


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--box", "--questions", "--sizes"):
            opts[a] = next(it, "")
        else:
            return usage()
    if not opts.get("--box") or not opts.get("--questions"):
        return usage()
    try:
        sizes = sorted({int(x) for x in opts.get("--sizes", "").split(",")}
                       if "--sizes" in opts else SIZES)  # fmt: skip
    except ValueError:
        return usage()
    if not sizes or sizes[0] < SMALLEST or sizes[-1] > kernel.MAX_FILE:
        return usage()
    box = Path(opts["--box"])
    if not (box / "record.jsonl").is_file():
        print(f"refused: {opts['--box']} is not a box", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    try:
        qs = scan.questions(Path(opts["--questions"]).read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: the questions can't be read: {type(e).__name__}",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    folder = Path(cfg["pile"])
    marked = pile_gold.gold(box, rows)
    where = {c["id"]: span(c) for c in kernel.chunks(folder)}
    asked = []
    for _, q in qs:
        spans = sorted(
            where[i] for i in marked.get(kernel.bite_key(q), ()) if i in where
        )
        if spans:
            asked.append((q, spans))
    if not asked:
        print(f"nothing to sweep: none of {len(qs)} questions has a sealed answer "
              "still in the folder")  # fmt: skip
        return kernel.ESCALATE
    table = sweep(folder, asked, sizes, alias)
    of = sum(len(s) for _, s in asked)
    print(f"{len(asked)} questions, {of} approved passages, top {pile_gold.AT}")
    print(f"{'size':>5}  {'kernel':<20}pile-rank")
    for size, got in table.items():
        cells = "".join(f"{f'{f} of {of}, {n} lines':<20}" for f, n in got.values())
        mark = "  <- the kernel's" if size == kernel.MAX_CHUNK else ""
        print(f"{size:>5}  {cells}{mark}".rstrip())
    print(f"best for the kernel: {best(table, 'kernel')}; "
          f"for pile-rank: {best(table, 'pile-rank')}")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
