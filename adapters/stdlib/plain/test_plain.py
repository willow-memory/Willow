"""plain: the kernel's bite as sentences, with its record and exit code unchanged."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("plain", HERE / "plain.py")
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text(
        "The bus leaves at seven from the square.\n\nWhen does the ferry sail?\n"
    )
    b = tmp_path / "box"
    assert run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
               "--key", str(tmp_path / "k"), *NOW).returncode == 0  # fmt: skip
    return b


def test_a_passage_is_said_with_its_file_and_line(tmp_path):
    got = run(str(HERE / "plain.py"), "bite", "--box", str(box(tmp_path)), *NOW,
              "when does the bus leave the square")  # fmt: skip
    assert got.returncode == 0
    assert (
        got.stdout
        == "From n.md, line 1:\n    The bus leaves at seven from the square.\n"
    )


def test_the_exit_code_and_the_record_are_the_kernels(tmp_path):
    b = box(tmp_path)
    q = "when does the ferry sail"
    mine = run(str(HERE / "plain.py"), "bite", "--box", str(b), *NOW, q)
    rows = (b / "record.jsonl").read_text().splitlines()
    theirs = run(str(KERNEL), "bite", "--box", str(b), *NOW, q)
    assert mine.returncode == theirs.returncode == 42
    after = (b / "record.jsonl").read_text().splitlines()
    assert {
        k: v for k, v in json.loads(rows[-1]).items() if k not in ("n", "prev", "hash")
    } == {
        k: v for k, v in json.loads(after[-1]).items() if k not in ("n", "prev", "hash")
    }
    assert "only asks your question back" in mine.stdout


def test_every_state_reads_as_a_sentence():
    assert pl.sentences({"state": "sealed", "answer": "Six hours."}) == (
        "You approved this answer:\n    Six hours."
    )
    empty = {"state": "empty", "served": [], "look": [
        {"why": "no file in your folder has frost", "where": "it may be called something else there",
         "next": "add it to your words list"}]}  # fmt: skip
    assert pl.sentences(empty) == (
        "Nothing in your folder says this.\n\nNote: no file in your folder has frost."
        " It may be called something else there. Next: add it to your words list."
    )


def test_a_refusal_passes_through_untouched(tmp_path):
    got = run(str(HERE / "plain.py"), "bite", "--box", str(tmp_path / "none"), "x")
    assert got.returncode == 2 and "init first" in got.stderr
