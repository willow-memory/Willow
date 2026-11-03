"""on-this-day: lines that carry today's month and day in an earlier year,
never a line a passage's other dates stand in for."""

from __future__ import annotations

import json
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
    assert lines == [
        "on-this-day: populated, 3 lines written on 10-23 in 3 earlier years",
        "## 2025",
        "  log.csv:3                    2025-10-23,weight 71.4",
        "## 2023",
        "  log.csv:2                    2023-10-23,check Ashby,110",
        "## 2022",
        "  memos/2022-10-23_0815.txt:1  Okay.",
    ]
    doc = json.loads(
        run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW, "--json").stdout
    )
    assert doc["state"] == "populated" and doc["said"] == (
        "3 lines written on 10-23 in 3 earlier years"
    )
    assert [g["name"] for g in doc["groups"]] == ["2025", "2023", "2022"]
    assert doc["groups"][2]["rows"] == [
        {"where": "memos/2022-10-23_0815.txt:1", "what": "Okay."}
    ]
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
    got = run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW)
    assert got.returncode == 0
    assert got.stdout == "on-this-day: empty, nothing dated 10-23 in an earlier year\n"


def test_nothing_says_which_day_and_a_long_line_is_cut_at_120(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("2024-01-01 new year\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW)
    assert got.stdout == "on-this-day: empty, nothing dated 10-23 in an earlier year\n"
    doc = json.loads(
        run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW, "--json").stdout
    )
    assert doc == {"addon": "on-this-day", "state": "empty",
                   "said": "nothing dated 10-23 in an earlier year", "groups": []}  # fmt: skip
    (pile / "a.md").write_text("2025-10-23 " + "x" * 200 + "\n")
    line = run(str(HERE / "on_this_day.py"), "--box", str(b), *NOW).stdout.splitlines()[
        2
    ]
    assert line.endswith("2025-10-23 " + "x" * 109)  # the line, 120 characters of it
