"""model-card: a card's hash on the record, never its text, and held to it."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "model_card.py"
KERNEL = HERE.parents[2] / "kernel.py"
WEIGHTS_CARD = HERE.parent / "weights-card" / "weights_card.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
SHA = "9c" * 32

CARD = f"""<!-- willow-model
file: gemma.gguf
sha256: {SHA}
name: Gemma 3 4b It
licence: gemma
runs: http://127.0.0.1:8080/v1
limits: makes up dates
-->
# Gemma 3 4b It

It is slow on a laptop.
"""


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


@pytest.fixture
def box(tmp_path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
    b = tmp_path / "box"
    init = run(
        KERNEL, "init", "--box", b, "--pile", pile, "--key", tmp_path / "k", *NOW
    )
    assert init.returncode == 0, init.stderr
    return b


def card(tmp_path: Path, text: str = CARD, name: str = "gemma.md") -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def rows(box: Path) -> list[dict]:
    return [
        json.loads(line) for line in (box / "record.jsonl").read_text().splitlines()
    ]


def test_add_puts_the_cards_hash_on_the_record_never_its_text(box, tmp_path):
    c = card(tmp_path)
    digest = hashlib.sha256(c.read_bytes()).hexdigest()
    got = run(SCRIPT, "add", "--box", box, "--from", c, *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout == (f"added  Gemma 3 4b It  card={digest}  weights={SHA}, "
                          "runs at http://127.0.0.1:8080/v1  (row 1)\n")  # fmt: skip
    row = rows(box)[-1]
    assert (row["kind"], row["who"], row["ts"]) == ("model-card", "model-card", NOW[1])
    assert (row["name"], row["card"], row["weights"], row["runs"]) == (
        "Gemma 3 4b It", digest, SHA, "http://127.0.0.1:8080/v1")  # fmt: skip
    assert row["model_version"] is None
    assert "slow on a laptop" not in json.dumps(row) and "makes up" not in json.dumps(
        row
    )
    assert run(KERNEL, "verify", "--box", box).returncode == 0


def test_the_same_card_twice_is_already_there_and_a_new_one_replaces_it(box, tmp_path):
    c = card(tmp_path)
    run(SCRIPT, "add", "--box", box, "--from", c, *NOW)
    again = run(SCRIPT, "add", "--box", box, "--from", c, *NOW)
    assert again.returncode == 0 and again.stdout.startswith(
        "already there  Gemma 3 4b It  "
    )
    assert len(rows(box)) == 2
    c.write_text(
        CARD.replace("makes up dates", "makes up dates and names"), encoding="utf-8"
    )
    newer = run(SCRIPT, "add", "--box", box, "--from", c, *NOW)
    assert newer.returncode == 0 and newer.stdout.endswith("(row 2, replacing row 1)\n")


def test_check_holds_a_card_to_its_row(box, tmp_path):
    c = card(tmp_path)
    got = run(SCRIPT, "check", "--box", box, "--from", c)
    assert got.returncode == 42 and got.stdout.startswith(
        "never added  Gemma 3 4b It  card="
    )
    run(SCRIPT, "add", "--box", box, "--from", c, *NOW)
    digest = hashlib.sha256(c.read_bytes()).hexdigest()
    got = run(SCRIPT, "check", "--box", box, "--from", c)
    assert got.returncode == 0
    assert got.stdout == f"same         Gemma 3 4b It  card={digest} (row 1)\n"
    c.write_text(CARD + "\nAnd it rhymes.\n", encoding="utf-8")
    got = run(SCRIPT, "check", "--box", box, "--from", c)
    assert got.returncode == 42
    assert got.stdout.startswith("changed      Gemma 3 4b It  card=")
    assert got.stdout.endswith(f", the record has {digest} (row 1)\n")


def test_list_says_each_names_latest_card(box, tmp_path):
    got = run(SCRIPT, "list", "--box", box)
    assert got.returncode == 42 and "no model card on the record" in got.stdout
    run(SCRIPT, "add", "--box", box, "--from", card(tmp_path), *NOW)
    hosted = card(
        tmp_path,
        "<!-- willow-model\nname: Claude\nmodel version: 2026-10\n-->\n",
        "c.md",
    )
    run(SCRIPT, "add", "--box", box, "--from", hosted, *NOW)
    got = run(SCRIPT, "list", "--box", box)
    assert got.returncode == 0
    lines = got.stdout.splitlines()
    assert lines[0].startswith("Claude  card=") and lines[0].endswith(
        "  version 2026-10, where it runs not said  (row 2)")  # fmt: skip
    assert lines[1].startswith("Gemma 3 4b It  card=") and lines[1].endswith("(row 1)")


def test_a_card_weights_card_wrote_can_be_added(box, tmp_path):
    w = tmp_path / "m.gguf"
    key, value = b"general.name", b"Tiny"
    w.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, 0, 1) + struct.pack("<Q", len(key)) + key
                  + struct.pack("<IQ", 8, len(value)) + value)  # fmt: skip
    made = run(WEIGHTS_CARD, "--from", w, "--to", tmp_path / "tiny.md")
    assert made.returncode == 0, made.stderr
    got = run(SCRIPT, "add", "--box", box, "--from", tmp_path / "tiny.md", *NOW)
    assert got.returncode == 0, got.stderr
    assert "added  Tiny  " in got.stdout and "where it runs not said" in got.stdout
    assert rows(box)[-1]["weights"] == hashlib.sha256(w.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "text, why",
    [
        ("# Notes\n", "no willow-model header"),
        ("<!-- willow-model\nname: X\nsha256: 1\n", "no willow-model header"),
        (f"<!-- willow-model\nsha256: {SHA}\n-->\n", "doesn't name the model"),
        (
            f"<!-- willow-model\nname: not in the header\nsha256: {SHA}\n-->\n",
            "doesn't name",
        ),
        (f"<!-- willow-model\nname:\nsha256: {SHA}\n-->\n", "doesn't name the model"),
        ("<!-- willow-model\nname: X\n-->\n", "doesn't say which model"),
        ("<!-- willow-model\nname: X\nsha256: abc\n-->\n", "its sha256 isn't one"),
        (f"name: X\nsha256: {SHA}\n-->\n", "no willow-model header"),
    ],
)
def test_a_card_that_doesnt_say_which_model_is_refused(text, why, box, tmp_path):
    got = run(SCRIPT, "add", "--box", box, "--from", card(tmp_path, text), *NOW)
    assert got.returncode == 2 and why in got.stderr, got.stderr
    assert len(rows(box)) == 1


def test_a_bad_command_line_is_refused(box, tmp_path):
    c = card(tmp_path)
    for argv in ([], ["add", "--box", box], ["list", "--box", box, "--from", c],
                 ["check", "--box", box, "--from", c, *NOW], ["add", "list", "--box", box],
                 ["show", "--box", box], ["list"], ["list", "--box", ""]):  # fmt: skip
        got = run(SCRIPT, *argv)
        assert got.returncode == 2 and "model_card.py" in got.stderr, argv
    got = run(SCRIPT, "list", "--box", tmp_path)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(SCRIPT, "add", "--box", box, "--from", tmp_path / "missing.md")
    assert got.returncode == 2 and "not a file" in got.stderr
    (tmp_path / "bin.md").write_bytes(b"\xff\xfe")
    got = run(SCRIPT, "add", "--box", box, "--from", tmp_path / "bin.md")
    assert got.returncode == 2 and "isn't UTF-8" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 9}\n')
    got = run(SCRIPT, "list", "--box", box)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
