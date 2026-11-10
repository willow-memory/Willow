"""demo/money-hour: what was frozen stays frozen, and the parts that need no
mirror do what they say.

The run needs the markets demo's mirror (fetch.py, then mirror.py, in
demo/markets-2026-11-05) and is not part of CI; this is.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_life  # noqa: E402
import run  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_as_it_was_frozen():
    for rel, sha in {
        **FROZEN["files"],
        **{f"../../{k}": v for k, v in FROZEN["tools"].items()},
    }.items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )


def test_every_line_about_the_world_names_it_so_the_check_can_find_it():
    lines = [
        x["line"]
        for x in Q["facts"] + [Q["quote"]] + Q["traps"] + Q["calls"]
        if "line" in x
    ]
    assert all(make_life.REAL.search(ln) for ln in lines), [
        ln for ln in lines if not make_life.REAL.search(ln)
    ]


def test_each_fact_and_trap_names_a_file_in_the_slice():
    patterns = " ".join(Q["slice"]["from_mirror"])
    for x in Q["facts"] + [Q["quote"]] + [t for t in Q["traps"] if "file" in t]:
        assert x["file"].split("/")[-1].split(".")[0] in patterns, x["id"]


def test_folding_keeps_every_word_and_leaves_short_lines_alone():
    long = "One sentence here. " * 40
    folded = run.fold("short line\n" + long.strip())
    assert folded.split() == ("short line " + long).split()
    assert all(len(ln) <= run.MAX_LINE for ln in folded.splitlines())
    assert folded.splitlines()[0] == "short line"


def test_the_calls_are_made_before_the_open_and_closed_after():
    for c in Q["calls"]:
        assert c["made"] < f"{c['date']}T13:00:00Z" < c["closed"], c["who"]


def test_run_refuses_a_work_folder_inside_the_repo(tmp_path):
    assert run.main(["--mirror", str(tmp_path), "--work", str(HERE / "work")]) == 2


def test_each_run_judged_its_freezes_rules_and_sealed_nothing():
    run1 = {"calls-made", "calls-closed", "lines", "after", "stack", "verify"}
    run2 = run1 | {"fold", "timeline", "sort", "thesis", "across", "stacks"}
    for n, rules in ((1, run1), (2, run2), (3, run2)):
        r = json.loads((HERE / "results" / f"run-{n}.json").read_text(encoding="utf-8"))
        ids = [f["id"] for f in Q["facts"]] + ["V1"] + [t["id"] for t in Q["traps"]
                                                     if n == 2 or t["id"] != "T6"]  # fmt: skip
        assert set(ids) | rules <= set(r), n
        assert all(" 0 sealed" in v for v in r["verify"]["boxes"].values())


def test_the_letter_is_one_sentence_a_line_and_its_slip_is_the_trap():
    final = Q["letter"]["final"]
    assert final[Q["letter"]["slip"] - 1] == next(
        t["line"] for t in Q["traps"] if t["id"] == "T6"
    )
    assert all(
        s.endswith(".") and s.count(". ") == 0 for s in final + Q["letter"]["draft"]
    )


def test_run_3_held_every_rule():
    r = json.loads((HERE / "results" / "run-3.json").read_text(encoding="utf-8"))
    assert all(v["held"] for v in r.values() if isinstance(v, dict) and "held" in v)
