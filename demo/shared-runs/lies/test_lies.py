"""shared-runs, the lies: every trial is named before it is run, a lie is
told to a copy and never to the honest run, each rule fails when what it
guards is broken, and the dry run kept is what its page says."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / "study"))
import dry  # noqa: E402
import lies  # noqa: E402
import sweep  # noqa: E402


def honest(tmp_path: Path) -> Path:
    assert dry.main(["--plan", str(HERE / "dry-plan.json"), "--work", str(tmp_path / "honest"), "--toy"]) == 0  # fmt: skip
    return tmp_path / "honest" / "runs"


def digest(folder: Path) -> str:
    whole = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            whole.update(p.relative_to(folder).as_posix().encode() + p.read_bytes())
    return whole.hexdigest()


def test_every_trial_is_named_from_the_file_and_the_honest_run_before_any_is_run(
    tmp_path,
):
    runs = honest(tmp_path)
    spec = lies.load(HERE / "dry-lies.json")
    plan = sweep.load(spec["plan_file"])
    starts = json.loads(spec["starts_file"].read_text())
    listed = lies.trials(spec, plan, starts, runs, toy=True)
    assert listed == lies.trials(spec, plan, starts, runs, toy=True)
    assert [t["kind"] for t in listed].count("one-bit") == 8 and len(listed) == 22
    assert {t["kind"] for t in listed} == set(lies.KINDS)
    for t in listed:
        if t["trajectory"]:
            assert t["machine"] == sweep.owner(plan, t["trajectory"])
    halts = [t for t in listed if t["kind"] == "no-halt"]
    assert [(t["trajectory"], t["step"]) for t in halts] == [("vvvv-halts", 71)]
    other = lies.trials({**spec, "seed": "another"}, plan, starts, runs, toy=True)
    assert [t["step"] for t in other] != [t["step"] for t in listed]


def test_a_lie_is_told_to_a_copy_and_the_trials_come_out_as_the_page_says(
    tmp_path, capsys
):
    runs = honest(tmp_path)
    before = digest(runs)
    work = tmp_path / "work"
    args = ["--lies", str(HERE / "dry-lies.json")]
    assert (
        lies.main(["run", *args, "--honest", str(runs), "--work", str(work), "--toy"])
        == 0
    )
    assert digest(runs) == before, "the honest run was written to"
    capsys.readouterr()
    assert lies.main(["judge", *args, "--work", str(work), "--json"]) == 0
    got = json.loads(capsys.readouterr().out)
    kept = json.loads((HERE / "dry" / "verdicts.json").read_text())
    assert got == kept, "the dry run kept is what running it again gives"
    assert {r: v["state"] for r, v in kept["verdicts"].items()} == {
        "L1": "passed", "L2": "passed", "L3": "passed", "L4": "passed",
        "L5": "measured", "L6": "measured", "L7": "passed",
    }  # fmt: skip
    found = kept["verdicts"]["L5"]["figures"]["found"]
    assert (
        found["as-run, one-bit"] == "3 of 8"
        and found["everything, one-bit"] == "8 of 8"
    )
    assert (
        found["as-run, false-halt"] == "3 of 4"
        and found["everything, no-halt"] == "0 of 1"
    )
    harm = kept["verdicts"]["L6"]["figures"]["harm"]
    assert harm["everything, one-bit"]["wrong_jobs"] == 3, "found is not prevented"
    assert harm["as-run, no-halt"] == {
        "lies": 1, "reached_no_job": 1, "wrong_jobs": 0,
        "wrong_jobs_where_nothing_was_found": 0, "halts_again": 1,
    }  # fmt: skip
    assert (
        lies.main(["run", *args, "--honest", str(runs), "--work", str(work), "--toy"])
        == 2
    )
    assert lies.main(["run", *args, "--honest", str(runs), "--work", str(HERE / "w"), "--toy"]) == 2  # fmt: skip
    assert not (HERE / "w").exists() and lies.main(["run"]) == 2 and lies.main([]) == 2


def test_each_rule_fails_when_what_it_guards_is_broken():
    spec = {"arms": [{"name": "as-run", "check_one_in": 4, "draw_one_in": 3},
                     {"name": "everything", "check_one_in": 1, "draw_one_in": 1}]}  # fmt: skip
    base = {"n": 1, "arm": "everything", "kind": "one-bit", "trajectory": "t", "step": 10,
            "machine": 0, "round_2_jobs": 4, "wrong": ["t@20"], "wrong_elsewhere": [],
            "lie_checked": 1, "found_by_state": 1, "wrong_run_afresh": ["t@20"],
            "found_by_afresh": ["t@20"], "halts_again": 0}  # fmt: skip
    none = {**base, "n": 2, "kind": "none", "wrong": [], "lie_checked": 0, "found_by_state": 0,
            "wrong_run_afresh": [], "found_by_afresh": []}  # fmt: skip
    states = lambda rows: {r: v["state"] for r, v in lies.verdicts(spec, rows).items()}  # noqa: E731
    assert states([base, none]) == {"L1": "passed", "L2": "passed", "L3": "passed", "L4": "passed",
                                    "L5": "measured", "L6": "measured", "L7": "passed"}  # fmt: skip
    assert states([base, {**none, "found_by_state": 1}])["L1"] == "failed"
    assert states([{**base, "found_by_state": 0}, none])["L2"] == "failed"
    assert states([{**base, "found_by_afresh": []}, none])["L3"] == "failed"
    assert states([{**base, "found_by_state": 0, "found_by_afresh": []}, none])["L4"] == "failed"  # fmt: skip
    assert states([{**base, "wrong_elsewhere": ["u@20"]}, none])["L7"] == "failed"
    assert states([{**base, "arm": "as-run"}])["L4"] == "not tested"
    assert states([base])["L1"] == "not tested"
    assert (
        lies.flipped("00ff") == "01ff" and lies.flipped(lies.flipped("ab12")) == "ab12"
    )


def test_the_lies_proposed_for_the_study_are_listed_from_its_own_kept_run():
    spec = lies.load(HERE / "lies.json")
    plan = sweep.load(spec["plan_file"])
    starts = json.loads(spec["starts_file"].read_text())
    listed = lies.trials(spec, plan, starts, HERE.parent / "study" / "runs", toy=False)
    assert len(listed) == 40 and sum(1 for t in listed if t["kind"] == "none") == 3
    assert [a["name"] for a in spec["arms"]] == ["as-run", "everything"]
    assert (spec["arms"][0]["check_one_in"], spec["arms"][0]["draw_one_in"]) == (
        plan["check_one_in"], plan["draw_one_in"]
    ), "the first arm checks what the study checked"  # fmt: skip
    assert "FROZEN" not in " ".join(p.name for p in HERE.iterdir()), (
        "drafted, not frozen"
    )
