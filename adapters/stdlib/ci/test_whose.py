"""whose: lines to the pull request that wrote them, and a report's text
refused unless it names a line range in a tracked file."""

from __future__ import annotations

import importlib.util
import io
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_whose", HERE / "whose.py")
whose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(whose)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org",
                    *args], cwd=root, check=True, capture_output=True)  # fmt: skip


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """main: a first commit straight on it (no pull request), then #4 merged,
    then a commit squashed as #9."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    (root / "k.py").write_text("one\ntwo\nthree\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "first")
    git(root, "checkout", "-q", "-b", "pr")
    (root / "k.py").write_text("one\nTWO\nthree\n")
    git(root, "commit", "-qam", "change two")
    (root / "k.py").write_text("one\nTWO\nthree\nfour\n")
    git(root, "commit", "-qam", "add four")
    git(root, "checkout", "-q", "main")
    git(root, "merge", "-q", "--no-ff", "pr", "-m", "Two fixed, four added (#4)")
    (root / "k.py").write_text("ONE\nTWO\nthree\nfour\n")
    git(root, "commit", "-qam", "One in capitals (#9)")
    monkeypatch.setattr(whose, "ROOT", root)
    return root


def test_lines_lead_to_the_pull_request_that_wrote_them(repo, capsys):
    assert whose.main(["k.py:2-4"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2-4\n"
    assert whose.main(["k.py:1", "k.py:2"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2\n#9 k.py:1\n"


def test_a_merge_titled_the_old_way_counts(repo, capsys):
    git(repo, "checkout", "-q", "-b", "pr2")
    (repo / "k.py").write_text("ONE\nTWO\nTHREE\nfour\n")
    git(repo, "commit", "-qam", "three")
    git(repo, "checkout", "-q", "main")
    git(
        repo, "merge", "-q", "--no-ff", "pr2", "-m", "Merge pull request #11 from x/pr2"
    )
    assert whose.main(["k.py:3"]) == 0
    assert capsys.readouterr().out == "#11 k.py:3\n"


def test_lines_from_before_pull_requests_are_none_found(repo, capsys):
    (repo / "k.py").write_text("ONE\nTWO\nthree\nfour\n")
    assert whose.main(["k.py:3"]) == 42
    assert "before pull requests" in capsys.readouterr().out


@pytest.mark.parametrize(
    "place",
    ["k.py", "k.py:0", "k.py:3-2", "k.py:1-99", "../k.py:1", "/etc/passwd:1",
     "nope.py:1", "k.py:1; rm -rf /", "@someone"],
)  # fmt: skip
def test_a_place_that_isnt_a_line_range_in_a_tracked_file_is_refused(repo, place, capsys):  # fmt: skip
    assert whose.main([place]) == 2
    assert capsys.readouterr().err.startswith("refused")


def test_the_form_section_is_read_and_its_blanks_left_out(repo, capsys, monkeypatch):
    body = ("### Which promise\n\nSomething else\n\n### Where it is\n\n"
            "`k.py:2`\n\nk.py:1\n\n### Anything\n\nk.py:3\n")  # fmt: skip
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    assert whose.main(["form"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2\n#9 k.py:1\n"
    monkeypatch.setattr("sys.stdin", io.StringIO("### Where it is\n\n_No response_\n"))
    assert whose.main(["form"]) == 42


def test_the_security_form_asks_under_the_heading_whose_reads():
    form = (HERE.parents[2] / ".github" / "ISSUE_TEMPLATE" / "security.yml").read_text()
    assert f"label: {whose.SECTION.removeprefix('### ')}\n" in form


@pytest.mark.parametrize("argv", [[], ["--x"], ["k.py:1", "-L"]])
def test_a_bad_command_line_is_refused(argv):
    assert whose.main(argv) == 2
