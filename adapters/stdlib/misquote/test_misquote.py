"""misquote: the passage nearest a quote, and the words it drops, adds or
changes; as written when it's there, nothing close when under half."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import misquote  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "misquote.py"
POLICY = (
    "We don't show you personalized ads based on your content from Drive, Gmail,\n"
    "or Google Photos, unless you choose to make data available.\n\n"
    "The council met on Tuesday and approved the budget.\n\n"
    "The council met on Tuesday, and after a long debate about the library, approved it.\n"
)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "policy.txt").write_text(POLICY)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-24T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(b: Path, quote: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(b), quote],
                          capture_output=True, text=True)  # fmt: skip


def test_a_dropped_word_is_named_as_the_file_spells_it(tmp_path):
    got = run(box(tmp_path), "We don't show you personalized ads based on your content "
                             "from Drive, Gmail, or Photos, unless you choose")  # fmt: skip
    assert got.returncode == 42
    lines = got.stdout.splitlines()
    assert (
        lines[0] == "closest      policy.txt:1   (19 of 19 words, in order)"
    )  # don't is two
    assert lines[1].split()[:2] == ["dropped", "Google"]  # the file's capital
    assert len(lines) == 2


def test_added_and_changed_words(tmp_path):
    got = run(
        box(tmp_path), "The council met on Monday and quietly approved the budget"
    )
    lines = got.stdout.splitlines()
    assert got.returncode == 42
    assert lines[0].startswith("closest      policy.txt:4   (8 of 10 words")
    assert lines[1].split()[:4] == ["changed", "Monday", "->", "Tuesday"]
    assert lines[2].split()[:2] == ["added", "quietly"]


def test_the_shorter_stretch_wins_a_tie(tmp_path):
    got = run(box(tmp_path), "The council met on Tuesday approved")
    assert "policy.txt:4" in got.stdout  # 6 of 6 in a stretch of 7, not of 17


def test_as_written_when_the_words_are_there_in_order(tmp_path):
    b = box(tmp_path)
    got = run(b, "drive gmail or GOOGLE photos!")
    assert got.returncode == 0 and got.stdout == "as written   policy.txt:1\n"


def test_nothing_close_under_half(tmp_path):
    b = box(tmp_path)
    got = run(b, "Google scans every Gmail message to serve ads")
    assert got.returncode == 42 and got.stdout.startswith("Nothing in your folder")
    # exactly half is close: 3 of 6 words in order
    assert run(b, "council met on zz yy xx").stdout.startswith("closest")


def test_refusals(tmp_path):
    b = box(tmp_path)
    assert run(b, "...").returncode == 2
    assert run(tmp_path, "the council").returncode == 2
    got = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert got.returncode == 2 and "misquote.py" in got.stderr


def test_closest_reads_passages_directly():
    pile = [{"path": "a.txt", "line": 1, "text": "one two three four"}]
    c, kept, diffs = misquote.closest(pile, "one two five four")
    assert kept == 3 and diffs == [("changed", ["five"], ["three"])]
    assert misquote.closest(pile, "six seven eight") is None
    assert misquote.closest(pile, "one two")[2] == []
