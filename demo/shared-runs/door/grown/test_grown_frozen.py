"""shared-runs, the sweep grown, the freeze: every frozen file is the bytes it was, and
the rules frozen are the rules grew.py judges."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grew  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_the_bytes_it_was_when_frozen():
    for name, want in FROZEN["files"].items():
        got = hashlib.sha256((HERE / name).resolve().read_bytes()).hexdigest()
        assert got == want, (
            f"{name} changed since the freeze: a new freeze, with its reason"
        )
    assert len(FROZEN["files"]) == 9


def test_the_rules_frozen_are_the_rules_judged():
    assert tuple(FROZEN["rules"]) == grew.RULES
    source = (HERE / "grew.py").read_text(encoding="utf-8")
    assert source.count("off <= 2") == 1 and "within 2 points" in FROZEN["rules"]["G2"]
