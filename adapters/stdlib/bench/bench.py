"""bench.py: how fast the kernel answers, on piles of set sizes. Python 3.9+.

    python adapters/stdlib/bench/bench.py run [--sizes 100,1000,5000] [--repeat 5]

The kernel reads the whole folder and ranks it on every question; that is its
cost, and it grows with the folder. `run` builds a pile of each size (in a
scratch folder it makes and throws away), reads and ranks it the way a bite
does, and reports the median time over `--repeat` runs. Run it each release and
watch for a size whose time jumped -- a slowdown the vectors wouldn't catch.

    kernel a1b2c3d4e5f6
       100 passages     0.4 ms
      1000 passages     4.2 ms
      5000 passages    23.1 ms

The pile is synthetic and the times are this machine's, so the numbers are a
trend to compare against the same machine's last run, not a fixed vector; the
kernel's version is printed so a comparison is of like with like.

It builds its piles with tempfile and reads them; it writes no box, no file of
yours, reads no key, and reaches no network. Exit codes, the kernel's: 0 it
ran; 2 refused (a bad command line: no `run`, a size that isn't a positive
number, or a repeat below 1).
"""

from __future__ import annotations

import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

QUESTION = "the roof estimate and the mould report"  # words every passage holds


def a_pile(folder: Path, size: int) -> None:
    """A synthetic pile of `size` passages, one dated line each, all holding
    the question's words so the rank does real work."""
    lines = []
    for i in range(size):
        lines.append(f"2026-03-{i % 28 + 1:02d} note {i}: the roof estimate and "
                     f"the mould report, item {i}")  # fmt: skip
        lines.append("")  # a blank line, so each note is its own passage
    (folder / "pile.md").write_text("\n".join(lines), encoding="utf-8")


def time_one(size: int, repeat: int) -> float:
    """The median seconds to read and rank a pile of `size` passages, the way
    a bite answers one question, over `repeat` runs."""
    runs = []
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        a_pile(folder, size)
        for _ in range(repeat):
            start = time.perf_counter()
            kernel.rank(kernel.chunks(folder), QUESTION)
            runs.append(time.perf_counter() - start)
    return statistics.median(runs)


def parse(argv: list[str]) -> tuple[list[int], int] | None:
    """(sizes, repeat), or None to refuse. `run`, then an optional --sizes (a
    comma list of positive numbers) and --repeat (a number at least 1)."""
    if not argv or argv[0] != "run":
        return None
    sizes, repeat = [100, 1000, 5000], 5
    it = iter(argv[1:])
    for a in it:
        if a == "--sizes":
            parts = [s.strip() for s in next(it, "").split(",")]
            if not all(p.isdigit() and int(p) > 0 for p in parts):
                return None
            sizes = [int(p) for p in parts]
        elif a == "--repeat":
            r = next(it, "")
            if not (r.isdigit() and int(r) >= 1):
                return None
            repeat = int(r)
        else:
            return None
    return sizes, repeat


def main(argv: list[str]) -> int:
    parsed = parse(argv)
    if parsed is None:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    sizes, repeat = parsed
    print(f"kernel {kernel.VERSION[:12]}")
    for size in sizes:
        ms = time_one(size, repeat) * 1000
        print(f"  {size:6} passages  {ms:8.1f} ms  (median of {repeat})")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
