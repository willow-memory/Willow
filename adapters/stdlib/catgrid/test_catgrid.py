"""catgrid: boards from the bot's stream with one answer, moves replayed, and
every game thrown again by check."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("catgrid", HERE / "catgrid.py")
cg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cg)
NOW = ["--now", "2026-11-01T09:00:00Z"]


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
        [sys.executable, str(HERE / "catgrid.py"), *argv],
        capture_output=True,
        text=True,
    )


def last(b: Path) -> dict:
    return json.loads((b / "record.jsonl").read_text().splitlines()[-1])


def cells_of(n: int, answer) -> list[str]:
    return [cg.address(r, c) for r, c in enumerate(answer)]


def test_a_board_has_n_connected_regions_and_exactly_one_answer():
    for n in range(cg.MIN_SIZE, cg.MAX_SIZE + 1):
        for text in ("a", "b", "c"):
            regions, answer = cg.board(cg.seed_of(text), n)
            assert set(regions) == set(range(1, n + 1)) and len(regions) == n * n
            assert all(cg.connected(regions, n, o) for o in range(1, n + 1))
            assert list(cg.solutions(n, regions)) == [answer]
            assert sorted(answer) == list(range(n))
            assert all(abs(a - b) >= 2 for a, b in zip(answer, answer[1:]))
            assert sorted(regions[r * n + c] for r, c in enumerate(answer)) == list(
                range(1, n + 1)
            )


def test_the_same_seed_is_the_same_board_and_another_seed_another():
    one = cg.board(cg.seed_of("a"), 6)
    assert one == cg.board(cg.seed_of("a"), 6)
    assert any(cg.board(cg.seed_of(t), 6) != one for t in "bcdef")
    # frozen: the stream's draws decide this, so a drifting stream shows here
    assert cg.Stream(b"seed").shuffled(range(5)) == cg.Stream(b"seed").shuffled(
        range(5)
    )
    assert sorted(cg.Stream(b"seed").shuffled(range(5))) == list(range(5))


def test_the_solver_counts_a_second_answer_when_regions_allow_one():
    n = 4
    split = [r + 1 for r in range(n) for _ in range(n)]  # a colour per row
    assert len(list(cg.solutions(n, split))) == 2  # the two non-touching placements


def test_a_won_game_stays_and_a_wrong_cat_costs_a_heart(tmp_path):
    b = make(tmp_path)
    _, answer = cg.board(cg.seed_of("w"), 5)
    right = cells_of(5, answer)
    wrong = next(cg.address(0, c) for c in range(5) if c != answer[0])
    got = run(
        "--box",
        str(b),
        "play",
        "--seed",
        "w",
        "--moves",
        ",".join([wrong, *right]),
        *NOW,
    )
    assert (
        got.returncode == 0 and "won: 2 hearts left, 5 of 5 cats placed" in got.stdout
    )
    row = last(b)
    assert row["kind"] == "catgrid" and row["who"] == "catgrid" and row["by"] == "given"
    assert row["verdicts"] == ["wrong"] + ["right"] * 5
    assert row["hearts"] == 2 and row["status"] == "won" and "solution" not in row
    assert got.stdout.count("@") == 5
    assert (b / "record.jsonl").read_text().count('"kind":"catgrid"') == 1


def test_three_wrong_cats_lose_and_moves_after_the_end_are_refused(tmp_path):
    b = make(tmp_path)
    _, answer = cg.board(cg.seed_of("l"), 5)
    wrongs = [cg.address(r, (answer[r] + 2) % 5) for r in range(4)]
    wrongs = [w for w in wrongs if cg.cell(w, 5)[1] != answer[cg.cell(w, 5)[0]]]
    got = run(
        "--box", str(b), "play", "--seed", "l", "--moves", ",".join(wrongs[:3]), *NOW
    )
    assert "lost: 0 hearts left, 0 of 5 cats placed" in got.stdout
    more = run("--box", str(b), "play", "--seed", "l", "--moves", ",".join(wrongs[:4]))
    assert more.returncode == 2 and "already over" in more.stderr


def test_no_moves_leaves_the_board_open_and_the_seed_is_the_tip(tmp_path):
    b = make(tmp_path)
    tip = last(b)["hash"]
    got = run("--box", str(b), "play", "--size", "4", *NOW)
    assert (
        got.returncode == 0 and "open: 3 hearts left, 0 of 4 cats placed" in got.stdout
    )
    row = last(b)
    assert row["seed"] == tip and row["by"] == "tip" and row["size"] == 4
    assert run("--box", str(b), "check").stdout.startswith("1 game on the record")


def test_check_throws_every_game_again_and_names_what_changed(tmp_path):
    b = make(tmp_path)
    _, answer = cg.board(cg.seed_of("k"), 5)
    run(
        "--box",
        str(b),
        "play",
        "--seed",
        "k",
        "--moves",
        ",".join(cells_of(5, answer)),
        *NOW,
    )
    run("--box", str(b), "play", "--size", "6", *NOW)
    got = run("--box", str(b), "check")
    assert (
        got.returncode == 0 and "2 games on the record; every one holds." in got.stdout
    )
    rows, _ = cg.kernel.read(b / "record.jsonl")
    flipped = dict(rows[1], verdicts=["wrong", *rows[1]["verdicts"][1:]])
    assert cg.check([*rows[:1], flipped, *rows[2:]]) == (
        0,
        "row 1: its verdicts aren't what its seed gives",
    )
    for key, why in (
        ("regions", "regions"),
        ("hearts", "hearts"),
        ("status", "status"),
    ):
        bad = dict(
            rows[1],
            **{key: [] if key == "regions" else 9 if key == "hearts" else "lost"},
        )
        assert cg.check([*rows[:1], bad]) == (
            0,
            f"row 1: its {why} aren't what its seed gives",
        )
    moved = dict(rows[2], seed="0" * 64)
    assert cg.check(rows[:2] + [moved]) == (
        1,
        "row 2: its seed isn't the hash of the row before it",
    )
    broken = dict(rows[1], moves=["Z9"])
    assert cg.check([*rows[:1], broken])[1].startswith("row 1: 'Z9' isn't a cell")
    assert cg.check([*rows[:1], dict(rows[1], size=2)])[0] == 0


def test_cells_sizes_and_a_bad_command_line_are_refused(tmp_path):
    b = make(tmp_path)
    for extra in (["--size", "3"], ["--size", "9"], ["--size", "x"],
                  ["--moves", "A0"], ["--moves", "F1"], ["--moves", "a1"], ["--moves", "A6"]):  # fmt: skip
        got = run("--box", str(b), "play", "--seed", "s", *extra)
        assert got.returncode == 2 and "refused" in got.stderr
    _, answer = cg.board(cg.seed_of("s"), 5)
    twice = cells_of(5, answer)[0]
    got = run("--box", str(b), "play", "--seed", "s", "--moves", f"{twice},{twice}")
    assert got.returncode == 2 and "already holds a cat" in got.stderr
    for argv in ([], ["--box", str(b)], ["--box", str(b), "toss"]):
        got = run(*argv)
        assert got.returncode == 2 and "catgrid.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path), "check").stderr
    assert (
        len((b / "record.jsonl").read_text().splitlines()) == 1
    )  # nothing was written
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"boot"', b'"booT"', 1))
    assert "doesn't verify" in run("--box", str(b), "check").stderr
    assert "doesn't verify" in run("--box", str(b), "play").stderr


def test_one_game_is_said_as_one_and_an_empty_record_holds(tmp_path):
    b = make(tmp_path)
    assert "0 games on the record" in run("--box", str(b), "check").stdout
    assert cg.address(1, 2) == "B3" and cg.cell("B3", 5) == (1, 2)
