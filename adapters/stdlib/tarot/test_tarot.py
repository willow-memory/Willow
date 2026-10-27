"""tarot: the deck is the standard 78, the tip deals the spread without
replacement, the record replays every draw, and a doctored one is named."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("tarot", HERE / "tarot.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def tarot_cmd(b: Path, *args: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "tarot.py"), "--box", str(b), *args, *NOW)


def test_the_deck_is_the_standard_78():
    assert len(tr.DECK) == 78 and len(set(tr.DECK)) == 78
    assert "The Fool" in tr.DECK and "The World" in tr.DECK
    assert "Six of Cups" in tr.DECK and "King of Pentacles" in tr.DECK
    minors = [c for c in tr.DECK if c.split(" of ")[0] in tr.RANKS]
    assert len(minors) == 56, "and Wheel of Fortune is a major, not a minor"


def test_the_same_seed_deals_the_same_spread_without_replacement():
    tip = "ab" * 32
    one, two = tr.deal(78, tip), tr.deal(78, tip)
    assert one == two, "the same seed, the same spread"
    names = [c for c, _ in one["cards"]]
    assert sorted(names) == sorted(tr.DECK), "the whole deck, each card once"
    assert any(turned for _, turned in one["cards"])
    assert not all(turned for _, turned in one["cards"])
    other = tr.deal(3, "cd" * 32)
    assert other["cards"] != tr.deal(3, tip)["cards"], "another seed, another spread"


def test_draw_writes_the_row_and_prints_the_spread(tmp_path):
    b = box(tmp_path)
    got = tarot_cmd(b, "draw")
    assert got.returncode == 0 and got.stdout.startswith("1. ")
    assert got.stdout.count("\n") == 4, "three cards and the row line"
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "draw" and row["who"] == "tarot" and row["count"] == 3
    assert len(row["cards"]) == 3
    got = tarot_cmd(b, "draw", "5")
    assert got.returncode == 0 and got.stdout.count("\n") == 6
    assert "replayable" in got.stdout


def test_check_replays_every_draw_and_names_a_doctored_one(tmp_path):
    b = box(tmp_path)
    tarot_cmd(b, "draw")
    tarot_cmd(b, "draw", "1")
    got = tarot_cmd(b, "check")
    assert (
        got.returncode == 0 and "2 draws on the record; every one holds." in got.stdout
    )
    record = b / "record.jsonl"
    lines = record.read_text().splitlines()
    row = json.loads(lines[-1])
    row["cards"][0][0] = "The Sun" if row["cards"][0][0] != "The Sun" else "The Moon"
    body = {k: v for k, v in row.items() if k != "hash"}
    row["hash"] = tr.kernel.h256(tr.kernel.canon(body))
    lines[-1] = tr.kernel.canon(row)
    record.write_text("\n".join(lines) + "\n")
    got = tarot_cmd(b, "check")
    assert got.returncode == 2 and "aren't what its seed deals" in got.stderr
    assert "(1 before it held)" in got.stderr


def test_check_names_a_doctored_count_too(tmp_path):
    b = box(tmp_path)
    tarot_cmd(b, "draw")
    record = b / "record.jsonl"
    lines = record.read_text().splitlines()
    row = json.loads(lines[-1])
    row["count"] = 0
    body = {k: v for k, v in row.items() if k != "hash"}
    row["hash"] = tr.kernel.h256(tr.kernel.canon(body))
    lines[-1] = tr.kernel.canon(row)
    record.write_text("\n".join(lines) + "\n")
    got = tarot_cmd(b, "check")
    assert got.returncode == 2 and "a count the deck hasn't" in got.stderr


def test_a_count_the_deck_hasnt_is_refused(tmp_path):
    b = box(tmp_path)
    for bad in ("0", "79", "three", "-1"):
        got = tarot_cmd(b, "draw", bad)
        assert got.returncode == 2, bad
    assert tarot_cmd(b, "draw", "78").returncode == 0


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "tarot.py"))
    assert got.returncode == 2 and "tarot.py" in got.stderr
    got = run(str(HERE / "tarot.py"), "--box", str(tmp_path), "draw", *NOW)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    b = box(tmp_path)
    got = tarot_cmd(b, "draw", "3", "--stray")
    assert got.returncode == 2 and "tarot.py" in got.stderr
