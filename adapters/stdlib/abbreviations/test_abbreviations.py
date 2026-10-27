"""abbreviations: an unheld word is read as the table's other form where the
files hold one, both ways round; `lines` writes what the files write only
one way, to FILE and nowhere else."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location(
    "abbreviations", HERE / "abbreviations.py"
)
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)
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


def pile_of(**files: str) -> list[dict]:
    return [{"path": name, "line": 1, "text": text} for name, text in files.items()]


def test_a_question_word_is_read_both_ways_round(tmp_path):
    b = box(tmp_path, {"diary.md": "Dentist appt at ten.\n\nMoved the appt to two.\n"})
    got = run(str(HERE / "abbreviations.py"), "--box", str(b),
              "when is the appointment")  # fmt: skip
    assert got.returncode == 0
    assert "read appointment as appt: 2 passages hold it" in got.stdout
    assert "ask:  when is the appt" in got.stdout
    b2 = box(tmp_path / "b2", {"diary.md": "Dentist appointment at ten.\n"})
    got = run(str(HERE / "abbreviations.py"), "--box", str(b2), "move the appt")
    assert "read appt as appointment: 1 passage holds it" in got.stdout


def test_the_most_held_form_wins_and_a_held_word_is_left_alone():
    pile = pile_of(a="Church Street corner.", b="Mill Street here.", c="Saint Brigid.")
    read, missing = ab.readings("the st fair", pile, {})
    assert read["st"] == ("street", 2) and missing == ["fair"]
    held = pile_of(a="the appt is Tuesday")
    read, missing = ab.readings("appt tuesday", held, {})
    assert read == {} and missing == [], "a word the files hold needs no reading"


def test_a_word_the_words_list_already_reads_is_left_alone():
    pile = pile_of(a="the booking is Tuesday")
    read, missing = ab.readings("appt", pile, {"appt": ["booking"]})
    assert read == {} and missing == []


def test_a_word_nothing_covers_escalates(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "abbreviations.py"), "--box", str(b), "zzqq tomatoes")
    assert got.returncode == 42
    assert "no file has zzqq, written out or short" in got.stdout


def test_lines_cover_each_way_the_files_write_only_one():
    pile = pile_of(a="appt at ten", b="every thursday", c="appt again")
    assert ab.words_lines(pile) == ["appointment = appt", "thurs = thursday"]
    both = pile_of(a="appt and appointment together")
    assert ab.words_lines(both) == [], "files holding both ways need no line"
    plural = pile_of(a="two appts booked")
    assert ab.words_lines(plural) == ["appointment = appt"], "a plural still holds"


def test_lines_are_written_to_file_and_nowhere_else(tmp_path):
    b = box(tmp_path, {"diary.md": "appt at ten\n"})
    to = tmp_path / "lines.txt"
    got = run(str(HERE / "abbreviations.py"), "lines", "--box", str(b), "--to", str(to))
    assert got.returncode == 0 and "wrote 1 words-list line" in got.stdout
    assert to.read_text() == "appointment = appt\n"
    assert to.stat().st_mode & 0o777 == 0o600, "readable only by you"
    got = run(str(HERE / "abbreviations.py"), "lines", "--box", str(b), "--to", str(to))
    assert got.returncode == 2 and not got.stdout, "never over a file that exists"
    inside = tmp_path / "pile" / "w.txt"
    got = run(str(HERE / "abbreviations.py"), "lines", "--box", str(b),
              "--to", str(inside))  # fmt: skip
    assert got.returncode == 2 and "inside your folder" in got.stderr
    assert not inside.exists()


def test_no_shorthand_in_the_files_writes_nothing(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    to = tmp_path / "lines.txt"
    got = run(str(HERE / "abbreviations.py"), "lines", "--box", str(b), "--to", str(to))
    assert got.returncode == 42 and not to.exists()


def test_a_words_list_that_cannot_be_read_refuses_the_question(tmp_path):
    import os

    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "diary.md").write_text("appt at ten\n")
    wl = tmp_path / "words.txt"
    wl.write_text("mum = margaret\n")
    os.chmod(wl, 0o600)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), "--words", str(wl), *NOW)  # fmt: skip
    wl.write_text("two words = broken\n")
    got = run(str(HERE / "abbreviations.py"), "--box", str(b), "appointment")
    assert got.returncode == 2 and got.stderr.startswith("refused")


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "abbreviations.py"))
    assert got.returncode == 2 and "abbreviations.py" in got.stderr
    got = run(str(HERE / "abbreviations.py"), "lines", "--box", str(tmp_path / "b"))
    assert got.returncode == 2, "lines needs --to"
    got = run(str(HERE / "abbreviations.py"), "--box", str(tmp_path / "b"),
              "--to", str(tmp_path / "x"), "appt")  # fmt: skip
    assert got.returncode == 2, "a question takes no --to"
    got = run(str(HERE / "abbreviations.py"), "--box", str(tmp_path), "appt")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
