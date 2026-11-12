"""shared-runs, the sweep grown: the notebooks made run in order with a made-up
stepper and grew.py passes them; what is changed, lost or not saved fails; and
the plan is ten times the first study's, with the first study's own inside it."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1] / "study"
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(STUDY))
import grew  # noqa: E402
import grown_notebooks as nbs  # noqa: E402
import sweep  # noqa: E402

PLAN = {
    "machines": 3, "rounds": 3, "spacing": 10, "draw_one_in": 2, "check_one_in": 1,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133, 210, 222],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23 * (i % 3)} if i % 4 == 2 else {})}}
                     for i in range(1, 13)],
}  # fmt: skip


def run_all(tmp: Path) -> tuple[Path, Path, dict, dict]:
    (tmp / "plan.json").write_text(json.dumps(PLAN))
    starts = {t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}
    (tmp / "starts.json").write_text(json.dumps(starts))
    nb, runs = tmp / "nb", tmp / "runs"
    names = nbs.make(tmp / "plan.json", tmp / "starts.json", "acct-zz9", nb)
    plan = sweep.load(tmp / "plan.json")
    assert len(names) == 12 and names[-3:] == ["check-0", "check-1", "check-2"]
    for role in nbs.roles(plan):
        given = tmp / "in" / role["name"]
        given.mkdir(parents=True)
        for need in role["needs"]:
            shutil.copytree(runs / need, given / nbs.slug(need) / need)
        env = {"SHARED_RUNS_INPUT": str(given), "SHARED_RUNS_WORKING": str(runs),
               "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
        done = subprocess.run(
            [sys.executable, str(nb / role["name"] / "run.py")],
            env=env,
            capture_output=True,
        )
        assert done.returncode == 0, role["name"]
    return nb, runs, plan, starts


def test_the_grown_notebooks_run_in_order_and_what_is_wrong_fails(tmp_path):
    nb, runs, plan, starts = run_all(tmp_path)
    ring = grew.machine.ring_of(nb / "ring.json")
    f = grew.figures(plan, starts, runs, ring, None)
    v = grew.verdicts(f)
    assert [v[r][0] for r in ("G1", "G2", "G3", "G4", "G5")] == ["passed"] * 5, v
    assert v["G6"][0] == "not tested" and f["jobs_done"] == f["jobs"] == 72
    assert f["halts"] and 0 in f["halts"].values(), (
        "one halts part way and one refuses its first step"
    )
    assert f["alone"] < sum(n for _, _, n in sweep.jobs(plan)), (
        "a halt shortens what alone would step"
    )
    assert f["stepped"] >= f["once"] and f["check"]["states"] == f["states"]
    meta = json.loads((nb / "round-3-machine-1" / "kernel-metadata.json").read_text())
    assert meta["kernel_sources"] == [
        f"acct-zz9/shared-runs-grown-round-{r}-machine-1" for r in (1, 2)
    ]
    assert (
        len(
            json.loads((nb / "check-2" / "kernel-metadata.json").read_text())[
                "kernel_sources"
            ]
        )
        == 3
    )
    args = ["--runs", str(runs), "--ring", str(nb / "ring.json"), "--plan", str(tmp_path / "plan.json"),
            "--starts", str(tmp_path / "starts.json")]  # fmt: skip
    assert grew.main(args) == 42, (
        "the anchor is not tested without the first study's runs"
    )

    # the anchor: jobs the first study also ran must come to its bytes
    theirs = tmp_path / "theirs" / "round-1-machine-0"
    theirs.mkdir(parents=True)
    some = grew.rows(runs / "round-1-machine-0" / "acts.jsonl")[:3]
    (theirs / "acts.jsonl").write_text("".join(json.dumps(a) + "\n" for a in some))
    assert (
        grew.verdicts(grew.figures(plan, starts, runs, ring, tmp_path / "theirs"))[
            "G6"
        ][0]
        == "passed"
    )
    some[0]["sha256"] = "0" * 64
    (theirs / "acts.jsonl").write_text("".join(json.dumps(a) + "\n" for a in some))
    assert (
        grew.verdicts(grew.figures(plan, starts, runs, ring, tmp_path / "theirs"))[
            "G6"
        ][0]
        == "failed"
    )

    # steps said twice: the saving is no longer what was foretold
    acts = runs / "round-1-machine-0" / "acts.jsonl"
    text = acts.read_text()
    acts.write_text(text + text)
    v = grew.verdicts(grew.figures(plan, starts, runs, ring, None))
    assert v["G1"][0] == "failed" and (v["G2"][0] == "failed" or v["G5"][0] == "failed")
    acts.write_text(text)
    shutil.rmtree(runs / "check-1")
    v = grew.verdicts(grew.figures(plan, starts, runs, ring, None))
    assert {how for how, _ in v.values()} == {"not tested"} and "check-1" in v["G3"][1]


def test_the_plan_is_ten_times_the_first_studys_with_the_first_studys_inside_it():
    plan, first = sweep.load(HERE / "plan.json"), sweep.load(STUDY / "plan.json")
    assert len(sweep.jobs(plan)) == 10 * len(sweep.jobs(first)) == 2200
    assert (plan["machines"], plan["rounds"], plan["spacing"]) == (5, 10, 100)
    assert set(first["lengths"]) < set(plan["lengths"]) and len(plan["lengths"]) == 20
    assert plan["project"] == first["project"]
    starts = json.loads((HERE / "starts.json").read_text())
    old = json.loads((STUDY / "starts.json").read_text())
    assert (
        set(starts) == {t["name"] for t in plan["trajectories"]} and len(starts) == 110
    )
    assert all(starts[name] == old[name] for name in old), (
        "the first study's setups, start for start"
    )
    assert len({json.dumps(s, sort_keys=True) for s in starts.values()}) == 110, (
        "no two starts the same"
    )
    assert max(len(r["needs"]) for r in nbs.roles(plan)) == 10


def test_a_bad_command_line_is_refused(tmp_path):
    assert nbs.main(["nonsense"]) == 2 and grew.main([]) == 2
    inside = HERE / "nb-should-not-be-made"
    assert (
        nbs.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
