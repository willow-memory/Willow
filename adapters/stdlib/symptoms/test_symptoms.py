"""symptoms: a diary line itself names the symptom, a turn is marked only
where the line says one, and nothing is averaged, trended or diagnosed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("symptoms", HERE / "symptoms.py")
sy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sy)
NOW = ["--now", "2026-10-23T00:00:00Z"]


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


def test_a_turn_is_marked_only_where_the_line_says_one():
    assert sy.turn_of("Knee bad on the stairs.") == "worse"
    assert sy.turn_of("knee held up on the loop") == "better"
    assert sy.turn_of("knee worse in the morning, better by noon") == "mixed"
    assert sy.turn_of("physio said pain 5/10 after stairs") == "5/10"
    assert sy.turn_of("worse again, maybe 7/10") == "worse", "a word outranks a score"
    assert sy.turn_of("saw Dr Tolley about the knee") == ""
    assert sy.turn_of("the test came back 8/100") == "", "a score is out of ten"


def test_the_line_itself_names_the_symptom_and_plain_forms_count():
    pile = [{"path": "knee/notes.md", "line": 1,
             "text": "the stairs again\n2026-01-02 knees aching on the hill\n"}]  # fmt: skip
    rows = sy.diary(pile, {"knee"}, {})
    assert [r["line"] for r in rows] == [2], "a folder's name writes no diary line"
    assert rows[0]["turn"] == ""
    assert sy.diary(pile, {"knee", "hill"}, {})
    assert sy.diary(pile, {"knee", "stairs"}, {}) == [], "every word, one line"


def test_a_words_list_reading_counts():
    pile = [{"path": "a.md", "line": 1, "text": "2026-01-02 genunchiul again\n"}]
    assert sy.diary(pile, {"knee"}, {"knee": ["genunchiul"]})
    assert sy.diary(pile, {"knee"}, {}) == []


def test_the_diary_is_dated_as_the_files_say_oldest_first(tmp_path):
    b = box(tmp_path, {
        "Daily/2026-03-04.md": "Walked the loop, knee held up.\n",
        "Daily/2026-03-01.md": "Knee bad on the stairs.\n",
        "health.md": "2026-02-01 physio\nknee pain 5/10 after the stairs test\n",
        "old.md": "knee twinged at the market\n",
    })  # fmt: skip
    got = run(str(HERE / "symptoms.py"), "--box", str(b), "knee")
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("2026-02-01  5/10") and "(date from line 1)" in lines[0]
    assert (
        lines[1].startswith("2026-03-01  worse") and "(date from file name)" in lines[1]
    )
    assert lines[2].startswith("2026-03-04  better")
    assert lines[3].startswith("undated") and "old.md:1" in lines[3]
    assert lines[4] == ('4 lines name "knee", 2026-02-01 to 2026-03-04:'
                        " 1 worse, 1 better, 1 scored")  # fmt: skip
    assert got.stdout == run(str(HERE / "symptoms.py"), "--box", str(b), "knee").stdout


def test_one_line_and_no_dated_lines_read_right():
    rows = sy.diary([{"path": "a.md", "line": 1, "text": "knee sore\n"}], {"knee"}, {})
    shown = sy.show("knee", rows)
    assert shown[-1] == '1 line names "knee": 0 worse, 0 better, 0 scored'


def test_never_named_and_only_common_words_escalate(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "symptoms.py"), "--box", str(b), "knee")
    assert got.returncode == 42 and 'names "knee"' in got.stdout
    got = run(str(HERE / "symptoms.py"), "--box", str(b), "the of")
    assert got.returncode == 42 and "only common words" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "symptoms.py"))
    assert got.returncode == 2 and "symptoms.py" in got.stderr
    got = run(str(HERE / "symptoms.py"), "--box", str(tmp_path / "b"), "knee", "hip")
    assert got.returncode == 2, "one symptom at a time"
    got = run(str(HERE / "symptoms.py"), "--box", str(tmp_path), "knee")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
