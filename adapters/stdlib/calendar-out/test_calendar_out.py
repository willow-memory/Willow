"""calendar-out: the dates coming up as an iCalendar file: an all-day event for
each, its title the line it was found on and its description where; escaped
and folded as the standard asks; stable ids so reimporting doesn't double;
calendar files not written again; nothing dated writes nothing; written once;
the same bytes twice; a bad command line refused."""

from __future__ import annotations

import importlib.util
import os
import re
import stat
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "calendar_out.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("calendar_out", SCRIPT)
co = importlib.util.module_from_spec(spec)
spec.loader.exec_module(co)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict[str, str]) -> Path:
    pile = tmp_path / "pile"
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    subprocess.run(
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
        check=True,
        capture_output=True,
    )
    return b


FILES = {
    "car.txt": "The car insurance renews on 2026-10-30.\n",
    "work/cover.txt": "Your cover ends on 31/10/2026 unless renewed, ask Sam; pay.\n",
}


def make(tmp_path: Path, files: dict[str, str] = FILES, *extra: str):
    b = box(tmp_path, files)
    to = tmp_path / "c.ics"
    to.unlink(missing_ok=True)
    got = run("--box", str(b), "--to", str(to), *NOW, *extra)
    return got, to.read_bytes().decode("utf-8") if to.exists() else ""


def test_each_date_is_an_all_day_event_titled_with_its_line_and_pointing_at_its_file(
    tmp_path,
):
    got, ics = make(tmp_path)
    assert got.returncode == 0, got.stderr
    assert ics.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n") and ics.endswith(
        "END:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    assert ics.count("BEGIN:VEVENT") == ics.count("END:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20261030\r\nDTEND;VALUE=DATE:20261031\r\n" in ics
    assert (
        "SUMMARY:The car insurance renews on 2026-10-30." in ics
        and "DESCRIPTION:From car.txt:1\r\n" in ics
    )
    assert (
        "DTSTART;VALUE=DATE:20261031" in ics
        and "DESCRIPTION:From work/cover.txt:1" in ics
    )
    assert "wrote" in got.stdout and "2 events, 2026-10-24 to 2026-11-23" in got.stdout


BS = chr(92)


def test_text_is_escaped_as_the_standard_asks(tmp_path):
    _, ics = make(tmp_path)
    assert f"unless renewed{BS}, ask Sam{BS}; pay." in ics
    assert co.escape(f"a{BS}b;c,d" + chr(10) + "e") == f"a{BS}{BS}b{BS};c{BS},d{BS}ne"


def test_long_lines_are_folded_at_75_bytes_and_never_inside_a_character(tmp_path):
    long = "Meeting on 2026-10-30 about " + "é" * 100 + "\n"
    _, ics = make(tmp_path, {"m.txt": long})
    lines = ics.split("\r\n")
    assert all(len(line.encode("utf-8")) <= 75 for line in lines)
    assert any(line.startswith(" ") for line in lines), (
        "a long line continues on a line that starts with a space"
    )
    unfolded = ics.replace("\r\n ", "")
    assert "SUMMARY:Meeting on 2026-10-30 about " + "é" * 92 + "\r\n" in unfolded, (
        "the title is cut at 120 characters"
    )


def test_the_id_is_stable_so_reimporting_updates_and_does_not_double(tmp_path):
    _, one = make(tmp_path)
    again = tmp_path / "again"
    again.mkdir()
    _, two = make(again)
    uids = sorted(re.findall(r"UID:(\S+)@willow", one))
    assert (
        uids == sorted(re.findall(r"UID:(\S+)@willow", two))
        and len(set(uids)) == 2
        and all(len(u) == 32 for u in uids)
    )


def test_the_stamp_is_now_so_the_same_folder_and_day_give_the_same_bytes(tmp_path):
    _, one = make(tmp_path)
    assert "DTSTAMP:20261024T000000Z" in one
    sub = tmp_path / "two"
    sub.mkdir()
    _, two = make(sub)
    assert one == two


def test_days_sets_the_window(tmp_path):
    _, narrow = make(tmp_path, FILES, "--days", "6")
    assert narrow.count("BEGIN:VEVENT") == 1 and "DTSTART;VALUE=DATE:20261030" in narrow
    assert "DTSTART;VALUE=DATE:20261031" not in narrow
    sub = tmp_path / "wide"
    sub.mkdir()
    _, wide = make(sub, FILES, "--days", "7")
    assert wide.count("BEGIN:VEVENT") == 2


def test_a_date_in_a_calendar_file_is_not_written_again(tmp_path):
    files = {
        **FILES,
        "home.ics": "BEGIN:VEVENT\nDTSTART:20261030\nSUMMARY:Dentist\nEND:VEVENT\n",
        "Calendar/Home.ics.txt": "2026-10-30  Car rego due\n",
    }
    _, ics = make(tmp_path, files)
    assert ics.count("BEGIN:VEVENT") == 2 and "Dentist" not in ics and "rego" not in ics
    assert (
        co.is_calendar("a/b.ics:12")
        and co.is_calendar("Cal/Home.ICS.txt:3")
        and not co.is_calendar("x.ics.md:1")
    )


def test_nothing_dated_writes_nothing_and_waits_on_you(tmp_path):
    got, ics = make(tmp_path, {"a.txt": "Nothing dated here.\n"})
    assert got.returncode == 42 and ics == "" and "no file was written" in got.stdout


def test_the_file_is_written_once_private_and_never_over_a_file(tmp_path):
    b = box(tmp_path, FILES)
    to = tmp_path / "c.ics"
    assert run("--box", str(b), "--to", str(to), *NOW).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("--box", str(b), "--to", str(to), *NOW)
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run("--box", str(b), "--to", str(tmp_path / "nope" / "c.ics"), *NOW).returncode
        == 2
    )


def test_the_folder_is_only_read(tmp_path):
    b = box(tmp_path, FILES)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "c.ics"), *NOW)
    assert {
        p: p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file() and p.name != "c.ics"
    } == before


def test_the_dates_are_dates(tmp_path):
    _, ics = make(tmp_path)
    for m in re.finditer(r"DTSTART;VALUE=DATE:(\d{8})", ics):
        date(int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(1)[6:]))


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path, FILES)
    to = str(tmp_path / "c.ics")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--days", "x"],
                 ["--box", str(b), "--to", to, "--now", "soon"], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "calendar_out.py" in run().stderr


def test_an_ascii_line_is_folded_to_exactly_75_bytes_a_line_with_the_space_counted():
    lines = co.fold("SUMMARY:" + "x" * 300).split("\r\n")
    assert [len(x) for x in lines[:-1]] == [75] * (len(lines) - 1) and 0 < len(
        lines[-1]
    ) <= 75
    assert (
        all(x.startswith(" ") for x in lines[1:])
        and "".join([lines[0]] + [x[1:] for x in lines[1:]]) == "SUMMARY:" + "x" * 300
    )
