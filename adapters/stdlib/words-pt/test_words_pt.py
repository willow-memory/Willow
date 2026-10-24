"""words-pt: Portuguese's common words out of a question before the kernel's
bite, and nothing else about the bite changed."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("words_pt", HERE / "words_pt.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = ["--now", "2026-10-24T00:00:00Z"]


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).write_text(text, encoding="utf-8")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "words_pt.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def test_the_common_words_are_left_out_and_the_rest_kept_in_order():
    assert mod.kept("Quando é a consulta no dentista?") == ["consulta", "dentista"]


def test_a_passage_sharing_only_common_words_is_not_served(tmp_path):
    b = box(
        tmp_path,
        {
            "noise.txt": "Quando é a festa no clube, a casa da Ana.",
            "answer.txt": "A consulta no dentista é terça às três.",
        },
    )
    got = run("bite", "--box", str(b), *NOW, "Quando é a consulta no dentista?")
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert [s["where"] for s in served] == ["answer.txt:1"]
    plain = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(b), *NOW, 'Quando é a consulta no dentista?'],
                           capture_output=True, text=True)  # fmt: skip
    assert "noise.txt:1" in plain.stdout  # the kernel alone serves the noise


def test_a_letter_typed_with_a_separate_accent_mark_is_the_same_word():
    split = unicodedata.normalize("NFD", "você")
    assert split != "você" and mod.kept(split + " x") == mod.kept("você" + " x")


def test_a_question_of_only_common_words_is_refused(tmp_path):
    b = box(tmp_path, {"answer.txt": "A consulta no dentista é terça às três."})
    only = " ".join(sorted(mod.COMMON)[:4])
    got = run("bite", "--box", str(b), only)
    assert got.returncode == 2 and "name the thing you mean" in got.stderr


def test_the_list_is_lowercase_words_the_kernel_would_split_the_same_way(capsys):
    assert mod.main(["list"]) == 0
    listed = capsys.readouterr().out.split()
    assert listed == sorted(mod.COMMON) and len(listed) > 80
    assert all(mod.kernel.words(w) == [w] for w in listed)


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["bite"],
        ["bite", "--box"],
        ["nope"],
        ["bite", "--box", "b", "q", "--stray"],
        ["bite", "--box", "b", "two", "words"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "words_pt.py" in got.stderr
        assert "bite --box DIR" in got.stderr  # the line for bite, at least
