"""words-tlh: Klingon's common words out of a question before the kernel's
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
spec = importlib.util.spec_from_file_location("words_tlh", HERE / "words_tlh.py")
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
    return subprocess.run([sys.executable, str(HERE / "words_tlh.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def test_the_common_words_are_left_out_and_the_rest_kept_in_order():
    assert mod.kept("qatlh yIH Datlhap 'ej nuqDaq Qe'?") == ["yih", "datlhap", "qe"]


def test_a_passage_sharing_only_common_words_is_not_served(tmp_path):
    b = box(
        tmp_path,
        {
            "noise.txt": "nuqDaq 'oH Duj'e'? ghaH 'ej jIH, HISlaH.",
            "answer.txt": "Qe' naDev yIH.",
        },
    )
    got = run("bite", "--box", str(b), *NOW, "nuqDaq 'oH yIH'e'?")
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert [s["where"] for s in served] == ["answer.txt:1"]
    plain = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(b), *NOW, "nuqDaq 'oH yIH'e'?"],
                           capture_output=True, text=True)  # fmt: skip
    assert "noise.txt:1" in plain.stdout  # the kernel alone serves the noise


def test_each_apostrophe_reads_as_the_kernel_reads_it():
    # A plain or curly apostrophe splits, as the kernel splits it; the
    # modifier letter is a letter, so a suffix after it stays on the word.
    assert mod.kept("nuqDaq 'oH yIH'e'?") == ["yih"]
    assert mod.kept("nuqDaq ’oH yIH’e’?") == ["yih"]
    assert mod.kept("nuqDaq ʼoH yIHʼeʼ?") == ["yihʼeʼ"]


def test_every_spelling_is_common_typed_either_way():
    for s in mod.SPELLED:
        assert mod.kept(s) == [] and mod.kept(s.replace("'", "ʼ")) == [], s


def test_case_is_folded_as_the_kernel_folds_it():
    # q and Q are two letters in Klingon; the kernel lowercases both, so
    # Qatlh ("be difficult") goes out with qatlh ("why"), as the card says.
    assert mod.kept("Qatlh yIH") == ["yih"]


def test_a_letter_typed_with_a_separate_accent_mark_is_the_same_word():
    whole = "é"
    split = unicodedata.normalize("NFD", whole)
    assert split != whole and mod.kept(split + " x") == mod.kept(whole + " x")


def test_a_question_of_only_common_words_is_refused(tmp_path):
    b = box(tmp_path, {"answer.txt": "Qe' naDev yIH."})
    got = run("bite", "--box", str(b), "nuq 'oH 'e'?")
    assert got.returncode == 2 and "name the thing you mean" in got.stderr


def test_the_list_is_lowercase_words_the_kernel_would_split_the_same_way(capsys):
    assert mod.main(["list"]) == 0
    listed = capsys.readouterr().out.split()
    assert listed == sorted(mod.COMMON) and len(listed) == 37
    assert len(mod.SPELLED) == 27
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
        assert got.returncode == 2 and "words_tlh.py" in got.stderr
        assert "bite --box DIR" in got.stderr  # the line for bite, at least
