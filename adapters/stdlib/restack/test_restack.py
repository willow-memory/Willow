"""restack: main merged into a branch, the repo's own conflicts settled by rule,
any other one stopping it untouched, and nothing moved before test_docs.py
passes."""

from __future__ import annotations

import ast
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


def docs_pass(repo: Path) -> bool:
    """Whether the copy's own test_docs.py passes at main. It doesn't in the
    copy test_strip.py makes, its FILES.md naming what was stripped: there
    nothing can move, and the tests hold restack to saying so."""
    work = repo.parent / "main-docs"
    git(repo, "worktree", "add", "-q", "--detach", str(work), "main")
    got = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                          "test_docs.py"], cwd=work, capture_output=True)  # fmt: skip
    git(repo, "worktree", "remove", "--force", str(work))
    return got.returncode == 0


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess:
    script = repo / "adapters" / "stdlib" / "restack" / "restack.py"
    return subprocess.run([sys.executable, str(script), *argv], cwd=repo, env=ENV,
                          capture_output=True, text=True)  # fmt: skip


def test_a_branch_is_put_on_top_with_its_changelog_settled_and_nothing_else_touched(
    clone,
):
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    if not docs_pass(clone):
        assert got.returncode == 2 and "test_docs.py fails" in got.stdout, got.stdout
        assert git(clone, "rev-parse", "work") == old, "nothing moves unchecked"
        return
    assert got.returncode == 0, got.stdout + got.stderr
    assert "settled CHANGELOG.md" in got.stdout
    assert "  push: git push origin work" in got.stdout
    assert git(clone, "merge-base", "--is-ancestor", "main", "work") == ""
    # merged, not rewritten: the branch's old commit is still under it
    assert git(clone, "log", "-1", "--format=%s", "work") == "Merge main into work"
    assert git(clone, "merge-base", "--is-ancestor", old, "work") == ""
    text = git(clone, "show", "work:CHANGELOG.md")
    assert "- `work`, from the branch.\n- `mainline`, from main. (#99)\n" in text + "\n"
    assert git(clone, "worktree", "list").count("\n") == 0, (
        "its scratch worktree is gone"
    )
    again = run(clone, "--onto", "main", "work")
    assert again.returncode == 42 and "already holds main" in again.stdout


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
    assert got.returncode == 2 and "with changes of yours" in got.stdout
    assert git(clone, "rev-parse", "work") == old
    (there / "mine.txt").unlink()
    moved = run(clone, "--onto", "main", "work")
    if not docs_pass(clone):
        assert moved.returncode == 2 and git(there, "rev-parse", "HEAD") == old
        return
    assert moved.returncode == 0, moved.stdout
    assert git(there, "rev-parse", "HEAD") == git(clone, "rev-parse", "work") != old


def test_a_branch_git_does_not_know_is_refused(clone):
    got = run(clone, "--onto", "main", "no-such-branch")
    assert got.returncode == 2 and "git doesn't know no-such-branch" in got.stdout


# ── test_contract.py, settled by what each side added ────────────────────────
BASE = """import os

NOW = ["--now"]

PILE_EXTRA: dict = {
    "scrub": {"photo.png": b""},
}

READERS: dict = {
    "office": ("office.py", {"a.docx": (
        b"roof"
    )}),
    "clauses": ("clauses.py", {"t.html": b"terms"}),
}  # fmt: skip

COMMANDS: dict = {
    "amounts": ("amounts.py", ["--box", "{box}"]),
    **{name: (script, ["mirror"]) for name, (script, _) in READERS.items()},
}  # fmt: skip
"""
MARKDOWN = """    "markdown": ("markdown.py", {"notes.md": (
        b"# Notes"
    )}),
"""
CSV = """    "csv-rows": ("csv_rows.py", {"rows.csv": (
        b"a,b"
    )}),
"""
SPLAT = "READERS.items()},\n"


def after_office(text: str, entry: str) -> str:
    """`entry` put after office's, whose last line every such entry shares."""
    old = '    )}),\n    "clauses"'
    assert text.count(old) == 1
    return text.replace(old, "    )}),\n" + entry + '    "clauses"')


def swapped(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


def test_contract_entries_puts_each_sides_new_entries_whole_at_its_dicts_end():
    ref = after_office(BASE, CSV)
    mine = after_office(BASE, MARKDOWN)
    mine = swapped(
        mine, SPLAT, SPLAT + '    # said over it\n    "zed": ("zed.py", [])\n'
    )
    mine = swapped(
        mine, '"photo.png": b""},\n', '"photo.png": b""},\n    "w": {}  # w\n'
    )
    mine = swapped(mine, "import os\n", "import os\nimport json\n")
    got = rs.contract_entries(BASE, ref, mine)
    ast.parse(got)
    assert got.count(MARKDOWN) == got.count(CSV) == 1
    assert got.index(CSV) < got.index(MARKDOWN) < got.index("}  # fmt: skip"), (
        "REF's entries first, the branch's at the end, before the closing brace"
    )
    assert SPLAT + '    # said over it\n    "zed": ("zed.py", []),\n}' in got, (
        "after a splat, its comment with it, given a comma"
    )
    assert '"photo.png": b""},\n    "w": {},  # w\n}' in got
    assert got.startswith("import os\nimport json\n\nNOW"), "the branch's import"
    readers = rs.keyed(got, rs.tables(ast.parse(got))["READERS"])
    assert list(readers) == ['"office"', '"csv-rows"', '"clauses"', '"markdown"']
    assert rs.contract_entries(BASE, BASE, BASE) == BASE


def test_contract_entries_carries_only_whats_new_to_ref():
    both = after_office(BASE, MARKDOWN)
    assert rs.contract_entries(BASE, both, both) == both, "REF has it already"
    amounts = '    "amounts": ("amounts.py", ["--box", "{box}"]),\n'
    plain = swapped(BASE, amounts, "")
    ref = swapped(
        plain, "    **{name", '    "amounts": ("amounts.py", []),\n    **{name'
    )
    with pytest.raises(rs.Stop, match='both sides added "amounts" to COMMANDS'):
        rs.contract_entries(plain, ref, BASE)
    bare = swapped(BASE, 'b"terms"}),\n}', 'b"terms"})\n}')
    mine = swapped(bare, 'b"terms"})\n}', 'b"terms"}),\n' + CSV + "}")
    with pytest.raises(rs.Stop, match="not only adds entries"):
        rs.contract_entries(bare, bare, mine)  # the branch gave base's last a comma
    got = rs.contract_entries(BASE, bare, after_office(BASE, CSV))
    assert 'b"terms"}),\n' + CSV + "}" in got, "REF's last entry given its comma"


@pytest.mark.parametrize("change", [
    ('b"roof"', 'b"a new roof"'),  # an entry that was there, changed
    ('    "amounts": ("amounts.py", ["--box", "{box}"]),\n', ""),  # one removed
    ('NOW = ["--now"]', 'NOW = ["--then"]'),  # another statement
    ("import os\n", ""),  # an import gone
    ("}  # fmt: skip\n\nCOMMANDS", "}  # fmt: skip\n# a word\nCOMMANDS"),
])  # fmt: skip
def test_contract_entries_stops_when_the_branch_changed_anything_but_adding(change):
    mine = after_office(swapped(BASE, *change), MARKDOWN)
    with pytest.raises(rs.Stop, match="not only adds entries"):
        rs.contract_entries(BASE, after_office(BASE, CSV), mine)


def test_contract_entries_stops_on_what_it_cant_take_whole():
    ref, mine = after_office(BASE, CSV), after_office(BASE, MARKDOWN)
    with pytest.raises(rs.Stop, match="doesn't parse on the branch"):
        rs.contract_entries(BASE, ref, BASE + "def (\n")
    shared = swapped(BASE, '    "clauses"', '    "x": 1, "clauses"')
    with pytest.raises(rs.Stop, match='READERS\'s "x" shares a line'):
        rs.contract_entries(BASE, ref, shared)
    with pytest.raises(rs.Stop, match="REF has no READERS"):
        rs.contract_entries(BASE, "import os\n", mine)
    flat = swapped(ref, 'b"terms"}),\n}', 'b"terms"})}')
    with pytest.raises(rs.Stop, match="doesn't close on a line of its own"):
        rs.contract_entries(BASE, flat, mine)
    with pytest.raises(rs.Stop, match="no import to put"):
        rs.contract_entries(
            BASE, swapped(ref, "import os\n", ""), "import json\n" + BASE
        )


CONTRACT_FILE = "adapters/stdlib/ci/test_contract.py"


def reader(name: str) -> str:
    return (f'    "{name}": ("{name}.py", {{"{name}.md": (\n'
            f'        b"# {name} notes\\n"\n    )}}),\n')  # fmt: skip


def add_reader(repo: Path, branch: str, name: str, also=lambda t: t) -> None:
    """On `branch`, a READERS entry after codebase-memory's, as each reader adds
    its own after one that is there."""
    git(repo, "checkout", "-q", branch)
    path = repo / CONTRACT_FILE
    text = swapped(path.read_text(encoding="utf-8"), '    )}),\n    "nestor"',
                   "    )}),\n" + reader(name) + '    "nestor"')  # fmt: skip
    path.write_text(also(text), encoding="utf-8")
    git(repo, "commit", "-q", "-am", f"{name}, a reader")


def test_two_readers_conflicting_in_readers_are_settled_whole(clone):
    add_reader(clone, "work", "markdown",
               lambda t: swapped(t, "import zipfile\n", "import zipfile\nimport base64\n"))  # fmt: skip
    add_reader(clone, "main", "csv-rows")
    # the failure as it was met: git splits the two entries, so neither side
    # of the conflict holds a whole one and the line rule can't settle it
    git(clone, "checkout", "-q", "--detach", "work")
    subprocess.run(["git", "merge", "-q", "main"], cwd=clone, env=ENV, capture_output=True)  # fmt: skip
    split = (clone / CONTRACT_FILE).read_text(encoding="utf-8")
    assert "<<<<<<<" in split
    with pytest.raises((rs.Stop, SyntaxError)):
        ast.parse(rs.contract(rs.swap(split)))
    git(clone, "merge", "--abort")
    git(clone, "checkout", "-q", "--detach")
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    if not docs_pass(clone):
        assert got.returncode == 2 and "test_docs.py fails" in got.stdout, got.stdout
        assert git(clone, "rev-parse", "work") == old
        return
    assert got.returncode == 0, got.stdout + got.stderr
    assert CONTRACT_FILE in got.stdout
    text = git(clone, "show", f"work:{CONTRACT_FILE}") + "\n"
    ast.parse(text)
    assert text.count(reader("markdown")) == text.count(reader("csv-rows")) == 1
    assert text.count("\nimport base64\n") == 1 and "<<<<<<<" not in text


@pytest.mark.parametrize("change", [
    ('{"letter.docx": _docx("The roof is fixed.")}', '{"letter.docx": _docx("Fixed.")}'),
    ('NOW = ["--now", "2026-10-23T00:00:00Z"]', 'NOW = ["--now", "2026-10-24T00:00:00Z"]'),
])  # fmt: skip
def test_a_reader_branch_that_changed_more_than_it_added_stops_untouched(clone, change):  # fmt: skip
    add_reader(clone, "work", "markdown", lambda t: swapped(t, *change))
    add_reader(clone, "main", "csv-rows")
    git(clone, "checkout", "-q", "--detach")
    old = git(clone, "rev-parse", "work")
    got = run(clone, "--onto", "main", "work")
    assert got.returncode == 2, got.stdout + got.stderr
    assert "work: stopped, left as it was: test_contract.py: the branch changes" in got.stdout  # fmt: skip
    assert git(clone, "rev-parse", "work") == old
    assert git(clone, "worktree", "list").count("\n") == 0
