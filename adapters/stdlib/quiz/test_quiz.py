"""quiz: the tip cuts the puzzle, the record holds a hash and never the
answer, one quiz is open at a time, and a changed folder marks no one
wrong."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("quiz", HERE / "quiz.py")
qz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qz)
NOW = ["--now", "2026-10-23T00:00:00Z"]

TEXT = "Ferris came by for the frames today. Two supers waiting on the strong hive.\n"


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


def quiz_cmd(b: Path, *args: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "quiz.py"), "--box", str(b), *args, *NOW)


def test_what_can_be_blanked():
    words = "the ferris with for supers s4me tiny supers again".split()
    got = qz.blankable(words)
    assert words.index("ferris") in got and words.index("again") in got
    assert words.index("the") not in got, "a common word blanks nothing"
    assert words.index("tiny") in got
    assert words.index("s4me") not in got, "a digit in a word"
    assert words.index("for") not in got, "too short"
    assert all(words[i] != "supers" for i in got), "a word standing twice"


def test_only_your_own_writing_is_quizzed():
    assert qz.yours("Ferris came by for the frames today, two supers waiting.")
    assert not qz.yours('<html><body style="font-family:arial">hello</body>')
    assert not qz.yours("---\ndate: 2024-03-15\ntags: [daily]\n---\n# Friday")
    assert not qz.yours("DTSTART;VALUE=DATE:20261028\nSUMMARY:Dentist")
    assert not qz.yours("ALL CAPS SHOUTING LINE")
    tip = "0" * 64
    html = [
        {
            "path": "m.eml",
            "line": 1,
            "text": "<p>You have six new hints waiting in the family tree</p>",
        }
    ]
    assert qz.cut(html, tip) is None, "a machine's words carry no quiz"


def test_the_tip_cuts_the_puzzle_and_the_record_never_holds_the_answer(tmp_path):
    b = box(tmp_path, {"hives.txt": TEXT})
    got = quiz_cmd(b, "ask")
    assert got.returncode == 0 and "hives.txt:1" in got.stdout
    assert "_" * 4 in got.stdout, "a blank as long as its word"
    row = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "quiz" and "answer_sha256" in row
    assert row["ts"] == "2026-10-23T00:00:00Z", "the clock given is the clock used"
    text_line = got.stdout.splitlines()[1]
    plain = [w.strip(".,").lower() for w in TEXT.split()]
    missing = [w for w in plain if w not in text_line.lower()]
    assert len(missing) == 1, "exactly one word is blanked"
    assert missing[0] not in json.dumps(row).lower(), (
        "the record holds a hash, never the word"
    )
    assert row["answer_sha256"] != missing[0]
    again = quiz_cmd(b, "ask")
    assert again.stdout.splitlines()[1] == got.stdout.splitlines()[1], (
        "asked again, the open quiz shows byte for byte"
    )
    assert "still open" in again.stdout


def test_a_right_answer_a_wrong_one_and_the_score(tmp_path):
    b = box(tmp_path, {"hives.txt": TEXT})
    asked = quiz_cmd(b, "ask").stdout
    text_line = asked.splitlines()[1]
    plain = [w.strip(".,").lower() for w in TEXT.split()]
    missing = [w for w in plain if w not in text_line.lower()]
    word = missing[0]
    got = quiz_cmd(b, "answer", word.upper())
    assert got.returncode == 0 and f"Right: the word is {word}." in got.stdout
    assert "1 right of 1 answered" in got.stdout
    quiz_cmd(b, "ask")
    got = quiz_cmd(b, "answer", "zzzz")
    assert got.returncode == 0 and "Not it: the word is" in got.stdout
    assert "1 right of 2 answered" in got.stdout


def test_a_new_ask_cuts_a_new_puzzle_from_the_new_tip(tmp_path):
    b = box(tmp_path, {"hives.txt": TEXT})
    one = quiz_cmd(b, "ask").stdout
    row1 = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    quiz_cmd(b, "answer", "zzzz")
    two = quiz_cmd(b, "ask").stdout
    row2 = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert row1["seed"] != row2["seed"], "the tip moved, so the seed moved"
    assert "(row" in one and "(row" in two


def test_a_changed_folder_marks_no_one_wrong(tmp_path):
    b = box(tmp_path, {"hives.txt": TEXT})
    quiz_cmd(b, "ask")
    (tmp_path / "pile" / "hives.txt").write_text(
        "Completely different sentences standing here instead, every single word replaced.\n"
    )
    got = quiz_cmd(b, "answer", "frames")
    assert got.returncode == 0
    assert "your folder has changed under the quiz" in got.stdout
    assert "0 right of 1 answered" in got.stdout
    got = quiz_cmd(b, "ask")
    assert got.returncode == 0, "the answer row closed it; a new quiz cuts"


def test_nothing_to_quiz_and_no_quiz_open_escalate(tmp_path):
    b = box(tmp_path, {"short.md": "Tomatoes want sun.\n"})
    got = quiz_cmd(b, "ask")
    assert got.returncode == 42 and "Nothing to quiz" in got.stdout
    got = quiz_cmd(b, "answer", "sun")
    assert got.returncode == 42 and "No quiz open" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "quiz.py"))
    assert got.returncode == 2 and "quiz.py" in got.stderr
    got = run(str(HERE / "quiz.py"), "--box", str(tmp_path), "ask", *NOW)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    b = box(tmp_path, {"hives.txt": TEXT})
    got = quiz_cmd(b, "ask", "--stray")
    assert got.returncode == 2 and "quiz.py" in got.stderr
    got = quiz_cmd(b, "answer")
    assert got.returncode == 2
