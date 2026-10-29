"""spread.py: phase 5, the frozen questions asked of another repository.

    python demo/known-gaps/spread.py --repo DIR --out FILE [--gap KG03|all]
        [--stats FILE] [--ix DIR] [--private ROOT]

A gap's 16 frozen questions (both writers) are asked of a repository at its
current HEAD, the way phase 2 asked a whole tree. There is no pass rule: this
makes a list of places for a person to look at, and a candidate is never a
flaw until a person has checked it.

For one gap G and one repository R:

1. R's HEAD tree is written as git stores it, vendored folders left out
   (node_modules, vendor, third_party, venv, .venv, target, dist, build, .git;
   the kernel itself skips hidden folders, binaries and files over its size
   cap), and indexed afresh (ask.py's `fresh_index`).
2. Each of G's 16 questions is asked with bm25, top 10, over the whole tree.
   The kernel's rank and grep are not asked here.
3. A passage is a **candidate** when it is in the top 10 for at least
   MIN_QUESTIONS (4) of the 16 questions, with at least one question from each
   writer: a passage reached only through one writer's words is not a candidate
   on its own.
4. A candidate row holds the gap, repository, path, line range, how many
   questions reached it, which writers, its best rank, and the SHA-256 of the
   passage (never its text), and `own_repo`: true when R is a repository the
   gap's fix landed in.
5. The stats row holds, beside the count, its chance: N passages, each question
   puts a given passage in its top 10 with probability 10/N, so the expected
   number of passages in the top 10 for 4 or more of 16 questions is
   N * P(Binomial(16, 10/N) >= 4), computed exactly. A (gap, repository) whose
   count is at or below its chance is marked so; it is still a count.

Findings are private, and the boundary is one folder. The private root is
`<this worktree's parent>/work/private` unless --private names another; it may
not lie inside any git work tree. --out, --stats (default `stats.jsonl` beside
--out) and --ix (default `ix-spread` in the root) must each resolve, links
followed, to a path strictly under the root and in no git work tree. --repo is
resolved first, and `.`, `..`, an empty name, the root, anything under it and
anything above it are refused; the index folder is named for its final
component. Symlinks in a repository are never followed: each is removed from
the written tree and counted (`symlinks_skipped`). The questions are the frozen
`questions/` folder and no other: exactly 16 a gap, 8 a writer, each file's
SHA-256 equal to FROZEN.json's (else refused) and recorded in the stats row.
The output files are appended to. Exit codes, the kernel's: 0 it ran; 42 a
(gap, repository) was unreachable (no tree, the index failed) and says why in
its stats row; 2 a bad command line or a refused path or question set.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

ask = trees.sibling("ask")
flag = trees.sibling("flag")
HERE = trees.HERE
ROOT = trees.ROOT
QDIR = HERE / "questions"  # the frozen questions, and no other set
DEFAULT_ROOT = ROOT.parent / "work" / "private"  # the one private root
TOP = 10
QUESTIONS = 16
MIN_QUESTIONS = 4
SKIP_DIRS = frozenset({".git", "node_modules", "vendor", "third_party", "venv", ".venv",
                       "target", "dist", "build"})  # fmt: skip


def chance(n: int) -> float:
    """Expected passages in the top 10 for MIN_QUESTIONS or more of 16 questions
    under a uniform random ranking of n passages: n * P(Binomial(16, 10/n) >= 4)."""
    if n <= 0:
        return 0.0
    p = min(1.0, TOP / n)
    tail = sum(comb(QUESTIONS, k) * p**k * (1 - p) ** (QUESTIONS - k)
               for k in range(MIN_QUESTIONS, QUESTIONS + 1))  # fmt: skip
    return n * tail


def own_repo(gap: str, repo: str, pins: dict) -> bool:
    """R is a repository the gap's fix landed in."""
    return any(u["gap"] == gap and u["repo"] == repo for u in pins.values())


def in_git_tree(path: Path) -> bool:
    """The path, or the nearest folder that exists above it, lies inside a git
    work tree (any repository, or any worktree of this one)."""
    here = path
    while not here.exists():
        here = here.parent
    folder = here if here.is_dir() else here.parent
    # no GIT_* variable (GIT_DIR, GIT_WORK_TREE, GIT_CEILING_DIRECTORIES, ...) may
    # steer the question, and it is asked from the folder itself, not by -C
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    done = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=folder, env=env,
                          capture_output=True, text=True)  # fmt: skip
    return done.returncode == 0


def private_root(root: Path) -> Path:
    """The one private root, resolved. It may not lie inside a git work tree:
    anything written there could be committed by `git add -A`."""
    if not root.is_absolute():
        raise ValueError(f"the private root {root} must be an absolute path")
    r = root.resolve()
    if in_git_tree(r):
        raise ValueError(f"the private root {root} lies inside a git work tree")
    return r


def under(root: Path, path: Path) -> Path:
    """The path resolved (links followed), if it lies strictly under `root`
    and in no git work tree. Anything else is refused."""
    p = path.resolve()
    if p == root or root not in p.parents:
        raise ValueError(f"{path} is not strictly under the private root")
    if in_git_tree(p):
        raise ValueError(f"{path} lies inside a git work tree")
    return p


def repo_path(arg: str, root: Path) -> Path:
    """The repository to ask, resolved. `.`, `..`, an empty name, the private
    root, anything under it and anything above it are refused: the index
    folder is named for the final component, and `fresh_index` replaces
    whatever it finds there."""
    if Path(arg).name in ("", ".", ".."):
        raise ValueError(f"{arg!r} does not name a repository")
    r = Path(arg).resolve()
    if r == root or root in r.parents or r in root.parents or r == Path(r.anchor):
        raise ValueError(f"{arg} is the private root, inside it, or above it")
    return r


def gap_questions(qdir: Path, gap: str) -> tuple:
    """([(name, question, writer)], {file: SHA-256}) for a gap: exactly 16,
    8 from each writer."""
    qs = flag.questions(qdir, gap, nulls=False)
    if len(qs) != QUESTIONS or any(
        sum(w == x for _, _, x in qs) != 8 for w in flag.WRITERS
    ):
        raise ValueError(f"{gap} has {len(qs)} questions, not 16 (8 a writer)")
    hashes = {f"{w}/{gap}.txt": hashlib.sha256((qdir / w / f"{gap}.txt").read_bytes()).hexdigest()
              for w in flag.WRITERS}  # fmt: skip
    return qs, hashes


def frozen_questions(qdir: Path, gaps: list) -> str:
    """Every question file of these gaps is the one FROZEN.json holds. Returns
    the SHA-256 of the FROZEN.json read, which the stats row records, so an edited
    freeze shows."""
    raw = (HERE / "FROZEN.json").read_bytes()
    frozen = json.loads(raw.decode("utf-8"))["files"]
    for g in gaps:
        for w in flag.WRITERS:
            rel = f"questions/{w}/{g}.txt"
            got = hashlib.sha256((qdir / w / f"{g}.txt").read_bytes()).hexdigest()
            if frozen.get(rel) != got:
                raise ValueError(f"{rel} is not the file FROZEN.json holds")
    return hashlib.sha256(raw).hexdigest()


def write_head(repo: Path, to: Path) -> tuple:
    """(HEAD commit, its git tree hash, the vendored folders left out): the
    HEAD tree written into `to`, as git stores it."""
    git = trees.phase3.git
    head = git("rev-parse", "HEAD", cwd=repo).decode().strip()
    tree = git("rev-parse", "HEAD^{tree}", cwd=repo).decode().strip()
    trees.phase3.write_tree(repo, head, to)
    links = 0
    for here, dirs, files in os.walk(to, followlinks=False):
        for n in [*dirs, *files]:  # a link is never followed or indexed
            if os.path.islink(os.path.join(here, n)):
                os.unlink(os.path.join(here, n))
                links += 1
        dirs[:] = [d for d in dirs if os.path.isdir(os.path.join(here, d))]
    skipped = []
    for p in sorted(to.rglob("*")):
        if p.is_dir() and p.name in SKIP_DIRS and p.exists():
            skipped.append(p.relative_to(to).as_posix())
            shutil.rmtree(p)
    return head, tree, skipped, links


def reach(index, questions: list) -> dict:
    """{(path, line): {"last", "sha", "names", "writers", "best"}} for every
    passage in the top 10 of any question."""
    seen: dict = {}
    for name, q, writer in questions:
        for rank, c in enumerate(index.bm25(q, TOP), 1):
            text = c["text"]
            row = seen.setdefault((c["path"], c["line"]), {
                "last": c["line"] + len(text.split("\n")) - 1,
                "sha": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "names": set(), "writers": set(), "best": rank})  # fmt: skip
            row["names"].add(name)
            row["writers"].add(writer)
            row["best"] = min(row["best"], rank)
    return seen


def candidates(seen: dict) -> list:
    """The passages in the top 10 for MIN_QUESTIONS questions of both writers."""
    return sorted(
        (k, v) for k, v in seen.items()
        if len(v["names"]) >= MIN_QUESTIONS and set(flag.WRITERS) <= v["writers"]
    )  # fmt: skip


def spread_repo(repo: Path, gaps: list, qdir: Path, ix: Path, pins: dict,
                frozen_sha: str | None = None) -> tuple:  # fmt: skip
    """(candidate rows, stats rows) for one repository and the given gaps."""
    name = repo.name
    rows, stats = [], []
    asked = {g: gap_questions(qdir, g) for g in gaps}  # a wrong set is refused up front
    try:
        if not (repo / ".git").exists():
            raise ValueError("not a git repository")
        ix.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=".tmp-tree-", dir=ix.parent))
        try:
            head, tree, skipped, links = write_head(repo, tmp)
            at = ask.fresh_index(ix.parent, ix.name, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        index = ask.scan.Index(at)
        info = {"repo": name, "head": head, "tree": tree, "skipped": skipped,
                "symlinks_skipped": links, "passages": len(index.pile),
                "index_sha256": ask.index_hash(at)}  # fmt: skip
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        return rows, [
            {"repo": name, "gap": g, "unreachable": str(e)[:200]} for g in gaps
        ]
    for g in gaps:
        questions, hashes = asked[g]
        seen = reach(index, questions)
        found = candidates(seen)
        own = own_repo(g, name, pins)
        for (path, line), v in found:
            rows.append({"gap": g, "repo": name, "path": path, "line": line,
                         "last_line": v["last"], "questions": len(v["names"]),
                         "writers": sorted(v["writers"]), "best_rank": v["best"],
                         "sha256": v["sha"], "own_repo": own})  # fmt: skip
        expected = chance(info["passages"])
        stats.append({**info, "gap": g, "own_repo": own, "candidates": len(found),
                      "question_count": len(questions), "questions_sha256": hashes,
                      "frozen_json_sha256": frozen_sha,
                      "reached_4_any_writer": sum(len(v["names"]) >= MIN_QUESTIONS
                                                  for v in seen.values()),
                      "chance": expected, "at_or_below_chance": len(found) <= expected})  # fmt: skip
    return rows, stats


def append(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    allowed = {"--repo", "--out", "--gap", "--stats", "--ix", "--private"}
    if len(argv) != 2 * len(opts) or not {"--repo", "--out"} <= set(opts) <= allowed:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]  # no GIT_* variable steers any git call this run makes
    gaps = list(trees.load_gaps())
    try:
        root = private_root(Path(opts.get("--private", DEFAULT_ROOT)))
        out = under(root, Path(opts["--out"]))
        stats_path = under(
            root, Path(opts.get("--stats", out.with_name("stats.jsonl")))
        )
        ix = under(root, Path(opts.get("--ix", root / "ix-spread")))
        repo = repo_path(opts["--repo"], root)
        index_at = under(root, ix / repo.name)  # never the root, never above it
        if opts.get("--gap", "all") != "all":
            if opts["--gap"] not in gaps:
                raise ValueError(f"no gap {opts['--gap']}")
            gaps = [opts["--gap"]]
        frozen_sha = frozen_questions(QDIR, gaps)  # the frozen questions or nothing
        rows, stats = spread_repo(
            repo, gaps, QDIR, index_at, trees.load_pins(), frozen_sha
        )
    except (ValueError, OSError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    append(out, rows)
    append(stats_path, stats)
    return 42 if any("unreachable" in s for s in stats) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
