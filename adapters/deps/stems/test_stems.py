"""stems: a word no file holds read as the form of its stem the files hold, by
Snowball's stemmer for the language asked; offered, never asked; nothing
written; and a refusal, never a quiet skip, without snowballstemmer."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "stems.py"
spec = importlib.util.spec_from_file_location("stems", SCRIPT)
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)
NOW = ["--now", "2026-10-29T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "briefe.md").write_text(
        "Das Haus am See ist verkauft.\n\nIm Haus wohnt jetzt Greta.\n\n"
        "Die Gärten hinter dem Hof.\n"
    )
    (pile / "полка.md").write_text("Книга о море лежит на столе.\n")
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b),
                          "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_a_form_no_file_holds_is_read_as_the_one_they_do(box):
    got = run("--box", str(box), "--lang", "german", "häuser am see")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "read häuser as haus: 2 passages hold it",
        "ask:  haus am see",
    ]


def test_each_language_by_its_own_stemmer(box):
    got = run("--box", str(box), "--lang", "russian", "книги")
    assert got.stdout.splitlines()[0] == "read книги as книга: 1 passage holds it"
    garten = run("--box", str(box), "--lang", "german", "garten")
    assert "read garten as gärten" in garten.stdout
    # english by default, whose stemmer doesn't cut "häuser" to "haus"
    assert run("--box", str(box), "häuser").returncode == 42


def test_a_word_held_as_typed_is_left_alone(box):
    got = run("--box", str(box), "--lang", "german", "haus see")
    assert got.returncode == 0
    assert got.stdout.startswith("Your files hold every word")


def test_a_word_no_file_has_in_any_form_is_said(box):
    got = run("--box", str(box), "--lang", "german", "bäckerei")
    assert got.returncode == 42
    assert got.stdout == "no file has bäckerei, in any form\n"


def test_the_most_held_form_wins_and_a_tie_goes_to_the_first_sorted():
    stem = st.stemmer("german")
    pile = [{"path": "a.md", "text": "hauses"}, {"path": "b.md", "text": "hauses"},
            {"path": "c.md", "text": "haus"}]  # fmt: skip
    assert st.readings("häuser", pile, {}, stem)[0] == {"häuser": ("hauses", 2)}
    pile = [{"path": "a.md", "text": "hauses"}, {"path": "b.md", "text": "haus"}]
    assert st.readings("häuser", pile, {}, stem)[0] == {"häuser": ("haus", 1)}


def test_a_word_the_words_list_reads_is_left_alone():
    pile = [{"path": "a.md", "text": "haus"}]
    alias = {"häuser": ["haus"]}
    assert st.readings("häuser", pile, alias, st.stemmer("german")) == ({}, [])


def test_nothing_is_written(box, tmp_path):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(box), "--lang", "german", "häuser")
    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_refusals(box, tmp_path):
    for argv in ([], ["--box", str(box)], ["--box", str(box), "a", "b"],
                 ["--box", str(box), "--lang", "klingon", "haus"],
                 ["--box", str(tmp_path), "haus"],
                 ["--box", str(box), "?!"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
    assert (
        "no stemmer for 'klingon'"
        in run("--box", str(box), "--lang", "klingon", "haus").stderr
    )


def test_without_snowballstemmer_it_refuses_and_names_the_install(box, tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "snowballstemmer.py").write_text("raise ImportError('hidden')\n")
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "--box", str(box), "haus"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
