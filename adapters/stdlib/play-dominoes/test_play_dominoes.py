"""play-dominoes: All Fives' counting and its spinner, every deal its seed's
own, the hand's ending and the game's, and check finding a forged row.
Hands are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("dominoes", HERE / "play_dominoes.py")
dom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dom)
kernel = dom.kernel
NOW = ["--now", "2026-11-26T09:00:00Z"]


def ts(text: str) -> list:
    return [dom.tile_of(t) for t in text.split()]


def game(
    north: str, south: str, boneyard: str = "", lead: str | None = None
) -> dom.Game:
    """A hand in play, north to move, with these tiles."""
    g = dom.Game()
    g.hands, g.boneyard, g.layout = [ts(north), ts(south)], ts(boneyard), dom.Layout()
    g.ended, g.turn = False, 0
    g.must_lead = None if lead is None else dom.tile_of(lead)
    return g


def laid(*moves) -> dom.Layout:
    L = dom.Layout()
    for tile, arm in moves:
        L.place(dom.tile_of(tile), arm)
    return L


class Table:
    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box = tmp / "box"
        subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(self.box), *NOW, "--pile", str(pile), "--key", str(tmp / "k")],
                       capture_output=True, text=True, check=True)  # fmt: skip

    def run(self, *argv):
        return subprocess.run([sys.executable, str(HERE / "play_dominoes.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True, check=False)  # fmt: skip

    def rows(self):
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self):
        return (self.box / "record.jsonl").read_bytes()

    def game(self):
        rows = self.rows()
        return dom.replay(rows, dom.games(rows)[-1])

    def game_n(self):
        return [r for r in self.rows() if r["kind"] == dom.OPEN][-1]["n"]

    def k_verify(self):
        return subprocess.run([sys.executable, str(KERNEL), "verify", "--box", str(self.box), *NOW],
                              capture_output=True, text=True, check=False).returncode == 0  # fmt: skip

    def forge(self, kind, **fields):
        kernel.append(self.box, NOW[1], kind, who=dom.WHO, **fields)

    def play_out(self):
        for _ in range(2000):
            if self.game().over:
                return
            got = self.run("auto")
            assert got.returncode == 0, got.stderr
        raise AssertionError("the game didn't end")


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the tiles ────────────────────────────────────────────────────────────────
def test_a_double_six_set_is_twenty_eight_tiles_each_once():
    every = dom.tiles()
    assert len(every) == 28 == len(set(every)) and (6, 6) in every and (0, 0) in every
    assert all(a >= b for a, b in every)


@pytest.mark.parametrize("text", ["6|5", "5|6", "6-5", "65", "6 5", "5/6"])
def test_a_tile_is_written_either_way_round(text):
    assert dom.tile_of(text) == (6, 5)


@pytest.mark.parametrize("text", ["7|1", "6", "", "a|b", "6|5|4", None])
def test_what_isnt_a_tile_is_refused(text):
    with pytest.raises(ValueError, match="isn't a tile"):
        dom.tile_of(text)


@pytest.mark.parametrize(
    "n,want", [(0, 0), (2, 0), (3, 5), (7, 5), (8, 10), (12, 10), (13, 15)]
)
def test_pips_go_to_the_nearest_five(n, want):
    assert dom.to_five(n) == want


def test_a_seed_deals_the_same_every_time_and_the_whole_set():
    a = dom.dealt("seed")
    assert a == dom.dealt("seed") and a != dom.dealt("other")
    every = [x for h in a["hands"] for x in h] + a["boneyard"]
    assert sorted(every) == sorted(dom.tiles()) and [len(h) for h in a["hands"]] == [
        9,
        9,
    ]
    assert len(a["boneyard"]) == 10


def test_the_stream_is_sha256_stream_v1():
    """sha256 over the seed and an 8-byte big-endian counter, first 4 bytes."""
    import hashlib

    s = dom.Stream(b"tip")
    want = [
        int.from_bytes(
            hashlib.sha256(b"tip" + n.to_bytes(8, "big")).digest()[:4], "big"
        )
        for n in range(3)
    ]
    assert [s.u32() for _ in range(3)] == want


# ── who leads ────────────────────────────────────────────────────────────────
def test_the_highest_double_leads_the_first_hand():
    assert dom.lead_of([ts("6|5 3|3"), ts("6|6 1|1")], None) == (1, (6, 6))
    assert dom.lead_of([ts("5|5 0|0"), ts("6|5 4|4")], None) == (0, (5, 5))


def test_with_no_double_the_heaviest_tile_leads():
    assert dom.lead_of([ts("6|4 2|1"), ts("6|5 1|0")], None) == (1, (6, 5))


def test_the_seat_that_went_out_leads_any_tile():
    assert dom.lead_of([ts("6|6"), ts("1|0")], 1) == (1, None)


def test_the_lead_a_hand_names_is_the_only_tile_it_takes():
    g = game("6|6 5|5", "6|1", lead="6|6")
    with pytest.raises(ValueError, match=r"6\|6 leads"):
        g.play(0, (5, 5), None)
    assert g.play(0, (6, 6), None) == ("lead", 0)
    assert g.layout.spinner == "lead" and g.turn == 1


# ── the spinner and the count ────────────────────────────────────────────────
def test_a_double_led_is_the_spinner_and_counts_once_alone():
    assert laid(("5|5", "lead")).count() == 10
    assert laid(("6|6", "lead")).count() == 12


def test_a_tile_led_counts_both_halves():
    assert laid(("5|0", "lead")).count() == 5
    assert laid(("6|4", "lead")).count() == 10


def test_the_spinner_counts_while_a_side_of_it_is_open():
    L = laid(("6|6", "lead"), ("6|3", "right"))
    assert L.count() == 15  # the spinner's 12 and the 3
    L.place((6, 1), "left")
    assert L.count() == 4  # both sides played: only their ends


def test_up_and_down_count_only_once_played_on():
    L = laid(("6|6", "lead"), ("6|3", "right"), ("6|1", "left"))
    assert L.count() == 4
    L.place((6, 5), "up")
    assert L.count() == 9
    L.place((6, 0), "down")
    assert L.count() == 9


def test_up_off_the_spinner_before_its_sides_counts_beside_it():
    assert laid(("6|6", "lead"), ("6|3", "up")).count() == 15


def test_a_double_at_an_end_counts_both_halves():
    L = laid(("6|6", "lead"), ("6|3", "right"), ("6|1", "left"), ("3|3", "right"))
    assert L.count() == 7  # the 1 and the 3|3's 6


def test_only_the_first_double_spins():
    L = laid(("6|6", "lead"), ("6|3", "right"), ("3|3", "right"))
    assert L.spinner == "lead" and L.open_arms() == list(dom.ARMS)
    assert L.end("right") == 3 and L.fits((3, 1)) == ["right"]


def test_a_layout_without_a_double_has_two_ends():
    L = laid(("6|4", "lead"))
    assert L.spinner is None and L.open_arms() == ["left", "right"]
    assert L.fits((6, 6)) == ["left"] and L.fits((5, 1)) == []


def test_the_first_double_played_later_spins_where_it_lies():
    L = laid(("6|4", "lead"), ("4|4", "right"))
    assert L.spinner == ("right", 0) and L.open_arms() == list(dom.ARMS)
    assert L.count() == 14  # the 6 and the 4|4's 8
    assert [L.end(a) for a in dom.ARMS] == [6, 4, 4, 4]
    L.place((4, 1), "up")
    assert L.count() == 15 and L.end("up") == 1
    L.place((4, 0), "right")
    assert L.count() == 7  # past it on the line: the 6, the 0 and the 1


def test_a_tile_goes_on_with_its_matching_half_inward():
    L = laid(("6|6", "lead"), ("3|6", "right"), ("3|1", "right"), ("5|6", "left"))
    assert L.arms["right"] == [(6, 3), (3, 1)] and L.arms["left"] == [(6, 5)]
    assert dom.arm_line(L, "right") == "[6|3] [3|1]"


# ── a turn ───────────────────────────────────────────────────────────────────
def test_a_multiple_of_five_scores_itself():
    g = game("6|6 6|3 1|0", "6|0 2|2")
    g.play(0, (6, 6), None)
    g.turn = 0
    assert g.play(0, (6, 3), "right") == ("right", 15) and g.scores == [15, 0]


def test_a_count_that_isnt_a_five_scores_nothing():
    g = game("6|6 6|2 1|0", "5|0 2|2")
    g.play(0, (6, 6), None)
    g.turn = 0
    assert g.play(0, (6, 2), "right") == ("right", 0) and g.scores == [0, 0]


def test_a_tile_that_fits_more_than_one_arm_needs_its_arm():
    g = game("6|6 6|3 1|0", "5|0 2|2")
    g.play(0, (6, 6), None)
    g.turn = 0
    with pytest.raises(ValueError, match="say which"):
        g.play(0, (6, 3), None)
    with pytest.raises(ValueError, match="doesn't fit an open end"):
        g.play(0, (1, 0), "left")


def test_a_tile_that_fits_one_arm_goes_there_unasked():
    g = game("6|4 4|1 2|2", "5|0 3|3")
    g.play(0, (6, 4), None)
    g.turn = 0
    assert g.play(0, (4, 1), None)[0] == "right"


def test_a_tile_on_the_wrong_arm_is_refused():
    g = game("6|4 4|1 2|2", "5|0 3|3")
    g.play(0, (6, 4), None)
    g.turn = 0
    with pytest.raises(ValueError, match="doesn't fit the left end"):
        g.play(0, (4, 1), "left")
    with pytest.raises(ValueError, match="doesn't fit the up end"):
        g.play(0, (4, 1), "up")


def test_a_tile_not_held_or_out_of_turn_is_refused():
    g = game("6|6", "5|5")
    with pytest.raises(ValueError, match="doesn't hold"):
        g.play(0, (5, 5), None)
    with pytest.raises(ValueError, match="north's turn"):
        g.play(1, (5, 5), None)


def test_a_seat_draws_only_with_nothing_to_play():
    g = game("6|6 1|0", "5|5 2|2", boneyard="6|1 6|2")
    g.play(0, (6, 6), None)
    with pytest.raises(ValueError, match="draws first"):
        g.pass_(1)
    assert g.draw(1) == (6, 1) and g.turn == 1
    with pytest.raises(ValueError, match="can play, so doesn't draw"):
        g.draw(1)


def test_a_seat_passes_only_with_nothing_to_play_and_no_boneyard():
    g = game("6|6 6|1 1|0", "5|5 2|2")
    g.play(0, (6, 6), None)
    with pytest.raises(ValueError, match="boneyard is empty"):
        g.draw(1)
    g.pass_(1)
    assert g.turn == 0 and not g.ended
    with pytest.raises(ValueError, match="can play"):
        g.pass_(0)


# ── the end of a hand, and of the game ───────────────────────────────────────
def test_going_out_scores_the_others_pips_to_the_nearest_five():
    g = game("6|6 6|1", "5|5 2|1", lead="6|6")  # south holds 13 pips
    g.play(0, (6, 6), None)
    g.turn = 0
    g.play(0, (6, 1), "right")  # 12 + 1: nothing
    assert (
        g.ended
        and g.scores == [15, 0]
        and g.last_hand == {"how": "out", "seat": "north", "points": 15}
    )
    assert g.result() == "hand over" and g.last_out == 0


def test_a_blocked_hand_goes_to_fewer_pips():
    g = game("6|6 5|5", "4|4 0|0 1|0")
    g.play(0, (6, 6), None)
    assert g.ended and g.last_hand == {"how": "blocked", "seat": "south", "points": 10}
    assert g.scores == [0, 10] and g.last_out is None


def test_a_blocked_hand_with_pips_tied_scores_nobody():
    g = game("6|6 4|0", "3|1")
    g.play(0, (6, 6), None)
    assert g.ended and g.last_hand == {"how": "blocked", "seat": None, "points": 0}
    assert g.scores == [0, 0]


def test_the_game_is_over_the_moment_a_seat_holds_250():
    g = game("6|6 6|3 1|0", "5|0 2|2")
    g.scores = [240, 0]
    g.play(0, (6, 6), None)
    g.turn = 0
    g.play(0, (6, 3), "right")
    assert g.over and g.result() == "north won" and g.last_hand["how"] == "target"
    with pytest.raises(ValueError, match="is over"):
        g.play(1, (2, 2), None)
    with pytest.raises(ValueError, match="is over"):
        g.deal("x")


def test_a_hand_is_dealt_only_once_the_one_before_is_over():
    g = dom.Game()
    g.deal("a")
    with pytest.raises(ValueError, match="isn't over"):
        g.deal("b")


# ── the seat played by a fixed rule ──────────────────────────────────────────
def test_auto_plays_what_scores_most_then_the_heaviest_tile():
    g = game("6|6", "6|3 6|2 6|5")
    g.play(0, (6, 6), None)
    assert dom.chosen(g, 1) == ((6, 3), "left")  # 15 beats the heavier 6|5's 17
    g2 = game("6|6", "6|1 6|2")
    g2.play(0, (6, 6), None)
    assert dom.chosen(g2, 1) == ((6, 2), "left")


def test_auto_leads_the_tile_the_hand_names():
    g = game("6|6 5|5", "1|0", lead="6|6")
    assert dom.chosen(g, 0) == ((6, 6), "lead")


# ── the record ───────────────────────────────────────────────────────────────
def test_new_deals_from_the_record_tip(t):
    got = t.run("new")
    assert got.returncode == 0 and "hand 1 dealt" in got.stdout
    rows = t.rows()
    d = rows[-1]
    want = dom.dealt(d["seed"])
    assert (
        rows[-2]["kind"] == dom.OPEN
        and d["kind"] == dom.DEAL
        and d["seed"] == rows[-2]["hash"]
    )
    assert (
        d["hands"] == [[dom.name(x) for x in h] for h in want["hands"]]
        and len(d["boneyard"]) == 10
    )
    assert (d["leader"], dom.tile_of(d["lead"])) == (lambda s, x: (dom.SEATS[s], x))(
        *dom.lead_of(want["hands"], None)
    )
    assert "boneyard 10" in t.run("show").stdout


def test_show_with_a_seat_shows_only_that_seats_tiles(t):
    t.run("new")
    g = t.game()
    north = " ".join(dom.name(x) for x in sorted(g.hands[0], reverse=True))
    south = " ".join(dom.name(x) for x in sorted(g.hands[1], reverse=True))
    got = t.run("show", "--seat", "north").stdout
    assert north in got and south not in got and "south  9 tiles" in got
    whole = t.run("show").stdout
    assert north in whole and south in whole
    assert "isn't a seat" in t.run("show", "--seat", "east").stderr


def test_a_whole_game_played_out_holds(t):
    t.run("new")
    t.play_out()
    g = t.game()
    assert max(g.scores) >= dom.TARGET and g.result() == f"{dom.SEATS[g.winner]} won"
    assert t.rows()[-1]["result"] == g.result() and g.hand_no > 1
    assert t.run("check").returncode == 0 and t.k_verify()
    assert "is over" in t.run("auto").stderr
    assert t.run("new").returncode == 0


def test_a_move_by_hand_is_the_same_row_auto_would_write(t):
    t.run("new")
    g = t.game()
    tile, arm = dom.chosen(g, g.turn)
    got = t.run("play", dom.name(tile))
    assert got.returncode == 0 and "leads" in got.stdout
    r = t.rows()[-1]
    assert (r["kind"], r["tile"], r["arm"], r["seat"]) == (
        dom.PLAY,
        dom.name(tile),
        arm,
        dom.SEATS[g.turn],
    )


def test_moves_the_rules_dont_allow_are_refused_and_write_nothing(t):
    t.run("new")
    g = t.game()
    held = set(g.hands[g.turn])
    wrong = next(x for x in dom.tiles() if x not in held)
    other = next(x for x in held if x != g.must_lead) if g.must_lead else None
    before = t.raw()
    argv = [
        ("play", dom.name(wrong)),
        ("play", "ZZ"),
        ("play", dom.name(sorted(held)[0]), "sideways"),
        ("pass",),
        ("draw",),
    ]
    if other:
        argv.append(("play", dom.name(other)))
    for a in argv:
        assert t.run(*a).returncode == 2, a
    assert t.raw() == before


def test_new_waits_for_the_game_to_end(t):
    t.run("new")
    assert "isn't over" in t.run("new").stderr


def test_nothing_is_played_before_a_game_is_open(t):
    for argv in (("play", "6|6"), ("draw",), ("pass",), ("auto",), ("show",)):
        assert "no game is open" in t.run(*argv).stderr
    assert "0 games" in t.run("check").stdout


# ── check ────────────────────────────────────────────────────────────────────
def test_check_finds_a_deal_its_seed_doesnt_give(t):
    t.forge(dom.OPEN, seats=list(dom.SEATS), each=dom.HAND, target=dom.TARGET)
    g = dom.Game()
    seed = t.rows()[-1]["hash"]
    g.deal("stacked")
    fields = {**dom.deal_fields("stacked", g), "seed": seed}
    t.forge(dom.DEAL, game=t.game_n(), **fields)
    got = t.run("check")
    assert got.returncode == 2 and "aren't what its seed deals" in got.stderr
    assert "don't hold" in t.run("show").stderr


def test_check_finds_a_deal_not_seeded_by_the_row_before_it(t):
    t.forge(dom.OPEN, seats=list(dom.SEATS), each=dom.HAND, target=dom.TARGET)
    g = dom.Game()
    g.deal("chosen")
    t.forge(dom.DEAL, game=t.game_n(), **dom.deal_fields("chosen", g))
    assert "isn't the hash of the row before it" in t.run("check").stderr


def test_check_finds_a_draw_that_isnt_the_next_in_the_boneyard(t):
    t.run("new")
    for _ in range(2000):
        g = t.game()
        if not g.ended and not g.can_play(g.turn) and len(g.boneyard) > 1:
            break
        assert t.run("auto").returncode == 0
    assert not g.can_play(g.turn) and len(g.boneyard) > 1, "no hand came to a draw"
    t.forge(
        dom.DRAW, game=t.game_n(), seat=dom.SEATS[g.turn], tile=dom.name(g.boneyard[1])
    )
    assert "isn't the next in the boneyard" in t.run("check").stderr


def test_check_finds_a_tile_played_out_of_turn(t):
    t.run("new")
    g = t.game()
    t.forge(dom.PLAY, game=t.game_n(), seat=dom.SEATS[1 - g.turn], tile=dom.name(g.hands[1 - g.turn][0]),
            arm="lead", scored=0, scores=[0, 0], result="on")  # fmt: skip
    assert f"it is {dom.SEATS[g.turn]}'s turn" in t.run("check").stderr


def test_check_finds_a_score_the_tiles_dont_give(t):
    t.run("new")
    assert t.run("auto").returncode == 0
    rows = t.rows()
    assert dom.check(rows) == (1, None)
    r = rows[-1]
    rows[-1] = {**r, "scored": r["scored"] + 5}
    held, why = dom.check(rows)
    assert held == 0 and f"it scored {r['scored']}" in why
    rows[-1] = {**r, "scores": [99, 99]}
    assert "the tiles say" in dom.check(rows)[1]


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(
        dom.PLAY,
        game=0,
        seat="north",
        tile="6|6",
        arm="lead",
        scored=0,
        scores=[0, 0],
        result="on",
    )
    assert "isn't a game opened before it" in t.run("check").stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in (
        (),
        ("play",),
        ("play", "6|6", "up", "x"),
        ("fly",),
        ("new", "x"),
        ("auto", "--seat", "north"),
    ):
        assert t.run(*argv).returncode == 2, argv
    got = subprocess.run([sys.executable, str(HERE / "play_dominoes.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
