"""question_profile.py: where a question's time goes, function by function. Python 3.9+.

    python adapters/stdlib/profile/question_profile.py --box DIR [--top N] [--repeat N] "your question"

The kernel answers a question in two steps: read the folder and cut it into
passages (`chunks`), then rank them (`rank`). This runs both on your folder
under cProfile, the way a bite does, and says how long each took and which
functions the time went to:

    kernel be6e99a1952d, release v0.1.0
    folder: 2,112 passages from 395 files; the question has 4 words
    read and cut the folder     0.041 s
    rank                        0.230 s
    own time, the 6 biggest
         ncalls    own s  total s  function
           2507    0.179    0.447  kernel.py:441 newest
         436402    0.160    0.217  kernel.py:415 _digits
        1361729    0.138    0.139  ~:0 <built-in method builtins.len>

`kernel` is the start of the SHA-256 of kernel.py, the same hash every row of
the record carries as its version, and the release is the newest heading in
CHANGELOG.md, so two runs of this on two releases compare. With --repeat N
(1 unless said) both steps run N times and the shortest is reported, which is
the fairest on a busy machine; the function table is from one profiled run.
--top N is how many functions the table lists (10 unless said).

It asks without asking: nothing is written, not even a record row, and the
question's words are not printed or kept; only how many they are.

Exit codes, the kernel's: 0 profiled; 2 refused.
"""

from __future__ import annotations

import cProfile
import pstats
import re
import sys
import time
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
ROOT = STDLIB.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402


def release() -> str:
    """The newest released heading in CHANGELOG.md, else "unreleased"."""
    try:
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        return "unreleased"
    m = re.search(r"^## (v\d+\.\d+\.\d+)\b", text, re.M)
    return m.group(1) if m else "unreleased"


def timed(fn, repeat: int):
    """(the result, the shortest of `repeat` runs in seconds)."""
    best, result = None, None
    for _ in range(repeat):
        t = time.perf_counter()
        result = fn()
        took = time.perf_counter() - t
        best = took if best is None or took < best else best
    return result, best


def table(stats: pstats.Stats, top: int) -> list[tuple[int, float, float, str]]:
    """(calls, own seconds, total seconds, "file:line name") for the biggest own times."""
    rows = []
    for (file, line, name), (_, calls, own, total, _) in stats.stats.items():
        path = Path(file)
        try:
            shown = path.resolve().relative_to(ROOT).as_posix()
        except (ValueError, OSError):
            shown = path.name if file.startswith(("~", "<")) is False else file
        rows.append((calls, own, total, f"{shown}:{line} {name}"))
    return sorted(rows, key=lambda r: (-r[1], r[3]))[:top]


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--top", "--repeat"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    top, repeat = opts.get("--top", "10"), opts.get("--repeat", "1")
    if (
        not opts.get("--box")
        or len(args) != 1
        or args[0].startswith("--")
        or not (top.isdigit() and repeat.isdigit() and int(top) and int(repeat))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    pile_dir, question = Path(cfg["pile"]), args[0]
    pile, read_s = timed(lambda: kernel.chunks(pile_dir), int(repeat))
    _, rank_s = timed(lambda: kernel.rank(pile, question, alias or {}), int(repeat))
    prof = cProfile.Profile()
    prof.runcall(lambda: kernel.rank(kernel.chunks(pile_dir), question, alias or {}))
    files = len({c["path"] for c in pile})
    print(f"kernel {kernel.VERSION[:12]}, release {release()}")
    print(
        f"folder: {len(pile):,} passage{'s' if len(pile) != 1 else ''} from {files:,} file{'s' if files != 1 else ''}; the question has {len(kernel.words(question))} words"
    )
    print(f"{'read and cut the folder':<26}{read_s:7.3f} s")
    print(f"{'rank':<26}{rank_s:7.3f} s")
    print(f"own time, the {top} biggest")
    print(f"{'ncalls':>11}  {'own s':>7}  {'total s':>7}  function")
    for calls, own, total, name in table(pstats.Stats(prof), int(top)):
        print(f"{calls:>11}  {own:7.3f}  {total:7.3f}  {name}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
