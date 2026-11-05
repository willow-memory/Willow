"""create_pr.py, in a small repo of its own: a bare origin beside it, steps
that are a script told what to exit, and a gh that answers from a file. The
guard is pointed at that repo, so its writes are held to the real card."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("create_pr", HERE / "create_pr.py")
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)

#: no waits between tries: a test isn't GitHub, and doesn't need a second
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "WILLOW_CREATE_PR_WAITS": "0,0,0"}  # fmt: skip
CHANGELOG = """# Changelog

## Unreleased

### Added

- `old`, from before. (#1)

## v0.1.0 · 2026-10-23

- the first. (#0)
"""
#: a step: exits with its first word, prints the rest, and makes the files
#: named make=PATH (as readme.py write makes ADDONS.md)
SAY = """import sys
from pathlib import Path
code, *words = sys.argv[1:]
for w in words:
    if w.startswith("make="):
        Path(w[5:]).write_text("made\\n", encoding="utf-8")
print(" ".join(words).replace(" / ", "\\n") or "(nothing)")
sys.exit(int(code))
"""
#: gh, answering `api` from gh.json: the open pull requests, and a new one
GH = """import json, os, sys
from pathlib import Path
state = Path(os.environ["FAKE_GH"])
s = json.loads(state.read_text())
s["calls"].append(sys.argv[1:])
state.write_text(json.dumps(s))
if os.environ.get("FAKE_GH_FAIL"):
    print("HTTP 403: Resource not accessible", file=sys.stderr)
    sys.exit(1)
# a 502 on the first open: made (FAKE_GH_502=made, as GitHub did for #236) or not
bad = os.environ.get("FAKE_GH_502") and not [c for c in s["calls"][:-1] if "POST" in c]
if "POST" in sys.argv and bad and os.environ["FAKE_GH_502"] != "made":
    print("gh: Server Error (HTTP 502)", file=sys.stderr)
    sys.exit(1)
if "POST" in sys.argv:
    sent = json.loads(Path(sys.argv[sys.argv.index("--input") + 1]).read_text())
    pr = {"number": 7, "html_url": "https://example.test/o/r/pull/7",
          "head": {"ref": sent["head"], "repo": {"full_name": "o/r"}}, "sent": sent}
    s["prs"].append(pr)
    state.write_text(json.dumps(s))
    if bad:
        print("gh: Server Error (HTTP 502)", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(pr))
else:
    print(json.dumps(s["prs"]))
"""


def git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=cwd, env=ENV, check=True,
                          capture_output=True, text=True).stdout.strip()  # fmt: skip


def card(writes: str) -> str:
    return (f"<!-- willow-addon\nsection: For maintainers\nline: A step.\nsource: new\n"
            f"added: 2026-11-04\nwrites: {writes}\nnetwork: none\n-->\n# step\n")  # fmt: skip


@pytest.fixture
def repo(tmp_path):
    """The repo, on branch `work` one commit past origin's main: a code file
    and its changelog entry. Its steps are written by each test."""
    r = tmp_path / "repo"
    for rel in ("kernel.py", "adapters/stdlib/stack/stack.py", "adapters/stdlib/ci/changelog.py",
                "adapters/stdlib/github/create_pr.py", "adapters/stdlib/github/README.md"):  # fmt: skip
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, r / rel)
    for name, writes in (("say", "made.txt"), ("against", "nothing")):
        (r / f"adapters/stdlib/{name}").mkdir(parents=True)
        (r / f"adapters/stdlib/{name}/{name}.py").write_text(SAY, encoding="utf-8")
        (r / f"adapters/stdlib/{name}/README.md").write_text(
            card(writes), encoding="utf-8"
        )
    (r / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (r / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", str(origin))
    git(r.parent, "init", "-q", "-b", "main", str(r))
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "the repo")
    git(r, "remote", "add", "origin", str(origin))
    git(r, "push", "-q", "origin", "main")
    git(r, "checkout", "-q", "-b", "work")
    (r / "thing.py").write_text("x = 1\n", encoding="utf-8")
    log = r / "CHANGELOG.md"
    log.write_text(log.read_text().replace("### Added\n\n", "### Added\n\n- `thing`, a new\n  thing.\n", 1))  # fmt: skip
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "thing: a new thing\n\nBecause it was missing.\n\nCo-Authored-By: x <x@x>")  # fmt: skip
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "gh").write_text(f"#!{sys.executable}\n" + GH, encoding="utf-8")
    (bin_ / "gh").chmod(0o755)
    (tmp_path / "gh.json").write_text(json.dumps({"prs": [], "calls": []}))
    return r


def steps(repo: Path, text: str) -> None:
    (repo / "steps.md").write_text(text, encoding="utf-8")
    (repo / ".git" / "info" / "exclude").write_text("steps.md\n", encoding="utf-8")


GREEN = """## made
- say -- 0 made it make=made.txt
## checked
- say -- 0 all good
## held
- against -- 0 {open}
## after it opens
- say -- 0 numbered {pr}
"""


def run(
    repo: Path, *argv: str, gh: bool = True, **env: str
) -> subprocess.CompletedProcess:
    """create_pr.py in the repo, with the fake gh first on PATH; with gh=False,
    a PATH holding git alone, so no gh this machine has (GitHub's runners
    keep one in /usr/bin) can answer."""
    if gh:
        path = str(repo.parent / "bin") + os.pathsep + ENV["PATH"]
    else:
        bare = repo.parent / "git-only"
        bare.mkdir(exist_ok=True)
        if not (bare / "git").exists():
            (bare / "git").symlink_to(shutil.which("git"))
        path = str(bare)
    e = {**ENV, "PATH": path, "FAKE_GH": str(repo.parent / "gh.json"),
         "WILLOW_GUARD_ROOT": str(repo), **env}  # fmt: skip
    script = repo / "adapters/stdlib/github/create_pr.py"
    return subprocess.run([sys.executable, str(script), "--repo", "o/r", "--steps",
                           str(repo / "steps.md"), *argv], cwd=repo, env=e,
                          capture_output=True, text=True)  # fmt: skip


def gh_state(repo: Path) -> dict:
    return json.loads((repo.parent / "gh.json").read_text())


def at_origin(repo: Path, path: str, branch: str = "work") -> str:
    git(repo, "fetch", "-q", "origin")
    return git(repo, "show", f"origin/{branch}:{path}")


# ── refused ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("argv", [["--base"], ["--stray", "x"], ["--title", "--base"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run([sys.executable, str(HERE / "create_pr.py"), *argv],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "create_pr.py" in got.stderr


def test_the_base_branch_uncommitted_work_or_nothing_new_is_refused(repo):
    steps(repo, GREEN)
    (repo / "thing.py").write_text("x = 2\n")
    got = run(repo)
    assert got.returncode == 2 and "uncommitted changes" in got.stderr
    git(repo, "checkout", "-q", "--", "thing.py")
    git(repo, "checkout", "-q", "main")
    got = run(repo)
    assert got.returncode == 2 and "on main itself" in got.stderr
    git(repo, "checkout", "-q", "-b", "empty")
    got = run(repo)
    assert got.returncode == 2 and "nothing origin/main doesn't" in got.stderr
    assert gh_state(repo)["calls"] == [], "refused before asking GitHub anything"


def test_a_step_naming_an_add_on_that_isnt_here_is_refused(repo):
    steps(repo, "## s\n- nowhere -- 0\n")
    got = run(repo)
    assert got.returncode == 2 and "adapters/stdlib/nowhere/nowhere.py" in got.stderr


# ── opened ───────────────────────────────────────────────────────────────────
def test_green_steps_open_it_with_its_body_and_number_and_push_it_all(repo):
    steps(repo, GREEN)
    got = run(repo, "--footer", "made by a test")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "opened #7" in got.stdout and "numbered 7" in got.stdout
    posts = [c for c in gh_state(repo)["calls"] if "POST" in c]
    assert len(posts) == 1
    sent = gh_state(repo)["prs"][0]["sent"]
    assert (sent["title"], sent["head"], sent["base"]) == (
        "thing: a new thing",
        "work",
        "main",
    )
    template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
    assert re.findall(r"^## (.+)$", sent["body"], re.M) == re.findall(
        r"^## (.+)$", template, re.M
    )
    assert (
        "Because it was missing." in sent["body"]
        and "Co-Authored-By" not in sent["body"]
    )
    assert "It touches no add-on." in sent["body"] and "say 0 all good" in sent["body"]
    assert sent["body"].rstrip().endswith("made by a test")
    log = at_origin(repo, "CHANGELOG.md")
    assert (
        "- `thing`, a new\n  thing. (#7)\n" in log
        and "- `old`, from before. (#1)" in log
    )
    subjects = git(repo, "log", "--format=%s", "origin/work").splitlines()
    assert subjects[:3] == ["changelog: its number (#7)",
                            "tidy: made again by say 0 made it make=made.txt",
                            "thing: a new thing"]  # fmt: skip
    assert at_origin(repo, "made.txt") == "made"


def test_run_again_it_finds_its_pull_request_and_opens_no_second(repo):
    steps(repo, GREEN)
    assert run(repo).returncode == 0
    again = run(repo)
    assert again.returncode == 0, again.stdout + again.stderr
    assert "#7 is already open for work" in again.stdout
    assert len([c for c in gh_state(repo)["calls"] if "POST" in c]) == 1
    assert (
        git(repo, "log", "-1", "--format=%s", "origin/work")
        == "changelog: its number (#7)"
    )


def test_the_other_open_pull_requests_are_what_against_is_held_to(repo):
    git(repo, "push", "-q", "origin", "main:refs/heads/theirs")
    s = gh_state(repo)
    s["prs"] = [{"number": 3, "head": {"ref": "theirs", "repo": {"full_name": "o/r"}}},
                {"number": 4, "head": {"ref": "fork", "repo": {"full_name": "x/r"}}}]  # fmt: skip
    (repo.parent / "gh.json").write_text(json.dumps(s))
    steps(repo, GREEN)
    got = run(repo)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "── against 0 origin/theirs\n" in got.stdout, "a fork's branch isn't fetched"


# ── stopped ──────────────────────────────────────────────────────────────────
def test_a_step_that_needs_you_stops_it_before_anything_is_pushed(repo):
    steps(repo, "## checked\n- say -- 42 a gate is red\n" + GREEN)
    got = run(repo)
    assert got.returncode == 42
    assert "stopped: say exited 42: a gate is red" in got.stderr
    assert git(repo, "ls-remote", "origin", "work") == ""
    assert gh_state(repo)["prs"] == []


def test_a_42_that_owes_nothing_is_said_in_the_pull_request_and_it_goes_on(repo):
    steps(
        repo, GREEN.replace("- against -- 0 {open}", "- against -- 42 nothing to check")
    )
    got = run(repo)
    assert got.returncode == 0, got.stdout + got.stderr
    sent = gh_state(repo)["prs"][0]["sent"]
    assert "`against` came back 42: nothing to check" in sent["body"]


def test_a_42_is_said_by_the_line_that_says_why_not_its_last(repo):
    steps(repo, GREEN.replace("- against -- 0 {open}",
                              "- against -- 42 ports:java  unreachable  (no java) / run it in CI"))  # fmt: skip
    got = run(repo)
    assert got.returncode == 0, got.stdout + got.stderr
    body = gh_state(repo)["prs"][0]["sent"]["body"]
    assert "`against` came back 42: ports:java unreachable (no java)" in body
    assert "run it in CI" not in body.split("## What you didn't check")[1]


def test_a_collision_stops_it_though_against_exits_0(repo):
    steps(
        repo,
        GREEN.replace("- against -- 0 {open}", "- against -- 0 collides: x.py with #3"),
    )
    got = run(repo)
    assert (
        got.returncode == 42 and "collides with another open pull request" in got.stderr
    )


def test_a_change_with_no_changelog_entry_stops_and_docs_alone_owe_none(repo):
    steps(repo, GREEN)
    git(repo, "checkout", "-q", "-b", "bare", "main")
    (repo / "other.py").write_text("y = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "other: no entry")
    got = run(repo)
    assert got.returncode == 42 and "no new entry under ## Unreleased" in got.stderr
    git(repo, "checkout", "-q", "-b", "docs", "main")
    (repo / "NOTES.md").write_text("words\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs: words")
    got = run(repo)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "(#7)" not in at_origin(repo, "CHANGELOG.md", "docs")


def test_origin_moved_on_is_stopped_on_never_force_pushed(repo):
    steps(repo, GREEN)
    git(repo, "push", "-q", "origin", "main:refs/heads/work")
    git(
        repo.parent,
        "clone",
        "-q",
        "-b",
        "work",
        str(repo.parent / "origin.git"),
        "other",
    )
    (repo.parent / "other" / "z.txt").write_text("theirs\n")
    git(repo.parent / "other", "add", "-A")
    git(repo.parent / "other", "commit", "-q", "-m", "someone else's")
    git(repo.parent / "other", "push", "-q", "origin", "work")
    got = run(repo)
    assert got.returncode == 42 and "never force-push" in got.stderr
    assert at_origin(repo, "z.txt") == "theirs"


def test_github_out_of_reach_stops_it_before_anything_is_pushed(repo):
    steps(repo, GREEN)
    got = run(repo, FAKE_GH_FAIL="1")
    assert (
        got.returncode == 42 and "couldn't list o/r's open pull requests" in got.stderr
    )
    got = run(repo, gh=False)
    assert got.returncode == 42 and "gh isn't installed" in got.stderr
    assert git(repo, "ls-remote", "origin", "work") == ""


def test_a_git_that_fails_is_stopped_on_with_what_git_said(repo):
    steps(repo, GREEN)
    git(repo, "remote", "set-url", "origin", str(repo.parent / "nowhere.git"))
    got = run(repo)
    assert got.returncode == 42 and "stopped: git fetch" in got.stderr
    assert "nowhere.git" in got.stderr, "git's own reason, not an empty one"


@pytest.mark.parametrize("made", ["made", "not made"])
def test_a_502_on_opening_is_looked_past_and_never_opens_a_second(repo, made):
    """GitHub answered #236's open with a 502 and opened it anyway: the
    run stopped, and a rerun did every gate again to find it."""
    steps(repo, GREEN)
    got = run(repo, FAKE_GH_502=made)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "HTTP 502" in got.stderr and "numbered 7" in got.stdout
    posts = [c for c in gh_state(repo)["calls"] if "POST" in c]
    assert len(gh_state(repo)["prs"]) == 1
    assert len(posts) == (1 if made == "made" else 2)
    assert ("#7 is open after all" in got.stderr) == (made == "made")
    assert "(#7)" in at_origin(repo, "CHANGELOG.md")


def test_a_push_github_turns_away_once_is_tried_again(repo):
    """'fatal error in commit_refs': a push GitHub failed, that went through
    on the next try."""
    steps(repo, GREEN)
    hook = repo.parent / "origin.git" / "hooks" / "pre-receive"
    once = repo.parent / "turned-away"
    hook.write_text(f"#!/bin/sh\n[ -e '{once}' ] && exit 0\ntouch '{once}'\n"
                    "echo 'fatal error in commit_refs' >&2\nexit 1\n")  # fmt: skip
    hook.chmod(0o755)
    got = run(repo)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "push failed" in got.stderr and "commit_refs" in got.stderr
    assert "(#7)" in at_origin(repo, "CHANGELOG.md")


def test_a_failed_open_keeps_the_body_and_says_the_command(repo):
    steps(repo, GREEN)
    gh = repo.parent / "bin" / "gh"
    gh.write_text(gh.read_text().replace('if "POST" in sys.argv:',
                  'if "POST" in sys.argv:\n    print("HTTP 422", file=sys.stderr); sys.exit(1)\nif False:'))  # fmt: skip
    got = run(repo)
    assert got.returncode == 42 and "--method POST --input" in got.stderr
    assert "HTTP 422, after 4 tries" in got.stderr, "GitHub's own reason, kept"
    kept = Path(re.search(r"the pull request is in (\S+):", got.stderr).group(1))
    assert json.loads(kept.read_text())["head"] == "work"
    shutil.rmtree(kept.parent)
    assert git(repo, "ls-remote", "origin", "work") != "", "pushed before it tried"


# ── the pieces ───────────────────────────────────────────────────────────────
def test_the_real_steps_are_a_stack_of_add_ons_that_are_here():
    pools = cp.steps(cp.STEPS)
    names = [n for _, ss in pools for n, _ in ss]
    assert names[0] == "restack" and names[-1] == "ci.changelog"
    assert pools[-1][0] == cp.AFTER and all(h != cp.AFTER for h, _ in pools[:-1])
    assert {"ci.made", "test-impact.impact", "against"} <= set(names)
    assert set(cp.FINE_42) <= set(names) and set(cp.STOP_ON) <= set(names)


def test_owner_and_name_come_from_origin_whatever_its_shape():
    for url in ("https://github.com/willow-memory/Willow.git", "git@github.com:willow-memory/Willow",
                "http://proxy@127.0.0.1:9/git/willow-memory/Willow/"):  # fmt: skip
        assert cp.slug_of(url) == "willow-memory/Willow", url
    with pytest.raises(cp.Refused):
        cp.slug_of("nowhere")


def test_fill_spreads_the_open_branches_and_fills_the_rest():
    fields = {"base": "origin/main", "pr": 7, "open": ["origin/a", "origin/b"]}
    assert cp.fill(["--base", "{base}", "{open}", "#{pr}"], fields) == [
        "--base", "origin/main", "origin/a", "origin/b", "#7"]  # fmt: skip
    assert cp.fill(["{open}"], {**fields, "open": []}) == []
