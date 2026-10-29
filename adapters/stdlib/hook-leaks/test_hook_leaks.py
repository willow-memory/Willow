"""hook-leaks: a write or command holding a key, password or card number is
refused with a reason that names only the kind; text an edit removes, other
tools, and plain text pass; unreadable input is refused; `check` lists a
file's kinds; a bad command line is refused; and nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_leaks.py"
KEY = "sk-ant-api03-" + "abcdefghij0123456789" * 3
CARD = "4111 1111 1111 1111"
PASSWORD = "password: hunter2x9"


def hook(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "run"],
        input=stdin,
        capture_output=True,
        text=True,
    )


def call(tool: str, **tool_input) -> subprocess.CompletedProcess:
    return hook(
        json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": tool,
                "tool_input": tool_input,
            }
        )
    )


def test_a_write_holding_a_key_is_refused_and_the_reason_names_only_the_kind():
    got = call("Write", file_path="a.env", content=f"TOKEN={KEY}\n")
    assert got.returncode == 2
    assert (
        "this Write holds a key" in got.stderr
        and "the value is not shown" in got.stderr
    )
    assert KEY not in got.stderr and KEY[:12] not in got.stderr and got.stdout == ""


def test_a_command_holding_a_card_number_is_refused():
    got = call("Bash", command=f"curl -d card={CARD} https://shop.example/pay")
    assert got.returncode == 2 and "this Bash holds a card number" in got.stderr
    assert "4111" not in got.stderr


def test_a_password_is_refused_and_several_kinds_are_all_named():
    assert "a password" in call("Edit", file_path="f", new_string=PASSWORD).stderr
    got = call("Write", file_path="f", content=f"{PASSWORD}\n{KEY}\n{CARD}\n")
    assert "a key, a password and a card number" in got.stderr
    assert (
        "a key and a card number"
        in call("Write", file_path="f", content=f"{KEY} {CARD}").stderr
    )


def test_text_an_edit_takes_out_is_not_looked_at_so_a_secret_can_be_removed():
    assert (
        call("Edit", file_path="f", old_string=PASSWORD, new_string="").returncode == 0
    )
    got = call(
        "MultiEdit",
        file_path="f",
        edits=[{"old_string": KEY, "new_string": "TOKEN=from-env"}],
    )
    assert got.returncode == 0, got.stderr
    assert (
        call(
            "MultiEdit", file_path="f", edits=[{"old_string": "x", "new_string": KEY}]
        ).returncode
        == 2
    )


def test_a_notebook_cell_and_a_nested_edit_are_looked_at():
    assert call("NotebookEdit", new_source=f"k = '{KEY}'").returncode == 2
    assert (
        call(
            "MultiEdit", file_path="f", edits=[{"old_string": "a", "new_string": CARD}]
        ).returncode
        == 2
    )


def test_an_email_a_phone_number_and_prose_are_not_refused():
    text = (
        "Write to ana@example.org or call +44 20 7946 0958 about the password policy."
    )
    assert call("Write", file_path="f", content=text).returncode == 0


def test_other_tools_pass_even_with_a_secret_in_them():
    assert call("Read", file_path=f"/tmp/{KEY}").returncode == 0
    assert call("Grep", pattern=KEY).returncode == 0
    assert (
        hook('{"tool_input": {"command": "' + CARD + '"}}').returncode == 0
    )  # no tool name


def test_input_that_is_not_a_json_object_is_refused():
    for stdin in ("", "not json", "[1, 2]", "42", "null"):
        got = hook(stdin)
        assert got.returncode == 2 and "can't read" in got.stderr, stdin


def test_a_tool_input_that_is_not_an_object_passes_if_nothing_is_in_it():
    assert hook(json.dumps({"tool_name": "Bash", "tool_input": None})).returncode == 0
    assert hook(json.dumps({"tool_name": "Bash"})).returncode == 0


def test_check_lists_the_kinds_in_a_file_and_waits_on_you(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text(f"{PASSWORD}\n{KEY}\nreset your password policy\n")
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--from", str(f)],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 42, got.stderr
    assert "key: 1" in got.stdout and "password: 1" in got.stdout
    assert KEY not in got.stdout and "hunter" not in got.stdout


def test_check_on_a_clean_file_is_clean(tmp_path):
    f = tmp_path / "ok.txt"
    f.write_text("Tomatoes want six hours of sun.\n")
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--from", str(f)],
        capture_output=True,
        text=True,
    )
    assert (
        got.returncode == 0 and "No key, password or card number found." in got.stdout
    )


def test_nothing_is_written(tmp_path):
    before = sorted(p.name for p in tmp_path.iterdir())
    call("Write", file_path=str(tmp_path / "x"), content=KEY)
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["nope"], ["run", "stray"], ["check"], ["check", "--from"],
                 ["check", "--from", str(tmp_path / "missing")]):  # fmt: skip
        got = subprocess.run(
            [sys.executable, str(SCRIPT), *argv],
            input="",
            capture_output=True,
            text=True,
        )
        assert got.returncode == 2, argv
    assert (
        "hook_leaks.py"
        in subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True
        ).stderr
    )
