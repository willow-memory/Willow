"""hook-errors: failed Bash exits are recorded; the third same failure is blocked."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_errors.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-07T12:00:00Z"]
CMD = "pytest adapters/stdlib/missing"


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        check=True,
        capture_output=True,
    )
    return b


def run(*argv: str, data: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        input=data,
        capture_output=True,
        text=True,
    )


def pre(command: str = CMD, session: str = "s1", tool: str = "Bash") -> str:
    return json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"command": command},
            "session_id": session,
        }
    )


def post(
    command: str = CMD,
    exit_code: int = 1,
    session: str = "s1",
    tool: str = "Bash",
) -> str:
    return json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": tool,
            "tool_input": {"command": command},
            "tool_response": {"exit_code": exit_code},
            "session_id": session,
        }
    )


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = run()
    assert got.returncode == 2 and "hook_errors.py" in got.stderr


def test_two_failures_are_recorded_and_the_third_try_is_blocked(tmp_path):
    b = make(tmp_path)
    assert run("--box", str(b), "run", *NOW, data=pre()).returncode == 0
    for _ in range(2):
        got = run("--box", str(b), "run", *NOW, data=post())
        assert got.returncode == 0 and got.stderr == ""
    rows = [
        json.loads(line)
        for line in (b / "record.jsonl").read_text().splitlines()
        if '"hook-errors"' in line
    ]
    assert len(rows) == 2
    assert rows[0]["exit"] == 1 and len(rows[0]["cmd_sha256"]) == 64
    # the record keeps acts, not words (CONST-VI-8): the hash, never the text
    assert (
        "command" not in rows[0]
        and rows[0]["cmd_sha256"] == hashlib.sha256(CMD.encode()).hexdigest()
    )
    assert "missing" not in (b / "record.jsonl").read_text()
    blocked = run("--box", str(b), "run", *NOW, data=pre())
    assert blocked.returncode == 2 and blocked.stdout == ""
    assert (
        blocked.stderr
        == "blocked: this command has failed 2 times with exit 1 (last at row 2); "
        "look at those before trying again\n"
    )
    check = run("--box", str(b), "check")
    assert check.returncode == 42
    assert "exit 1  2 times" in check.stdout and rows[0]["cmd_sha256"] in check.stdout
    assert CMD not in check.stdout


def test_a_different_exit_is_a_different_failure(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=post(exit_code=1))
    run("--box", str(b), "run", *NOW, data=post(exit_code=127))
    # one of each: PreToolUse still allowed
    assert run("--box", str(b), "run", *NOW, data=pre()).returncode == 0
    run("--box", str(b), "run", *NOW, data=post(exit_code=1))  # second exit 1
    blocked = run("--box", str(b), "run", *NOW, data=pre())
    assert blocked.returncode == 2 and "exit 1" in blocked.stderr


def test_a_different_session_does_not_inherit_the_block(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=post(session="a"))
    run("--box", str(b), "run", *NOW, data=post(session="a"))
    assert run("--box", str(b), "run", *NOW, data=pre(session="a")).returncode == 2
    assert run("--box", str(b), "run", *NOW, data=pre(session="b")).returncode == 0


def test_a_zero_exit_is_not_recorded(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run("--box", str(b), "run", *NOW, data=post(exit_code=0))
    assert got.returncode == 0
    assert (b / "record.jsonl").read_text() == before


def test_a_non_shell_tool_is_allowed(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}}),
    )
    assert got.returncode == 0
    assert (b / "record.jsonl").read_text() == before


def test_shell_and_run_terminal_cmd_are_watched(tmp_path):
    b = make(tmp_path)
    for tool in ("Shell", "run_terminal_cmd"):
        assert run("--box", str(b), "run", *NOW, data=post(tool=tool)).returncode == 0
    assert run("--box", str(b), "run", *NOW, data=pre(tool="Shell")).returncode == 2


def test_check_is_clean_when_nothing_has_failed_twice(tmp_path):
    b = make(tmp_path)
    assert run("--box", str(b), "check").returncode == 0
    run("--box", str(b), "run", *NOW, data=post())
    assert run("--box", str(b), "check").returncode == 0
    assert "exit 1  1 times" in run("--box", str(b), "check").stdout


def test_unreadable_input_is_refused(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data="not-json")
    assert got.returncode == 2 and "can't read" in got.stderr


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = make(tmp_path)
    lines = (b / "record.jsonl").read_text().splitlines()
    (b / "record.jsonl").write_text(lines[0].replace("boot", "bootx") + "\n")
    got = run("--box", str(b), "run", *NOW, data=pre())
    assert got.returncode == 2 and "doesn't verify" in got.stderr
    assert run("--box", str(b), "check").returncode == 2
