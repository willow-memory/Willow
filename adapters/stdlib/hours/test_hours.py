"""hours: work words with a length of time, added up for whom they name; a
time with no work word and a line no day reaches count for nothing."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("hours", HERE / "hours.py")
hr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hr)
NOW = ["--now", "2026-10-23T00:00:00Z"]


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


def test_a_line_says_its_times_and_they_add():
    assert hr.spent("worked 3 hours") == 3
    assert hr.spent("worked 2.5 h") == 2.5
    assert hr.spent("logged 1h30") == 1.5
    assert hr.spent("worked 45 min") == 0.75
    assert hr.spent("worked 2 hrs 15 min") == 2.25
    assert hr.spent("worked 1 hour and 30 minutes") == 1.5
    assert hr.spent("worked 2h and 3h") == 5
    assert hr.spent("worked all day") == 0
    assert hr.spent("worked at 9:30") == 0, "a clock time is no length of time"
    assert hr.spent("worked 5 hats") == 0, "h must stand alone"


def test_whom_it_is_for():
    assert hr.whom("worked 3 hours for Acme on the site") == "acme"
    assert hr.whom("volunteered 6h @ the Food Bank, Saturday") == "the food bank"
    assert hr.whom("shift with Ana Lopez, 4 hours") == "ana lopez"
    assert hr.whom("billed 2 hours at Dunmore Ltd.") == "dunmore ltd"
    assert hr.whom("worked 2 hours") == hr.NONE
    assert hr.whom("worked 2 hours for 3 clients") == hr.NONE
    assert hr.whom("worked for   Acme   Co from nine") == "acme co"


def test_a_work_word_and_a_day_are_needed():
    pile = [
        {"path": "log.md", "line": 1, "text": (
            "2026-03-01 worked 3 hours for Acme\n"
            "2026-03-01 slept 8 hours\n"
            "worked 2 hours for Acme\n"        # the day above
            "2026-03-02\n"
            "meeting 1h for Acme\n"
        )},
        {"path": "nodate.md", "line": 1, "text": "worked 9 hours for Acme\n"},
        {"path": "2026-04-01.md", "line": 1, "text": "shift 4 hours at the food bank\n"},
    ]  # fmt: skip
    got = hr.tally(pile)
    assert set(got) == {"acme", "the food bank"}
    assert got["acme"] == [6.0, ["20260301", "20260301", "20260302"]]
    assert got["the food bank"][0] == 4
    assert hr.tally(pile, since="20260302") == {
        "acme": [1.0, ["20260302"]],
        "the food bank": [4.0, ["20260401"]],
    }
    assert set(hr.tally(pile, until="20260301")) == {"acme"}
    assert hr.tally(pile, until="20260301")["acme"][0] == 5, "both ends are kept"
    assert hr.tally(pile, since="20260301", until="20260301")["acme"][0] == 5


def test_the_listing_biggest_first_with_the_unnamed_counted(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-03-01 worked 3 hours for Acme\n"
                  "2026-03-20 worked 9.5 hours for Acme\n"
                  "2026-03-07 volunteered 6 hours at the food bank\n"
                  "2026-03-12 worked 1h30\n",
    })  # fmt: skip
    got = run(str(HERE / "hours.py"), "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "    12.5 h  acme  (2 entries, 2026-03-01 to 2026-03-20)",
        "       6 h  the food bank  (1 entry, 2026-03-07 to 2026-03-07)",
        "     1.5 h  (no one named)  (1 entry, 2026-03-12 to 2026-03-12)",
        "3 groups, 20 h in 4 entries",
    ]
    again = run(str(HERE / "hours.py"), "--box", str(b))
    assert again.stdout == got.stdout


def test_one_group_one_entry_is_singular(tmp_path):
    b = box(tmp_path, {"log.md": "2026-03-01 worked 2 hours for Acme\n"})
    out = run(str(HERE / "hours.py"), "--box", str(b)).stdout.splitlines()
    assert out[-1] == "1 group, 2 h in 1 entry"


def test_since_and_until_keep_to_their_days(tmp_path):
    b = box(
        tmp_path,
        {
            "log.md": "2026-03-01 worked 2 hours for Acme\n2026-04-01 worked 1 hour for Acme\n"
        },
    )
    got = run(str(HERE / "hours.py"), "--box", str(b), "--since", "2026-03-15")
    assert got.stdout.splitlines()[-1] == "1 group, 1 h in 1 entry"
    got = run(str(HERE / "hours.py"), "--box", str(b), "--until", "2026-03-15")
    assert got.stdout.splitlines()[-1] == "1 group, 2 h in 1 entry"


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "hours.py"), "--box", str(b))
    assert got.returncode == 42 and "length of time" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--since", "soon"],
        ["--box", str(b), "--until", "2026-3-1"],
    ):
        got = run(str(HERE / "hours.py"), *argv)
        assert got.returncode == 2, argv
    assert "hours.py" in run(str(HERE / "hours.py")).stderr
    assert (
        "not a kernel box" in run(str(HERE / "hours.py"), "--box", str(tmp_path)).stderr
    )
