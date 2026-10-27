"""daily-word: the same folder asks the same word on the same day, marking
spends each answer letter once with greens first, the folder is the
dictionary, and the word shows only when the day is done."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("daily_word", HERE / "daily_word.py")
dw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dw)
NOW = ["--now", "2026-10-23T00:00:00Z"]

TEXT = "The crane and the frame and the flame stood on the bench by the geese.\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, text: str = TEXT) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    (pile / "notes.md").write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def play(b: Path, *args: str, now: str = "2026-10-23T00:00:00Z"):
    return run(str(HERE / "daily_word.py"), "--box", str(b), *args, "--now", now)


def test_the_same_folder_asks_the_same_word_and_another_day_another_word():
    words = dw.field([{"path": "a.md", "line": 1, "text": TEXT}])
    assert words == ["bench", "crane", "flame", "frame", "geese", "stood"]
    one = dw.word_of("2026-10-23", words)
    assert one == dw.word_of("2026-10-23", words), "the same day, the same word"
    assert one in words
    days = {dw.word_of(f"2026-11-{d:02}", words) for d in range(1, 15)}
    assert len(days) > 1, "the word moves with the day"


def test_marking_spends_each_answer_letter_once_greens_first():
    assert dw.marks("flame", "flame") == "GGGGG"
    assert dw.marks("crane", "flame") == "..G.G"
    assert dw.marks("bench", "crane") == ".yyy."
    assert dw.marks("eeeee", "geese") == ".GG.G", "greens first, then nothing left"
    assert dw.marks("eeeee", "crane") == "....G", "a letter the answer has once"
    assert dw.marks("geese", "flame") == "....G"
    assert dw.marks("stood", "bench") == "....."


def test_a_days_play_on_the_record(tmp_path):
    b = box(tmp_path)
    words = dw.field([{"path": "notes.md", "line": 1, "text": TEXT}])
    answer = dw.word_of("2026-10-23", words)
    got = play(b, "today")
    assert got.returncode == 0 and "No guesses yet today; 6 left." in got.stdout
    wrong = next(w for w in words if w != answer)
    got = play(b, "guess", wrong)
    assert got.returncode == 0 and "5 guesses left." in got.stdout
    assert answer not in got.stdout, "the word is not shown while the day is open"
    got = play(b, "guess", answer)
    assert got.returncode == 0 and "Solved in 2. Back tomorrow." in got.stdout
    got = play(b, "guess", wrong)
    assert got.returncode == 42, "the day is done"
    got = play(b, "today")
    assert got.returncode == 0 and "Solved in 2" in got.stdout
    nxt = play(b, "today", now="2026-10-24T00:00:00Z")
    assert "No guesses yet today" in nxt.stdout, "a new day starts clean"


def test_six_misses_end_the_day_and_show_the_word(tmp_path):
    b = box(tmp_path)
    words = dw.field([{"path": "notes.md", "line": 1, "text": TEXT}])
    answer = dw.word_of("2026-10-23", words)
    wrong = [w for w in words if w != answer]
    for i in range(6):
        got = play(b, "guess", wrong[i % len(wrong)])
    assert f"Out of guesses. The word was {answer}." in got.stdout
    got = play(b, "guess", wrong[0])
    assert got.returncode == 42 and answer in got.stdout


def test_the_folder_is_the_dictionary_and_a_miss_there_costs_no_guess(tmp_path):
    b = box(tmp_path)
    got = play(b, "guess", "zzzzz")
    assert got.returncode == 2 and "costs no guess" in got.stderr
    got = play(b, "guess", "cranes")
    assert got.returncode == 2 and "one five-letter word" in got.stderr
    got = play(b, "today")
    assert "No guesses yet today; 6 left." in got.stdout


def test_a_folder_with_no_five_letter_words_escalates(tmp_path):
    b = box(tmp_path, text="Tomatoes want sun.\n")
    got = play(b, "today")
    assert got.returncode == 42 and "no five-letter words" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "daily_word.py"))
    assert got.returncode == 2 and "daily_word.py" in got.stderr
    got = run(str(HERE / "daily_word.py"), "--box", str(tmp_path), "today", *NOW)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    b = box(tmp_path)
    got = play(b, "today", "--stray")
    assert got.returncode == 2 and "daily_word.py" in got.stderr
