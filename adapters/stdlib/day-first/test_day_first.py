"""day-first's tests: each day-first form given its ISO date, what reads
some other way left as it is, a file that says month first named, the
kernel's own files mirrored under their names, and the kernel then reading
a date it couldn't before."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("day_first", HERE / "day_first.py")
df = importlib.util.module_from_spec(spec)
spec.loader.exec_module(df)
kernel = df.kernel


def cli(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "day_first.py"), *map(str, argv)],
                          capture_output=True, text=True, check=False)  # fmt: skip


@pytest.mark.parametrize("text, marked", [
    ("Expiry: 09/11/2026", "Expiry: 09/11/2026 [2026-11-09]"),
    ("ends 03/11/26.", "ends 03/11/26 [2026-11-03]."),
    ("on 3.11.2026 at noon", "on 3.11.2026 [2026-11-03] at noon"),
    ("Tue 3 Nov 2026", "Tue 3 Nov 2026 [2026-11-03]"),
    ("the 3rd November, 2026", "the 3rd November, 2026 [2026-11-03]"),
    ("24/10/2026", "24/10/2026 [2026-10-24]"),
    ("born 01/02/1971", "born 01/02/1971 [1971-02-01]"),
    ("[03/12/2024, 08:10:00]", "[03/12/2024 [2024-12-03], 08:10:00]"),
])  # fmt: skip
def test_each_day_first_form_is_given_its_iso_date(text, marked):
    got, n, says_month_first = df.mark(text)
    assert (got, n, says_month_first) == (marked, 1, False)


@pytest.mark.parametrize("text", [
    "MOT item 1.1.11 (c)",      # a dotted date needs its four-digit year
    "version 1.2.3",
    "see 2/3/2026/x",            # part of a path
    "v1 03/11/2026.5",
    "Mon 26 Oct",                # no year: its year would be a guess
    "31/02/2026",                # no such day
    "03/11/1850",                # before 1900
    "09/11/2026 [2026-11-09]",   # marked already
])  # fmt: skip
def test_what_isnt_a_day_first_date_is_left_as_it_is(text):
    assert df.mark(text) == (text, 0, False)


def test_a_file_whose_dates_say_month_first_keeps_its_numbers_and_says_so():
    got, n, says = df.mark("Paid 11/24/2026; due 03/11/2026; on 3 Nov 2026")
    assert says is True and n == 1  # only the words, which read one way
    assert got == "Paid 11/24/2026; due 03/11/2026; on 3 Nov 2026 [2026-11-03]"


@pytest.fixture
def life(tmp_path):
    src = tmp_path / "life"
    (src / "car").mkdir(parents=True)
    (src / "car" / "MOT.txt").write_text("Test date: 10/11/2025\nExpiry: 09/11/2026\n")
    (src / "mail.eml").write_text("Subject: cover\n\nYour cover ends on 03/11/2026.\n")
    (src / "cal.ics").write_text(
        "BEGIN:VEVENT\nSUMMARY:Party, 7 Nov 2026\nEND:VEVENT\n"
    )
    (src / "page.html").write_text("<p>Due <b>06/12/2026</b></p>")
    (src / "us.md").write_text("Filed 11/24/2026, hearing 03/11/2026\n")
    (src / "photo.jpg").write_bytes(b"\xff\xd8\x00\x00binary")
    (src / ".hidden.txt").write_text("01/02/2026\n")
    return src


def test_every_file_the_kernel_reads_is_mirrored_under_its_name(life, tmp_path):
    got = cli("mirror", "--from", life, "--to", tmp_path / "m")
    assert got.returncode == 0, got.stderr
    m = tmp_path / "m"
    assert sorted(p.relative_to(m).as_posix() for p in m.rglob("*") if p.is_file()) == [
        "cal.ics", "car/MOT.txt", "mail.eml", "page.html.txt", "us.md"]  # fmt: skip
    assert (m / "car" / "MOT.txt").read_text() == "Test date: 10/11/2025 [2025-11-10]\nExpiry: 09/11/2026 [2026-11-09]\n"  # fmt: skip
    assert "03/11/2026 [2026-11-03]" in (m / "mail.eml").read_text()
    assert "7 Nov 2026 [2026-11-07]" in (m / "cal.ics").read_text()
    assert (
        " ".join((m / "page.html.txt").read_text().split())
        == "Due 06/12/2026 [2026-12-06]"
    )  # tags dropped as the kernel drops them
    assert (m / "us.md").read_text() == "Filed 11/24/2026, hearing 03/11/2026\n"
    assert "month first: us.md" in got.stderr and "5 day-first dates" in got.stdout
    assert (
        (life / "car" / "MOT.txt").read_text().startswith("Test date: 10/11/2025\n")
    )  # the original stays


def test_a_mirror_run_again_comes_out_the_same(life, tmp_path):
    cli("mirror", "--from", life, "--to", tmp_path / "a")
    cli("mirror", "--from", tmp_path / "a", "--to", tmp_path / "b")
    for p in (tmp_path / "a").rglob("*"):
        if p.is_file():
            q = tmp_path / "b" / p.relative_to(tmp_path / "a")
            q = q if q.exists() else q.with_name(q.name + ".txt")
            assert q.read_text() == p.read_text(), p


def test_the_kernel_places_a_date_it_couldnt_before(life, tmp_path):
    line = (life / "car" / "MOT.txt").read_text().splitlines()[1]
    assert kernel.newest(line) == ""
    cli("mirror", "--from", life, "--to", tmp_path / "m")
    marked = (tmp_path / "m" / "car" / "MOT.txt").read_text().splitlines()[1]
    assert kernel.newest(marked) == "20261109"


@pytest.mark.parametrize("argv, says", [
    (("mirror", "--from", "{life}", "--to", "{life}/inside"), "must not be inside each other"),
    (("mirror", "--from", "{tmp}/none", "--to", "{tmp}/m"), "is not a folder"),
])  # fmt: skip
def test_what_isnt_a_mirror_is_refused(life, tmp_path, argv, says):
    got = cli(*(a.format(life=life, tmp=tmp_path) for a in argv))
    assert got.returncode == 2 and says in got.stderr


def test_a_folder_with_nothing_the_kernel_reads_writes_nothing(tmp_path):
    (tmp_path / "only").mkdir()
    (tmp_path / "only" / "a.jpg").write_bytes(b"\x00\x01")
    got = cli("mirror", "--from", tmp_path / "only", "--to", tmp_path / "m")
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = cli()
    assert got.returncode == 2 and "day_first.py" in got.stderr
