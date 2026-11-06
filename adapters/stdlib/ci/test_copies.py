"""copies.py: the functions add-ons keep a copy of, each group's common
version, and the copies that drifted from it, as a report and as diffs."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("copies", HERE / "copies.py")
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)

COMMON = '''def helper(x):
    """It says what it does."""
    y = x + 1
    return y * 2
'''
DRIFTED = """def helper(x):
    y = x + 1
    return y * 3
"""
OTHER = """def helper(path, more, flags):
    for p in path.iterdir():
        print(p, more, flags)
    raise SystemExit(0)
"""


def repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / "adapters" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return tmp_path


def test_a_drifted_copy_is_found_and_another_function_by_the_name_is_not(tmp_path):
    root = repo(tmp_path, {
        "stdlib/a/a.py": COMMON, "stdlib/b/b.py": "# reformatted\n" + COMMON.replace("x + 1", "x+1"),
        "stdlib/c/c.py": DRIFTED, "deps/d/d.py": COMMON, "stdlib/e/e.py": OTHER,
        "stdlib/f/test_f.py": DRIFTED,
    })  # fmt: skip
    doc, code = cp.survey(root)
    assert code == 42 and doc["state"] == "populated"
    assert (
        doc["said"]
        == "1 function kept in 3 or more add-ons has a copy that drifted, 1 copy in all"
    )
    (group,) = doc["groups"]
    assert group == {"name": "helper: 3 of 5 the same, as a has it",
                     "rows": [{"where": "c/c.py:1", "what": "2 lines differ"}]}  # fmt: skip
    got = cp.drift(cp.functions(root)["helper"])
    assert got["others"] == 1, "e's helper shares only the name"
    assert [c[0] for c in got["same"]] == ["a/a.py", "b/b.py", "d/d.py"], (
        "formatting and docstring aside; tests left out"
    )


def test_no_common_version_without_three_add_ons_and_two_the_same(tmp_path):
    two = repo(tmp_path / "two", {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": DRIFTED})
    assert cp.drift(cp.functions(two)["helper"]) is None
    apart = repo(tmp_path / "apart", {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": DRIFTED,
                                      "stdlib/c/c.py": DRIFTED.replace("3", "4")})  # fmt: skip
    assert cp.drift(cp.functions(apart)["helper"]) is None, "no two the same"
    same = repo(tmp_path / "same", {f"stdlib/{n}/{n}.py": COMMON for n in "abc"})
    doc, code = cp.survey(same)
    assert code == 0 and doc == {"addon": "copies", "state": "empty",
                                 "said": "no copy of a function kept in 3 or more add-ons drifted", "groups": []}  # fmt: skip


def test_a_tie_goes_to_the_version_the_first_add_on_keeps(tmp_path):
    root = repo(tmp_path, {"stdlib/a/a.py": DRIFTED, "stdlib/b/b.py": COMMON, "stdlib/c/c.py": "\n\n" + DRIFTED,
                           "stdlib/d/d.py": "\n\n" + COMMON})  # fmt: skip
    got = cp.drift(cp.functions(root)["helper"])
    assert [c[0] for c in got["same"]] == ["a/a.py", "c/c.py"], "a's version, A to Z"


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "copies.py"), *argv], capture_output=True, text=True
    )


def test_diff_prints_each_drifted_copys_lines_against_the_common_one(
    tmp_path, monkeypatch, capsys
):
    root = repo(
        tmp_path,
        {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": COMMON, "stdlib/c/c.py": DRIFTED},
    )
    assert cp.diff("helper", root) == 42
    out = capsys.readouterr().out.splitlines()
    assert out[:2] == ["--- a/a.py:1 (the common version, 2 copies)", "+++ c/c.py:1"]
    assert "-    return y * 2" in out and "+    return y * 3" in out
    same = repo(tmp_path / "s", {f"stdlib/{n}/{n}.py": COMMON for n in "abc"})
    assert cp.diff("helper", same) == 0
    assert (
        capsys.readouterr().out
        == "helper: every copy is the common version, 3 of them\n"
    )
    assert cp.diff("nothing", root) == 2


def test_its_command_line(tmp_path):
    got = run("survey", "--json")
    doc = json.loads(got.stdout)
    assert doc["addon"] == "copies" and got.returncode in (0, 42)
    assert cp.report_text(doc) == run("survey").stdout.rstrip("\n"), (
        "--json is the same report"
    )
    for argv in (
        [],
        ["survey", "x"],
        ["diff"],
        ["diff", "a", "b"],
        ["diff", "not-a-name"],
        ["diff", "x", "--json"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "copies.py" in got.stderr, argv
    got = run("diff", "no_add_on_keeps_this")
    assert got.returncode == 2 and got.stderr.startswith("refused: ")


def test_a_copy_that_says_why_is_on_purpose_and_a_survey_of_only_those_is_0(tmp_path):
    said = "# differs on purpose: its report shows the refusal\n" + DRIFTED
    root = repo(
        tmp_path,
        {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": COMMON, "stdlib/c/c.py": said},
    )
    (c,) = cp.drift(cp.functions(root)["helper"])["drifted"]
    assert c[3] == "its report shows the refusal" and c[1] == 2
    doc, code = cp.survey(root)
    assert code == 0 and doc["said"].endswith("1 copy in all, 1 of them on purpose")
    assert (
        doc["groups"][0]["rows"][0]["what"]
        == "2 lines differ; on purpose: its report shows the refusal"
    )
    far = repo(tmp_path / "far", {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": COMMON,
                                  "stdlib/c/c.py": "# differs on purpose: x\n\n" + DRIFTED})  # fmt: skip
    assert cp.drift(cp.functions(far)["helper"])["drifted"][0][3] == "", (
        "only the line just above"
    )


def git(root: Path, *argv: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv], cwd=root,
                   check=True, capture_output=True)  # fmt: skip


def test_new_names_only_the_drift_a_branch_adds_and_doesnt_say_why(tmp_path, capsys):
    root = repo(tmp_path, {"stdlib/a/a.py": COMMON, "stdlib/b/b.py": COMMON, "stdlib/c/c.py": COMMON,
                           "stdlib/d/d.py": DRIFTED})  # fmt: skip
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    assert cp.new("HEAD", root) == 0
    assert capsys.readouterr().out.endswith("None: every copy this pull request leaves drifted was drifted already, or says why.\n")  # fmt: skip
    (root / "adapters/stdlib/c/c.py").write_text(DRIFTED.replace("3", "4"))
    (root / "adapters/stdlib/b/b.py").write_text(
        "# differs on purpose: b's own\n" + DRIFTED.replace("3", "5")
    )
    assert cp.new("HEAD", root) == 0
    out = capsys.readouterr().out
    assert "- `helper` in `c/c.py:1` differs from the 1 copies" not in out, (
        "a, alone, is no common version"
    )
    (root / "adapters/stdlib/e/e.py").parent.mkdir(parents=True)
    (root / "adapters/stdlib/e/e.py").write_text(COMMON)
    assert cp.new("HEAD", root) == 0
    out = capsys.readouterr().out
    assert (
        "- `helper` in `c/c.py:1` differs from the 2 copies the others keep, as `a/a.py` has it:"
        in out
    )
    assert "+    return y * 4" in out and "b/b.py" not in out and "d/d.py" not in out
    assert cp.new("no-such-ref", root) == 2
    assert cp.sources_at("no-such-ref", root) is None
