"""hearts: game-lab's rules held, every deal its seed's own, and check
finding a forged row. Hands are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("hearts", HERE / "hearts.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
kernel = h.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]


def cards(text: str) -> list:
    return [h.card_of(c) for c in text.split()]


class Table:
    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box = tmp / "box"
        subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(self.box), *NOW, "--pile", str(pile), "--key", str(tmp / "k")],
                       capture_output=True, text=True, check=True)  # fmt: skip

    def run(self, *argv):
        return subprocess.run([sys.executable, str(HERE / "hearts.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def game(self):
        rows = self.rows()
        return h.replay(rows, h.games(rows)[-1])

    def game_n(self):
        return [r for r in self.rows() if r["kind"] == h.OPEN][-1]["n"]

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=h.WHO, **fields)

    def pass_all(self):
        g = self.game()
        for s in range(4):
            assert (
                self.run(
                    "pass", h.SEATS[s], *(h.name(c) for c in g.hands[s][:3])
                ).returncode
                == 0
            )

    def play_hand(self):
        if self.game().phase == "pass":
            self.pass_all()
        for _ in range(52):
            g = self.game()
            s = g.to_play()
            card = h.legal(g.hands[s], g.trick, g.broken, g.tricks == 0)[0]
            got = self.run("play", h.name(card))
            assert got.returncode == 0, got.stderr


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the rules ────────────────────────────────────────────────────────────────
def test_the_two_of_clubs_leads_the_first_trick():
    assert h.legal(cards("2C 5C AH QS"), [], False, True) == [h.TWO_CLUBS]


def test_hearts_wait_to_be_broken_unless_nothing_else_is_held():
    assert h.legal(cards("3H AH 4D"), [], False, False) == cards("4D")
    assert h.legal(cards("3H AH"), [], False, False) == cards("3H AH")
    assert h.legal(cards("3H AH 4D"), [], True, False) == cards("3H AH 4D")


def test_the_suit_led_is_followed_when_it_can_be():
    trick = [(0, h.card_of("9D"))]
    assert h.legal(cards("3H 4D KD QS"), trick, True, False) == cards("4D KD")
    assert h.legal(cards("3H QS 5C"), trick, True, False) == cards("3H QS 5C")


def test_no_points_on_the_first_trick_unless_there_is_nothing_else():
    trick = [(0, h.TWO_CLUBS)]
    assert h.legal(cards("3H QS 5D"), trick, False, True) == cards("5D")
    assert h.legal(cards("3H QS"), trick, False, True) == cards("3H QS")


def test_the_passes_go_left_right_across_then_none():
    assert [h.TO[h.direction(n)] for n in range(5)] == ["left", "right", "across", "held", "left"]  # fmt: skip
    assert [h.target(0, w) for w in range(4)] == [1, 3, 2, 0]


@pytest.mark.parametrize("text, card", [("2C", (2, "C")), ("10h", (10, "H")), ("TH", (10, "H")), ("QS", (12, "S")), ("AD", (14, "D"))])  # fmt: skip
def test_a_card_is_rank_then_suit(text, card):
    assert h.card_of(text) == card and h.card_of(h.name(card)) == card


@pytest.mark.parametrize("text", ["1C", "QX", "Q", "", "11H"])
def test_what_isnt_a_card_is_refused(text):
    with pytest.raises(ValueError, match="isn't a card"):
        h.card_of(text)


def test_a_seed_deals_the_same_four_hands_every_time():
    a, b = h.dealt("seed"), h.dealt("seed")
    assert a == b and a != h.dealt("other")
    assert sorted(c for hand in a for c in hand) == sorted(h.deck())


def test_shooting_the_moon_gives_every_other_seat_26():
    g = h.Game()
    g.taken = [[(r, "H") for r in range(2, 15)] + [h.QUEEN], [], [], []]
    g._score()
    assert g.last == [0, 26, 26, 26]


def test_the_lowest_score_wins_once_a_seat_is_on_100():
    g = h.Game()
    g.scores, g.over = [101, 40, 55, 40], True
    assert g.result() == "east and west tied"
    g.scores = [101, 39, 55, 40]
    assert g.result() == "east won"


# ── the record ───────────────────────────────────────────────────────────────
def test_new_deals_the_first_hand_from_the_record_tip(t):
    got = t.run("new")
    assert got.returncode == 0 and "pass left" in got.stdout
    deal = t.rows()[-1]
    assert deal["kind"] == h.DEAL and deal["seed"] == t.rows()[-2]["hash"]
    assert deal["hands"] == [
        [h.name(c) for c in hand] for hand in h.dealt(deal["seed"])
    ]
    assert "waiting on north, east, south, west" in t.run("show").stdout


def test_the_passes_move_three_cards_to_the_left(t):
    t.run("new")
    before = t.game().hands
    for s in range(3):
        assert "every pass is in" not in t.run("pass", h.SEATS[s], *(h.name(c) for c in before[s][:3])).stdout  # fmt: skip
    assert "the 2C leads" in t.run("pass", "west", *(h.name(c) for c in before[3][:3])).stdout  # fmt: skip
    after = t.game().hands
    for s in range(4):
        assert set(before[s][:3]) <= set(after[(s + 1) % 4])
        assert not set(before[s][:3]) & set(after[s])
    assert t.game().phase == "play"


def test_a_pass_that_isnt_three_of_the_seats_own_is_refused_and_writes_nothing(t):
    t.run("new")
    g = t.game()
    mine = [h.name(c) for c in g.hands[0][:3]]
    theirs = h.name(g.hands[1][0])
    before = t.raw()
    for argv in (("pass", "north", mine[0], mine[0], mine[1]), ("pass", "north", mine[0], mine[1], theirs), ("pass", "nobody", *mine)):  # fmt: skip
        assert t.run(*argv).returncode == 2
    assert t.raw() == before
    assert t.run("play", "2C").returncode == 2


def test_a_card_out_of_turn_or_against_the_rules_is_refused(t):
    t.run("new")
    t.pass_all()
    g = t.game()
    s = g.to_play()
    other = next(c for c in g.hands[s] if c != h.TWO_CLUBS)
    got = t.run("play", h.name(other))
    assert got.returncode == 2 and "may play 2C" in got.stderr
    assert "isn't a card" in t.run("play", "ZZ").stderr


def test_a_hand_played_out_is_scored_and_the_next_dealt(t):
    t.run("new")
    t.play_hand()
    g = t.game()
    assert g.phase == "deal" and sum(g.scores) in (26, 78)
    assert t.rows()[-1]["scores"] == g.scores
    assert t.run("play", "2C").returncode == 2
    got = t.run("deal")
    assert got.returncode == 0 and "pass right" in got.stdout
    assert t.run("deal").returncode == 2  # this hand isn't played out
    assert t.run("check").returncode == 0


def test_a_whole_game_played_to_100_holds(t):
    t.run("new")
    for _ in range(60):
        t.play_hand()
        if t.game().over:
            break
        assert t.run("deal").returncode == 0
    g = t.game()
    assert g.over and max(g.scores) >= 100
    assert "won" in t.run("show").stdout or "tied" in t.run("show").stdout
    assert t.run("check").returncode == 0
    assert "is over" in t.run("deal").stderr
    assert t.run("new").returncode == 0


def test_a_fourth_hand_holds_its_cards(t):
    t.run("new")
    for _ in range(3):
        t.play_hand()
        t.run("deal")
    assert t.rows()[-1]["way"] == "held" and t.game().phase == "play"


def test_nothing_is_played_before_a_game_is_opened(t):
    for argv in (
        ("play", "2C"),
        ("deal",),
        ("show",),
        ("pass", "north", "2C", "3C", "4C"),
    ):
        assert "no game is open" in t.run(*argv).stderr
    assert "0 games" in t.run("check").stdout


def test_new_waits_for_the_open_game_to_end(t):
    t.run("new")
    assert "isn't over" in t.run("new").stderr


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_deal_its_seed_doesnt_give(t):
    t.run("new")
    t.play_hand()
    seed = t.rows()[-1]["hash"]
    hands = [[h.name(c) for c in hand] for hand in h.dealt("stacked")]
    t.forge(h.DEAL, game=t.game_n(), hand=1, seed=seed, generator=h.GENERATOR, way="right", hands=hands)  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and "aren't what its seed deals" in got.stderr
    assert "don't hold" in t.run("show").stderr


def test_check_finds_a_deal_seeded_by_another_row(t):
    t.run("new")
    t.play_hand()
    seed = t.rows()[0]["hash"]
    hands = [[h.name(c) for c in hand] for hand in h.dealt(seed)]
    t.forge(h.DEAL, game=t.game_n(), hand=1, seed=seed, generator=h.GENERATOR, way="right", hands=hands)  # fmt: skip
    assert "isn't the hash of the row before it" in t.run("check").stderr


def test_check_finds_a_card_played_out_of_turn(t):
    t.run("new")
    t.pass_all()
    g = t.game()
    wrong = (g.to_play() + 1) % 4
    t.forge(h.PLAY, game=t.game_n(), hand=0, seat=h.SEATS[wrong], card=h.name(g.hands[wrong][0]))  # fmt: skip
    assert f"it is {h.SEATS[g.to_play()]}'s turn" in t.run("check").stderr


def test_check_finds_a_pass_of_cards_not_held(t):
    t.run("new")
    g = t.game()
    theirs = [h.name(c) for c in g.hands[1][:3]]
    t.forge(h.PASS, game=t.game_n(), hand=0, seat="north", cards=theirs)
    assert "passes three cards of its own" in t.run("check").stderr


def test_check_finds_scores_the_tricks_dont_give(t):
    t.run("new")
    t.play_hand()
    rows = t.rows()
    assert rows[-1]["kind"] == h.PLAY and h.check(rows) == (1, None)
    rows[-1] = {**rows[-1], "scores": [0, 0, 0, 0]}
    held, why = h.check(rows)
    assert held == 0 and "scores aren't what the tricks give" in why


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(h.PLAY, game=0, hand=0, seat="north", card="2C")
    assert "isn't a game opened before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("play",), ("pass", "north", "2C"), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "hearts.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
