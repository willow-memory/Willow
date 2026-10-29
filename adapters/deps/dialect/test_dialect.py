"""dialect: your files' words against wordfreq's counts, those the world
doesn't have apart from those you use far more than it does; a file's codes
in capitals left out; nothing written; and a refusal, never a quiet skip,
without wordfreq."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "dialect.py"
spec = importlib.util.spec_from_file_location("dialect", SCRIPT)
di = importlib.util.module_from_spec(spec)
spec.loader.exec_module(di)
NOW = ["--now", "2026-10-29T09:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


def passage(text: str, n: int) -> dict:
    return {"path": "a.md", "line": n, "text": text, "id": f"{n}{text}"}


WORLD = {"allotment": 2.5, "beans": 4.0, "today": 6.0}


def test_unknown_words_by_passages_and_known_ones_by_how_far_beyond():
    pile = [
        passage("Gerry and the beans at the allotment today", 1),
        passage("Gerry watered the allotment", 2),
        passage("the allotment beans and Gerry again, Wendouree", 3),
        passage("Wendouree allotment beans today", 4),
        passage("Wendouree beans today", 5),
    ]
    unknown, known = di.dialect(pile, lambda w: WORLD.get(w, 0.0))
    assert [(w, n) for w, _, n in unknown] == [("gerry", 3), ("wendouree", 3)]
    assert [w for w, *_ in known] == ["allotment", "beans", "today"]
    assert known[0][2] == 2.5 and known[0][3] == 4


def test_fewer_than_three_passages_a_codes_capitals_and_repeats_dont_count():
    pile = [passage("DTSTART VEVENT gerry", n) for n in range(1, 6)]
    pile += [passage("rarely", 9), passage("rarely", 10)]
    pile += [passage("same memo said again", 11)] * 4  # one id: one passage
    unknown, known = di.dialect(pile, lambda w: 0.0)
    assert [w for w, *_ in unknown] == ["gerry"]


def test_a_word_used_less_than_the_world_uses_it_isnt_listed():
    pile = [passage("today " + "x" * 3 + f" pad{n} " * 50, n) for n in range(1, 4)]
    unknown, known = di.dialect(pile, lambda w: {"today": 9.0}.get(w, 0.0))
    assert "today" not in [w for w, *_ in known]


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "diary.md").write_text(
        "Gerry at the allotment in Wendouree.\n\nThe allotment beans are up; Gerry pleased.\n\n"
        "Wendouree market, then the allotment with Gerry.\n\n"
        "DTSTART:20260301\nDTSTART:20260302\n\nDTSTART:20260303\n"
    )
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b),
                          "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_against_wordfreqs_own_counts(box):
    got = run("--box", str(box))
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "Your words against wordfreq's en, from 5 passages.\n"
        "\n"
        "Words you use far more than the world does (Zipf, you and it):\n"
        "  allotment  8.1 to 3.1, +4.9  in 3 passages\n"
        "  gerry      8.1 to 3.6, +4.4  in 3 passages\n"
    )  # wendouree is in two passages only; DTSTART is a calendar's code


def test_another_language_and_top(box):
    got = run("--box", str(box), "--lang", "de", "--top", "1")
    assert got.returncode == 0
    assert got.stdout.startswith("Your words against wordfreq's de")
    assert got.stdout.count(" passages\n") <= 2


def test_too_few_files_is_42(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Just one note.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), *NOW], capture_output=True)  # fmt: skip
    assert run("--box", str(b)).returncode == 42


def test_nothing_is_written(box, tmp_path):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(box))
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_refusals(box, tmp_path):
    for argv in ([], ["--box", str(box), "stray"], ["--box", str(box), "--top", "0"],
                 ["--box", str(box), "--top", "x"], ["--box", str(tmp_path)],
                 ["--box", str(box), "--lang", "klingon"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv


def test_without_wordfreq_it_refuses_and_names_the_install(box, tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "wordfreq.py").write_text("raise ImportError('hidden')\n")
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "--box", str(box)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
