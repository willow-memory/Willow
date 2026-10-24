"""life: the known patterns end as they're known to (the R-pentomino's 116
cells at 1103, as willow-bot's own test holds); a game on the record is one
row, played again by check."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("life", HERE / "life.py")
lf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lf)
NOW = ["--now", "2026-10-24T09:00:00Z"]
GLIDER = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)}


def test_the_known_patterns_end_as_they_are_known_to():
    assert lf.run(set(GLIDER), 20, "B3/S23")[1:] == ("spaceship", 4)
    assert lf.run({(0, 1), (1, 1), (2, 1)}, 20, "B3/S23")[1:] == ("oscillator", 2)
    assert lf.run({(0, 0), (1, 0), (0, 1), (1, 1)}, 20, "B3/S23")[1:] == ("still", 1)
    assert lf.run({(0, 0)}, 5, "B3/S23")[1:] == ("dies", 0)
    steps, fate, _ = lf.run({(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)}, 1103, "B3/S23")
    assert (
        [s[0] for s in steps[:6]] == [5, 6, 7, 9, 8, 9]
        and steps[-1][0] == 116
        and fate == "running"
    )


def test_one_shape_has_one_hash_wherever_it_sits():
    a = lf.shape(GLIDER)
    b = lf.shape({(x + 7, y - 3) for x, y in GLIDER})
    assert a[0] == b[0] and a[1:] != b[1:] and lf.shape(set())[0] == lf.shape(set())[0]


def test_another_rule_plays_by_that_rule():
    assert (
        lf.run({(0, 0), (1, 0)}, 3, "B2/S")[0][1][0] == 4
    )  # seeds: two cells make four
    for bad in ("B9/S2", "S23/B3", "life"):
        try:
            lf.rule_of(bad)
            raise AssertionError(bad)
        except ValueError:
            pass


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
        [sys.executable, str(HERE / "life.py"), *argv], capture_output=True, text=True
    )


def test_a_game_is_one_row_and_check_plays_it_again(tmp_path):
    b = make(tmp_path)
    got = run(
        "--box",
        str(b),
        "play",
        "--seed",
        "soup one",
        "--size",
        "12",
        "--generations",
        "40",
        *NOW,
    )
    assert got.returncode == 0 and "(row 1)" in got.stdout
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "life" and row["who"] == "life" and row["rule"] == "B3/S23"
    assert row["fate"] in ("dies", "still", "oscillator", "spaceship", "running")
    assert len(row["steps"]) <= 41 and row["steps"][0][0] == len(
        lf.soup(bytes.fromhex(row["seed"]), 12, 35)
    )
    run("--box", str(b), "play", *NOW)  # seeded by the tip
    got = run("--box", str(b), "check")
    assert (
        got.returncode == 0 and "2 games on the record; every one holds." in got.stdout
    )
    rows, _ = lf.kernel.read(b / "record.jsonl")
    bad = dict(
        rows[1], steps=[rows[1]["steps"][0], [999, 0, 0, "x"]] + rows[1]["steps"][2:]
    )
    assert lf.check([rows[0], bad]) == (
        0,
        "row 1: generation 1 isn't what the rule makes",
    )
    ended = dict(rows[1], fate="dies" if rows[1]["fate"] != "dies" else "still")
    assert lf.check([rows[0], ended]) == (
        0,
        "row 1: how it ended isn't what the rule makes",
    )


def test_bad_settings_and_a_bad_command_line_are_refused(tmp_path):
    b = make(tmp_path)
    for extra in (["--size", "0"], ["--size", "65"], ["--density", "101"], ["--generations", "501"],
                  ["--rule", "B9/S1"], ["--size", "x"]):  # fmt: skip
        got = run("--box", str(b), "play", *extra)
        assert got.returncode == 2 and "refused" in got.stderr
    for argv in (
        [],
        ["--box", str(b)],
        ["--box", str(b), "run"],
        ["--box", str(b), "play", "x"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "life.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path), "check").stderr


def test_the_empty_board_and_the_picture_of_the_last_generation():
    import hashlib

    assert lf.shape(set()) == (hashlib.sha256(b"").hexdigest()[:16], 0, 0)
    seed = hashlib.sha256(b"pic").digest()
    game = lf.play(seed, 10, 40, 6, "B3/S23")
    board = lf.soup(seed, 10, 40)
    birth, survive = lf.rule_of("B3/S23")
    for _ in range(len(game["steps"]) - 1):
        board = lf.step(board, birth, survive)
    rows = lf.picture(seed, game).splitlines()
    assert sum(r.count("#") for r in rows) == len(board) == game["steps"][-1][0]


def test_an_empty_soup_is_allowed_and_dies(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "play", "--density", "0", *NOW)
    assert (
        got.returncode == 0
        and "(empty)" in got.stdout
        and "dies: 0 alive" in got.stdout
    )


def test_zero_generations_is_the_first_board_alone(tmp_path):
    b = make(tmp_path)
    got = run("--box", str(b), "play", "--generations", "0", "--seed", "z", *NOW)
    assert got.returncode == 0 and "after 0 generations" in got.stdout
