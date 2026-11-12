"""shared-runs, the door on Kaggle: the notebooks made run in order with a
made-up stepper and come to what the first study's runner comes to; a part
that comes back on another kind is begun over and says so; and held.py
passes what is right and fails what is not."""

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
import held  # noqa: E402
import door_notebooks as notebooks  # noqa: E402
import sweep  # noqa: E402

PLAN = {
    "machines": 2, "rounds": 2, "spacing": 10, "draw_one_in": 2, "check_one_in": 2,
    "deal_seed": "a deal", "draw_seed": "a draw", "lengths": [7, 25, 60, 133],
    "trajectories": [{"name": f"t{i}", "toy": {"seed": i, **({"halts_after": 23} if i == 2 else {})}}
                     for i in range(1, 6)],
}  # fmt: skip


def made(tmp: Path) -> tuple[Path, Path, dict]:
    (tmp / "plan.json").write_text(json.dumps(PLAN))
    (tmp / "starts.json").write_text(json.dumps({t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}))  # fmt: skip
    names = notebooks.make(
        tmp / "plan.json", tmp / "starts.json", "acct-zz9", tmp / "nb", cut=0
    )
    plan = sweep.load(tmp / "plan.json")
    assert names == [r["name"] for r in notebooks.roles(plan, 0)] and len(names) == 7
    return tmp / "nb", tmp / "runs", plan


def push(nb: Path, runs: Path, role: dict, tmp: Path, spoil=None) -> int:
    given = tmp / "in" / role["name"]
    given.mkdir(parents=True)
    for need in role["needs"]:
        shutil.copytree(runs / need, given / notebooks.slug(need) / need)
        if spoil:
            spoil(given / notebooks.slug(need) / need)
    env = {"SHARED_RUNS_INPUT": str(given), "SHARED_RUNS_WORKING": str(runs),
           "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
    return subprocess.run([sys.executable, str(nb / role["name"] / "run.py")], env=env,
                          capture_output=True).returncode  # fmt: skip


def first_study(tmp: Path, plan: dict) -> Path:
    """The same plan through the first study's own runner."""
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


def test_the_notebooks_run_in_order_and_come_to_the_first_studys_runs(tmp_path):
    nb, runs, plan = made(tmp_path)
    for role in notebooks.roles(plan, 0):
        assert push(nb, runs, role, tmp_path) == 0, role["name"]
    ring = held.machine.ring_of(nb / "ring.json")
    f = held.figures(plan, runs, ring, first_study(tmp_path, plan))
    v = held.verdicts(f)
    assert [v[r][0] for r in ("K1", "K2", "K4", "K5", "K6")] == ["passed"] * 5, v
    assert v["K3"][0] == "not tested", (
        "a budget of nothing stops before any job, not inside one"
    )
    assert f["carried"] == ["round-1-machine-0", "round-1-machine-1"] == f["cut"]
    assert f["stepped"] == f["first_study"] > 0 and f["check"]["halts"] >= 1
    assert held.main(["--runs", str(runs), "--ring", str(nb / "ring.json")]) == 42
    # a state changed after it came back: K1 and K2 fail
    text = (runs / "round-2-machine-0" / "memory.jsonl").read_text()
    (runs / "round-2-machine-0" / "memory.jsonl").write_text(text.replace('"state": "', '"state": "ff', 1))  # fmt: skip
    v = held.verdicts(held.figures(plan, runs, ring, tmp_path / "theirs"))
    assert v["K1"][0] == v["K2"][0] == "failed" and "round-2-machine-0" in v["K2"][1]
    # one that did not come back: nothing passes on what is there
    shutil.rmtree(runs / "check")
    v = held.verdicts(held.figures(plan, runs, ring, tmp_path / "theirs"))
    assert (
        v["K5"][0] == "not tested"
        and "check" in v["K6"][1]
        and v["K6"][0] == "not tested"
    )


def test_a_part_that_comes_back_on_another_kind_is_begun_over_and_says_so(tmp_path):
    nb, runs, plan = made(tmp_path)
    every = notebooks.roles(plan, 0)

    def another_kind(folder: Path) -> None:
        if folder.name == "round-1-machine-0-a":
            said = json.loads((folder / "machine.json").read_text())
            (folder / "machine.json").write_text(
                json.dumps({**said, "kind": "another kind"})
            )

    for role in every:
        assert push(nb, runs, role, tmp_path, another_kind) == 0, role["name"]
    over = json.loads((runs / "round-1-machine-0" / "restarted.json").read_text())
    assert "kind of processor" in over["refused"]
    f = held.figures(
        plan, runs, held.machine.ring_of(nb / "ring.json"), first_study(tmp_path, plan)
    )
    v = held.verdicts(f)
    assert f["begun_over"] == ["round-1-machine-0"] and f["carried"] == [
        "round-1-machine-1"
    ]
    assert v["K2"][0] == v["K4"][0] == v["K1"][0] == "passed", v


def test_a_notebook_without_its_inputs_stops_and_the_maker_keeps_names_out(
    tmp_path, capsys
):
    nb, runs, plan = made(tmp_path)
    role = next(r for r in notebooks.roles(plan, 0) if r["name"] == "round-2-machine-1")
    runs.mkdir()
    assert push(nb, runs, {**role, "needs": []}, tmp_path) != 0
    meta = json.loads((nb / "round-2-machine-1" / "kernel-metadata.json").read_text())
    assert meta["is_private"] is True and meta["enable_gpu"] is False
    assert meta["kernel_sources"] == ["acct-zz9/shared-runs-door-round-1-machine-1"], (
        "its own place only"
    )
    assert "acct-zz9" not in (nb / "round-2-machine-1" / "run.py").read_text()
    seeds = {(nb / n / "run.py").read_text().split("SEED = ")[1].split("\n")[0]
             for n in ("round-1-machine-0-a", "round-1-machine-0", "round-1-machine-1", "check")}  # fmt: skip
    assert len(seeds) == 3, "one identity a place, and one for the check"
    inside = HERE / "nb-should-not-be-made"
    assert (
        notebooks.main(["make", "--user", "acct-zz9", "--to", str(inside)]) == 2
        and not inside.exists()
    )
    assert (
        notebooks.main(["make", "--user", "not a name", "--to", str(tmp_path / "x")])
        == 2
    )
    assert notebooks.main(["nonsense"]) == 2
    assert held.main([]) == 2
