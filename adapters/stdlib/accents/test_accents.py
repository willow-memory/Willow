"""accents: a word no file holds read as the files write it, accents off both
sides; offered, never asked; and the words-list lines that make it lasting;
nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "accents.py"
spec = importlib.util.spec_from_file_location("accents", SCRIPT)
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)
NOW = ["--now", "2026-10-25T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "town.md").write_text(
        "Coffee at the café on Sjøgata with Zoë.\n\nThe café shuts at four.\n\n"
        "Zoë's cafe card is in the drawer.\n"
    )
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b),
                          "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_a_word_typed_without_its_accent_is_read_as_the_files_write_it(box):
    got = run("--box", str(box), "where is zoe")
    assert got.returncode == 0 and got.stdout.splitlines() == [
        "read zoe as zoë: 2 passages hold it",
        "ask:  where is zoë",
    ]


def test_it_works_both_ways_and_with_letters_unicode_wont_split(box):
    assert "read sjogata as sjøgata" in run("--box", str(box), "sjogata").stdout
    pile = [{"path": "a.md", "text": "cafe"}]
    assert ac.readings("café", pile, {})[0] == {"café": ("cafe", 1)}
    assert ac.bare("straße") == "strasse" and ac.bare("ærø") == "aero"


def test_a_word_held_as_typed_is_left_alone(box):
    got = run("--box", str(box), "cafe card")
    assert got.returncode == 0 and got.stdout.startswith("Your files hold every word")


def test_a_word_no_file_has_either_way_is_said(box):
    got = run("--box", str(box), "bakery")
    assert got.returncode == 42
    assert got.stdout == "no file has bakery, with its accents or without\n"


def test_the_most_held_way_wins_and_a_tie_goes_to_the_first_sorted():
    pile = [{"path": "a.md", "text": "rené"}, {"path": "b.md", "text": "rené"},
            {"path": "c.md", "text": "renè"}]  # fmt: skip
    assert ac.readings("rene", pile, {})[0] == {"rene": ("rené", 2)}
    pile = [{"path": "a.md", "text": "rené"}, {"path": "b.md", "text": "renè"}]
    assert ac.readings("rene", pile, {})[0] == {"rene": ("renè", 1)}  # è < é


def test_words_prints_the_lines_a_words_list_keeps(box, tmp_path):
    got = run("words", "--box", str(box))
    assert got.returncode == 0
    assert got.stdout.splitlines() == ["cafe = café", "sjogata = sjøgata", "zoe = zoë"]
    words = tmp_path / "words.txt"
    words.write_text(got.stdout)
    words.chmod(0o600)
    cfg = box / "kernel.json"
    cfg.write_text(cfg.read_text().replace("}", f', "words": "{words}"}}'))
    bite = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box),
                           *NOW, "zoe sjogata"], capture_output=True, text=True)  # fmt: skip
    assert bite.returncode == 0, "the kernel reads them now, on its own"
    assert run("--box", str(box), "zoe").stdout.startswith("Your files hold every")


def test_it_writes_nothing(box):
    files = {p: p.read_bytes() for p in box.rglob("*") if p.is_file()}
    run("--box", str(box), "zoe")
    run("words", "--box", str(box))
    assert {p: p.read_bytes() for p in box.rglob("*") if p.is_file()} == files


def test_a_bad_command_line_or_box_is_refused(tmp_path, box):
    for argv in ([], ["--box"], ["--box", str(box)], ["--box", str(box), "a", "b"],
                 ["words", "--box", str(box), "zoe"], ["words"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "accents.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path), "x").stderr
    assert "no words" in run("--box", str(box), "?!").stderr
