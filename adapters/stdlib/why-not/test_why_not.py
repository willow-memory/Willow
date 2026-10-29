"""why-not: for a question the folder doesn't hold, which words nothing holds,
the nearest passages and what they lacked, a close spelling with the words-list
line that would teach it, and the kind of file that would have answered; a
question it does hold said so; nothing written, not even a record row."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "why_not.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("why_not", SCRIPT)
wn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wn)

DIARY = "Tomatoes need six hours of sun.\n\nThe frosts came early last year.\n\nPlant the beans in May.\n"


def box(
    tmp_path: Path, files: dict[str, str] | None = None, words: str | None = None
) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(exist_ok=True)
    for name, text in (files or {"diary.txt": DIARY}).items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    argv = [
        sys.executable,
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    subprocess.run(argv, check=True, capture_output=True)
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_a_question_the_files_hold_says_so_and_where(tmp_path):
    got = run("--box", str(box(tmp_path)), "how much sun do tomatoes want")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[1] == "Your files do hold it: diary.txt:1."


def test_each_word_is_counted_and_a_word_nothing_holds_is_named(tmp_path):
    got = run("--box", str(box(tmp_path)), "when does the frost come in autumn")
    assert got.returncode == 42
    out = got.stdout.splitlines()
    assert out[0] == "when does the frost come in autumn"
    assert out[1].split() == ["frost", "held", "by", "1", "passage:", "diary.txt:3"]
    assert out[2].split() == ["come", "no", "passage", "holds", "it"]
    assert "A passage has to hold 2 of the 3 words at once." in out
    assert "  diary.txt:3  holds 1 (frost); lacks come, autumn" in out


def test_the_words_the_kernel_leaves_out_are_not_counted():
    assert wn.want_of("When does the frost come? Frost!") == ["frost", "come"]
    assert wn.want_of("how do I") == []


def test_a_question_of_only_common_words_says_to_name_the_thing(tmp_path):
    got = run("--box", str(box(tmp_path)), "how do I")
    assert got.returncode == 42 and "name the thing you mean" in got.stdout


def test_a_word_held_by_its_plain_form_counts_as_held(tmp_path):
    b = box(tmp_path, {"bills.txt": "The invoices are in the blue folder.\n"})
    got = run("--box", str(b), "where is the invoice paperwork cabinet")
    assert got.returncode == 42, got.stdout
    assert "invoice" in got.stdout and "held by 1 passage: bills.txt:1" in got.stdout
    assert "paperwork  no passage holds it" in got.stdout


def test_a_spelling_nothing_holds_but_a_close_one_does(tmp_path):
    b = box(
        tmp_path,
        {
            "n.txt": "The boiler service is due in November.\n\nCall the plumber about the radiator.\n"
        },
    )
    got = run("--box", str(b), "when is the radiater serviced again")
    assert got.returncode == 42
    assert "(your files say 'radiator': radiater = radiator)" in got.stdout


def test_the_kind_of_file_follows_the_questions_opening():
    kinds = {q: wn.kind_of(q) for q in ("how much rent", "how many hives", "when is it", "what time is it", "who owes me",
             "where is the key", "why did it fail", "how do I bake", "what is the code", "tell me more")}  # fmt: skip
    assert "number" in kinds["how much rent"] and "number" in kinds["how many hives"]
    assert "dated" in kinds["when is it"] and "dated" in kinds["what time is it"]
    assert "person" in kinds["who owes me"] and "place" in kinds["where is the key"]
    assert "reason" in kinds["why did it fail"] and "steps" in kinds["how do I bake"]
    assert "plainly" in kinds["what is the code"] and kinds["tell me more"] is None


def test_a_boxs_words_list_is_read_as_the_bite_reads_it(tmp_path):
    b = box(
        tmp_path,
        {"n.txt": "The boiler service is due in November.\n"},
        words="serviced = service\n",
    )
    assert run("--box", str(b), "when is the boiler serviced").returncode == 0


def test_it_writes_nothing_not_even_a_record_row(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "when does the frost come in autumn")
    run("--box", str(b), "how much sun do tomatoes want")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_passage_holding_none_of_the_words_is_said_so(tmp_path):
    got = run("--box", str(box(tmp_path)), "zebra giraffe")
    assert got.returncode == 42 and "No passage holds any of them." in got.stdout


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b)],
        ["--box", str(b), "a", "b"],
        ["--box", str(b), "--stray"],
        ["--box", str(tmp_path), "q"],
    ):
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "why_not.py" in run().stderr


def test_one_word_is_not_pluralised(tmp_path):
    got = run("--box", str(box(tmp_path)), "zebra")
    assert "A passage has to hold 1 of the 1 word at once." in got.stdout
