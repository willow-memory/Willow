"""ready's tests: a copy of the repo's few files it needs, a branch one commit
past main, and steps of a test's own (a `say` add-on that exits with its
first word), run with no host at all."""

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

spec = importlib.util.spec_from_file_location("ready", HERE / "ready.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}  # fmt: skip
#: a step: exits with its first word, prints the rest (" / " a new line), and
#: makes the files named make=PATH
SAY = """import sys
from pathlib import Path
code, *words = sys.argv[1:]
for w in words:
    if w.startswith("make="):
        Path(w[5:]).write_text("made\\n", encoding="utf-8")
print(" ".join(words).replace(" / ", "\\n") or "(nothing)")
sys.exit(int(code))
"""
GREEN = """## made
- say -- 0 made it make=made.txt
## checked
- say -- 0 on {branch} against {base}
## held
- against -- 0 {open}
## after it opens
- say -- 0 numbered {pr}
"""


def git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=cwd, env=ENV, check=True,
                          capture_output=True, text=True).stdout.strip()  # fmt: skip


def card(writes: str) -> str:
    return (f"<!-- willow-addon\nsection: For maintainers\nline: A step.\nsource: new\n"
            f"added: 2026-11-08\nwrites: {writes}\nnetwork: none\n-->\n# step\n")  # fmt: skip


@pytest.fixture
def repo(tmp_path):
    """On branch `work`, one commit past main (as origin/main has it): a code
    file and its fragment, changes/+work.added.md."""
    r = tmp_path / "repo"
    for rel in ("kernel.py", "adapters/stdlib/stack/stack.py",
                "adapters/stdlib/ci/changelog.py", "adapters/stdlib/ready/ready.py",
                "adapters/stdlib/ready/README.md"):  # fmt: skip
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, r / rel)
    for name, writes in (("say", "made.txt"), ("against", "nothing")):
        (r / f"adapters/stdlib/{name}").mkdir(parents=True)
        (r / f"adapters/stdlib/{name}/{name}.py").write_text(SAY, encoding="utf-8")
        (r / f"adapters/stdlib/{name}/README.md").write_text(card(writes), encoding="utf-8")  # fmt: skip
    (r / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (r / "steps.md").write_text(GREEN, encoding="utf-8")
    git(r.parent, "init", "-q", "-b", "main", str(r))
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "the repo")
    git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    git(r, "checkout", "-q", "-b", "work")
    (r / "thing.py").write_text("x = 1\n", encoding="utf-8")
    (r / "changes").mkdir()
    (r / "changes/+work.added.md").write_text("`thing`, a new thing\n", encoding="utf-8")  # fmt: skip
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "thing: a new thing\n\nBecause it was missing.\n\nCo-Authored-By: x <x@x>")  # fmt: skip
    return r


def steps(repo: Path, text: str) -> None:
    (repo / "steps.md").write_text(text, encoding="utf-8")
    git(repo, "commit", "-q", "-am", "steps")


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess:
    """ready.py in the repo, under the guard's root as the repo's own tests are."""
    e = {**ENV, "WILLOW_GUARD_ROOT": str(repo)}
    return subprocess.run([sys.executable, str(repo / "adapters/stdlib/ready/ready.py"), *argv],
                          cwd=repo, env=e, capture_output=True, text=True)  # fmt: skip


def go(repo: Path, verb: str, *argv: str) -> subprocess.CompletedProcess:
    more = ["--steps", str(repo / "steps.md")] if verb in ("run", "opened") else []
    return run(repo, verb, "--base", "origin/main", *more, *argv)


def subjects(repo: Path) -> list[str]:
    return git(repo, "log", "--format=%s", "origin/main..HEAD").splitlines()


# ── refused ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("argv", [
    [], ["go"], ["check"], ["check", "--base"], ["check", "--base", "--base"],
    ["check", "--base", "a", "--stray", "x"], ["check", "--base", "a", "--base", "b"],
    ["body", "--base", "a"], ["opened", "--base", "a", "--pr", "seven"],
    ["steps", "--open", "x"],
])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run([sys.executable, str(HERE / "ready.py"), *argv],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "ready.py" in got.stderr


def test_check_refuses_what_has_nothing_to_open_and_stops_on_a_missing_fragment(repo):
    assert go(repo, "check").returncode == 0
    (repo / "thing.py").write_text("x = 2\n")
    got = go(repo, "check")
    assert got.returncode == 2 and "uncommitted changes" in got.stderr
    git(repo, "checkout", "-q", "--", "thing.py")
    got = run(repo, "check", "--base", "origin/elsewhere")
    assert got.returncode == 2 and "no origin/elsewhere here" in got.stderr
    git(repo, "checkout", "-q", "main")
    got = go(repo, "check")
    assert got.returncode == 2 and "on main itself" in got.stderr
    git(repo, "checkout", "-q", "-b", "empty")
    got = go(repo, "check")
    assert got.returncode == 2 and "nothing origin/main doesn't" in got.stderr
    git(repo, "checkout", "-q", "--detach")
    got = go(repo, "check")
    assert got.returncode == 2 and "not on a branch" in got.stderr
    git(repo, "checkout", "-q", "work")
    git(repo, "rm", "-q", "changes/+work.added.md")
    git(repo, "commit", "-q", "-m", "no entry")
    got = go(repo, "check")
    assert got.returncode == 42 and "changes/+<branch>.<kind>.md" in got.stderr


def test_docs_alone_owe_no_fragment(repo):
    git(repo, "checkout", "-q", "-b", "docs", "main")
    (repo / "NOTES.md").write_text("words\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs: words")
    assert go(repo, "check").returncode == 0


def test_a_step_naming_an_add_on_that_isnt_here_is_refused(repo):
    steps(repo, "## s\n- nowhere -- 0\n")
    got = go(repo, "run")
    assert got.returncode == 2 and "adapters/stdlib/nowhere/nowhere.py" in got.stderr


# ── run ──────────────────────────────────────────────────────────────────────
def test_run_does_each_pool_but_the_last_in_order_and_commits_what_they_make(repo, tmp_path):  # fmt: skip
    to = tmp_path / "record.json"
    got = go(repo, "run", "--open", "origin/a", "--open", "origin/b", "--to", str(to))
    assert got.returncode == 0, got.stdout + got.stderr
    order = [x for x in got.stdout.splitlines() if x.startswith("── ")]
    assert order == ["── say 0 made it make=made.txt",
                     "── say 0 on work against origin/main",
                     "── against 0 origin/a origin/b"]  # fmt: skip
    assert "numbered" not in got.stdout, "the last pool waits for the number"
    assert subjects(repo)[0] == "tidy: made again by say 0 made it make=made.txt"
    assert (repo / "made.txt").read_text() == "made\n" and git(repo, "status", "--porcelain") == ""  # fmt: skip
    kept = json.loads(to.read_text())
    assert [s[0] for s in kept["said"]] == ["say", "say", "against"]
    assert kept["said"][1][2:] == [0, "on work against origin/main"] and kept["notes"] == []  # fmt: skip


def test_a_step_that_needs_you_stops_it_there_and_what_ran_is_kept(repo, tmp_path):
    steps(repo, "## checked\n- say -- 42 a gate is red\n" + GREEN)
    to = tmp_path / "record.json"
    got = go(repo, "run", "--to", str(to))
    assert got.returncode == 42
    assert "stopped: say exited 42: a gate is red" in got.stderr
    assert "made it" not in got.stdout, "nothing after it ran"
    assert [s[2] for s in json.loads(to.read_text())["said"]] == [42]
    steps(repo, "## checked\n- say -- 2\n")
    got = go(repo, "run")
    assert got.returncode == 42 and "say exited 2: (nothing)" in got.stderr


def test_a_42_that_owes_nothing_is_noted_by_the_line_that_says_why_and_it_goes_on(repo, tmp_path):  # fmt: skip
    steps(repo, GREEN.replace("- against -- 0 {open}",
                              "- against -- 42 ports:java  unreachable  (no java) / run it in CI"))  # fmt: skip
    to = tmp_path / "record.json"
    got = go(repo, "run", "--to", str(to))
    assert got.returncode == 0, got.stdout + got.stderr
    assert json.loads(to.read_text())["notes"] == [
        "`against` came back 42: ports:java unreachable (no java)"]  # fmt: skip
    steps(repo, GREEN.replace("- against -- 0 {open}", "- against -- 42 nothing to check"))  # fmt: skip
    go(repo, "run", "--to", str(to))
    assert json.loads(to.read_text())["notes"] == ["`against` came back 42: nothing to check"]  # fmt: skip
    steps(repo, "## s\n- say -- 42 nothing owed?\n")
    assert go(repo, "run").returncode == 42, "say's 42 is not one that owes nothing"


def test_a_collision_stops_it_though_against_exits_0(repo):
    steps(repo, GREEN.replace("- against -- 0 {open}", "- against -- 0 collides: x.py with #3"))  # fmt: skip
    got = go(repo, "run")
    assert (
        got.returncode == 42 and "collides with another open pull request" in got.stderr
    )


def test_a_git_that_fails_is_stopped_on_with_what_git_said(repo):
    """A hook that turns the tidy commit away: the stop says git's own reason."""
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'no tidy today' >&2\nexit 1\n")
    hook.chmod(0o755)
    got = go(repo, "run")
    assert got.returncode == 42 and "stopped: git commit" in got.stderr
    assert "no tidy today" in got.stderr, "git's own reason, not an empty one"


def test_run_refuses_a_to_whose_folder_isnt_there(repo, tmp_path):
    got = go(repo, "run", "--to", str(tmp_path / "missing" / "record.json"))
    assert got.returncode == 2 and "no folder" in got.stderr
    assert not (tmp_path / "missing").exists()


# ── body ─────────────────────────────────────────────────────────────────────
def test_the_body_is_the_templates_sections_from_the_commits_cards_and_steps(repo, tmp_path):  # fmt: skip
    say = repo / "adapters/stdlib/say/say.py"
    say.write_text(say.read_text(encoding="utf-8") + "# touched\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "say: touched")
    to = tmp_path / "record.json"
    assert go(repo, "run", "--to", str(to)).returncode == 0
    got = go(repo, "body", "--from", str(to), "--footer", "made by a test")
    assert got.returncode == 0, got.stderr
    text = got.stdout
    # ready's own sections, in order: that they are the host's template's is
    # github's test to hold (test_create_pr.py), which goes when GitHub does
    assert re.findall(r"^## (.+)$", text, re.M) == list(rd.SECTIONS)
    assert "**thing: a new thing**\n\nBecause it was missing." in text
    assert "Co-Authored-By" not in text and "tidy:" not in text.split("## Its promises")[0]  # fmt: skip
    assert "- `say`: writes made.txt; network none" in text
    assert "`say 0 on work against origin/main`: exit 0" in text
    assert "doesn't reach here runs in CI" in text and text.rstrip().endswith("made by a test")  # fmt: skip


def test_a_body_with_no_add_on_touched_and_notes_says_both(repo, tmp_path):
    to = tmp_path / "record.json"
    to.write_text(json.dumps({"said": [], "notes": ["`against` came back 42: x"]}))
    text = go(repo, "body", "--from", str(to)).stdout
    assert "It touches no add-on." in text and "- `against` came back 42: x" in text


def test_body_refuses_a_record_it_cant_read(repo, tmp_path):
    for bad in ("", "{}", "[]"):
        (tmp_path / "r.json").write_text(bad)
        got = go(repo, "body", "--from", str(tmp_path / "r.json"))
        assert got.returncode == 2 and "can't read" in got.stderr, bad
    got = go(repo, "body", "--from", str(tmp_path / "none.json"))
    assert got.returncode == 2 and "can't read" in got.stderr


# ── opened ───────────────────────────────────────────────────────────────────
def test_opened_names_the_fragment_past_a_name_taken_and_runs_the_last_pool(repo, tmp_path):  # fmt: skip
    (repo / "changes/7.added.md").write_text("an older one\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "an older one")
    to = tmp_path / "record.json"
    assert go(repo, "run", "--to", str(to)).returncode == 0
    got = go(repo, "opened", "--pr", "7", "--to", str(to))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "named its changelog fragment changes/7.added.1.md" in got.stdout
    assert "numbered 7" in got.stdout and "made it" not in got.stdout
    assert (repo / "changes/7.added.1.md").read_text() == "`thing`, a new thing\n"
    assert not (repo / "changes/+work.added.md").exists()
    assert subjects(repo)[0] == "changelog: its number (#7)"
    assert [s[1][-1] for s in json.loads(to.read_text())["said"]][-1] == "7", "added to what run kept"  # fmt: skip
    assert len(json.loads(to.read_text())["said"]) == 4


def test_opened_again_has_nothing_to_name_and_commits_nothing(repo):
    assert go(repo, "opened", "--pr", "7").returncode == 0
    head = git(repo, "rev-parse", "HEAD")
    got = go(repo, "opened", "--pr", "7")
    assert got.returncode == 0 and "named" not in got.stdout
    assert git(repo, "rev-parse", "HEAD") == head


# ── the pieces ───────────────────────────────────────────────────────────────
def test_the_real_steps_are_a_stack_of_add_ons_that_are_here():
    pools = rd.steps(rd.STEPS)
    names = [n for _, ss in pools for n, _ in ss]
    assert names[0] == "restack" and names[-1] == "ci.changelog"
    assert pools[-1][0] == rd.AFTER and all(h != rd.AFTER for h, _ in pools[:-1])
    assert {"ci.made", "test-impact.impact", "against"} <= set(names)
    assert set(rd.FINE_42) <= set(names) and set(rd.STOP_ON) <= set(names)


def test_steps_prints_each_pool_and_its_steps():
    got = subprocess.run([sys.executable, str(HERE / "ready.py"), "steps"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0
    lines = got.stdout.splitlines()
    assert lines[0] == "## main brought in" and lines[1].startswith("- restack -- --onto {base}")  # fmt: skip
    assert f"## {rd.AFTER}" in lines and lines[-1].startswith("- ci.changelog -- ")


def test_fill_spreads_the_open_branches_and_fills_the_rest():
    fields = {"base": "origin/main", "pr": 7, "open": ["origin/a", "origin/b"]}
    assert rd.fill(["--base", "{base}", "{open}", "#{pr}"], fields) == [
        "--base", "origin/main", "origin/a", "origin/b", "#7"]  # fmt: skip
    assert rd.fill(["{open}"], {**fields, "open": []}) == []
