"""phase4.py: the whole vulnerable release, with no later release to compare.

    python demo/php2shell/phase4.py --data DIR --ix DIR --p3 DIR --p3ix DIR
        --box DIR --out FILE

--data and --ix as in phase2.py; --p3 and --p3ix as phase3.py's --to and
--ix. Frozen, with its measures and pass rules, before it ran (FROZEN.json).

With no fixed release yet, does asking the whole vulnerable release point at
the code that was later changed? Each question is ranked over the whole
release, top 50, three ways: the kernel's rank, BM25 (scan's), and grep
(most of the question's words as written, ties in the index's order).

Two levels. A line hit is a passage holding a changed line by rule 2
(score2.py): for PHP2Shell in a core file (score.py), for phase 3 in any
file its rule counts (phase3.py). A file hit is any passage of such a file
the fix changed. The measure is recall at k: the share of questions with a
hit in the top k, for k in 3, 10, 50.

Random, computed not drawn: a release of N passages holds H that hit, so k
ranked at random hold one with probability 1 - C(N-H, k) / C(N, k). Over
questions on different releases that is a sum of unequal probabilities
(a Poisson binomial), summed exactly.

Pass rule: for the kernel and for BM25, each group's questions with a line
hit in the top 10 beat random, one-sided p < 0.01. Groups: PHP2Shell's
blind sets (96 = 24 questions x 4 releases), phase 3's two newer CVEs (16),
phase 3's five older CVEs (40). The author's set, grep, and the file level
are reported, not judged.

Exit 0 when every rule passes, 42 when one fails, 2 for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import phase3  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

NOW = "2026-10-24T00:00:00Z"
KS = (3, 10, 50)
TOP = 50


def grep_rank(ix: scan.Index, question: str, top: int) -> list[dict]:
    """The passages holding most of the question's words as written, the
    kernel's split with its common words dropped; ties keep the index's
    order."""
    ws = set(w for w in kernel.words(question) if w not in kernel.FUNCTION)
    got = []
    for i, c in enumerate(ix.pile):
        held = len(ws & set(kernel.words(c["text"])))
        if held:
            got.append((-held, i))
    return [ix.pile[i] for _, i in sorted(got)][:top]


def ranked(ix: scan.Index, question: str, by: str, top: int) -> list[dict]:
    if by == "kernel":
        return ix.rank(question, {}, top)
    if by == "bm25":
        return ix.bm25(question, top)
    return grep_rank(ix, question, top)


def hit_sets(ix: scan.Index, fix: dict, core) -> tuple[set, set, int]:
    """(line-hit ids, file-hit ids, N) for one release: a line hit holds a
    changed line of the fix in a counted file (for PHP2Shell, in `core`); a
    file hit is any passage of such a file. N is the release's passages."""
    changed_files = set(fix["files"]) if core is None else (set(fix["files"]) & core)
    changed_lines = {f: fix["old"][f] for f in fix["old"] if core is None or f in core}
    line_ids, file_ids = set(), set()
    for c in ix.pile:
        if c["path"] in changed_files:
            file_ids.add(c["id"])
            if {x.strip() for x in c["text"].splitlines()} & changed_lines.get(
                c["path"], set()
            ):
                line_ids.add(c["id"])
    return line_ids, file_ids, len(ix.pile)


def recall_at(served: list[dict], hits: set, ks) -> dict:
    """For each k, whether a hit id is in the first k served."""
    firsts = [i for i, c in enumerate(served, 1) if c["id"] in hits]
    first = firsts[0] if firsts else None
    return {k: bool(first and first <= k) for k in ks}


def chance_one(n: int, h: int, k: int) -> float:
    """P(at least one of h hitting passages in k ranked at random from n)."""
    if h <= 0 or k <= 0:
        return 0.0
    if h > n - k:
        return 1.0
    return 1.0 - comb(n - h, k) / comb(n, k)


def poisson_binomial_tail(ps: list[float], k: int) -> float:
    """P(at least k successes) over independent trials of probabilities ps."""
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for i, d in enumerate(dist):
            nxt[i] += d * (1 - p)
            nxt[i + 1] += d * p
        dist = nxt
    return sum(dist[k:])


def jobs(data: Path, ix: Path, p3: Path, p3ix: Path):
    """(label, question-id, question, index path, fix diff path, core) per ask."""
    out = []
    auth = scan.questions(
        (HERE / "questions" / "author.txt").read_text(encoding="utf-8")
    )
    blind = []
    for s in ("blind-a", "blind-b", "blind-c"):
        blind += scan.questions(
            (HERE / "questions" / f"{s}.txt").read_text(encoding="utf-8")
        )
    for branch, fix in score.PINS["fixes"].items():
        vuln = fix["vulnerable"]
        d = data / "fixes" / f"{branch}.diff"
        for group, qs in (("author", auth), ("blind", blind)):
            for n, q in qs:
                out.append((group, f"{vuln} {n}", q, ix / vuln, d, "php2shell"))
    for cve, pin in phase3.PINS.items():
        group = "p3-new" if not pin["known_to_models"] else "p3-old"
        d = p3 / "fixes" / f"{cve}.diff"
        for n, q in scan.questions(
            (HERE / "questions" / "phase3.txt").read_text(encoding="utf-8")
        ):
            if n.startswith(cve + " "):
                out.append((group, n, q, p3ix / cve / "vulnerable", d, None))
    return out


def run(data: Path, ix: Path, p3: Path, p3ix: Path, out: Path) -> dict:
    todo = jobs(data, ix, p3, p3ix)
    diffs: dict = {}
    sets: dict = {}  # index path -> (fix path, core marker) -> (line_ids, file_ids, N)
    rows = []
    cur_ix = None
    index = None
    for group, qid, q, ixp, dpath, core in sorted(todo, key=lambda j: str(j[3])):
        if str(ixp) != cur_ix:
            index = scan.Index(ixp)
            cur_ix = str(ixp)
        if dpath not in diffs:
            text = dpath.read_text(encoding="utf-8")
            diffs[dpath] = (
                score2.changed(text) if core == "php2shell" else phase3.changed(text)
            )
        corelset = score.CORE if core == "php2shell" else None
        key = (cur_ix, dpath)
        if key not in sets:
            sets[key] = hit_sets(index, diffs[dpath], corelset)
        line_ids, file_ids, n = sets[key]
        row = {
            "group": group,
            "question": qid,
            "index": ixp.name,
            "n": n,
            "h_line": len(line_ids),
            "h_file": len(file_ids),
        }
        for by in ("kernel", "bm25", "grep"):
            served = ranked(index, q, by, TOP)
            row[by] = {
                "line": recall_at(served, line_ids, KS),
                "file": recall_at(served, file_ids, KS),
                "chance_line": {k: chance_one(n, len(line_ids), k) for k in KS},
            }
        rows.append(row)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return summarise(rows)


def summarise(rows: list[dict]) -> dict:
    groups = sorted({r["group"] for r in rows})
    summary, passes = {}, {}
    for by in ("kernel", "bm25", "grep"):
        for g in groups:
            rs = [r for r in rows if r["group"] == g]
            for lvl in ("line", "file"):
                recall = {k: sum(r[by][lvl][k] for r in rs) for k in KS}
                summary[f"{by}, {g}, {lvl}"] = {"of": len(rs), **recall}
            ps = [r[by]["chance_line"][10] for r in rs]
            k10 = sum(r[by]["line"][10] for r in rs)
            p = poisson_binomial_tail(ps, k10) if k10 else 1.0
            summary[f"{by}, {g}, line"]["p@10"] = p
            summary[f"{by}, {g}, line"]["expected@10"] = sum(ps)
            if by in ("kernel", "bm25") and g in ("blind", "p3-new", "p3-old"):
                passes[f"{by}, {g}"] = p < 0.01
    return {"summary": summary, "passes": passes}


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    need = {"--data", "--ix", "--p3", "--p3ix", "--box", "--out"}
    if len(argv) != 2 * len(need) or set(opts) != need:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box, out = Path(opts["--box"]), Path(opts["--out"])
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
                != kernel.ALIVE
            ):
                print(f"refused: couldn't start a record at {box}", file=sys.stderr)
                return 2
    result = run(
        Path(opts["--data"]),
        Path(opts["--ix"]),
        Path(opts["--p3"]),
        Path(opts["--p3ix"]),
        out,
    )
    tools = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
        for p in (
            "kernel.py",
            "adapters/stdlib/scan/scan.py",
            "demo/php2shell/phase4.py",
        )
    }
    answers = hashlib.sha256(out.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(
            box,
            NOW,
            "verdict",
            who="php2shell",
            gate=f"phase4:{test}",
            state="satisfied" if passed else "failing",
            answers_sha256=answers,
            tools=tools,
        )
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
