"""shared-runs, every kind, the freeze: the judge, the first study's files it
uses and the truth it holds a machine to are the bytes they were."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "study"
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_every_frozen_file_is_the_bytes_it_was():
    for name, want in FROZEN["files"].items():
        assert sha(HERE / name) == want, f"{name} changed since the freeze"
    for name, want in FROZEN["from_the_first_study"].items():
        assert sha(STUDY / name) == want, (
            f"the first study's {name} is not the one frozen with"
        )
    for name, want in FROZEN["truth"].items():
        assert sha(HERE.parent / name) == want, (
            "the truth is not the baseline frozen with"
        )
    first = json.loads((STUDY / "FROZEN.json").read_text(encoding="utf-8"))["files"]
    assert all(first[n] == h for n, h in FROZEN["from_the_first_study"].items())


def test_only_the_named_machines_are_added_and_the_rules_are_the_two_judged():
    import sys

    sys.path.insert(0, str(HERE))
    import every_kind

    assert tuple(FROZEN["rules"]) == every_kind.RULES
    runs = HERE / "runs"
    there = sorted(p.name for p in runs.iterdir()) if runs.is_dir() else []
    assert set(there) <= set(FROZEN["machines"]), (
        "a machine was added that the freeze does not name"
    )
