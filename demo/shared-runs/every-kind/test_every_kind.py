"""shared-runs, every kind: a machine that ran the whole sweep alone is held
to the baseline job by job, and a job counts for a kind only when that
kind ran it from its start."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / "study"))
import every_kind  # noqa: E402
import runner  # noqa: E402
import sweep  # noqa: E402

PLAN = {
    "machines": 2, "rounds": 2, "spacing": 10, "draw_one_in": 2, "check_one_in": 2,
    "deal_seed": "a", "draw_seed": "b", "lengths": [7, 25, 40],
    "trajectories": [{"name": "t1", "toy": {"seed": 1}},
                     {"name": "t2", "toy": {"seed": 2, "halts_after": 23}}],
}  # fmt: skip


def made(tmp_path: Path) -> tuple[Path, Path, Path]:
    file = tmp_path / "plan.json"
    file.write_text(json.dumps(PLAN))
    starts = tmp_path / "starts.json"
    starts.write_text(json.dumps(sweep.starts(PLAN, tmp_path)))
    base = ["--plan", str(file), "--starts", str(starts), "--toy"]
    for to in ("study/baseline-1", "added/laptop", "added/phone"):
        assert runner.main(["alone", *base, "--to", str(tmp_path / to)]) == 0
    for name, kind in (
        ("study/baseline-1", "k1"),
        ("added/laptop", "k2"),
        ("added/phone", "k3"),
    ):
        said = json.loads((tmp_path / name / "machine.json").read_text())
        (tmp_path / name / "machine.json").write_text(
            json.dumps({**said, "kind": kind})
        )
    return file, tmp_path / "study", tmp_path / "added"


def states(file: Path, study: Path, added: Path) -> dict:
    return every_kind.judged(sweep.load(file), study / "baseline-1", added, study)[1]


def test_a_machine_is_held_to_the_baseline_job_by_job(tmp_path):
    file, study, added = made(tmp_path)
    v = states(file, study, added)
    assert v["E1"]["state"] == "passed" and v["E1"]["figures"]["laptop"]["same"] == 6
    assert v["E2"]["figures"]["by_kind"] == {"k1": 6, "k2": 6, "k3": 6}
    assert v["E2"]["figures"]["jobs_by_number_of_kinds"][3] == 6
    acts = (added / "laptop" / "acts.jsonl").read_text().splitlines()
    one = json.loads(acts[1])
    (added / "laptop" / "acts.jsonl").write_text("\n".join([acts[0], json.dumps({**one, "sha256": "0" * 64}), *acts[2:]]) + "\n")  # fmt: skip
    v = states(file, study, added)
    assert v["E1"]["state"] == "failed" and v["E1"]["figures"]["laptop"]["differ"] == [
        one["job"]
    ]
    (added / "laptop" / "acts.jsonl").write_text("\n".join(acts[:4]) + "\n")
    v = states(file, study, added)
    assert v["E1"]["state"] == "not tested" and "laptop" in v["E1"]["said"]


def test_a_job_counts_for_a_kind_only_when_that_kind_ran_it_from_its_start(tmp_path):
    file, study, added = made(tmp_path)
    served = study / "round-2-machine-0"
    served.mkdir()
    (served / "machine.json").write_text(json.dumps({"kind": "k4"}))
    row = {
        "mode": "shared",
        "job": "t1@40",
        "outcome": "ended",
        "ended": 40,
        "sha256": "x",
    }
    (served / "acts.jsonl").write_text(json.dumps({**row, "took": True}) + "\n")
    assert "k4" not in states(file, study, added)["E2"]["figures"]["by_kind"]
    (served / "acts.jsonl").write_text(json.dumps({**row, "took": False}) + "\n")
    assert states(file, study, added)["E2"]["figures"]["by_kind"]["k4"] == 1
    empty = tmp_path / "none"
    empty.mkdir()
    assert states(file, study, empty)["E1"]["state"] == "not tested"


def test_before_any_machine_is_added_the_study_has_each_job_in_full_on_one_kind(
    tmp_path,
):
    study = HERE.parent / "study"
    plan = sweep.load(study / "plan.json")
    before = every_kind.judged(
        plan, study / "runs" / "baseline-1", tmp_path, study / "runs"
    )[1]
    assert before["E1"]["state"] == "not tested"
    assert before["E2"]["figures"]["by_kind"] == {
        "intel x86_64 avx2": 220,
        "intel x86_64 avx512": 20,
    }, "the AMD machine's jobs all went on from the memory; none was from its start"


def test_the_command_line_refuses_what_it_cannot_judge(tmp_path, capsys):
    file, study, added = made(tmp_path)
    args = [
        "--plan",
        str(file),
        "--truth",
        str(study / "baseline-1"),
        "--runs",
        str(added),
    ]
    assert every_kind.main(args) == 0
    assert "E1: passed" in capsys.readouterr().out
    assert (
        every_kind.main(args + ["--box", str(tmp_path / "nobox"), "--gate", "g"]) == 2
    )
    assert every_kind.main(args + ["--box", str(tmp_path)]) == 2
    assert every_kind.main(["--plan", str(file)]) == 2 and every_kind.main([]) == 2
    assert every_kind.main(["--plan", str(file), "--truth", str(added / "laptop"), "--runs", str(added), "--gate", "x", "--box", str(tmp_path)]) == 2  # fmt: skip


def test_what_has_come_back_is_what_the_page_says():
    study = HERE.parent / "study"
    kept = json.loads((HERE / "results" / "verdicts.json").read_text())["verdicts"]
    live = every_kind.judged(sweep.load(study / "plan.json"), study / "runs" / "baseline-1", HERE / "runs", study / "runs")[1]  # fmt: skip
    assert json.loads(json.dumps(live)) == kept, (
        "what is kept is what judging again gives"
    )
    cloud = kept["E1"]["figures"]["cloud-session"]
    assert kept["E1"]["state"] == "passed" and (cloud["ran"], cloud["same"]) == (
        220,
        220,
    )
    assert kept["E2"]["figures"]["by_kind"]["intel x86_64 avx512"] == 220
    rows = [
        json.loads(x)
        for x in (HERE / "results" / "record.jsonl").read_text().splitlines()
    ]
    assert [r.get("gate") for r in rows[-2:]] == ["shared-runs:every-kind:E1", "shared-runs:every-kind:E2"]  # fmt: skip
    frozen = json.loads((HERE / "FROZEN.json").read_text())
    assert rows[-2]["tools"]["every_kind.py"] == frozen["files"]["every_kind.py"]
