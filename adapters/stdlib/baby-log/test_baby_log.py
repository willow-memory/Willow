"""baby-log: a feed, a sleep or a nappy on a day, the first time on the line,
the last of each, and the newest days counted."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("baby_log", HERE / "baby_log.py")
bl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bl)
NOW = ["--now", "2026-10-23T00:00:00Z"]
SCRIPT = str(HERE / "baby_log.py")


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
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'baby_log.py')!r})\n"
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


def test_the_first_time_on_a_line():
    c = bl.clock
    assert c("07:30 feed") == "07:30"
    assert c("feed at 7.30pm") == "19:30"
    assert c("feed 7:05 am") == "07:05"
    assert c("slept 13:00-14:30") == "13:00"
    assert c("12:15am nappy") == "00:15"
    assert c("12:15pm nappy") == "12:15"
    assert c("feed 24:00") == ""
    assert c("feed 7:60") == ""
    assert c("feed 120ml") == ""
    assert c("feed on 2026-03-02") == ""
    assert c("nappy at 9:30 and 10:15") == "09:30"
    assert c("feed 13:30pm") == "", "pm needs a twelve-hour clock"
    assert c("feed 1.5 oz at 6:45") == "06:45"


def test_a_line_is_the_first_kind_it_names():
    k = bl.kind_of
    assert k("fed 120ml") == "feed"
    assert k("bottle at 7") == "feed"
    assert k("breastfed 10 min") == "feed"
    assert k("slept 2h") == "sleep"
    assert k("nap 13:00") == "sleep"
    assert k("wet nappy") == "nappy"
    assert k("diaper change, poo") == "nappy"
    assert k("fed, then nappy") == "feed"
    assert k("nappy, then fed") == "nappy"
    assert k("slept after the feed") == "sleep"
    assert k("went to the shops") == ""
    assert k("the weekend was fun") == ""


def test_a_line_is_the_babys_only_when_it_or_its_path_says_so():
    pile = [
        {"path": "hives/2026.txt", "line": 1, "text": "2026-10-12 H1 feed syrup\n"},
        {"path": "chats/sam.txt", "line": 1, "text": "2026-10-13 can't sleep\n"},
        {"path": "baby/log.md", "line": 1, "text": "2026-10-14 feed\n"},
        {"path": "notes.md", "line": 1, "text": "2026-10-15 baby slept\n2026-10-16 wet nappy\n2026-10-17 newborn fed\n"},
    ]  # fmt: skip
    got = bl.log(pile)
    assert got == {
        "20261014": [("feed", "")], "20261015": [("sleep", "")],
        "20261016": [("nappy", "")], "20261017": [("feed", "")],
    }  # fmt: skip


def test_the_listing_shows_the_last_of_each_and_the_newest_days(tmp_path):
    b = box(tmp_path, {
        "baby/2026-03-01.md": "06:00 feed 120ml\n09:00 nap\n10:00 nappy\n12:00 fed\n",
        "baby/2026-03-02.md": "07:00 feed\n13:00 slept 13:00-14:30\n14:10 feed\n14:35 nappy\nnappy (no time)\n",
        "baby/2026-02-28.md": "feed\n"})  # fmt: skip
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "last feed    2026-03-02 14:10",
        "last sleep   2026-03-02 13:00",
        "last nappy   2026-03-02 14:35",
        "2026-03-02  feeds 2  sleeps 1  nappies 2",
        "2026-03-01  feeds 2  sleeps 1  nappies 1",
        "2026-02-28  feeds 1  sleeps 0  nappies 0",
        "3 days shown",
    ]
    two = run(SCRIPT, "--box", str(b), "--days", "2").stdout.splitlines()
    assert two[3:] == [
        "2026-03-02  feeds 2  sleeps 1  nappies 2",
        "2026-03-01  feeds 2  sleeps 1  nappies 1",
        "2 days shown",
    ]
    assert run(SCRIPT, "--box", str(b)).stdout == got.stdout


def test_a_last_with_no_time_says_so_and_one_day_is_singular(tmp_path):
    b = box(tmp_path, {"baby/2026-03-02.md": "feed\n"})
    assert run(SCRIPT, "--box", str(b)).stdout.splitlines() == [
        "last feed    2026-03-02 (no time written)",
        "2026-03-02  feeds 1  sleeps 0  nappies 0",
        "1 day shown",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b))
    assert got.returncode == 42 and "a feed, a sleep or a nappy" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--days", "0"],
        ["--box", str(b), "--days", "many"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "baby_log.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
