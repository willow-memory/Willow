"""syllabus: lines about a course that give a reading, an assignment or an exam
a day, soonest first, cited, with the distance from --now."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "syllabus.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-03-09T00:00:00Z"]
spec = importlib.util.spec_from_file_location("syllabus", SCRIPT)
sy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sy)


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


SYLLABUS = (
    "# Course syllabus\n"
    "2026-03-02 Read Ch. 1-2: Introduction\n"
    "2026-03-09 Essay 1 due\n"
    "2026-03-16 Midterm exam\n"
    "Week 5 (2026-03-23)\n"
    "Read chapter 4\n"
    "Problem set 2\n"
    "Final exam\n"
    "2026-03-30 lunch with Ana\n"
)


def test_a_line_is_the_first_kind_it_names_exam_before_assignment_before_reading():
    pile = [{"path": "course/syllabus.md", "line": 1, "text": SYLLABUS}]
    got = sy.due(pile)
    assert [(d["day"].isoformat(), d["kind"], d["where"]) for d in got] == [
        ("2026-03-02", "reading", "course/syllabus.md:2"),
        ("2026-03-09", "assignment", "course/syllabus.md:3"),
        ("2026-03-16", "exam", "course/syllabus.md:4"),
        ("2026-03-23", "reading", "course/syllabus.md:6"),
        ("2026-03-23", "assignment", "course/syllabus.md:7"),
        ("2026-03-23", "exam", "course/syllabus.md:8"),
    ]
    both = sy.due(
        [
            {
                "path": "c/syllabus.md",
                "line": 1,
                "text": "2026-03-02 read for the exam\n2026-03-03 homework paper due\n",
            }
        ]
    )
    assert [d["kind"] for d in both] == ["exam", "assignment"]


def test_a_line_must_be_about_a_course_and_have_a_day():
    pile = [
        {"path": "notes/shopping.md", "line": 1, "text": "2026-03-02 read the instructions\n"},
        {"path": "undated.md", "line": 1, "text": "course: read chapter 1\n"},
        {"path": "uni/2026-03-04.md", "line": 1, "text": "lecture 3: read chapter 2\n"},
    ]  # fmt: skip
    got = sy.due(pile)
    assert [(d["day"].isoformat(), d["where"]) for d in got] == [
        ("2026-03-04", "uni/2026-03-04.md:1")
    ]


def test_distance_in_days():
    t = date(2026, 3, 9)
    assert sy.distance(date(2026, 3, 9), t) == "today"
    assert sy.distance(date(2026, 3, 10), t) == "in 1 day"
    assert sy.distance(date(2026, 3, 19), t) == "in 10 days"
    assert sy.distance(date(2026, 3, 8), t) == "1 day ago"
    assert sy.distance(date(2026, 2, 27), t) == "10 days ago"


def test_the_listing_with_distances_and_the_next_day(tmp_path):
    b = box(tmp_path, {"course/syllabus.md": SYLLABUS})
    got = run("--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    out = got.stdout.splitlines()
    assert out[0].startswith(
        "2026-03-02  reading     2026-03-02 Read Ch. 1-2: Introduction"
    )
    assert out[0].endswith("(course/syllabus.md:2, 7 days ago)")
    assert out[1].endswith("(course/syllabus.md:3, today)")
    assert out[2].endswith("(course/syllabus.md:4, in 7 days)")
    assert out[-1] == "2 readings, 2 assignments, 2 exams; next 2026-03-09"
    assert run("--box", str(b), *NOW).stdout == got.stdout


def test_a_long_line_is_cut_and_when_nothing_is_left_to_come_it_says_so(tmp_path):
    b = box(tmp_path, {"c/syllabus.md": "2026-03-02 read " + "x" * 100 + "\n"})
    out = run("--box", str(b), *NOW).stdout.splitlines()
    assert "…" in out[0] and out[-1] == "1 reading; none still to come"


def test_nothing_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b), *NOW)
    assert got.returncode == 42 and "for a course a day" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(b), "--now", "2026-13-45"],
        ["--box", str(tmp_path)],
    ):
        assert run(*argv).returncode == 2, argv
    assert "syllabus.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'syllabus.py')!r})\n"
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
