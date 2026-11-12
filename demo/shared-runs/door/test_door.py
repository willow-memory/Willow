"""shared-runs, the door: what is counted is what the first study's machines
did, to the step; a lie is found by a check that looks at it; and the
tables kept are what counting again gives."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "study"
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(STUDY))
import door  # noqa: E402
import sweep  # noqa: E402

PLAN = sweep.load(STUDY / "plan.json")
STOPS = json.loads((HERE / "stops.json").read_text())


def acts(name: str) -> list[dict]:
    return [
        json.loads(x)
        for x in (STUDY / "runs" / name / "acts.jsonl").read_text().splitlines()
    ]


def test_counting_comes_to_what_the_studys_machines_did_to_the_step():
    stops = {a["trajectory"]: a["ended"] for a in acts("baseline-1")
             if a["mode"] == "alone" and a["outcome"] != "ended"}  # fmt: skip
    assert stops == STOPS, "where each trajectory stops is the baseline's own finding"
    got = door.count(PLAN, STOPS)
    ran = [
        sum(a["stepped"] for a in acts(f"round-{r}-machine-{k}"))
        for r in (1, 2)
        for k in range(5)
    ]
    assert got["per_run"] == ran and got["stepped"] == sum(ran) == 336379
    assert got["alone"] == sum(
        a["stepped"] for a in acts("baseline-1") if a["mode"] == "alone"
    )
    kept = sum(1 for r in (1, 2) for k in range(5)
               for line in (STUDY / "runs" / f"round-{r}-machine-{k}" / "memory.jsonl").read_text().splitlines()
               if '"step"' in line)  # fmt: skip
    assert got["states_kept"] == kept == 3473
    check = door.as_run(PLAN, STOPS)
    did = acts("check")
    assert (
        check["state_checks"]
        == sum(a["stepped"] for a in did if a["mode"] == "check")
        == 41410
    )
    assert (
        check["afresh"]
        == sum(a["stepped"] for a in did if a["mode"] == "afresh")
        == 121940
    )


def test_a_lie_is_found_by_a_check_that_looks_and_not_by_one_that_does_not():
    plan = {**PLAN, "rounds": 4}
    honest = door.count(plan, STOPS, check=1, draw=0)
    assert (honest["lies_told"], honest["again"], honest["wrong_handed_out"]) == (
        0,
        0,
        0,
    )
    every = door.count(plan, STOPS, check=1, draw=0, liar=2, tip=True)
    assert (
        every["lies_found"],
        every["wrong_handed_out"],
        every["found_in_round"],
    ) == (1, 0, 2)
    assert every["standing_lost"] == 1 and every["stepped"] >= honest["stepped"]
    none = door.count(plan, STOPS, check=0, draw=0, liar=2, tip=True)
    assert none["lies_found"] == 0 and none["checking"] == 0
    assert none["wrong_handed_out"] == none["wrong_never_found"] > 0
    assert none["saving_after_the_door"] == none["saving"]


def test_a_signer_nobody_enrolled_is_held_until_all_it_kept_is_stepped_again():
    plan = {**PLAN, "rounds": 4}
    known = door.count(plan, STOPS, signers=5, enrolled=5, check=8, draw=0)
    strangers = door.count(plan, STOPS, signers=5, enrolled=0, check=8, draw=0)
    assert known["held_rounds"] == 0 and strangers["held_rounds"] == 5
    assert strangers["stepped"] == known["stepped"], (
        "the stepping is the same; the door costs checking"
    )
    assert strangers["checking"] > known["checking"]
    assert strangers["saving_after_the_door"] < known["saving_after_the_door"]
    once = door.count(plan, STOPS, signers=20, enrolled=0, check=8, draw=0)
    assert once["held_rounds"] == 20 and once["checking"] >= once["stepped"] * 0.99, (
        "signers who never come back are stepped again whole"
    )


def test_more_of_everything_is_the_same_arithmetic():
    plan, stops = door.scaled(PLAN, STOPS, 3)
    got = door.count(plan, stops)
    assert got["jobs"] == 660 and got["alone"] == 3 * 1256518
    assert len(plan["trajectories"]) == 66 and len(stops) == 12
    assert abs(got["saving"] - 73.2) < 0.6
    assert door.scaled(PLAN, STOPS, 1) == (PLAN, STOPS)


def test_the_tables_kept_are_what_counting_again_gives(capsys):
    kept = json.loads((HERE / "results" / "tables.json").read_text())
    assert kept["the first study's own check"] == door.as_run(PLAN, STOPS)
    again = door.tables(PLAN, STOPS, seeds=3)
    assert again["size"] == kept["size"] and again["strangers"] == kept["strangers"]
    checked = kept["checked"]
    assert [name for name, _, _ in door.LEVELS] == list(checked)
    whole = checked["every state, no job afresh"]
    assert (whole["found"], whole["wrong_jobs_handed_out"]) == (60, 0)
    assert (
        checked["nothing"]["found"] == 0
        and checked["nothing"]["saving_after_the_door"] == 73.2
    )
    assert checked["every state and every served job"]["saving_after_the_door"] < 0
    assert door.main(["count", "--plan", str(STUDY / "plan.json"), "--stops", str(HERE / "stops.json")]) == 0  # fmt: skip
    assert "336379" in capsys.readouterr().out
    assert door.main(["count"]) == 2 and door.main([]) == 2


def test_the_probe_ticks_into_its_own_folder_and_says_no_secrets_value(tmp_path, capsys, monkeypatch):  # fmt: skip
    import probe

    monkeypatch.setenv("PROBE_SECONDS", "0")
    monkeypatch.setenv("PROBE_OUT", str(tmp_path))
    assert probe.main() == 0
    said = json.loads((tmp_path / "probe.json").read_text())
    assert said["ticks"] == 1 and said["same_machine"] is True
    assert (tmp_path / "ticks.txt").read_text().startswith("tick 0 of run ")
    assert (
        "its value is not said" in probe.secret.__doc__
        or "never what it is" in probe.secret.__doc__
    )
    assert "no secrets client here" in said["secret"]
    assert "tick 0" in capsys.readouterr().out
    assert sorted(p.name for p in tmp_path.iterdir()) == ["probe.json", "ticks.txt"]
