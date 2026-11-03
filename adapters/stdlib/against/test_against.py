"""against: a pull request held to the other open ones, on fixture repos built
with git in a scratch folder: duplicates fail, collisions warn, restack's files
are said as settled, and nothing goes online."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "against.py"
sys.path.insert(0, str(HERE))
import against  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}  # fmt: skip

CONTRACT = "adapters/stdlib/ci/test_contract.py"
CARD = "<!-- willow-addon\nsection: Play\nline: {line}\nsource: new\n-->\n# {name}\n"
CONTRACT_TEXT = 'COMMANDS = {\n    "dice": ("dice.py", ["roll"]),\n}\nREADERS = {}\n'
FILES_TEXT = (
    "willow/\n├── kernel.py    it\n├── adapters/\n│   ├── stdlib/\n"
    "│   │   ├── dice/\n│   │   │   └── README.md\n│   └── planned.json\n└── CHANGELOG.md\n"
)
CHANGELOG = "# Changelog\n\n## Unreleased\n\n### Added\n\n- old.\n"
BASE = {
    "kernel.py": "x = 1\n",
    "CHANGELOG.md": CHANGELOG,
    "FILES.md": FILES_TEXT,
    CONTRACT: CONTRACT_TEXT,
    "adapters/planned.json": "[]\n",
    "adapters/stdlib/ci/ci.py": "def gates():\n    return 1\n",
    "adapters/stdlib/dice/README.md": CARD.format(name="dice", line="Rolls dice."),
}


def git(repo: Path, *argv: str) -> str:
    got = subprocess.run(["git", *argv], cwd=repo, capture_output=True, text=True,
                         env=ENV)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return got.stdout.strip()


def write(repo: Path, files: dict[str, str | None]) -> None:
    for rel, text in files.items():
        p = repo / rel
        if text is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def planned(*ideas: tuple[str, str]) -> str:
    return json.dumps([{"name": n, "line": line} for n, line in ideas],
                      indent=1, ensure_ascii=False) + "\n"  # fmt: skip


LINES = {"sort": "Orders a pile of papers.", "zip": "Packs files tight.",
         "tar": "Bundles folders together.", "words-ko": "Korean common words."}  # fmt: skip


def addon(name: str, line: str | None = None) -> dict[str, str]:
    line = line or LINES.get(name, f"Unrelated {name} line.")
    return {f"adapters/stdlib/{name}/README.md": CARD.format(name=name, line=line)}


def tree(*names: str) -> str:
    """FILES.md with these add-on folders added, A to Z."""
    out = FILES_TEXT
    for n in names:
        out = out.replace("│   └── planned.json",
                          f"│   │   ├── {n}/\n│   │   │   └── README.md\n│   └── planned.json")  # fmt: skip
    return out


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    write(r, BASE)
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def branch(repo: Path, name: str, files: dict, start: str = "main") -> str:
    git(repo, "checkout", "-q", "-b", name, start)
    write(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", name)
    git(repo, "checkout", "-q", "main")
    return git(repo, "rev-parse", "--short=7", name)


def check(repo: Path, *argv: str, base: str = "main"):
    return subprocess.run([sys.executable, str(SCRIPT), "check", "--base", base, *argv],
                          cwd=repo, capture_output=True, text=True, env=ENV)  # fmt: skip


# ── a duplicate fails ────────────────────────────────────────────────────────
def test_two_branches_adding_the_same_addon_folder_fail(repo):
    branch(repo, "mine", addon("sort"))
    other = branch(repo, "pr/12", addon("sort"))
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 2, got.stdout
    assert "duplicate: both add add-on sort (#12)" in got.stdout.splitlines()
    assert f"checked: #12 {other}" in got.stdout.splitlines()
    assert got.stdout.splitlines()[-1] == "1 checked, 1 duplicated, 0 collided, 0 near, 0 not checked"  # fmt: skip


def test_the_same_name_in_stdlib_and_deps_is_the_same_add_on(repo):
    branch(repo, "mine", addon("sort"))
    branch(repo, "pr/12", {"adapters/deps/sort/README.md": CARD.format(name="sort", line="x")})  # fmt: skip
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 2 and "duplicate: both add add-on sort (#12)" in got.stdout


def test_two_branches_adding_different_addons_pass_and_a_changelog_clash_is_settled(
    repo,
):
    mine = {
        **addon("sort"),
        "CHANGELOG.md": CHANGELOG.replace("- old.", "- `sort`.\n- old."),
    }
    theirs = {**addon("zip", "Packs files."), "CHANGELOG.md": CHANGELOG.replace("- old.", "- `zip`.\n- old.")}  # fmt: skip
    branch(repo, "mine", mine)
    branch(repo, "pr/12", theirs)
    got = check(repo, "mine", "pr/12")
    lines = got.stdout.splitlines()
    assert got.returncode == 0, got.stdout
    assert "settled: CHANGELOG.md with #12; restack settles it" in lines
    assert not [x for x in lines if x.startswith(("duplicate:", "collides:"))]
    assert lines[-1] == "1 checked, 0 duplicated, 0 collided, 0 near, 0 not checked"


def test_a_real_code_collision_warns_and_exits_zero(repo):
    branch(repo, "mine", {"adapters/stdlib/ci/ci.py": "def gates():\n    return 2\n"})
    branch(repo, "pr/13", {"adapters/stdlib/ci/ci.py": "def gates():\n    return 3\n"})
    got = check(repo, "mine", "pr/13")
    assert got.returncode == 0, got.stdout
    assert ("collides: adapters/stdlib/ci/ci.py with #13; "
            "merge its branch first and base on it") in got.stdout.splitlines()  # fmt: skip
    assert got.stdout.splitlines()[-1] == "1 checked, 0 duplicated, 1 collided, 0 near, 0 not checked"  # fmt: skip


def test_a_collision_beside_a_duplicate_still_fails(repo):
    both = {"adapters/stdlib/ci/ci.py": "def gates():\n    return {}\n"}
    branch(repo, "mine", {**addon("sort"), **{k: v.format(2) for k, v in both.items()}})
    branch(
        repo, "pr/13", {**addon("sort"), **{k: v.format(3) for k, v in both.items()}}
    )
    got = check(repo, "mine", "pr/13")
    assert got.returncode == 2
    assert "collides: adapters/stdlib/ci/ci.py with #13; merge its branch first and base on it" in got.stdout  # fmt: skip


def test_a_collision_leaves_no_object_in_the_repository(repo):
    branch(repo, "mine", {"adapters/stdlib/ci/ci.py": "def gates():\n    return 2\n"})
    branch(repo, "pr/13", {"adapters/stdlib/ci/ci.py": "def gates():\n    return 3\n"})
    before = git(repo, "count-objects", "-v")
    assert "collides" in check(repo, "mine", "pr/13").stdout
    assert git(repo, "count-objects", "-v") == before
    assert git(repo, "status", "--porcelain") == ""


def test_the_same_idea_added_to_planned_json_fails_and_a_different_one_does_not(repo):
    branch(repo, "mine", {"adapters/planned.json": planned(("sort", "Sorts a pile."))})
    branch(
        repo, "pr/12", {"adapters/planned.json": planned(("sort", "Orders things."))}
    )
    branch(
        repo, "pr/13", {"adapters/planned.json": planned(("weather", "Rain, by day."))}
    )
    got = check(repo, "mine", "pr/12", "pr/13")
    assert got.returncode == 2
    assert "duplicate: both add idea sort (#12)" in got.stdout
    assert "(#13)" not in "".join(x for x in got.stdout.splitlines() if x.startswith("duplicate:"))  # fmt: skip
    assert got.stdout.splitlines()[-1].startswith("2 checked, 1 duplicated")


def test_an_idea_added_by_one_and_built_by_the_other_is_the_same_name(repo):
    branch(repo, "mine", {"adapters/planned.json": planned(("sort", "Sorts a pile."))})
    branch(repo, "pr/12", addon("sort"))
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 2
    assert "duplicate: both add idea / add-on sort (#12)" in got.stdout


def test_both_taking_the_same_idea_off_planned_json_is_not_a_duplicate(repo):
    start = {"adapters/planned.json": planned(("sort", "Sorts."), ("weather", "Rain."))}
    git(repo, "checkout", "-q", "-b", "fresh", "main")
    write(repo, start)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "ideas")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--ff-only", "fresh")
    gone = {"adapters/planned.json": planned(("weather", "Rain."))}
    branch(repo, "mine", gone)
    branch(repo, "pr/12", gone)
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 0, got.stdout
    assert "duplicate:" not in got.stdout


def test_the_same_commands_key_added_by_both_is_a_duplicate(repo):
    row = '    "dice": ("dice.py", ["roll"]),\n'
    mine = CONTRACT_TEXT.replace(row, row + '    "sort": ("sort.py", ["a"]),\n')
    theirs = CONTRACT_TEXT.replace(row, row + '    "sort": ("sort.py", ["b"]),\n')
    branch(repo, "mine", {CONTRACT: mine})
    branch(repo, "pr/12", {CONTRACT: theirs})
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 2
    assert "duplicate: both add COMMANDS key sort (#12)" in got.stdout.splitlines()
    assert "dice" not in got.stdout


def test_different_commands_keys_pass(repo):
    row = '    "dice": ("dice.py", ["roll"]),\n'
    branch(repo, "mine", {CONTRACT: CONTRACT_TEXT.replace(row, row + '    "a": ("a.py", []),\n')})  # fmt: skip
    branch(repo, "pr/12", {CONTRACT: CONTRACT_TEXT.replace(row, row + '    "b": ("b.py", []),\n')})  # fmt: skip
    assert check(repo, "mine", "pr/12").returncode == 0


def test_a_path_both_add_to_files_md_is_a_duplicate_said_once_at_its_top(repo):
    mine = tree("sort").replace(
        "└── CHANGELOG.md", "├── docs/\n│   └── notes.md\n└── CHANGELOG.md"
    )
    theirs = tree("zip").replace(
        "└── CHANGELOG.md", "├── docs/\n│   └── notes.md\n└── CHANGELOG.md"
    )
    branch(repo, "mine", {"FILES.md": mine})
    branch(repo, "pr/12", {"FILES.md": theirs})
    got = check(repo, "mine", "pr/12")
    assert got.returncode == 2
    said = [x for x in got.stdout.splitlines() if x.startswith("duplicate:")]
    assert said == ["duplicate: both add docs to FILES.md (#12)"]


def test_an_addon_both_add_is_not_said_again_for_its_files_md_lines(repo):
    branch(repo, "mine", {**addon("sort"), "FILES.md": tree("sort")})
    branch(repo, "pr/12", {**addon("sort"), "FILES.md": tree("sort")})
    said = [x for x in check(repo, "mine", "pr/12").stdout.splitlines() if x.startswith("duplicate:")]  # fmt: skip
    assert said == ["duplicate: both add add-on sort (#12)"]


def test_a_words_pack_both_add_is_a_duplicate(repo):
    branch(repo, "mine", addon("words-ko"))
    branch(repo, "pr/12", addon("words-ko"))
    assert (
        "duplicate: both add add-on words-ko (#12)"
        in check(repo, "mine", "pr/12").stdout
    )


def test_main_moving_on_is_nobodys_duplicate(repo):
    branch(repo, "mine", addon("sort"))
    git(repo, "checkout", "-q", "main")
    write(repo, addon("sort"))
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "main took sort")
    # pr/12 left main before sort landed there, and adds it too: a duplicate of main's,
    # but each is compared with where it left main, so mine/pr/12 are the pair
    other = branch(repo, "pr/12", addon("zip"), start="main~1")
    got = check(repo, "mine", "pr/12")
    assert "duplicate:" not in got.stdout and f"checked: #12 {other}" in got.stdout


# ── near ideas ───────────────────────────────────────────────────────────────
def test_an_idea_near_one_the_other_adds_is_suggested(repo):
    line = "Rain and frost for each garden bed, by day, from your own notes."
    branch(repo, "mine", {"adapters/planned.json": planned(("frost", line))})
    branch(repo, "pr/12", {"adapters/planned.json": planned(("beds", "Frost and rain for each garden bed, by day, from notes."))})  # fmt: skip
    branch(repo, "pr/13", {"adapters/planned.json": planned(("tax", "Prepares an annual return."))})  # fmt: skip
    got = check(repo, "mine", "pr/12", "pr/13")
    assert got.returncode == 0, got.stdout
    assert "near: your idea frost is near #12's beds" in got.stdout.splitlines()
    assert "#13's" not in got.stdout
    assert got.stdout.splitlines()[-1] == "2 checked, 0 duplicated, 0 collided, 1 near, 0 not checked"  # fmt: skip


def test_a_new_addon_is_near_an_addon_the_other_adds(repo):
    line = "Frost and rain for each garden bed, by day, from notes."
    branch(repo, "mine", addon("frost", line))
    branch(repo, "pr/12", addon("beds", line))
    assert "near: your add-on frost is near #12's beds" in check(repo, "mine", "pr/12").stdout  # fmt: skip


# ── the report and the exit codes ────────────────────────────────────────────
def test_the_report_is_the_same_each_time_and_in_the_order_given(repo):
    branch(repo, "mine", addon("sort"))
    a = branch(repo, "pr/20", addon("zip"))
    b = branch(repo, "pr/3", addon("tar"))
    first = check(repo, "mine", "pr/20", "pr/3", "pr/20")
    assert first.stdout == check(repo, "mine", "pr/20", "pr/3").stdout
    assert first.stdout.splitlines() == [f"checked: #20 {a}", f"checked: #3 {b}",
        "2 checked, 0 duplicated, 0 collided, 0 near, 0 not checked"]  # fmt: skip


def test_a_ref_may_be_a_pull_ref_or_a_plain_name(repo):
    branch(repo, "mine", addon("sort"))
    sha = branch(repo, "feature", addon("sort"))
    git(repo, "update-ref", "refs/pull/7/head", sha)
    assert "(#7)" in check(repo, "mine", "refs/pull/7/head").stdout
    assert "(feature)" in check(repo, "mine", "feature").stdout


def test_a_missing_ref_is_42_and_named(repo):
    branch(repo, "mine", addon("sort"))
    got = check(repo, "mine", "pr/99")
    assert got.returncode == 42
    assert got.stdout.splitlines()[0] == "not checked: #99: not a ref"
    assert got.stdout.splitlines()[-1] == "0 checked, 0 duplicated, 0 collided, 0 near, 1 not checked"  # fmt: skip


def test_a_missing_ref_beside_a_good_one_is_42_unless_a_duplicate_is_found(repo):
    branch(repo, "mine", addon("sort"))
    branch(repo, "pr/12", addon("zip"))
    branch(repo, "pr/14", addon("sort"))
    assert check(repo, "mine", "pr/12", "pr/99").returncode == 42
    assert check(repo, "mine", "pr/14", "pr/99").returncode == 2


def test_no_other_pull_request_is_42_before_git_is_asked(tmp_path):
    got = subprocess.run([sys.executable, str(SCRIPT), "check", "--base", "nothing", "nope"],
                         cwd=tmp_path, capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 42 and "no other pull request" in got.stdout


def test_a_branch_with_no_history_in_common_is_said_not_checked(repo):
    branch(repo, "mine", addon("sort"))
    git(repo, "checkout", "-q", "--orphan", "island")
    write(repo, {"x.txt": "x\n"})
    git(repo, "add", "x.txt")
    git(repo, "commit", "-qm", "island")
    git(repo, "checkout", "-q", "-f", "main")
    got = check(repo, "mine", "island")
    assert got.returncode == 42
    assert got.stdout.startswith("not checked: island: ")


def test_a_head_or_base_that_is_not_a_ref_is_refused(repo):
    branch(repo, "pr/12", addon("zip"))
    got = check(repo, "ghost", "pr/12")
    assert got.returncode == 2 and "ghost is not a ref" in got.stderr
    got = check(repo, "pr/12", "pr/12", base="ghost")
    assert got.returncode == 2 and "ghost is not a ref" in got.stderr


@pytest.mark.parametrize("argv", [
    [], ["check"], ["check", "--base", "main"], ["check", "main", "a", "b"],
    ["check", "--base", "main", "mine", "--stray"], ["check", "--base", "main", "--x", "b"],
    ["merge", "--base", "main", "mine", "a"],
])  # fmt: skip
def test_a_bad_command_line_is_2_and_says_how(argv, tmp_path):
    got = subprocess.run([sys.executable, str(SCRIPT), *argv], cwd=tmp_path,
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2
    assert got.stderr.strip() == against.USAGE


# ── held to restack ──────────────────────────────────────────────────────────
def test_the_files_it_calls_settled_are_the_ones_restack_settles():
    sys.path.insert(0, str(HERE.parent / "restack"))
    import restack

    ours = set(against.SETTLED)
    assert ours == set(restack.MADE) | set(restack.SETTLE) | {"adapters/planned.json"}
    assert against.CONTRACT == restack.CONTRACT


def test_restacks_card_names_each_of_them_in_its_table():
    card = (HERE.parent / "restack" / "README.md").read_text(encoding="utf-8")
    table = card.split("| File | Settled as |")[1].split("\n\n")[0]
    cells = [row.split("|")[1].strip() for row in table.splitlines()[2:]]
    names = {n.strip().strip("`") for cell in cells for n in cell.split(",")}
    short = {Path(p).name: p for p in against.SETTLED}
    assert {short.get(n, n) for n in names} == set(against.SETTLED)


# ── read on this repo's own files ────────────────────────────────────────────
def test_this_repos_files_md_and_contract_are_read_the_way_the_checks_read_them():
    text = (ROOT / "FILES.md").read_text(encoding="utf-8")
    here = {p for p in against.tree_paths_of(text)}
    assert "adapters/stdlib/against/against.py" in here
    assert "kernel.py" in here and "willow" not in here
    keys = against.command_keys(Path(ROOT / CONTRACT).read_text(encoding="utf-8"))
    assert "restack" in keys and "against" in keys


def test_a_card_line_is_read_from_the_header_only():
    assert against.card_line("<!-- willow-addon\nline: Sorts.\n-->\n# x\nline: no\n") == "Sorts."  # fmt: skip
    assert against.card_line("# no header\nline: no\n") == ""
    assert re.fullmatch(r"#\d+", against.label("refs/pull/12/head")) and against.label("main") == "main"  # fmt: skip
