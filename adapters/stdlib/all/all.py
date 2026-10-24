"""all.py: every passage that holds your question, ranked, not just the top three.

    python adapters/stdlib/all/all.py --box DIR [--top N] "your words"

The kernel serves at most three passages. This ranks with the kernel's own
`rank`, the same rule, the same order and the same words list, and shows as
many as hold the question (or the first N): its first three are always exactly
the three the kernel would serve.

It prints JSON like the kernel's bite, each passage with its rank:

    {"state": "populated", "count": 14, "served": [{"rank": 1, "where": ..., ...}]}

It only reads. A search through it writes no row to the record: the record is
of what was served and approved, and this serves nothing an approval can cite.

Exit codes, the kernel's: 0 something holds the question; 42 nothing does; 2
refused.

How: the kernel's `rank` stops at its `TOP` (3); its `top` serves more,
for this call only. `kernel.py` itself is never changed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

EVERY = 10**9


def ranked(box: Path, question: str, top: int = EVERY) -> list[dict]:
    """Every passage the kernel's rank would serve, in its order, up to `top`."""
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            raise ValueError(why)
    pile = kernel.chunks(Path(cfg["pile"]))
    return kernel.rank(pile, question, alias, top)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--top"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    top = opts.get("--top", "")
    if not opts.get("--box") or len(args) != 1 or (top and not top.isdigit()):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    try:
        hits = ranked(box, args[0], int(top) if top else EVERY)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    served = [
        {
            "rank": i,
            "id": c["id"],
            "where": f"{c['path']}:{c['line']}",
            "echo": kernel.echo(args[0], c["text"]),
            "text": c["text"],
        }
        for i, c in enumerate(hits, 1)
    ]
    state = "populated" if served else "empty"
    print(
        json.dumps(
            {"state": state, "count": len(served), "served": served}, ensure_ascii=False
        )
    )
    return kernel.ALIVE if served else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
