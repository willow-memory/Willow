"""fuzzy-dates: each worded doubt reads as its EDTF and nothing else does; a
price never reads as a year, and overlapping readings keep the first."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("fuzzy_dates", HERE / "fuzzy_dates.py")
fz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fz)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def reads(text: str) -> list[tuple[str, str]]:
    rows = fz.found([{"path": "a.md", "line": 1, "text": text}])
    return [(r[0], r[1]) for r in rows]


def test_each_worded_doubt_reads_as_its_edtf():
    assert reads("born about 1880, in Mayo") == [("1880~", "about 1880")]
    assert reads("circa March 1972") == [("1972-03~", "circa March 1972")]
    assert reads("moved here maybe 2019") == [("2019?", "maybe 2019")]
    assert reads("built in the early 1880s") == [("188X", "early 1880s")]
    assert reads("the 1990s were kind") == [("199X", "the 1990s")]
    assert reads("taken spring 1944") == [("1944-21", "spring 1944")]
    assert reads("summer 1950 by the lake") == [("1950-22", "summer 1950")]
    assert reads("autumn 1933") == [("1933-23", "autumn 1933")]
    assert reads("winter of 2001") == [("2001-24", "winter of 2001")]
    assert reads("the fall of 1929") == [("1929-23", "fall of 1929")]
    assert reads("gone before 1900") == [("../1900", "before 1900")]
    assert reads("only after 1950") == [("1950/..", "after 1950")]
    assert reads("between 1880 and 1885") == [("1880/1885", "between 1880 and 1885")]
    assert reads("from 1910 to 1912 or so") == [("1910/1912", "from 1910 to 1912")]
    assert reads("sometime in March") == [("XXXX-03", "sometime in March")]
    assert reads("sometime in March 1972") == [("1972-03", "sometime in March 1972")]


def test_what_admits_no_doubt_in_words_reads_as_nothing():
    for text in ("born 1880", "on 2026-03-01", "March 1972 was wet",
                 "was it 1880?", "about 500 people", "about £1880",
                 "the 80s", "page 1880", "roughly 30 minutes",
                 "about 18805 units", "maybe tomorrow"):  # fmt: skip
        assert reads(text) == [], text


def test_overlapping_readings_keep_the_first():
    got = reads("between 1880 and 1885 or so")
    assert got == [("1880/1885", "between 1880 and 1885")], (
        "the years inside the span read once, as the span"
    )


def test_rows_come_in_file_order_with_the_tally(tmp_path):
    b = box(tmp_path, {
        "b.md": "about 1880 it was\n",
        "a.md": "sometime in June, with Ada\nand maybe 2019\n",
    })  # fmt: skip
    got = run(str(HERE / "fuzzy_dates.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("XXXX-06") and lines[0].endswith("a.md:1")
    assert lines[1].startswith("2019?") and lines[1].endswith("a.md:2")
    assert lines[2].startswith("1880~") and lines[2].endswith("b.md:1")
    assert lines[3] == "3 fuzzy dates, the doubt kept"
    assert got.stdout == run(str(HERE / "fuzzy_dates.py"), "--box", str(b)).stdout


def test_one_alone_is_a_fuzzy_date_not_dates(tmp_path):
    b = box(tmp_path, {"g.md": "about 1880\n"})
    got = run(str(HERE / "fuzzy_dates.py"), "--box", str(b))
    assert got.stdout.splitlines()[-1] == "1 fuzzy date, the doubt kept"


def test_none_found_is_42(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "fuzzy_dates.py"), "--box", str(b))
    assert got.returncode == 42 and "admits doubt" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "fuzzy_dates.py"))
    assert got.returncode == 2 and "fuzzy_dates.py" in got.stderr
    got = run(str(HERE / "fuzzy_dates.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_early_or_late_in_a_year_reads_as_the_year_with_the_phrase_kept():
    assert reads("organized late in 1893") == [("1893", "late in 1893")]
    assert reads("early in 1894 it opened") == [("1894", "early in 1894")]
    assert reads("very early in the year 1873") == [("1873", "early in the year 1873")]
    assert reads("in the early part of 1872") == [("1872", "the early part of 1872")]
    assert reads("the latter part of 1872") == [("1872", "the latter part of 1872")]
    assert reads("the first part of 1850") == [("1850", "the first part of 1850")]
    assert reads("the last part of 1850") == [("1850", "the last part of 1850")]
    assert reads("at the close of 1872") == [("1872", "the close of 1872")]
    assert reads("the end of the year 1869") == [("1869", "the end of the year 1869")]
    assert reads("the beginning of 1850") == [("1850", "the beginning of 1850")]
    assert reads("EARLY IN 1881") == [("1881", "EARLY IN 1881")]


def test_a_year_said_as_two_digits_leaves_its_century_unspecified():
    assert reads("in '70. Mrs. B") == [("XX70", "in '70")]
    assert reads("the one of '64.") == [("XX64", "of '64")]
    assert reads("an orchard in ’88 that") == [("XX88", "in ’88")]  # curly
    assert reads("the spring of '79 we broke") == [("XX79-21", "spring of '79")]
    assert reads("winter '80") == [("XX80-24", "winter '80")]
    # a season keeps the one reading: the shorter "of '79" inside it is not a second
    assert len(reads("In the spring of '79 we broke")) == 1


def test_what_looks_like_these_but_is_not_one_reads_as_nothing():
    for text in ("in '60s style", "the '60s", "price in '150", "in 'em all",
                 "early in the morning", "late in life", "the end of 18",
                 "early in 800", "close of 12345", "at the end of the line",
                 "in '7", "of '123"):  # fmt: skip
        assert reads(text) == [], text
    # the decade shapes are the same as before, and are not read twice
    assert reads("late 1880s") == [("188X", "late 1880s")]
    assert reads("the 1860s and early in 1861") == [
        ("186X", "the 1860s"), ("1861", "early in 1861")]  # fmt: skip
    # a year said in full after a doubt word is still the old reading
    assert reads("about 1880 and late in 1881") == [
        ("1880~", "about 1880"), ("1881", "late in 1881")]  # fmt: skip
