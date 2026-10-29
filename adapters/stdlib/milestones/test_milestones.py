"""milestones: a child's firsts, milestones and measurements with their age on
the day, counted on the calendar from --born; a line must be about a child."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "milestones.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("milestones", SCRIPT)
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def test_age_is_counted_on_the_calendar():
    born = date(2026, 1, 31)
    assert ms.age(born, date(2026, 1, 31)) == (0, 0, 0)
    assert ms.age(born, date(2026, 2, 27)) == (0, 0, 27)
    assert ms.age(born, date(2026, 2, 28)) == (0, 1, 0), (
        "born on the 31st, a month later is the last day"
    )
    assert ms.age(born, date(2026, 3, 30)) == (0, 1, 30)
    assert ms.age(date(2026, 3, 2), date(2026, 5, 2)) == (0, 2, 0)
    assert ms.age(date(2026, 3, 2), date(2026, 5, 1)) == (0, 1, 29)
    assert ms.age(date(2026, 3, 2), date(2027, 3, 2)) == (1, 0, 0)
    assert ms.age(date(2026, 3, 2), date(2027, 3, 1)) == (0, 11, 27)
    assert ms.age(date(2024, 2, 29), date(2025, 2, 28)) == (1, 0, 0)
    assert ms.age(date(2026, 12, 31), date(2027, 1, 1)) == (0, 0, 1)
    assert ms.age(date(2026, 3, 2), date(2028, 9, 20)) == (2, 6, 18)


def test_months_clamp_to_the_end_of_the_month():
    assert ms.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert ms.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert ms.add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)
    assert ms.add_months(date(2026, 12, 31), 12) == date(2027, 12, 31)
    assert ms.add_months(date(2026, 1, 15), 0) == date(2026, 1, 15)


def test_a_first_a_milestone_or_a_measurement_about_a_child():
    pile = [{"path": "notes/baby.md", "line": 1, "text": (
        "2026-03-02 first smile!\n"
        "2026-07-14 sat up on her own\n"
        "2027-01-09 first steps\n"
        "2027-01-09 height 74 cm, weight 9.6 kg\n"
        "2027-01-10 weighed 12 lb 4 oz\n"
        "2027-01-11 the first draft of the report\n"
        "2027-01-12 walked to the shop\n"
        "2026-02-01 first words before she was born\n")},
        {"path": "work/log.md", "line": 1, "text": "2027-01-09 first steps in the project\nwalked the dog\n"},
        {"path": "diary.md", "line": 1, "text": "2027-02-01 first tooth, said my daughter\n2027-02-02 Ava first words\n"}]  # fmt: skip
    got = ms.milestones(pile, date(2026, 3, 1), name="Ava")
    assert [(m["day"].isoformat(), m["where"]) for m in got] == [
        ("2026-03-02", "notes/baby.md:1"), ("2026-07-14", "notes/baby.md:2"),
        ("2027-01-09", "notes/baby.md:3"), ("2027-01-09", "notes/baby.md:4"),
        ("2027-01-12", "notes/baby.md:7"), ("2027-02-01", "diary.md:1"), ("2027-02-02", "diary.md:2"),
    ]  # fmt: skip
    assert len(ms.milestones(pile, date(2026, 3, 1))) == 6, (
        "without --name the second diary line is no child's"
    )


def test_the_listing_with_ages(tmp_path):
    b = box(
        tmp_path,
        {
            "notes/baby.md": "2026-03-02 first smile\n2027-01-09 first steps\n2027-01-09 height 74 cm\n"
        },
    )
    got = run("--box", str(b), "--born", "2026-02-27")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "0y 0m 3d   2026-03-02  2026-03-02 first smile  (notes/baby.md:1)",
        "0y 10m 13d 2027-01-09  2027-01-09 first steps  (notes/baby.md:2)",
        "0y 10m 13d 2027-01-09  2027-01-09 height 74 cm  (notes/baby.md:3)",
        "3 milestones",
    ]
    assert run("--box", str(b), "--born", "2026-02-27").stdout == got.stdout


def test_one_milestone_is_singular_and_a_long_line_is_cut(tmp_path):
    b = box(tmp_path, {"baby.md": "2026-03-02 first smile " + "x" * 120 + "\n"})
    out = run("--box", str(b), "--born", "2026-01-01").stdout.splitlines()
    assert out[-1] == "1 milestone"
    assert "…" in out[0] and len(out[0].split("  ")[2]) == 90


def test_nothing_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b), "--born", "2026-01-01")
    assert got.returncode == 42 and "child's first" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in (
        [], ["--box", str(b)], ["--box", str(b), "--born", "soon"], ["--box", str(b), "--born", "2026-02-30"],
        ["--box", str(b), "--born", "2026-1-1"], ["--box", str(b), "--born", "2026-01-01", "stray"],
        ["--box", str(b), "--born", "2026-01-01", "--name", ""], ["--box", str(tmp_path), "--born", "2026-01-01"],
    ):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "milestones.py" in run().stderr
    assert (
        "not a kernel box" in run("--box", str(tmp_path), "--born", "2026-01-01").stderr
    )
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'milestones.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
