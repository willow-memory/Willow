"""The CI one-script: verdict rows on a kernel record, the same every run.

Each test holds one promise in adapters/stdlib/ci/README.md, and each can fail: the
record is byte-for-byte the same for the same files, a missing tool is
unreachable (not failing, not a pass), a failing command is failing, and the
record holds only ci verdicts, which `verify` checks along with the kernel's
own chain.
"""

from __future__ import annotations

import importlib.util
import json
import types
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ci", HERE / "ci.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
k = ci.kernel
NOW = "2026-10-23T00:00:00Z"
# The gates the runs below drive: two, so their order is tested, and the
# cheapest that a machine with only pytest satisfies (about a second, where
# the demo part took 50 s a run). Nothing here asks what a gate does.
PART = ["tests:beats", "tests:coverage"]


def cli(*argv: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "ci.py"), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


def rows(box: Path) -> list[dict]:
    return k.read(box / "record.jsonl")[0]


def test_the_same_files_give_the_same_record_byte_for_byte(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for box in (a, b):
        assert cli("run", *PART, "--box", str(box), "--now", NOW).returncode == 0
    assert (a / "record.jsonl").read_bytes() == (b / "record.jsonl").read_bytes()
    made = rows(a)
    assert [r["gate"] for r in made[1:]] == PART
    assert {r["state"] for r in made[1:]} == {ci.SATISFIED}


def test_what_changes_between_runs_never_reaches_a_row():
    once = f"wrote 3 files to {ci.ROOT}/x in 0.31s\n9 passed in 12.5s"
    again = f"wrote 3 files to {ci.ROOT}/x in 2.04s\n9 passed in 1s"
    assert ci.steady(once) == ci.steady(again)
    assert ci.steady("9 passed") != ci.steady("8 passed")


def test_a_missing_tool_is_unreachable_not_failing(tmp_path):
    """No JDK, Node or .NET on PATH: every port is unreachable, exit 42."""
    bare = tmp_path / "bin"
    bare.mkdir()
    (bare / "git").symlink_to(subprocess.run(
        ["sh", "-c", "command -v git"], capture_output=True, text=True
    ).stdout.strip())  # fmt: skip
    env = {**os.environ, "PATH": str(bare)}
    box = tmp_path / "box"
    got = cli("run", "ports", "--box", str(box), "--now", NOW, env=env)
    assert got.returncode == k.ESCALATE, got.stdout + got.stderr
    made = rows(box)[1:]
    assert [r["state"] for r in made] == [ci.UNREACHABLE] * len(ci.PORTS)
    assert all("not on PATH" in r["why"] for r in made)


def test_needs_says_what_cant_run_here_without_running_anything(tmp_path):
    """The same bare PATH: `needs` names every port as unreachable, as `run`
    would find them, writes no record, and says deps can only be known by
    running; a gate whose needs are met is said to run here."""
    bare = tmp_path / "bin"
    bare.mkdir()
    env = {**os.environ, "PATH": str(bare)}
    got = cli("needs", "ports", env=env)
    assert got.returncode == k.ESCALATE, got.stdout + got.stderr
    said = got.stdout.splitlines()
    assert said[0] == (
        f"needs: {len(ci.PORTS)} gates; 0 can run here, {len(ci.PORTS)} would be"
        " unreachable, 0 known only by running"
    )
    assert all("unreachable:" in s and "not on PATH" in s for s in said[1:])
    assert len(said) == 1 + len(ci.PORTS)
    got = cli("needs", "deps:floors")
    assert got.returncode == k.ESCALATE
    assert "only a run can tell" in got.stdout
    got = cli("needs", "tests:docs")
    assert (got.returncode, got.stdout) == (
        k.ALIVE,
        "needs: 1 gate; 1 can run here, 0 would be unreachable, 0 known only by running\n",
    )
    assert cli("needs", "tests:strpi").returncode == k.REFUSED
    # it takes no record to write to
    assert cli("needs", "--box", str(tmp_path)).returncode == k.REFUSED


def test_needs_asks_what_a_gate_needs_before_saying_only_a_run_can_tell(
    monkeypatch, capsys
):
    """A gate that installs from PyPI and runs a program this machine lacks
    is unreachable here, known now; one whose needs are met is still known
    only by running."""

    def gate(needs=None, online=None):
        def how():
            raise AssertionError("needs runs no gate")

        how.needs = lambda: needs
        if online:
            how.online = online
        return how

    fake = [("deps", "deps:a", gate("tesseract not on PATH", "installs")),
            ("deps", "deps:b", gate(None, "installs")),
            ("demo", "demo:c", gate())]  # fmt: skip
    monkeypatch.setattr(ci, "gates", lambda: fake)
    assert ci.do_needs([]) == k.ESCALATE
    said = capsys.readouterr().out.splitlines()
    assert said[0] == (
        "needs: 3 gates; 1 can run here, 1 would be unreachable,"
        " 1 known only by running"
    )
    assert said[1].split() == [
        "deps:a",
        "unreachable:",
        "tesseract",
        "not",
        "on",
        "PATH",
    ]
    assert said[2].split()[:2] == ["deps:b", "only"]


def test_a_failing_command_is_failing_and_a_judge_can_fail_a_zero_exit():
    state, _, why = ci.command(sys.executable, "-c", "raise SystemExit(3)")()
    assert (state, why) == (ci.FAILING, "exit 3")
    skipped = "  java    25/25 session checks ok\nunexplained differences: 0\n"
    assert ci.port_ran("java")(skipped) is None
    assert ci.port_ran("ts")(skipped) == "ts: no full session line"
    assert ci.code_of([ci.SATISFIED, ci.UNREACHABLE, ci.FAILING]) == k.REFUSED
    assert ci.code_of([ci.SATISFIED, ci.UNREACHABLE]) == k.ESCALATE
    assert ci.code_of([ci.SATISFIED]) == k.ALIVE
    assert ci.code_of([]) == k.ESCALATE  # nothing checked is not a pass


def test_a_skipped_test_is_said_on_its_row_and_never_changes_its_state(
    tmp_path, monkeypatch, capsys
):
    """A skip is no pass of that test: its gate's row says how many and why,
    with no machine's path in it, and the gate's state is what it was."""
    skips, clean = tmp_path / "skips", tmp_path / "clean"
    for d in (skips, clean):
        d.mkdir()
    (skips / "test_s.py").write_text(
        "import pytest\n"
        "def test_ran(): pass\n"
        "def test_gone(): pytest.skip('no vim (here)')\n"
        "def test_also_gone(): pytest.skip('not Linux')\n"
    )
    (clean / "test_c.py").write_text("def test_ran(): pass\n")
    fake = [("tests", "tests:skips", ci.command(*ci.PYTEST, str(skips))),
            ("tests", "tests:clean", ci.command(*ci.PYTEST, str(clean)))]  # fmt: skip
    monkeypatch.setattr(ci, "gates", lambda: fake)
    box = tmp_path / "box"
    assert ci.do_run(box, ["tests:skips", "tests:clean"], NOW) == k.ALIVE
    made = rows(box)[1:]
    assert [r["state"] for r in made] == [ci.SATISFIED, ci.SATISFIED]
    said = made[0]["skipped"]
    assert said.startswith("2 skipped: ") and "no vim (here)" in said
    assert "not Linux" in said and str(tmp_path) not in said
    assert "skipped" not in made[1]
    assert ci.do_verify(box) == k.ALIVE
    printed = capsys.readouterr().out
    assert "tests:skips        satisfied  [2 skipped: " in printed
    assert "tests:clean        satisfied\n" in printed
    assert ci.do_show(box) == k.ALIVE
    assert "row 1  [2 skipped: " in capsys.readouterr().out
    assert ci.skipped("3 passed in 0.1s") is None


def test_verify_holds_the_chain_and_refuses_anything_but_ci_verdicts(tmp_path):
    box = tmp_path / "box"
    assert cli("run", *PART, "--box", str(box), "--now", NOW).returncode == 0
    assert cli("verify", "--box", str(box)).returncode == k.ALIVE
    made = rows(box)
    assert all(
        r["kind"] == "verdict" and r["standing"] == "unattested" for r in made[1:]
    )

    seal = box.parent / "seal"  # a seal row, written by hand through the kernel
    seal.mkdir()
    (seal / "record.jsonl").write_bytes((box / "record.jsonl").read_bytes())
    (seal / "kernel.json").write_bytes((box / "kernel.json").read_bytes())
    k.append(seal, NOW, "seal", who="human", subject="proposal:" + "0" * 64, proof="0")
    got = cli("verify", "--box", str(seal))
    assert got.returncode == k.REFUSED and "not a ci verdict" in got.stdout

    path = box / "record.jsonl"  # one field of one past row edited
    path.write_bytes(path.read_bytes().replace(b'"satisfied"', b'"failing"', 1))
    assert cli("verify", "--box", str(box)).returncode == k.REFUSED
    assert cli("show", "--box", str(box)).returncode == k.REFUSED


def test_the_gates_run_in_one_fixed_order_and_cover_every_part():
    names = [g for _, g, _ in ci.gates()]
    assert names == [
        "lint:check", "lint:format", "lint:py39",
        "tests:beats", "tests:kernel", "tests:docs",
        *(f"tests:adapters-{k}" for k in range(1, ci.ADAPTER_CHUNKS + 1)),
        "tests:alone",
        "tests:ui",
        "tests:vectors",
        *(f"tests:strip-{k}" for k in range(1, ci.STRIP_CHUNKS + 1)),
        "tests:constitution", "tests:coverage",
        *(f"ports:{p}" for p in ci.PORTS),
        *sorted([*(f"demo:{p}" for p in ci.people()), "demo:craft-assembly", "demo:five-repos",
                 "demo:google-privacy-2026-10-16", "demo:known-gaps", "demo:novelty", "demo:ofrenda-frozen",
                 "demo:php2shell", "demo:redteam", "demo:share", "demo:small-models", "demo:stack",
                 "demo:stewart-crossover-frozen", "demo:teodora-words",
                 *(g for g, _, _ in ci.demo_tests()[len(ci.DEMO_TESTS):])]),
        *(g for d in ci.deps_add_ons() for g in (f"deps:{d}", f"deps:{d}@floor")),
        "deps:advisories",
        "deps:floors",
        *(f"mutants:{n}" for n in ci.mutant_targets()),
        *(f"tools:{n}" for n in ci.live_checks()),
    ]  # fmt: skip
    assert ci.live_checks()[:2] == ["bash", "zsh"]
    assert {p for p, _, _ in ci.gates()} == set(ci.PARTS)


def test_every_test_file_under_demo_is_run_by_a_gate():
    # a demo's tests that no gate names never fail: ofrenda's, stewart-
    # crossover's and small-models' went unrun, and one broke unseen
    targets = [t for _, t, _ in ci.demo_tests()]
    under = lambda f, t: f == t or f.startswith(t + "/")  # noqa: E731
    files = sorted(
        p.relative_to(ci.ROOT).as_posix()
        for p in (ci.ROOT / "demo").rglob("test_*.py")
        if "__pycache__" not in p.parts
    )
    assert files and [f for f in files if not any(under(f, t) for t in targets)] == []
    assert all((ci.ROOT / t).exists() for t in targets)


def test_a_demo_with_tests_and_no_row_gets_a_gate_of_its_own(monkeypatch, tmp_path):
    """No row to write for a new demo's tests: its folder's name is its gate,
    beside a person's own gate when it has one; a file at demo/'s top too."""
    for rel in ("demo/fresh/test_fresh.py", "demo/odile/make_life.py",
                "demo/odile/test_words.py", "demo/test_loose.py",
                "demo/php2shell/test_php2shell.py", "demo/plain/README.md"):  # fmt: skip
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("")
    monkeypatch.setattr(ci, "ROOT", tmp_path)
    monkeypatch.setattr(ci, "DEMO_TESTS", (("demo:php2shell", "demo/php2shell", ()),))
    assert ci.demo_tests() == [
        ("demo:php2shell", "demo/php2shell", ()),
        ("demo:fresh", "demo/fresh", ()),
        ("demo:odile-tests", "demo/odile", ()),
        ("demo:loose", "demo/test_loose.py", ()),
    ]


def test_shards_run_every_gate_of_what_was_named_once_in_its_order():
    every = ci.select(["mutants"], [], None)
    assert every == [f"mutants:{n}" for n in ci.mutant_targets()]
    for n in (1, 2, 3, 7):
        parts = [ci.select(["mutants"], [], f"{k}/{n}") for k in range(1, n + 1)]
        assert sorted(g for p in parts for g in p) == sorted(every), n
        assert all(p == [g for g in every if g in p] for p in parts)
    assert ci.select(["mutants"], [], "1/1") == every


def test_every_gate_weighs_a_whole_number_of_seconds_of_at_least_one():
    for _, gate, _ in ci.gates():
        weight = ci.gate_weight(gate)
        assert isinstance(weight, int) and weight >= 1, gate


def test_a_gate_weighs_what_its_tests_took():
    times = json.loads(ci.TIMES.read_text(encoding="utf-8"))
    own = sum(t for f, t in times.items() if f.startswith("adapters/stdlib/ci/"))
    mine = ci.gate_weight("mutants:ci")
    assert mine == round(ci.MUTANT_COPY + ci.MUTANT_BREAKS * ci.TIMES_TO_RUNNER * own)
    assert mine > 10 * ci.gate_weight("mutants:accents"), "ci's tests are the slow ones"
    chunk = ci.adapter_parts()[2]
    median = sorted(times.values())[len(times) // 2]
    want = ci.TIMES_TO_RUNNER * sum(times.get(f, median) for f in chunk)
    assert ci.gate_weight("tests:adapters-3") == round(want)
    assert ci.gate_weight("tests:alone") == ci.GATE_COST["tests:alone"]
    assert ci.gate_weight("tests:strip-1") == ci.DEFAULT_COST, "nothing prices it"


def test_the_mutants_shards_end_closer_together_than_a_cut_by_count():
    split = ci.load_shards().split
    every = ci.select(["mutants"], [], None)

    def seconds(cut):
        return [sum(ci.gate_weight(g) for g in part) for part in cut]

    by_count = seconds(split(dict.fromkeys(every, 1), 4))
    by_time = seconds(split({g: ci.gate_weight(g) for g in every}, 4))
    parts = [ci.select(["mutants"], [], f"{k}/4") for k in range(1, 5)]
    assert seconds(parts) == by_time, "select cuts by time"
    assert max(by_time) - min(by_time) < (max(by_count) - min(by_count)) / 4
    assert max(by_time) < max(by_count)


def test_a_gate_is_named_or_left_out_by_name():
    tests = [g for p, g, _ in ci.gates() if p == "tests"]
    strip = [g for g in tests if g.startswith("tests:strip-")]
    assert ci.select(["tests:strip-2"], [], None) == ["tests:strip-2"]
    assert ci.select(["tests:strip"], [], None) == strip  # a group is its chunks
    assert ci.select(["tests"], ["tests:strip"], None) == [g for g in tests if g not in strip]  # fmt: skip
    assert ci.select(["lint", "tests:strip-1"], [], None) == ["lint:check", "lint:format", "lint:py39", "tests:strip-1"]  # fmt: skip
    assert ci.select([], [], None) == [g for _, g, _ in ci.gates()]


def test_the_add_on_tests_are_cut_with_none_dropped_twice_or_left_empty():
    files = ci.adapter_tests()
    cut = ci.chunks(files, ci.ADAPTER_CHUNKS)
    assert sorted(f for part in cut for f in part) == files
    assert all(cut), "an empty chunk would run all of pytest's default paths"
    # what pytest itself collects from adapters/stdlib, file by file
    got = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "adapters/stdlib"],
        cwd=ci.ROOT, capture_output=True, text=True,
    )  # fmt: skip
    collected = {ln.split("::")[0] for ln in got.stdout.splitlines() if "::" in ln}
    assert collected == set(files), sorted(collected ^ set(files))


@pytest.mark.parametrize("argv", [["tests:strpi"], ["--without", "tests"], ["--without", "nope"],
                                  ["--shard", "0/3"], ["--shard", "4/3"], ["--shard", "1/0"],
                                  ["--shard", "x"], ["--shard"], ["--without"], ["--stray"]])  # fmt: skip
def test_what_it_doesnt_know_is_refused_and_runs_nothing(tmp_path, argv):
    box = tmp_path / "box"
    got = cli("run", *PART, *argv, "--box", str(box), "--now", NOW)
    assert got.returncode == 2
    assert not box.exists(), "refused before the record is made"
    assert got.stderr.startswith(
        ("refused: ", "    python adapters/stdlib/ci/ci.py run")
    )


def test_leaving_out_a_part_is_refused_by_name():
    got = cli("run", "--without", "tests", "--box", "/nonexistent/box", "--now", NOW)
    assert (
        got.returncode == 2
        and "--without takes a gate, and tests is a part" in got.stderr
    )


def test_a_shard_on_the_command_line_writes_only_its_gates(tmp_path):
    box = tmp_path / "box"
    assert cli("run", *PART, "--shard", "2/2", "--box", str(box), "--now", NOW).returncode == 0  # fmt: skip
    assert [r["gate"] for r in rows(box)[1:]] == ci.select(PART, [], "2/2")


def test_a_record_inside_the_repo_where_git_would_count_it_is_refused(tmp_path):
    """It would be hashed into the files it records (the first CI run did
    exactly this, and the docs test caught the files it left)."""
    inside = ci.ROOT / "ci-record-test-only"
    try:
        got = cli("run", *PART, "--box", str(inside), "--now", NOW)
        assert got.returncode != 0 and "not ignored by git" in got.stderr
        assert not inside.exists()
        assert not inside.with_name(inside.name + ".key").exists()
    finally:  # even when it fails: nothing may be left in the repo
        if inside.exists():
            import shutil

            shutil.rmtree(inside)
        inside.with_name(inside.name + ".key").unlink(missing_ok=True)
    ok = cli("run", *PART, "--box", str(tmp_path / "out"), "--now", NOW)
    assert ok.returncode == 0  # outside the repo is fine


def test_the_floor_rule_takes_the_last_release_of_2020_else_the_first():
    old = {"1.0": "2019-03-01T00:00:00Z", "1.1": "2020-12-31T23:00:00Z",
           "0.9": "2021-02-01T00:00:00Z", "2.0": "2022-01-01T00:00:00Z"}  # fmt: skip
    assert ci.rule_floor(old) == "1.1"  # by upload time: 0.9 came out after 1.1
    assert (
        ci.rule_floor({"0.1": "2024-11-20T00:00:00Z", "1.0": "2025-01-01T00:00:00Z"})
        == "0.1"
    )


def test_a_floor_above_the_rule_needs_a_reason_on_its_card(monkeypatch):
    # PyPI's own dates for each floor pin and the rule's release, kept by
    # pypi_dates.py write: no package is typed here by hand
    uploaded = json.loads((ci.ROOT / "adapters/stdlib/ci/pypi-dates.json").read_text())
    monkeypatch.setattr(ci, "releases", lambda package: uploaded[package])
    assert ci.floors()[0] == ci.SATISFIED
    monkeypatch.setattr(ci, "floor_line", lambda name: "")
    state, _, why = ci.floors()
    assert state == ci.FAILING and "gives no reason" in why

    def offline(package):
        raise OSError("no network")

    monkeypatch.setattr(ci, "releases", offline)
    assert ci.floors()[0] == ci.UNREACHABLE


def test_an_advisory_on_a_pin_fails_and_on_a_floor_is_only_said(monkeypatch):
    def found(path):
        if path.name == "requirements.txt" and path.parent.name == "pdf":
            return [("pypdf", "1.0", "PYSEC-1", "2.0")]
        if path.name == "requirements-floor.txt" and path.parent.name == "mcp":
            return [("mcp", "0.1", "GHSA-x", "")]
        return []

    monkeypatch.setattr(ci, "audit", found)
    state, said, why = ci.advisories()
    assert state == ci.FAILING
    assert why == "pdf: pypdf==1.0 in requirements.txt has PYSEC-1, fixed in 2.0"
    assert "mcp: mcp==0.1 floor has 1 advisory, said, not failed" in said
    monkeypatch.setattr(ci, "audit", lambda path: [] if path.parent.name == "pdf"
                        else found(path))  # fmt: skip
    assert ci.advisories()[0] == ci.SATISFIED

    def offline(path):
        raise OSError("no network")

    monkeypatch.setattr(ci, "audit", offline)
    assert ci.advisories()[0] == ci.UNREACHABLE


def test_audit_reads_pip_audits_json(monkeypatch):
    answer = json.dumps({"dependencies": [
        {"name": "llm", "version": "0.27", "vulns": [{"id": "PYSEC-2026-400", "fix_versions": []}]},
        {"name": "pyyaml", "version": "5.3.1", "vulns": [{"id": "PYSEC-2021-142", "fix_versions": ["5.4"]}]},
        {"name": "ok", "version": "1", "vulns": []},
    ]})  # fmt: skip
    monkeypatch.setattr(ci.subprocess, "run", lambda *a, **k: types.SimpleNamespace(
        stdout=answer, stderr="", returncode=1))  # fmt: skip
    assert ci.audit(ci.ROOT / "requirements.txt") == [
        ("llm", "0.27", "PYSEC-2026-400", ""),
        ("pyyaml", "5.3.1", "PYSEC-2021-142", "5.4"),
    ]
    monkeypatch.setattr(ci.subprocess, "run", lambda *a, **k: types.SimpleNamespace(
        stdout="", stderr="ConnectionError: no route\n", returncode=1))  # fmt: skip
    try:
        ci.audit(ci.ROOT / "requirements.txt")
    except OSError as exc:
        assert "no route" in str(exc)
    else:
        raise AssertionError("an unreadable answer is unreachable, not clean")


def test_a_program_a_deps_card_names_and_this_machine_lacks_is_unreachable(
    monkeypatch,
):
    """ocr runs tesseract, which PyPI doesn't install: without it on PATH
    deps:ocr is unreachable, asked before any install, never failing. A deps
    add-on whose card names no program is left to its install and tests."""
    assert ci.programs_of("ocr") == ("tesseract",)
    assert ci.programs_of("kart") == ("bwrap",)
    assert ci.programs_of("pdf") == ()
    monkeypatch.setenv("PATH", "")

    class Made(Exception):
        """ci.py went on to make a virtual environment"""

    def made(*a, **kw):
        raise Made

    monkeypatch.setattr(ci.subprocess, "run", made)
    for pins in ("requirements.txt", "requirements-floor.txt"):
        state, said, why = ci.deps_add_on("ocr", pins)()  # Made, were it run
        assert (state, said) == (ci.UNREACHABLE, "")
        assert why == "tesseract not on PATH, which its card's programs: names"
        # the same, asked without a run, for `ci.py needs`
        assert ci.deps_add_on("ocr", pins).needs() == why
    assert ci.deps_add_on("pdf").needs() is None
    with pytest.raises(Made):  # pdf names no program: on to its install
        ci.deps_add_on("pdf")()


# ── a deps gate held by an earlier satisfied verdict with its key ────────────
def earlier(tmp_path: Path, *rows: tuple[str, str, str]) -> Path:
    """A ci record holding a verdict per (gate, state, key): what main's
    deps run uploads, as a pull request's deps job downloads it."""
    box = tmp_path / "main-record"
    ts = "2026-11-06T00:00:00Z"
    ci.open_box(box, ts)
    for gate, state, key in rows:
        ci.kernel.append(box, ts, "verdict", who=ci.WHO, gate=gate, state=state,
                         files_sha256="0" * 64, said_sha256="0" * 64, python="3.13",
                         key=key)  # fmt: skip
    return box / "record.jsonl"


def test_a_deps_key_is_what_its_run_rests_on():
    pdf = ci.deps_key("pdf", "requirements.txt")
    assert pdf == ci.deps_key("pdf", "requirements.txt"), "the same files, the same key"
    assert pdf != ci.deps_key("pdf", "requirements-floor.txt")
    assert pdf != ci.deps_key("ocr", "requirements.txt")
    listed = subprocess.run(["git", "ls-files", "--", "adapters/deps/pdf", *ci.DEPS_RESTS_ON],
                            cwd=ci.ROOT, capture_output=True, text=True).stdout.split()  # fmt: skip
    assert "adapters/deps/pdf/requirements.txt" in listed and "kernel.py" in listed
    assert any(p.startswith("adapters/stdlib/ci/guard/") for p in listed)


def test_a_deps_key_changes_with_any_file_it_rests_on(monkeypatch, tmp_path):
    """The key hashes bytes, so a change to the add-on, the kernel or the guard
    is a new key, and the gate runs."""
    real = ci.Path.read_bytes
    before = ci.deps_key("pdf", "requirements.txt")
    for changed in ("adapters/deps/pdf/requirements.txt", "kernel.py",
                    "adapters/stdlib/ci/guard/sitecustomize.py"):  # fmt: skip
        target = ci.ROOT / changed

        def read(self, target=target):
            return real(self) + (b"\n# changed" if self == target else b"")

        monkeypatch.setattr(ci.Path, "read_bytes", read)
        assert ci.deps_key("pdf", "requirements.txt") != before, changed
        monkeypatch.setattr(ci.Path, "read_bytes", real)


def test_a_deps_gate_with_a_satisfied_verdict_for_its_key_is_held_not_run(
    monkeypatch, tmp_path
):
    gate = ci.deps_add_on("pdf")
    key = gate.key()
    record = earlier(tmp_path, ("deps:pdf", ci.SATISFIED, key))
    monkeypatch.setenv(ci.HELD, str(record))

    def ran(*a, **kw):
        raise AssertionError("a held gate installs nothing")

    real_run = ci.subprocess.run
    monkeypatch.setattr(ci.subprocess, "run", lambda argv, *a, **kw: (
        real_run(argv, *a, **kw) if argv[:2] == ["git", "ls-files"] else ran()))  # fmt: skip
    state, said, why = gate()
    assert (state, why) == (ci.SATISFIED, None)
    assert said == f"held: unchanged since its satisfied verdict, key {key[:12]}\n"


@pytest.mark.parametrize(
    "which", ["other key", "failing", "floor gate", "no record", "broken"]
)
def test_a_deps_gate_runs_unless_that_verdict_is_there(monkeypatch, tmp_path, which):
    """Another key, a verdict that wasn't satisfied (even after a satisfied
    one), the other pins' gate, a record that isn't there or won't read: it
    runs, which here stops at making its environment."""
    gate = ci.deps_add_on("pdf")
    key = gate.key()
    rows = {
        "other key": [("deps:pdf", ci.SATISFIED, "f" * 64)],
        "failing": [("deps:pdf", ci.SATISFIED, key), ("deps:pdf", ci.FAILING, key)],
        "floor gate": [("deps:pdf@floor", ci.SATISFIED, key)],
        "no record": [],
        "broken": [("deps:pdf", ci.SATISFIED, key)],
    }[which]
    record = earlier(tmp_path, *rows)
    if which == "no record":
        record = tmp_path / "missing.jsonl"
    if which == "broken":
        lines = record.read_text().splitlines()
        lines[-1] = lines[-1].replace(ci.SATISFIED, "satisfied ", 1)
        record.write_text("\n".join(lines) + "\n")
    monkeypatch.setenv(ci.HELD, str(record))

    class Made(Exception):
        """it went on to make a virtual environment"""

    real_run = ci.subprocess.run

    def run(argv, *a, **kw):
        if argv[:2] == ["git", "ls-files"]:
            return real_run(argv, *a, **kw)
        raise Made

    monkeypatch.setattr(ci.subprocess, "run", run)
    with pytest.raises(Made):
        gate()


def test_a_deps_verdict_row_carries_its_key_and_says_when_it_was_held(
    monkeypatch, tmp_path
):
    gate = ci.deps_add_on("pdf")
    record = earlier(tmp_path, ("deps:pdf", ci.SATISFIED, gate.key()))
    monkeypatch.setenv(ci.HELD, str(record))
    monkeypatch.setattr(ci, "gates", lambda: [("deps", "deps:pdf", gate)])
    box = tmp_path / "this-run"
    assert ci.do_run(box, ["deps:pdf"], "2026-11-06T01:00:00Z") == 0
    rows, _ = ci.kernel.read(box / "record.jsonl")
    assert rows[-1]["gate"] == "deps:pdf" and rows[-1]["key"] == gate.key()
    assert rows[-1]["held"] is True and rows[-1]["state"] == ci.SATISFIED
