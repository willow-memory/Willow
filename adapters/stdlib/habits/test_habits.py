"""habits: the same short line on four days or more, runs and misses by
plain counting, no clock consulted, and prose never mistaken for a tick."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("habits", HERE / "habits.py")
hb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hb)
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


def test_the_key_drops_digits_case_and_punctuation_and_prose_is_no_tick():
    assert hb.key_of("2026-03-01 Ran 5k!") == "ran"
    assert hb.key_of("Walked the dog.") == "walked the dog"
    assert hb.key_of("walked   the DOG") == "walked the dog"
    assert hb.key_of("Wrote to the council about the mould again today") == "", (
        "a sentence of more than six words is prose"
    )
    assert hb.key_of("2026-03-01") == "", "a date alone ticks nothing"
    assert hb.key_of("") == ""
    assert hb.key_of("DTSTART;VALUE=DATE:20261028") == "", "a machine's line shouts"
    assert hb.key_of("DD HARBOUR PENSIONS SIPP") == ""
    assert hb.key_of("tags: daily") == "", "a field is a file's furniture"
    assert hb.key_of("UID:20261028-xyz@example.net") == ""
    assert hb.key_of("DTEND;TZID=Australia/Melbourne:20220102") == ""
    assert hb.key_of("name=value lines are fields too") == ""
    assert hb.key_of("</body></html>") == "", "markup is no one's habit"
    assert hb.key_of("walked: felt good") == "", "a field's shape, even yours"
    assert hb.key_of("Walked, felt good") == "walked felt good"


def test_four_distinct_days_make_a_habit_and_fewer_never_do():
    pile = [{"path": f"d/2026-01-0{i}.md", "line": 1, "text": "walked\nstretched\n"}
            for i in range(1, 5)]  # fmt: skip
    pile += [{"path": "d/2026-01-09.md", "line": 1, "text": "stretched\n"}]
    got = hb.ticks(pile)
    assert set(got) == {"walked", "stretched"}
    assert len(got["stretched"]) == 5
    three = hb.ticks(pile[:3])
    assert three == {}, "three days are notes, not yet a habit"
    twice_one_day = [{"path": "a.md", "line": 1,
                      "text": "2026-01-01 walked\nwalked\n"}]  # fmt: skip
    assert hb.ticks(twice_one_day * 4) == {}, "one day twice is one day"


def test_a_lines_day_is_said_above_or_the_files_name():
    pile = [{"path": "log.md", "line": 1,
             "text": "2026-01-01 a cold day\nwalked\n2026-01-02\nwalked\n"},
            {"path": "d/2026-01-03.md", "line": 1, "text": "walked\n"},
            {"path": "undated.md", "line": 1, "text": "walked\n2026-01-04 walked\n"}]  # fmt: skip
    got = hb.ticks(pile)
    assert got == {"walked": {"20260101", "20260102", "20260103", "20260104"}}, (
        "the undated file's bare line ticks nothing"
    )


def test_runs_and_misses_are_plain_counting():
    days = {"20260101", "20260102", "20260103", "20260105", "20260106"}
    assert hb.runs_of(days) == [3, 2]
    assert hb.missed(days) == (1, "2026-01-04")
    assert hb.runs_of({"20260131", "20260201"}) == [2], "a run crosses the month"
    assert hb.runs_of({"20260930", "20261001"}) == [2], "and into October"
    assert hb.missed({"20261030", "20261101"}) == (1, "2026-10-31")
    assert hb.runs_of({"20251231", "20260101"}) == [2], "and across the year"
    assert hb.missed({"20260101", "20260102"}) == (0, "")
    days = {"20260101", "20260110", "20260111", "20260120"}
    assert hb.runs_of(days) == [1, 2, 1]
    assert hb.missed(days) == (16, "2026-01-19"), "the most recent gap is named"


def test_the_listing_most_days_first_with_runs_and_misses(tmp_path):
    files = {f"d/2026-02-0{i}.md": "walked the dog\n" for i in range(1, 8)}
    del files["d/2026-02-05.md"]
    files.update({f"d/2026-02-0{i}b.md": "no sugar 2026-02-0" + str(i) + "\n"
                  for i in range(1, 5)})  # fmt: skip
    b = box(tmp_path, files)
    got = run(str(HERE / "habits.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and len(lines) == 3
    assert lines[0] == ("   6 days  longest run 4  ends on 2  walked the dog"
                        "  (2026-02-01 to 2026-02-07; missed 1, last 2026-02-05)")  # fmt: skip
    assert lines[1] == ("   4 days  longest run 4  ends on 4  no sugar"
                        "  (2026-02-01 to 2026-02-04; missed none)")  # fmt: skip
    assert lines[2] == "2 habits, written on 4 days or more"
    assert got.stdout == run(str(HERE / "habits.py"), "--box", str(b)).stdout


def test_nothing_on_four_days_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "habits.py"), "--box", str(b))
    assert got.returncode == 42 and "4 days or more" in got.stdout
    got = run(str(HERE / "habits.py"))
    assert got.returncode == 2 and "habits.py" in got.stderr
    got = run(str(HERE / "habits.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(str(HERE / "habits.py"), "--box", str(b), "--stray", "more")
    assert got.returncode == 2 and "habits.py" in got.stderr
