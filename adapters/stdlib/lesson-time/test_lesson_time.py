"""lesson-time: a plan's timed parts against the time it says it takes;
ranges held as ranges, optional parts left out, a plan with no stated time
held only to --period."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("lesson_time", HERE / "lesson_time.py")
lt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lt)
NOW = ["--now", "2026-10-29T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def ask(b: Path, *extra: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "lesson_time.py"), "--box", str(b), *extra)


SHORT = """# The Ledger

**Suggested time:** 50 minutes

### Part 1 — Opening (8 min)
Talk.

### Part 2 — Journey (12 min)
Map.

### Part 3 — Role-play (20 min)
Play. Then: 5 minutes of whole-class debrief.

### Part 4 — Ledger (5 min)
Write.
"""

EVEN = """# The Oracle

**Time:** 50 min

### Part 1 — Hook (10 min)
### Part 2 — Mechanic (15 min)
### Part 3 — Cards (15 min)
### Part 4 — Hard part (7 min)
### Part 5 — Exit (3 min)

## Optional Device Extension (15 min, additive)
"""


def test_a_plan_whose_parts_fall_short_is_off(tmp_path):
    got = ask(box(tmp_path, {"ledger.md": SHORT, "oracle.md": EVEN}))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("off  45 of 50 min  ledger.md")
    assert "8+12+20+5  (said on line 3)" in lines[0]
    assert lines[-1] == "2 plans read, 1 off"


def test_minutes_inside_a_part_are_not_counted(tmp_path):
    got = ask(box(tmp_path, {"ledger.md": SHORT}))
    assert "45 of 50" in got.stdout and "50 of 50" not in got.stdout


def test_an_optional_part_is_left_out_of_the_sum(tmp_path):
    got = ask(box(tmp_path, {"oracle.md": EVEN}))
    assert got.stdout.splitlines()[0].startswith("ok   50 of 50 min  oracle.md")
    assert got.returncode == 42


def test_ranges_are_held_as_ranges(tmp_path):
    plan = (
        "**Time:** 45–55 minutes\n\n## Setup (5 min)\n\n"
        "## Sketches (15–20 min)\n\n## Discussion (15–20 min)\n\n## Close (2 min)\n"
    )
    got = ask(box(tmp_path, {"long.md": plan}))
    assert got.stdout.splitlines()[0].startswith("ok   37-47 of 45-55 min  long.md")
    assert "5+15-20+15-20+2" in got.stdout


def test_a_range_that_misses_entirely_is_off(tmp_path):
    plan = "**Duration:** 60 minutes\n\n## A (5–10 min)\n\n## B (20–25 min)\n"
    got = ask(box(tmp_path, {"p.md": plan}))
    assert got.stdout.startswith("off  25-35 of 60 min")


def test_no_stated_time_is_left_out_unless_a_period_is_given(tmp_path):
    plan = "## A (10 min)\n\n## B (30 min)\n"
    b = box(tmp_path, {"p.md": plan})
    assert ask(b).returncode == 42
    got = ask(b, "--period", "45")
    assert got.stdout.startswith("off  40 of 45 min  p.md")
    assert "(from --period)" in got.stdout


def test_one_timed_heading_is_not_a_plan(tmp_path):
    got = ask(
        box(tmp_path, {"essay.md": "**Time:** 5 minutes\n\n## A walk (20 min)\n"})
    )
    assert got.returncode == 42
    assert "No lesson plan" in got.stdout


def test_refusals(tmp_path):
    assert ask(tmp_path / "nobox").returncode == 2
    b = box(tmp_path, {"p.md": SHORT})
    assert ask(b, "--period", "lots").returncode == 2
    assert ask(b, "--period", "0").returncode == 2
    assert ask(b, "stray").returncode == 2
    assert run(str(HERE / "lesson_time.py")).returncode == 2


def test_read_plan_reads_the_first_stated_time():
    rows = list(
        enumerate(
            ["**Time:** 40 min", "**Time:** 90 min", "## A (20 min)", "## B (20 min)"],
            1,
        )
    )
    plan = lt.read_plan(rows)
    assert plan == {"parts": [(20, 20), (20, 20)], "said": (40, 40), "at": 1}
