"""shared-runs, the freeze: every frozen file is the bytes it was, the rules
frozen are the rules judged, and the thresholds are the ones written down."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import account  # noqa: E402
import judge  # noqa: E402
import sweep  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_the_bytes_it_was_when_frozen():
    for name, want in FROZEN["files"].items():
        got = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert got == want, (
            f"{name} changed since the freeze: a new freeze, with its reason"
        )
    assert {"plan.json", "starts.json", "judge.py", "runner.py"} <= set(FROZEN["files"])


def test_the_rules_frozen_are_the_rules_judged_with_their_thresholds():
    assert tuple(FROZEN["rules"]) == judge.RULES
    plan = sweep.load(HERE / "plan.json")
    assert plan["draw_one_in"] == 10 and "one in 10" in FROZEN["rules"]["R4"]
    assert plan["project"] == FROZEN["project"]
    asked = [fig is not None for _, _, fig in account.QUESTIONS]
    assert (sum(asked), len(asked) - sum(asked)) == (16, 5)
    source = (HERE / "judge.py").read_text(encoding="utf-8")
    assert source.count("off <= 2") == 1 and "within 2 points" in FROZEN["rules"]["R3"]
    assert source.count("kinds < 3") == 1 and "three kinds" in FROZEN["rules"]["R1"]
