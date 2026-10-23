"""changelog: a change beyond the docs owes a line under Unreleased naming
its pull request; docs alone owe nothing; a line elsewhere doesn't count."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_changelog", HERE / "changelog.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

LOG = "# Changelog\n\n## Unreleased\n\n- an older line (#1)\n\n## 2026-10-23\n\n- old\n"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org",
                    *args], cwd=root, check=True, capture_output=True)  # fmt: skip


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo on `main` with a changelog, and a branch to change it on."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    (root / "CHANGELOG.md").write_text(LOG)
    (root / "code.py").write_text("x = 1\n")
    (root / "README.md").write_text("hi\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "checkout", "-q", "-b", "change")
    monkeypatch.setattr(cl, "ROOT", root)
    return root


def commit(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).write_text(text)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "change")


def test_docs_alone_owe_nothing(repo):
    commit(repo, {"README.md": "hello\n"})
    assert cl.check("main", "7") == 0


def test_a_code_change_without_its_line_is_refused(repo, capsys):
    commit(repo, {"code.py": "x = 2\n"})
    assert cl.check("main", "7") == 2
    assert "ending (#7)" in capsys.readouterr().err


def test_its_line_under_unreleased_ending_with_its_number(repo):
    log = LOG.replace(
        "- an older line (#1)", "- an older line (#1)\n- the change,\n  wrapped (#7)"
    )
    commit(repo, {"code.py": "x = 2\n", "CHANGELOG.md": log})
    assert cl.check("main", "7") == 0


@pytest.mark.parametrize(
    "log",
    [
        LOG.replace("- old\n", "- old\n- the change (#7)\n"),  # not under Unreleased
        LOG.replace("- an older line (#1)", "- an older line (#1)\n- the change (#8)"),
        LOG.replace(
            "- an older line (#1)", "- an older line (#1)\n- the change (#7) later"
        ),
    ],
)
def test_a_line_elsewhere_or_for_another_pull_request_doesnt_count(repo, log):
    commit(repo, {"code.py": "x = 2\n", "CHANGELOG.md": log})
    assert cl.check("main", "7") == 2


def test_an_old_line_already_there_doesnt_count_as_this_ones(repo):
    commit(repo, {"code.py": "x = 2\n"})
    assert cl.check("main", "1") == 2  # (#1) was there before this change


def test_a_base_git_cant_find_is_unreachable(repo):
    assert cl.check("no-such-branch", "7") == 42


@pytest.mark.parametrize(
    "argv", [[], ["--base", "main"], ["--base", "main", "--pr", "x"]]
)
def test_a_bad_command_line_is_refused(argv):
    assert cl.main(argv) == 2
