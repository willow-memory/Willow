"""Teodora, built blind, against the starter words list: what it does on a
folder no one fitted it to, measured, not assumed.

She asks "how much do I still owe dev" (QUESTIONS.md, 9). Her files say Dev
would "lend" the money; none says "owe". Without a words list the kernel
serves nothing; with starter-words' list, the chat where Dev offers to lend
is served. The add-on's own test holds the same claim on that one chat line;
this holds it on everything make_life.py writes for her."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KERNEL = ROOT / "kernel.py"
STARTER = ROOT / "adapters" / "stdlib" / "starter-words" / "starter.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def test_teodoras_debt_is_served_with_the_starter_words_and_not_without(tmp_path):
    shutil.copytree(HERE, tmp_path / "teodora")
    assert run(str(tmp_path / "teodora" / "make_life.py")).returncode == 0
    assert (
        run(str(STARTER), "copy", "--to", str(tmp_path / "words.txt")).returncode == 0
    )
    served = {}
    for name, extra in (
        ("without", []),
        ("with", ["--words", str(tmp_path / "words.txt")]),
    ):
        b = tmp_path / name
        run(str(KERNEL), "init", "--box", str(b), "--pile", str(tmp_path / "teodora" / "life"),
            "--key", str(tmp_path / "k"), *NOW, *extra)  # fmt: skip
        served[name] = json.loads(
            run(
                str(KERNEL),
                "bite",
                "--box",
                str(b),
                *NOW,
                "how much do I still owe dev",
            ).stdout
        )
    assert served["without"]["state"] == "empty"
    assert any(
        "lend" in s["text"] and "Dev" in s["text"] for s in served["with"]["served"]
    )
