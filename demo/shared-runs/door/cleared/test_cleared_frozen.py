"""shared-runs, strangers cleared every round, the freeze: every frozen file is
the bytes it was, the rules frozen are the rules bought.py judges, and what
was foretold is kept."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bought  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_the_bytes_it_was_when_frozen():
    for name, want in FROZEN["files"].items():
        got = hashlib.sha256((HERE / name).resolve().read_bytes()).hexdigest()
        assert got == want, (
            f"{name} changed since the freeze: a new freeze, with its reason"
        )
    assert len(FROZEN["files"]) == 10


def test_the_rules_frozen_are_the_rules_judged_and_the_figures_foretold_are_on_the_page():
    assert (
        tuple(FROZEN["rules"]) == bought.RULES
        and tuple(FROZEN["strangers"]) == bought.STRANGERS
    )
    assert "714369" in FROZEN["rules"]["C4"] and FROZEN["foretold"]["clears"] == 714369
    page = (HERE / "README.md").read_text(encoding="utf-8")
    assert "714,369" in page and "81.7%" in page and "7,542" in page
