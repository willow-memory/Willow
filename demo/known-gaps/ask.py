"""ask.py: ask one unit's questions of its vulnerable tree, three ways.

    python demo/known-gaps/ask.py --to DIR --ix DIR --questions FILE --out FILE
        --unit NAME [--mode found|before]

DIR (--to) is trees.py's; --ix is where indexes are kept, one folder a git
tree hash. Every run holds each tree to its pinned git tree hash (a missing or
different tree is refused) and builds its index afresh, into a temporary folder
renamed into place: an index already there is never read. The vulnerable tree
(and, for `found`, the fixed one) are indexed with scan.py, then each
question that names the unit's gap (its name starts `KG03 `) is asked of the
vulnerable index and answered three ways: the kernel's rank, BM25, and a
word-match grep baseline. Null questions (`null `) are asked in `before` only.

`found` (the default, phase 1) asks only the passages the fix changed
(`--changed-from`) and ranks all of them: top is the changed set's size, so
the rank of the first hit is known (score.py's first_hit_rank; run.py counts a
passage never returned as last). `before` (phase 2) asks the whole vulnerable
tree, top 10.

Writes FILE, one JSON line an answer and, last, the unit's `stats` line: how
many passages were asked (`changed`; `changed_all` is the set before a
`files_scored` limit, which keeps only passages of those files, by path), how many
of them hit (score.py's rule, by position: `hit_passages`), how many a text
match would count (`hit_by_text`), how many of those are not hits by position
(`text_only`) and lie in no hunk at all (`text_outside_hunks`),
how many lie in a file the fix changed (`file_passages`), and a `random_rate`:
for `found`, the rate at which 3 changed passages drawn at random hit, from
10,000 draws seeded by SEED; for `before`, the exact chance that 10 passages of
the tree drawn at random hold a hit (php2shell's phase4 `chance_one`). Timings
go to stderr, never into FILE, so the same inputs give the same bytes. The stats
line also names what was asked: the pinned tree hashes checked, and a SHA-256
over each index's files (`old_index_sha256`, `new_index_sha256`, and
`limited_index_sha256` for a `files_scored` unit). Writes
only --ix and FILE. Exit 0 asked; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
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


def check_tree(folder: Path, tree: str) -> None:
    """The folder is there, and is the pinned git tree."""
    if not folder.is_dir():
        raise ValueError(f"{folder} is missing: fetch the trees first")
    if trees.make_trees.git_tree(folder) != tree:
        raise ValueError(f"{folder} is not the pinned tree {tree[:12]}")


def index_hash(at: Path) -> str:
    """SHA-256 over an index's files, so a verdict names exactly what was asked."""
    h = hashlib.sha256()
    for name in ("chunks.jsonl", "words.tsv", "index.json"):
        h.update(name.encode() + b"\0" + (at / name).read_bytes() + b"\0")
    return h.hexdigest()


def fresh_index(ix: Path, name: str, folder: Path, tree: str | None = None) -> Path:
    """Index `folder` into ix/name, every run: held to its pinned tree hash
    first (when `tree` is given), built into a temporary folder and renamed into
    place. An index already there is never read, so nothing planted or left by a
    crash can be asked in its stead."""
    if tree is not None:
        check_tree(folder, tree)
    ix.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-ix-", dir=ix))
    scan.build(folder, tmp)
    at = ix / name
    shutil.rmtree(at, ignore_errors=True)
    os.rename(tmp, at)
    return at


def limited_paths(ix: Path, tree: str, files: list) -> tuple:
    """(the cached copy of the scored files, the index made of it)."""
    key = hashlib.sha1("\n".join(sorted(files)).encode()).hexdigest()[:12]
    return ix / f"src-{tree}-{key}", ix / f"{tree}-{key}"


def limited_source_ok(src: Path, old_tree: Path, files: list) -> bool:
    """The cached copy holds exactly the scored files of the tree, byte for byte."""
    want = {f for f in files if (old_tree / f).is_file()}
    have = {p.relative_to(src).as_posix() for p in src.rglob("*") if p.is_file()}
    return have == want and all(
        (src / f).read_bytes() == (old_tree / f).read_bytes() for f in want
    )


def limited_index(ix: Path, old_tree: Path, tree: str, files: list) -> Path:
    """An index of only the scored files of the vulnerable tree, so a limit by
    path leaves no passage of any other file in the pool, even one whose text
    matches a passage of a scored file. Its line numbers are the files' own.

    The tree is held to its pinned git tree hash, and a cached copy is reused
    only when it matches the tree's own files exactly; otherwise it, and the
    index made of it, are rebuilt. The copy is written to a temporary folder
    and renamed into place, so a crash leaves nothing a later run would trust."""
    check_tree(old_tree, tree)
    src, at = limited_paths(ix, tree, files)
    if not (src.is_dir() and limited_source_ok(src, old_tree, files)):
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(at, ignore_errors=True)  # an index of a partial copy is no index
        ix.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=".tmp-src-", dir=ix))
        for f in files:
            if (old_tree / f).is_file():
                (tmp / f).parent.mkdir(parents=True, exist_ok=True)
                (tmp / f).write_bytes((old_tree / f).read_bytes())
        os.rename(tmp, src)
    return fresh_index(ix, at.name, src)  # the copy is checked; its index is always new


def served(passages: list) -> list:
    return [{"path": c["path"], "line": c["line"], "text": c["text"]} for c in passages]


def ask(to: Path, ix: Path, unit: str, pin: dict, qs: list, mode: str) -> list:
    t0 = time.monotonic()
    old_tree, new_tree = pin["vulnerable"]["tree"], pin["fixed"]["tree"]
    old_at = fresh_index(ix, old_tree, to / "trees" / unit / "old", old_tree)
    if mode == "found":
        new_at = fresh_index(ix, new_tree, to / "trees" / unit / "new", new_tree)
    else:  # phase 2 never reads the fixed side, but it must still be the pinned one
        check_tree(to / "trees" / unit / "new", new_tree)
        new_at = None
    print(f"{unit}: indexed in {time.monotonic() - t0:.1f}s", file=sys.stderr)
    t1 = time.monotonic()
    fix = score.changed(
        (to / "fixes" / f"{unit}.diff").read_text(encoding="utf-8"),
        to / "trees" / unit / "old",
    )
    before = {c["id"] for c in scan.passages(new_at)} if mode == "found" else None
    old = scan.Index(old_at)
    changed = [c for c in old.pile if before is None or c["id"] not in before]
    changed_all = len(changed)
    limited_at = None
    if mode == "found" and pin.get("files_scored"):
        # limited to the files the gap scores, by path: the changed set, the
        # ranking and the chance draw only on passages of those files
        limited_at = limited_index(ix, to / "trees" / unit / "old", old_tree,
                                   pin["files_scored"])  # fmt: skip
        old = scan.Index(limited_at)
        changed = [c for c in old.pile if c["id"] not in before]
    top = TOP[mode] or max(len(changed), 1)
    rows = []
    # null questions are asked in phase 2 only (a changed set is too small for
    # a null to fail to hit it by anything but luck)
    names = (pin["gap"], "null") if mode == "before" else (pin["gap"],)
    mine = [(n, q) for n, q in qs if n.split(" ")[0] in names]
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
    by_text = [c for c in changed if score.hit_by_text(c, fix)]
    if mode == "found":
        rng = random.Random(f"{SEED} {unit}")
        k = min(TOP3, len(changed))
        drawn = sum(any(score.hit(c, fix) for c in rng.sample(changed, k))
                    for _ in range(DRAWS)) if k else 0  # fmt: skip
        rate = drawn / DRAWS
    else:
        rate = phase4.chance_one(len(changed), hits, top)
    rows.append({"type": "stats", "unit": unit, "gap": pin["gap"], "mode": mode,
                 "changed": len(changed), "changed_all": changed_all,
                 "questions": len(mine), "unreachable_files": fix["unreachable"],
                 "old_tree": old_tree, "new_tree": new_tree,
                 "old_index_sha256": index_hash(old_at),
                 "new_index_sha256": index_hash(new_at) if new_at else None,
                 "limited_index_sha256": index_hash(limited_at) if limited_at else None,
                 "hit_passages": hits, "hit_by_text": len(by_text),
                 "text_only": sum(not score.hit(c, fix) for c in by_text),
                 "text_outside_hunks": sum(not score.in_a_hunk(c, fix) for c in by_text),
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
