"""quotes: each quotation in a document checked against the folder: as
written, almost (with what differs), or not there; a summary; exit 0 only
when every quote holds."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quotes  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "quotes.py"
POLICY = (
    "We don't show you personalized ads based on your content from Drive, Gmail,\n"
    "or Google Photos, unless you choose to make data available.\n\n"
    "The council met on Tuesday and approved the budget.\n"
)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "policy.txt").write_text(POLICY)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-11-01T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(b: Path, doc: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(b), "--in", str(doc)],
                          capture_output=True, text=True)  # fmt: skip


def write(tmp_path: Path, text: str) -> Path:
    doc = tmp_path / "report.md"
    doc.write_text(text)
    return doc


def test_each_quote_gets_its_verdict_and_a_summary(tmp_path):
    doc = write(tmp_path, 'It says "We don\'t show you personalized ads based on your content".\n'
                          'Minutes: "The council met on Monday and approved the budget".\n'
                          'And "We sell nothing to anyone, ever, at all".\n')  # fmt: skip
    got = run(box(tmp_path), doc)
    lines = got.stdout.splitlines()
    assert got.returncode == 42
    assert lines[0].startswith("as written   policy.txt:1 ")
    assert lines[1].startswith("almost       policy.txt:4 ")
    assert lines[1].endswith("(8 of 9 words)")
    assert lines[2].split() == ["changed", "Monday", "->", "Tuesday"]
    assert lines[3].startswith("not there    ")
    assert lines[-1] == "3 quotes: 1 as written, 1 almost, 1 not there."


def test_every_quote_holding_is_exit_zero_and_curly_marks_count(tmp_path):
    doc = write(tmp_path, "“The council met on Tuesday and approved the budget”\n")
    got = run(box(tmp_path), doc)
    assert got.returncode == 0
    assert (
        got.stdout.splitlines()[-1] == "1 quotes: 1 as written, 0 almost, 0 not there."
    )


def test_short_and_repeated_quotations_are_left_out():
    text = '"three word bit" and "The council met on Tuesday" then "The council met on Tuesday"'
    assert quotes.quotations(text) == ["The council met on Tuesday"]
    assert quotes.quotations('"across\na line break here"') == []


def test_a_document_with_no_quotations_says_so(tmp_path):
    got = run(box(tmp_path), write(tmp_path, "Nothing quoted here at all.\n"))
    assert got.returncode == 0
    assert got.stdout.startswith("no quotations of 4 words or more in ")


def test_refusals(tmp_path):
    b = box(tmp_path)
    assert run(tmp_path / "nobox", write(tmp_path, '"a b c d"')).returncode == 2
    assert run(b, tmp_path / "missing.md").returncode == 2
    (tmp_path / "bin").write_bytes(b"\xff\xfe\x00")
    assert run(b, tmp_path / "bin").returncode == 2
    got = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert got.returncode == 2 and "quotes.py" in got.stderr


def test_check_returns_the_verdict_place_and_words_kept():
    pile = [
        {
            "path": "policy.txt",
            "line": 4,
            "text": "The council met on Tuesday and approved the budget.",
        }
    ]
    assert quotes.check(pile, "The council met on Tuesday and approved the budget") == (
        "as written", "policy.txt:4", 9, [])  # fmt: skip
    verdict, place, kept, diffs = quotes.check(
        pile, "The council met on Monday and approved the budget"
    )
    assert (verdict, place, kept) == ("almost", "policy.txt:4", 8)
    assert diffs == [("changed", ["Monday"], ["Tuesday"])]
    assert quotes.check(pile, "Nothing like this sentence appears anywhere") == (
        "not there",
        "",
        0,
        [],
    )


def test_a_long_quote_is_shortened_at_sixty_characters():
    exactly = "x" * 60
    assert quotes.short(exactly) == f'"{exactly}"'
    assert quotes.short(exactly + "y") == '"' + "x" * 59 + '…"'
