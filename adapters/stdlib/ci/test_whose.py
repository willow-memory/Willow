"""whose: lines to the commit that wrote them with git alone, and with a
host's host.json to the pull request; places refused unless each is a line
range in a tracked file."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_whose", HERE / "whose.py")
whose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(whose)
#: GitHub's merge titles, written out here so these tests need no host add-on
#: (adapters/stdlib/github tests its own host.json)
HUB = {"name": "GitHub", "label": "#{n}",
       "titles": ["\\(#(\\d+)\\)$", "^Merge pull request #(\\d+) "]}  # fmt: skip


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org",
                           *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout  # fmt: skip


@pytest.fixture
def hub(tmp_path_factory) -> str:
    folder = tmp_path_factory.mktemp("hub")
    (folder / "host.json").write_text(json.dumps(HUB))
    return str(folder)


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


def sha(root: Path, rev: str) -> str:
    return git(root, "rev-parse", rev).strip()[:12]


def test_with_git_alone_lines_lead_to_their_commits(repo, capsys):
    assert whose.main(["k.py:1", "k.py:3"]) == 0
    assert capsys.readouterr().out == (
        f"{sha(repo, 'HEAD')} k.py:1\n{sha(repo, 'main~1^1')} k.py:3\n"
    )


def test_with_github_lines_lead_to_the_pull_request_that_wrote_them(repo, hub, capsys):
    assert whose.main(["--host", hub, "k.py:2-4"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2-4\n"
    assert whose.main(["--host", hub, "k.py:1", "k.py:2"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2\n#9 k.py:1\n"


def test_a_merge_titled_the_old_way_counts(repo, hub, capsys):
    git(repo, "checkout", "-q", "-b", "pr2")
    (repo / "k.py").write_text("ONE\nTWO\nTHREE\nfour\n")
    git(repo, "commit", "-qam", "three")
    git(repo, "checkout", "-q", "main")
    git(
        repo, "merge", "-q", "--no-ff", "pr2", "-m", "Merge pull request #11 from x/pr2"
    )
    assert whose.main(["--host", hub, "k.py:3"]) == 0
    assert capsys.readouterr().out == "#11 k.py:3\n"


def test_another_host_is_a_host_json(repo, hub, tmp_path, capsys):
    """GitLab, say: its own label, and the number in the merge's message,
    not its title. Nothing else changes."""
    git(repo, "checkout", "-q", "-b", "mr")
    (repo / "k.py").write_text("ONE\nTWO\nTHREE\nfour\n")
    git(repo, "commit", "-qam", "three")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "mr", "-m",
        "Merge branch 'mr' into 'main'\n\nSee merge request x/y!5")  # fmt: skip
    lab = tmp_path / "gitlab"
    lab.mkdir()
    (lab / "host.json").write_text(json.dumps(
        {"name": "GitLab", "label": "!{n}", "titles": [r"See merge request \S+!(\d+)$"]}))  # fmt: skip
    assert whose.main(["--host", str(lab), "k.py:3"]) == 0
    assert capsys.readouterr().out == "!5 k.py:3\n"
    assert whose.main(["--host", hub, "k.py:3"]) == 42  # GitHub's titles don't read it


def test_lines_from_before_pull_requests_are_none_found(repo, hub, capsys):
    (repo / "k.py").write_text("ONE\nTWO\nthree\nfour\n")
    assert whose.main(["--host", hub, "k.py:3"]) == 42
    assert "before pull requests" in capsys.readouterr().out


def test_places_from_stdin(repo, hub, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("k.py:2\n\n`k.py:1`\n"))
    assert whose.main(["--host", hub, "-"]) == 0
    assert capsys.readouterr().out == "#4 k.py:2\n#9 k.py:1\n"
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    assert whose.main(["-"]) == 42


@pytest.mark.parametrize(
    "place",
    ["k.py", "k.py:0", "k.py:3-2", "k.py:1-99", "../k.py:1", "/etc/passwd:1",
     "nope.py:1", "k.py:1; rm -rf /", "@someone"],
)  # fmt: skip
def test_a_place_that_isnt_a_line_range_in_a_tracked_file_is_refused(repo, place, capsys):  # fmt: skip
    assert whose.main([place]) == 2
    assert capsys.readouterr().err.startswith("refused")


@pytest.mark.parametrize(
    "host_json",
    [None, "not json", {"label": "#{n}", "titles": ["(\\d+)"]},
     {"name": "X", "label": "#", "titles": ["(\\d+)"]},
     {"name": "X", "label": "#{n}", "titles": []},
     {"name": "X", "label": "#{n}", "titles": ["\\d+"]}],
)  # fmt: skip
def test_a_host_without_a_good_host_json_is_refused(repo, tmp_path, host_json, capsys):
    if host_json is not None:
        text = host_json if isinstance(host_json, str) else json.dumps(host_json)
        (tmp_path / "host.json").write_text(text)
    assert whose.main(["--host", str(tmp_path), "k.py:1"]) == 2
    assert "host.json" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [[], ["--x"], ["k.py:1", "-L"], ["--host"]])
def test_a_bad_command_line_is_refused(argv):
    assert whose.main(argv) == 2
