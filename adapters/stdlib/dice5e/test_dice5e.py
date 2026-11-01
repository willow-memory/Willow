"""dice5e: keep-highest and keep-lowest, adv and dis, drawn from dice's seeded
stream with the record's tip as seed, every die on the record and every roll
thrown again by check."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "dice5e.py"
spec = importlib.util.spec_from_file_location("dice5e", SCRIPT)
d5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d5)
NOW = ["--now", "2026-11-01T09:00:00Z"]
TIP = "ab" * 32


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "notes.md").write_text("The goblin has twelve hit points.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = d5.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def test_the_notation():
    assert d5.parse("4d6kh3") == ([(1, 4, 6, "h", 3)], 0)
    assert d5.parse("ADV + 5") == ([(1, 2, 20, "h", 1)], 5)
    assert d5.parse("dis-1") == ([(1, 2, 20, "l", 1)], -1)
    assert d5.parse("d8 - 1d4kl1 + 2") == ([(1, 1, 8, "", 1), (-1, 1, 4, "l", 1)], 2)
    for bad in ("", "4d6kh5", "4d6kh0", "4d6k3", "2d6x", "adv5", "advantage",
                "2d6 2d6", "2d6++1", "3", "0d6", "1d1", "101d6", "1d1001"):  # fmt: skip
        with pytest.raises(ValueError):
            d5.parse(bad)


def test_keeping_counts_the_highest_or_lowest_and_the_first_of_a_tie():
    assert d5.kept([2, 6, 6, 2], "h", 3) == [0, 1, 2]
    assert d5.kept([2, 6, 6, 2], "l", 1) == [0]
    assert d5.kept([5, 1, 5, 1], "h", 1) == [0]
    assert d5.kept([5, 1, 5, 1], "l", 3) == [0, 1, 3]
    assert d5.kept([3, 1, 2], "", 3) == [0, 1, 2]
    for tip in ("0" * 64, TIP, "c3" * 32):
        r = d5.throw("4d6kh3", tip)
        assert r["total"] == sum(sorted(r["faces"][0])[1:])
        r = d5.throw("adv+5", tip)
        assert r["total"] == max(r["faces"][0]) + 5
        r = d5.throw("dis", tip)
        assert r["total"] == min(r["faces"][0])
        r = d5.throw("2d6-1d4kh1-1", tip)
        assert r["total"] == sum(r["faces"][0]) - r["faces"][1][0] - 1


def test_plain_dice_are_dices_own_faces():
    for text in ("2d6", "1d20+3", "1d8+1d6"):
        mine, theirs = d5.throw(text, TIP), d5.dice.throw(text, TIP)
        assert mine["faces"] == theirs["faces"] and mine["total"] == theirs["total"]
    assert d5.throw("4d6kh3", TIP) == d5.throw("4d6kh3", TIP), "the same every time"
    assert d5.throw("4d6kh3", TIP)["generator"] == "sha256-stream/v1"


def test_what_a_roll_says():
    row = {"dice": "3d6kl2-1d4kh1+2", "faces": [[5, 4, 2], [3]], "kept": [[1, 2], [0]],
           "add": 2, "total": 5}  # fmt: skip
    assert (
        d5.said(row) == "3d6kl2-1d4kh1+2: [5, 4, 2] keep 4 + 2 - ([3] keep 3) + 2 = 5"
    )
    row = {"dice": "-1d4-1", "faces": [[2]], "kept": [[0]], "add": -1, "total": -3}
    assert d5.said(row) == "-1d4-1: -(2) - 1 = -3"


def test_a_roll_is_a_row_seeded_by_the_tip_and_check_throws_it_again(tmp_path):
    box = make(tmp_path)
    tip = rows(box)[-1]["hash"]
    got = run("--box", str(box), "roll", "4d6kh3", *NOW)
    assert got.returncode == 0, got.stderr
    row = rows(box)[-1]
    assert row["kind"] == "roll5e" and row["who"] == "dice5e" and row["seed"] == tip
    assert got.stdout == f"{d5.said(row)}   (row {row['n']})\n"
    assert {k: row[k] for k in d5.throw("4d6kh3", tip)} == d5.throw("4d6kh3", tip)
    run("--box", str(box), "roll", "adv+5", *NOW)
    got = run("--box", str(box), "check")
    assert (
        got.returncode == 0 and "2 rolls on the record; every one holds." in got.stdout
    )
    assert run("--box", str(box), "check", script=d5.dice.__file__).returncode == 0


def test_check_finds_a_roll_that_was_changed(tmp_path):
    box = make(tmp_path)
    run("--box", str(box), "roll", "4d6kh3", *NOW)
    good = rows(box)

    def fails(change: dict, why: str) -> None:
        rs = [dict(r) for r in good]
        rs[-1].update(change)
        held, said = d5.check(rs)
        assert held == 0 and said == f"row {rs[-1]['n']}: {why}"

    fails({"seed": "0" * 64}, "its seed isn't the hash of the row before it")
    fails({"total": good[-1]["total"] + 1}, "its faces aren't what its seed gives")
    fails({"kept": [[0, 1, 2, 3]]}, "its faces aren't what its seed gives")
    fails({"dice": "4d6kh9"}, "4d6kh9: keep 1 to 4")
    assert d5.check(good) == (1, None)
    first = [{**good[0], "kind": "roll5e", "dice": "1d6", "seed": "x"}]
    assert d5.check(first)[1] == "row 0: its seed isn't the hash of the row before it"


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    box = make(tmp_path)
    b = str(box)
    for argv in ([], ["--box", b], ["--box", b, "roll"], ["--box", b, "fly", "2d6"],
                 ["--box", b, "check", *NOW], ["--box", b, "roll", "2d6", "--x", "1"],
                 ["--box", b, "roll", "2d6", "--now", ""], ["--box", "", "check"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "dice5e.py" in got.stderr, argv
    got = run("--box", b, "roll", "4d6kh5")
    assert got.returncode == 2 and "keep 1 to 4" in got.stderr
    assert len(rows(box)) == 1, "nothing written by a refusal"
    got = run("--box", str(tmp_path / "nobox"), "check")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    run("--box", b, "roll", "2d6", *NOW)
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"roll5e"', '"roll5f"', 1))
    got = run("--box", b, "check")
    assert got.returncode == 2 and "chain broken" in got.stderr
