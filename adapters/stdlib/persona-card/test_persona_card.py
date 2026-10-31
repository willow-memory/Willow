"""persona-card: the same card compiles to the same bytes; the hash
goes on the record, never the prompt."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "persona_card.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]

CARD = """<!-- willow-persona
name: Binder
-->
You file everything.
"""


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def box_and_card(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    b = tmp_path / "box"
    init = run(
        KERNEL, "init", "--box", b, "--pile", pile, "--key", tmp_path / "k", *NOW
    )
    assert init.returncode == 0, init.stderr
    card = tmp_path / "binder.md"
    card.write_text(CARD, encoding="utf-8")
    return b, card


def test_the_same_card_compiles_to_the_same_bytes_and_the_hash_is_on_the_record(
    tmp_path,
):
    b, card = box_and_card(tmp_path)
    first = run(SCRIPT, "--box", str(b), "--from", str(card), *NOW)
    assert first.returncode == 0, first.stderr
    prompt = "# Binder\n\nYou file everything.\n"
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    assert f"compiled  Binder  sha256={digest}  (row 1)" in first.stdout
    assert first.stdout.endswith(prompt)
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["who"], row["name"], row["sha256"]) == (
        "persona-card",
        "persona-card",
        "Binder",
        digest,
    )
    assert row["ts"] == NOW[1]
    assert "You file everything" not in json.dumps(row)
    second = run(SCRIPT, "--box", str(b), "--from", str(card), *NOW)
    assert second.returncode == 0
    again = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert again["sha256"] == digest and again["n"] == 2


def test_check_holds_a_card_to_its_row(tmp_path):
    b, card = box_and_card(tmp_path)
    run(SCRIPT, "--box", str(b), "--from", str(card), *NOW)
    same = run(SCRIPT, "check", "--box", str(b), "--from", str(card))
    assert same.returncode == 0
    assert same.stdout == f"same            {card} (row 1)\n"
    card.write_text(CARD.replace("everything.", "nothing."), encoding="utf-8")
    got = run(SCRIPT, "check", "--box", str(b), "--from", str(card))
    assert got.returncode == 42
    assert got.stdout == f"changed         {card} (compiled at row 1)\n"


def test_a_card_without_a_header_uses_its_file_name(tmp_path):
    b, _ = box_and_card(tmp_path)
    plain = tmp_path / "clerk.md"
    plain.write_text("You stamp the forms.\n", encoding="utf-8")
    got = run(SCRIPT, "--box", str(b), "--from", str(plain), *NOW)
    assert got.returncode == 0
    assert "compiled  clerk  " in got.stdout
    assert got.stdout.endswith("# clerk\n\nYou stamp the forms.\n")


def test_a_folder_compiles_markdown_cards_only(tmp_path):
    b, _ = box_and_card(tmp_path)
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "binder.md").write_text(CARD, encoding="utf-8")
    (cards / "notes.txt").write_text("not a card\n", encoding="utf-8")
    got = run(SCRIPT, "--box", str(b), "--from", str(cards), *NOW)
    assert got.returncode == 0, got.stderr
    assert "compiled  Binder  " in got.stdout
    assert "notes" not in got.stdout
    kinds = [
        json.loads(line)["kind"]
        for line in (b / "record.jsonl").read_text().splitlines()
    ]
    assert kinds.count("persona-card") == 1


def test_a_folder_with_no_card_is_nothing_there(tmp_path):
    b, _ = box_and_card(tmp_path)
    empty = tmp_path / "cards"
    empty.mkdir()
    got = run(SCRIPT, "--box", str(b), "--from", str(empty), *NOW)
    assert got.returncode == 42
    assert "nothing there" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = run(SCRIPT)
    assert got.returncode == 2 and "persona_card.py" in got.stderr
    b, card = box_and_card(tmp_path)
    got = run(SCRIPT, "--box", str(b), "--from", str(card), "stray")
    assert got.returncode == 2
    got = run(SCRIPT, "--box", str(tmp_path / "missing"), "--from", str(card))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
