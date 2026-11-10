"""restack_open.py: every open pull request that conflicts with its base,
merged up to it by restack's rules and pushed, or named for a person.
Python 3.9+.

    python adapters/stdlib/restack-open/restack_open.py --repo OWNER/NAME [--push] [--json]
    python adapters/stdlib/restack-open/restack_open.py --prs FILE [--push] [--json]

Run it in a clone of the repository whose remote `origin` is the one the
pull requests are on. It lists the open pull requests (`gh api`, or a file
of what GitHub's pulls API returns, with `--prs`), and for each one from
this repository's own branches:

    restack-open: populated, 4 open; 1 merged up, 1 for a person
    ## for a person
      #281  add/stack-share  realdata.py: a conflict with no rule; settle it by hand
    ## merged up
      #280  dialect-dates    main merged in; settled ADDONS.md: pushed
    ## left as they are
      #283  dependabot/...   a bot's branch: it rebases its own
      #279  equations-...    merges clean into main

A branch that merges cleanly into its base is left as it is. One that
conflicts is given to `adapters/stdlib/restack/restack.py`: when restack
settles every conflict by its rules (the files the repo makes, the
changelog, FILES.md, the COMMANDS table, planned.json, a Markdown file both
sides only added to), its merge commit is pushed with `--push`, or said as
the push to make without it; any other conflict is named for a person, and
the branch is left exactly as it was. A pull request from a fork, or a
bot's, is never touched: its branch is its author's.

It pushes only a merge commit on top of the branch as it was fetched, by a
plain push: a branch that moved meanwhile refuses it, and nothing is forced.
A push made with GitHub Actions' own token starts no CI, so the workflow
that runs this gives it a token of its own.

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract); `--json` gives the same report as one JSON object.

Exit codes, the kernel's: 0 nothing needs a person (empty, or every
conflict settled); 42 one does (populated); 2 refused (a bad command line,
a pull request list that won't read, or git that can't fetch).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "restack"))
import kernel  # noqa: E402
import restack as rs  # noqa: E402

NAME = "restack-open"
USAGE = "usage: restack_open.py (--repo OWNER/NAME | --prs FILE) [--push] [--json]"
REMOTE = "origin"
GROUPS = ("for a person", "merged up", "left as they are")


def git(*argv: str, ok=(0,)) -> subprocess.CompletedProcess:
    got = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)
    if got.returncode not in ok:
        raise RuntimeError(f"git {' '.join(argv[:2])}: {(got.stderr or got.stdout).strip()[:200]}")  # fmt: skip
    return got


def open_pulls(opts: dict) -> list[dict]:
    """The open pull requests, as GitHub's pulls API lists them."""
    if "--prs" in opts:
        got = json.loads(Path(opts["--prs"]).read_text(encoding="utf-8"))
    else:
        out = subprocess.run(
            ["gh", "api", "--paginate", f"repos/{opts['--repo']}/pulls?state=open&per_page=100"],
            capture_output=True, text=True,
        )  # fmt: skip
        if out.returncode != 0:
            raise ValueError(f"gh couldn't list the pull requests: {out.stderr.strip()[:200]}")  # fmt: skip
        got = json.loads(out.stdout)
    if not isinstance(got, list):
        raise ValueError("the pull request list isn't a list")
    return got


def left_alone(pr: dict) -> str | None:
    """Why a pull request is never touched, or None."""
    head, base = pr.get("head") or {}, pr.get("base") or {}
    if (head.get("repo") or {}).get("full_name") != (base.get("repo") or {}).get("full_name"):  # fmt: skip
        return "a fork's branch: its author's"
    if str((pr.get("user") or {}).get("login", "")).endswith("[bot]"):
        return "a bot's branch: it rebases its own"
    return None


def conflicts(base: str, head: str) -> bool:
    """Whether the two would conflict merged, by a trial merge that writes no ref."""
    return git("merge-tree", "--write-tree", "--name-only", base, head, ok=(0, 1)).returncode == 1  # fmt: skip


def one(pr: dict, push: bool) -> tuple[str, str]:
    """(its group, what was done) for one open pull request."""
    why = left_alone(pr)
    if why:
        return GROUPS[2], why
    head, base = pr["head"]["ref"], pr["base"]["ref"]
    git("fetch", "-q", REMOTE, f"+refs/heads/{head}:refs/remotes/{REMOTE}/{head}",
        f"+refs/heads/{base}:refs/remotes/{REMOTE}/{base}")  # fmt: skip
    theirs, onto = f"{REMOTE}/{head}", f"{REMOTE}/{base}"
    if not conflicts(onto, theirs):
        return GROUPS[2], f"merges clean into {base}"
    local = f"restack-open/{pr['number']}"
    git("branch", "-f", local, theirs)
    try:
        try:
            code, lines = rs.restack(local, onto)
        except rs.Stop as stop:
            return GROUPS[0], str(stop)
        if code != kernel.ALIVE:
            return GROUPS[0], lines[0].split(": ", 1)[-1]
        said = re.sub(r"^[0-9a-f]+ -> [0-9a-f]+, ", "", lines[0].split(": ", 1)[-1])
        said = said.replace(f"{onto} merged in", f"{base} merged in")
        new = git("rev-parse", local).stdout.strip()
        if not push:
            return GROUPS[
                1
            ], f"{said}: push with git push {REMOTE} {new[:12]}:refs/heads/{head}"
        got = git("push", REMOTE, f"{new}:refs/heads/{head}", ok=(0, 1))
        if got.returncode != 0:
            return GROUPS[
                0
            ], f"{said}, but the push was refused (the branch moved): run it again"
        return GROUPS[1], f"{said}: pushed"
    finally:
        git("branch", "-D", local, ok=(0, 1))


def report(rows: list[tuple[int, str, str, str]]) -> dict:
    count = {g: sum(r[2] == g for r in rows) for g in GROUPS}
    said = (f"{len(rows)} open; {count[GROUPS[1]]} merged up, {count[GROUPS[0]]} for a person"
            if rows else "no open pull request")  # fmt: skip
    groups = [{"name": g, "rows": [{"where": f"#{n}  {ref}", "what": what}
                                   for n, ref, grp, what in rows if grp == g]}
              for g in GROUPS]  # fmt: skip
    return {"addon": NAME, "state": "populated" if count[GROUPS[0]] else "empty",
            "said": said, "groups": [g for g in groups if g["rows"]]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    flags = {"--push", "--json"}
    on = {a for a in argv if a in flags}
    rest = [a for a in argv if a not in flags]
    opts = dict(zip(rest[0::2], rest[1::2]))
    if len(rest) != 2 or len(opts) != 1 or not set(opts) <= {"--repo", "--prs"}:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        pulls = open_pulls(opts)
        rows = []
        for pr in sorted(pulls, key=lambda p: p.get("number", 0)):
            group, what = one(pr, "--push" in on)
            rows.append(
                (pr.get("number", 0), pr.get("head", {}).get("ref", "?"), group, what)
            )
    except (OSError, ValueError, KeyError, RuntimeError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    doc = report(rows)
    print(json.dumps(doc, ensure_ascii=False) if "--json" in on else report_text(doc))
    return kernel.ESCALATE if doc["state"] == "populated" else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
