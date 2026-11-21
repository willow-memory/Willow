"""dice: faces from the bot's stream seeded by the record's tip, one roll
row through the kernel, and every roll thrown again by check."""

from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("play-dice", HERE / "play_dice.py")
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)
NOW = ["--now", "2026-10-24T09:00:00Z"]


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("x\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "play_dice.py"), *argv],
        capture_output=True,
        text=True,
    )


def test_the_stream_is_the_bots_draw_for_draw():
    s = dc.Stream(b"seed")
    d = hashlib.sha256(b"seed" + (0).to_bytes(8, "big")).digest()
    assert s.u32() == int.from_bytes(d[:4], "big") and s.n == 1
    faces = collections.Counter(dc.Stream(b"x").die(6) for _ in range(1))
    rolls = collections.Counter()
    s = dc.Stream(b"fair")
    for _ in range(6000):
        rolls[s.die(6)] += 1
    assert (
        set(rolls) == {1, 2, 3, 4, 5, 6}
        and all(900 < n < 1100 for n in rolls.values())
        and faces
    )


def test_a_roll_is_seeded_by_the_tip_and_written_as_one_row(tmp_path):
    b = make(tmp_path)
    tip = json.loads((b / "record.jsonl").read_text().splitlines()[-1])["hash"]
    got = run("--box", str(b), "roll", "2d6+1", *NOW)
    assert got.returncode == 0
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "roll" and row["who"] == "dice" and row["seed"] == tip
    assert row == {**row, **dc.throw("2d6+1", tip)}
    assert (
        got.stdout.startswith("2d6+1: ") and f"= {row['total']}   (row 1)" in got.stdout
    )
    assert 3 <= row["total"] <= 13 and len(row["faces"][0]) == 2


def test_check_throws_every_roll_again_and_catches_a_changed_one(tmp_path):
    b = make(tmp_path)
    for dice in ("1d20", "3d6-2", "1d8+1d4"):
        run("--box", str(b), "roll", dice, *NOW)
    got = run("--box", str(b), "check")
    assert (
        got.returncode == 0 and "3 rolls on the record; every one holds." in got.stdout
    )
    rows, _ = dc.kernel.read(b / "record.jsonl")
    faces = rows[2]["faces"]  # one face changed, so never the faces it rolled
    bad = dict(rows[2], faces=[[faces[0][0] % 6 + 1, *faces[0][1:]], *faces[1:]])
    assert dc.check(rows[:2] + [bad] + rows[3:]) == (
        1,
        "row 2: its faces aren't what its seed gives",
    )
    moved = dict(rows[2], seed="0" * 64)
    assert dc.check(rows[:2] + [moved]) == (
        1,
        "row 2: its seed isn't the hash of the row before it",
    )


def test_signs_and_constants_are_said_as_rolled():
    row = {"dice": "1d4-1d4-2", "faces": [[3], [-1]], "add": -2, "total": 0}
    assert dc.said(row) == "1d4-1d4-2: 3 + (-1) + (-2) = 0"


def test_dice_it_cant_read_and_a_bad_command_line_are_refused(tmp_path):
    b = make(tmp_path)
    for dice in ("2x6", "", "101d6", "3", "2d6 4"):
        got = run("--box", str(b), "roll", dice)
        assert got.returncode == 2 and "refused" in got.stderr
    for argv in (
        [],
        ["--box", str(b)],
        ["--box", str(b), "roll"],
        ["--box", str(b), "toss", "1d6"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "play_dice.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path), "check").stderr
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"boot"', b'"booT"', 1))
    assert "doesn't verify" in run("--box", str(b), "check").stderr


def test_one_roll_is_said_as_one(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "roll", "1d6", *NOW)
    assert (
        "1 roll on the record; every one holds." in run("--box", str(b), "check").stdout
    )


def test_a_roll_with_no_count_is_one_die():
    assert dc.parse("d6") == ([(1, 1, 6)], 0)
    assert dc.parse("d20+3") == ([(1, 1, 20)], 3)


def test_a_roll_said_is_kept_as_said_and_marked_so(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "said", "2d6", "4,6", *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout == "2d6: 4 + 6 = 10, as said   (row 1)\n"
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "roll" and row["generator"] == "said" and "seed" not in row
    assert (row["faces"], row["add"], row["total"]) == ([[4, 6]], 0, 10)
    assert run("--box", str(b), "said", "1d8-1d4+2", "8 1", *NOW).stdout.startswith("1d8-1d4+2: 8 + (-1) + 2 = 9, as said")  # fmt: skip
    seeded = run("--box", str(b), "roll", "2d6", *NOW)
    assert ", as said" not in seeded.stdout
    out = run("--box", str(b), "check")
    assert out.returncode == 0 and out.stdout == "3 rolls on the record; every one holds. 2 of them said, kept as said.\n"  # fmt: skip


def test_faces_that_arent_the_dices_are_refused_and_nothing_written(tmp_path):
    b = make(tmp_path)
    for faces, why in [("7,1", "7 isn't a face of a d6: 1 to 6"), ("0,3", "0 isn't a face of a d6"), ("4", "2d6 is 2 dice: say one face for each"), ("4,5,6", "2d6 is 2 dice"), ("four,six", "isn't faces")]:  # fmt: skip
        got = run("--box", str(b), "said", "2d6", faces, *NOW)
        assert got.returncode == 2 and why in got.stderr, (faces, got.stderr)
    kinds = [json.loads(x)["kind"] for x in (b / "record.jsonl").read_text().splitlines()]  # fmt: skip
    assert "roll" not in kinds


def test_only_a_caller_that_takes_said_rolls_holds_one(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "roll", "2d6", *NOW)
    run("--box", str(b), "said", "2d6", "3,3", *NOW)
    rows = [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]
    assert dc.check(rows) == (1, f"row {rows[-1]['n']}: a roll said, not thrown, where only seeded rolls count")  # fmt: skip
    assert dc.check(rows, said=True) == (2, None)


def test_a_said_roll_changed_after_the_fact_doesnt_hold(tmp_path):
    b = make(tmp_path)
    run("--box", str(b), "said", "2d6", "3,4", *NOW)
    good = [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]
    for change in ({"total": 12}, {"faces": [[3, 9]]}, {"faces": [[3]]}, {"add": 1}, {"dice": "1d6"}, {"faces": "x"}):  # fmt: skip
        rows = [dict(r) for r in good]
        rows[-1].update(change)
        held, why = dc.check(rows, said=True)
        assert held == 0 and why and why.startswith(f"row {rows[-1]['n']}: "), change
