"""The CI one-script: verdict rows on a kernel record, the same every run.

Each test holds one promise in adapters/ci/README.md, and each can fail: the
record is byte-for-byte the same for the same files, a missing tool is
unreachable (not failing, not a pass), a failing command is failing, and the
record holds only ci verdicts, which `verify` checks along with the kernel's
own chain.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ci", HERE / "ci.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
k = ci.kernel
NOW = "2026-10-23T00:00:00Z"


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
        assert cli("run", "demo", "--box", str(box), "--now", NOW).returncode == 0
    assert (a / "record.jsonl").read_bytes() == (b / "record.jsonl").read_bytes()
    made = rows(a)
    assert [r["gate"] for r in made[1:]] == [f"demo:{p}" for p in ci.people()]
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


def test_verify_holds_the_chain_and_refuses_anything_but_ci_verdicts(tmp_path):
    box = tmp_path / "box"
    assert cli("run", "demo", "--box", str(box), "--now", NOW).returncode == 0
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
        "lint:check", "lint:format",
        "tests:beats", "tests:kernel", "tests:docs", "tests:adapters", "tests:vectors",
        *(f"ports:{p}" for p in ci.PORTS),
        *(f"demo:{p}" for p in ci.people()),
    ]  # fmt: skip
    assert {p for p, _, _ in ci.gates()} == set(ci.PARTS)


def test_a_record_inside_the_repo_where_git_would_count_it_is_refused(tmp_path):
    """It would be hashed into the files it records (the first CI run did
    exactly this, and the docs test caught the files it left)."""
    inside = ci.ROOT / "ci-record-test-only"
    try:
        got = cli("run", "demo", "--box", str(inside), "--now", NOW)
        assert got.returncode != 0 and "not ignored by git" in got.stderr
        assert not inside.exists()
        assert not inside.with_name(inside.name + ".key").exists()
    finally:  # even when it fails: nothing may be left in the repo
        if inside.exists():
            import shutil

            shutil.rmtree(inside)
        inside.with_name(inside.name + ".key").unlink(missing_ok=True)
    ok = cli("run", "demo", "--box", str(tmp_path / "out"), "--now", NOW)
    assert ok.returncode == 0  # outside the repo is fine
