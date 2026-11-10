"""create_pr.py: this branch's pull request on GitHub, made ready by the
repo's own add-ons, stopping only where a person is needed. Python 3.9+.

    python adapters/stdlib/github/create_pr.py [--base BRANCH] [--title TEXT]
                                               [--footer TEXT] [--repo OWNER/NAME]
                                               [--steps FILE]

Commit your change, with its changelog entry (changes/+<branch>.<kind>.md,
changes/README.md says how), then run it. Everything that needs no host is
ready's (adapters/stdlib/ready): its `check`, then its `run` of the steps
(ready/steps.md, or `--steps`), held to the other open pull requests, then
its `body`. This adds GitHub's part around them: the open pull requests to
hold the branch to, the push, the pull request opened (or the one already
open for it found), then ready's `opened` with its number, and the push
again.

What it never does: rebase, amend, or force-push; write a file; approve or
merge.

GitHub is asked through `gh api` (REST): the open pull requests, and a new
one. Without gh it stops before anything runs, and says the commands that
do the same by hand. A push or an open GitHub answers with an error (a 502)
is tried again, after 2, 4, 8 and 16 seconds, and before each new try at
opening it looks for the pull request, which an error answer can still have
made.

Exit codes, the kernel's: 0 the pull request is open and has everything
pushed; 42 something needs you (a step that failed or stopped, a missing
changelog entry, a branch origin has moved, gh not here): it says what;
2 refused (a bad command line, or ready's check refused it: not on a
branch, the base branch itself, uncommitted changes, nothing to open).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STDLIB = ROOT / "adapters" / "stdlib"
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

READY = STDLIB / "ready" / "ready.py"
USAGE = (
    "usage: create_pr.py [--base BRANCH] [--title TEXT] [--footer TEXT]"
    " [--repo OWNER/NAME] [--steps FILE]"
)
#: seconds between tries when GitHub answers a push or an open with an error
#: (a 502, "fatal error in commit_refs"): the push may yet go through, and the
#: pull request may be open though the answer said not. WILLOW_CREATE_PR_WAITS
#: (seconds, by commas) sets them; its tests set none.
WAITS = tuple(
    float(w)
    for w in os.environ.get("WILLOW_CREATE_PR_WAITS", "2,4,8,16").split(",")
    if w.strip()
)


class Stop(Exception):
    """Something a person has to look at: exit 42."""


class Refused(Exception):
    """The command line, or where it was run: exit 2."""


class Passed(Exception):
    """ready said no and already said why: its exit code, as it gave it."""


def git(*args: str, check: bool = True) -> str:
    got = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and got.returncode != 0:
        raise Stop(f"git {' '.join(args)}: {(got.stderr or got.stdout).strip()}")
    return got.stdout.strip() if got.returncode == 0 else ""


def ready(*args: str, capture: bool = False) -> str:
    """ready.py with these args, its output passed through (or kept, with
    `capture`); a refusal or a stop is passed on with ready's own exit code."""
    got = subprocess.run([sys.executable, str(READY), *args], cwd=ROOT,
                         capture_output=capture, text=True)  # fmt: skip
    if got.returncode != kernel.ALIVE:
        if capture:
            print(got.stderr, end="", file=sys.stderr)
        raise Passed(got.returncode)
    return got.stdout if capture else ""


# ── GitHub ───────────────────────────────────────────────────────────────────
def gh(*args: str) -> tuple[int, str]:
    if shutil.which("gh") is None:
        return -1, "gh isn't installed"
    got = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    return got.returncode, (got.stdout if got.returncode == 0 else got.stderr).strip()


def slug_of(remote: str) -> str:
    """owner/name from origin's address, https or ssh, with a proxy in front
    or not: its last two path parts."""
    parts = re.split(r"[/:]", remote.strip().removesuffix("/").removesuffix(".git"))
    if len(parts) < 2 or not all(parts[-2:]):
        raise Refused(f"can't tell owner/name from origin ({remote}): give --repo")
    return "/".join(parts[-2:])


def by_hand(base: str) -> str:
    return ("by hand: python adapters/stdlib/ready/ready.py run --base"
            f" {base} --open <each open branch> --to FILE; ready.py body --base {base}"
            " --from FILE; push and open it; ready.py opened --base"
            f" {base} --pr <its number>; push again")  # fmt: skip


def open_prs(slug: str, base: str) -> list[dict]:
    code, out = gh("api", f"repos/{slug}/pulls?state=open&per_page=100")
    if code != 0:
        raise Stop(f"couldn't list {slug}'s open pull requests: {out}. {by_hand(base)}")
    return [p for p in json.loads(out) if (p.get("head") or {}).get("repo")]


def args_of(argv: list[str]) -> dict:
    opts = {
        "--base": "main",
        "--title": "",
        "--footer": "",
        "--repo": "",
        "--steps": "",
    }
    it = iter(argv)
    for a in it:
        if a not in opts:
            raise Refused(USAGE)
        value = next(it, None)
        if value is None or (value.startswith("--") and value in opts):
            raise Refused(USAGE)
        opts[a] = value
    return opts


def push(branch: str) -> None:
    git(
        "fetch",
        "-q",
        "origin",
        f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
        check=False,
    )
    theirs = git(
        "rev-parse", "-q", "--verify", f"refs/remotes/origin/{branch}", check=False
    )
    behind = subprocess.run(
        ["git", "merge-base", "--is-ancestor", theirs or "HEAD", "HEAD"], cwd=ROOT
    ).returncode
    if theirs and behind:
        raise Stop(f"origin's {branch} has commits this branch doesn't: merge"
                   f" origin/{branch} in, then run this again (never force-push)")  # fmt: skip
    for wait in WAITS:
        try:
            git("push", "-q", "origin", f"HEAD:refs/heads/{branch}")
            return
        except Stop as why:
            print(f"push failed ({why}); again in {wait:g}s", file=sys.stderr)
            time.sleep(wait)
    git("push", "-q", "origin", f"HEAD:refs/heads/{branch}")


def open_pr(slug: str, branch: str, payload: Path) -> tuple[dict | None, str]:
    """(the pull request opened for `branch`, or None when GitHub won't; its
    last answer). An error answer can come for a pull request that was made
    (a 502): it is looked for before trying again, so none is opened twice."""
    for wait in (*WAITS, None):
        code, out = gh("api", f"repos/{slug}/pulls", "--method", "POST",
                       "--input", str(payload))  # fmt: skip
        if code == 0:
            return json.loads(out), out
        if wait is None:
            return None, out
        print(f"opening it failed ({out}); looking again in {wait:g}s", file=sys.stderr)
        time.sleep(wait)
        try:
            prs = open_prs(slug, "")
        except Stop:
            continue
        found = next((p for p in prs if p["head"]["ref"] == branch and p["head"]["repo"]["full_name"] == slug), None)  # fmt: skip
        if found is not None:
            print(f"#{found['number']} is open after all", file=sys.stderr)
            return found, out
    return None, out


def title_of(base: str, branch: str) -> str:
    """The change's first own commit's subject, as ready's body reads them."""
    for subject in git("log", "--reverse", "--no-merges", "--format=%s", f"{base}..HEAD").split("\n"):  # fmt: skip
        if subject and not re.match(r"^(tidy: |changelog: its number )", subject):
            return subject
    return branch


def create(opts: dict) -> int:
    base_name = opts["--base"]
    steps = ["--steps", opts["--steps"]] if opts["--steps"] else []
    ready("steps", *steps, capture=True)  # a step naming no add-on here: refused
    slug = opts["--repo"] or slug_of(git("remote", "get-url", "origin"))
    git(
        "fetch",
        "-q",
        "origin",
        f"+refs/heads/{base_name}:refs/remotes/origin/{base_name}",
    )
    base = f"origin/{base_name}"
    ready("check", "--base", base, capture=True)
    branch = git("symbolic-ref", "-q", "--short", "HEAD")

    prs = open_prs(slug, base)
    mine = next((p for p in prs if p["head"]["ref"] == branch and p["head"]["repo"]["full_name"] == slug), None)  # fmt: skip
    others = []
    for p in prs:
        ref = p["head"]["ref"]
        if p is mine or p["head"]["repo"]["full_name"] != slug:
            continue
        git(
            "fetch",
            "-q",
            "origin",
            f"+refs/heads/{ref}:refs/remotes/origin/{ref}",
            check=False,
        )
        if git(
            "rev-parse", "-q", "--verify", f"refs/remotes/origin/{ref}", check=False
        ):
            others += ["--open", f"origin/{ref}"]
    with tempfile.TemporaryDirectory() as scratch:
        record = str(Path(scratch) / "record.json")
        ready("run", "--base", base, *others, *steps, "--to", record)

        push(branch)
        if mine is None:
            payload = Path(scratch) / "pull.json"
            text = ready("body", "--base", base, "--from", record,
                         *(["--footer", opts["--footer"]] if opts["--footer"] else []),
                         capture=True)  # fmt: skip
            payload.write_text(json.dumps({
                "title": opts["--title"] or title_of(base, branch),
                "head": branch, "base": base_name, "body": text,
            }), encoding="utf-8")  # fmt: skip
            mine, out = open_pr(slug, branch, payload)
            if mine is None:
                kept = Path(tempfile.mkdtemp(prefix="create_pr-")) / "pull.json"
                kept.write_text(payload.read_text(encoding="utf-8"), encoding="utf-8")
                raise Stop(f"couldn't open it ({out}, after {len(WAITS) + 1} tries). Pushed; the pull request is in {kept}:"
                           f" open it with `gh api repos/{slug}/pulls --method POST --input"
                           f" {kept}` (or by hand), then run this again")  # fmt: skip
            print(f"\nopened #{mine['number']}: {mine.get('html_url', '')}")
        else:
            print(
                f"\n#{mine['number']} is already open for {branch}: {mine.get('html_url', '')}"
            )
        number = int(mine["number"])
        ready("opened", "--base", base, "--pr", str(number), *steps, "--to", record)
        push(branch)
    print(f"\n#{number} is open, everything pushed: {mine.get('html_url', '')}")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    try:
        return create(args_of(argv))
    except Passed as code:
        return code.args[0]
    except Refused as why:
        print(f"refused: {why}" if str(why) != USAGE else USAGE, file=sys.stderr)
        return kernel.REFUSED
    except Stop as why:
        print(f"\nstopped: {why}", file=sys.stderr)
        return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
