"""ask.py: ask one unit's questions of its vulnerable tree, three ways.

    python demo/known-gaps/ask.py --to DIR --ix DIR --questions FILE --out FILE
        --unit NAME [--mode found|before]

DIR (--to) is trees.py's; --ix is where indexes are kept, one folder a git
tree hash (an index of a tree already made is reused: the index cache). The
vulnerable tree and the fixed one are indexed with scan.py, then each
question that names the unit's gap (its name starts `KG03 `), and each null
question (`null `), is asked of the vulnerable index and answered three ways:
the kernel's rank, BM25, and a word-match grep baseline.

`found` (the default, phase 1) asks only the passages the fix changed
(`--changed-from`) and ranks all of them: top is the changed set's size, so
the rank of the first hit is known (score.py's first_hit_rank; run.py counts a
passage never returned as last). `before` (phase 2) asks the whole vulnerable
tree, top 10.

Writes FILE, one JSON line an answer and, last, the unit's `stats` line: how
many passages were asked (`changed`), how many of them hit (score.py's rule),
how many lie in a file the fix changed (`file_passages`), and a `random_rate`:
for `found`, the rate at which 3 changed passages drawn at random hit, from
10,000 draws seeded by SEED; for `before`, the exact chance that 10 passages of
the tree drawn at random hold a hit (php2shell's phase4 `chance_one`). Timings
go to stderr, never into FILE, so the same inputs give the same bytes. Writes
only --ix and FILE. Exit 0 asked; 2 refused.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

import phase2  # noqa: E402
import phase4  # noqa: E402
import scan  # noqa: E402

score = trees.sibling("score")
SEED = "known-gaps phase 1"
DRAWS = 10_000
TOP = {"found": None, "before": 10}  # found: the whole changed set
TOP3 = 3  # the top-3 hit rate stays in the output beside the rank statistic


def index_of(ix: Path, tree: str, folder: Path) -> Path:
    at = ix / tree
    if not (at / "index.json").exists():
        ix.mkdir(parents=True, exist_ok=True)
        scan.build(folder, at)
    return at


def served(passages: list) -> list:
    return [{"path": c["path"], "line": c["line"], "text": c["text"]} for c in passages]


def ask(to: Path, ix: Path, unit: str, pin: dict, qs: list, mode: str) -> list:
    t0 = time.monotonic()
    old_at = index_of(ix, pin["vulnerable"]["tree"], to / "trees" / unit / "old")
    new_at = index_of(ix, pin["fixed"]["tree"], to / "trees" / unit / "new")
    print(f"{unit}: indexed in {time.monotonic() - t0:.1f}s", file=sys.stderr)
    t1 = time.monotonic()
    fix = score.changed((to / "fixes" / f"{unit}.diff").read_text(encoding="utf-8"))
    before = {c["id"] for c in scan.passages(new_at)} if mode == "found" else None
    old = scan.Index(old_at)
    changed = [c for c in old.pile if before is None or c["id"] not in before]
    top = TOP[mode] or max(len(changed), 1)
    rows = []
    mine = [(n, q) for n, q in qs if n.split(" ")[0] in (pin["gap"], "null")]
    for by in ("kernel", "bm25", "grep"):
        for n, q in mine:
            if by == "kernel":
                got = old.rank(q, {}, top, before)
            elif by == "bm25":
                got = old.bm25(q, top, before)
            else:
                got = phase2.grep(changed, q)[:top]
            rows.append({"type": "answer", "unit": unit, "gap": n.split(" ")[0],
                         "question": n, "ranked_by": by, "mode": mode,
                         "served": served(got)})  # fmt: skip
    hits = sum(score.hit(c, fix) for c in changed)
    if mode == "found":
        rng = random.Random(f"{SEED} {unit}")
        k = min(TOP3, len(changed))
        drawn = sum(any(score.hit(c, fix) for c in rng.sample(changed, k))
                    for _ in range(DRAWS)) if k else 0  # fmt: skip
        rate = drawn / DRAWS
    else:
        rate = phase4.chance_one(len(changed), hits, top)
    rows.append({"type": "stats", "unit": unit, "gap": pin["gap"], "mode": mode,
                 "changed": len(changed), "questions": len(mine),
                 "hit_passages": hits,
                 "file_passages": sum(c["path"] in fix["files"] for c in changed),
                 "random_rate": rate})  # fmt: skip
    print(f"{unit}: asked in {time.monotonic() - t1:.1f}s", file=sys.stderr)
    return rows


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    need = {"--to", "--ix", "--questions", "--out", "--unit"}
    if len(argv) != 2 * len(opts) or not need <= set(opts) <= need | {"--mode"}:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    mode = opts.get("--mode", "found")
    pins = trees.load_pins()
    if mode not in TOP or opts["--unit"] not in pins:
        print(
            "refused: a mode of found or before, and a unit of pins.json",
            file=sys.stderr,
        )
        return 2
    try:
        qs = scan.questions(Path(opts["--questions"]).read_text(encoding="utf-8"))
        rows = ask(Path(opts["--to"]), Path(opts["--ix"]), opts["--unit"],
                   pins[opts["--unit"]], qs, mode)  # fmt: skip
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    with open(opts["--out"], "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
