"""minutes: decisions and actions by what a line opens with, an owner only
when the line names one, and an action closed by its own words or a later
"Done" line, never by a guess."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("minutes", HERE / "minutes.py")
mn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mn)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "minutes.py")


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_bullets_numbers_bold_and_checkboxes_are_ignored():
    assert mn.clean("- **Action:** Ana to send") == ("Action: Ana to send", False)
    assert mn.clean("3. Decision: AGM in May") == ("Decision: AGM in May", False)
    assert mn.clean("  * [ ] Action: x") == ("Action: x", False)
    assert mn.clean("- [x] Action: x") == ("Action: x", True)
    assert mn.clean("- [X] Action: x") == ("Action: x", True)
    assert mn.clean("> __Agreed__: yes") == ("Agreed: yes", False)
    assert mn.clean("Plain") == ("Plain", False)


def test_an_owner_is_only_what_the_line_says():
    assert mn.owner_of("Ana to send the figures") == ("Ana", "send the figures")
    assert mn.owner_of("Ana Lopez will book the hall") == ("Ana Lopez", "book the hall")
    assert mn.owner_of("@ana send the figures") == ("ana", "send the figures")
    assert mn.owner_of("(Ana) send the figures") == ("Ana", "send the figures")
    assert mn.owner_of("Ana: send the figures") == ("Ana", "send the figures")
    assert mn.owner_of("Ana - send the figures") == ("Ana", "send the figures")
    assert mn.owner_of("send the figures to Ana") == (
        mn.NO_OWNER,
        "send the figures to Ana",
    )
    assert mn.owner_of("The board to decide") == (mn.NO_OWNER, "The board to decide")
    assert mn.owner_of("Ana should call") == ("Ana", "call")
    assert mn.owner_of("Ana must call") == ("Ana", "call")
    assert mn.owner_of("Ana can call") == ("Ana", "call")


def test_decisions_actions_open_and_closed():
    pile = [{"path": "board/2026-03-02.md", "line": 1, "text": (
        "# Board\n"
        "- Decision: Move the AGM to May.\n"
        "- Agreed the budget\n"
        "- **Action:** Ana to send the figures by 2026-03-09\n"
        "- Action: Book the hall - done\n"
        "- [x] Todo: Order chairs\n"
        "- AI: Ben to email the council\n"
        "Resolved - rotate the chair\n"
        "Discussed the weather\n"
    )}]  # fmt: skip
    got = mn.read(pile)
    assert [d["what"] for d in got["decisions"]] == [
        "Move the AGM to May.", "the budget", "rotate the chair"
    ]  # fmt: skip
    assert got["decisions"][0] == {"day": "20260302", "where": "board/2026-03-02.md:2",
                                   "what": "Move the AGM to May."}  # fmt: skip
    assert [(a["who"], a["what"], a["due"]) for a in got["open"]] == [
        ("Ana", "send the figures by 2026-03-09", "20260309"),
        ("Ben", "email the council", ""),
    ]
    assert [a["what"] for a in got["closed"]] == [
        "Book the hall - done",
        "Order chairs",
    ]


def test_a_later_done_line_closes_the_same_words_and_only_on_or_after_its_day():
    pile = [
        {"path": "2026-03-02.md", "line": 1, "text": "Action: Ana to send the figures\nAction: Ben to ring\n"},
        {"path": "2026-03-20.md", "line": 1, "text": "Done: Ana to send the figures!\n"},
        {"path": "2026-02-01.md", "line": 1, "text": "Done: Ben to ring\n"},
    ]  # fmt: skip
    got = mn.read(pile)
    assert [a["who"] for a in got["closed"]] == ["Ana"], (
        "a done on another day is not enough"
    )
    assert [a["who"] for a in got["open"]] == ["Ben"], (
        "a done before it was made does not count"
    )
    same = [
        {"path": "2026-03-02.md", "line": 1, "text": "Action: Ana to ring\nDone: Ana to ring\n"},
    ]  # fmt: skip
    assert mn.read(same)["closed"] != [], "on its own day counts"
    near = [
        {"path": "2026-03-02.md", "line": 1, "text": "Action: Ana to ring\n"},
        {"path": "2026-03-03.md", "line": 1, "text": "Done: Ana to ring again\n"},
    ]  # fmt: skip
    assert mn.read(near)["closed"] == [], "the same words, not nearly"


def test_the_listing_and_open_only(tmp_path):
    b = box(tmp_path, {"board/2026-03-02.md": (
        "Decision: Move the AGM to May.\n"
        "Action: Ana to send the figures by 2026-03-09\n"
        "Action: Book the hall - done\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "decisions",
        "  2026-03-02  board/2026-03-02.md:1  Move the AGM to May.",
        "actions open",
        "  2026-03-02  board/2026-03-02.md:2  Ana  send the figures by 2026-03-09  (due 2026-03-09)",
        "actions closed",
        "  2026-03-02  board/2026-03-02.md:3  (no owner)  Book the hall - done",
        "1 decision, 1 open action, 1 closed",
    ]
    only = run(SCRIPT, "--box", str(b), "--open").stdout.splitlines()
    assert only == [
        "actions open",
        "  2026-03-02  board/2026-03-02.md:2  Ana  send the figures by 2026-03-09  (due 2026-03-09)",
        "1 decision, 1 open action, 1 closed",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout


def test_a_machines_shouting_line_is_not_an_action():
    pile = [{"path": "Calendar/Home.ics", "line": 1,
             "text": "DTSTART:20261101\nACTION:DISPLAY\nDECISION: YES\nAction: ring the vet\n"}]  # fmt: skip
    got = mn.read(pile)
    assert [a["what"] for a in got["open"]] == ["ring the vet"]
    assert got["decisions"] == []


def test_plurals(tmp_path):
    b = box(
        tmp_path, {"2026-03-02.md": "Decision: a\nDecision: b\nAction: x\nAction: y\n"}
    )
    assert (
        run(SCRIPT, "--box", str(b)).stdout.splitlines()[-1]
        == "2 decisions, 2 open actions, 0 closed"
    )


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "decision or an action" in got.stdout
    for argv in ([], ["--box", str(tmp_path)], ["--box", str(b), "stray"]):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "minutes.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
