"""duplicates: the same words in order are a copy, case and punctuation
aside; a word changed is not; short lines and one file's repeats never
count; the newest is named only when it beats every other."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("duplicates", HERE / "duplicates.py")
du = importlib.util.module_from_spec(spec)
spec.loader.exec_module(du)
NOW = ["--now", "2026-10-23T00:00:00Z"]

SAME = "Knead the dough, prove it twice, bake at 230 for Mum."


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


def pile_of(**files: str) -> list[dict]:
    return [{"path": name, "line": 1, "text": text} for name, text in files.items()]


def test_case_punctuation_and_spacing_aside_nothing_else_forgiven():
    other = "knead the dough  prove it twice,\nbake at 230 for mum!"
    same = pile_of(**{"a.md": SAME, "b.md": other})
    assert len(du.copies_of(same)) == 1
    changed = pile_of(**{"a.md": SAME, "b.md": SAME.replace("twice", "once")})
    assert du.copies_of(changed) == [], "a word changed is another passage"


def test_short_lines_and_one_files_repeats_never_count():
    short = pile_of(**{"a.md": "see the note above", "b.md": "See the note above."})
    assert du.copies_of(short) == []
    one = [{"path": "log.md", "line": 1, "text": SAME},
           {"path": "log.md", "line": 9, "text": SAME}]  # fmt: skip
    assert du.copies_of(one) == [], "one file's repeats are the file's business"
    both = one + [{"path": "b.md", "line": 2, "text": SAME}]
    assert [len(g) for g in du.copies_of(both)] == [3], (
        "spanning two files, every copy is listed, the same file's too"
    )


def test_the_newest_is_named_only_when_it_beats_every_other(tmp_path):
    b = box(tmp_path, {
        "garden/2026-05-02.md": f"{SAME}\n",
        "garden/2024-04-01.md": f"{SAME}\n",
    })  # fmt: skip
    got = run(str(HERE / "duplicates.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0] == "2 copies, newer garden/2026-05-02.md:1"
    assert lines[1].startswith("  2026-05-02") and "garden/2026-05-02.md:1" in lines[1]
    assert lines[2].startswith("  2024-04-01")
    assert lines[3] == "1 passage said in two or more files, 2 copies in all"


def test_tied_days_and_an_undated_newest_leave_it_unsaid():
    tied = pile_of(**{"a/2026-05-02.md": SAME, "b/2026-05-02.md": SAME})
    rows = du.copies_of(tied)[0]
    assert du.newer(rows) is None
    dated = f"2024-01-01 {SAME}"
    undated = pile_of(**{"a.md": dated, "b.md": dated})
    rows = du.copies_of(undated)[0]
    assert rows[0]["when"] == "20240101", "the date a copy says is its date"
    assert du.newer(rows) is None, "both say the same day"
    one = pile_of(**{"a.md": SAME, "b/2024-01-01.md": SAME})
    assert du.newer(du.copies_of(one)[0]) == "b/2024-01-01.md:1", "one date beats none"
    none = pile_of(**{"a.md": SAME, "b.md": SAME})
    assert du.newer(du.copies_of(none)[0]) is None


def test_a_copys_date_falls_back_to_its_files_name():
    p = pile_of(**{"letters/2026-03-10.md": SAME, "old.md": SAME})
    rows = du.copies_of(p)[0]
    assert rows[0]["when"] == "20260310" and rows[0]["path"].startswith("letters")


def test_copy_lines_are_cut_at_100_characters_and_whitespace_folded():
    long = SAME + " " + "x" * 300
    p = pile_of(**{"a.md": long.replace(" ", "\n", 3), "b.md": long})
    shown = du.show(du.copies_of(p))
    text = shown[1].split("  ")[-1]
    assert len(text) == 100 and "\n" not in text


def test_nothing_doubled_is_42_and_the_same_folder_gives_the_same_bytes(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "duplicates.py"), "--box", str(b))
    assert got.returncode == 42 and "No passage" in got.stdout
    b2 = box(tmp_path / "again", {"a.md": SAME + "\n", "b.md": SAME + "\n"})
    one = run(str(HERE / "duplicates.py"), "--box", str(b2)).stdout
    assert one == run(str(HERE / "duplicates.py"), "--box", str(b2)).stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "duplicates.py"))
    assert got.returncode == 2 and "duplicates.py" in got.stderr
    got = run(str(HERE / "duplicates.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
