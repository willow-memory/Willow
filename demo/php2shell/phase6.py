"""phase6.py: reproducibility. Anyone gets the same answers from the same files.

    python demo/php2shell/phase6.py exact  --data DIR --ix DIR --box DIR
    python demo/php2shell/phase6.py bytes  --data DIR --ix DIR --box DIR --work DIR
    python demo/php2shell/phase6.py ports  --data DIR --ix DIR --box DIR --work DIR
    python demo/php2shell/phase6.py items  --data DIR --ix DIR --out FILE
    python demo/php2shell/phase6.py agree  --data DIR --ix DIR --box DIR --labels FILE

The same --data, --ix and --box as phase2.py. Frozen, with its pass rules,
before any part ran (FROZEN.json). Each part writes one verdict row a check.

| Part | What it does | Passes when |
|---|---|---|
| exact | every release's index ranks the author's questions, every passage, against the kernel's own `rank` over the whole tree | all 16 releases x 8 questions the same |
| bytes | scan's answers for 8.5.11 (whole, and `--changed-from` 8.5.12) on Python 3.9, 3.11, 3.12, 3.13 and 3.14, hash seeds 0, 1 and 4242; and the index of 8.5.11 made on 3.9 and 3.14 | every run's bytes the same; a Python not on the machine is unreachable, never a pass |
| ports | the Java, TypeScript and C# kernels' `bite` on 8.5.11 for the author's questions, beside kernel.py's | every port serves the same passages, in order, for every question; a toolchain not on the machine is unreachable |
| items | writes, for an independent labeller, every distinct passage phase 1 served in a file the fix changed, with that file's part of the fix | (no verdict) |
| agree | the labeller's yes or no, set beside rule 2's (core or any is yes) and rule 1's | Cohen's kappa against rule 2 at least 0.6 |

Exit 0 when a part's checks pass, 42 when one fails or can't be reached, 2
for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

NOW = "2026-10-24T00:00:00Z"
SCAN = ROOT / "adapters" / "stdlib" / "scan" / "scan.py"
PYTHONS = ("3.9", "3.11", "3.12", "3.13", "3.14")
SEEDS = ("0", "1", "4242")
VERSIONS = [
    v for v, p in score.PINS["releases"].items() if v not in ("8.4.25", "8.5.10")
]


def author() -> list[tuple[str, str]]:
    return scan.questions(
        (HERE / "questions" / "author.txt").read_text(encoding="utf-8")
    )


def verdict(box: Path, check: str, ok: bool | None, **fields) -> None:
    state = "unreachable" if ok is None else "satisfied" if ok else "failing"
    kernel.append(box, NOW, "verdict", who="php2shell", gate=f"phase6:{check}",
                  state=state, **fields)  # fmt: skip
    print(f"{check:<40} {state}")


def open_box(box: Path) -> None:
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
                != kernel.ALIVE
            ):
                raise SystemExit(f"refused: couldn't start a record at {box}")


def place(c: dict) -> list:
    return [c["path"], c["line"], c["id"]]


def exact_one(job: tuple[str, str]) -> tuple[str, list[bool]]:
    tree, ix = job
    pile = kernel.chunks(Path(tree))
    index = scan.Index(Path(ix))
    kernel.TOP = 10**9
    same = []
    for _, q in author():
        same.append(
            list(map(place, kernel.rank(pile, q)))
            == list(map(place, index.rank(q, {}, 10**9)))
        )
    return Path(tree).name, same


def exact(data: Path, ix: Path, box: Path) -> bool:
    jobs = [(str(data / "trees" / v), str(ix / v)) for v in VERSIONS]
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        got = dict(pool.map(exact_one, jobs))
    ok = True
    for v in VERSIONS:
        verdict(box, f"exact {v}", all(got[v]), same=sum(got[v]), of=len(got[v]))
        ok = ok and all(got[v])
    return ok


def python(version: str) -> str | None:
    found = shutil.which(f"python{version}")
    if found:
        return found
    got = subprocess.run(
        ["uv", "python", "find", version], capture_output=True, text=True
    )
    return got.stdout.strip() or None if got.returncode == 0 else None


def run_bytes(py: str, seed: str, argv: list[str]) -> bytes:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    got = subprocess.run([py, str(SCAN), *argv], capture_output=True, env=env)
    return got.stdout + b"\nexit %d\n" % got.returncode


def same_bytes(data: Path, ix: Path, box: Path, work: Path) -> bool:
    q = str(HERE / "questions" / "author.txt")
    asks = {
        "whole": ["scan", "--index", str(ix / "8.5.11"), "--questions", q],
        "changed": ["scan", "--index", str(ix / "8.5.11"), "--changed-from",
                    str(ix / "8.5.12"), "--questions", q],
    }  # fmt: skip
    ok = True
    for name, argv in asks.items():
        seen: dict[str, str] = {}
        for v in PYTHONS:
            py = python(v)
            if py is None:
                verdict(box, f"bytes {name} python {v}", None)
                ok = False
                continue
            for seed in SEEDS:
                seen[f"{v} seed {seed}"] = hashlib.sha256(
                    run_bytes(py, seed, argv)
                ).hexdigest()
        one = len(set(seen.values())) == 1
        verdict(
            box, f"bytes {name}", one, runs=len(seen), sha256=sorted(set(seen.values()))
        )
        ok = ok and one
    made = {}
    for v in ("3.9", "3.13", "3.14"):
        py = python(v)
        if py is None:
            verdict(box, f"bytes index python {v}", None)
            ok = False
            continue
        to = work / f"index-{v}"
        shutil.rmtree(to, ignore_errors=True)
        subprocess.run([py, str(SCAN), "index", "--from", str(data / "trees" / "8.5.11"),
                        "--to", str(to)], check=True, capture_output=True)  # fmt: skip
        made[v] = {
            f: hashlib.sha256((to / f).read_bytes()).hexdigest() for f in scan.FILES
        }
        shutil.rmtree(to)
    one = len({json.dumps(m, sort_keys=True) for m in made.values()}) == 1
    verdict(box, "bytes index", one, made_on=sorted(made))
    return ok and one


def bite_ids(argv_of, tree: Path, work: Path, name: str) -> list[list[str]]:
    """Each author question's served ids, through one implementation's own
    command line, on a box of its own."""
    b = work / f"box-{name}"
    shutil.rmtree(b, ignore_errors=True)
    (work / f"key-{name}").unlink(missing_ok=True)
    sys.path.insert(0, str(ROOT / "vectors"))
    import compare

    env = compare.ENV  # the environment compare.py runs every port in
    subprocess.run(argv_of("init", "--box", str(b), "--pile", str(tree), "--key",
                           str(work / f"key-{name}"), "--now", NOW),
                   check=True, capture_output=True, env=env)  # fmt: skip
    out = []
    for _, q in author():
        got = subprocess.run(argv_of("bite", "--box", str(b), "--now", NOW, q),
                             capture_output=True, text=True, env=env)  # fmt: skip
        out.append([s["id"] for s in json.loads(got.stdout).get("served", [])])
    return out


class Python:
    """kernel.py itself, run the way compare.py runs a port."""

    tools = ("python3",)

    def argv(self, *args: str) -> list[str]:
        return [sys.executable, str(ROOT / "kernel.py"), *args]


def ports(data: Path, ix: Path, box: Path, work: Path) -> bool:
    sys.path.insert(0, str(ROOT / "vectors"))
    import compare  # the repo's own way of building and running each port

    tree = data / "trees" / "8.5.11"
    built = {"python": Python()}
    for name, cls in compare.PORTS.items():
        if all(shutil.which(t) for t in cls.tools):
            built[name] = cls(work)  # built once, here, before any runs
        else:
            verdict(box, f"ports {name}", None)
    with Pool(len(built)) as pool:
        runs = pool.starmap(
            bite_ids, [(b.argv, tree, work, n) for n, b in built.items()]
        )
    got = dict(zip(built, runs))
    ok = len(built) == 4
    for name in built:
        if name == "python":
            continue
        same = got[name] == got["python"]
        verdict(box, f"ports {name}", same,
                same=sum(a == b for a, b in zip(got[name], got["python"])), of=len(got["python"]))  # fmt: skip
        ok = ok and same
    return ok


def served_in_phase1(ix: Path) -> list[dict]:
    """Every distinct passage phase 1 served, asking the old code."""
    import phase1

    sets = {s: scan.questions((HERE / "questions" / f"{s}.txt").read_text(encoding="utf-8"))
            for s in phase1.SETS}  # fmt: skip
    seen: dict[tuple, dict] = {}
    for branch, fix in score.PINS["fixes"].items():
        before = {c["id"] for c in scan.passages(ix / fix["fixed"])}
        old = scan.Index(ix / fix["vulnerable"])
        for qs in sets.values():
            for _, q in qs:
                for c in old.rank(q, {}, 3, before) + old.bm25(q, 3, before):
                    seen.setdefault((branch, c["path"], c["line"], c["id"]),
                                    {"fix": branch, "where": f"{c['path']}:{c['line']}",
                                     "text": c["text"]})  # fmt: skip
        old = None
    return list(seen.values())


def file_diff(diff: str, path: str) -> str:
    """The part of a unified diff that changes `path`."""
    out, keep = [], False
    for ln in diff.splitlines():
        if ln.startswith("diff --git "):
            keep = ln.endswith(f" b/{path}")
        if keep:
            out.append(ln)
    return "\n".join(out)


def items(data: Path, ix: Path, out: Path) -> None:
    fixes = {
        b: (data / "fixes" / f"{b}.diff").read_text(encoding="utf-8")
        for b in score.PINS["fixes"]
    }
    files = {b: score.changed(d)["files"] for b, d in fixes.items()}
    got = [
        p
        for p in served_in_phase1(ix)
        if p["where"].rsplit(":", 1)[0] in files[p["fix"]]
    ]
    got.sort(key=lambda p: (p["fix"], p["where"]))
    with open(out, "w", encoding="utf-8") as f:
        f.write("# For the labeller. Each item is a passage of a vulnerable PHP release, and the\n"
                "# part of the security fix that changes its file. For each item, answer yes or no:\n"
                "# does the fix change this passage's code, by removing or changing a line of it,\n"
                "# or by inserting code inside it or directly next to it?\n\n")  # fmt: skip
        shown = set()
        for n, p in enumerate(got, 1):
            path = p["where"].rsplit(":", 1)[0]
            if (p["fix"], path) not in shown:
                shown.add((p["fix"], path))
                f.write(
                    f"=== FIX {p['fix']}, FILE {path}\n{file_diff(fixes[p['fix']], path)}\n\n"
                )
            f.write(f"--- ITEM {n} (fix {p['fix']}, {p['where']})\n{p['text']}\n\n")
    (out.with_suffix(".key.json")).write_text(json.dumps(got, indent=1) + "\n")
    print(
        f"{len(got)} items in {len({(p['fix'], p['where'].rsplit(':', 1)[0]) for p in got})} files"
    )


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def agree(data: Path, ix: Path, box: Path, labels: Path, key: Path) -> bool:
    got = json.loads(key.read_text())
    said = json.loads(labels.read_text())  # {"1": "yes", ...}
    answers = [{"index": score.PINS["fixes"][p["fix"]]["vulnerable"], "question": str(n),
                "served": [p]} for n, p in enumerate(got, 1)]  # fmt: skip
    fixes = data / "fixes"
    human = [said[str(n)].strip().lower() == "yes" for n in range(1, len(got) + 1)]
    ok = True
    for rule, scorer in (("rule 2", score2.score_answers), ("rule 1", score.score)):
        mine = [r["best"] in ("core", "any") for r in scorer(answers, fixes)]
        k = kappa(human, mine)
        both = sum(h == m for h, m in zip(human, mine))
        if rule == "rule 2":
            verdict(
                box,
                "agree rule 2",
                k >= 0.6,
                kappa=round(k, 3),
                agree=both,
                of=len(got),
            )
            ok = k >= 0.6
        else:
            verdict(
                box,
                "agree rule 1 (reported)",
                True,
                kappa=round(k, 3),
                agree=both,
                of=len(got),
            )
    return ok


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    needs = {"exact": {"--data", "--ix", "--box"}, "bytes": {"--data", "--ix", "--box", "--work"},
             "ports": {"--data", "--ix", "--box", "--work"}, "items": {"--data", "--ix", "--out"},
             "agree": {"--data", "--ix", "--box", "--labels"}}  # fmt: skip
    if (
        cmd not in needs
        or set(opts) != needs[cmd]
        or len(argv) != 1 + 2 * len(needs[cmd])
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    data, ix = Path(opts["--data"]), Path(opts["--ix"])
    if cmd == "items":
        items(data, ix, Path(opts["--out"]))
        return 0
    box = Path(opts["--box"])
    open_box(box)
    if cmd == "exact":
        ok = exact(data, ix, box)
    elif cmd == "agree":
        labels = Path(opts["--labels"])
        ok = agree(data, ix, box, labels, labels.parent / "items.key.json")
    else:
        work = Path(opts["--work"])
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work):
            ok = (same_bytes if cmd == "bytes" else ports)(data, ix, box, work)
    return 0 if ok else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
