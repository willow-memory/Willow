"""restack-open: each open pull request from this repository that conflicts
with its base is given to restack, and pushed when restack settles it; one
restack can't settle is named for a person; a clean one, a fork's and a
bot's are left as they are; nothing is pushed without --push, and a push
the remote refuses is never forced. restack's own rules are test_restack.py's:
here a stand-in for it makes the merge commit."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("restack_open", HERE / "restack_open.py")
ro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ro)


def git(where: Path, *argv: str) -> str:
    got = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *argv],
                         cwd=where, capture_output=True, text=True, check=True)  # fmt: skip
    return got.stdout.strip()


def commit(work: Path, branch: str, start: str, files: dict) -> None:
    git(work, "checkout", "-q", "-B", branch, *([start] if start else []))
    for name, text in files.items():
        (work / name).write_text(text)
    git(work, "add", "-A")
    git(work, "commit", "-qm", branch)


def pr(
    n: int, head: str, base: str = "main", fork: bool = False, user: str = "rudi"
) -> dict:
    repo = {"full_name": "willow-memory/Willow"}
    return {"number": n, "user": {"login": user},
            "head": {"ref": head, "repo": {"full_name": "someone/Willow"} if fork else repo},
            "base": {"ref": base, "repo": repo}}  # fmt: skip


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """An origin and a clone of it: main, then main moved on in a.md and
    b.md, and five pull requests' branches from before it moved."""
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(work))
    commit(work, "main", "", {"a.md": "a\n", "b.md": "b\n", "c.md": "c\n"})
    for name, files in (("clean", {"c.md": "c, the branch's\n"}),
                        ("settles", {"a.md": "a, the branch's\n"}),
                        ("stops", {"b.md": "b, the branch's\n"}),
                        ("forked", {"a.md": "a, a fork's\n"}),
                        ("bot", {"a.md": "a, a bot's\n"})):  # fmt: skip
        commit(work, name, "main", files)
    commit(work, "main", "main", {"a.md": "a, main's\n", "b.md": "b, main's\n"})
    git(work, "push", "-q", "--all", "origin")
    pulls = [pr(1, "clean"), pr(2, "settles"), pr(3, "stops"), pr(4, "forked", fork=True),
             pr(5, "bot", user="dependabot[bot]")]  # fmt: skip
    (tmp_path / "prs.json").write_text(json.dumps(pulls))
    monkeypatch.setattr(ro, "ROOT", work)
    calls = []

    def restack(branch: str, onto: str):
        calls.append((branch, onto))
        if branch.endswith("/3"):
            raise ro.rs.Stop("a conflict with no rule, in b.md; settle it by hand")
        old = git(work, "rev-parse", branch)
        tree = git(work, "rev-parse", f"{onto}^{{tree}}")
        new = git(
            work, "commit-tree", tree, "-p", old, "-p", onto, "-m", f"Merge {onto}"
        )
        git(work, "update-ref", f"refs/heads/{branch}", new, old)
        return ro.kernel.ALIVE, [
            f"{branch}: {old[:8]} -> {new[:8]}, {onto} merged in; settled a.md"
        ]

    monkeypatch.setattr(ro.rs, "restack", restack)
    return tmp_path, origin, work, calls


def test_each_open_pull_request_is_merged_up_named_or_left(repo, capsys):
    tmp, origin, work, calls = repo
    before = git(origin, "rev-parse", "settles")
    assert ro.main(["--prs", str(tmp / "prs.json"), "--push"]) == 42
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "restack-open: populated, 5 open; 1 merged up, 1 for a person"
    assert out[1:3] == ["## for a person",
                        "  #3  stops    a conflict with no rule, in b.md; settle it by hand"]  # fmt: skip
    assert out[3:5] == ["## merged up",
                        "  #2  settles  main merged in; settled a.md: pushed"]  # fmt: skip
    assert out[5:] == ["## left as they are",
                       "  #1  clean    merges clean into main",
                       "  #4  forked   a fork's branch: its author's",
                       "  #5  bot      a bot's branch: it rebases its own"]  # fmt: skip
    # only the conflicting ones went to restack, onto their own base
    assert calls == [
        ("restack-open/2", "origin/main"),
        ("restack-open/3", "origin/main"),
    ]
    # pushed as a merge on top of the branch as it was, never rewritten
    after = git(origin, "rev-parse", "settles")
    assert git(origin, "rev-parse", f"{after}^1") == before
    assert git(origin, "rev-parse", f"{after}^2") == git(origin, "rev-parse", "main")
    assert git(work, "branch", "--list", "restack-open/*") == "", (
        "its own branches are gone"
    )


def test_without_push_nothing_is_pushed_and_the_push_is_said(repo, capsys):
    tmp, origin, _, _ = repo
    before = git(origin, "rev-parse", "settles")
    assert ro.main(["--prs", str(tmp / "prs.json")]) == 42
    assert "settled a.md: push with git push origin " in capsys.readouterr().out
    assert git(origin, "rev-parse", "settles") == before


def test_a_branch_that_moved_meanwhile_is_refused_never_forced(
    repo, monkeypatch, capsys
):
    tmp, origin, work, _ = repo
    settle = ro.rs.restack

    def moved(branch, onto):
        got = settle(branch, onto)
        other = tmp / "other"  # someone pushes to the branch while restack runs
        git(tmp, "clone", "-q", "-b", "settles", str(origin), str(other))
        (other / "d.md").write_text("d\n")
        git(other, "add", "-A")
        git(other, "commit", "-qm", "theirs")
        git(other, "push", "-q", "origin", "settles")
        return got

    monkeypatch.setattr(ro.rs, "restack", moved)
    theirs = None
    (tmp / "one.json").write_text(json.dumps([pr(2, "settles")]))
    assert ro.main(["--prs", str(tmp / "one.json"), "--push"]) == 42
    assert (
        "the push was refused (the branch moved): run it again"
        in capsys.readouterr().out
    )
    theirs = git(origin, "log", "-1", "--format=%s", "settles")
    assert theirs == "theirs", "their commit is still the branch's head"


def test_a_stacked_pull_request_is_merged_up_to_its_own_base(repo, capsys):
    """Its base is another pull request's branch, not main: both changed a.md,
    so it conflicts with that branch, and that is what it is merged up to."""
    tmp, origin, work, calls = repo
    (tmp / "one.json").write_text(json.dumps([pr(6, "forked", base="settles")]))
    assert ro.main(["--prs", str(tmp / "one.json")]) == 0
    assert calls == [("restack-open/6", "origin/settles")]
    assert (
        "settles merged in; settled a.md: push with git push origin "
        in capsys.readouterr().out
    )


def test_nothing_open_is_empty(repo, capsys):
    tmp, *_ = repo
    (tmp / "none.json").write_text("[]")
    assert ro.main(["--prs", str(tmp / "none.json"), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "addon": "restack-open",
        "state": "empty",
        "said": "no open pull request",
        "groups": [],
    }


@pytest.mark.parametrize("argv", [[], ["--push"], ["--repo"], ["--prs", "x", "--repo", "y"],
                                  ["--other", "x"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run([sys.executable, str(HERE / "restack_open.py"), *argv],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "restack_open.py" in got.stderr


def test_a_list_that_wont_read_is_refused(repo, capsys):
    tmp, *_ = repo
    (tmp / "bad.json").write_text("{not json")
    assert ro.main(["--prs", str(tmp / "bad.json")]) == 2
    (tmp / "obj.json").write_text("{}")
    assert ro.main(["--prs", str(tmp / "obj.json")]) == 2
    assert "refused:" in capsys.readouterr().err
