"""phase1.py: the blind questions, under both rules, ranked two ways.

    python demo/php2shell/phase1.py --data DIR --ix DIR --box DIR --out FILE

The same arguments as phase2.py. Frozen, with the blind question sets, the
second rule (score2.py) and scan's BM25, before it ran (FROZEN.json).

Each set (blind-a, blind-b, blind-c, and the author's for comparison) is
asked of each fix's pair, the vulnerable release `--changed-from` the fixed
one, top 3, ranked by the kernel and by BM25 (scan.py's `--rank bm25`), and
scored by score.py (rule 1) and score2.py (rule 2). The random rate under
each rule is from 10,000 draws of 3 changed passages a fix, as in phase 2.

The pass rules, set before any blind question was asked:

| Rule | Passes when |
|---|---|
| blind like author | the three blind sets' core rate, pooled, ranked by the kernel under rule 1, is at least half the author's |
| kernel above chance, rule N | the blind sets' pooled core answers, ranked by the kernel, beat the random core rate under rule N: one-sided binomial p < 0.01 |
| bm25 above chance, rule N | the same, ranked by BM25 |

Exit 0 when every rule passes, 42 when one fails, 2 for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import phase2  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

SEED = "php2shell phase 1"
DRAWS = 10_000
TOP = 3
SETS = ("blind-a", "blind-b", "blind-c", "author")
BLIND = SETS[:3]
RULES = {"rule 1": score.score, "rule 2": score2.score_answers}
NOW = "2026-10-24T00:00:00Z"


def run(data: Path, ix: Path, out: Path) -> dict:
    sets = {
        s: scan.questions((HERE / "questions" / f"{s}.txt").read_text(encoding="utf-8"))
        for s in SETS
    }
    fixes = data / "fixes"
    rows: list[dict] = []
    drawn: dict[str, list[dict]] = {}
    for branch, fix in score.PINS["fixes"].items():
        vuln, fixed = fix["vulnerable"], fix["fixed"]
        before = {c["id"] for c in scan.passages(ix / fixed)}
        old = scan.Index(ix / vuln)
        changed = [c for c in old.pile if c["id"] not in before]
        for s, qs in sets.items():
            for by in ("kernel", "bm25"):
                got = [
                    phase2.answers(vuln, n, old.rank(q, {}, TOP, before) if by == "kernel"
                                   else old.bm25(q, TOP, before))
                    for n, q in qs
                ]  # fmt: skip
                for rule, scorer in RULES.items():
                    for r in scorer(got, fixes):
                        rows.append({**r, "set": s, "ranked_by": by, "rule": rule})
        rng = random.Random(f"{SEED} {branch}")
        drawn[branch] = [
            phase2.answers(vuln, f"draw{i}", rng.sample(changed, TOP))
            for i in range(DRAWS)
        ]
        old = changed = None  # one whole index in memory at a time
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    def core(sel) -> tuple[int, int]:
        got = [r for r in rows if sel(r)]
        return sum(r["best"] == "core" for r in got), len(got)

    random_rate = {}
    for rule, scorer in RULES.items():
        scored = [r for d in drawn.values() for r in scorer(d, fixes)]
        random_rate[rule] = sum(r["best"] == "core" for r in scored) / len(scored)
    table = {
        f"{s}, {by}, {rule}": dict(zip(("core", "answers"), core(
            lambda r, s=s, by=by, rule=rule: (r["set"], r["ranked_by"], r["rule"]) == (s, by, rule))))
        for s in SETS for by in ("kernel", "bm25") for rule in RULES
    }  # fmt: skip
    blind = {
        (by, rule): core(lambda r, by=by, rule=rule: r["set"] in BLIND
                         and (r["ranked_by"], r["rule"]) == (by, rule))
        for by in ("kernel", "bm25") for rule in RULES
    }  # fmt: skip
    author = core(
        lambda r: (
            (r["set"], r["ranked_by"], r["rule"]) == ("author", "kernel", "rule 1")
        )
    )
    k, n = blind[("kernel", "rule 1")]
    p = {f"{by}, {rule}": phase2.binomial_tail(*blind[(by, rule)], random_rate[rule])
         for by in ("kernel", "bm25") for rule in RULES}  # fmt: skip
    passes = {
        "blind like author": k / n >= 0.5 * author[0] / author[1],
        **{f"{by} above chance, {rule}": p[f"{by}, {rule}"] < 0.01
           for by in ("kernel", "bm25") for rule in RULES},
    }  # fmt: skip
    return {
        "table": table,
        "random_core_rate": random_rate,
        "blind_p": p,
        "passes": passes,
    }


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 8 or set(opts) != {"--data", "--ix", "--box", "--out"}:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box, out = Path(opts["--box"]), Path(opts["--out"])
    if not (box / "record.jsonl").exists():
        key = box.parent / (box.name + ".key")
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            made = kernel.init(box, HERE, key, NOW)
        if made != kernel.ALIVE:
            print(f"refused: couldn't start a record at {box}", file=sys.stderr)
            return 2
    result = run(Path(opts["--data"]), Path(opts["--ix"]), out)
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "kernel.py", "adapters/stdlib/scan/scan.py", "demo/php2shell/score.py",
        "demo/php2shell/score2.py", "demo/php2shell/phase1.py")}  # fmt: skip
    answers_sha = hashlib.sha256(out.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(box, NOW, "verdict", who="php2shell", gate=f"phase1:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=answers_sha, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
