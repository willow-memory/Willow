"""reading-log: read / reads / reading with pages or minutes on a day, by ISO
week and by book; the times on a line add; a title is quoted or capitalised
after the verb; a line with neither length counts for nothing."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "reading_log.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("reading_log", SCRIPT)
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
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
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def test_pages_and_minutes_are_what_a_line_says():
    assert (
        rl.pages("read 30 pages") == 30
        and rl.pages("12pp") == 12
        and rl.pages("1 page") == 1
    )
    assert rl.pages("read 10 pages then 5 pages") == 15
    assert (
        rl.pages("page 30") == 0
        and rl.pages("read a lot") == 0
        and rl.pages("2026-03-01") == 0
    )
    assert rl.pages("read 3pm") == 0
    assert (
        rl.minutes("read 20 minutes") == 20
        and rl.minutes("20 mins") == 20
        and rl.minutes("20 min") == 20
    )
    assert (
        rl.minutes("read 1h") == 60
        and rl.minutes("read 2 hours") == 120
        and rl.minutes("1.5 hrs") == 90
    )
    assert rl.minutes("read 1h30") == 90 and rl.minutes("1h 30 min") == 90
    assert rl.minutes("read 1h30 and 10 min") == 100
    assert rl.minutes("read 5 pages") == 0 and rl.minutes("read at 9:30") == 0
    assert rl.minutes("read 5 hats") == 0


def test_a_title_is_quoted_or_capitalised_after_the_verb():
    t = rl.title_of
    assert t('read "The BFG" for 20 minutes') == "The BFG"
    assert t("read “Matilda” 30 pages") == "Matilda"
    assert t("finished _Charlotte's Web_ today") == "Charlotte's Web"
    assert t("read *Fantastic Mr Fox*, 12pp") == "Fantastic Mr Fox"
    assert t("read Charlotte's Web, 20 pages") == "Charlotte's Web"
    assert (
        t("started The Lion the Witch and the Wardrobe, 20 pages")
        == "The Lion the Witch and the Wardrobe"
    )
    assert t("reading The Wind in the Willows 15 minutes") == "The Wind in the Willows"
    assert t("read a bit, 10 minutes") == ""
    assert t("read 20 pages") == ""
    assert t('read "x" twice') == "", "a title is two characters or more"


def test_a_line_needs_a_read_word_and_a_length_and_a_day():
    pile = [{"path": "log/2026-03-02.md", "line": 1, "text": (
        "read The BFG, 20 pages\n"
        "Reading Matilda for 15 minutes\n"
        "reads 10 pages and 5 minutes\n"
        "20 pages of homework\n"
        "read a book\n"
        "2026-03-03 read \"Holes\" 1h30\n")},
        {"path": "undated.md", "line": 1, "text": "read The BFG 20 pages\n"}]  # fmt: skip
    got = rl.log(pile)
    assert got == [
        {"day": "20260302", "title": "The BFG", "pages": 20, "minutes": 0},
        {"day": "20260302", "title": "Matilda", "pages": 0, "minutes": 15},
        {"day": "20260302", "title": "", "pages": 10, "minutes": 5},
        {"day": "20260303", "title": "Holes", "pages": 0, "minutes": 90},
    ]


def test_the_iso_week_of_a_day():
    assert rl.week("20260302") == "2026-W10"
    assert rl.week("20261001") == "2026-W40"
    assert rl.week("20261215") == "2026-W51"
    assert rl.week("20261231") == "2026-W53"
    assert rl.week("20270101") == "2026-W53", "the ISO year, not the calendar's"
    assert rl.week("20260105") == "2026-W02"
    assert rl.dash("20260302") == "2026-03-02"


def test_the_listing_by_week_and_by_book(tmp_path):
    b = box(tmp_path, {
        "log/2026-03-02.md": "read Charlotte's Web, 30 pages, 20 minutes\nread a poem 5 minutes\n",
        "log/2026-03-04.md": "read Charlotte's Web 30 pages 25 min\n",
        "log/2026-03-05.md": "read The BFG 40 pages 30 min\n",
        "log/2026-03-13.md": "read The BFG 135 pages 90 min\n"})  # fmt: skip
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "2026-W10  3 days  100 pages  80 min  Charlotte's Web; The BFG",
        "2026-W11  1 day  135 pages  90 min  The BFG",
        "Charlotte's Web  60 pages, 45 min  (2026-03-02 to 2026-03-04)",
        "The BFG  175 pages, 120 min  (2026-03-05 to 2026-03-13)",
        "2 books, 4 days read, 235 pages, 170 min",
    ]
    assert run("--box", str(b)).stdout == got.stdout


def test_one_book_and_one_day_are_singular_and_a_week_without_a_title_has_none(
    tmp_path,
):
    b = box(tmp_path, {"2026-03-02.md": "read 10 pages\n"})
    assert run("--box", str(b)).stdout.splitlines() == [
        "2026-W10  1 day  10 pages  0 min",
        "0 books, 1 day read, 10 pages, 0 min",
    ]


def test_nothing_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b))
    assert got.returncode == 42 and "something read" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(tmp_path)]):
        assert run(*argv).returncode == 2, argv
    assert "reading_log.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'reading_log.py')!r})\n"
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
