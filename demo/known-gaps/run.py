"""run.py: score a phase's answers and write its verdicts to a record.

    python demo/known-gaps/run.py found --to DIR --answers FILE --box DIR --out FILE

`found` is phase 1: ask.py's answers (the lines of every unit's file,
joined), asked of the passages each fix changed, top 3, scored by score.py.
Per group, strong (the gap's text was written before the fix: a gap record or
an audit finding) and weaker (only the fixer's own commit message), apart:

| Rule | Passes when |
|---|---|
| above chance, bm25, GROUP | the group's pooled hits beat its pooled random rate, one-sided binomial p < 0.01 |
| null questions hit nothing | at least one null question was asked, and none of its answers, ranked by anything, hit |

The kernel's and the grep baseline's rates are reported beside, never gates.
`before` (phase 2) and every later phase are not in bite 2: exit 2.

--out gets the scored answers, one JSON line each (origin.py reads it). --box
is a record (made if there is none; its key beside it); each rule is a
`verdict` row with the SHA-256 of --answers and of the tools. NOW is fixed, so
the same answers give the same rows. Exit 0 every rule passes, 42 one fails,
2 for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

import kernel  # noqa: E402
import phase2  # noqa: E402

score = trees.sibling("score")
HERE = trees.HERE
ROOT = trees.ROOT
NOW = "2026-10-28T00:00:00Z"
BYS = ("kernel", "bm25", "grep")
STRONG = ("gap_record", "audit_finding")
TOOLS = ("kernel.py", "adapters/stdlib/scan/scan.py", "adapters/stdlib/ci/whose.py",
         "demo/known-gaps/trees.py", "demo/known-gaps/ask.py",
         "demo/known-gaps/score.py", "demo/known-gaps/run.py")  # fmt: skip


def judge(rows: list, scored: list, group_of: dict) -> dict:
    stats = {r["unit"]: r for r in rows if r.get("type") == "stats"}
    groups: dict = {}
    for by in BYS:
        for group in ("strong", "weaker"):
            mine = [r for r in scored if r["ranked_by"] == by
                    and group_of.get(r["gap"]) == group]  # fmt: skip
            n, k = len(mine), sum(r["best"] == "hit" for r in mine)
            rate = (
                (sum(stats[r["unit"]]["random_rate"] for r in mine) / n) if n else 1.0
            )
            groups[f"{by}, {group}"] = {"hits": k, "of": n, "random": rate,
                                        "p": phase2.binomial_tail(k, n, rate)}  # fmt: skip
    null = [r for r in scored if r["gap"] == "null"]
    passes = {
        **{f"above chance, bm25, {g}": groups[f"bm25, {g}"]["of"] > 0
           and groups[f"bm25, {g}"]["p"] < 0.01 for g in ("strong", "weaker")},
        "null questions hit nothing": bool(null) and not any(r["best"] == "hit" for r in null),
    }  # fmt: skip
    return {"groups": groups, "null_answers": len(null), "passes": passes}


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    if cmd == "before":
        print("refused: before (phase 2) is not in bite 2", file=sys.stderr)
        return 2
    if (cmd != "found" or set(opts) != {"--to", "--answers", "--box", "--out"}
            or len(argv) != 9):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box, answers, out = (
        Path(opts["--box"]),
        Path(opts["--answers"]),
        Path(opts["--out"]),
    )
    try:
        rows = [json.loads(x) for x in answers.read_text(encoding="utf-8").splitlines()]
        scored = score.score([r for r in rows if r.get("type") == "answer"],
                             Path(opts["--to"]) / "fixes")  # fmt: skip
    except (OSError, ValueError, KeyError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    group_of = {g: "strong" if v["source_kind"] in STRONG else "weaker"
                for g, v in trees.load_gaps().items()}  # fmt: skip
    result = judge(rows, scored, group_of)
    out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in scored),
                   encoding="utf-8")  # fmt: skip
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            made = kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
        if made != kernel.ALIVE:
            print(f"refused: couldn't start a record at {box}", file=sys.stderr)
            return 2
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in TOOLS}
    sha = hashlib.sha256(answers.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(box, NOW, "verdict", who="known-gaps", gate=f"phase1:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=sha, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
