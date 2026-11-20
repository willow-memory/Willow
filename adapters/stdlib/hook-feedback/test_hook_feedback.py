"""hook-feedback: corrections at the prompt are proposed for you to keep or drop."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_feedback.py"
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


def prompt(text: str, event: str = "UserPromptSubmit") -> str:
    return json.dumps({"hook_event_name": event, "prompt": text, "session_id": "s1"})


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = run()
    assert got.returncode == 2 and "hook_feedback.py" in got.stderr


def test_a_correction_is_proposed_and_check_names_it(tmp_path):
    b = make(tmp_path)
    assert run("--box", str(b), "check").stdout == "no feedback waiting\n"
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=prompt("No, the bins go out on Thursday night."),
    )
    assert got.returncode == 0 and got.stdout == "" and got.stderr == ""
    row = [
        json.loads(line)
        for line in (b / "record.jsonl").read_text().splitlines()
        if '"hook-feedback"' in line and '"kind"' in line
    ][-1]
    assert row["kind"] == "hook-feedback" and row["path"].startswith("feedback/")
    assert row["subject"].startswith("proposal:")
    assert (b / "proposals" / f"{row['subject'][9:]}.json").is_file()
    check = run("--box", str(b), "check")
    assert check.returncode == 42
    assert row["subject"] in check.stdout and row["path"] in check.stdout


def test_wrong_and_i_said_are_caught(tmp_path):
    b = make(tmp_path)
    for text in (
        "Wrong — use the garden path, not the shed.",
        "I said six hours of sun, not four.",
    ):
        got = run("--box", str(b), "run", *NOW, data=prompt(text))
        assert got.returncode == 0, text
    assert run("--box", str(b), "check").returncode == 42


def test_an_ordinary_ask_is_not_proposed(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=prompt("When do the bins go out?"),
    )
    assert got.returncode == 0
    assert (b / "record.jsonl").read_text() == before
    assert run("--box", str(b), "check").returncode == 0


def test_a_non_prompt_event_is_left_alone(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=prompt("No, ignore this.", event="PreToolUse"),
    )
    assert got.returncode == 0
    assert (b / "record.jsonl").read_text() == before


def test_unreadable_input_is_refused(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "run", *NOW, data="not-json")
    assert got.returncode == 2 and "can't read" in got.stderr


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = make(tmp_path)
    lines = (b / "record.jsonl").read_text().splitlines()
    (b / "record.jsonl").write_text(lines[0].replace("boot", "bootx") + "\n")
    got = run(
        "--box",
        str(b),
        "run",
        *NOW,
        data=prompt("No, that is not right."),
    )
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def said(text: str) -> str:
    return json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": text})


def test_the_words_list_says_what_is_a_correction_and_what_never_is():
    """Seen driving a provider's hooks: "No thanks, that's fine" and "no
    worries" were handed in as corrections, and "nope, not that" wasn't."""
    caught = ("no, the other file", "wrong again", "nope, not that", "I said tabs",
              "ok but I said tabs", "not what I asked", "That’s not what I meant")  # fmt: skip
    left = ("No thanks, that's fine", "no worries, carry on", "no problem", "No need",
            "no rush", "now the tests", "nobody uses it", "is there no test?", "said so")  # fmt: skip
    for text in caught:
        assert run("match", data=said(text)).returncode == 42, text
    for text in left:
        assert run("match", data=said(text)).returncode == 0, text
    other = json.dumps({"hook_event_name": "Stop", "prompt": "no"})
    assert run("match", data=other).returncode == 0  # only a prompt
    assert run("match", data="not json").returncode == 2


def test_match_writes_nothing_and_run_still_hands_one_in(tmp_path):
    b = make(tmp_path)
    before = (b / "record.jsonl").read_text()
    assert (
        run("match", "--box", str(b), data=said("no, the other one")).returncode == 42
    )
    assert (b / "record.jsonl").read_text() == before  # match proposes nothing
    assert run("run", "--box", str(b), *NOW, data=said("No thanks")).returncode == 0
    assert (b / "record.jsonl").read_text() == before  # polite: nothing handed in
    assert (
        run("run", "--box", str(b), *NOW, data=said("nope, the other one")).returncode
        == 0
    )
    assert "hook-feedback" in (b / "record.jsonl").read_text()


def test_a_words_list_of_your_own_replaces_the_base_one(tmp_path):
    mine = tmp_path / "mine.txt"
    mine.write_text("# mine\n+ actually\n- no\n")
    assert (
        run("match", "--words", str(mine), data=said("actually, tabs")).returncode == 42
    )
    assert (
        run("match", "--words", str(mine), data=said("no, the other")).returncode == 0
    )
    bad = tmp_path / "bad.txt"
    bad.write_text("actually\n")
    got = run("match", "--words", str(bad), data=said("actually"))
    assert got.returncode == 2 and "isn't a words list" in got.stderr
    assert (
        run("match", "--words", str(tmp_path / "gone.txt"), data=said("no")).returncode
        == 2
    )
