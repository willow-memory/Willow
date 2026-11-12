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


TEXT = (
    "the following winter father was at omaha attending the legislature and "
    "the rest of us stayed on the claim through the cold months until spring"
)  # 25 words


def spread(text: str, per: int) -> str:
    """The same words in paragraphs of `per` words each: the kernel cuts a file
    at its blank lines, so where they fall decides which passages it has."""
    ws = text.split()
    return "\n\n".join(" ".join(ws[i : i + per]) for i in range(0, len(ws), per))


def pile_paras(**files: str) -> list[dict]:
    """A pile cut at blank lines, as the kernel cuts a file into passages."""
    rows = []
    for name, text in files.items():
        line = 1
        for para in text.split("\n\n"):
            rows.append({"path": name, "line": line, "text": para})
            line += para.count("\n") + 2  # its lines, and the blank one after
    return rows


def test_runs_find_a_copy_whose_paragraphs_were_broken_differently():
    pile = pile_paras(**{"a.txt": spread(TEXT, 5), "b.txt": spread(TEXT, 9)})
    got = du.runs_of(pile)
    assert len(got) == 1
    assert [(r["path"], r["line"]) for r in got[0]] == [("a.txt", 1), ("b.txt", 1)]
    assert len(got[0][0]["words"]) == 25
    assert " ".join(got[0][0]["words"]) == TEXT
    assert du.copies_of(pile) == [], (
        "the same text cut into passages two ways never matches"
    )


def test_a_run_ends_where_a_word_changes_and_short_runs_are_not_copies():
    ws = TEXT.split()
    late = ws[:20] + ["CHANGED"] + ws[21:]  # a word changed at the 21st
    got = du.runs_of(pile_of(**{"a.txt": " ".join(ws), "b.txt": " ".join(late)}))
    assert [len(g[0]["words"]) for g in got] == [20]  # the 4 after it are under 8
    mid = ws[:12] + ["CHANGED"] + ws[13:]  # at the 13th: 12 words before, 12 after
    got = du.runs_of(pile_of(**{"a.txt": " ".join(ws), "b.txt": " ".join(mid)}))
    assert sorted(len(g[0]["words"]) for g in got) == [12, 12]
    seven = pile_of(
        **{"a.txt": " ".join(ws[:7]) + " x1", "b.txt": " ".join(ws[:7]) + " y2"}
    )
    assert du.runs_of(seven) == []  # 7 shared words: under the floor of 8
    eight = pile_of(
        **{"a.txt": " ".join(ws[:8]) + " x1", "b.txt": " ".join(ws[:8]) + " y2"}
    )
    assert len(du.runs_of(eight)) == 1 and len(du.runs_of(eight)[0][0]["words"]) == 8


def test_one_files_repeats_are_its_own_unless_another_file_has_them_too():
    twice = pile_of(**{"a.txt": TEXT + "\n\n" + TEXT})
    assert du.runs_of(twice) == []
    three = pile_of(
        **{"a.txt": TEXT + "\n\nbreak of words here\n\n" + TEXT, "b.txt": TEXT}
    )
    got = du.runs_of(three)
    assert len(got) == 1
    assert [r["path"] for r in got[0]] == [
        "a.txt",
        "a.txt",
        "b.txt",
    ]  # every copy listed


def test_a_run_is_cut_where_the_files_that_share_it_change():
    """c.txt holds all of TEXT; a.txt holds all of it, b.txt only the first half:
    the first 15 words are a run of three copies, the last 17 a run of two (the
    two overlap by the 7 words the window that changes the sharing spans)."""
    ws = TEXT.split()
    pile = pile_of(
        **{"a.txt": TEXT, "b.txt": " ".join(ws[:15]) + " zz1 zz2", "c.txt": TEXT}
    )
    got = sorted(du.runs_of(pile), key=lambda g: len(g[0]["words"]))
    assert [(len(g[0]["words"]), [r["path"] for r in g]) for g in got] == [
        (15, ["a.txt", "b.txt", "c.txt"]),
        (17, ["a.txt", "c.txt"]),
    ]


def test_runs_are_a_flag_of_box_and_the_default_is_unchanged(tmp_path):
    b = box(tmp_path, {"a.txt": spread(TEXT, 5), "b.txt": spread(TEXT, 9)})
    default = run(str(HERE / "duplicates.py"), "--box", str(b))
    assert default.returncode == 42 and "No passage of 8 words" in default.stdout
    runs = run(str(HERE / "duplicates.py"), "--box", str(b), "--runs")
    assert runs.returncode == 0
    assert runs.stdout.splitlines()[0] == "2 copies of a run of 25 words"
    assert runs.stdout.splitlines()[1].startswith("  a.txt:1  ")
    assert runs.stdout.splitlines()[2].startswith("  b.txt:1  ")
    assert (
        runs.stdout.splitlines()[-1]
        == "1 run said in two or more files, 2 copies in all"
    )
    none = box(tmp_path / "n", {"a.txt": TEXT, "b.txt": "nothing at all alike in here"})
    got = run(str(HERE / "duplicates.py"), "--box", str(none), "--runs")
    assert got.returncode == 42 and "No run of 8 words or more" in got.stdout
    assert run(str(HERE / "duplicates.py"), "--runs").returncode == 2  # no box
