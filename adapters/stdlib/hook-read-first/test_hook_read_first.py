"""hook-read-first: a PreToolUse hook that records each Read's hash and
refuses an edit until that hash still matches."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_read_first.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-07T12:00:00Z"]


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    note = pile / "notes.md"
    note.write_text("Tomatoes want six hours of sun.\n")
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
    return b, note


def run(*argv: str, data: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        input=data,
        capture_output=True,
        text=True,
    )


def call(tool: str, path: Path, session: str = "s1", **extra) -> str:
    body = {"tool_name": tool, "tool_input": {"file_path": str(path), **extra}}
    if session is not None:
        body["session_id"] = session
    return json.dumps(body)


def test_a_read_is_recorded_and_an_edit_then_holds(tmp_path):
    b, note = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data=call("Read", note))
    assert got.returncode == 0 and got.stdout == "" and got.stderr == ""
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["who"], row["path"], row["session"]) == (
        "hook-read-first",
        "hook-read-first",
        str(note.resolve()),
        "s1",
    )
    assert len(row["sha256"]) == 64
    edit = run("--box", str(b), "run", *NOW, data=call("Edit", note, old_string="a"))
    assert edit.returncode == 0 and edit.stderr == ""
    assert (
        run("--box", str(b), "check", str(note)).stdout
        == f"read        {note} (row 1)\n"
    )


def test_an_edit_without_a_read_is_blocked(tmp_path):
    b, note = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data=call("Write", note, content="x"))
    assert got.returncode == 2 and got.stdout == ""
    assert got.stderr == f"blocked: never read  {note.resolve()}\n"


def test_a_changed_file_must_be_read_again(tmp_path):
    b, note = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=call("Read", note))
    note.write_text("Something else.\n")
    got = run("--box", str(b), "run", *NOW, data=call("Edit", note))
    assert got.returncode == 2
    assert got.stderr == f"blocked: changed     {note.resolve()} (read at row 1)\n"
    assert run("--box", str(b), "check", str(note)).returncode == 42
    run("--box", str(b), "run", *NOW, data=call("Read", note))  # fresh read
    assert run("--box", str(b), "run", *NOW, data=call("Edit", note)).returncode == 0


def test_creating_a_file_needs_no_read(tmp_path):
    b, _ = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    new = tmp_path / "pile" / "new.md"
    got = run("--box", str(b), "run", *NOW, data=call("Write", new, content="hi\n"))
    assert got.returncode == 0 and got.stderr == ""
    assert (b / "record.jsonl").read_text() == before


def test_another_session_does_not_count(tmp_path):
    b, note = make(tmp_path)
    run("--box", str(b), "run", *NOW, data=call("Read", note, session="alpha"))
    got = run("--box", str(b), "run", *NOW, data=call("Edit", note, session="beta"))
    assert got.returncode == 2
    assert "never read" in got.stderr


def test_other_tools_pass_and_write_nothing(tmp_path):
    b, _ = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}),
    )
    assert got.returncode == 0 and (b / "record.jsonl").read_text() == before


def test_unreadable_input_is_refused(tmp_path):
    b, _ = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data="not-json")
    assert got.returncode == 2 and "can't read" in got.stderr


def test_refusals(tmp_path):
    b, note = make(tmp_path)
    assert run().returncode == 2
    assert run("--box", str(b)).returncode == 2
    assert run("--box", str(tmp_path / "nobox"), "run").returncode == 2
    assert run("--box", str(b), "check").returncode == 2
    assert run("--box", str(b), "check", str(tmp_path / "missing")).returncode == 2
    never = run("--box", str(b), "check", str(note))
    assert never.returncode == 42 and never.stdout.startswith("never read")
