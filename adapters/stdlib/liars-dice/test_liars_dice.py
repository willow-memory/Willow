"""liars-dice: game-lab's rules held, every cup dice's own throw, and check
finding a forged row. Tables are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("liars_dice", HERE / "liars_dice.py")
ld = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ld)
kernel = ld.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]


def table(*cups: str, dice=None) -> ld.Game:
    g = ld.Game()
    if dice:
        g.dice = list(dice)
    g.start({s: [int(c) for c in cup] for s, cup in enumerate(cups) if cup})
    return g


class Table:
    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box = tmp / "box"
        subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(self.box), *NOW, "--pile", str(pile), "--key", str(tmp / "k")],
                       capture_output=True, text=True, check=True)  # fmt: skip

    def run(self, *argv):
        return subprocess.run([sys.executable, str(HERE / "liars_dice.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def verify(self):
        return subprocess.run([sys.executable, str(KERNEL), "verify", "--box", str(self.box), *NOW],
                              capture_output=True, text=True, check=False).returncode == 0  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def game(self):
        rows = self.rows()
        return ld.replay(rows, ld.games(rows)[-1])

    def game_n(self):
        return [r for r in self.rows() if r["kind"] == ld.OPEN][-1]["n"]

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=ld.WHO, **fields)


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the rules ────────────────────────────────────────────────────────────────
def test_ones_are_wild_except_in_a_bid_on_ones():
    assert ld.counted([1, 5, 5, 3, 1], 5) == 4
    assert ld.counted([1, 5, 5, 3, 1], 1) == 2


@pytest.mark.parametrize(
    "bid, q, f, ok",
    [(None, 1, 1, True), ((3, 4), 3, 5, True), ((3, 4), 4, 2, True), ((3, 4), 3, 4, False),
     ((3, 4), 2, 6, False), ((3, 4), 21, 2, False), ((3, 4), 4, 7, False), (None, 0, 3, False)],
)  # fmt: skip
def test_a_raise_is_more_dice_or_as_many_of_a_higher_face(bid, q, f, ok):
    assert ld.above(bid, q, f, 20) is ok


def test_a_bid_that_holds_costs_the_caller_a_die():
    g = table("11111", "22222", "33333", "44444")
    g.raise_(0, 9, 2)  # five 2s and five wild ones: ten
    said = g.call(1)
    assert said == {"bid": [9, 2], "bidder": "north", "count": 10, "loser": "east"}
    assert g.dice == [5, 4, 5, 5] and g.opener == 1


def test_a_bid_that_doesnt_costs_the_bidder_a_die():
    g = table("23456", "23456", "23456", "23456")
    g.raise_(0, 5, 6)
    g.call(1)
    assert g.dice == [4, 5, 5, 5] and g.opener == 0


def test_the_turn_goes_round_the_seats_still_in():
    g = table("2", "", "34", "5", dice=[1, 0, 2, 1])
    g.raise_(0, 1, 3)
    assert g.turn == 2
    g.raise_(2, 1, 4)
    assert g.turn == 3


def test_a_loser_out_of_dice_hands_the_opening_on_and_the_last_seat_wins():
    g = table("6", "", "", "2", dice=[1, 0, 0, 1])
    g.raise_(0, 2, 6)
    g.call(3)  # one 6, the bid fails: north is out
    assert g.over and g.result() == "west won"


def test_the_opener_bids_and_nobody_calls_out_of_turn():
    g = table("11111", "22222", "33333", "44444")
    with pytest.raises(ValueError, match="no bid to call"):
        g.call(0)
    with pytest.raises(ValueError, match="north's turn"):
        g.raise_(1, 1, 2)


def test_a_round_throws_every_cup_still_in():
    g = ld.Game()
    with pytest.raises(ValueError, match="every cup still in"):
        g.start({0: [1, 2, 3, 4, 5]})
    assert g.throws_wanted() == [(s, "5d6") for s in range(4)]


# ── the record ───────────────────────────────────────────────────────────────
def test_new_throws_every_cup_as_dices_own_row(t):
    got = t.run("new")
    assert got.returncode == 0 and "north opens" in got.stdout
    rows = t.rows()
    rnd = rows[-1]
    assert rnd["kind"] == ld.ROUND and rnd["rolls"] == [
        rnd["n"] - 4 + i for i in range(4)
    ]
    assert all(
        rows[n]["kind"] == "roll" and rows[n]["dice"] == "5d6" for n in rnd["rolls"]
    )
    assert rnd["cups"]["north"] == ld.faces_of(rows[rnd["rolls"][0]])
    assert "north opens with a bid" in t.run("show").stdout


def test_a_call_counts_the_dice_and_throws_the_next_round(t):
    t.run("new")
    assert t.run("bid", "1", "2").returncode == 0
    got = t.run("call")
    assert got.returncode == 0 and "round 2 thrown" in got.stdout
    rows = t.rows()
    call = next(r for r in reversed(rows) if r["kind"] == ld.CALL)
    assert call["loser"] == ("east" if call["count"] >= 1 else "north")
    assert sum(t.game().dice) == 19 and rows[-1]["kind"] == ld.ROUND
    assert t.run("check").returncode == 0 and t.verify()


def test_a_whole_game_played_to_its_end_holds(t):
    t.run("new")
    for _ in range(200):
        g = t.game()
        if g.over:
            break
        if g.bid is None:
            assert t.run("bid", "1", "6").returncode == 0
        else:
            assert t.run("call").returncode == 0
    g = t.game()
    assert g.over and sum(g.dice) == g.dice[g.seats_in()[0]] and "won" in g.result()
    assert t.run("check").returncode == 0
    assert "is over" in t.run("call").stderr
    assert t.run("new").returncode == 0


def test_bids_the_rules_dont_allow_are_refused_and_write_nothing(t):
    t.run("new")
    t.run("bid", "3", "4")
    before = t.raw()
    for argv in (
        ("bid", "3", "4"),
        ("bid", "2", "6"),
        ("bid", "21", "2"),
        ("bid", "4", "7"),
        ("bid", "x", "2"),
    ):
        assert t.run(*argv).returncode == 2, argv
    assert t.raw() == before


def test_nothing_is_played_before_a_game_is_opened(t):
    for argv in (("bid", "1", "2"), ("call",), ("show",)):
        assert "no game is open" in t.run(*argv).stderr
    assert "0 games" in t.run("check").stdout


def test_new_waits_for_the_game_to_end(t):
    t.run("new")
    assert "isn't over" in t.run("new").stderr


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_bid_out_of_turn(t):
    t.run("new")
    t.forge(ld.BID, game=t.game_n(), round=1, seat="south", quantity=2, face=3)
    got = t.run("check")
    assert got.returncode == 2 and "north's turn" in got.stderr
    assert "don't hold" in t.run("show").stderr


def test_check_finds_a_call_that_isnt_what_the_dice_count(t):
    t.run("new")
    t.run("bid", "1", "2")
    t.run("call")
    rows = t.rows()
    i = next(i for i in range(len(rows) - 1, -1, -1) if rows[i]["kind"] == ld.CALL)
    assert ld.check(rows) == (1, None)
    rows[i] = {**rows[i], "loser": "north" if rows[i]["loser"] != "north" else "east"}
    held, why = ld.check(rows)
    assert held == 0 and "the dice say" in why


def test_check_finds_cups_that_arent_the_throws_before_them(t):
    t.run("new")
    t.run("bid", "1", "2")
    t.run("call")
    rows = t.rows()
    first = next(r for r in rows if r["kind"] == ld.ROUND)
    assert rows[-1]["kind"] == ld.ROUND and ld.check(rows) == (1, None)
    rows[-1] = {**rows[-1], "rolls": first["rolls"]}  # round 2 naming round 1's throws
    held, why = ld.check(rows)
    assert held == 0 and "throws straight before it" in why


def test_check_finds_a_cup_that_isnt_what_dice_threw(t):
    t.run("new")
    rows = t.rows()
    rows[-1] = {**rows[-1], "cups": {**rows[-1]["cups"], "north": [6, 6, 6, 6, 6]}}
    held, why = ld.check(rows)
    assert held == 0 and "aren't what dice threw" in why


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(ld.BID, game=0, round=1, seat="north", quantity=1, face=2)
    assert "isn't a game opened before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("bid",), ("bid", "3"), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "liars_dice.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
