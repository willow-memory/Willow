"""phase3.py: out of sample. Seven other CVEs, the same method, questions blind.

    python demo/php2shell/phase3.py fetch --to DIR
    python demo/php2shell/phase3.py check --to DIR
    python demo/php2shell/phase3.py run --to DIR --ix DIR --box DIR --out FILE

`fetch` writes, for each CVE in phase3.json, DIR/trees/<CVE>/vulnerable and
/fixed, and DIR/fixes/<CVE>.diff (its fix commits' diffs against their
parents, in order), from each project's git repository (online, with git).
Each tree is every file of the pinned commit, byte for byte, as git stores
it: not `git archive`, whose export rules leave files out (Brotli marks most
of its tree export-ignore) or rewrite them (Log4j turns one file's line
endings to CRLF). `check` holds each tree to its git tree hash and each diff
to its SHA-256, without git. `run` expects DIR/../ix/<CVE>/vulnerable and
/fixed, made by `scan.py index`, or --ix.

Frozen, with the questions and its pass rules, before it ran (FROZEN.json).

**The rule.** score2.py's rule 2, at its `any` level: a passage hits when it
holds a line a fix commit removed, or one unchanged line next to a run of
added lines. These fixes change 1 to 24 files, so no file is singled out as
core. Never counted: any path with a folder named test, tests, testing,
spec or changes; files named NEWS, UPGRADING, ChangeLog, CHANGES,
CHANGES.md, CHANGELOG.md, version.h or RELEASE-NOTES.md, and .phpt files.

**The tests.** Each CVE's questions are asked of its vulnerable release
`--changed-from` its fixed one, top 3, ranked by the kernel and by BM25,
beside 10,000 random draws of 3 changed passages.

| Rule | Passes when |
|---|---|
| found, kernel / bm25 | at least half of a CVE's questions hit; it passes for most CVEs (4 of 7) |
| above chance, kernel / bm25, new and old apart | the group's pooled hits beat its pooled random rate, one-sided binomial p < 0.01 |

The two CVEs disclosed after mid-2026 (`known_to_models: false`) are judged
apart from the five older ones, whose blind writer may remember their code.

Exit 0 when every rule passes, 42 when one fails, 2 for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import make_trees  # noqa: E402
import phase2  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

PINS = json.loads((HERE / "phase3.json").read_text(encoding="utf-8"))["cves"]
SEED = "php2shell phase 3"
DRAWS = 10_000
TOP = 3
NOW = "2026-10-24T00:00:00Z"
SKIP_DIRS = {"test", "tests", "testing", "spec", "changes"}
SKIP_NAMES = {"NEWS", "UPGRADING", "ChangeLog", "CHANGES", "CHANGES.md", "CHANGELOG.md",
              "version.h", "RELEASE-NOTES.md"}  # fmt: skip


def counts(path: str) -> bool:
    parts = path.split("/")
    return not (
        SKIP_DIRS & set(parts[:-1]) or parts[-1] in SKIP_NAMES or path.endswith(".phpt")
    )


def repo_dir(to: Path, url: str) -> Path:
    return to / "repos" / url.rstrip("/").rsplit("/", 1)[1]


def git(*argv: str, cwd: Path | None = None, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", *argv], cwd=cwd, input=data, check=True,
                          capture_output=True).stdout  # fmt: skip


def write_tree(src: Path, commit: str, out: Path) -> None:
    """Every file of `commit`, as git stores it, with its mode."""
    listing = git("ls-tree", "-r", "-z", commit, cwd=src).split(b"\0")
    entries = [e.split(b"\t", 1) for e in listing if e]
    shas = [meta.split()[2].decode() for meta, _ in entries]
    git(
        "archive", "--format=tar", "-o", os.devnull, commit, cwd=src
    )  # fetches its blobs at once
    batch = git(
        "cat-file", "--batch", cwd=src, data="".join(s + "\n" for s in shas).encode()
    )
    pos = 0
    for (meta, name), sha in zip(entries, shas):
        head_end = batch.index(b"\n", pos)
        size = int(batch[pos:head_end].split()[2])
        body = batch[head_end + 1 : head_end + 1 + size]
        pos = head_end + 1 + size + 1
        mode = meta.split()[0]
        path = out / name.decode()
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == b"120000":
            os.symlink(body.decode(), path)
        elif mode == b"160000":
            continue  # a submodule: not this repository's files
        else:
            path.write_bytes(body)
            if mode == b"100755":
                path.chmod(0o755)


def fetch(to: Path) -> None:
    for cve, pin in PINS.items():
        src = repo_dir(to, pin["source"])
        if not (src / ".git").exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            git(
                "clone",
                "--quiet",
                "--filter=blob:none",
                "--no-checkout",
                pin["source"],
                str(src),
            )
        git("fetch", "--quiet", "origin", pin["vulnerable"]["commit"], pin["fixed"]["commit"],
            *[f["commit"] for f in pin["fixes"]], cwd=src)  # fmt: skip
        for side in ("vulnerable", "fixed"):
            out = to / "trees" / cve / side
            if out.exists() and make_trees.git_tree(out) == pin[side]["tree"]:
                continue
            out.mkdir(parents=True, exist_ok=True)
            write_tree(src, pin[side]["commit"], out)
        (to / "fixes").mkdir(exist_ok=True)
        diff = b"".join(git(*make_trees.DIFF, f["commit"] + "^", f["commit"], cwd=src)
                        for f in pin["fixes"])  # fmt: skip
        (to / "fixes" / f"{cve}.diff").write_bytes(diff)


def check(to: Path) -> int:
    bad = missing = 0
    for cve, pin in PINS.items():
        for side in ("vulnerable", "fixed"):
            t = to / "trees" / cve / side
            if not t.is_dir():
                print(f"missing   {cve} {side}")
                missing += 1
            elif make_trees.git_tree(t) != pin[side]["tree"]:
                print(f"DIFFERS   {cve} {side}")
                bad += 1
            else:
                print(f"matches   {cve} {side}")
        d = to / "fixes" / f"{cve}.diff"
        if not d.is_file():
            print(f"missing   {cve} fix")
            missing += 1
        elif hashlib.sha256(d.read_bytes()).hexdigest() != pin["diff_sha256"]:
            print(f"DIFFERS   {cve} fix")
            bad += 1
        else:
            print(f"matches   {cve} fix")
    return 2 if bad else 42 if missing else 0


def changed(diff: str) -> dict:
    """Rule 2's changed lines, with this phase's files left out."""
    was = score.counts
    score.counts = counts
    try:
        return score2.changed(diff)
    finally:
        score.counts = was


def hit(passage: dict, fix: dict) -> bool:
    path = passage["path"]
    return bool(
        {x.strip() for x in passage["text"].splitlines()} & fix["old"].get(path, set())
    )


def run(to: Path, ix: Path, out: Path) -> dict:
    qs = scan.questions((HERE / "questions" / "phase3.txt").read_text(encoding="utf-8"))
    rows, groups = [], {}
    for cve, pin in PINS.items():
        fix = changed((to / "fixes" / f"{cve}.diff").read_text(encoding="utf-8"))
        before = {c["id"] for c in scan.passages(ix / cve / "fixed")}
        old = scan.Index(ix / cve / "vulnerable")
        changed_set = [c for c in old.pile if c["id"] not in before]
        mine = [(n, q) for n, q in qs if n.startswith(cve + " ")]
        for by in ("kernel", "bm25"):
            for n, q in mine:
                got = (
                    old.rank(q, {}, TOP, before)
                    if by == "kernel"
                    else old.bm25(q, TOP, before)
                )
                hits = [hit(c, fix) for c in got]
                rows.append({"cve": cve, "question": n, "ranked_by": by, "hit": any(hits),
                             "served": [f"{c['path']}:{c['line']}" for c in got], "hits": hits})  # fmt: skip
        rng = random.Random(f"{SEED} {cve}")
        k = min(TOP, len(changed_set))
        drawn = (
            sum(
                any(hit(c, fix) for c in rng.sample(changed_set, k))
                for _ in range(DRAWS)
            )
            if k
            else 0
        )
        groups[cve] = {"changed": len(changed_set), "random_rate": drawn / DRAWS,
                       "new": not pin["known_to_models"], "questions": len(mine)}  # fmt: skip
        old = changed_set = None
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    found, chance = {}, {}
    for by in ("kernel", "bm25"):
        for cve, g in groups.items():
            h = sum(r["hit"] for r in rows if r["cve"] == cve and r["ranked_by"] == by)
            g[f"{by}_hits"] = h
        found[by] = sum(
            g[f"{by}_hits"] * 2 >= g["questions"] > 0 for g in groups.values()
        )
        for name, new in (("new", True), ("old", False)):
            gs = [g for g in groups.values() if g["new"] == new]
            n = sum(g["questions"] for g in gs)
            k = sum(g[f"{by}_hits"] for g in gs)
            rate = sum(g["random_rate"] * g["questions"] for g in gs) / n if n else 1.0
            chance[f"{by}, {name}"] = {"hits": k, "of": n, "random": rate,
                                       "p": phase2.binomial_tail(k, n, rate)}  # fmt: skip
    passes = {
        **{f"found, {by}": found[by] >= 4 for by in ("kernel", "bm25")},
        **{f"above chance, {k}": v["p"] < 0.01 for k, v in chance.items()},
    }
    return {"cves": groups, "found": found, "chance": chance, "passes": passes}


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    needs = {
        "fetch": {"--to"},
        "check": {"--to"},
        "run": {"--to", "--ix", "--box", "--out"},
    }
    if (
        cmd not in needs
        or set(opts) != needs[cmd]
        or len(argv) != 1 + 2 * len(needs[cmd])
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    to = Path(opts["--to"])
    if cmd == "fetch":
        to.mkdir(parents=True, exist_ok=True)
        fetch(to)
        return check(to)
    if cmd == "check":
        return check(to)
    box, out = Path(opts["--box"]), Path(opts["--out"])
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
                != kernel.ALIVE
            ):
                print(f"refused: couldn't start a record at {box}", file=sys.stderr)
                return 2
    result = run(to, Path(opts["--ix"]), out)
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "kernel.py", "adapters/stdlib/scan/scan.py", "demo/php2shell/score2.py",
        "demo/php2shell/phase3.py")}  # fmt: skip
    answers = hashlib.sha256(out.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(box, NOW, "verdict", who="php2shell", gate=f"phase3:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=answers, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
