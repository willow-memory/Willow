"""backgammon: the rules held whole, every throw dice's own row, and check
finding a forged one. Positions are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("backgammon", HERE / "backgammon.py")
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)
kernel = bg.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]


def board(white: dict, black: dict, wbar=0, bbar=0, woff=None, boff=None) -> dict:
    def side(pts, bar, off):
        return {"pts": dict(pts), "bar": bar, "off": 15 - sum(pts.values()) - bar if off is None else off}  # fmt: skip

    return {"white": side(white, wbar, woff), "black": side(black, bbar, boff)}


def plays(state, side, faces) -> set[str]:
    return {bg.written(m) for m, _ in bg.turns(state, side, faces)}


class Table:
    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box = tmp / "box"
        self.k("init", "--pile", str(pile), "--key", str(tmp / "k"))

    def k(self, *argv):
        return subprocess.run([sys.executable, str(KERNEL), argv[0], "--box", str(self.box), *NOW, *argv[1:]],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def run(self, *argv):
        return subprocess.run([sys.executable, str(HERE / "backgammon.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def state(self):
        rows = self.rows()
        return bg.state_of(rows, bg.games(rows)[-1])

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=bg.WHO, **fields)

    def game(self):
        return [r for r in self.rows() if r["kind"] == bg.OPEN][-1]["n"]


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the rules ────────────────────────────────────────────────────────────────
def test_the_opening_three_one_makes_the_five_point():
    s = board(bg.START, bg.START)
    assert "8/5 6/5" in plays(s, "white", [3, 1])
    assert all(len(p.split()) == 2 for p in plays(s, "white", [3, 1]))


def test_a_doublet_is_played_four_times():
    s = board(bg.START, bg.START)
    assert all(len(p.split()) == 4 for p in plays(s, "white", [6, 6]))
    assert "24/18 24/18 13/7 13/7" in plays(s, "white", [6, 6])


def test_a_checker_on_the_bar_enters_before_anything_else():
    s = board({13: 5, 6: 5, 8: 4}, bg.START, wbar=1)
    assert all(p.startswith("bar/") for p in plays(s, "white", [4, 2]))
    shut = board(
        {13: 5, 6: 5, 8: 4}, {4: 2, 2: 2, 13: 5, 6: 6}, wbar=1
    )  # white's 21 and 23 held
    assert plays(shut, "white", [4, 2]) == {"none"}


def test_a_turn_uses_both_dice_when_it_can():
    s = board(
        {6: 1}, {12: 2}, woff=14
    )  # 6/off alone is a 6; a 4 and a 2 must both be used
    assert plays(s, "white", [4, 2]) == {"6/2 2/off", "6/4 4/off"}


def test_when_only_one_die_can_be_played_it_is_the_larger():
    """Either die alone can be played here, but not both: so the 3."""
    s = board(
        {9: 1, 17: 1}, {18: 2, 17: 2, 12: 4, 3: 2, 23: 2, 19: 2, 22: 2}, woff=13, boff=1
    )
    assert bg.single(s, "white", 1) and bg.single(s, "white", 3)
    assert plays(s, "white", [1, 3]) == {"17/14"}


def test_bearing_off_is_from_home_exact_or_from_the_highest():
    s = board(
        {5: 1, 3: 1}, {6: 2}, woff=13
    )  # black's 6 is white's 19: nothing in the way
    assert "5/off 3/1" in plays(s, "white", [6, 2])
    assert ("5/off", "3/off") == tuple(sorted(w for w in plays(s, "white", [6, 5]) if w.count("off") == 2)[0].split())  # fmt: skip
    not_home = board({7: 1, 3: 1}, {6: 2}, woff=13)
    assert not any(p.startswith("3/off") for p in plays(not_home, "white", [6, 1]))


def test_the_endings_are_one_two_and_three():
    won = board({}, {6: 2}, woff=15, boff=13)
    assert bg.ending(won, "white") == ("white won", 1)
    gammon = board({}, {6: 15}, woff=15, boff=0)
    assert bg.ending(gammon, "white") == ("white won a gammon", 2)
    back = board({}, {20: 1, 6: 14}, woff=15, boff=0)
    assert bg.ending(back, "white") == ("white won a backgammon", 3)
    on_bar = board({}, {6: 14}, bbar=1, woff=15, boff=0)
    assert bg.ending(on_bar, "white") == ("white won a backgammon", 3)
    assert bg.ending(board(bg.START, bg.START), "white") == ("on", 0)


def test_a_hit_sends_the_lone_checker_to_the_bar():
    s = board({13: 1}, {19: 1}, woff=14, boff=14)  # black's 19 is white's 6
    after = bg.play(s, "white", 13, 6)
    assert after["black"]["bar"] == 1 and 19 not in after["black"]["pts"]


@pytest.mark.parametrize(
    "text, says",
    [
        ("24-18", "isn't a move"),
        ("6/9", "higher point to a lower one"),
        ("25/off", "isn't a turn"),
    ],
)
def test_what_isnt_a_turn_says_what_is(text, says):
    with pytest.raises(ValueError, match=says):
        bg.find(board(bg.START, bg.START), "white", [3, 1], text)


def test_the_same_checkers_in_another_order_are_the_same_turn():
    s = board(bg.START, bg.START)
    moves, _ = bg.find(s, "white", [3, 1], "6/5 8/5")
    assert bg.written(moves) == "6/5 8/5"


# ── the record ───────────────────────────────────────────────────────────────
def test_new_throws_the_opening_and_the_higher_plays_both(t):
    got = t.run("new")
    assert got.returncode == 0 and "opening throw" in got.stdout
    o = [r for r in t.rows() if r["kind"] == bg.OPEN][-1]
    rolls = [t.rows()[n] for n in o["rolls"]]
    assert all(r["kind"] == "roll" and r["dice"] == "2d6" for r in rolls)
    w, b = (abs(f) for f in rolls[-1]["faces"][0])
    assert o["first"] == ("white" if w > b else "black") and o["dice"] == [w, b]
    assert t.run("check").returncode == 0


def test_a_turn_is_played_then_the_other_side_throws(t):
    t.run("new")
    st = t.state()
    turn = bg.written(bg.turns(st["board"], st["to_move"], st["faces"])[0][0])
    got = t.run("move", turn)
    assert got.returncode == 0, got.stderr
    assert t.run("move", turn).returncode == 2  # the other side hasn't thrown
    assert "to throw: roll" in t.run("show").stdout
    assert t.run("roll").returncode == 0
    r = t.rows()[-1]
    assert (
        r["kind"] == bg.ROLL
        and r["roll_row"] == r["n"] - 1
        and r["side"] != t.rows()[-3]["side"]
    )
    assert t.run("roll").returncode == 2  # a throw waits to be played
    assert t.run("check").returncode == 0 and t.k("verify").returncode == 0


def test_a_whole_game_played_to_its_end_holds(t):
    t.run("new")
    for _ in range(600):
        st = t.state()
        if st["result"] != "on":
            break
        if st["faces"] is None:
            assert t.run("roll").returncode == 0
            continue
        moves = bg.turns(st["board"], st["to_move"], st["faces"])[0][0]
        assert t.run("move", bg.written(moves)).returncode == 0
    assert "won" in t.state()["result"]
    assert t.run("check").returncode == 0
    assert "is over" in t.run("roll").stderr
    assert t.run("new").returncode == 0


def test_a_turn_the_dice_dont_allow_is_refused_and_writes_nothing(t):
    t.run("new")
    before = t.raw()
    for text in ("24/1", "nonsense", "none"):
        assert t.run("move", text).returncode == 2
    assert t.raw() == before


def test_the_side_to_move_resigns(t):
    t.run("new")
    side = t.state()["to_move"]
    got = t.run("resign")
    assert got.returncode == 0 and f"{side} resigns" in got.stdout
    assert t.run("check").returncode == 0


def test_nothing_is_played_before_a_game_is_opened(t):
    for argv in (("roll",), ("move", "24/18"), ("resign",), ("show",)):
        assert "no game is open" in t.run(*argv).stderr
    assert "0 games" in t.run("check").stdout


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_move_the_throw_doesnt_allow(t):
    t.run("new")
    st = t.state()
    t.forge(
        bg.MOVE, game=t.game(), side=st["to_move"], move="24/1", result="on", points=0
    )
    got = t.run("check")
    assert got.returncode == 2 and "isn't a turn" in got.stderr
    assert "don't hold" in t.run("show").stderr


def test_check_finds_a_move_by_the_wrong_side_or_before_a_throw(t):
    t.run("new")
    st = t.state()
    wrong = bg.other(st["to_move"])
    t.forge(bg.MOVE, game=t.game(), side=wrong, move="24/23", result="on", points=0)
    assert f"it was {st['to_move']}'s turn" in t.run("check").stderr


def test_check_finds_a_throw_that_isnt_the_dices(t):
    t.run("new")
    st = t.state()
    turn = bg.written(bg.turns(st["board"], st["to_move"], st["faces"])[0][0])
    t.run("move", turn)
    t.forge(
        bg.ROLL, game=t.game(), side=bg.other(st["to_move"]), roll_row=1, dice=[6, 6]
    )
    assert "not straight after the 2d6 it names" in t.run("check").stderr


def test_check_finds_an_opening_that_isnt_its_throw(t):
    t.run("new")
    o = [r for r in t.rows() if r["kind"] == bg.OPEN][-1]
    t.forge(bg.OPEN, rolls=o["rolls"], first=bg.other(o["first"]), dice=o["dice"])
    assert "the opening throw says" in t.run("check").stderr


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(bg.MOVE, game=0, side="white", move="24/23", result="on", points=0)
    assert "isn't a game opened before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("move",), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "backgammon.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
