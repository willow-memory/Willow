"""demo/ofrenda: what was frozen is what is here, and Marisol's folder is
made the same every time, labelled as fiction, holding every planted line."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_every_frozen_file_is_as_it_was_frozen():
    for name, want in FROZEN["files"].items():
        assert sha(HERE / name) == want, f"{name} changed since the freeze"


def test_the_last_freeze_says_why():
    last = FROZEN["freezes"][-1]
    assert last["n"] == len(FROZEN["freezes"]) and len(last["why"]) > 40


def test_life_is_made_the_same_and_holds_what_was_planted(tmp_path):
    for name in ("make_life.py", "questions.json"):
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    make = [sys.executable, str(tmp_path / "make_life.py")]
    assert subprocess.run(make, capture_output=True).returncode == 0
    first = {p: p.read_bytes() for p in (tmp_path / "life").rglob("*") if p.is_file()}
    got = subprocess.run([*make, "--check"], capture_output=True, text=True)
    assert got.returncode == 0, got.stdout
    subprocess.run(make, capture_output=True)
    again = {p: p.read_bytes() for p in (tmp_path / "life").rglob("*") if p.is_file()}
    assert first == again, "the same bytes every run"


def test_a_question_is_frozen_with_its_box_voice_and_rule():
    q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    for item in q["questions"]:
        assert item["box"] in ("ofrenda", "ghost-club")
        assert (HERE / "voices" / f"{item['voice']}.md").is_file()
        assert (item["holds"] is None) == (item["says"] == [])
    assert set(q["pass_rules"]) == {"served", "cited", "says", "unsealed", "verify"}
