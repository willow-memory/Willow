"""exhaustion: both SRD editions, kept apart, and what each does to a roll,
a speed and a hit point maximum; level 6 death, a long rest one level off;
anything else refused, never guessed; and the command line saying it."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "exhaustion.py"
spec = importlib.util.spec_from_file_location("exhaustion", SCRIPT)
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def test_5_2_takes_two_off_every_d20_and_five_feet_a_level():
    assert [ex.d20_modifier(n) for n in range(7)] == [0, -2, -4, -6, -8, -10, -12]
    assert [ex.speed_change(n, 30) for n in range(7)] == [30, 25, 20, 15, 10, 5, 0]
    assert ex.speed_change(6, 20) == 0  # never below 0


def test_5_1_gives_disadvantage_by_level_and_no_number():
    assert [ex.roll_mode("check", n, "5.1") for n in range(4)] == ["normal", "disadvantage", "disadvantage", "disadvantage"]  # fmt: skip
    assert [ex.roll_mode("attack", n, "5.1") for n in range(4)] == ["normal", "normal", "normal", "disadvantage"]  # fmt: skip
    assert [ex.roll_mode("save", n, "5.1") for n in range(4)] == ["normal", "normal", "normal", "disadvantage"]  # fmt: skip
    assert ex.d20_modifier(4, "5.1") == 0


def test_5_1_speed_is_halved_from_two_and_zero_from_five():
    assert [ex.speed_change(n, 30, "5.1") for n in range(7)] == [30, 30, 15, 15, 15, 0, 0]  # fmt: skip
    assert ex.speed_change(2, 25, "5.1") == 12  # rounded down


def test_5_1_halves_the_hit_point_maximum_from_four_and_5_2_does_not():
    assert [ex.hp_max(n, 21, "5.1") for n in range(7)] == [21, 21, 21, 21, 10, 10, 10]
    assert ex.hp_max(4, 1, "5.1") == 1  # at least 1
    assert ex.hp_max(6, 21) == 21  # 5.2, the default


def test_the_default_is_5_2_so_no_disadvantage_unless_5_1_is_asked_for():
    assert ex.DEFAULT == "5.2"
    assert ex.roll_mode("check", 5) == "normal"
    assert ex.roll_mode("check", 5, "5.2") == "normal"
    assert ex.roll_mode("check", 5, "5.1") == "disadvantage"


def test_level_six_is_death_in_both_editions_and_only_then():
    assert [ex.dead(n) for n in range(7)] == [False] * 6 + [True]


def test_said_in_the_tables_words_for_each_edition():
    assert ex.said(0) == ex.said(0, "5.1") == "not worn out"
    assert ex.said(1) == "worn out (1): every d20 roll -2, speed -5 feet"
    assert ex.said(2) == "worn out (2): every d20 roll -4, speed -10 feet"
    assert ex.said(1, "5.1") == "worn out (1): disadvantage on ability checks"
    assert ex.said(2, "5.1") == "worn out (2): disadvantage on ability checks, speed halved"  # fmt: skip
    assert ex.said(5, "5.1") == (
        "worn out (5): disadvantage on ability checks, speed halved, disadvantage on "
        "attacks and saves, hit point maximum halved, speed 0"
    )
    assert ex.said(6, "5.1") == ex.said(6) == "worn out to death"


@pytest.mark.parametrize("bad", [-1, 7, 2.0, "2", True, None])
def test_a_level_that_is_not_0_to_6_is_refused(bad):
    for f in (ex.d20_modifier, ex.dead, ex.after_long_rest, ex.said):
        with pytest.raises(ValueError, match="exhaustion level is 0 to 6"):
            f(bad)


@pytest.mark.parametrize("bad", [-1, 2.5, True, "30"])
def test_a_speed_that_is_not_feet_is_refused(bad):
    with pytest.raises(ValueError, match="a speed is a whole number"):
        ex.speed_change(1, bad)
    assert ex.speed_change(1, 0) == 0


@pytest.mark.parametrize("bad", [0, -3, 1.5, True])
def test_a_hit_point_maximum_below_one_is_refused(bad):
    with pytest.raises(ValueError, match="a hit point maximum is a whole number"):
        ex.hp_max(1, bad)


def test_an_unknown_edition_or_kind_is_refused_not_guessed():
    with pytest.raises(ValueError, match="edition is one of 5.1, 5.2"):
        ex.d20_modifier(1, "5.5")
    with pytest.raises(ValueError, match="edition is one of"):
        ex.speed_change(1, 30, "5e")
    with pytest.raises(ValueError, match="edition is one of"):
        ex.hp_max(4, 21, "")
    with pytest.raises(ValueError, match="a kind of roll is one of check, attack, save"):  # fmt: skip
        ex.roll_mode("skill", 1)


def test_a_long_rest_eases_one_level_and_never_below_zero():
    assert [ex.after_long_rest(n) for n in range(7)] == [0, 0, 1, 2, 3, 4, 5]


# ── the command line ────────────────────────────────────────────────────────


def test_the_command_line_says_each_effect_in_5_2_by_default():
    got = run("2", "--speed", "30", "--hp-max", "21")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "SRD 5.2, level 2",
        "worn out (2): every d20 roll -4, speed -10 feet",
        "d20 tests: -4",
        "checks: normal; attacks: normal; saves: normal",
        "speed: 30 feet, 20 worn out",
        "hit point maximum: 21, 21 worn out",
        "after a long rest: level 1",
    ]


def test_the_command_line_in_5_1_and_without_a_speed_or_maximum():
    got = run("4", "--edition", "5.1")
    assert got.returncode == 0, got.stderr
    assert (
        got.stdout.splitlines()
        == [
            "SRD 5.1, level 4",
            "worn out (4): disadvantage on ability checks, speed halved, disadvantage on attacks and saves, hit point maximum halved",  # fmt: skip
            "d20 tests: +0",
            "checks: disadvantage; attacks: disadvantage; saves: disadvantage",
            "after a long rest: level 3",
        ]
    )
    assert "hit point maximum: 21, 10 worn out" in run("4", "--edition", "5.1", "--hp-max", "21").stdout  # fmt: skip


@pytest.mark.parametrize(
    "argv, said",
    [
        (["7"], "exhaustion level is 0 to 6"),
        (["two"], "LEVEL is a whole number"),
        (["1", "--edition", "5e"], "edition is one of"),
        (["1", "--speed", "fast"], "--speed is a whole number"),
        (["1", "--hp-max", "0"], "a hit point maximum is a whole number"),
    ],
)
def test_the_command_line_refuses_with_why(argv, said):
    got = run(*argv)
    assert got.returncode == 2 and said in got.stderr and got.stdout == ""


@pytest.mark.parametrize("argv", [[], ["1", "2"], ["1", "--speed"]])
def test_a_command_line_it_has_not_is_refused_with_its_usage(argv):
    got = run(*argv)
    assert got.returncode == 2 and "exhaustion.py LEVEL" in got.stderr
