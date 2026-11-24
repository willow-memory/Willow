"""play-fight5e's board: a fight drawn from its rows alone, with no dice
(Die-Namic's board tests, from tests/test_safety_carry.py at 514823c, on
play-fight5e's row kinds): every kind of blow moves the board as it says,
a stun lasts until the turn it loses and a blinding its round, the fallen are
skipped, a bar is never empty while standing, the board is of the fight it
names."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402


def blows(*states) -> list[dict]:
    rs = [{"n": 0, "kind": board.OPEN, "encounter": "bruiser", "desc": "a test"}]
    rs += [{"n": i + 1, "kind": board.BLOW, "fight": 0, "state": s} for i, s in enumerate(states)]  # fmt: skip
    return rs


ORDER = {"kind": "initiative", "order": ["Sena Koll", "Engine-Blooded Bruiser", "Tide-touched Scout", "Tide-Touched Scout", "Warforged"]}  # fmt: skip


def test_the_board_follows_every_kind_of_blow():
    rs = blows(ORDER, {"kind": "round", "n": 1},
               {"kind": "attack", "by": "Sena Koll", "vs": "Engine-Blooded Bruiser", "hit": True, "target_hp": 40},
               {"kind": "attack", "by": "Engine-Blooded Bruiser", "vs": "Sena Koll", "hit": False, "target_hp": 3},
               {"kind": "special", "by": "Tide-Touched Scout", "name": "Riptide"},
               {"kind": "save", "who": "Warforged", "vs": "Riptide", "saved": False, "dmg": 6, "hp": 25},
               {"kind": "save", "who": "Sena Koll", "vs": "Glare", "saved": False, "effect": "blind"},
               {"kind": "save", "who": "Tide-touched Scout", "vs": "Slam", "saved": False, "effect": "stun"},
               {"kind": "overheat", "who": "Engine-Blooded Bruiser", "dmg": 5, "hp": 35})  # fmt: skip
    s = board.state(rs, 0)
    f = {x["name"]: x for x in s["fighters"]}
    assert (
        f["Engine-Blooded Bruiser"]["hp"] == 35 and f["Sena Koll"]["hp"] == 20
    )  # a miss moves nothing
    assert f["Warforged"]["hp"] == 25 and f["Sena Koll"]["blinded"] and f["Tide-touched Scout"]["stunned"]  # fmt: skip
    assert (
        s["round"] == 1 and s["outcome"] is None and s["next"] == "Warforged"
    )  # after the scout's special
    text = board.draw(s)
    assert "Sena Koll" in text and "blinded" in text and "stunned" in text and "▶ Warforged" in text  # fmt: skip


def test_a_stun_ends_with_the_turn_it_loses_and_a_blinding_with_its_round():
    rs = blows(ORDER, {"kind": "round", "n": 1},
               {"kind": "save", "who": "Sena Koll", "vs": "Glare", "saved": False, "effect": "blind"},
               {"kind": "save", "who": "Warforged", "vs": "Slam", "saved": False, "effect": "stun"},
               {"kind": "round", "n": 2},
               {"kind": "stunned_skip", "who": "Warforged"})  # fmt: skip
    f = {x["name"]: x for x in board.state(rs, 0)["fighters"]}
    assert not f["Sena Koll"]["blinded"] and not f["Warforged"]["stunned"]
    g = {x["name"]: x for x in board.state(rs, 0, 1)["fighters"]}  # as round 1 ended
    assert g["Sena Koll"]["blinded"] and g["Warforged"]["stunned"]


def test_the_fallen_are_down_and_skipped_for_the_next_turn():
    rs = blows(ORDER, {"kind": "round", "n": 1},
               {"kind": "attack", "by": "Sena Koll", "vs": "Engine-Blooded Bruiser", "hit": True, "target_hp": 0},
               {"kind": "down", "who": "Engine-Blooded Bruiser"})  # fmt: skip
    s = board.state(rs, 0)
    assert s["next"] == "Tide-touched Scout"  # the Bruiser, next in order, is down
    assert "✖ down" in board.draw(s) and "Engine-Blooded Bruiser ✖" in board.draw(s)


def test_a_bar_is_never_empty_while_standing_and_full_at_full():
    assert board.bar(1, 75) == "█" + "░" * 9
    assert board.bar(0, 75) == "░" * 10 and board.bar(31, 31) == "█" * 10
    assert board.bar(10, 20) == "█" * 5 + "░" * 5


def test_the_board_is_of_the_fight_it_names_when_the_record_holds_two():
    first = blows(ORDER, {"kind": "round", "n": 1}, {"kind": "attack", "by": "Sena Koll", "vs": "Engine-Blooded Bruiser", "hit": True, "target_hp": 9})  # fmt: skip
    second = [{"n": 10, "kind": board.OPEN, "encounter": "warden", "desc": "the warden"},
              {"n": 11, "kind": board.BLOW, "fight": 10, "state": {"kind": "initiative", "order": ["Warforged", "Mind-Forge Warden"]}},
              {"n": 12, "kind": board.BLOW, "fight": 10, "state": {"kind": "round", "n": 1}},
              {"n": 13, "kind": board.BLOW, "fight": 10, "state": {"kind": "attack", "by": "Warforged", "vs": "Mind-Forge Warden", "hit": True, "target_hp": 60}}]  # fmt: skip
    s = board.state(first + second, 10)
    assert s["desc"] == "the warden" and {f["name"]: f["hp"] for f in s["fighters"]}["Mind-Forge Warden"] == 60  # fmt: skip
    assert "Engine-Blooded Bruiser" not in {f["name"] for f in s["fighters"]}
    assert {f["name"]: f["hp"] for f in board.state(first + second, 0)["fighters"]}["Engine-Blooded Bruiser"] == 9  # fmt: skip


def test_a_fight_before_its_first_round_is_round_nought():
    s = board.state(blows(ORDER), 0)
    assert s["round"] == 0 and s["next"] is None


def test_a_hit_leaves_the_hit_points_it_says_and_a_fall_is_none():
    rs = blows(ORDER, {"kind": "round", "n": 1},
               {"kind": "attack", "by": "Sena Koll", "vs": "Tide-Touched Scout", "hit": True, "target_hp": 11},
               {"kind": "attack", "by": "Sena Koll", "vs": "Warforged", "hit": True, "target_hp": 4},
               {"kind": "down", "who": "Warforged"})  # fmt: skip
    f = {x["name"]: x for x in board.state(rs, 0)["fighters"]}
    assert f["Tide-Touched Scout"]["hp"] == 11 and f["Warforged"]["hp"] == 0 and f["Warforged"]["down"]  # fmt: skip


def test_a_bar_with_no_hit_points_to_have_is_empty():
    assert board.bar(0, 0) == "░" * 10
