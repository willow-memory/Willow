"""kinds: a file has a kind only when something the repo keeps says so, the
first kind that fits is it, what nothing declares is listed and ends 42, a
made file whose script isn't known is said, and nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "kinds.py"
sys.path.insert(0, str(HERE))
import kinds  # noqa: E402

CARD = "<!-- willow-addon\nline: a thing\n-->\n# thing\n"
MADE = 'MADE = (\n    ("the list", "adapters/stdlib/readme/readme.py"),\n)\n'
TOML = '[tool.towncrier]\ndirectory = "changes"\nfilename = "CHANGELOG.md"\n'

#: A small repo with one of everything: each path, what it holds, its kind.
TREE = {
    "kernel.py": ("", None),
    "CONSTITUTION.md": ("# law\n", None),
    "towncrier.toml": (TOML, None),
    "CHANGELOG.md": ("# changes\n", "account"),
    "changes/12.added.md": ("a thing\n", "account"),
    "changes/README.md": ("# how\n", None),
    "ADDONS.md": ("# add-ons\n", "made"),
    "adapters/README.md": ("# the rules\n", None),
    "adapters/planned.json": ("[]\n", "idea"),
    "adapters/stdlib/ci/made.py": (MADE, None),
    "adapters/stdlib/readme/README.md": (CARD, "card"),
    "adapters/stdlib/readme/readme.py": ("", "code"),
    "adapters/stdlib/readme/test_readme.py": ("", "test"),
    "adapters/stdlib/thing/README.md": (CARD, "card"),
    "adapters/stdlib/thing/thing.py": ("", "code"),
    "adapters/stdlib/thing/conftest.py": ("", "test"),
    "adapters/stdlib/thing/sample.txt": ("", "fixture"),
    "adapters/stdlib/thing/example/run.py": ("", "fixture"),
    "adapters/stdlib/thing/example/README.md": ("# not a card\n", "fixture"),
    "adapters/stdlib/loose/README.md": ("# no card header\n", None),
    "adapters/stdlib/loose/loose.py": ("", None),
    "demo/ada/make_life.py": ("", "made-up"),
    "demo/ada/CHARACTER.md": ("", "made-up"),
    "demo/ada/test_ada.py": ("", "test"),
    "demo/ada/FROZEN.json": ('{"files": {"questions.json": "ab"}}', "frozen"),
    "demo/ada/questions.json": ("[]", "frozen"),
    "demo/study/README.md": ("# a study\n", None),
    "demo/study/FROZEN-2.json": ('{"sources": ["pins/a.json", 7]}', "frozen"),
    "demo/study/pins/a.json": ("{}", "frozen"),
    "demo/study/run.py": ("", None),
    "demo/study/KEPT.json": ('{"files": ["out/run.json", 7]}', None),
    "demo/study/out/run.json": ("{}", "kept"),
    "demo/test_novelty.py": ("", "test"),
    "docs/tour.md": ("# tour\n", None),
}


def git(root: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(root), *argv], check=True, capture_output=True)


def make(root: Path, tree: dict | None = None) -> Path:
    for rel, (text, _) in (TREE if tree is None else tree).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    return root


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def doc_of(root: Path, *argv: str) -> tuple[dict, int]:
    got = run("of" if argv else "count", "--json", "--root", str(root), *argv)
    return json.loads(got.stdout), got.returncode


def rows(doc: dict, group: str | None) -> dict[str, str]:
    for g in doc["groups"]:
        if g["name"] == group:
            return {r["where"]: r["what"] for r in g["rows"]}
    return {}


def test_each_file_is_the_first_kind_that_fits_and_no_other(tmp_path):
    root = make(tmp_path)
    known, unknown = kinds.census(root, kinds.tracked(root))
    assert unknown == []
    for rel, (_, kind) in TREE.items():
        assert (known[rel][0] if rel in known else None) == kind, rel
    assert known["ADDONS.md"] == ("made", "adapters/stdlib/readme/readme.py")
    assert known["changes/12.added.md"] == ("account", "towncrier.toml")
    assert known["adapters/stdlib/thing/thing.py"] == ("code", "adapters/stdlib/thing/README.md")  # fmt: skip
    assert (
        known["adapters/stdlib/thing/sample.txt"][1]
        == "adapters/stdlib/thing/README.md"
    )
    assert known["demo/ada/questions.json"] == ("frozen", "demo/ada/FROZEN.json")
    assert known["demo/study/pins/a.json"] == ("frozen", "demo/study/FROZEN-2.json")
    assert known["demo/ada/CHARACTER.md"] == ("made-up", "demo/ada/make_life.py")
    assert known["demo/ada/test_ada.py"] == ("test", "its name")


def test_the_whole_report_counts_each_kind_and_lists_what_nothing_declares(tmp_path):
    doc, code = doc_of(make(tmp_path))
    want = {}
    for _, kind in TREE.values():
        want[kind] = want.get(kind, 0) + 1
    lacking = want.pop(None)
    assert doc["addon"] == "kinds" and doc["state"] == "populated" and code == 42
    assert doc["said"] == (
        f"{len(TREE)} files: {len(TREE) - lacking} are one of {len(want)} kinds, "
        f"{lacking} nothing declares"
    )
    said = rows(doc, "what it is, and what says so")
    assert list(said) == [k for k, _ in kinds.KINDS if k in want], (
        "in the order they are tried"
    )
    for kind, n in want.items():
        assert said[kind].startswith(f"{n} file{'' if n == 1 else 's'}; "), kind
    assert said["idea"].startswith("1 file; ") and said["made"].startswith("1 file; ")
    none = rows(doc, "nothing declares")
    assert none == {
        "(top level)": "3 files, such as CONSTITUTION.md",
        "adapters/stdlib/": "3 files, such as adapters/stdlib/ci/made.py",
        "demo/study/": "3 files, such as demo/study/KEPT.json",
        "adapters/": "1 file, such as adapters/README.md",
        "changes/": "1 file, such as changes/README.md",
        "docs/": "1 file, such as docs/tour.md",
    }
    assert list(none)[:3] == ["(top level)", "adapters/stdlib/", "demo/study/"], "most first, then A to Z"  # fmt: skip
    assert rows(doc, "a script whose files aren't known") == {}


def all_declared() -> dict:
    """TREE with nothing undeclared: made.py gets a card beside it, so it is
    code, and the changelog goes, since the file that names it has no kind."""
    tree = {rel: v for rel, v in TREE.items() if v[1] not in (None, "account", "kept")}
    tree["adapters/stdlib/ci/README.md"] = (CARD, "card")
    tree["adapters/stdlib/ci/made.py"] = (MADE, "code")
    return tree


def test_a_repo_where_everything_has_a_kind_ends_zero(tmp_path):
    tree = all_declared()
    doc, code = doc_of(make(tmp_path, tree))
    assert code == 0 and doc["said"] == f"{len(tree)} files: {len(tree)} are one of 8 kinds, 0 nothing declares"  # fmt: skip
    assert rows(doc, "nothing declares") == {}


def test_the_changelog_is_an_account_only_while_towncrier_names_it(tmp_path):
    root = make(tmp_path, {k: v for k, v in TREE.items() if k != "towncrier.toml"})
    known, _ = kinds.census(root, kinds.tracked(root))
    assert "CHANGELOG.md" not in known and "changes/12.added.md" not in known


def test_a_made_file_is_made_only_while_something_says_so(tmp_path):
    for gone in ("adapters/stdlib/readme/readme.py", "adapters/stdlib/ci/made.py"):
        sub = tmp_path / gone.rsplit("/", 1)[1]
        sub.mkdir()
        root = make(sub, {k: v for k, v in TREE.items() if k != gone})
        known, _ = kinds.census(root, kinds.tracked(root))
        assert "ADDONS.md" not in known, f"without {gone}, nothing says it is made"


def test_a_script_made_py_names_that_this_does_not_know_is_said_and_ends_42(tmp_path):
    tree = all_declared()
    more = MADE[:-2] + '    ("a new list", "adapters/stdlib/ci/newlist.py"),\n)\n'
    assert more.count(".py") == 2 and more.endswith("),\n)\n")
    tree["adapters/stdlib/ci/made.py"] = (more, "code")
    doc, code = doc_of(make(tmp_path, tree))
    assert code == 42
    assert rows(doc, "a script whose files aren't known") == {
        "adapters/stdlib/ci/newlist.py": "made.py names it, and what it writes isn't said here"
    }
    assert doc["said"].endswith("0 nothing declares"), "42 is for the script alone"


def test_every_script_the_real_made_py_names_has_its_files_said():
    files, unknown = kinds.made_by(ROOT)
    assert unknown == [], f"add what each writes to WRITES in kinds.py: {unknown}"
    assert files["ADDONS.md"] == "adapters/stdlib/readme/readme.py"
    assert set(kinds.WRITES) == set(
        kinds.re.findall(
            r'"((?:adapters|demo)/[^"\s]+\.py)"', (ROOT / kinds.MADE_PY).read_text()
        )
    ), "a script made.py no longer names is still in WRITES"
    for made in files:
        assert (ROOT / made).is_file(), made


def test_asked_of_files_by_name_it_says_each_ones_kind_and_what_says_so(tmp_path):
    root = make(tmp_path)
    doc, code = doc_of(root, "ADDONS.md", "adapters/stdlib/thing/thing.py")
    assert code == 0 and doc["said"] == "2 asked: 2 have a kind, 0 nothing declares"
    assert rows(doc, None) == {
        "ADDONS.md": "made; adapters/stdlib/readme/readme.py",
        "adapters/stdlib/thing/thing.py": "code; adapters/stdlib/thing/README.md",
    }
    doc, code = doc_of(root, "kernel.py", "ADDONS.md")
    assert code == 42 and doc["said"] == "2 asked: 1 have a kind, 1 nothing declares"
    assert rows(doc, None)["kernel.py"] == "nothing declares it"
    assert list(rows(doc, None)) == ["kernel.py", "ADDONS.md"], "in the order asked"


def test_the_text_is_the_report_its_json_holds(tmp_path):
    root = make(tmp_path)
    doc, _ = doc_of(root)
    text = run("count", "--root", str(root)).stdout
    assert text == kinds.report_text(doc) + "\n"
    assert text.splitlines()[0] == f"kinds: populated, {doc['said']}"
    assert "\n## nothing declares\n" in text and "\n  (top level)" in text


@pytest.mark.parametrize(
    "argv,said",
    [
        ([], "usage: kinds.py count"),
        (["--json"], "usage: kinds.py count"),
        (["tally"], "usage: kinds.py count"),
        (["count", "--nope"], "usage: kinds.py count"),
        (["count", "kernel.py"], "usage: kinds.py count"),
        (["of"], "usage: kinds.py count"),
        (["of", "--json"], "usage: kinds.py count"),
        (["count", "--root"], "--root with no folder is not a folder"),
        (["count", "--root", "{root}/absent"], "is not a folder"),
        (["of", "--root", "{root}", "not/here.txt"], "git doesn't track not/here.txt"),
        (["of", "--root", "{root}", "docs"], "git doesn't track docs"),
    ],
)
def test_a_bad_command_line_is_refused_and_says_why(tmp_path, argv, said):
    make(tmp_path)
    got = run(*[a.replace("{root}", str(tmp_path)) for a in argv])
    assert got.returncode == 2 and said in got.stderr and got.stdout == ""


def test_a_folder_git_does_not_know_is_unreachable_not_empty(tmp_path):
    (tmp_path / "kernel.py").write_text("")
    got = run("count", "--json", "--root", str(tmp_path))
    doc = json.loads(got.stdout)
    assert (
        got.returncode == 42 and doc["state"] == "unreachable" and doc["groups"] == []
    )
    assert "git couldn't list the files" in doc["said"]


def test_a_repo_with_no_file_is_empty(tmp_path):
    git(tmp_path, "init", "-q")
    doc, code = doc_of(tmp_path)
    assert code == 0 and doc["state"] == "empty" and doc["groups"] == []


def test_a_freeze_that_is_not_json_or_lists_nothing_freezes_only_itself(tmp_path):
    tree = {
        "demo/a/FROZEN.json": ("not json", "frozen"),
        "demo/a/data.json": ("{}", None),
        "demo/b/FROZEN.json": ('{"files": "data.json"}', "frozen"),
        "demo/b/data.json": ("{}", None),
        "demo/c/deeper/FROZEN.json": ('{"files": {"x.json": 1}}', None),
        "demo/c/deeper/x.json": ("{}", None),
        "demo/d/FROZEN-old.json": ('{"files": {"x.json": 1}}', None),
        "demo/d/x.json": ("{}", None),
    }
    root = make(tmp_path, tree)
    known, _ = kinds.census(root, kinds.tracked(root))
    for rel, (_, kind) in tree.items():
        assert (known[rel][0] if rel in known else None) == kind, rel


def test_a_card_is_one_only_at_an_add_ons_own_depth_and_by_its_first_line(tmp_path):
    tree = {
        "adapters/README.md": (CARD, None),
        "adapters/stdlib/README.md": (CARD, None),
        "adapters/stdlib/a/README.md": ("\n" + CARD, None),
        "adapters/stdlib/a/a.py": ("", None),
        "adapters/deps/b/README.md": (CARD, "card"),
        "adapters/deps/b/b.py": ("", "code"),
        "other/stdlib/c/README.md": (CARD, None),
        "other/stdlib/c/c.py": ("", None),
    }
    root = make(tmp_path, tree)
    known, _ = kinds.census(root, kinds.tracked(root))
    for rel, (_, kind) in tree.items():
        assert (known[rel][0] if rel in known else None) == kind, rel


def test_on_this_repo_the_kernel_and_its_law_are_what_nothing_declares():
    got = run("of", "--json", "kernel.py", "CONSTITUTION.md", "adapters/stdlib/kinds/kinds.py",
              "adapters/stdlib/kinds/README.md", "adapters/stdlib/kinds/test_kinds.py",
              "FILES.md", "CHANGELOG.md", "adapters/planned.json")  # fmt: skip
    assert got.returncode == 42, got.stderr
    said = rows(json.loads(got.stdout), None)
    assert said["kernel.py"] == said["CONSTITUTION.md"] == "nothing declares it"
    assert (
        said["adapters/stdlib/kinds/kinds.py"]
        == "code; adapters/stdlib/kinds/README.md"
    )
    assert said["adapters/stdlib/kinds/README.md"].startswith("card; ")
    assert said["adapters/stdlib/kinds/test_kinds.py"] == "test; its name"
    assert said["FILES.md"] == "made; adapters/stdlib/ci/files.py"
    assert said["CHANGELOG.md"] == "account; towncrier.toml"
    assert said["adapters/planned.json"].startswith("idea; ")


def test_a_new_file_git_has_not_been_told_of_counts_and_an_ignored_one_does_not(
    tmp_path,
):
    root = make(tmp_path)
    (root / ".gitignore").write_text("scratch/\n")
    (root / "scratch").mkdir()
    (root / "scratch" / "notes.txt").write_text("")
    (root / "docs" / "new.md").write_text("")
    files = kinds.tracked(root)
    assert "docs/new.md" in files and ".gitignore" in files
    assert "scratch/notes.txt" not in files


def test_it_writes_nothing(tmp_path):
    root = make(tmp_path)
    before = sorted(str(p) for p in root.rglob("*") if ".git" not in p.parts)
    assert run("count", "--root", str(root)).returncode == 42
    assert run("of", "--json", "--root", str(root), "kernel.py").returncode == 42
    assert sorted(str(p) for p in root.rglob("*") if ".git" not in p.parts) == before


def a_report(tmp_path: Path, groups: list, addon: str = "digest") -> Path:
    doc = {"addon": addon, "state": "populated", "said": "x",
           "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows_]} for g, rows_ in groups]}  # fmt: skip
    file = tmp_path / "report.json"
    file.write_text(json.dumps(doc))
    return file


def sifted(root: Path, report: Path, *more: str) -> tuple[dict, int]:
    got = run("sift", "--of", str(report), "--json", "--root", str(root), *more)
    assert got.stdout, got.stderr
    return json.loads(got.stdout), got.returncode


def test_sift_leaves_out_rows_in_tests_fixtures_made_up_and_frozen_files(tmp_path):
    root = make(tmp_path / "repo" if (tmp_path / "repo").mkdir() is None else tmp_path)
    report = a_report(tmp_path, [
        ("Coming up", [
            ("demo/ada/CHARACTER.md:3", "a made-up date"),
            ("adapters/stdlib/thing/sample.txt:1", "a fixture's date"),
            ("adapters/stdlib/readme/test_readme.py:9:2", "a test's date"),
            ("demo/ada/questions.json", "a frozen file's date"),
            ("adapters/stdlib/thing/README.md:21", "a card's example"),
            ("kernel.py:10", "the kernel's own"),
            ("docs/tour.md:4", "a doc's"),
        ]),
        ("Waiting", [("proposal:abc", "waiting on your seal"), ("demo/ada/CHARACTER.md:9", "another")]),
    ])  # fmt: skip
    doc, code = sifted(root, report)
    assert code == 0 and doc["state"] == "populated"
    assert doc["said"] == "digest's 9 rows: 4 kept, 5 left out"
    assert rows(doc, "Coming up") == {
        "adapters/stdlib/thing/README.md:21": "a card's example",
        "kernel.py:10": "the kernel's own",
        "docs/tour.md:4": "a doc's",
    }
    assert rows(doc, "Waiting") == {"proposal:abc": "waiting on your seal"}, (
        "a row that names no file stays"
    )
    assert rows(doc, "left out, by what kind of file the row is in") == {
        "test": "1 row in 1 file",
        "fixture": "1 row in 1 file",
        "made-up": "2 rows in 1 file",
        "frozen": "1 row in 1 file",
    }
    assert [g["name"] for g in doc["groups"]] == ["Coming up", "Waiting", "left out, by what kind of file the row is in"]  # fmt: skip


def test_sift_leaves_out_the_kinds_it_is_told_and_only_those(tmp_path):
    root = make(tmp_path / "repo" if (tmp_path / "repo").mkdir() is None else tmp_path)
    report = a_report(tmp_path, [(None, [
        ("demo/ada/CHARACTER.md:3", "made up"), ("adapters/stdlib/thing/README.md:2", "a card"),
        ("adapters/stdlib/thing/thing.py:5", "code"), ("ADDONS.md:7", "made")])])  # fmt: skip
    doc, _ = sifted(root, report, "--leave", "card, made")
    assert rows(doc, None) == {
        "demo/ada/CHARACTER.md:3": "made up",
        "adapters/stdlib/thing/thing.py:5": "code",
    }
    assert rows(doc, "left out, by what kind of file the row is in") == {
        "made": "1 row in 1 file",
        "card": "1 row in 1 file",
    }
    assert list(rows(doc, "left out, by what kind of file the row is in")) == [
        "made",
        "card",
    ], "in the order the kinds are tried"
    doc, _ = sifted(root, report, "--leave", "idea")
    assert (
        doc["said"] == "digest's 4 rows: 4 kept, 0 left out"
        and rows(doc, "left out, by what kind of file the row is in") == {}
    )
    for bad, why in ((["--leave", "nope"], "names no kind: nope"), (["--leave", ""], "names no kind: nothing"),
                     (["--leave", "test,sauce"], "names no kind: sauce")):  # fmt: skip
        got = run("sift", "--of", str(report), "--root", str(root), *bad)
        assert got.returncode == 2 and why in got.stderr, bad


def test_a_row_is_at_a_file_by_its_path_or_its_path_and_line():
    files = {"a/b.py", "c.md", "odd:name.txt"}
    for where, want in (("a/b.py", "a/b.py"), ("a/b.py:12", "a/b.py"), ("a/b.py:12:3", "a/b.py"),
                        ("c.md:1", "c.md"), ("odd:name.txt:4", "odd:name.txt"), ("a/b.py:x", None),
                        ("proposal:abc", None), ("a/b.py:1:2:3", None), ("", None), ("z.py:1", None)):  # fmt: skip
        assert kinds.file_of(where, files) == want, where


def test_sift_of_a_report_with_no_rows_is_empty_and_of_no_report_is_refused(tmp_path):
    root = make(tmp_path / "repo" if (tmp_path / "repo").mkdir() is None else tmp_path)
    doc, code = sifted(root, a_report(tmp_path, [("Coming up", [])], addon="xref"))
    assert (
        code == 0
        and doc["state"] == "empty"
        and doc["said"] == "xref has no rows to sift"
    )
    not_json = tmp_path / "not.json"
    not_json.write_text("digest: populated, 3 coming up\n")
    no_groups = tmp_path / "list.json"
    no_groups.write_text("[1, 2]")
    for argv, why in (
        (["sift"], "usage: kinds.py count"),
        (["sift", "--root", str(root)], "usage: kinds.py count"),
        (["sift", "--of", str(tmp_path / "absent.json")], "no report at"),
        (["sift", "--of", str(not_json), "--root", str(root)], "is not a report"),
        (
            ["sift", "--of", str(no_groups), "--root", str(root)],
            "is not a report: it has no groups",
        ),
        (["sift", "--of", str(not_json), "extra"], "usage: kinds.py count"),
        (["count", "--of", str(not_json)], "usage: kinds.py count"),
        (["count", "--leave", "test"], "usage: kinds.py count"),
    ):
        got = run(*argv)
        assert got.returncode == 2 and why in got.stderr and got.stdout == "", argv


def test_the_sifted_text_is_the_report_its_json_holds(tmp_path):
    root = make(tmp_path / "repo" if (tmp_path / "repo").mkdir() is None else tmp_path)
    report = a_report(
        tmp_path,
        [("Coming up", [("kernel.py:1", "x"), ("demo/ada/CHARACTER.md:3", "y")])],
    )
    doc, _ = sifted(root, report)
    text = run("sift", "--of", str(report), "--root", str(root)).stdout
    assert text == kinds.report_text(doc) + "\n"
    assert (
        text.splitlines()[0] == "kinds: populated, digest's 2 rows: 1 kept, 1 left out"
    )


def test_a_runs_kept_output_is_kept_only_while_its_demos_kept_json_lists_it(tmp_path):
    tree = {
        "demo/a/KEPT.json": (
            '{"files": {"runs/x.json": "abc", "runs/absent.json": "def"}}',
            None,
        ),
        "demo/a/runs/x.json": ("{}", "kept"),
        "demo/a/runs/y.json": ("{}", None),
        "demo/b/KEPT.json": ('{"files": ["out.txt"]}', None),
        "demo/b/out.txt": ("", "kept"),
        "demo/c/KEPT.json": ("not json", None),
        "demo/c/out.txt": ("", None),
        "demo/d/KEPT.json": ('{"files": "out.txt", "sources": ["out.txt"]}', None),
        "demo/d/out.txt": ("", None),
        "demo/e/deeper/KEPT.json": ('{"files": ["out.txt"]}', None),
        "demo/e/deeper/out.txt": ("", None),
        "other/f/KEPT.json": ('{"files": ["out.txt"]}', None),
        "other/f/out.txt": ("", None),
        "demo/g/make_life.py": ("", "made-up"),
        "demo/g/KEPT.json": ('{"files": ["said.txt"]}', "made-up"),
        "demo/g/said.txt": ("", "kept"),
        "demo/g/note.txt": ("", "made-up"),
    }
    root = make(tmp_path, tree)
    known, _ = kinds.census(root, kinds.tracked(root))
    for rel, (_, kind) in tree.items():
        assert (known[rel][0] if rel in known else None) == kind, rel
    assert known["demo/a/runs/x.json"] == ("kept", "demo/a/KEPT.json")


def test_sift_leaves_out_a_runs_kept_output_unless_told_otherwise(tmp_path):
    root = make(tmp_path / "repo" if (tmp_path / "repo").mkdir() is None else tmp_path)
    report = a_report(
        tmp_path,
        [(None, [("demo/study/out/run.json:3", "a model said"), ("kernel.py:1", "x")])],
    )
    doc, _ = sifted(root, report)
    assert rows(doc, None) == {"kernel.py:1": "x"}
    assert rows(doc, "left out, by what kind of file the row is in") == {
        "kept": "1 row in 1 file"
    }
    doc, _ = sifted(root, report, "--leave", "test")
    assert len(rows(doc, None)) == 2
    assert kinds.LEAVE == ("test", "fixture", "made-up", "frozen", "kept")
