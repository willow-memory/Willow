"""gradebook: a name, a colon and a score make a mark; dates and totals do
not; behind is the average under the line or the last two marks well under
the ones before, by plain arithmetic."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("gradebook", HERE / "gradebook.py")
gb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gb)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "gradebook.py")


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


def test_a_mark_is_a_name_a_colon_and_a_score():
    assert gb.mark_of("Maya Chen: Essay 2 - 17/20") == ("Maya Chen", "Essay 2", 85.0)
    assert gb.mark_of("- Ben: Quiz 4, 7 out of 10") == ("Ben", "Quiz 4", 70.0)
    assert gb.mark_of("Cy Dunn: Project 62%") == ("Cy Dunn", "Project", 62.0)
    assert gb.mark_of("Cy Dunn: 12.5/25") == ("Cy Dunn", "(unnamed)", 50.0)
    assert gb.mark_of("Ana Maria Lopez: Quiz (9/10)") == (
        "Ana Maria Lopez",
        "Quiz",
        90.0,
    )
    assert gb.mark_of("O'Brien: Test 8/10")[0] == "O'Brien"
    assert gb.mark_of("Maya Chen: Essay") is None, "no score"
    assert gb.mark_of("maya: Essay 17/20") is None, "a name starts with a capital"
    assert gb.mark_of("Maya Chen has 17/20") is None, "no colon"
    assert gb.mark_of("Total: 17/20") is None
    assert gb.mark_of("Page: 3/4") is None
    assert gb.mark_of("Four Capital Words Here: 3/4") is None, "one to three words"
    assert gb.mark_of("Maya: met on 3/4/2026") is None, "a date is not a score"
    assert gb.mark_of("Maya: Essay 5/0") is None, "nothing out of nothing"
    assert gb.mark_of("Maya: Essay 3/4/5") is None
    assert (
        gb.mark_of("H6: 5 fr bees, eggs yes, brood 7 fr, queen not seen, mites 1/300")
        is None
    )
    assert gb.mark_of("H6: Quiz 8/10") is None, "an id has no lowercase letter"
    assert gb.mark_of("Subject: Re: Imre Varga appointment 38%") is None
    assert gb.mark_of("Description: booked by phone 250%") is None
    assert gb.mark_of("Maya: one two three four five six seven 8/10") is not None
    assert gb.mark_of("Maya: one two three four five six seven eight 8/10") is None, (
        "a sentence"
    )
    assert gb.mark_of("Maya: Essay 100%")[2] == 100.0
    assert gb.mark_of("Maya: Essay 0/10")[2] == 0.0


def test_behind_is_the_average_or_a_fall():
    rows = lambda *ps: [("2026030%d" % i, "x", p) for i, p in enumerate(ps, 1)]  # noqa: E731
    assert gb.flags(rows(90, 80), 50) == []
    assert gb.flags(rows(40, 50), 50) == ["below 50%"]
    assert gb.flags(rows(50, 50), 50) == [], "the line itself is not below it"
    assert gb.flags(rows(50, 50), 60) == ["below 60%"]
    assert gb.flags(rows(90, 90, 70, 70), 50) == ["falling"]
    assert gb.flags(rows(90, 90, 76, 76), 50) == [], "14 points is not 15"
    assert gb.flags(rows(90, 75, 75), 50) == ["falling"], "15 points is"
    assert gb.flags(rows(90, 60), 50) == [], "two marks are not a trend"
    assert gb.flags(rows(90, 30, 30), 50) == ["falling"]
    assert gb.flags(rows(60, 60, 20, 20), 50) == ["below 50%", "falling"]


def test_marks_come_in_day_order_with_the_day_above_or_the_file_name():
    pile = [
        {"path": "2026-03-05.md", "line": 1, "text": "Maya Chen: Essay 2 - 17/20\n"},
        {"path": "term.md", "line": 1, "text": "2026-03-01\nMaya Chen: Essay 1 - 10/20\nTotal: 3/4\n"},
        {"path": "undated.md", "line": 1, "text": "Maya Chen: Essay 3 - 20/20\n"},
    ]  # fmt: skip
    got = gb.marks(pile)
    assert got == {
        "Maya Chen": [("20260301", "Essay 1", 50.0), ("20260305", "Essay 2", 85.0)]
    }


def test_the_listing_lowest_average_first(tmp_path):
    b = box(tmp_path, {"term/2026-03-02.md": (
        "Maya Chen: Essay 1 17/20\nMaya Chen: Essay 2 18/20\n"
        "Ben Ruiz: Quiz 1 4/10\nBen Ruiz: Quiz 2 5/10\n"
        "Cy: Essay 1 90%\n"), "term/2026-03-09.md": "Cy: Essay 2 90%\nCy: Essay 3 50%\nCy: Essay 4 45%\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Ben Ruiz    45%  2 marks  latest 50% (Quiz 2, 2026-03-02)  below 50%",
        "Cy          69%  4 marks  latest 45% (Essay 4, 2026-03-09)  falling",
        "Maya Chen   88%  2 marks  latest 90% (Essay 2, 2026-03-02)",
        "3 students, 2 behind",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout
    higher = run(SCRIPT, "--box", str(b), "--below", "90").stdout.splitlines()
    assert higher[-1] == "3 students, 3 behind" and "below 90%" in higher[0]


def test_one_student_one_mark_is_singular(tmp_path):
    b = box(tmp_path, {"2026-03-02.md": "Maya: Essay 8/10\n"})
    assert run(SCRIPT, "--box", str(b)).stdout.splitlines() == [
        "Maya   80%  1 mark  latest 80% (Essay, 2026-03-02)",
        "1 student, 0 behind",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "gives a student a mark" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--below", "half"],
        ["--box", str(b), "--below", "-5"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "gradebook.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
