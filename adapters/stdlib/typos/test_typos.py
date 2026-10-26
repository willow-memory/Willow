"""typos: a word no file holds read as the files spell it, one edit inside it,
the most-held spelling first; printed for the person to ask, never asked for
them, and nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "typos.py"
spec = importlib.util.spec_from_file_location("typos", SCRIPT)
ty = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ty)
NOW = ["--now", "2026-10-25T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "ring.md").write_text(
        "The jeweller says the claws need retipping.\n\n"
        "Sturt St jeweller, open Saturdays.\n\n"
        "Referral letter from Dr Tolley to the dermatologist.\n"
    )
    (pile / "money.md").write_text("Dev lent me 350 for the boiler.\n")
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b),
                          "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_a_misspelt_word_is_read_as_the_files_spell_it(box):
    got = run("--box", str(box), "what did the jeweler say")
    assert got.returncode == 0
    assert got.stdout.splitlines() == [
        "read jeweler as jeweller: 2 passages hold it",
        "ask:  what did the jeweller say",
    ]


def test_each_misspelt_word_of_a_question_is_read(box):
    got = run("--box", str(box), "dermatoligist referal letter")
    assert "read dermatoligist as dermatologist: 1 passage holds it" in got.stdout
    assert "read referal as referral: 1 passage holds it" in got.stdout
    assert got.stdout.endswith("ask:  dermatologist referral letter\n")


def test_it_never_asks_for_you_and_writes_nothing(box):
    before = (box / "record.jsonl").read_bytes()
    files = sorted(box.rglob("*"))
    run("--box", str(box), "what did the jeweler say")
    assert (box / "record.jsonl").read_bytes() == before, "no bite, no row"
    assert sorted(box.rglob("*")) == files


def test_a_word_spelt_right_but_not_in_your_files_is_said_not_changed(box):
    got = run("--box", str(box), "how much do I owe dev")
    assert got.returncode == 42 and got.stdout == (
        "no file has owe, nor anything one edit from it\n"
    )
    assert "ask:" not in got.stdout


def test_held_words_are_left_alone(box):
    got = run("--box", str(box), "the jeweller")
    assert got.returncode == 0 and got.stdout.startswith("Your files hold every word")


def test_a_words_list_reading_counts_as_held(box, tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("jewler = jeweller\n")
    words.chmod(0o600)
    cfg = box / "kernel.json"
    cfg.write_text(cfg.read_text().replace("}", f', "words": "{words}"}}'))
    got = run("--box", str(box), "jewler")
    assert got.returncode == 0 and got.stdout.startswith("Your files hold every word")


@pytest.mark.parametrize("word, reading", [
    ("jeweler", "jeweller"),          # a letter added
    ("jewelller", "jeweller"),        # a letter dropped
    ("jewaller", "jeweller"),         # a letter changed
    ("jeewller", "jeweller"),         # two side by side swapped
])  # fmt: skip
def test_one_edit_inside_the_word_each_way(word, reading):
    pile = [{"path": "a.md", "text": "the jeweller"}]
    assert ty.readings(word, pile, {})[0] == {word: (reading, 1)}


@pytest.mark.parametrize("word", [
    "hjeweller",   # its first letter would change
    "jewellerz",   # its last letter would change
    "gave",        # too short: "give" is another word, not a slip
    "jeweĺler",    # a letter outside a to z: the accents add-on's
])  # fmt: skip
def test_what_is_never_read_differently(word):
    pile = [{"path": "a.md", "text": "the jeweller gives"}]
    assert ty.readings(word, pile, {})[0] == {}


def test_the_most_held_spelling_wins_and_a_tie_goes_alphabetical():
    pile = [
        {"path": "a.md", "text": "carton"},
        {"path": "a.md", "text": "carton"},
        {"path": "a.md", "text": "cartoon"},
    ]
    assert ty.readings("cartoan", pile, {})[0] == {"cartoan": ("carton", 2)}
    pile = [{"path": "a.md", "text": "carton"}, {"path": "a.md", "text": "cartoon"}]
    assert ty.readings("cartoan", pile, {})[0] == {"cartoan": ("carton", 1)}


def test_a_bad_command_line_or_box_is_refused(tmp_path, box):
    for argv in ([], ["--box"], ["--box", str(box)], ["--box", str(box), "a", "b"],
                 ["--box", str(box), "--now"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "typos.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path), "x").stderr
    assert "no words" in run("--box", str(box), "?!").stderr
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"boot"', '"booted"', 1))
    got = run("--box", str(box), "jeweler")
    assert got.returncode == 2 and "chain broken" in got.stderr
