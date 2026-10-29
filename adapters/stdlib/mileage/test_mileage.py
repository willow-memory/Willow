"""mileage: a drive word and a distance, work and other apart, miles and km
never added, the tax year from the date you give, odometer readings left out."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("mileage", HERE / "mileage.py")
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "mileage.py")


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


def test_distances_keep_miles_and_km_apart():
    assert ml.distances("drove 12 miles") == {"miles": 12}
    assert ml.distances("drove 8.5 mi to the site") == {"miles": 8.5}
    assert ml.distances("drove 1,240 miles") == {"miles": 1240}
    assert ml.distances("drove 130 km") == {"km": 130}
    assert ml.distances("drove 2 kilometres and 3 kilometers") == {"km": 5}
    assert ml.distances("drove 12 miles there and 12 back") == {"miles": 12}
    assert ml.distances("drove 5 miles then 40 km") == {"miles": 5, "km": 40}
    assert ml.distances("drove 3 mi and 4 miles") == {"miles": 7}
    assert ml.distances("drove a long way") == {}
    assert ml.distances("drove 12 milestones") == {}, "mi must stand alone"
    assert ml.distances("drove 5 kmh") == {}


def test_the_tax_year_starts_where_you_say():
    assert ml.start_of("20261015", (1, 1)) == date(2026, 1, 1)
    assert ml.start_of("20260405", (4, 6)) == date(2025, 4, 6)
    assert ml.start_of("20260406", (4, 6)) == date(2026, 4, 6), "the first day is in"
    assert ml.start_of("20261231", (4, 6)) == date(2026, 4, 6)
    assert ml.start_of("20260101", (4, 6)) == date(2025, 4, 6)
    assert ml.start_of("20260301", (7, 1)) == date(2025, 7, 1)
    assert ml.month_day("04-06") == (4, 6)
    for bad in ("4-6", "13-01", "02-30", "02-29", "april", ""):
        assert ml.month_day(bad) is None, bad


def test_the_sibling_it_reads_through_comes_first_and_the_year_defaults_to_the_calendar():
    here = sys.path.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert sys.path[here - 1] == root and sys.path[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
    pile = [{"path": "log.md", "line": 1, "text": "2026-05-01 drove 4 miles\n"}]
    assert ml.tally(pile) == ml.tally(pile, (1, 1))
    assert list(ml.tally(pile)) == [date(2026, 1, 1)]


def test_work_and_other_are_apart_and_odometers_left_out():
    pile = [{"path": "log.md", "line": 1, "text": (
        "2026-05-01 drove 40 miles to the client\n"
        "2026-05-02 drove 10 miles to the cinema\n"
        "2026-05-03 odometer 45,200 miles after the trip\n"
        "2026-05-04 lunch was 12 miles from here\n"
        "2026-05-05 trip to site, 30 miles\n"
        "2026-05-06 drove 10 km for a delivery\n"
    )}]  # fmt: skip
    got = ml.tally(pile, (1, 1))
    year = got[date(2026, 1, 1)]
    assert year == {
        ("miles", "work"): [70.0, 2],
        ("miles", "other"): [10.0, 1],
        ("km", "work"): [10.0, 1],
    }


def test_each_tax_year_has_its_totals_newest_first(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-04-05 drove 20 miles for work\n"
                  "2026-04-06 drove 30 miles for work\n"
                  "2026-04-07 drove 1.5 miles to the shops\n"
                  "2026-04-08 trip 130 km to the client\n",
    })  # fmt: skip
    got = run(SCRIPT, "--box", str(b), "--year-start", "04-06")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "tax year 2026-04-06 to 2027-04-05",
        "          30 miles  for work  (1 trip)",
        "         1.5 miles  other  (1 trip)",
        "         130 km  for work  (1 trip)",
        "tax year 2025-04-06 to 2026-04-05",
        "          20 miles  for work  (1 trip)",
        "4 trips in 2 tax years",
    ]
    assert run(SCRIPT, "--box", str(b), "--year-start", "04-06").stdout == got.stdout


def test_the_calendar_year_is_the_default_and_a_single_trip_is_singular(tmp_path):
    b = box(tmp_path, {"log.md": "2026-03-01 drove 5 miles for work\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.stdout.splitlines() == [
        "tax year 2026-01-01 to 2026-12-31",
        "           5 miles  for work  (1 trip)",
        "1 trip in 1 tax year",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "a drive and how far" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--year-start", "april"],
        ["--box", str(b), "--year-start", "02-30"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "mileage.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
