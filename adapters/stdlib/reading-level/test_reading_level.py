"""reading-level: Flesch by the book, sentences as written, syllables by
rule of thumb, and a file too short to score listed, never scored."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location(
    "reading_level", HERE / "reading_level.py"
)
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)
NOW = ["--now", "2026-10-23T00:00:00Z"]

EASY = ("The cat sat on the mat. The dog lay by the door. We ate our bread. "
        "The sun was out all day. A bird sang in the tree. The milk was cold. "
        "We went to bed at nine. The rain came in the night.")  # fmt: skip
HARD = ("Notwithstanding the aforementioned considerations, the undersigned "
        "beneficiary acknowledges comprehensive responsibility regarding "
        "collateral documentation obligations throughout the administration "
        "period, including supplementary verification requirements imposed "
        "unilaterally by participating institutional representatives, whose "
        "determinations remain conclusively authoritative notwithstanding "
        "subsequent administrative reconsideration.")  # fmt: skip


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


def test_syllables_by_rule_of_thumb():
    assert rl.syllables("cat") == 1
    assert rl.syllables("making") == 2
    assert rl.syllables("piece") == 1, "a silent final e is taken off"
    assert rl.syllables("table") == 2, "but -le keeps its syllable"
    assert rl.syllables("rhythm") == 1, "never fewer than one"
    assert rl.syllables("don't") == 1, "the apostrophe splits no word"
    assert rl.syllables("beautiful") == 3


def test_sentences_end_at_punctuation_or_the_lines_end():
    assert rl.sentences("The cat sat. The dog lay!") == 2
    assert rl.sentences("buy milk\nring the bank\n") == 2, "a list reads as items"
    assert rl.sentences("Done... or not?") == 2, "a run of stops is one end"
    assert rl.sentences("\n\n...\n") == 0, "no words, no sentence"


def test_flesch_by_the_book():
    score, wps, spw, n = rl.measure("The cat sat on the mat.")
    assert (score, wps, n) == (116, 6.0, 6) and spw == 1.0
    assert rl.measure(EASY)[0] > 90 > rl.measure(HARD)[0]
    assert rl.measure(HARD)[0] < 30, "legalese reads very hard"


def test_each_band_at_its_floor():
    assert [rl.band(s) for s in (90, 89, 80, 70, 60, 50, 30, 29)] == [
        "very easy", "easy", "easy", "fairly easy", "plain", "fairly hard",
        "hard", "very hard"]  # fmt: skip


def test_rows_come_easiest_first_and_a_short_file_is_listed_not_scored(tmp_path):
    b = box(tmp_path, {"hard.txt": HARD, "easy.txt": EASY, "note.md": "ring Ana\n"})
    got = run(str(HERE / "reading_level.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and len(lines) == 4
    assert "very easy" in lines[0] and lines[0].endswith("easy.txt")
    assert "very hard" in lines[1] and lines[1].endswith("hard.txt")
    assert lines[2] == "too short to score (2 words)  note.md"
    assert lines[3] == "2 files scored, 1 too short"


def test_a_files_passages_are_scored_together_and_a_bare_number_is_no_word():
    pile = [{"path": "a.md", "line": 1, "text": EASY},
            {"path": "a.md", "line": 9, "text": EASY}]  # fmt: skip
    scored, short = rl.rows(pile)
    assert short == [] and len(scored) == 1
    assert scored[0][3] == 2 * rl.measure(EASY)[3], "both passages counted"
    assert rl.measure("paid 450 on time")[3] == 3


def test_the_thirty_word_floor_exactly():
    one_word_sentences = "word. " * 29
    scored, short = rl.rows([{"path": "a.md", "line": 1, "text": one_word_sentences}])
    assert scored == [] and short == [(29, "a.md")]
    scored, short = rl.rows([{"path": "a.md", "line": 1, "text": "word. " * 30}])
    assert short == [] and len(scored) == 1


def test_nothing_long_enough_is_42_and_the_same_folder_gives_the_same_bytes(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "reading_level.py"), "--box", str(b))
    assert got.returncode == 42 and "Nothing long enough" in got.stdout
    b2 = box(tmp_path / "again", {"easy.txt": EASY})
    one = run(str(HERE / "reading_level.py"), "--box", str(b2)).stdout
    assert one == run(str(HERE / "reading_level.py"), "--box", str(b2)).stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "reading_level.py"))
    assert got.returncode == 2 and "reading_level.py" in got.stderr
    got = run(str(HERE / "reading_level.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
