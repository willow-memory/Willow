"""odds: exact fractions over every way the dice fall, summing to exactly 1;
at-least and bands; dice notation it can't read refused."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("odds", HERE / "odds.py")
od = importlib.util.module_from_spec(spec)
spec.loader.exec_module(od)


def test_2d6_is_the_triangle_and_sums_to_exactly_one():
    d = od.distribution("2d6")
    assert (
        d[2] == Fraction(1, 36) and d[7] == Fraction(1, 6) and d[12] == Fraction(1, 36)
    )
    assert sorted(d) == list(range(2, 13)) and sum(d.values()) == 1


def test_constants_signs_and_mixed_dice():
    d = od.distribution("1d20+3")
    assert min(d) == 4 and max(d) == 23 and set(d.values()) == {Fraction(1, 20)}
    assert od.distribution("1d4-1") == {
        0: Fraction(1, 4),
        1: Fraction(1, 4),
        2: Fraction(1, 4),
        3: Fraction(1, 4),
    }
    mixed = od.distribution("1d8+1d6")
    assert min(mixed) == 2 and max(mixed) == 14 and mixed[2] == Fraction(1, 48)
    assert od.distribution("d6") == od.distribution("1d6")
    assert min(od.distribution("2d6-1d4")) == -2


def test_at_least_and_the_2d6_games_bands():
    d = od.distribution("2d6")
    assert (
        od.at_least(d, 10) == Fraction(1, 6)
        and od.at_least(d, 2) == 1
        and od.at_least(d, 13) == 0
    )
    assert od.bands(d, [10, 7]) == [
        ("10+", Fraction(1, 6)),
        ("7-9", Fraction(5, 12)),
        ("6 or less", Fraction(5, 12)),
    ]
    assert od.bands(d, [7, 7, 8])[:2] == [
        ("8+", Fraction(5, 12)),
        ("7", Fraction(1, 6)),
    ]


@pytest.mark.parametrize(
    "bad", ["", "2x6", "d", "2d1", "101d6", "1d1001", "2d6 4", "3", "2d6+-1"]
)
def test_notation_it_cant_read_is_refused(bad):
    with pytest.raises(ValueError):
        od.distribution(bad)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "odds.py"), *argv], capture_output=True, text=True
    )


def test_the_command_line(tmp_path):
    got = run("2d6")
    assert (
        got.returncode == 0
        and "     7   1/6   " in got.stdout
        and "16.67%" in got.stdout
    )
    got = run("2d6", "--at-least", "10")
    assert got.stdout.splitlines()[1] == "  10 or more: 1/6  16.67%"
    got = run("2d6", "--bands", "10,7")
    assert "10+" in got.stdout and "7-9" in got.stdout and "6 or less" in got.stdout
    assert run("2d6 + 1").returncode == 0 and run(" 1d20 - 2 ").returncode == 0
    for argv in ([], ["2d6", "3d6"], ["--bands", "1"]):
        got = run(*argv)
        assert got.returncode == 2 and "odds.py" in got.stderr
    for argv in (["2x6"], ["2d6", "--at-least", "x"], ["2d6", "--bands", "a"]):
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("refused: ")
