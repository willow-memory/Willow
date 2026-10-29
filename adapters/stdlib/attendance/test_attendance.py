"""attendance: a status and names, or a name and a status; late counts as
there, a later mark the same day wins, and the rate is days there over days
marked."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("attendance", HERE / "attendance.py")
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "attendance.py")


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


def test_the_sibling_it_reads_through_is_put_at_the_front():
    here = sys.path.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert sys.path[here - 1] == root and sys.path[here + 1] == root


def test_a_line_gives_marks_as_a_list_or_as_a_name_and_a_status():
    m = at.marks_of
    assert m("Absent: Ben, Cy") == [("Ben", "absent"), ("Cy", "absent")]
    assert m("Present: Ana and Dee") == [("Ana", "present"), ("Dee", "present")]
    assert m("- Late - Eve") == [("Eve", "late")]
    assert m("sick: Fay Lopez; Gus & Hal") == [
        ("Fay Lopez", "absent"),
        ("Gus", "absent"),
        ("Hal", "absent"),
    ]
    assert m("Absent: Ben (flu), Cy") == [("Ben", "absent"), ("Cy", "absent")]
    assert m("Ana present") == [("Ana", "present")]
    assert m("Ben: absent") == [("Ben", "absent")]
    assert m("Cy - late") == [("Cy", "late")]
    assert m("- Dee Marsh excused") == [("Dee Marsh", "absent")]
    assert m("Click here") == [] and m("Click away") == [] and m("Ana missed") == []
    assert m("Here: Ana") == []
    assert m("Away: Ana") == [("Ana", "absent")]
    assert m("Attended: Ana") == [("Ana", "present")]
    assert m("Missed: Ana") == [("Ana", "absent")]
    assert m("Absent: nobody, today") == []
    assert m("Absent: ") == []
    assert m("absent") == []
    assert m("Present") == []
    assert m("The class was absent of noise") == []
    assert m("Ana was present") == [], "a name and a status are side by side"
    assert m("Absentee list: Ana") == []


def test_a_later_mark_the_same_day_wins_and_the_day_comes_from_above_or_the_name():
    pile = [
        {"path": "reg/2026-03-02.md", "line": 1, "text": "Ana absent\nAna present\nBen late\n"},
        {"path": "reg/term.md", "line": 1, "text": "2026-03-03\nAna sick\n2026-03-04 Ana present\n"},
        {"path": "undated.md", "line": 1, "text": "Zed absent\n"},
    ]  # fmt: skip
    assert at.register(pile) == {
        ("Ana", "20260302"): "present", ("Ben", "20260302"): "late",
        ("Ana", "20260303"): "absent", ("Ana", "20260304"): "present",
    }  # fmt: skip


def test_the_listing_by_person_lowest_first(tmp_path):
    b = box(tmp_path, {"reg/2026-03-02.md": "Present: Ana, Dee\nAbsent: Ben\nLate: Cy\n",
                       "reg/2026-03-04.md": "Present: Ana, Cy\nAbsent: Ben, Dee\n",
                       "reg/2026-03-09.md": "Present: Ana\nLate: Ben\nCy absent\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Ben  1 of 3  33%  (2 absent, 1 late)  last absent 2026-03-04",
        "Dee  1 of 2  50%  (1 absent)  last absent 2026-03-04",
        "Cy   2 of 3  67%  (1 absent, 1 late)  last absent 2026-03-09",
        "Ana  3 of 3  100%  (0 absent)",
        "4 people, 11 marks",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout


def test_by_week(tmp_path):
    b = box(tmp_path, {"reg/2026-03-02.md": "Present: Ana, Dee\nAbsent: Ben\nLate: Cy\n",
                       "reg/2026-03-09.md": "Present: Ana\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), "--by", "week").stdout.splitlines()
    assert got == [
        "2026-W10  present 2, late 1, absent 1  (4 marks)",
        "2026-W11  present 1, late 0, absent 0  (1 mark)",
        "2 weeks, 5 marks",
    ]


def test_one_person_one_week_are_singular(tmp_path):
    b = box(tmp_path, {"reg/2026-03-02.md": "Ana present\n"})
    assert run(SCRIPT, "--box", str(b)).stdout.splitlines()[-1] == "1 person, 1 mark"
    assert (
        run(SCRIPT, "--box", str(b), "--by", "week").stdout.splitlines()[-1]
        == "1 week, 1 mark"
    )


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "present or absent" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--by", "month"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "attendance.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
