"""shared-runs, strangers at the door: the notebooks made run in order with a
made-up stepper; the two nobody enrolled are held, the honest one is taken on
the checker's word, the liar's lie is found and never gone on from, and no job
comes to a wrong byte. And told.py fails what is not so."""

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
import strangers_notebooks as nbs  # noqa: E402
import sweep  # noqa: E402
import told  # noqa: E402

PLAN = {
    "machines": 5, "rounds": 2, "spacing": 10, "draw_one_in": 2, "check_one_in": 2,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133, 210],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23} if i % 9 == 2 else {})}}
                     for i in range(1, 31)],
}  # fmt: skip


def push(nb: Path, runs: Path, role: dict, tmp: Path) -> int:
    given = tmp / "in" / role["name"]
    given.mkdir(parents=True)
    for need in role["needs"]:
        shutil.copytree(runs / need, given / nbs.slug(need) / need)
    env = {"SHARED_RUNS_INPUT": str(given), "SHARED_RUNS_WORKING": str(runs),
           "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
    return subprocess.run([sys.executable, str(nb / role["name"] / "run.py")], env=env,
                          capture_output=True).returncode  # fmt: skip


def first_study(tmp: Path, plan: dict) -> Path:
    """The same plan through the first study's own runner, every machine honest."""
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


def test_the_strangers_are_held_the_honest_one_cleared_and_the_lie_found(tmp_path):
    (tmp_path / "plan.json").write_text(json.dumps(PLAN))
    (tmp_path / "starts.json").write_text(json.dumps({t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}))  # fmt: skip
    nb, runs = tmp_path / "nb", tmp_path / "runs"
    names = nbs.make(tmp_path / "plan.json", tmp_path / "starts.json", "acct-zz9", nb)
    plan = sweep.load(tmp_path / "plan.json")
    assert len(names) == 13 and names[-2:] == [
        "round-2-machine-1-after",
        "round-2-machine-3-after",
    ]
    for role in nbs.roles(plan):
        assert push(nb, runs, role, tmp_path) == 0, role["name"]
    ring = told.machine.ring_of(nb / "ring.json")
    assert len(ring) == 9 and len(json.loads((nb / "strangers.json").read_text())) == 2
    theirs = first_study(tmp_path, plan)
    f = told.figures(plan, runs, ring, theirs)
    v = told.verdicts(plan, f)
    assert [how for how, _ in v.values()] == ["passed"] * 5, v
    lied = f["lied"]
    assert ["round-1-machine-3", "check", *lied["state"]] in f["not_same"]
    assert ["round-1-machine-3", "halt-check", *lied["halt"]] in f["not_same"]
    assert (
        f["steps"]["round-2-machine-1-before"] > f["steps"]["round-2-machine-1-after"]
    )
    assert (
        f["steps"]["round-2-machine-3-before"] == f["steps"]["round-2-machine-3-after"]
    )
    assert told.main(["--runs", str(runs), "--ring", str(nb / "ring.json"), "--against", str(theirs),
                      "--plan", str(tmp_path / "plan.json")]) == 0  # fmt: skip

    # had the door taken the liar on its seal alone, wrong bytes would have gone out: the lie bites
    free = tmp_path / "free"
    code = told.machine.main(["shared", "--plan", str(tmp_path / "plan.json"), "--starts",
                              str(tmp_path / "starts.json"), "--toy", "--machine", "3", "--round", "2",
                              "--memory", str(runs / "round-1-machine-3"), "--to", str(free)])  # fmt: skip
    assert code == 0
    ends = {
        a["job"]: a["sha256"]
        for a in told.rows(theirs / "round-2-machine-3" / "acts.jsonl")
    }
    wrong = [
        a["job"]
        for a in told.rows(free / "acts.jsonl")
        if a["sha256"] != ends[a["job"]]
    ]
    assert len(wrong) >= 2, (
        "the changed state and the halt that is no halt each spoil a job"
    )

    # told.py fails what is not so: the liar's round 1 swapped for an honest one
    spoiled = tmp_path / "spoiled"
    shutil.copytree(runs, spoiled)
    shutil.rmtree(spoiled / "round-2-machine-1-after")
    shutil.copytree(
        spoiled / "round-2-machine-1-before", spoiled / "round-2-machine-1-after"
    )
    v = told.verdicts(plan, told.figures(plan, spoiled, ring, theirs))
    assert v["T4"][0] == "failed" and v["T2"][0] == "passed"
    shutil.rmtree(spoiled / "check")
    v = told.verdicts(plan, told.figures(plan, spoiled, ring, theirs))
    assert {how for how, _ in v.values()} == {"not tested"}


def test_the_maker_keeps_names_and_keys_out_and_refuses_a_bad_line(tmp_path):
    inside = HERE / "nb-should-not-be-made"
    assert (
        nbs.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
    assert nbs.main(["make", "--user", "acct-zz9", "--to", str(tmp_path / "nb")]) == 0
    text = (tmp_path / "nb" / "round-1-machine-3" / "run.py").read_text()
    assert "acct-zz9" not in text and "'lies': True" in text
    assert (
        "'lies': False"
        in (tmp_path / "nb" / "round-1-machine-1" / "run.py").read_text()
    )
    meta = json.loads(
        (
            tmp_path / "nb" / "round-2-machine-3-after" / "kernel-metadata.json"
        ).read_text()
    )
    assert meta["kernel_sources"] == ["acct-zz9/shared-runs-strangers-round-1-machine-3",
                                      "acct-zz9/shared-runs-strangers-check"]  # fmt: skip
    assert nbs.main(["nonsense"]) == 2 and told.main([]) == 2
    import lie

    assert lie.main([]) == 2
