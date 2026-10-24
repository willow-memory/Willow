"""bugs: every expected failure is a strict one naming its bug, and BUGS.md
is made from them, so the list and the tests can't disagree: a known defect
is a check expected to fail, and leaves only by a fix (CONST-VI-7)."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_bugs", HERE / "bugs.py")
bugs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bugs)

MARK = 'pytest.mark.xfail(strict=True, reason="bug #{n}: {what}")'


@pytest.fixture
def repo(monkeypatch):
    """A scratch repo tempfile made, the only place outside the record the
    guard lets bugs.py write besides the repo's own BUGS.md."""
    root = Path(tempfile.mkdtemp()) / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    monkeypatch.setattr(bugs, "ROOT", root)
    yield root
    shutil.rmtree(root.parent)


def write(root: Path, name: str, text: str) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text("import pytest\n\n" + text)


def test_no_marks_is_none_known_said_not_left_blank(repo):
    write(repo, "test_a.py", "def test_a():\n    pass\n")
    assert bugs.bugs() == []
    assert "None known" in bugs.render([])


def test_each_strict_mark_is_a_bug_by_its_number(repo):
    write(repo, "a/test_a.py", f"@{MARK.format(n=12, what='ages read  wrong')}\n"
          "def test_ages():\n    assert False\n")  # fmt: skip
    write(repo, "test_b.py", "@pytest.mark.parametrize('x', [1, pytest.param(2, marks="
          f"{MARK.format(n=3, what='twos')})])\ndef test_twos(x):\n    pass\n")  # fmt: skip
    got = bugs.bugs()
    assert got == [
        {"n": 3, "what": "twos", "test": "test_b.py::test_twos"},
        {"n": 12, "what": "ages read wrong", "test": "a/test_a.py::test_ages"},
    ]
    assert bugs.numbers(bugs.render(got)) == {3, 12}


@pytest.mark.parametrize(
    "mark",
    [
        "pytest.mark.xfail",  # bare
        'pytest.mark.xfail(reason="bug #1: x")',  # not strict
        'pytest.mark.xfail(strict=False, reason="bug #1: x")',
        'pytest.mark.xfail(strict=True, reason="flaky")',  # no bug
        'pytest.mark.xfail(strict=True, reason="bug #1:")',  # no words
        "pytest.mark.xfail(strict=True)",
    ],
)
def test_any_other_mark_is_refused(repo, mark):
    write(repo, "test_a.py", f"@{mark}\ndef test_a():\n    assert False\n")
    with pytest.raises(bugs.Refused, match="test_a.py:3"):
        bugs.bugs()


def test_check_says_when_bugs_md_is_out_of_date(repo, capsys):
    """BUGS.md is a view of the tests, recomputed (CONST-VI-6)."""
    write(repo, "test_a.py", f"@{MARK.format(n=5, what='x')}\ndef test_a():\n    assert False\n")  # fmt: skip
    assert bugs.main(["check"]) == 2  # no BUGS.md yet
    assert bugs.main(["write"]) == 0
    assert bugs.main(["check"]) == 0
    assert "| #5 | x | `test_a.py::test_a` |" in (repo / "BUGS.md").read_text()
    write(repo, "test_a.py", "def test_a():\n    pass\n")  # fixed, the mark off
    assert bugs.main(["check"]) == 2
    assert "isn't current" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [[], ["writ"], ["write", "x"]])
def test_a_bad_command_line_is_refused(argv):
    assert bugs.main(argv) == 2
