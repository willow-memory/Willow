"""crazy-eights: game-lab's rules held, every deal its seed's own, and
check finding a forged row. Hands are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("crazy_eights", HERE / "crazy_eights.py")
c8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c8)
kernel = c8.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]


def cards(text: str) -> list:
    return [c8.card_of(c) for c in text.split()]


def game(hands: str, top: str, suit: str, stock: str = "") -> c8.Game:
    g = c8.Game("x")
    g.hands = [cards(h) for h in hands.split("|")]
    g.top, g.suit, g.stock = c8.card_of(top), suit, cards(stock)
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
        return subprocess.run([sys.executable, str(HERE / "crazy_eights.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def game(self):
        rows = self.rows()
        return c8.replay(rows, c8.games(rows)[-1])

    def game_n(self):
        return [r for r in self.rows() if r["kind"] == c8.DEAL][-1]["n"]

    def k_verify(self):
        return subprocess.run([sys.executable, str(KERNEL), "verify", "--box", str(self.box), *NOW],
                              capture_output=True, text=True, check=False).returncode == 0  # fmt: skip

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=c8.WHO, **fields)

    def step(self):
        g = self.game()
        ok = g.can_play()
        if ok:
            card = ok[0]
            argv = ("play", c8.name(card), *(["H"] if card[0] == 8 else []))
        else:
            argv = ("draw",) if g.stock else ("pass",)
        got = self.run(*argv)
        assert got.returncode == 0, got.stderr

    def play_out(self):
        for _ in range(400):
            if self.game().over:
                return
            self.step()
        raise AssertionError("the hand didn't end")


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the rules ────────────────────────────────────────────────────────────────
def test_a_card_follows_the_suit_or_the_rank_and_an_8_always():
    g = game("3C 9D 8S KH 9H|2C|2C|2C", "9C", "C")
    assert g.can_play() == cards("3C 9D 8S 9H")


def test_after_an_8_the_named_suit_is_followed():
    g = game("3C 9D 8S KH 2D|2C|2C|2C", "8S", "H")
    assert g.can_play() == cards("8S KH")


def test_an_8_names_a_suit_and_nothing_else_does():
    g = game("8S 3C|2C 2D|2C|2C", "9C", "C")
    with pytest.raises(ValueError, match="names the suit"):
        g.play(0, c8.card_of("8S"), None)
    with pytest.raises(ValueError, match="only an 8"):
        g.play(0, c8.card_of("3C"), "H")
    g.play(0, c8.card_of("8S"), "D")
    assert (g.suit, g.turn) == ("D", 1)


def test_a_seat_draws_only_with_nothing_to_play_and_goes_again():
    g = game("3C|2D|2C|2C", "9H", "H", "5S KH")
    assert g.draw(0) == c8.card_of("KH")  # the last first, as game-lab draws
    assert g.turn == 0 and g.can_play() == cards("KH")
    with pytest.raises(ValueError, match="can play, so doesn't draw"):
        g.draw(0)


def test_a_seat_passes_only_with_nothing_to_play_and_no_stock():
    g = game("3C|2D|2C|2C", "9H", "H", "5S")
    with pytest.raises(ValueError, match="draws first"):
        g.pass_(0)
    g.stock = []
    g.pass_(0)
    assert g.turn == 1 and g.passes == 1


def test_four_passes_with_no_stock_stall_the_hand():
    g = game("3C|3D|3S|4C", "9H", "H")
    for s in range(4):
        g.pass_(s)
    assert g.over and g.result() == "stalled"


def test_the_last_card_played_wins():
    g = game("3H|2D 4D|2C|2C", "9H", "H")
    g.play(0, c8.card_of("3H"), None)
    assert g.over and g.result() == "north won"
    with pytest.raises(ValueError, match="is over"):
        g.play(1, c8.card_of("2D"), None)


def test_a_card_not_held_or_out_of_turn_is_refused():
    g = game("3H|4H|2C|2C", "9H", "H")
    with pytest.raises(ValueError, match="doesn't hold"):
        g.play(0, c8.card_of("4H"), None)
    with pytest.raises(ValueError, match="north's turn"):
        g.play(1, c8.card_of("4H"), None)


def test_a_seed_deals_the_same_every_time_and_the_whole_deck():
    a = c8.dealt("seed")
    assert a == c8.dealt("seed") and a != c8.dealt("other")
    every = [c for h in a["hands"] for c in h] + [a["top"]] + a["stock"]
    assert sorted(every) == sorted(c8.deck()) and all(len(h) == 5 for h in a["hands"])


@pytest.mark.parametrize("text", ["1C", "QX", "Q", "", "11H", None])
def test_what_isnt_a_card_is_refused(text):
    with pytest.raises(ValueError, match="isn't a card"):
        c8.card_of(text)


# ── the record ───────────────────────────────────────────────────────────────
def test_new_deals_from_the_record_tip(t):
    got = t.run("new")
    assert got.returncode == 0 and "north to play" in got.stdout
    d = t.rows()[-1]
    want = c8.dealt(d["seed"])
    assert d["kind"] == c8.DEAL and d["seed"] == t.rows()[-2]["hash"]
    assert d["top"] == c8.name(want["top"]) and len(d["stock"]) == 31
    assert "to follow; stock: 31" in t.run("show").stdout


def test_a_whole_hand_played_out_holds(t):
    t.run("new")
    t.play_out()
    g = t.game()
    assert g.result() in ("stalled", *(f"{s} won" for s in c8.SEATS))
    assert t.rows()[-1]["result"] == g.result()
    assert t.run("check").returncode == 0 and t.k_verify()
    assert "is over" in t.run("draw").stderr
    assert t.run("new").returncode == 0


def test_moves_the_rules_dont_allow_are_refused_and_write_nothing(t):
    t.run("new")
    g = t.game()
    held = set(g.hands[0])
    wrong = next(c for c in c8.deck() if c not in held and c != g.top)
    before = t.raw()
    argv = [("play", c8.name(wrong)), ("play", "ZZ"), ("pass",)]
    argv.append(("draw",) if g.can_play() else ("play", c8.name(sorted(held)[0])))
    for a in argv:
        assert t.run(*a).returncode == 2, a
    assert t.raw() == before


def test_new_waits_for_the_hand_to_end(t):
    t.run("new")
    assert "isn't over" in t.run("new").stderr


def test_nothing_is_played_before_a_hand_is_dealt(t):
    for argv in (("play", "2C"), ("draw",), ("pass",), ("show",)):
        assert "no hand is dealt" in t.run(*argv).stderr
    assert "0 hands" in t.run("check").stdout


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_deal_its_seed_doesnt_give(t):
    seed = t.rows()[-1]["hash"]
    d = c8.dealt("stacked")
    t.forge(c8.DEAL, seats=list(c8.SEATS), seed=seed, generator=c8.GENERATOR, hands=[[c8.name(c) for c in h] for h in d["hands"]],
            top=c8.name(d["top"]), stock=[c8.name(c) for c in d["stock"]])  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "aren't what its seed deals" in got.stderr
    assert "don't hold" in t.run("show").stderr


def test_check_finds_a_draw_that_isnt_the_top_of_the_stock(t):
    t.run("new")
    for _ in range(2000):
        g = t.game()
        if not g.over and not g.can_play() and g.stock:
            break
        if g.over:
            t.run("new")
        else:
            t.step()
    assert not g.can_play() and g.stock, "no hand came to a draw"
    wrong = c8.name(g.stock[0])
    t.forge(c8.DRAW, game=t.game_n(), seat=c8.SEATS[g.turn], card=wrong, result="on")
    assert "isn't the one on top of the stock" in t.run("check").stderr


def test_check_finds_a_card_played_out_of_turn(t):
    t.run("new")
    g = t.game()
    t.forge(
        c8.PLAY, game=t.game_n(), seat="east", card=c8.name(g.hands[1][0]), result="on"
    )
    assert "it is north's turn" in t.run("check").stderr


def test_check_finds_an_ending_the_cards_dont_give(t):
    t.run("new")
    t.step()
    rows = t.rows()
    assert c8.check(rows) == (1, None)
    rows[-1] = {**rows[-1], "result": "north won"}
    held, why = c8.check(rows)
    assert held == 0 and "the cards say 'on'" in why


def test_check_finds_a_row_whose_game_was_never_dealt(t):
    t.forge(c8.PLAY, game=0, seat="north", card="2C", result="on")
    assert "isn't a game dealt before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("play",), ("play", "8H", "S", "x"), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "crazy_eights.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
