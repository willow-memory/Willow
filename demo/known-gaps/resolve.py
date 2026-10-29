"""resolve.py: gaps.json to pins.json, from the fleet's own repositories.

    python demo/known-gaps/resolve.py --repos DIR --out FILE

For each fix in gaps.json, from the repository DIR/<repo>: the full commit of
the vulnerable side (a merge's first parent, or a lone commit's parent), the
fixed side (the merge, or the commit), each side's git tree hash, and the
SHA-256 of the fix's diff (php2shell's DIFF flags), restricted to the gap's
files_scored where it names any. A gap fixed in two repositories gives two
units (KG03-kartikeya, KG03-willow-mcp); any other gives one, named by its id.

Reads local repositories with git, no network, and writes only FILE. A merge
that doesn't carry its pull request's number in its message, a commit with
other than one parent, or a name git can't resolve is refused, and nothing is
written. Exit codes, the kernel's: 0 written; 2 refused or a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402


def rev(repo: Path, name: str) -> str:
    out = trees.phase3.git("rev-parse", "--verify", "--quiet", name + "^{commit}",
                           cwd=repo)  # fmt: skip
    return out.decode().strip()


def side(repo: Path, commit: str) -> dict:
    tree = trees.phase3.git("rev-parse", commit + "^{tree}", cwd=repo)
    return {"commit": commit, "tree": tree.decode().strip()}


def resolve_fix(repos: Path, fix: dict, files: list | None) -> dict:
    repo = repos / fix["repo"]
    if fix["kind"] == "merge":
        fixed = rev(repo, fix["merge"])
        message = trees.phase3.git("log", "-1", "--format=%B", fixed, cwd=repo).decode()
        if not re.search(rf"#{fix['pr']}\b", message):
            raise ValueError(
                f"{fix['merge']} in {fix['repo']} doesn't name #{fix['pr']}"
            )
    else:
        fixed = rev(repo, fix["commit"])
    parents = trees.phase3.git("rev-list", "--parents", "-n", "1", fixed, cwd=repo)
    parents = parents.decode().split()[1:]
    if not parents or (fix["kind"] == "commit" and len(parents) != 1):
        raise ValueError(f"{fixed[:12]} in {fix['repo']} has {len(parents)} parents")
    vulnerable = parents[0]
    names = trees.phase3.git("diff", "--no-renames", "--name-only", vulnerable, fixed,
                             cwd=repo).decode().splitlines()  # fmt: skip
    for f in files or []:
        if f not in names:
            raise ValueError(f"{f} is not in the diff of {fixed[:12]} in {fix['repo']}")
    argv = [*trees.DIFF, vulnerable, fixed] + (["--", *files] if files else [])
    diff = trees.phase3.git(*argv, cwd=repo)
    if not diff:
        raise ValueError(f"{fixed[:12]} in {fix['repo']}: an empty diff")
    return {"repo": fix["repo"], "vulnerable": side(repo, vulnerable),
            "fixed": side(repo, fixed), "files_scored": files,
            "diff_files": names,
            "diff_sha256": hashlib.sha256(diff).hexdigest()}  # fmt: skip


def resolve(repos: Path, gaps: dict) -> dict:
    units = {}
    for gid, gap in gaps.items():
        for fix in gap["fix"]:
            name = gid if len(gap["fix"]) == 1 else f"{gid}-{fix['repo']}"
            if name in units:
                raise ValueError(f"{name} is pinned twice")
            units[name] = {"gap": gid,
                           **resolve_fix(repos, fix, fix.get("files_scored"))}  # fmt: skip
    return units


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 4 or set(opts) != {"--repos", "--out"}:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        units = resolve(Path(opts["--repos"]), trees.load_gaps())
    except (ValueError, OSError, trees.phase3.subprocess.CalledProcessError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    doc = {"about": "pins.json: each gap's vulnerable and fixed commits and trees, and the "
           "SHA-256 of the fix's diff. Made by resolve.py from gaps.json.", "units": units}  # fmt: skip
    Path(opts["--out"]).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    for unit, u in units.items():
        print(
            f"{unit:14} {u['vulnerable']['commit'][:12]} -> {u['fixed']['commit'][:12]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
