"""on-this-day: lines that carry today's month and day in an earlier year,
never a line a passage's other dates stand in for."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def test_earlier_years_newest_first_and_a_file_named_by_the_day(tmp_path):
    pile = tmp_path / "pile"
    (pile / "memos").mkdir(parents=True)
    (pile / "log.csv").write_text(
        "2023-08-05,spring order,110\n2023-10-23,check Ashby,110\n2025-10-23,weight 71.4\n"
        "2026-10-23,today is not an earlier year\n"
    )
    (pile / "memos" / "2022-10-23_0815.txt").write_text("Okay.\n\nA second line.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW)
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert [ln[:4] for ln in lines] == ["2025", "2023", "2022"]
    assert "spring order" not in got.stdout  # the passage's later date never stands in
    assert (
        "memos/2022-10-23_0815.txt:1" in got.stdout
        and "A second line" not in got.stdout
    )


def test_nothing_on_this_day(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("2024-01-01 new year\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    assert run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW).returncode == 42
