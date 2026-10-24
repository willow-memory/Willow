"""hold.py: the kernel's hold rule against looser ones, on phase 3's CVEs. Not frozen.

    python demo/php2shell/hold.py --to DIR --ix DIR

Run after phase 3, to answer one question its results raised: would a looser
rule than the kernel's (a passage holds at least half the question's content
words) find the fixed code more often, and at what cost? DIR is what
`phase3.py fetch` wrote (trees/ and fixes/); --ix holds `scan.py index` of
each CVE's vulnerable and fixed trees, as phase 3 makes them. It reads both
and writes nothing.

For each CVE fetched, every phase-3 question is asked of the passages the fix
changed, top 3, under five rules, beside BM25:

    half          the kernel's: half the content words
    third         a third of them
    idf-half      half the words' weight, rarer words weighing more
    present-half  half of the words the changed passages hold at all, and two
    any-two       any two of them

and each rule is also asked every other CVE's questions on the same passages.
An answer to a question about another bug is an answer the folder doesn't
have: the price of a looser rule. A hit is phase 3's rule 2.
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [
    str(HERE),
    str(HERE.parents[1] / "adapters" / "stdlib" / "scan"),
    str(HERE.parents[1]),
]
import kernel  # noqa: E402
import phase3  # noqa: E402
import scan  # noqa: E402

TOP = 3

RULES = {
    "half": lambda h, want, ctx: len(h) >= kernel.HOLD * len(want),
    "third": lambda h, want, ctx: len(h) * 3 >= len(want),
    "idf-half": lambda h, want, ctx: sum(map(ctx["idf"], h)) >= 0.5 * sum(map(ctx["idf"], want)),
    "present-half": lambda h, want, ctx: (p := {w for w in want if ctx["df"].get(w)})
    and len(h) >= 0.5 * len(p) and len(h) >= min(2, len(want)),
    "any-two": lambda h, want, ctx: len(h) >= min(2, len(want)),
}  # fmt: skip


def ranked(pool: list[dict], bite: str, keep, ctx: dict) -> list[dict]:
    """The kernel's own scoring (rarest words most, one copy of a text),
    over the passages `keep` lets through."""
    want = set(kernel.words(bite)) - kernel.FUNCTION
    if not want:
        return []
    held = [
        (c, {w for w in want if kernel.held_by(w, kernel.toks(c), {})}) for c in pool
    ]
    held = [(c, h) for c, h in held if h and keep(h, want, ctx)]
    df = {w: sum(w in h for _, h in held) for w in want}
    order = sorted(held, key=lambda x: (-sum(Fraction(1, df[w]) for w in x[1]),
                                        x[0]["path"], x[0]["line"]))  # fmt: skip
    out: list[dict] = []
    for c, _ in order:
        if len(out) == TOP:
            break
        if all(c["id"] != o["id"] for o in out):
            out.append(c)
    return out


def run(to: Path, ix: Path) -> dict:
    qs = scan.questions((HERE / "questions" / "phase3.txt").read_text(encoding="utf-8"))
    cves = [
        c
        for c in phase3.PINS
        if (to / "fixes" / f"{c}.diff").exists() and (ix / c / "fixed").exists()
    ]
    names = [*RULES, "bm25"]
    hits = {r: {c: 0 for c in cves} for r in names}
    other = {r: [0, 0] for r in RULES}
    for cve in cves:
        fix = phase3.changed((to / "fixes" / f"{cve}.diff").read_text(encoding="utf-8"))
        before = {c["id"] for c in scan.passages(ix / cve / "fixed")}
        old = scan.Index(ix / cve / "vulnerable")
        pool = [c for c in old.pile if c["id"] not in before]
        df: dict[str, int] = {}
        for c in pool:
            for w in set(kernel.words(c["text"])) - kernel.FUNCTION:
                df[w] = df.get(w, 0) + 1
        ctx = {
            "df": df,
            "idf": lambda w, n=len(pool), df=df: math.log(
                (n + 1) / (df.get(w, 0) + 0.5)
            ),
        }
        for n, q in qs:
            mine = n.startswith(cve + " ")
            if not mine and not any(n.startswith(c + " ") for c in phase3.PINS):
                continue
            for r, keep in RULES.items():
                got = ranked(pool, q, keep, ctx)
                if mine:
                    hits[r][cve] += any(phase3.hit(c, fix) for c in got)
                else:
                    other[r][0] += bool(got)
                    other[r][1] += 1
            if mine:
                hits["bm25"][cve] += any(
                    phase3.hit(c, fix) for c in old.bm25(q, TOP, before)
                )
    return {"cves": cves, "hits": hits, "other": other}


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if set(opts) != {"--to", "--ix"} or len(argv) != 4:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    got = run(Path(opts["--to"]), Path(opts["--ix"]))
    print(
        "| Rule | "
        + " | ".join(c for c in got["cves"])
        + " | Total | Answers to other CVEs' questions |"
    )
    print("|---" * (len(got["cves"]) + 3) + "|")
    for r, by in got["hits"].items():
        o = got["other"].get(r)
        tail = f"{o[0]} of {o[1]}" if o else "always 3"
        cells = " | ".join(f"{by[c]} of 8" for c in got["cves"])
        print(
            f"| {r} | {cells} | {sum(by.values())} of {8 * len(got['cves'])} | {tail} |"
        )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
