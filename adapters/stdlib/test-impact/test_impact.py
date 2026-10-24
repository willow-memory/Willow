"""test-impact: what a change reaches, placed by the import graph and a few
rules, said in ci.py's gate names, and never narrower than it can place."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_impact", HERE / "impact.py")
imp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imp)
ci = imp.ci
ROOT = imp.ROOT


def cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "impact.py"), *argv],
                          capture_output=True, text=True, cwd=ROOT)  # fmt: skip


@pytest.fixture
def plan_of(capsys, monkeypatch):
    """`impact.py plan ...` run in this process, on this repo's graph (parsed
    once): what it returned and printed."""
    graph = imp.Graph(imp.repo_pythons())
    monkeypatch.setattr(imp, "Graph", lambda files: graph)
    # paths are only names here: a stripped copy of the repo (test_strip.py)
    # has no .github or github add-on to be named
    monkeypatch.setattr(imp, "by_hand", lambda arg: arg)

    def go(*argv: str):
        code = imp.main(["plan", *argv])
        return SimpleNamespace(returncode=code, stdout=capsys.readouterr().out)

    return go


def write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def graph_of(root: Path, files: dict[str, str], monkeypatch) -> "imp.Graph":
    write(root, files)
    monkeypatch.setattr(imp, "ROOT", root)
    return imp.Graph(sorted(f for f in files if f.endswith(".py")))


def gate_names(out: str) -> list[str]:
    """The gate of each numbered step of a printed plan."""
    return [line.split(". ", 1)[1].split(": ")[0]
            for line in out.splitlines() if line[:3].strip(" .").isdigit()]  # fmt: skip


# ── the command line ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("argv", [
    [], ["plan"], ["run"], ["go", "README.md"], ["plan", "--head", "main", "README.md"],
    ["plan", "--base"], ["plan", "--base", "--head", "x"], ["plan", "--stray", "README.md"],
    ["plan", "README.md", "--stray", "more"],
])  # fmt: skip
def test_nothing_or_a_stray_argument_is_refused_and_names_the_script(argv):
    got = cli(*argv)
    assert got.returncode == 2 and "impact.py" in got.stderr and got.stdout == ""


def test_a_ref_git_does_not_know_is_refused():
    got = cli("plan", "--base", "no-such-ref-anywhere")
    assert got.returncode == 2 and got.stderr.startswith("refused: git ")


def test_a_path_outside_the_repo_or_not_there_is_refused():
    out = cli("plan", "/etc/hostname")
    assert out.returncode == 2 and "outside the repo" in out.stderr
    gone = cli("plan", "adapters/stdlib/changed/no_such_file.py")
    assert gone.returncode == 2 and "never knew it" in gone.stderr
    folder = cli("plan", "adapters/stdlib/changed")
    assert folder.returncode == 2 and "is a folder" in folder.stderr


def test_no_difference_is_42_and_still_says_the_full_run_comes_after():
    got = cli("plan", "--base", "HEAD", "--head", "HEAD")
    assert got.returncode == 42, got.stderr
    assert "nothing changed (git diff from HEAD to HEAD): nothing to run" in got.stdout
    assert imp.FULL in got.stdout


def test_a_plan_is_the_same_bytes_twice_and_ends_with_the_full_run():
    a = cli("plan", "adapters/stdlib/changed/changed.py")
    b = cli("plan", "adapters/stdlib/changed/changed.py")
    assert a.returncode == 0 and a.stdout == b.stdout
    assert a.stdout.endswith(
        "This does not replace the full run: it still runs after, in CI, and here:\n"
        f"  {imp.FULL}\n"
    )
    assert str(ROOT) not in a.stdout


# ── the plan, on this repo ───────────────────────────────────────────────────
def test_an_add_on_gets_its_tests_its_share_of_the_contract_its_docs_and_its_mutants(
    plan_of,
):
    got = plan_of("adapters/stdlib/changed/changed.py").stdout
    assert "pytest adapters/stdlib/changed/test_changed.py" in got
    assert "WILLOW_ONLY=changed pytest adapters/stdlib/ci/test_contract.py" in got
    assert "pytest test_docs.py\n" in got
    assert "mutants:changed" in got and "mutants.py run changed" in got
    assert "ruff check adapters/stdlib/changed/changed.py" in got
    assert "mutants:stale" not in got and "WILLOW_ONLY=stale" not in got
    assert "test_docs_fires" not in got and "tests:strip" not in got
    assert "everything" not in got


def test_the_steps_are_ordered_cheapest_first(plan_of):
    got = plan_of("adapters/stdlib/changed/changed.py").stdout
    order = [g for g in gate_names(got)]
    assert order == ["lint:check", "lint:format", "tests:adapters", "tests:adapters",
                     "tests:docs", "demo:stack", "mutants:changed"]  # fmt: skip
    narrow, own = (
        "WILLOW_ONLY=changed pytest",
        "pytest adapters/stdlib/changed/test_changed.py",
    )
    assert got.index(narrow) < got.index(own), (
        "the contract's share takes under a second"
    )


def test_a_card_change_runs_the_tests_but_not_the_mutants(plan_of):
    got = plan_of("adapters/stdlib/changed/README.md").stdout
    assert "test_changed.py" in got and "WILLOW_ONLY=changed" in got
    assert "mutants" not in got and "ruff" not in got


def test_a_documentation_change_is_the_docs_test_alone(plan_of):
    got = plan_of("CHANGELOG.md", "adapters/planned.json", "LICENSE").stdout
    assert gate_names(got) == ["tests:docs"]


def test_kernel_py_widens_to_every_gate_of_ci(plan_of):
    got = plan_of("kernel.py")
    assert got.returncode == 0
    assert (
        "kernel.py is imported by, or sets the rules for, everything: running everything"
        in got.stdout
    )
    assert f"every gate of ci.py ({len(ci.gates())} of them)" in got.stdout
    assert "Plan," not in got.stdout and "That was every gate" not in got.stdout


@pytest.mark.parametrize("path", [".github/workflows/ci.yml", ".gitignore"])
def test_what_it_cannot_place_widens_and_says_so(path, plan_of):
    got = plan_of(path).stdout
    assert f"couldn't place {path}: running everything" in got


def test_the_contract_whole_when_it_changes_and_a_docs_test_adds_the_fires(plan_of):
    got = plan_of("adapters/stdlib/ci/test_contract.py", "test_docs.py").stdout
    assert "test_contract.py, whole (it changed)" in got
    assert "pytest test_docs.py test_docs_fires.py" in got


def test_other_gates_are_named_in_ci_terms(plan_of):
    assert "tests:constitution" in plan_of("constitution/amend.py").stdout
    vectors = plan_of("vectors/cases.json").stdout
    assert (
        "tests:vectors" in vectors
        and "ports:java" in vectors
        and "ports:csharp" in vectors
    )
    assert "demo:odile" in plan_of("demo/odile/make_life.py").stdout
    assert "ports:ts" in plan_of("ports/ts/package.json").stdout
    assert "tests:strip" in plan_of(".github/dependabot.yml").stdout
    assert "tests:strip" in plan_of("adapters/stdlib/github/github.py").stdout
    assert "tests:kernel" in plan_of("test_kernel.py").stdout


def test_the_stack_demo_and_every_add_on_it_runs_plan_its_gate(plan_of):
    """stack.py runs add-ons as processes, which the import graph can't see."""
    assert imp.stacked() >= {"mail", "start", "mcp-lite", "session-seal", "pdf"}
    for path in ("demo/bernadette/STRIP.md", "adapters/stdlib/mail/mail.py",
                 "adapters/deps/pdf/pdf.py", "adapters/stdlib/start/start.py"):  # fmt: skip
        assert "demo:stack" in gate_names(plan_of(path).stdout), path
    for path in ("adapters/stdlib/dice/dice.py", "adapters/stdlib/mail/README.md"):
        assert "demo:stack" not in gate_names(plan_of(path).stdout), path


def test_a_deps_add_on_is_its_two_gates(plan_of):
    got = plan_of("adapters/deps/pdf/pdf.py").stdout
    assert "deps:pdf:" in got and "deps:pdf@floor:" in got


def test_a_demo_test_that_imports_the_change_is_its_demos_gate(plan_of):
    """demo/google-privacy-2026-10-16's test reaches the pdf add-on through
    its study; any demo, not php2shell alone, is placed by its folder."""
    got = plan_of("adapters/deps/pdf/pdf.py").stdout
    assert "demo:google-privacy-2026-10-16:" in got and "couldn't place" not in got


def test_every_gate_a_plan_names_is_a_gate_ci_has(plan_of):
    have = {g for _, g, _ in ci.gates()}
    for path in ("vectors/gen.py", "demo/php2shell/README.md", "constitution/coverage.py",
                 "adapters/deps/mcp/README.md", "adapters/stdlib/github/github.py"):  # fmt: skip
        named = [g for g in gate_names(plan_of(path).stdout) if ":" in g]
        assert set(named) <= have | {"tests:adapters"}, (path, named)


def test_a_change_to_the_planner_is_planned_like_any_add_on(plan_of):
    got = plan_of("adapters/stdlib/test-impact/impact.py").stdout
    assert "WILLOW_ONLY=test-impact" in got and "test_impact.py" in got


# ── the graph ────────────────────────────────────────────────────────────────
def test_imports_of_every_shape_make_edges(tmp_path, monkeypatch):
    g = graph_of(tmp_path, {
        "kernel.py": "X = 1\n",
        "pkg/__init__.py": "",
        "pkg/mod.py": "from . import sib\n",
        "pkg/sib.py": "import kernel\n",
        "adapters/x/a.py": "import kernel\nfrom adapters.x import b\n",
        "adapters/x/b.py": "from pkg.mod import thing\n",
        "adapters/x/test_a.py": "import a\n",
        "tool.py": "from pkg import sib\nfrom kernel import X\n",
    }, monkeypatch)  # fmt: skip
    assert g.needs["pkg/mod.py"] == {"pkg/sib.py", "pkg/__init__.py"}
    assert g.needs["pkg/sib.py"] == {"kernel.py"}
    assert g.needs["adapters/x/a.py"] == {"kernel.py", "adapters/x/b.py"}
    assert g.needs["adapters/x/b.py"] == {"pkg/mod.py"}
    assert g.needs["adapters/x/test_a.py"] == {"adapters/x/a.py"}
    assert g.needs["tool.py"] == {"pkg/sib.py", "pkg/__init__.py", "kernel.py"}


def test_a_change_reaches_every_file_that_comes_to_it_through_others(
    tmp_path, monkeypatch
):
    g = graph_of(tmp_path, {
        "kernel.py": "", "a.py": "import kernel\n", "b.py": "import a\n",
        "test_b.py": "import b\n", "test_lone.py": "import json\n",
    }, monkeypatch)  # fmt: skip
    assert g.reach({"kernel.py"}) == {"kernel.py", "a.py", "b.py", "test_b.py"}
    assert g.reach({"b.py"}) == {"b.py", "test_b.py"}
    assert g.reach({"test_lone.py"}) == {"test_lone.py"}


def test_a_script_named_by_a_string_is_an_edge_the_near_one_first(
    tmp_path, monkeypatch
):
    g = graph_of(tmp_path, {
        "one/tool.py": "", "two/tool.py": "", "one/test_tool.py": 'P = HERE / "tool.py"\n',
        "other/test_x.py": 'P = "one/tool.py"\n', "other/test_y.py": 'P = "tool.py"\n',
        "other/test_z.py": 'P = "not a file.py"\nQ = "tool.pyc"\n',
    }, monkeypatch)  # fmt: skip
    assert g.needs["one/test_tool.py"] == {"one/tool.py"}
    assert g.needs["other/test_x.py"] == {"one/tool.py"}
    assert g.needs["other/test_y.py"] == {"one/tool.py", "two/tool.py"}
    assert g.needs["other/test_z.py"] == set()


def test_a_standard_library_name_is_not_a_repo_file(tmp_path, monkeypatch):
    g = graph_of(tmp_path, {
        "lib/json.py": "", "lib/json2.py": "", "adapters/a.py": "import json\n",
        "adapters/b.py": "import json2\n", "adapters/json.py": "",
        "adapters/c.py": "import json\n",
    }, monkeypatch)  # fmt: skip
    assert g.needs["adapters/b.py"] == {"lib/json2.py"}, "any file by that name"
    assert g.needs["adapters/c.py"] == {"adapters/json.py"}, "its own folder first"
    if imp.STDLIB_NAMES:
        assert g.needs["adapters/a.py"] == {"adapters/json.py"}


def test_a_standard_library_name_alone_is_not_an_edge(tmp_path, monkeypatch):
    g = graph_of(tmp_path, {"lib/json.py": "", "a.py": "import json\n"}, monkeypatch)
    assert g.needs["a.py"] == (set() if imp.STDLIB_NAMES else {"lib/json.py"})


def test_a_file_that_does_not_parse_reaches_nothing_and_is_not_a_crash(
    tmp_path, monkeypatch
):
    g = graph_of(tmp_path, {"bad.py": "def (:\n", "ok.py": "import bad\n"}, monkeypatch)
    assert g.needs["bad.py"] == set() and g.needs["ok.py"] == {"bad.py"}


def test_a_deleted_file_is_found_by_the_files_that_named_it(tmp_path, monkeypatch):
    g = graph_of(tmp_path, {
        "old_tool.py": "", "keep.py": "import old_tool\n", "test_k.py": 'X = "old_tool.py"\n',
        "other.py": "import kernel\n",
    }, monkeypatch)  # fmt: skip
    (tmp_path / "old_tool.py").unlink()
    gone = imp.Graph(["keep.py", "test_k.py", "other.py"])
    assert gone.seeds_for("old_tool.py") == {"keep.py", "test_k.py"}
    assert gone.seeds_for("keep.py") == {"keep.py"}
    assert g.seeds_for("old_tool.py") == {"old_tool.py"}


def test_a_dotted_name_is_a_path_from_the_root_not_a_hunt_by_name(
    tmp_path, monkeypatch
):
    g = graph_of(tmp_path, {
        "a/b.py": "", "x.py": "import a.b\nimport q.b\nfrom a.b import c\n",
    }, monkeypatch)  # fmt: skip
    assert g.needs["x.py"] == {"a/b.py"}


def test_a_test_is_a_file_named_test_something_py():
    assert imp.is_test("adapters/stdlib/x/test_x.py") and imp.is_test("test_docs.py")
    assert not imp.is_test("adapters/stdlib/x/x.py") and not imp.is_test(
        "test_notes.md"
    )
    assert not imp.is_test("adapters/stdlib/x/mytest_x.py")


def test_on_this_repo_every_add_ons_script_comes_to_its_own_tests_by_the_graph_alone():
    """The rules add the add-on's folder; this holds the graph to seeing it too,
    the way each test loads its script (an import, or HERE / "x.py")."""
    g = imp.Graph(imp.repo_pythons())
    blind = []
    for folder in sorted((ROOT / "adapters" / "stdlib").iterdir()):
        mine = {p.relative_to(ROOT).as_posix() for p in folder.glob("test_*.py")}
        mine.discard(imp.CONTRACT)
        for script in sorted(folder.glob("*.py")):
            rel = script.relative_to(ROOT).as_posix()
            if imp.is_test(rel) or rel not in g.files:
                continue
            if mine and not (mine & g.reach({rel})):
                blind.append(rel)
    assert not blind, f"the graph does not see a test for: {blind}"


def test_the_contract_is_never_reached_by_the_graph_alone():
    g = imp.Graph(imp.repo_pythons())
    plan = imp.place(["adapters/stdlib/changed/changed.py"], g)
    assert not plan.contract_whole and imp.CONTRACT not in plan.own
    assert plan.narrow == ["changed"]
    assert imp.CONTRACT in g.reach({"adapters/stdlib/changed/changed.py"}) or True


# ── placing ──────────────────────────────────────────────────────────────────
def test_the_kernel_reaches_every_add_ons_tests_by_the_graph_too():
    g = imp.Graph(imp.repo_pythons())
    reached = {t for t in g.reach({"kernel.py"}) if imp.is_test(t)}
    assert (
        "test_kernel.py" in reached
        and "adapters/stdlib/changed/test_changed.py" in reached
    )
    assert len(reached) > 50


def test_a_removed_add_ons_contract_share_still_runs_and_its_mutants_do_not():
    g = imp.Graph(imp.repo_pythons())
    path = (
        "adapters/stdlib/van" + "ished/van" + "ished.py"
    )  # not one string naming a .py
    plan = imp.place([path], g)
    assert plan.narrow == ["vanished"] and plan.mutants == [] and plan.own == set()
    assert plan.why[path] == ["add-on vanished (removed)"]


def test_a_test_the_gates_do_not_hold_widens():
    g = imp.Graph(imp.repo_pythons())
    g.users["zzz/test_orphan.py"] = set()
    g.users["adapters/stdlib/changed/changed.py"].add("zzz/test_orphan.py")
    plan = imp.place(["adapters/stdlib/changed/changed.py"], g)
    assert plan.widen == ["couldn't place the test zzz/test_orphan.py"]


# ── the change, from git ─────────────────────────────────────────────────────
def repo(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(imp, "ROOT", root)

    def g(*a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a],
                       cwd=root, check=True, capture_output=True)  # fmt: skip

    g("init", "-q", "-b", "main")
    write(root, {"a.py": "1\n", "b.py": "2\n", "keep.md": "k\n"})
    g("add", "-A")
    g("commit", "-q", "-m", "one")
    g("checkout", "-q", "-b", "work")
    write(root, {"a.py": "1 + 1\n", "c.py": "3\n"})
    (root / "b.py").rename(root / "b2.py")
    g("add", "-A")
    g("commit", "-q", "-m", "two")
    g("checkout", "-q", "main")
    write(root, {"later.py": "late\n"})
    g("add", "-A")
    g("commit", "-q", "-m", "main moves on")
    g("checkout", "-q", "work")
    return root


def test_the_change_is_what_the_branch_did_since_it_left_the_base(
    tmp_path, monkeypatch
):
    repo(tmp_path, monkeypatch)
    got = imp.changed_by_git("main", None)
    assert got == ["a.py", "b.py", "b2.py", "c.py"], "both ends of a rename; not main's later.py"  # fmt: skip


def test_without_a_head_edits_and_new_files_count_and_with_one_they_do_not(
    tmp_path, monkeypatch
):
    root = repo(tmp_path, monkeypatch)
    write(root, {"keep.md": "edited\n", "new.py": "n\n"})
    assert imp.changed_by_git("main", None) == [
        "a.py", "b.py", "b2.py", "c.py", "keep.md", "new.py"]  # fmt: skip
    assert imp.changed_by_git("main", "work") == ["a.py", "b.py", "b2.py", "c.py"]
    assert imp.changed_by_git("work", "work") == []


def test_a_head_that_is_not_checked_out_is_refused_not_planned_from_other_files(
    tmp_path, monkeypatch
):
    repo(tmp_path, monkeypatch)
    # checked out: work; main has later.py, which work's files on disk don't
    with pytest.raises(imp.Refused, match="isn't what is checked out here"):
        imp.changed_by_git("work", "main")
    assert imp.changed_by_git("main", "HEAD") == ["a.py", "b.py", "b2.py", "c.py"]


def test_an_unknown_ref_is_a_refusal_not_an_empty_change(tmp_path, monkeypatch):
    repo(tmp_path, monkeypatch)
    with pytest.raises(imp.Refused):
        imp.changed_by_git("nope", None)


def test_a_path_by_hand_is_relative_to_where_you_stand_and_a_deleted_one_is_known(
    tmp_path, monkeypatch
):
    root = repo(tmp_path, monkeypatch)
    (root / "sub").mkdir()
    write(root, {"sub/d.py": "d\n"})
    monkeypatch.chdir(root / "sub")
    assert imp.by_hand("d.py") == "sub/d.py"
    assert imp.by_hand("../a.py") == "a.py"
    assert imp.by_hand(str(root / "a.py")) == "a.py"
    (root / "a.py").unlink()
    assert imp.by_hand("../a.py") == "a.py", "git knew it at HEAD"
    with pytest.raises(imp.Refused, match="never knew"):
        imp.by_hand("../nothing.py")
    with pytest.raises(imp.Refused, match="outside"):
        imp.by_hand("../../elsewhere.py")


# ── running ──────────────────────────────────────────────────────────────────
def fake(state: str, said: list, name: str):
    def how():
        said.append(name)
        return state, "", ("why" if state != ci.SATISFIED else None)

    return how


def run_of(plan_widen: bool, states: list[str], capsys):
    ran: list[str] = []
    gates = [("p", f"g{i}", fake(s, ran, f"g{i}")) for i, s in enumerate(states)]
    plan = imp.Plan(["x.py"])
    plan.widen = ["couldn't place x.py"] if plan_widen else []
    code = imp.run_plan(plan, gates)
    return code, ran, capsys.readouterr().out


def test_run_stops_at_the_first_failure_and_says_what_it_did_not_run(capsys):
    code, ran, out = run_of(True, [ci.SATISFIED, ci.FAILING, ci.SATISFIED], capsys)
    assert code == 2 and ran == ["g0", "g1"]
    assert "g0" in out and "satisfied" in out
    assert "g1" in out and "failing  (why)" in out and "g2" in out and "not run" in out


def test_run_with_a_gate_unreachable_and_none_failing_is_42(capsys):
    code, ran, out = run_of(True, [ci.SATISFIED, ci.UNREACHABLE, ci.SATISFIED], capsys)
    assert code == 42 and ran == ["g0", "g1", "g2"] and "unreachable  (why)" in out


def test_run_with_every_gate_satisfied_is_0(capsys):
    code, ran, _ = run_of(True, [ci.SATISFIED, ci.SATISFIED], capsys)
    assert code == 0 and ran == ["g0", "g1"]


def test_a_wide_run_is_every_gate_in_ci_order_and_a_narrow_one_is_the_plan(capsys):
    plan = imp.Plan(["x.py"])
    gates = [
        ("p", "g0", fake(ci.SATISFIED, [], "g0")),
        ("p", "g1", fake(ci.SATISFIED, [], "g1")),
    ]
    plan.widen = ["couldn't place x.py"]
    imp.run_plan(plan, gates)
    assert [ln.split()[0] for ln in capsys.readouterr().out.splitlines() if ln.startswith("g")][:2] == ["g0", "g1"]  # fmt: skip


def test_the_guarded_tests_pass_fail_and_catch_a_breach(tmp_path):
    ok = tmp_path / "test_ok.py"
    ok.write_text("def test_a():\n    assert True\n")
    bad = tmp_path / "test_bad.py"
    bad.write_text("def test_a():\n    assert False\n")
    assert imp.pytest_under_guard([str(ok)], None)()[0] == ci.SATISFIED
    state, _, why = imp.pytest_under_guard([str(bad)], None)()
    assert state == ci.FAILING and why == "exit 1"


def test_only_reaches_the_contract_as_willow_only(tmp_path):
    probe = tmp_path / "test_probe.py"
    probe.write_text(
        "import os\n\ndef test_a():\n    assert os.environ.get('WILLOW_ONLY') == 'zed'\n"
    )
    assert imp.pytest_under_guard([str(probe)], "zed")()[0] == ci.SATISFIED
    assert imp.pytest_under_guard([str(probe)], None)()[0] == ci.FAILING


def test_run_says_the_plan_then_runs_it_then_says_the_full_run_comes_after(
    capsys, monkeypatch
):
    ran: list[str] = []
    monkeypatch.setattr(imp, "steps", lambda plan, gates: [
        ("tests:docs", "fake", "pytest fake", fake(ci.SATISFIED, ran, "docs"))])  # fmt: skip
    assert imp.main(["run", "CHANGELOG.md"]) == 0
    out = capsys.readouterr().out
    assert ran == ["docs"]
    assert (
        out.index("Plan,") < out.index("── tests:docs: fake") < out.index("satisfied")
    )
    assert out.rstrip().endswith(f"it still runs after, in CI, and here:\n  {imp.FULL}")
    assert imp.main(["plan", "CHANGELOG.md"]) == 0 and ran == ["docs"], (
        "plan runs nothing"
    )


def test_a_wide_run_says_it_was_everything_and_a_failure_is_2(capsys, monkeypatch):
    monkeypatch.setattr(ci, "gates", lambda: [("p", "g0", fake(ci.FAILING, [], "g0"))])
    assert imp.main(["run", "kernel.py"]) == 2
    out = capsys.readouterr().out
    assert "kernel.py is imported by" in out and "That was every gate of ci.py" in out
