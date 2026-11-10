"""hook-handoff: Stop records where the session ended; the next session gets it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_handoff.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-07T12:00:00Z"]


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


def stop(
    session: str = "s1",
    cwd: str = "/home/you/proj",
    transcript: str = "/tmp/t.jsonl",
    active: bool = False,
) -> str:
    return json.dumps(
        {
            "hook_event_name": "Stop",
            "session_id": session,
            "cwd": cwd,
            "transcript_path": transcript,
            "stop_hook_active": active,
        }
    )


def start(session: str = "s2", event: str = "SessionStart") -> str:
    return json.dumps({"hook_event_name": event, "session_id": session})


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = run()
    assert got.returncode == 2 and "hook_handoff.py" in got.stderr


def test_a_stop_is_recorded_and_the_next_session_gets_it(tmp_path):
    b = make(tmp_path)
    assert run("--box", str(b), "check").returncode == 42
    assert run("--box", str(b), "check").stdout == "no handoff yet\n"
    got = run("--box", str(b), "run", *NOW, data=stop())
    assert got.returncode == 0 and got.stdout == ""
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["session"], row["cwd"], row["transcript"]) == (
        "hook-handoff",
        "s1",
        "/home/you/proj",
        "/tmp/t.jsonl",
    )
    check = run("--box", str(b), "check")
    assert check.returncode == 0
    assert "session s1 ended in /home/you/proj (row 1)" in check.stdout
    give = run("--box", str(b), "run", *NOW, data=start("s2"))
    assert give.returncode == 0
    body = json.loads(give.stdout)
    assert "session s1 ended in /home/you/proj (row 1)" in body["additionalContext"]
    assert "do not invent" in body["additionalContext"]


def test_the_same_session_does_not_get_its_own_handoff(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=stop("s1"))
    got = run("--box", str(b), "run", *NOW, data=start("s1"))
    assert got.returncode == 0 and got.stdout == ""


def test_a_handoff_is_served_only_once_per_session(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=stop("s1"))
    assert run("--box", str(b), "run", *NOW, data=start("s2")).stdout
    again = run("--box", str(b), "run", *NOW, data=start("s2"))
    assert again.returncode == 0 and again.stdout == ""


def test_user_prompt_submit_also_gives_it_back(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=stop("s1"))
    got = run("--box", str(b), "run", *NOW, data=start("s2", event="UserPromptSubmit"))
    assert got.returncode == 0 and "additionalContext" in got.stdout


def test_stop_hook_active_writes_nothing(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run("--box", str(b), "run", *NOW, data=stop(active=True))
    assert got.returncode == 0
    assert (b / "record.jsonl").read_text() == before


def test_unreadable_input_is_refused(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data="not-json")
    assert got.returncode == 2 and "can't read" in got.stderr


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=stop("s1"))
    lines = (b / "record.jsonl").read_text().splitlines()
    (b / "record.jsonl").write_text(lines[0].replace("boot", "bootx") + "\n")
    got = run("--box", str(b), "run", *NOW, data=start("s2"))
    assert got.returncode == 2 and "doesn't verify" in got.stderr
    assert run("--box", str(b), "check").returncode == 2


def test_a_non_string_cwd_is_stored_as_empty(tmp_path):
    b = make(tmp_path)
    raw = json.dumps(
        {
            "hook_event_name": "Stop",
            "session_id": "s1",
            "cwd": 7,
            "stop_hook_active": False,
        }
    )
    assert run("--box", str(b), "run", *NOW, data=raw).returncode == 0
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["cwd"] == ""
    assert "(no cwd)" in run("--box", str(b), "check").stdout


def test_an_unrelated_event_is_allowed_and_writes_nothing(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash"}),
    )
    assert got.returncode == 0 and got.stdout == ""
    assert (b / "record.jsonl").read_text() == before
