"""run.py: score a phase's answers and write its verdicts to a record.

    python demo/known-gaps/run.py found|before --to DIR --answers FILE --box DIR --out FILE

ask.py's answers (the lines of every unit's file, joined), scored by score.py.
Per group, strong (the gap's text was written before the fix: a gap record or
an audit finding) and weaker (only the fixer's own commit message), apart.

`found` is phase 1: each question asked of the passages the fix changed, all of
them ranked. A (question, unit) pair's statistic is the rank of the first
passage that hits; a passage the ranker did not return counts as last (rank n),
which is conservative. The null is a uniform random ordering of the same set,
so a pair's chance of each first-hit rank is exact (n passages, h of them hits:
C(n-r, h-1) / C(n, h)). The group statistic is the sum of 1/rank over its
pairs; its p-value is Monte Carlo over DRAWS random orderings seeded by SEED,
both recorded in the output. The top-3 hit rate and each unit's random-draw
chance are reported beside it.

| Rule | Passes when |
|---|---|
| rank, bm25, GROUP | the group's sum of 1/rank beats random orderings, one-sided p < 0.01 |
| null questions hit nothing | at least one null question was asked, and none of its top 3, ranked by anything, hit |

`before` is phase 2, the main judged test: each question asked of the whole
vulnerable tree, top 10, scored at line level (a passage holding a counted
line) and file level (any passage of a scored file). The chance is exact
(php2shell's phase4 `chance_one` per pair, `poisson_binomial_tail` over a
group).

| Rule | Passes when |
|---|---|
| line level above chance, bm25, GROUP | questions with a line hit in the top 10 beat chance, one-sided p < 0.01 |

The file level, and the kernel's and grep's results, are reported, never gates.
A unit whose fix has files_scored counts only passages of those files.
Every later phase is not built: exit 2.

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
import random
import sys
from itertools import accumulate
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

import kernel  # noqa: E402
import phase2  # noqa: E402
import phase4  # noqa: E402

score = trees.sibling("score")
HERE = trees.HERE
ROOT = trees.ROOT
NOW = "2026-10-28T00:00:00Z"
SEED = "known-gaps phase 1 rank"
DRAWS = 100_000
KS = (3, 10)
BYS = ("kernel", "bm25", "grep")
GROUPS = ("strong", "weaker")
STRONG = ("gap_record", "audit_finding")
TOOLS = ("kernel.py", "adapters/stdlib/scan/scan.py", "adapters/stdlib/ci/whose.py",
         "demo/php2shell/phase3.py", "demo/php2shell/phase4.py",
         "demo/known-gaps/trees.py", "demo/known-gaps/ask.py",
         "demo/known-gaps/score.py", "demo/known-gaps/run.py")  # fmt: skip


def rank_pmf(n: int, h: int) -> list:
    """P(the first hit is at rank r), r = 1..n, for h hits among n passages in
    a uniformly random order. With no hit the pair counts as last."""
    if h <= 0:
        return [0.0] * (n - 1) + [1.0]
    return [comb(n - r, h - 1) / comb(n, h) if n - r >= h - 1 else 0.0
            for r in range(1, n + 1)]  # fmt: skip


def first_rank(row: dict, n: int) -> int:
    """The rank of the first hit; a passage never returned counts as last."""
    return row["first_hit_rank"] or n


def rank_statistic(pairs: list) -> float:
    """pairs: [(first-hit rank, n)]; the sum of 1/rank."""
    return sum(1 / r for r, _ in pairs)


def rank_p(sizes: list, observed: float, rng: random.Random) -> tuple:
    """(expected statistic under random orderings, one-sided Monte Carlo p).
    sizes: [(n, h)] a pair each. p = (1 + draws at least as good) / (1 + DRAWS)."""
    totals = [0.0] * DRAWS
    expected = 0.0
    for n, h in sizes:
        pmf = rank_pmf(n, h)
        expected += sum(p / r for r, p in enumerate(pmf, 1))
        inv = [0.0] + [1 / r for r in range(1, n + 1)]
        draws = rng.choices(range(1, n + 1), cum_weights=list(accumulate(pmf)), k=DRAWS)
        for i, r in enumerate(draws):
            totals[i] += inv[r]
    as_good = sum(t >= observed - 1e-9 for t in totals)
    return expected, (1 + as_good) / (1 + DRAWS)


def judge(rows: list, scored: list, group_of: dict) -> dict:
    """Phase 1."""
    stats = {r["unit"]: r for r in rows if r.get("type") == "stats"}
    top3: dict = {}
    rank: dict = {}
    for by in BYS:
        for group in GROUPS:
            mine = [r for r in scored if r["ranked_by"] == by
                    and group_of.get(r["gap"]) == group]  # fmt: skip
            n, k = len(mine), sum("hit" in r["served"][:3] for r in mine)
            rate = (
                (sum(stats[r["unit"]]["random_rate"] for r in mine) / n) if n else 1.0
            )
            top3[f"{by}, {group}"] = {"hits": k, "of": n, "random": rate,
                                      "p": phase2.binomial_tail(k, n, rate)}  # fmt: skip
            sizes = [(stats[r["unit"]]["changed"], stats[r["unit"]]["hit_passages"])
                     for r in mine]  # fmt: skip
            observed = rank_statistic([(first_rank(r, s[0]), s[0])
                                       for r, s in zip(mine, sizes)])  # fmt: skip
            expected, p = (rank_p(sizes, observed, random.Random(f"{SEED} {by} {group}"))
                           if mine else (0.0, 1.0))  # fmt: skip
            rank[f"{by}, {group}"] = {"pairs": n, "observed": observed,
                                      "expected": expected, "p": p}  # fmt: skip
    null = [r for r in scored if r["gap"] == "null"]
    passes = {
        **{f"rank, bm25, {g}": rank[f"bm25, {g}"]["pairs"] > 0
           and rank[f"bm25, {g}"]["p"] < 0.01 for g in GROUPS},
        "null questions hit nothing": bool(null)
        and not any("hit" in r["served"][:3] for r in null),
    }  # fmt: skip
    return {"seed": SEED, "draws": DRAWS, "rank": rank, "top3_hit_rate": top3,
            "null_answers": len(null), "passes": passes}  # fmt: skip


def judge_before(rows: list, scored: list, group_of: dict) -> dict:
    """Phase 2."""
    stats = {r["unit"]: r for r in rows if r.get("type") == "stats"}
    table: dict = {}
    passes: dict = {}
    for by in BYS:
        for group in GROUPS:
            mine = [r for r in scored if r["ranked_by"] == by
                    and group_of.get(r["gap"]) == group]  # fmt: skip
            line = file = 0
            ps_line, ps_file = [], []
            for r in mine:
                s = stats[r["unit"]]
                served = [{"id": c} for c in r["served"]]
                line += phase4.recall_at(served, {"hit"}, KS)[10]
                file += phase4.recall_at(served, {"hit", "file"}, KS)[10]
                ps_line.append(phase4.chance_one(s["changed"], s["hit_passages"], 10))
                ps_file.append(phase4.chance_one(s["changed"], s["file_passages"], 10))
            table[f"{by}, {group}"] = {
                "of": len(mine),
                "line_hits@10": line, "line_expected": sum(ps_line),
                "line_p": phase4.poisson_binomial_tail(ps_line, line) if line else 1.0,
                "file_hits@10": file, "file_expected": sum(ps_file),
                "file_p": phase4.poisson_binomial_tail(ps_file, file) if file else 1.0,
            }  # fmt: skip
            if by == "bm25":
                passes[f"line level above chance, bm25, {group}"] = (
                    bool(mine) and table[f"{by}, {group}"]["line_p"] < 0.01
                )
    return {"table": table, "passes": passes}


PHASES = {"found": ("phase1", judge), "before": ("phase2", judge_before)}


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    if (cmd not in PHASES or set(opts) != {"--to", "--answers", "--box", "--out"}
            or len(argv) != 9):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    prefix, judge_it = PHASES[cmd]
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
    result = judge_it(rows, scored, group_of)
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
        kernel.append(box, NOW, "verdict", who="known-gaps", gate=f"{prefix}:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=sha, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
