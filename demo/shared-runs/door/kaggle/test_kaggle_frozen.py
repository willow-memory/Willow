"""shared-runs, the door on Kaggle, the freeze: every frozen file is the bytes it
was, and the rules frozen are the rules held.py judges."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import held  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_the_bytes_it_was_when_frozen():
    for name, want in FROZEN["files"].items():
        got = hashlib.sha256((HERE / name).resolve().read_bytes()).hexdigest()
        assert got == want, (
            f"{name} changed since the freeze: a new freeze, with its reason"
        )
    assert len(FROZEN["files"]) == 8


def test_the_rules_frozen_are_the_rules_held():
    assert tuple(FROZEN["rules"]) == held.RULES
    assert "336379" in FROZEN["rules"]["K4"] and FROZEN["cut_seconds"] == 10
    source = (HERE / "door_notebooks.py").read_text(encoding="utf-8")
    assert source.count("cut: int = 10") == 1
