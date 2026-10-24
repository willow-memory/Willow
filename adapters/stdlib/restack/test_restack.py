"""restack: a branch on top of main, the repo's own conflicts settled by rule,
any other one stopping it untouched, and nothing moved before test_docs.py
passes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import restack as rs  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}  # fmt: skip


def conflict(ref: str, mine: str) -> str:
    return f"<<<<<<< HEAD\n{ref}=======\n{mine}>>>>>>> abc (theirs)\n"


# ── the rules ────────────────────────────────────────────────────────────────
def test_changelog_puts_the_branchs_entries_above_refs_inside_unreleased():
    text = ("# Changelog\n\n## Unreleased\n\n### Added\n\n"
            + conflict("- `scan`, from main. (#15)\n", "- `lending`, from the branch.\n")
            + "- older.\n\n## v0.1.0 · 2026-10-23\n")  # fmt: skip
    got = rs.changelog(text)
    assert "- `lending`, from the branch.\n- `scan`, from main. (#15)\n- older." in got
    assert "<<<<<<<" not in got


def test_changelog_never_settles_a_conflict_outside_unreleased():
    text = "## Unreleased\n\n- a\n\n## v0.1.0\n\n" + conflict("- x\n", "- y\n")
    with pytest.raises(rs.Stop, match="outside ## Unreleased"):
        rs.changelog(text)


TREE = "│   │   ├── {n}/\n│   │   │   ├── {n}.py    it\n│   │   │   ├── test_{n}.py\n"
CLOSE = "│   │   │   └── README.md\n"


def test_files_tree_is_both_sides_entries_a_to_z_each_one_closed():
    text = (TREE.format(n="gaps") + CLOSE
            + conflict(TREE.format(n="life"), TREE.format(n="lending"))
            + CLOSE + TREE.format(n="mail") + CLOSE)  # fmt: skip
    got = rs.files_tree(text)
    assert got == (TREE.format(n="gaps") + CLOSE + TREE.format(n="lending") + CLOSE
                   + TREE.format(n="life") + CLOSE + TREE.format(n="mail") + CLOSE)  # fmt: skip


def test_files_tree_with_closed_entries_needs_no_tail():
    text = conflict(TREE.format(n="zed") + CLOSE, TREE.format(n="again") + CLOSE)
    assert rs.files_tree(text) == TREE.format(n="again") + CLOSE + TREE.format(n="zed") + CLOSE  # fmt: skip


def test_files_tree_stops_when_both_sides_changed_one_entry_or_it_isnt_a_tree():
    a = TREE.format(n="todo")
    with pytest.raises(rs.Stop, match="both sides changed todo/"):
        rs.files_tree(conflict(a, a.replace("it", "something else")))
    with pytest.raises(rs.Stop, match="isn't two sets of entries"):
        rs.files_tree(conflict("plain words\n", TREE.format(n="x")))


def test_contract_keeps_both_sides_commands_lines_refs_first():
    ref = '    "scan": ("scan.py", ["index"]),\n'
    mine = '    "lending": ("lending.py", ["--box", "{box}"]),\n'
    assert rs.contract("COMMANDS = {\n" + conflict(ref, mine) + "}\n") == (
        "COMMANDS = {\n" + ref + mine + "}\n"
    )
    with pytest.raises(rs.Stop, match="outside COMMANDS"):
        rs.contract(conflict("def f():\n", '    "x": ("x.py", []),\n'))


def test_a_conflict_it_cant_read_stops():
    with pytest.raises(rs.Stop, match="can't read"):
        rs.hunks("no markers here\n", lambda *a: "")


def entry(name: str) -> dict:
    return {"name": name, "kind": "stdlib", "line": f"{name}."}


def test_planned_is_refs_list_less_what_the_branch_built_plus_what_it_added():
    dump = lambda xs: json.dumps(xs, indent=1)  # noqa: E731
    base = dump([entry("a"), entry("b"), entry("c")])
    ref = dump([entry("a"), entry("c"), entry("d")])  # main built b, added d
    mine = dump([entry("a"), entry("b"), entry("e")])  # branch built c, added e
    got = json.loads(rs.planned(base, ref, mine))
    assert [x["name"] for x in got] == ["a", "d", "e"]
    assert rs.planned(base, ref, mine).startswith('[\n {\n  "name"'), (
        "the file's own indent"
    )
    with pytest.raises(rs.Stop, match="isn't JSON"):
        rs.planned(base, "{", mine)


@pytest.mark.parametrize("argv", [[], ["--onto"], ["--onto", "main"], ["main", "x"],
                                  ["--onto", "main", "--stray"], ["--into", "main", "x"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run([sys.executable, str(HERE / "restack.py"), *argv],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "restack.py" in got.stderr


# ── on a real clone of this repo ─────────────────────────────────────────────
def git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=cwd, env=ENV, check=True,
                          capture_output=True, text=True).stdout.strip()  # fmt: skip


@pytest.fixture
def clone(tmp_path):
    """This repo's committed files, a branch `work` with one changelog entry,
    and `main` moved on with another in the same place."""
    repo = tmp_path / "repo"
    # the files as they are, not a clone: mutants tests a copy with no .git,
    # and the restack.py under test is the one in that copy
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"))  # fmt: skip
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the repo as it is")
    log = repo / "CHANGELOG.md"
    head = "### Added\n\n"

    def add(branch: str, line: str, base: str = "main"):
        git(repo, "checkout", "-q", "-B", branch, base)
        text = log.read_text(encoding="utf-8")
        log.write_text(text.replace(head, head + line, 1), encoding="utf-8")
        git(repo, "commit", "-q", "-am", line)

    add("work", "- `work`, from the branch.\n")
    add("main", "- `mainline`, from main. (#99)\n", base="main")
    git(repo, "checkout", "-q", "--detach")
    return repo


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess:
    script = repo / "adapters" / "stdlib" / "restack" / "restack.py"
    return subprocess.run([sys.executable, str(script), *argv], cwd=repo, env=ENV,
                          capture_output=True, text=True)  # fmt: skip


def test_a_branch_is_put_on_top_with_its_changelog_settled_and_nothing_else_touched(
    clone,
):
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "settled CHANGELOG.md" in got.stdout
    assert f"git push --force-with-lease=work:{old[:12]} origin work" in got.stdout
    assert git(clone, "merge-base", "--is-ancestor", "main", "work") == ""
    text = git(clone, "show", "work:CHANGELOG.md")
    assert "- `work`, from the branch.\n- `mainline`, from main. (#99)\n" in text + "\n"
    assert git(clone, "worktree", "list").count("\n") == 0, (
        "its scratch worktree is gone"
    )
    again = run(clone, "--onto", "main", "work")
    assert again.returncode == 42 and "already on top" in again.stdout


def test_a_conflict_with_no_rule_stops_it_and_leaves_the_branch_as_it_was(clone):
    for branch, words in (("work", "branch words"), ("main", "main words")):
        git(clone, "checkout", "-q", branch)
        (clone / "LIMITS.md").write_text(words + "\n", encoding="utf-8")
        git(clone, "commit", "-q", "-am", words)
    git(clone, "checkout", "-q", "--detach")
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    assert got.returncode == 2
    assert (
        "work: stopped, left as it was: a conflict with no rule, in LIMITS.md"
        in got.stdout
    )
    assert git(clone, "rev-parse", "work") == old
    assert git(clone, "worktree", "list").count("\n") == 0


def test_a_checkout_with_changes_of_yours_is_never_moved(clone, tmp_path):
    there = tmp_path / "there"
    git(clone, "worktree", "add", "-q", str(there), "work")
    (there / "mine.txt").write_text("not committed\n")
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    assert got.returncode == 2 and "has changes of yours" in got.stdout
    assert git(clone, "rev-parse", "work") == old
    (there / "mine.txt").unlink()
    moved = run(clone, "--onto", "main", "work")
    assert moved.returncode == 0, moved.stdout
    assert git(there, "rev-parse", "HEAD") == git(clone, "rev-parse", "work") != old


def test_a_branch_git_does_not_know_is_refused(clone):
    got = run(clone, "--onto", "main", "no-such-branch")
    assert got.returncode == 2 and "git doesn't know no-such-branch" in got.stdout
