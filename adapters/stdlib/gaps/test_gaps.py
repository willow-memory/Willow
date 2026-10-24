"""gaps: where a log stops, by a rule a person can read: the typical spacing
is the middle one, a gap is more than three times it, too few dates is said,
undated files are said, and no date is guessed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("gaps", HERE / "gaps.py")
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)
NOW = ["--now", "2026-10-23T00:00:00Z"]
END = "A gap is days with no entry written, not days when nothing happened."


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict[str, str]) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def gaps(tmp_path: Path, files: dict[str, str], *more: str):
    return run(str(HERE / "gaps.py"), "--box", str(box(tmp_path, files)), *more)


def daily(folder: str, days: list[int], month: str = "2026-03") -> dict[str, str]:
    return {f"{folder}/{month}-{d:02d}.md": f"note {d}\n" for d in days}


def test_a_steady_log_has_no_gap(tmp_path):
    got = gaps(tmp_path, daily("notes", [1, 2, 3, 4, 5, 6]))
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "notes/  files named by a date  6 entries, 2026-03-01 to 2026-03-06, "
        "typical spacing 1 day",
        "  no gap",
        "No gaps in 1 log with a rhythm.",
        END,
    ]


def test_a_gap_is_said_with_its_days(tmp_path):
    got = gaps(tmp_path, daily("notes", [1, 2, 3, 4, 11, 12, 13, 14, 15, 16]))
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        "notes/  files named by a date  10 entries, 2026-03-01 to 2026-03-16, "
        "typical spacing 1 day",
        "  GAP       2026-03-04 to 2026-03-11  6 days with no entry",
        "1 gap in 1 of 1 log with a rhythm.",
        END,
    ]


def test_too_few_dates_is_said_not_judged(tmp_path):
    got = gaps(tmp_path, {"reading.md": "2026-05-01 a\n2026-05-02 b\n2026-05-30 c\n"})
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "reading.md  lines that start with a date  3 entries: too few for a "
        "rhythm (it needs 4)",
        "No log has enough dates for a rhythm (it needs 4).",
        END,
    ]
    one = gaps(tmp_path / "x", {"r.md": "2026-05-01 a\n"})
    assert "  1 entry: too few" in one.stdout


def test_four_dates_are_enough_for_a_rhythm(tmp_path):
    got = gaps(
        tmp_path, {"r.md": "2026-05-01 a\n2026-05-02 b\n2026-05-03\n2026-05-30\n"}
    )
    assert got.returncode == 0
    assert "  GAP       2026-05-03 to 2026-05-30  26 days with no entry" in got.stdout


def test_undated_files_beside_a_log_are_said_not_counted(tmp_path):
    files = daily("notes", [1, 2, 3, 4, 5])
    files |= {"notes/index.md": "all my notes\n", "garden.md": "Tomatoes want sun.\n",
              "notes/books.md": "2026-01-01 Middlemarch\n"}  # fmt: skip
    got = gaps(tmp_path, files)
    lines = got.stdout.splitlines()
    undated = [x for x in lines if "UNDATED" in x]
    # garden.md is beside no log; books.md is a log of its own lines
    assert undated == [
        "  UNDATED   notes/index.md  no date in its name or at the start of a "
        "line, not counted"
    ]
    assert lines[3] == (
        "notes/books.md  lines that start with a date  1 entry: too few for a "
        "rhythm (it needs 4)"
    )
    assert "No gaps in 1 log with a rhythm; 1 log too short for a rhythm." in lines


def test_nothing_dated_is_its_own_answer(tmp_path):
    got = gaps(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    assert got.returncode == 42
    assert got.stdout.startswith("Nothing dated in your folder")


def test_the_threshold_is_more_than_three_times_typical():
    d = [date(2026, 1, x) for x in (1, 2, 3, 4)]
    assert gp.gaps(set(d), None) == (1, [])  # every step 1
    assert gp.gaps(set(d) | {date(2026, 1, 7)}, None) == (1, [])  # 3: not more
    typical, found = gp.gaps(set(d) | {date(2026, 1, 8)}, None)
    assert (typical, found) == (1, [(date(2026, 1, 4), date(2026, 1, 8), 3, False)])


def test_typical_is_the_smaller_middle_of_an_even_count():
    # spacings 1, 1, 5, 5: the middle two are 1 and 5, typical is 1
    d = {date(2026, 1, x) for x in (1, 2, 3, 8, 13)}
    typical, found = gp.gaps(d, None)
    assert typical == 1
    assert [(a.day, b.day, n) for a, b, n, _ in found] == [(3, 8, 4), (8, 13, 4)]
    # spacings 1, 5, 5: the middle is 5, so nothing is a gap
    assert gp.gaps({date(2026, 1, x) for x in (1, 2, 7, 12)}, None) == (5, [])


def test_now_counts_the_days_since_the_last_entry(tmp_path):
    files = daily("notes", [1, 2, 3, 4])
    got = gaps(tmp_path, files, "--now", "2026-03-09T08:00:00Z")
    assert got.returncode == 0
    assert (
        "  SINCE     2026-03-04 to 2026-03-09 (--now)  4 days with no entry so far"
        in got.stdout.splitlines()
    )
    # three days on is not more than three times one day
    got = run(str(HERE / "gaps.py"), "--box", str(tmp_path / "box"), "--now",
              "2026-03-07T08:00:00Z")  # fmt: skip
    assert got.returncode == 42 and "SINCE" not in got.stdout
    # without --now, nothing after the last entry is judged
    assert (
        "SINCE" not in run(str(HERE / "gaps.py"), "--box", str(tmp_path / "box")).stdout
    )


def test_a_log_is_shown_with_its_gaps_open_and_closed():
    d = {date(2026, 1, x) for x in (1, 2, 3, 4, 9)}
    log = {"name": "a.md", "how": "h", "days": d, "undated": ["a/x.md"]}
    rows, n = gp.show(log, date(2026, 1, 14))
    assert n == 2
    assert rows == [
        "a.md  h  5 entries, 2026-01-01 to 2026-01-09, typical spacing 1 day",
        "  GAP       2026-01-04 to 2026-01-09  4 days with no entry",
        "  SINCE     2026-01-09 to 2026-01-14 (--now)  4 days with no entry so far",
        "  UNDATED   a/x.md  no date in its name or at the start of a line, not counted",
    ]
    rows, n = gp.show(log | {"days": {date(2026, 1, x) for x in (1, 8, 15, 22)}}, None)
    assert (
        n == 0 and rows[0].endswith("typical spacing 7 days") and rows[1] == "  no gap"
    )
    assert gp.plural(1, "day") == "1 day" and gp.plural(2, "day") == "2 days"


def test_a_date_is_read_at_a_lines_start_after_a_heading_or_bullet(tmp_path):
    text = ("## 2026-01-05 Monday\n- 2026-01-12\n* 2026-01-19 walk\n"
            "> 2026-01-26\n\t2026-02-02\nsaw Ana on 2026-02-09\n"
            "2026-02-31 not a day\n11/03/2026 never guessed\n")  # fmt: skip
    got = gaps(tmp_path, {"diary.md": text})
    assert got.stdout.splitlines()[0] == (
        "diary.md  lines that start with a date  5 entries, 2026-01-05 to "
        "2026-02-02, typical spacing 7 days"
    )


def test_a_file_named_by_a_date_is_its_folders_entry_only(tmp_path):
    files = {
        f"2026-04-0{d}.md": f"2026-01-0{d} old\n2026-01-2{d}\n" for d in range(1, 6)
    }
    got = gaps(tmp_path, files)
    assert got.stdout.splitlines()[:2] == [
        "./  files named by a date  5 entries, 2026-04-01 to 2026-04-05, "
        "typical spacing 1 day",
        "  no gap",
    ]
    assert gp.starts_with_date("") is None and gp.day("20260231") is None


def test_a_windows_path_is_read_by_its_folder():
    pile = [{"path": f"notes\\2026-03-0{d}.md", "text": "x"} for d in range(1, 5)]
    assert [x["name"] for x in gp.logs(pile)] == ["notes/"]


def test_logs_are_in_name_order_and_the_same_bytes_twice(tmp_path):
    files = daily("b", [1, 2, 3, 9]) | daily("a", [1, 2, 3, 4])
    first = gaps(tmp_path, files)
    names = [x.split()[0] for x in first.stdout.splitlines() if not x.startswith(" ")]
    assert names[:2] == ["a/", "b/"]
    assert "1 gap in 1 of 2 logs with a rhythm." in first.stdout
    again = run(str(HERE / "gaps.py"), "--box", str(tmp_path / "box"))
    assert again.stdout == first.stdout


def test_refused(tmp_path):
    b = box(tmp_path, daily("n", [1, 2, 3, 4]))
    script = str(HERE / "gaps.py")
    for argv in ([], ["--box"], ["--box", str(b), "x"], ["--box", str(b), "--now"],
                 ["--box", str(b), "--now", "soon"]):  # fmt: skip
        got = run(script, *argv)
        assert got.returncode == 2 and "gaps.py --box DIR" in got.stderr, argv
    got = run(script, "--box", str(tmp_path))
    assert got.returncode == 2 and got.stderr.startswith("refused")
