"""quote-check: every place a quote's words appear in order, verbatim or not,
and the line it starts on."""

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
    (pile / "letter.txt").write_text(
        "You will hear from us.\nThe determination limits the well. You may file\n"
        "a response within 180 days.\n"
    )
    (pile / "draft.md").write_text(
        "They said you may file a RESPONSE, within 180 days!\n"
    )
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


def test_verbatim_and_same_words_with_the_starting_line(tmp_path):
    got = run(str(HERE / "quote_check.py"), "--box", str(box(tmp_path)),
              "You may file a response within 180 days.")  # fmt: skip
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].split() == ["verbatim", "letter.txt:2"]  # not line 1's "You"
    assert lines[1].startswith("same words") and "draft.md:1" in lines[1]


def test_words_out_of_order_or_absent_are_not_found(tmp_path):
    b = box(tmp_path)
    assert (
        run(str(HERE / "quote_check.py"), "--box", str(b), "file you may").returncode
        == 42
    )
    assert run(str(HERE / "quote_check.py"), "--box", str(b), "...").returncode == 2
