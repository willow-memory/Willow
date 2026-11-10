"""main_run.py: the CI run that holds main's records, by gh. Python 3.9+.

    python adapters/stdlib/ci/main_run.py --artifact PATTERN [--repo OWNER/NAME] [--limit N]

Prints `ID SHA`: the newest green run of ci.yml on main whose artifacts hold
one named PATTERN (a shell pattern: `ci-record-mutants-*`, `test-times`),
and the commit it ran on. That is main's push run, or, when the push stood
on the merge queue's run of the very same commit (its heavy jobs skipped, so
it kept no records), the queue's green run of that commit. Pull requests
read main's records from it: mutants-reach's pin, deps' held record,
red-on-main's comparison, and times.py's test-times.json.

It looks at main's last N green push runs (10 unless `--limit` says),
newest first, and takes the first commit either run of holds the artifact;
an expired artifact holds nothing. Only main's own runs are read, by event:
never an artifact found by name alone, which a fork's pull request could
have uploaded.

Exit codes, the kernel's: 0 found; 42 none held it, or gh couldn't be asked
(it says which); 2 a bad command line.
"""

from __future__ import annotations

import fnmatch
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: main_run.py --artifact PATTERN [--repo OWNER/NAME] [--limit N]"


class Unreached(Exception):
    """gh couldn't be asked, or answered with an error: exit 42."""


def gh(*args: str) -> str:
    if shutil.which("gh") is None:
        raise Unreached("gh isn't installed")
    got = subprocess.run(["gh", *args], capture_output=True, text=True)
    if got.returncode != 0:
        raise Unreached(f"gh {args[0]} {args[1]}: {got.stderr.strip()[:200]}")
    return got.stdout


def runs(repo: list[str], *where: str, limit: int) -> list[tuple[str, str]]:
    """(id, sha) of ci.yml's green runs that match, newest first."""
    out = gh("run", "list", *repo, "--workflow", "ci.yml", "--status", "success",
             *where, "--limit", str(limit), "--json", "databaseId,headSha")  # fmt: skip
    return [(str(r["databaseId"]), r["headSha"]) for r in json.loads(out or "[]")]


def holds(repo: str, run: str, pattern: str) -> bool:
    out = gh("api", f"repos/{repo}/actions/runs/{run}/artifacts", "--paginate",
             "--jq", ".artifacts[] | select(.expired | not) | .name")  # fmt: skip
    return any(fnmatch.fnmatchcase(name, pattern) for name in out.split())


def find(repo: str, pattern: str, limit: int) -> tuple[str, str] | None:
    flag = ["--repo", repo] if repo else []
    slug = repo or "{owner}/{repo}"
    for run, sha in runs(flag, "--branch", "main", "--event", "push", limit=limit):
        if holds(slug, run, pattern):
            return run, sha
        for queued, _ in runs(flag, "--event", "merge_group", "--commit", sha, limit=1):
            if holds(slug, queued, pattern):
                return queued, sha
    return None


def args_of(argv: list[str]) -> dict:
    opts: dict = {"--repo": "", "--limit": "10"}
    it = iter(argv)
    for a in it:
        value = next(it, None)
        if a not in ("--artifact", "--repo", "--limit") or not value or value.startswith("--"):  # fmt: skip
            raise ValueError(USAGE)
        opts[a] = value
    if "--artifact" not in opts or not opts["--limit"].isdigit() or opts["--limit"] == "0":  # fmt: skip
        raise ValueError(USAGE)
    return opts


def main(argv: list[str]) -> int:
    try:
        opts = args_of(argv)
    except ValueError as why:
        print(why, file=sys.stderr)
        return kernel.REFUSED
    try:
        found = find(opts["--repo"], opts["--artifact"], int(opts["--limit"]))
    except Unreached as why:
        print(f"unreachable: {why}", file=sys.stderr)
        return kernel.ESCALATE
    if found is None:
        print(f"none of main's last {opts['--limit']} green runs holds {opts['--artifact']}", file=sys.stderr)  # fmt: skip
        return kernel.ESCALATE
    print(*found)
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
