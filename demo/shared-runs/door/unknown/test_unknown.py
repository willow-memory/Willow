"""shared-runs, nobody known: with a made-up stepper every round holds what it
is given, the saving falls to what was counted beforehand, and every job still
ends as it did where every signer was enrolled. And fell.py fails what is not so."""

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
import fell  # noqa: E402
import sweep  # noqa: E402
import unknown_notebooks as nbs  # noqa: E402

PLAN = {
    "machines": 3, "rounds": 3, "spacing": 10, "draw_one_in": 2, "check_one_in": 1,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133, 210, 222],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23 * (i % 3)} if i % 4 == 2 else {})}}
                     for i in range(1, 13)],
}  # fmt: skip


def run_all(tmp: Path, maker, name: str) -> tuple[Path, Path]:
    nb, runs = tmp / f"nb-{name}", tmp / f"runs-{name}"
    maker.make(tmp / "plan.json", tmp / "starts.json", "acct-zz9", nb)
    plan = sweep.load(tmp / "plan.json")
    for role in maker.roles(plan):
        given = tmp / f"in-{name}" / role["name"]
        given.mkdir(parents=True)
        for need in role["needs"]:
            shutil.copytree(runs / need, given / maker.slug(need) / need)
        env = {"SHARED_RUNS_INPUT": str(given), "SHARED_RUNS_WORKING": str(runs),
               "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
        done = subprocess.run(
            [sys.executable, str(nb / role["name"] / "run.py")],
            env=env,
            capture_output=True,
        )
        assert done.returncode == 0, (role["name"], done.stderr[-300:])
    return nb, runs


def test_nobody_known_every_round_is_held_and_the_saving_falls_to_what_was_counted(
    tmp_path,
):
    (tmp_path / "plan.json").write_text(json.dumps(PLAN))
    starts = {t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}
    (tmp_path / "starts.json").write_text(json.dumps(starts))
    plan = sweep.load(tmp_path / "plan.json")
    _, enrolled = run_all(tmp_path, nbs.grown, "enrolled")
    nb, runs = run_all(tmp_path, nbs, "unknown")
    ring = fell.machine.ring_of(nb / "ring.json")
    assert len(ring) == 1
    f = fell.figures(plan, starts, runs, ring, enrolled)
    v = fell.verdicts(f)
    assert [how for how, _ in v.values()] == ["passed"] * 5, v
    assert f["stepped"] == f["foretold"]["stepped"], (
        "counted to the step, with a made-up stepper"
    )
    assert f["stepped"] > f["enrolled_stepped"] and f["wrong"] == []
    assert (
        len(
            {
                json.loads((runs / n / "manifest.json").read_text())["signer"]
                for n in f["standing"]
            }
        )
        == 9
    )
    args = ["--runs", str(runs), "--ring", str(nb / "ring.json"), "--against", str(enrolled),
            "--plan", str(tmp_path / "plan.json"), "--starts", str(tmp_path / "starts.json")]  # fmt: skip
    assert fell.main(args) == 0 and fell.main(["foretell", *args[4:]]) == 0

    # fell.py fails what is not so: the enrolled sweep passed off as this one
    v = fell.verdicts(fell.figures(plan, starts, enrolled, ring, enrolled))
    assert v["U2"][0] == v["U3"][0] == "failed" and v["U4"][0] == "passed"
    acts = runs / "round-2-machine-0" / "acts.jsonl"
    text = acts.read_text()
    acts.write_text(text.replace('"sha256":"', '"sha256":"00', 1))
    v = fell.verdicts(fell.figures(plan, starts, runs, ring, enrolled))
    assert v["U4"][0] == "failed" and v["U1"][0] == "failed"
    shutil.rmtree(runs / "check-1")
    assert {
        how
        for how, _ in fell.verdicts(
            fell.figures(plan, starts, runs, ring, enrolled)
        ).values()
    } == {"not tested"}


def test_a_bad_command_line_is_refused(tmp_path):
    assert (
        nbs.main(["nonsense"]) == 2
        and fell.main([]) == 2
        and fell.main(["foretell"]) == 2
    )
    inside = HERE / "nb-should-not-be-made"
    assert (
        nbs.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
