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


def pile_of(**files: str) -> list[dict]:
    return [{"path": name, "line": 1, "text": text} for name, text in files.items()]


def soon(pile: list[dict], today: str = "2026-10-24", days: int = 30) -> list:
    return [
        (str(d), place)
        for d, place, _ in cu.coming(pile, date.fromisoformat(today), days)
    ]


def test_a_yearly_event_and_a_birthday_come_up_on_this_years_date():
    pile = pile_of(**{
        "cal.txt": "2022-11-03  Car rego due  (yearly, from this date)\n"
                   "notes: renew before 3 Nov\nrepeats: FREQ=YEARLY",
        "people.txt": "contact: Mags Doyle\nbirthday: 1957-10-30",
    })  # fmt: skip
    assert soon(pile) == [("2026-10-30", "people.txt:2"), ("2026-11-03", "cal.txt:1")]
    hits = cu.coming(pile, date(2026, 10, 24), 30)
    assert hits[0][2] == "birthday: 1957-10-30  (every year)"
    assert hits[1][2].startswith("2022-11-03  Car rego due")


def test_a_raw_calendar_rule_belongs_to_its_dtstart_and_shows_its_summary():
    raw = ("BEGIN:VEVENT\nDTSTAMP:20261024T000000Z\nDTSTART;VALUE=DATE:20221103\n"
           "DTEND;VALUE=DATE:20221104\nRRULE:FREQ=YEARLY\nSUMMARY:Car rego due\n"
           "END:VEVENT")  # fmt: skip
    hits = cu.coming(pile_of(**{"home.ics": raw}), date(2026, 10, 25), 30)
    assert [(str(d), p, t) for d, p, t in hits] == [
        (
            "2026-11-03",
            "home.ics:3",
            "DTSTART;VALUE=DATE:20221103  SUMMARY:Car rego due",
        )
    ]


def test_each_rule_is_kept_to():
    def on(rule: str, start: str, today: str, days: int = 60) -> list[str]:
        got = cu.repeats(date.fromisoformat(start), rule, date.fromisoformat(today),
                         date.fromisoformat(today) + cu.timedelta(days=days))  # fmt: skip
        return [str(d) for d in got]

    assert on("FREQ=MONTHLY", "2026-01-31", "2026-02-01") == ["2026-03-31"]  # no 31 Feb
    assert on("FREQ=YEARLY", "2024-02-29", "2027-01-01", 800) == ["2028-02-29"]
    assert on("FREQ=WEEKLY;INTERVAL=2", "2026-10-01", "2026-10-02", 30) == [
        "2026-10-15", "2026-10-29"]  # fmt: skip
    assert on("FREQ=DAILY;COUNT=3", "2026-10-01", "2026-10-02") == [
        "2026-10-02",
        "2026-10-03",
    ]
    assert on("FREQ=WEEKLY;UNTIL=20261015T000000Z", "2026-10-01", "2026-10-02") == [
        "2026-10-08", "2026-10-15"]  # fmt: skip
    assert (
        on("FREQ=WEEKLY;BYDAY=MO,TH", "2026-10-01", "2026-10-02") == []
    )  # not guessed
    assert on("FREQ=HOURLY", "2026-10-01", "2026-10-02") == []


def test_a_rule_stops_looking_up_at_its_paragraph_or_event():
    pile = pile_of(**{"cal.txt": "2020-11-03  Old thing\n\nrepeats: FREQ=YEARLY"})
    assert soon(pile) == [], "a rule with no start in its own paragraph counts nothing"
