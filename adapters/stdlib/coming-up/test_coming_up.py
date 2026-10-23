"""coming-up: dated lines in the window, soonest first, read as the kernel
reads dates, with a calendar's bare start line given its summary."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("coming_up", HERE / "coming_up.py")
cu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cu)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return b


def test_the_window_soonest_first_and_dates_as_the_kernel_reads_them(tmp_path):
    b = box(tmp_path, {"notes.md": (
        "Dentist 2026-10-30.\n\nInsurance ends 31/10/2026 unless renewed.\n\n"
        "Last year: 2025-10-30.\n\nFar off: 2027-01-01.\n\nAmbiguous: 11/03/2026.\n"
    )})  # fmt: skip
    got = run(str(HERE / "coming_up.py"), "--box", str(b), *NOW)
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and len(lines) == 2
    assert lines[0].startswith("2026-10-30") and "Dentist" in lines[0]
    assert (
        lines[1].startswith("2026-10-31") and "Insurance" in lines[1]
    )  # 03 > 12? no: 03/11 is day 3, month 11
    wide = run(str(HERE / "coming_up.py"), "--box", str(b), "--days", "90", *NOW).stdout
    assert "2027-01-01" in wide and "11/03/2026" not in wide  # never guessed


def test_a_calendars_start_line_is_given_its_summary_across_a_passage_cut(tmp_path):
    filler = "".join(f"DESCRIPTION:line {i} of a long note\n" for i in range(18))
    ics = (f"BEGIN:VEVENT\n{filler}DTSTART;VALUE=DATE:20261028\nSUMMARY:Tune - Ybarra\n"
           "END:VEVENT\n")  # fmt: skip
    b = box(tmp_path, {"calendar.ics": ics})
    out = run(str(HERE / "coming_up.py"), "--box", str(b), *NOW).stdout
    assert "DTSTART;VALUE=DATE:20261028  SUMMARY:Tune - Ybarra" in out


def test_nothing_in_the_window_and_an_impossible_date(tmp_path):
    b = box(tmp_path, {"a.md": "Next year 2027-05-01. Not a day: 2026-02-31.\n"})
    got = run(str(HERE / "coming_up.py"), "--box", str(b), *NOW)
    assert got.returncode == 42
    pile = [
        {"path": "a.md", "line": 1, "text": "2026-10-31 then 2026-02-31", "id": "x"}
    ]
    assert cu.coming(pile, date(2026, 10, 23), 14)[0][0] == date(2026, 10, 31)


def test_a_bare_start_line_skips_a_dated_line_to_reach_its_summary(tmp_path):
    """The next line with its own date is another event, never this one's
    summary: the summary is the first undated line that says something."""
    b = box(tmp_path, {"cal.ics": "DTSTART:20261028\nRENEWAL 2026-11-30 at the bank\n"
                                  "SUMMARY:Dentist at ten\n"})  # fmt: skip
    got = run(str(HERE / "coming_up.py"), "--box", str(b), *NOW)
    assert "DTSTART:20261028  SUMMARY:Dentist at ten" in got.stdout
    assert "DTSTART:20261028  RENEWAL" not in got.stdout
