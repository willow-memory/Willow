"""dialect-dates: dialect's words, each dated by first-mention's reading of
its lines, oldest first; a word with no dated line last and said so;
nothing written; and a refusal, never a quiet skip."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "dialect_dates.py"
spec = importlib.util.spec_from_file_location("dialect_dates", SCRIPT)
dd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dd)
NOW = ["--now", "2026-11-06T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


def passage(path: str, text: str, n: int) -> dict:
    return {"path": path, "line": n, "text": text, "id": f"{path}{n}{text}"}


def test_each_word_is_dated_by_its_first_and_last_line_oldest_first():
    pile = [
        passage("2026-03-01.md", "the keybed again", 1),
        passage("2025-01-10.md", "a trapwork squeak", 1),
        passage("2025-06-02.md", "keybed felt and trapwork", 1),
        passage("2026-01-05.md", "trapwork done", 1),
    ]
    rows = dd.dated(pile, ["keybed", "trapwork"], {})
    assert [(r["word"], r["first"], r["last"]) for r in rows] == [
        ("trapwork", "2025-01-10", "2026-01-05"),
        ("keybed", "2025-06-02", "2026-03-01"),
    ]
    assert rows[0]["mentions"] == 3 and rows[0]["files"] == 3
    assert (
        rows[0]["where"] == "2025-01-10.md:1" and rows[0]["text"] == "a trapwork squeak"
    )


def test_a_word_no_line_dates_comes_last_and_a_word_no_line_holds_is_left_out():
    pile = [
        passage("notes.md", "the keybed", 1),
        passage("2025-02-01.md", "trapwork", 1),
    ]
    rows = dd.dated(pile, ["keybed", "trapwork", "absent"], {})
    assert [(r["word"], r["first"]) for r in rows] == [
        ("trapwork", "2025-02-01"),
        ("keybed", ""),
    ]


def test_a_date_in_the_line_beats_the_file_name():
    pile = [passage("2026-01-01.md", "2024-05-06 first keybed job", 1)]
    assert dd.dated(pile, ["keybed"], {})[0]["first"] == "2024-05-06"


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for day, text in (("2025-01-10", "Trapwork squeak at the Holloway house, keybed loose."),
                      ("2025-06-02", "Keybed shimmed. Trapwork fine."),
                      ("2026-01-05", "Trapwork again, and the keybed.")):  # fmt: skip
        (pile / f"{day}.md").write_text(text + "\n")
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b),
                          "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_a_box_prints_its_words_dated_and_writes_nothing(box: Path):
    pytest.importorskip("wordfreq")
    before = {p: p.stat().st_mtime_ns for p in box.parent.rglob("*") if p.is_file()}
    got = run("--box", str(box), "--top", "5")
    assert got.returncode == 0, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0].startswith("Your words against wordfreq's en, dated:")
    trap = next(ln for ln in lines if " trapwork " in ln)
    assert trap.split()[:2] == ["2025-01-10", "2026-01-05"]
    assert "3 mentions in 3 files" in trap
    after = {p: p.stat().st_mtime_ns for p in box.parent.rglob("*") if p.is_file()}
    assert after == before


@pytest.mark.parametrize("argv", [[], ["--box"], ["--top", "3"], ["--box", "x", "--top", "0"],
                                  ["--box", "x", "--top", "many"], ["--box", "x", "extra"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = run(*argv)
    assert got.returncode == 2 and "dialect_dates.py" in got.stderr


def test_a_folder_that_isnt_a_box_is_refused(tmp_path: Path):
    pytest.importorskip("wordfreq")
    got = run("--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_a_language_wordfreq_lacks_is_refused(box: Path):
    pytest.importorskip("wordfreq")
    got = run("--box", str(box), "--lang", "qq")
    assert got.returncode == 2 and "no counts for 'qq'" in got.stderr
