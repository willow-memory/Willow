"""phase2.py: the null tests. Could anything have landed on the fix?

    python demo/php2shell/phase2.py --data DIR --ix DIR --box DIR --out FILE

DIR for --data is make_trees.py's `--to`; --ix holds one scan index per
release, named by its version (8.5.11, ...); --box is a kernel record,
outside the repo, that each test's result is written to as a row; --out
gets every scored answer, one JSON line each. Frozen, with its seed and its
pass rules, before it ran (FROZEN.json).

Each test is asked of each fix's pair: the vulnerable release, `--changed-from`
the fixed one (the passages the fix replaced), scored by score.py on the old
side. Asked of the fixed release against the vulnerable one, the kernel is
scored too, for the record; nothing passes or fails on that.

| Test | What answers each question | Passes when |
|---|---|---|
| kernel | the kernel's rank, top 3: the result under test | the baseline for the rest |
| random | 3 passages drawn from the changed set, 10,000 times a fix | the kernel's core answers are above the draws' rate, one-sided binomial p < 0.01 |
| null | the kernel, on questions/null.txt | its core rate is below the kernel's on the author's questions |
| wrong pair | the kernel, on a pair the fix isn't in: 8.5.10 to 8.5.11, 8.4.25 to 8.4.26 | no core answer |
| diff size | the first changed passage of each of the 3 files with most changed passages | the kernel's core answers are at least as many |
| grep | the 3 changed passages holding most of the question's words, as written | the kernel's core answers are at least as many |
| bm25 | BM25 (k1 1.2, b 0.75) over the changed passages' words | the kernel's core answers are at least as many |

grep and bm25 split words the kernel's way and drop the kernel's common
words, so the only difference is the ranking. Ties keep the kernel's order.

Exit 0 when every test passes, 42 when one fails (a finding, not a bug), 2
for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402

SEED = "php2shell phase 2"
DRAWS = 10_000
TOP = 3
WRONG = [("8.5.10", "8.5.11"), ("8.4.25", "8.4.26")]
NOW = "2026-10-24T00:00:00Z"


def want(q: str) -> list[str]:
    return [w for w in dict.fromkeys(kernel.words(q)) if w not in kernel.FUNCTION]


def grep(changed: list[dict], q: str) -> list[dict]:
    ws = set(want(q))
    hits = [(len(ws & set(kernel.words(c["text"]))), i) for i, c in enumerate(changed)]
    return [changed[i] for n, i in sorted((-n, i) for n, i in hits if n)][:TOP]


def bm25(changed: list[dict], q: str, k1: float = 1.2, b: float = 0.75) -> list[dict]:
    docs = [kernel.words(c["text"]) for c in changed]
    avg = sum(map(len, docs)) / max(len(docs), 1)
    df: dict[str, int] = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    n = len(docs)
    scored = []
    for i, d in enumerate(docs):
        s = 0.0
        for w in want(q):
            f = d.count(w)
            if f:
                idf = math.log((n - df[w] + 0.5) / (df[w] + 0.5) + 1)
                s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(d) / avg))
        if s > 0:
            scored.append((-s, i))
    return [changed[i] for _, i in sorted(scored)][:TOP]


def diff_size(changed: list[dict]) -> list[dict]:
    per: dict[str, list[dict]] = {}
    for c in changed:
        per.setdefault(c["path"], []).append(c)
    biggest = sorted(per, key=lambda p: (-len(per[p]), p))[:TOP]
    return [per[p][0] for p in biggest]


def answers(index: str, question: str, served: list[dict]) -> dict:
    where = [{"where": f"{c['path']}:{c['line']}", "text": c["text"]} for c in served]
    return {"index": index, "question": question, "served": where}


def tally(rows: list[dict]) -> dict:
    return {k: sum(r["best"] == k for r in rows) for k in score.ORDER} | {
        "answers": len(rows)
    }


def binomial_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def run(data: Path, ix: Path, out: Path) -> tuple[dict, list[dict]]:
    qs = scan.questions((HERE / "questions" / "author.txt").read_text(encoding="utf-8"))
    nulls = scan.questions(
        (HERE / "questions" / "null.txt").read_text(encoding="utf-8")
    )
    fixes = data / "fixes"
    rows: list[dict] = []
    tests: dict[str, list[dict]] = {}
    draws: dict[str, dict] = {}

    def scored(test: str, got: list[dict]) -> None:
        for r in score.score(got, fixes):
            r["test"] = test
            rows.append(r)
            tests.setdefault(test, []).append(r)

    def ask(idx: scan.Index, qset: list, lacked: set) -> list[dict]:
        return [answers(idx.name, n, idx.rank(q, {}, TOP, lacked)) for n, q in qset]

    for branch, fix in score.PINS["fixes"].items():
        vuln, fixed = fix["vulnerable"], fix["fixed"]
        before = {c["id"] for c in scan.passages(ix / fixed)}
        old = scan.Index(ix / vuln)
        changed = [c for c in old.pile if c["id"] not in before]
        scored("kernel", ask(old, qs, before))
        scored("null", ask(old, nulls, before))
        scored("diff size", [answers(vuln, n, diff_size(changed)) for n, _ in qs])
        scored("grep", [answers(vuln, n, grep(changed, q)) for n, q in qs])
        scored("bm25", [answers(vuln, n, bm25(changed, q)) for n, q in qs])
        rng = random.Random(f"{SEED} {branch}")
        drawn = [
            answers(vuln, f"draw{i}", rng.sample(changed, TOP)) for i in range(DRAWS)
        ]
        draws[branch] = {"changed": len(changed), **tally(score.score(drawn, fixes))}
        after = {c["id"] for c in old.pile}
        old = changed = None  # one whole index in memory at a time
        scored("kernel, the fix's side", ask(scan.Index(ix / fixed), qs, after))
    for a, b in WRONG:
        later = {c["id"] for c in scan.passages(ix / b)}
        scored("wrong pair", ask(scan.Index(ix / a), qs, later))

    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    summary = {t: tally(rs) for t, rs in tests.items()}
    p_core = sum(d["core"] for d in draws.values()) / sum(
        d["answers"] for d in draws.values()
    )
    k = summary["kernel"]
    verdicts = {
        "random": binomial_tail(k["core"], k["answers"], p_core) < 0.01,
        "null": summary["null"]["core"] / summary["null"]["answers"]
        < k["core"] / k["answers"],
        "wrong pair": summary["wrong pair"]["core"] == 0,
        **{b: k["core"] >= summary[b]["core"] for b in ("diff size", "grep", "bm25")},
    }
    return {
        "summary": summary,
        "draws": draws,
        "random_core_rate": p_core,
        "kernel_vs_random_p": binomial_tail(k["core"], k["answers"], p_core),
        "passes": verdicts,
    }, rows


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
    result, _ = run(Path(opts["--data"]), Path(opts["--ix"]), out)
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "kernel.py", "adapters/stdlib/scan/scan.py", "demo/php2shell/score.py",
        "demo/php2shell/phase2.py")}  # fmt: skip
    answers_sha = hashlib.sha256(out.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(box, NOW, "verdict", who="php2shell", gate=f"phase2:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=answers_sha, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
