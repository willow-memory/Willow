"""shared-runs, strangers cleared every round: with a made-up stepper the
strangers' rounds are taken on the checker's word, every round is the enrolled
sweep's byte for byte, and the clearings look at each state once and step what
was counted. And bought.py fails what is not so."""

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
import bought  # noqa: E402
import cleared_notebooks as nbs  # noqa: E402
import sweep  # noqa: E402

PLAN = {
    "machines": 5, "rounds": 4, "spacing": 10, "draw_one_in": 2, "check_one_in": 1,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133, 210, 222],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23 * (i % 3)} if i % 4 == 2 else {})}}
                     for i in range(1, 31)],
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
        assert done.returncode == 0, (role["name"], done.stderr[-400:])
    return nb, runs


def test_strangers_cleared_every_round_cost_the_clearings_and_nothing_of_the_sweep(
    tmp_path,
):
    (tmp_path / "plan.json").write_text(json.dumps(PLAN))
    starts = {t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}
    (tmp_path / "starts.json").write_text(json.dumps(starts))
    plan = sweep.load(tmp_path / "plan.json")
    names = [r["name"] for r in nbs.roles(plan)]
    assert (
        len(names) == 20 + 6 + 5
        and names[5:7] == ["clear-1-1", "clear-1-3"]
        and "clear-4-1" not in names
    )
    _, enrolled = run_all(tmp_path, nbs.grown, "enrolled")
    nb, runs = run_all(tmp_path, nbs, "cleared")
    ring = bought.machine.ring_of(nb / "ring.json")
    assert len(ring) == 3 + 2 + 5, (
        "three places, two checkers and five checks; no stranger's round"
    )
    f = bought.figures(plan, starts, runs, ring, enrolled)
    v = bought.verdicts(f)
    assert [how for how, _ in v.values()] == ["passed"] * 5, v
    assert (
        f["stepped"] == f["enrolled_stepped"]
        and f["clears"]["stepped"] == f["foretold_clears"] > 0
    )
    assert f["clears"]["looked"] == f["clears"]["of"] > 0 and f["clears"]["twice"] == 0
    second = bought.rows(runs / "clear-2-1" / "acts.jsonl")
    first = bought.rows(runs / "clear-1-1" / "acts.jsonl")
    assert second[: len(first)] == first and {
        a["of"] for a in second[len(first) :]
    } <= {"round-2-machine-1"}
    args = ["--runs", str(runs), "--ring", str(nb / "ring.json"), "--against", str(enrolled),
            "--plan", str(tmp_path / "plan.json"), "--starts", str(tmp_path / "starts.json")]  # fmt: skip
    assert bought.main(args) == 0 and bought.main(["foretell", *args[4:]]) == 0

    # bought.py fails what is not so: the enrolled sweep's rounds in place of the strangers'
    spoiled = tmp_path / "spoiled"
    shutil.copytree(runs, spoiled)
    shutil.rmtree(spoiled / "round-2-machine-1")
    shutil.copytree(enrolled / "round-2-machine-1", spoiled / "round-2-machine-1")
    v = bought.verdicts(bought.figures(plan, starts, spoiled, ring, enrolled))
    assert v["C2"][0] == "failed" and v["C3"][0] == "passed", (
        "it took its earlier round as enrolled, not on a check"
    )
    shutil.rmtree(spoiled / "clear-3-3")
    assert {
        how
        for how, _ in bought.verdicts(
            bought.figures(plan, starts, spoiled, ring, enrolled)
        ).values()
    } == {"not tested"}


def test_a_bad_command_line_is_refused(tmp_path):
    assert (
        nbs.main(["nonsense"]) == 2
        and bought.main([]) == 2
        and bought.main(["foretell"]) == 2
    )
    inside = HERE / "nb-should-not-be-made"
    assert (
        nbs.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
