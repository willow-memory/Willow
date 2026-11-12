"""shared-runs, nobody known, the freeze: every frozen file is the bytes it was,
the rules frozen are the rules fell.py judges, and what was foretold is kept."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fell  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_the_bytes_it_was_when_frozen():
    for name, want in FROZEN["files"].items():
        got = hashlib.sha256((HERE / name).resolve().read_bytes()).hexdigest()
        assert got == want, (
            f"{name} changed since the freeze: a new freeze, with its reason"
        )
    assert len(FROZEN["files"]) == 10


def test_the_rules_frozen_are_the_rules_judged_and_the_figure_foretold_is_on_the_page():
    assert tuple(FROZEN["rules"]) == fell.RULES
    assert FROZEN["foretold"]["saved"] == 34.8 and "34.8" in FROZEN["rules"]["U3"]
    source = (HERE / "fell.py").read_text(encoding="utf-8")
    assert source.count("off <= 2") == 1 and "within 2 points" in FROZEN["rules"]["U3"]
    page = (HERE / "README.md").read_text(encoding="utf-8")
    assert "8,683,650" in page and "34.8%" in page
