"""mood: "mood" and the number after it, out of ten unless the line says
another top, a day's scores averaged, periods oldest first with the change."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("mood", HERE / "mood.py")
md = importlib.util.module_from_spec(spec)
spec.loader.exec_module(md)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "mood.py")


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
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'mood.py')!r})\n"
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


def test_a_score_is_mood_and_the_number_after_it_on_a_scale_of_ten():
    assert md.score_of("mood: 7") == 7
    assert md.score_of("Mood 7/10") == 7
    assert md.score_of("MOOD - 4 out of 5") == 8
    assert md.score_of("mood: 55/100") == 5.5
    assert md.score_of("mood 6.5") == 6.5
    assert md.score_of("mood: 0") == 0
    assert md.score_of("mood: 10") == 10
    assert md.score_of("slept badly, mood: 3, tired") == 3
    assert md.score_of("mood: 11") is None, "over the top of ten"
    assert md.score_of("mood: 6/5") is None, "over its own top"
    assert md.score_of("mood: 3/0") is None
    assert md.score_of("mood swings are normal") is None
    assert md.score_of("good mood") is None, "no number"
    assert md.score_of("moody 7") is None, "the word stands alone"
    assert md.score_of("mood is a long way from 7") is None, (
        "the number is straight after"
    )
    assert md.score_of("mood 7/10/2026") is None, "a date is not a score"
    assert md.score_of("") is None


def test_a_days_scores_average():
    pile = [{"path": "j/2026-03-01.md", "line": 1, "text": "mood: 4\nmood: 8\nwalked\n"},
            {"path": "j/2026-03-02.md", "line": 1, "text": "mood: 5\n"}]  # fmt: skip
    assert md.days_of(pile) == {"20260301": 6.0, "20260302": 5.0}


def test_periods_by_month_and_by_iso_week():
    assert md.period("20260301", "month") == "2026-03"
    assert md.period("20260301", "week") == "2026-W09"
    assert md.period("20260105", "week") == "2026-W02"
    assert md.period("20251231", "week") == "2026-W01", (
        "the ISO year, not the calendar's"
    )


def test_the_listing_oldest_first_with_the_change(tmp_path):
    b = box(tmp_path, {
        "j/2026-02-09.md": "mood: 3\n", "j/2026-02-20.md": "mood: 9\n",
        "j/2026-03-02.md": "mood: 4\n", "j/2026-03-28.md": "mood: 9\nmood: 9/10\n",
        "j/2026-04-01.md": "mood: 6\n", "j/2026-05-01.md": "mood: 6.5\n",
        "j/2026-06-01.md": "mood: 6.5\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "2026-02  avg 6.0  2 days  low 3 on 2026-02-09, high 9 on 2026-02-20",
        "2026-03  avg 6.5  2 days  low 4 on 2026-03-02, high 9 on 2026-03-28  up 0.5",
        "2026-04  avg 6.0  1 day  low 6 on 2026-04-01, high 6 on 2026-04-01  down 0.5",
        "2026-05  avg 6.5  1 day  low 6.5 on 2026-05-01, high 6.5 on 2026-05-01  up 0.5",
        "2026-06  avg 6.5  1 day  low 6.5 on 2026-06-01, high 6.5 on 2026-06-01  same",
        "5 months, 7 days",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout


def test_by_week(tmp_path):
    b = box(tmp_path, {"j/2026-03-02.md": "mood: 4\n", "j/2026-03-09.md": "mood: 8\n"})
    got = run(SCRIPT, "--box", str(b), "--by", "week").stdout.splitlines()
    assert got == [
        "2026-W10  avg 4.0  1 day  low 4 on 2026-03-02, high 4 on 2026-03-02",
        "2026-W11  avg 8.0  1 day  low 8 on 2026-03-09, high 8 on 2026-03-09  up 4.0",
        "2 weeks, 2 days",
    ]


def test_ties_name_the_earlier_low_and_high(tmp_path):
    b = box(tmp_path, {"j/2026-03-02.md": "mood: 4\n", "j/2026-03-09.md": "mood: 4\n"})
    out = run(SCRIPT, "--box", str(b)).stdout.splitlines()[0]
    assert "low 4 on 2026-03-02, high 4 on 2026-03-02" in out


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "a mood a score" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--by", "year"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "mood.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
