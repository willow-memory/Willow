"""shared-runs, a liar the ring trusts: with a made-up stepper the notebooks
run in order; the liar is taken before anyone looks and wrong bytes go out;
the check finds it; after, it and the round that went on from it are held and
every byte is right. And seen.py fails what is not so."""

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
import seen  # noqa: E402
import sweep  # noqa: E402
import trusted_notebooks as nbs  # noqa: E402

PLAN = {
    "machines": 5, "rounds": 2, "spacing": 10, "draw_one_in": 2, "check_one_in": 2,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133, 210],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23} if i % 9 == 2 else {})}}
                     for i in range(1, 31)],
}  # fmt: skip


def first_study(tmp: Path, plan: dict) -> Path:
    out = tmp / "theirs"
    base = [
        "--plan",
        str(tmp / "plan.json"),
        "--starts",
        str(tmp / "starts.json"),
        "--toy",
    ]
    for r in range(1, plan["rounds"] + 1):
        for k in range(plan["machines"]):
            cmd = [sys.executable, str(STUDY / "runner.py"), "shared", *base, "--machine", str(k),
                   "--round", str(r), "--to", str(out / f"round-{r}-machine-{k}")]  # fmt: skip
            for q in range(1, r):
                for j in range(plan["machines"]):
                    cmd += ["--memory", str(out / f"round-{q}-machine-{j}")]
            assert subprocess.run(cmd).returncode == 0
    return out


def test_the_trusted_liar_is_taken_then_found_then_held(tmp_path):
    (tmp_path / "plan.json").write_text(json.dumps(PLAN))
    (tmp_path / "starts.json").write_text(json.dumps({t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}))  # fmt: skip
    nb, runs = tmp_path / "nb", tmp_path / "runs"
    names = nbs.make(tmp_path / "plan.json", tmp_path / "starts.json", "acct-zz9", nb)
    plan = sweep.load(tmp_path / "plan.json")
    assert len(names) == 12 and names[-2:] == ["check", "round-2-machine-3-after"]
    for role in nbs.roles(plan):
        given = tmp_path / "in" / role["name"]
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
        assert done.returncode == 0, (role["name"], done.stderr[-300:])
    ring = seen.machine.ring_of(nb / "ring.json")
    assert len(ring) == 11, "every signer is in the ring, the liar among them"
    theirs = first_study(tmp_path, plan)
    f = seen.figures(plan, runs, ring, theirs)
    v = seen.verdicts(plan, f)
    assert [how for how, _ in v.values()] == ["passed"] * 5, v
    assert (
        len(f["wrong"]["round-2-machine-3-before"]) >= 2
        and f["wrong"]["round-2-machine-3-after"] == []
    )
    assert seen.main(["--runs", str(runs), "--ring", str(nb / "ring.json"), "--against", str(theirs),
                      "--plan", str(tmp_path / "plan.json")]) == 0  # fmt: skip

    # seen.py fails what is not so: had the door gone on taking the liar after the check
    spoiled = tmp_path / "spoiled"
    shutil.copytree(runs, spoiled)
    shutil.rmtree(spoiled / "round-2-machine-3-after")
    shutil.copytree(
        spoiled / "round-2-machine-3-before", spoiled / "round-2-machine-3-after"
    )
    v = seen.verdicts(plan, seen.figures(plan, spoiled, ring, theirs))
    assert v["N4"][0] == "failed" and v["N2"][0] == "passed"
    (spoiled / "round-1-machine-3.lied.json").unlink()
    v = seen.verdicts(plan, seen.figures(plan, spoiled, ring, theirs))
    assert v["N2"][0] == v["N3"][0] == "not tested"
    shutil.rmtree(spoiled / "check")
    assert {
        how
        for how, _ in seen.verdicts(
            plan, seen.figures(plan, spoiled, ring, theirs)
        ).values()
    } == {"not tested"}


def test_the_maker_keeps_names_out_and_refuses_a_bad_line(tmp_path):
    inside = HERE / "nb-should-not-be-made"
    assert (
        nbs.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
    assert nbs.main(["make", "--user", "acct-zz9", "--to", str(tmp_path / "nb")]) == 0
    assert (
        "acct-zz9" not in (tmp_path / "nb" / "round-1-machine-3" / "run.py").read_text()
    )
    meta = json.loads(
        (
            tmp_path / "nb" / "round-2-machine-3-after" / "kernel-metadata.json"
        ).read_text()
    )
    assert meta["kernel_sources"] == [f"acct-zz9/shared-runs-trusted-{n}" for n in
                                      ("round-1-machine-3", "round-2-machine-3-before", "check")]  # fmt: skip
    assert (
        len(
            json.loads(
                (tmp_path / "nb" / "check" / "kernel-metadata.json").read_text()
            )["kernel_sources"]
        )
        == 6
    )
    assert nbs.main(["nonsense"]) == 2 and seen.main([]) == 2
