"""pipeline.py: the whole PHP2Shell method in one command, three rankers.

    python demo/php2shell/pipeline.py --php DIR --p3 DIR --work DIR
        [--rankers kernel,bm25,latent]

Composes what's in the box end to end: index each release with scan, ask the
frozen question sets of only what each fix changed (scan's --changed-from),
rank by the kernel, by BM25 (both scan's) and by meaning (the latent
add-on), and score each answer against the fix with the frozen rule
(score2 for PHP2Shell's core files, phase3's rule for the seven other CVEs).
It prints the hit rate per group and ranker: the "see what comes back" table.

--php is make_trees.py's --to (its trees/ and fixes/); --p3 is phase3.py's
--to. --work holds the indexes it builds. This is a runner, not an add-on:
it orchestrates the built commands, so it is not bound by an add-on's
promises, needs numpy (through latent), and is not part of CI. Its answers
rest on the tested pieces it calls.

Exit 0 always; it reports, it does not judge.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(ROOT / "adapters" / "deps" / "latent"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import latent  # noqa: E402
import phase3  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

TOP = 3


def q(name: str):
    return scan.questions((HERE / "questions" / name).read_text(encoding="utf-8"))


def rankers(names):
    table = {
        "kernel": lambda ix, s, top, lacked: ix.rank(s, {}, top, lacked),
        "bm25": lambda ix, s, top, lacked: ix.bm25(s, top, lacked),
        "latent": lambda ix, s, top, lacked: latent.rank(ix, s, top, lacked),
    }
    return {n: table[n] for n in names}


def changed(diff: str, core):
    if core is score.CORE:
        full = score2.changed(diff)
        return {f: full["old"][f] for f in full["old"] if f in core}
    return phase3.changed(diff)["old"]


def hit(served, old) -> bool:
    # scan's rankers return raw chunks (path); latent returns where=path:line
    def path(c):
        return c["path"] if "path" in c else c["where"].rsplit(":", 1)[0]

    return any({x.strip() for x in c["text"].splitlines()} & old.get(path(c), set())
               for c in served)  # fmt: skip


def index_pair(work: Path, label: str, vuln: Path, fixed: Path):
    a, b = work / label / "vuln", work / label / "fixed"
    for src, to in ((vuln, a), (fixed, b)):
        if not (to / "index.json").exists():
            to.mkdir(parents=True, exist_ok=True)
            scan.build(src, to)
    return a, b


def pairs(php: Path, p3: Path):
    php_q = q("author.txt") + sum(
        (q(f"{s}.txt") for s in ("blind-a", "blind-b", "blind-c")), []
    )
    out = []
    for branch, f in score.PINS["fixes"].items():
        out.append(
            (
                f"php2shell/{branch}",
                "php2shell",
                php / "trees" / f["vulnerable"],
                php / "trees" / f["fixed"],
                php / "fixes" / f"{branch}.diff",
                score.CORE,
                php_q,
            )
        )
    p3_q = q("phase3.txt")
    for cve, pin in phase3.PINS.items():
        out.append(
            (
                cve,
                "p3-new" if not pin["known_to_models"] else "p3-old",
                p3 / "trees" / cve / "vulnerable",
                p3 / "trees" / cve / "fixed",
                p3 / "fixes" / f"{cve}.diff",
                None,
                [(n, s) for n, s in p3_q if n.startswith(cve + " ")],
            )
        )
    return out


def run(php: Path, p3: Path, work: Path, names) -> dict:
    fns = rankers(names)
    agg: dict = {}
    for label, group, vuln, fixed, diff, core, qs in pairs(php, p3):
        old = changed(diff.read_text(encoding="utf-8"), core)
        vix, fix = index_pair(work, label.replace("/", "_"), vuln, fixed)
        lacked = {c["id"] for c in scan.passages(fix)}
        idx = scan.Index(vix)
        for name, fn in fns.items():
            got = sum(hit(fn(idx, s, TOP, lacked), old) for _, s in qs)
            a = agg.setdefault((group, name), [0, 0])
            a[0] += got
            a[1] += len(qs)
        idx = None
    return agg


def main(argv) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if {"--php", "--p3", "--work"} - set(opts):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    names = opts.get("--rankers", "kernel,bm25,latent").split(",")
    agg = run(Path(opts["--php"]), Path(opts["--p3"]), Path(opts["--work"]), names)
    print(f"{'group':10} {'ranker':8} hits/total  rate")
    for (group, name), (got, n) in sorted(agg.items()):
        print(
            f"{group:10} {name:8} {got:3}/{n:<3}     {got / n:.0%}"
            if n
            else f"{group} {name} -"
        )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
