"""pile-rungs: a question climbs words, phrases, embedder. The words rung
answers as the kernel does, and the higher rungs say they were skipped for it;
a phrase the folder uses answers when the words don't, serving only passages
that hold it; a question with no phrase of the folder skips that rung; the
embedder rung always says why it is skipped; a current store is read; and a
bad command line is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PR = HERE / "pile_rungs.py"
PS = HERE.parent / "pile-store" / "pile_store.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PR), *argv], capture_output=True, text=True
    )


def ask(folder: Path, *more: str) -> tuple[int, dict]:
    got = run("--from", str(folder), *more)
    assert got.returncode in (0, 42), got.stderr
    return got.returncode, json.loads(got.stdout)


def states(row: dict) -> list[tuple[str, str]]:
    return [(r["rung"], r["state"]) for r in row["rungs"]]


def a_folder(tmp: Path) -> Path:
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "loaf.md").write_text("Baked sourdough bread on Sunday.\n")
    (folder / "again.md").write_text("More sourdough bread for the market stall.\n")
    (folder / "garden.md").write_text("Tomatoes want sun and a warm wall.\n")
    return folder


def test_the_words_rung_answers_as_the_kernel_does(tmp_path):
    folder = a_folder(tmp_path)
    code, row = ask(folder, "tomatoes", "sun")
    assert code == 0 and row["rung"] == "words"
    assert states(row) == [
        ("words", "answered"),
        ("phrases", "skipped"),
        ("embedder", "skipped"),
    ]
    assert row["rungs"][1]["why"] == "words answered"
    want = [c["id"] for c in kernel.rank(kernel.chunks(folder), "tomatoes sun", top=5)]
    assert [s["id"] for s in row["served"]] == want
    assert [s["rank"] for s in row["served"]] == [1] and "score" not in row["served"][0]


def test_a_phrase_answers_when_the_words_do_not(tmp_path):
    folder = a_folder(tmp_path)
    q = ["where", "is", "the", "sourdough", "bread", "recipe", "card", "kept"]
    code, row = ask(folder, *q)
    assert code == 0 and row["rung"] == "phrases", row["rungs"]
    assert states(row)[:2] == [("words", "empty"), ("phrases", "answered")]
    assert row["rungs"][1]["why"] == "held sourdough bread"
    assert sorted(s["where"] for s in row["served"]) == ["again.md:1", "loaf.md:1"]
    assert all(s["phrases"] == ["sourdough bread"] for s in row["served"])
    assert [s["rank"] for s in row["served"]] == [1, 2]


def test_a_question_using_no_phrase_skips_that_rung_and_says_so(tmp_path):
    folder = a_folder(tmp_path)
    code, row = ask(folder, "kayak", "paddle", "storage")
    assert code == 42 and row["rung"] is None and row["served"] == []
    assert states(row) == [
        ("words", "empty"),
        ("phrases", "skipped"),
        ("embedder", "skipped"),
    ]
    assert "none of the folder's phrases" in row["rungs"][1]["why"]
    assert "latent needs numpy" in row["rungs"][2]["why"]
    code, row = ask(folder, "the", "and")
    assert code == 42 and row["rungs"][0]["state"] == "skipped"


def test_a_phrase_no_passage_holds_beside_its_words_is_empty(tmp_path):
    folder = a_folder(tmp_path)
    (folder / "rye.md").write_text("Rye and sourdough, bread on the side.\n")
    code, row = ask(folder, "sourdough", "bread", "kayak", "paddle", "oar")
    assert code == 0 and row["rung"] == "phrases"
    assert "rye.md:1" not in [s["where"] for s in row["served"]]


def test_a_current_store_is_read(tmp_path):
    folder = a_folder(tmp_path)
    store = tmp_path / "pile.sqlite"
    subprocess.run([sys.executable, str(PS), "--from", str(folder),
                    "--to", str(store)], check=True, capture_output=True)  # fmt: skip
    _, row = ask(folder, "--store", str(store), "tomatoes", "sun")
    assert row["read_from"] == "store" and row["rung"] == "words"
    assert row["served"] == ask(folder, "tomatoes", "sun")[1]["served"]


def test_top_limits_what_is_served(tmp_path):
    folder = a_folder(tmp_path)
    _, row = ask(folder, "--top", "1", "sourdough", "bread")
    assert len(row["served"]) == 1


def test_a_bad_command_line_is_refused(tmp_path):
    folder = a_folder(tmp_path)
    for argv in ([], ["bread"], ["--from", str(folder)],
                 ["--from", str(folder), "--stray", "bread"],
                 ["--from", str(folder), "--top", "0", "bread"],
                 ["--from", str(folder), "--top", "x", "bread"],
                 ["--from", str(folder), "--store", "", "bread"],
                 ["--from", str(folder / "loaf.md"), "bread"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert "pile_rungs.py" in run().stderr
