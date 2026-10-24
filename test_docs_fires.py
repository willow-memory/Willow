"""Every check test_docs.py makes is shown to fire.

A check that has never failed has not been shown to check anything. For each
test in test_docs.py there is one planted violation here: the repo is copied,
the violation is made in the copy, and that test, run on the copy, has to
fail. The copy untouched has to pass every one, so a failure is the plant's.
A test added to test_docs.py with no plant here fails this file.
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def _append(rel: str, text: str):
    def plant(c: Path) -> None:
        with (c / rel).open("a", encoding="utf-8") as f:
            f.write(text)

    return plant


def _replace(rel: str, old: str, new: str):
    """The first match of the pattern `old` made `new`."""

    def plant(c: Path) -> None:
        p = c / rel
        s = p.read_text(encoding="utf-8")
        assert re.search(old, s), f"the plant's anchor {old!r} is gone from {rel}"
        p.write_text(re.sub(old, new, s, count=1), encoding="utf-8")

    return plant


def _add(rel: str, text: str = "planted\n"):
    def plant(c: Path) -> None:
        (c / rel).parent.mkdir(parents=True, exist_ok=True)
        (c / rel).write_text(text, encoding="utf-8")

    return plant


def _remove(rel: str):
    return lambda c: (c / rel).unlink()


#: one violation for each test in test_docs.py, by the test's name
PLANTS = {
    "test_the_tree_lists_every_file_and_nothing_else": _add("planted.txt"),
    "test_the_readmes_tree_is_the_repos_top_level": _add("planted/x.txt"),
    "test_every_folder_in_the_tree_is_one_that_holds_its_files": _replace(
        "FILES.md", "willow/\n", "willow/\n├── empty-planted/\n"
    ),
    "test_every_path_a_doc_names_exists": _append(
        "CONTRIBUTING.md", "\nSee `no/such/planted.py`.\n"
    ),
    "test_a_question_number_is_one_its_folder_asks_and_its_words_are_its_own": _append(
        "demo/hollis/STRIP.md", "\nAs question 999 asked.\n"
    ),
    "test_no_doc_uses_the_willow_systems_id_families": _append(
        "CONTRIBUTING.md", "\nAs OW12 says.\n"
    ),
    "test_the_case_count_is_cases_jsons": _replace(
        "vectors/README.md", r"(\| `cases\.json` \| )([\d,]+)", r"\g<1>1\2"
    ),
    "test_the_kernels_length_is_what_the_tree_says": _replace(
        "README.md",
        r"the whole program \(about ([\d,]+)",
        r"the whole program (about 9\1",
    ),
    "test_odiles_files_are_what_the_docs_say": _replace(
        "docs/how-it-works.md", "On Odile's ", "On Odile's 1"
    ),
    "test_the_readmes_contents_link_every_section_in_order": _replace(
        "README.md", r" · \[Commands\]\(#commands\)", ""
    ),
    "test_the_python_version_is_the_kernels": _replace(
        "README.md", "Python 3.9 or newer", "Python 3.8 or newer"
    ),
    "test_add_ons_live_only_in_stdlib_or_deps": _add("adapters/loose/loose.py"),
    "test_every_add_on_has_its_card_and_its_tests": _remove(
        "adapters/stdlib/todo/test_todo.py"
    ),
    "test_every_deps_add_on_pins_what_it_needs_and_names_it_on_its_card": _replace(
        "adapters/deps/pdf/requirements.txt", "==", ">="
    ),
    "test_every_deps_add_on_has_a_floor_and_its_card_names_it": _remove(
        "adapters/deps/pdf/requirements-floor.txt"
    ),
    "test_every_port_folder_is_one_compare_runs_and_ci_requires": _add(
        "ports/planted/Kernel.planted"
    ),
    "test_every_file_is_checked_out_with_lf_line_endings": _append(
        "kernel.py", "# planted\r\n"
    ),
    "test_each_release_is_a_changelog_heading_and_the_citation_names_the_newest": _replace(
        "CHANGELOG.md",
        "\n## Unreleased\n",
        "\n## Unreleased\n\n## v0.1.0 · 2026-10-24\n",
    ),
    "test_every_citation_names_a_clause_the_constitution_has": _append(
        "adapters/stdlib/todo/todo.py", "# holds CONST-0-9\n"
    ),
    "test_every_clause_is_enforced_or_answered_in_reach_json": _replace(
        "constitution/reach.json", r',\n    "CONST-XIII": \{[^}]*\}', ""
    ),
    "test_every_clause_the_code_enforces_a_test_attacks": _append(
        "adapters/stdlib/todo/todo.py", "# holds CONST-VIII\n"
    ),
    "test_every_clause_an_amendment_brings_is_enforced_and_attacked": _replace(
        "constitution/amendments/0001.md",
        "clauses: CONST-VIII-4",
        "clauses: CONST-VIII-4, CONST-VIII-2",
    ),
    "test_the_readmes_guarantees_name_their_clauses_and_every_eternity_clause_is_there": _replace(
        "README.md", r"\| `CONST-0-6` \|", "| none |"
    ),
    "test_bugs_md_is_the_tests_marked_as_known_bugs": _add(
        "test_planted.py",
        "import pytest\n\n\n@pytest.mark.xfail(strict=True, reason='bug #1: planted')\n"
        "def test_planted():\n    assert False\n",
    ),
}


def checks() -> list[str]:
    tree = ast.parse((ROOT / "test_docs.py").read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]  # fmt: skip


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org",
                           *args], cwd=cwd, capture_output=True, text=True)  # fmt: skip


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
    """The repo's files as git sees them, in a fresh repo of their own."""
    listed = git(ROOT, "ls-files", "--cached", "--others", "--exclude-standard")
    copy = tmp_path_factory.mktemp("docs") / "willow"
    for rel in listed.stdout.splitlines():
        if (ROOT / rel).is_file():
            (copy / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, copy / rel)
    git(copy, "init", "-q")
    git(copy, "add", "-A")
    return copy


def run(copy: Path, test: str = "") -> subprocess.CompletedProcess:
    target = str(copy / "test_docs.py") + (f"::{test}" if test else "")
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           target], cwd=copy, capture_output=True, text=True)  # fmt: skip


def test_every_check_has_a_plant():
    assert set(checks()) == set(PLANTS)


def test_the_copy_untouched_passes_every_check(clean):
    got = run(clean)
    assert got.returncode == 0, got.stdout[-2000:]


@pytest.mark.parametrize("check", sorted(PLANTS))
def test_each_check_fires_on_its_plant(clean, check, tmp_path):
    copy = tmp_path / "willow"
    shutil.copytree(clean, copy)
    PLANTS[check](copy)
    git(copy, "add", "-A")
    got = run(copy, check)
    assert got.returncode == 1, (
        f"{check} didn't fail on its plant:\n{got.stdout[-1500:]}"
    )
