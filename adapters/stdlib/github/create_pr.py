"""create_pr.py: this branch's pull request, opened by a stack of the repo's
own add-ons, stopping only where a person is needed. Python 3.9+.

    python adapters/stdlib/github/create_pr.py [--base BRANCH] [--title TEXT]
                                               [--footer TEXT] [--repo OWNER/NAME]
                                               [--steps FILE]

Commit your change, with its CHANGELOG.md entry, then run it. The steps are
create_pr.md beside it (`--steps` names another): a stack, the same file
the stack add-on reads, run in order rather than composed, stopping at the
first step that doesn't come back clean. Then it pushes the branch, opens
the pull request (or finds the one already open for it), writes its number
into the entry, pushes again, and runs the steps that need the number.

The pull request's body is the template's four sections, made from what is
here: the commits' messages; each add-on touched and its card's promises;
what each step printed; and what wasn't checked here, which CI runs.

What it does by itself: a step that leaves files changed (`readme.py
write`, say) is committed as `tidy:`; a branch main moved under is merged
by restack; the number is written in. What it never does: rebase, amend,
or force-push; write anything a step didn't make; approve or merge.

GitHub is asked through `gh api` (REST): the open pull requests, and a new
one. Without gh, the body is left in a file and it says the one command to
run, then run this again. A push or an open GitHub answers with an error (a
502) is tried again, after 2, 4, 8 and 16 seconds, and before each new try
at opening it looks for the pull request, which an error answer can still
have made.

Exit codes, the kernel's: 0 the pull request is open and has everything
pushed; 42 something needs you (a step that failed or stopped, a missing
changelog entry, a branch origin has moved, gh not here): it says what;
2 refused (a bad command line, not on a branch, the base branch itself,
uncommitted changes, nothing to open).
"""

from __future__ import annotations

import importlib.util
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

STEPS = HERE / "create_pr.md"
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
#: the pool whose steps need the pull request's number
AFTER = "after it opens"
#: a step's 42 that owes nothing: said in the pull request, not stopped on
FINE_42 = {"restack", "test-impact.impact", "against", "ci.realdata"}
#: a line that stops a step which exited 0: (step, the line's start, why)
STOP_ON = {
    "against": (
        "collides:",
        "it collides with another open pull request: merge that one's branch"
        " in and base on it (CONTRIBUTING.md, Pull requests)",
    )
}
#: the template's sections, in its order
SECTIONS = (
    "What this changes, and why",
    "Its promises",
    "Evidence",
    "What you didn't check",
)
#: a commit made here is the run's own, not the change's
MINE = re.compile(r"^(tidy: |changelog: its number )")
TRAILER = re.compile(r"^(Co-Authored-By|Claude-Session|Signed-off-by): ", re.I)
TAIL = 15


class Stop(Exception):
    """Something a person has to look at: exit 42."""


class Refused(Exception):
    """The command line, or where it was run: exit 2."""


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(*args: str, check: bool = True) -> str:
    got = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and got.returncode != 0:
        raise Stop(f"git {' '.join(args)}: {(got.stderr or got.stdout).strip()}")
    return got.stdout.strip() if got.returncode == 0 else ""


def clean() -> bool:
    return git("status", "--porcelain") == ""


# ── the steps ────────────────────────────────────────────────────────────────
def script_of(name: str) -> Path:
    """`ci.bugs` is adapters/stdlib/ci/bugs.py; `readme` is readme/readme.py
    (a dash in the folder's name is an underscore in the script's)."""
    folder, _, file = name.partition(".")
    path = STDLIB / folder / f"{file or folder.replace('-', '_')}.py"
    if not path.is_file():
        raise Refused(f"a step names {name}, and there is no {path.relative_to(ROOT)}")
    return path


def steps(path: Path) -> list[tuple[str, list[tuple[str, list[str]]]]]:
    stack = load("willow_stack_for_create_pr", STDLIB / "stack" / "stack.py")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise Refused(f"can't read {path}: {e}") from e
    pools, error = stack.parse_stack(text)
    if error:
        raise Refused(f"{path.name}: {error}")
    for _, ss in pools:
        for name, _ in ss:
            script_of(name)
    return pools


def fill(args: list[str], fields: dict) -> list[str]:
    out = []
    for a in args:
        if a == "{open}":
            out += fields["open"]
            continue
        for k, v in fields.items():
            if k != "open":
                a = a.replace("{" + k + "}", str(v))
        out.append(a)
    return out


def run_step(name: str, args: list[str], said: list, notes: list) -> None:
    """One step: done, said in `notes`, or Stop. A change it leaves is
    committed as tidy."""
    print(f"\n── {name} {' '.join(args)}", flush=True)
    got = subprocess.run(
        [sys.executable, str(script_of(name)), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (got.stdout + got.stderr).rstrip()
    print(out, flush=True)
    said.append((name, args, got.returncode, out))
    last = out.splitlines()[-1] if out else "(it printed nothing)"
    if got.returncode == kernel.ESCALATE and name in FINE_42:
        # the line that says why (a gate's verdict), not a closing line
        why = [x.strip() for x in out.splitlines() if " unreachable " in f" {x} "]
        notes.append(f"`{name}` came back 42: {'; '.join(why) or last}")
    elif got.returncode != kernel.ALIVE:
        raise Stop(f"{name} exited {got.returncode}: {last}")
    stop = STOP_ON.get(name)
    if stop and any(line.startswith(stop[0]) for line in out.splitlines()):
        raise Stop(f"{name}: {stop[1]}")
    if not clean():
        git("add", "-A")
        git("commit", "-q", "-m", f"tidy: made again by {name} {' '.join(args)}")
        print(f"(committed what {name} made, as tidy)")


# ── the changelog ────────────────────────────────────────────────────────────
def changed(base: str) -> list[str]:
    return [f for f in git("diff", "--name-only", f"{base}...HEAD").split("\n") if f]


def owes_an_entry(base: str) -> bool:
    """Anything beyond Markdown and CITATION.cff owes one, as changelog.py says."""
    return any(not f.endswith(".md") and f != "CITATION.cff" for f in changed(base))


def new_entries(base: str) -> list[tuple[int, int]]:
    """(first line, last line) of each `## Unreleased` entry this branch
    added, 0-based, in CHANGELOG.md as it is now. An entry is a `- ` line and
    the indented lines that wrap it, as changelog.py reads them."""
    log = load("willow_changelog_for_create_pr", STDLIB / "ci" / "changelog.py")
    old = set(log.unreleased(git("show", f"{base}:CHANGELOG.md", check=False)))
    lines = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n")
    spans, heading, inside, start = [], "", False, None
    for i, line in enumerate(lines + ["## end"]):
        wraps = start is not None and line.startswith("  ") and bool(line.strip())
        if start is not None and not wraps:
            text = " ".join(x.strip() for x in lines[start:i])[2:]
            if (heading, text) not in old:
                spans.append((start, i - 1))
            start = None
        if line.startswith("## "):
            inside = line.strip() == "## Unreleased"
        elif inside and line.startswith("### "):
            heading = line[4:].strip()
        elif inside and line.startswith("- "):
            start = i
    return spans


def write_number(base: str, number: int) -> bool:
    """`(#N)` at the end of each entry this branch added that has no number;
    True when the file changed. One that names another number is Stop."""
    path = ROOT / "CHANGELOG.md"
    lines = path.read_text(encoding="utf-8").split("\n")
    moved = False
    for _, end in new_entries(base):
        m = re.search(r"\(#(\d+)\)\s*$", lines[end])
        if m and int(m.group(1)) != number:
            raise Stop(
                f"CHANGELOG.md line {end + 1} names #{m.group(1)}, not #{number}"
            )
        if not m:
            lines[end] = f"{lines[end].rstrip()} (#{number})"
            moved = True
    if moved:
        path.write_text("\n".join(lines), encoding="utf-8")
    return moved


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


def open_prs(slug: str) -> list[dict]:
    code, out = gh("api", f"repos/{slug}/pulls?state=open&per_page=100")
    if code != 0:
        raise Stop(f"couldn't list {slug}'s open pull requests: {out}")
    return [p for p in json.loads(out) if (p.get("head") or {}).get("repo")]


# ── the body ─────────────────────────────────────────────────────────────────
def commits(base: str) -> list[tuple[str, str]]:
    """(subject, body) of the change's own commits, oldest first, trailers
    and the run's own tidy and number commits left out."""
    raw = git(
        "log", "--reverse", "--no-merges", "--format=%s%x00%b%x1e", f"{base}..HEAD"
    )
    out = []
    for rec in raw.split("\x1e"):
        if not rec.strip():
            continue
        subject, _, body = rec.strip("\n").partition("\x00")
        if MINE.match(subject):
            continue
        body = "\n".join(x for x in body.strip().split("\n") if not TRAILER.match(x))
        out.append((subject, body.strip()))
    return out


def promises(base: str) -> list[str]:
    seen, out = set(), []
    for f in changed(base):
        m = re.match(r"adapters/(stdlib|deps)/([^/]+)/", f)
        if not m or m.group(2) in seen:
            continue
        seen.add(m.group(2))
        card = ROOT / m.group(0) / "README.md"
        head = (
            card.read_text(encoding="utf-8").split("-->")[0] if card.is_file() else ""
        )
        field = {
            k: v.strip() for k, v in re.findall(r"^(writes|network): (.*)$", head, re.M)
        }
        out.append(f"- `{m.group(2)}`: writes {field.get('writes', '(no card)')};"
                   f" network {field.get('network', '(no card)')}")  # fmt: skip
    return out


def body(base: str, said: list, notes: list, footer: str) -> str:
    what = "\n\n".join(f"**{s}**" + (f"\n\n{b}" if b else "") for s, b in commits(base))
    kept = promises(base)
    evidence = "\n\n".join(
        f"`{name} {' '.join(args)}`: exit {code}\n\n```\n"
        + "\n".join(out.splitlines()[-TAIL:])
        + "\n```"
        for name, args, code, out in said
    )
    left = notes + [
        "Every gate this change doesn't reach here runs in CI on this pull request."
    ]
    parts = [
        (SECTIONS[0], what or "(no commit message says)"),
        (SECTIONS[1], "\n".join(kept) or "It touches no add-on."),
        (SECTIONS[2], f"Made by create_pr.py, on {git('rev-parse', '--short', 'HEAD')}:\n\n{evidence}"),
        (SECTIONS[3], "\n".join(f"- {n}" for n in left)),
    ]  # fmt: skip
    text = "\n\n".join(f"## {h}\n\n{t}" for h, t in parts)
    return text + (f"\n\n{footer}" if footer else "") + "\n"


# ── the run ──────────────────────────────────────────────────────────────────
def args_of(argv: list[str]) -> dict:
    opts = {
        "--base": "main",
        "--title": "",
        "--footer": "",
        "--repo": "",
        "--steps": str(STEPS),
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
            prs = open_prs(slug)
        except Stop:
            continue
        found = next((p for p in prs if p["head"]["ref"] == branch and p["head"]["repo"]["full_name"] == slug), None)  # fmt: skip
        if found is not None:
            print(f"#{found['number']} is open after all", file=sys.stderr)
            return found, out
    return None, out


def create(opts: dict) -> int:
    base_name = opts["--base"]
    pools = steps(Path(opts["--steps"]))
    branch = git("symbolic-ref", "-q", "--short", "HEAD", check=False)
    if not branch:
        raise Refused("not on a branch: check out the one to open")
    if branch == base_name:
        raise Refused(
            f"on {base_name} itself: a pull request comes from a branch of its own"
        )
    if not clean():
        raise Refused("uncommitted changes: commit the change, entry and all, first")
    slug = opts["--repo"] or slug_of(git("remote", "get-url", "origin"))
    git(
        "fetch",
        "-q",
        "origin",
        f"+refs/heads/{base_name}:refs/remotes/origin/{base_name}",
    )
    base = f"origin/{base_name}"
    if git("rev-list", "--count", f"{base}..HEAD") == "0":
        raise Refused(f"{branch} holds nothing {base} doesn't: nothing to open")
    if owes_an_entry(base) and not new_entries(base):
        raise Stop("CHANGELOG.md has no new entry under ## Unreleased: write one"
                   " (Added, Changed, Fixed or Removed), commit it, run this again")  # fmt: skip

    prs = open_prs(slug)
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
            others.append(f"origin/{ref}")
    said, notes = [], []
    with tempfile.TemporaryDirectory() as scratch:
        fields = {"base": base, "branch": branch, "scratch": scratch, "open": others}
        for heading, ss in pools:
            if heading == AFTER:
                continue
            for name, args in ss:
                run_step(name, fill(args, fields), said, notes)

        push(branch)
        if mine is None:
            payload = Path(scratch) / "pull.json"
            payload.write_text(json.dumps({
                "title": opts["--title"] or (commits(base) or [(branch, "")])[0][0],
                "head": branch, "base": base_name,
                "body": body(base, said, notes, opts["--footer"]),
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

        if write_number(base, number):
            git("add", "CHANGELOG.md")
            git("commit", "-q", "-m", f"changelog: its number (#{number})")
            print(f"wrote #{number} into its changelog entry")
        fields["pr"] = number
        for heading, ss in pools:
            if heading == AFTER:
                for name, args in ss:
                    run_step(name, fill(args, fields), said, notes)
        push(branch)
    print(f"\n#{number} is open, everything pushed: {mine.get('html_url', '')}")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    try:
        return create(args_of(argv))
    except Refused as why:
        print(f"refused: {why}" if str(why) != USAGE else USAGE, file=sys.stderr)
        return kernel.REFUSED
    except Stop as why:
        print(f"\nstopped: {why}", file=sys.stderr)
        return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
