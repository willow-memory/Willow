"""again: repeats counted from the record's bite keys, offered on willow-bot's
ladder (every third ask), and never offered once an approval stands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return b


def ask(b: Path, q: str, n: int) -> None:
    for _ in range(n):
        run(str(KERNEL), "bite", "--box", str(b), *NOW, q)


def test_the_ladder_asked_noticed_offered(tmp_path):
    b = box(tmp_path)
    ask(b, "how much sun do tomatoes want", 1)
    assert (
        "No question asked more than once"
        in run(str(HERE / "again.py"), "--box", str(b)).stdout
    )
    ask(b, "How much SUN do tomatoes want?", 1)  # the same words: the same question
    got = run(str(HERE / "again.py"), "--box", str(b))
    assert (
        got.returncode == 0
        and "asked 2 times" in got.stdout
        and "standing?" not in got.stdout
    )
    ask(b, "how much sun do tomatoes want", 1)
    got = run(str(HERE / "again.py"), "--box", str(b))
    assert (
        got.returncode == 42
        and "asked 3 times" in got.stdout
        and "make it standing?" in got.stdout
    )
    assert "answered from garden.md:1" in got.stdout
    ask(b, "how much sun do tomatoes want", 1)
    assert (
        "standing?" not in run(str(HERE / "again.py"), "--box", str(b)).stdout
    )  # 4: not a third


def test_one_question_by_its_words_and_no_words_in_the_record(tmp_path):
    b = box(tmp_path)
    ask(b, "when does the frost come", 2)
    one = run(str(HERE / "again.py"), "--box", str(b), "When does the frost come?")
    assert (
        "asked 2 times" in one.stdout
        and "nothing in your folder answered it" in one.stdout
    )
    assert (
        "haven't asked"
        in run(str(HERE / "again.py"), "--box", str(b), "something new").stdout
    )
    assert "frost" not in (b / "record.jsonl").read_text()
