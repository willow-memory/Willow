"""first-mention: the earliest dated line that itself holds every word, read
the kernel's way; what no date reaches is counted, never placed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location(
    "first_mention", HERE / "first_mention.py"
)
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)
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


def ask(b: Path, words: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "first_mention.py"), "--box", str(b), words)


def test_the_earliest_dated_line_wins_across_files(tmp_path):
    b = box(tmp_path, {
        "diary.md": "2026-03-09 wrote to the landlord about the mould\n",
        "tenancy/log.md": "2026-03-01 reported the mould upstairs\n",
    })  # fmt: skip
    got = ask(b, "mould")
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0] == 'first mention of "mould": 2026-03-01'
    assert lines[1] == "  tenancy/log.md:1  2026-03-01 reported the mould upstairs"
    assert lines[2] == "2 mentions in 2 files, 2026-03-01 to 2026-03-09"


def test_a_mention_is_written_in_the_line_not_its_files_name(tmp_path):
    b = box(tmp_path, {"mould/notes.md": "the fan helps\n2026-01-02 mould is back\n"})
    got = ask(b, "mould")
    assert "notes.md:2" in got.stdout and "1 mention in 1 file" in got.stdout


def test_a_words_plain_form_counts_and_every_word_must_share_the_line():
    pile = [{"path": "a.md", "line": 1,
             "text": "2026-01-01 Dev owed me for June\nthe knee again\nknee physio at 2pm\n"}]  # fmt: skip
    assert [r["line"] for r in fm.mentions(pile, {"owes"}, {})] == [1]
    assert [r["line"] for r in fm.mentions(pile, {"knee", "physio"}, {})] == [3]


def test_a_words_list_reading_counts_as_the_word():
    pile = [{"path": "a.md", "line": 1, "text": "tea with Margaret\n"}]
    assert fm.mentions(pile, {"mum"}, {"mum": ["margaret"]})
    assert not fm.mentions(pile, {"mum"}, {})


def test_dated_from_the_line_above_or_the_file_name_each_saying_so(tmp_path):
    b = box(tmp_path, {"log/2026-04-02.txt": "called about the roof\n"})
    got = ask(b, "roof")
    assert 'first mention of "roof": 2026-04-02  (date from file name)' in got.stdout
    b2 = box(tmp_path / "b2", {"log.md": "2026-02-03 a slow day\nroof leak worse\n"})
    got = ask(b2, "roof")
    assert 'first mention of "roof": 2026-02-03  (date from line 1)' in got.stdout


def test_undated_mentions_are_counted_beside_the_answer_never_placed(tmp_path):
    b = box(tmp_path, {
        "old.md": "the roof needs looking at\n",
        "log.md": "2026-02-03 roof quote came in\n",
    })  # fmt: skip
    out = ask(b, "roof").stdout
    assert 'first mention of "roof": 2026-02-03' in out
    assert "2 mentions in 2 files, 2026-02-03; 1 undated, which could be earlier" in out


def test_no_mention_is_dated_and_the_first_by_file_and_line_says_so(tmp_path):
    b = box(tmp_path, {"b.md": "roof again\n", "a.md": "the roof, still\n"})
    got = ask(b, "roof")
    assert got.returncode == 0
    assert 'first mention of "roof": undated' in got.stdout
    assert "a.md:1" in got.stdout and "2 mentions in 2 files, none dated" in got.stdout


def test_a_long_line_is_cut_at_120_characters():
    text = "2026-01-01 roof " + "x" * 300
    found = fm.mentions([{"path": "a.md", "line": 1, "text": text}], {"roof"}, {})
    got = fm.answer("roof", found)
    assert got.splitlines()[1].endswith(text[:120]) and text[:121] not in got


def test_never_mentioned_and_only_common_words_both_escalate(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = ask(b, "mould")
    assert got.returncode == 42 and "never mention" in got.stdout
    got = ask(b, "the of and")
    assert got.returncode == 42 and "only common words" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "first_mention.py"))
    assert got.returncode == 2 and "first_mention.py" in got.stderr
    got = run(str(HERE / "first_mention.py"), "--box", str(tmp_path), "roof")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
