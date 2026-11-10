"""versions.py: each add-on and idea a pull request changes steps its version
once, by the size of its change (CONTRIBUTING.md, Releases)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("versions", HERE / "versions.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


def card(version="0.1.0", network="none", extra=""):
    return (
        f"<!-- willow-addon\nsection: Play\nline: A thing.\nsource: new\nadded: 2026-11-09\n"
        f"version: {version}\nwrites: nothing\nnetwork: {network}\nrole: tools\n{extra}-->\n# x\n"
    )


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo():
    """main with one add-on, alpha 0.1.0, and one idea, gamma 0.0.1; then a
    branch, as a pull request is."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        (r / "adapters/stdlib/alpha").mkdir(parents=True)
        (r / "adapters/stdlib/alpha/README.md").write_text(card())
        (r / "adapters/stdlib/alpha/alpha.py").write_text("print(1)\n")
        (r / "adapters/stdlib/alpha/test_alpha.py").write_text("x = 1\n")
        ideas = [
            {"name": "gamma", "kind": "stdlib", "line": "Later.", "version": "0.0.1"}
        ]
        (r / "adapters/planned.json").write_text(json.dumps(ideas, indent=1) + "\n")
        git(r, "init", "-q", "-b", "main")
        git(r, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        git(r, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
        git(r, "checkout", "-qb", "pr")
        yield r


def commit(repo: Path) -> None:
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "change", "--allow-empty")  # fmt: skip


def check(repo: Path) -> tuple[int, list[str]]:
    items = vs.owed("main", repo)
    return vs.main(["check", "--base", "main"], repo), [it["why"] for it in items if "why" in it]  # fmt: skip


def ideas(repo: Path) -> list[dict]:
    return json.loads((repo / "adapters/planned.json").read_text())


def set_ideas(repo: Path, entries: list[dict]) -> None:
    (repo / "adapters/planned.json").write_text(json.dumps(entries, indent=1) + "\n")


@pytest.mark.parametrize(
    "old, new, want",
    [
        ("0.1.0", "0.1.0", "same"),
        ("0.1.0", "0.1.1", "patch"),
        ("0.1.0", "0.2.0", "minor"),
        ("0.9.4", "1.0.0", "major"),
        ("0.1.0", "0.3.0", None),
        ("0.1.0", "0.2.1", None),
        ("0.2.0", "0.1.9", None),
        ("0.1.0", "v0.2.0", None),
    ],
)
def test_a_step_is_one_of_three_or_none(old, new, want):
    assert vs.step(old, new) == want


def test_nothing_changed_nothing_owed(repo):
    commit(repo)
    assert check(repo) == (0, [])


def test_a_changed_add_on_steps_and_write_takes_the_smallest_step(repo):
    (repo / "adapters/stdlib/alpha/alpha.py").write_text("print(2)\n")
    commit(repo)
    code, why = check(repo)
    assert code == 2 and why == ["changed here, so its version steps from 0.1.0"]
    vs.main(["write", "--base", "main"], repo)
    assert "version: 0.1.1" in (repo / "adapters/stdlib/alpha/README.md").read_text()
    commit(repo)
    assert check(repo) == (0, [])


def test_a_bigger_step_is_the_authors_and_a_skipped_one_is_refused(repo):
    (repo / "adapters/stdlib/alpha/alpha.py").write_text("print(2)\n")
    (repo / "adapters/stdlib/alpha/README.md").write_text(card("0.2.0"))
    commit(repo)
    assert check(repo) == (
        0,
        [],
    )  # a minor step for a fix is allowed: the author's call
    (repo / "adapters/stdlib/alpha/README.md").write_text(card("0.3.0"))
    commit(repo)
    code, why = check(repo)
    assert code == 2 and "more than one step" in why[0]
    vs.main(["write", "--base", "main"], repo)  # never changes a step taken
    assert "version: 0.3.0" in (repo / "adapters/stdlib/alpha/README.md").read_text()


def test_only_its_tests_changing_owes_nothing(repo):
    (repo / "adapters/stdlib/alpha/test_alpha.py").write_text("x = 2\n")
    commit(repo)
    assert check(repo) == (0, [])


def test_a_change_to_its_cards_words_is_a_change(repo):
    """Its card is one of its files: what it says it does changed, so it steps."""
    (repo / "adapters/stdlib/alpha/README.md").write_text(card() + "\nmore words.\n")
    commit(repo)
    code, why = check(repo)
    assert code == 2 and why == ["changed here, so its version steps from 0.1.0"]


def test_a_changed_promise_is_never_a_patch(repo):
    (repo / "adapters/stdlib/alpha/README.md").write_text(card("0.1.1", network="example.com, to fetch"))  # fmt: skip
    commit(repo)
    code, why = check(repo)
    assert code == 2 and "changed what its card promises (network)" in why[0]
    (repo / "adapters/stdlib/alpha/README.md").write_text(card("0.1.0", extra="hands: x, to y\n"))  # fmt: skip
    commit(repo)
    vs.main(["write", "--base", "main"], repo)
    assert "version: 0.2.0" in (repo / "adapters/stdlib/alpha/README.md").read_text()
    commit(repo)
    assert check(repo) == (0, [])


def test_a_new_add_on_starts_at_0_1_0(repo):
    (repo / "adapters/stdlib/beta").mkdir()
    (repo / "adapters/stdlib/beta/README.md").write_text(card("1.0.0"))
    commit(repo)
    code, why = check(repo)
    assert code == 2 and "first build is 0.1.0, not 1.0.0" in why[0]
    vs.main(["write", "--base", "main"], repo)
    commit(repo)
    assert check(repo) == (0, [])


def test_an_idea_built_is_0_1_0_and_its_idea_gone(repo):
    set_ideas(repo, [])
    (repo / "adapters/stdlib/gamma").mkdir()
    (repo / "adapters/stdlib/gamma/README.md").write_text(card("0.0.1"))
    commit(repo)
    code, why = check(repo)
    assert code == 2 and "first build is 0.1.0, not 0.0.1" in why[0]
    (repo / "adapters/stdlib/gamma/README.md").write_text(card("0.1.0"))
    commit(repo)
    assert check(repo) == (0, [])


def test_an_idea_steps_a_patch_each_time_it_changes(repo):
    set_ideas(repo, [{**ideas(repo)[0], "line": "Later, and better."}])
    commit(repo)
    code, why = check(repo)
    assert code == 2 and "steps a patch from 0.0.1" in why[0]
    vs.main(["write", "--base", "main"], repo)
    assert ideas(repo)[0]["version"] == "0.0.2"
    commit(repo)
    assert check(repo) == (0, [])
    set_ideas(repo, [{**ideas(repo)[0], "version": "0.1.0"}])  # not by moving it
    commit(repo)
    assert check(repo)[0] == 2


def test_an_unchanged_idea_keeps_its_version_and_a_new_one_starts_at_0_0_1(repo):
    set_ideas(repo, [{**ideas(repo)[0], "version": "0.0.2"},
                     {"name": "delta", "kind": "stdlib", "line": "New.", "version": "0.0.5"}])  # fmt: skip
    commit(repo)
    code, why = check(repo)
    assert code == 2
    assert "didn't change here, so stays 0.0.1, not 0.0.2" in why
    assert "is a new idea, so it starts at 0.0.1, not 0.0.5" in why


def test_one_pull_request_is_one_step_however_many_commits(repo):
    for n in (2, 3):
        (repo / "adapters/stdlib/alpha/alpha.py").write_text(f"print({n})\n")
        commit(repo)
    (repo / "adapters/stdlib/alpha/README.md").write_text(card("0.1.1"))
    commit(repo)
    assert check(repo) == (0, [])


@pytest.mark.parametrize(
    "argv", [[], ["check"], ["check", "main"], ["bump", "--base", "main"]]
)
def test_a_bad_command_line_is_refused(argv, repo):
    assert vs.main(argv, repo) == 2


def test_a_base_git_cant_find_is_unreachable(repo):
    assert vs.main(["check", "--base", "no-such-ref"], repo) == 42
