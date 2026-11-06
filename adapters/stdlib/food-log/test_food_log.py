"""food-log: lines that name a meal or say you ate, under their day, each
with its meal and where it is; a spec for log-kit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "food_log.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-06T00:00:00Z"]
DIARY = (
    "2026-03-02\nBreakfast: porridge and honey.\nLunch was leek soup at Ana's.\n"
    "Walked the dog.\n\n2026-03-03\nSupper: the rest of the soup.\n"
    "Ate an apple on the bus.\nKieran ate two dinners.\nAteliers open.\n"
)


def box(tmp_path: Path, text: str) -> Path:
    (tmp_path / "pile" / "diary").mkdir(parents=True)
    (tmp_path / "pile" / "diary" / "march.md").write_text(text)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile",
                    str(tmp_path / "pile"), "--key", str(tmp_path / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def test_each_meal_line_is_under_its_day_with_its_meal(tmp_path):
    got = run("--box", box(tmp_path, DIARY))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "2026-03-02",
        "  breakfast  diary/march.md:2  Breakfast: porridge and honey.",
        "  lunch      diary/march.md:3  Lunch was leek soup at Ana's.",
        "2026-03-03",
        "  dinner     diary/march.md:7  Supper: the rest of the soup.",
        "             diary/march.md:8  Ate an apple on the bus.",
        "  dinner     diary/march.md:9  Kieran ate two dinners.",
        "2 days, 5 lines",
    ]


def test_by_month_and_nothing_found(tmp_path):
    got = run("--box", box(tmp_path, DIARY), "--by", "month")
    assert got.stdout.splitlines()[0] == "2026-03" and got.stdout.endswith(
        "1 month, 5 lines\n"
    )
    got = run("--box", box(tmp_path / "b", "2026-03-02\nWalked the dog.\n"))
    assert (
        got.returncode == 42
        and got.stdout == "No line of your folder says what you ate.\n"
    )


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    b = box(tmp_path, DIARY)
    for argv in (
        [],
        ["--box", b, "--by", "year"],
        ["--box", b, "--words", "x"],
        ["--box", b, "x"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "food_log.py" in got.stderr, argv
