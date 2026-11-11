"""shared-runs, the study's scripts: the deal gives every job once, a job
run with the memory is the bytes of the job run alone, each rule fails when
what it guards is broken, and the dry run is never the study's sweep."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import account  # noqa: E402
import dry  # noqa: E402
import judge  # noqa: E402
import runner  # noqa: E402
import sweep  # noqa: E402

PLAN = {
    "machines": 3, "rounds": 2, "spacing": 10, "draw_one_in": 3, "check_one_in": 2,
    "deal_seed": "a", "draw_seed": "b", "lengths": [7, 15, 32, 50],
    "trajectories": [
        {"name": "t1", "toy": {"seed": 1}},
        {"name": "t2", "toy": {"seed": 2, "halts_after": 23}},
        {"name": "t3", "toy": {"seed": 3, "halts_after": 0}},
        {"name": "t4", "toy": {"seed": 4}},
    ],
}  # fmt: skip


def whole(tmp_path: Path, plan: dict = PLAN) -> tuple[Path, Path]:
    """The plan run as the study would be, with the made-up stepper: the
    baseline twice, each round's machines, then the check."""
    file = tmp_path / "plan.json"
    file.write_text(json.dumps(plan))
    starts = tmp_path / "starts.json"
    starts.write_text(json.dumps(sweep.starts(plan, tmp_path)))
    runs = tmp_path / "runs"
    base = ["--plan", str(file), "--starts", str(starts), "--toy"]
    for b in ("baseline-1", "baseline-2"):
        assert runner.main(["alone", *base, "--to", str(runs / b)]) == 0
        assert runner.main(["native", *base, "--to", str(runs / b)]) == 0
    given: list[str] = []
    for r in range(1, plan["rounds"] + 1):
        for k in range(plan["machines"]):
            to = runs / f"round-{r}-machine-{k}"
            assert runner.main(["shared", *base, "--machine", str(k), "--round", str(r), "--to", str(to), *given]) == 0  # fmt: skip
        for k in range(plan["machines"]):
            given += ["--memory", str(runs / f"round-{r}-machine-{k}")]
    assert runner.main(["check", *base, "--to", str(runs / "check"), *given]) == 0
    return file, runs


def rewrite(folder: Path, change) -> None:
    """Each act of one machine's run, put through `change`."""
    path = folder / "acts.jsonl"
    rows = [change(json.loads(line)) for line in path.read_text().splitlines()]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def states(file: Path, runs: Path) -> dict[str, str]:
    return {r: v["state"] for r, v in judge.judged(file, runs)[1].items()}


def test_the_deal_gives_every_job_once_to_the_machine_its_trajectory_belongs_to():
    plan = sweep.load(HERE / "plan.json")
    got = [
        (job, k)
        for r in range(plan["rounds"])
        for k in range(plan["machines"])
        for job, _, _ in sweep.mine(plan, k, r)
    ]
    assert sorted(j for j, _ in got) == sorted(j for j, _, _ in sweep.jobs(plan))
    assert len(got) == 220
    owners = {}
    for job, k in got:
        assert owners.setdefault(job.rpartition("@")[0], k) == k
    assert sweep.predicted(plan) == {"alone": 1481810, "once": 396000, "share": 73.3}
    assert sweep.as_dealt(plan) == 403390, "the order costs a little, and is counted"
    assert any(n % plan["spacing"] for n in plan["lengths"]), (
        "lengths all on the spacing would make the saving an identity"
    )


def test_the_draw_is_the_same_each_time_and_one_in_n_rounded_up():
    names = [f"n{i}" for i in range(21)]
    assert sweep.drawn("s", names, 10) == sweep.drawn("s", list(reversed(names)), 10)
    assert len(sweep.drawn("s", names, 10)) == 3
    assert sweep.drawn("s", names, 10) != sweep.drawn("t", names, 10)
    assert sweep.drawn("s", [], 10) == []


def test_a_job_run_with_the_memory_is_the_bytes_of_the_job_run_alone(tmp_path):
    file, runs = whole(tmp_path)
    f, v, _ = judge.judged(file, runs)
    assert f["differ"] == [] and f["jobs_run"] == 16 and f["shared_jobs"] == 16
    assert f["halted"] == ["t2"] and f["refused"] == ["t3"], "a refusal is not a halt"
    assert f["halts_tried"] == {"t2": 1}
    assert f["baseline_steps"] == 276 and f["shared_steps"] < 276
    assert f["states_checked"] and f["states_same"] == f["states_checked"]
    assert f["afresh"] == f["draw"] and f["afresh_same"] == len(f["draw"]) > 0
    assert {r: x["state"] for r, x in v.items()} == {
        "R1": "not tested", "R2": "measured", "R3": "failed", "R4": "passed",
        "R5": "measured", "R6": "passed", "R7": "not tested", "R8": "not tested",
        "R9": "not tested",
    }  # fmt: skip


def test_with_no_halt_the_shared_run_steps_what_the_plan_counts_as_dealt(tmp_path):
    plan = {**PLAN, "trajectories": [PLAN["trajectories"][0], PLAN["trajectories"][3]]}
    file, runs = whole(tmp_path, plan)
    f = judge.judged(file, runs)[0]
    assert f["shared_steps"] == sweep.as_dealt(plan)
    assert f["predicted_with_halts"] == f["predicted"] == sweep.predicted(plan)["share"]


def test_r1_needs_three_kinds_of_processor_and_fails_on_one_other_byte(tmp_path):
    file, runs = whole(tmp_path)
    assert states(file, runs)["R1"] == "not tested"
    for folder, kind in (("baseline-2", "another"), ("check", "a third")):
        said = json.loads((runs / folder / "machine.json").read_text())
        (runs / folder / "machine.json").write_text(json.dumps({**said, "kind": kind}))  # fmt: skip
    assert states(file, runs)["R1"] == "passed"

    def other(act):
        return {**act, "sha256": "0" * 64} if act.get("job") == "t1@50" and act["mode"] == "alone" else act  # fmt: skip

    rewrite(runs / "baseline-2", other)
    got = judge.judged(file, runs)
    assert got[1]["R1"]["state"] == "failed" and got[0]["differ"] == ["t1@50"]


def test_a_kind_is_the_maker_the_architecture_and_the_widest_vector_instructions():
    xeon = "Intel(R) Xeon(R) Processor @ 2.10GHz"
    assert runner.kind_of(xeon, "x86_64", {"AVX2", "AVX512F"}) == "intel x86_64 avx512"
    assert runner.kind_of("Intel(R) Xeon(R) CPU @ 2.20GHz", "AMD64", {"avx2", "fma"}) == "intel x86_64 avx2"  # fmt: skip
    assert runner.kind_of("AMD EPYC 7B12", "x86_64", {"avx2"}) == "amd x86_64 avx2"
    assert runner.kind_of("arm apple", "arm64", {"NEON", "ASIMD"}) == "apple arm64 neon"
    assert runner.kind_of("", "riscv64", set()) == "other riscv64 plain"
    assert runner.kind_of(xeon, "x86_64", {"avx2"}) == runner.kind_of(
        "Intel(R) Xeon(R) CPU @ 2.20GHz", "x86_64", {"avx2"}
    ), "another clock speed is not another kind"


def test_r6_fails_when_a_known_halt_is_stepped_into_again(tmp_path):
    file, runs = whole(tmp_path)
    again = [p for p in sorted(runs.glob("round-2-*")) if "t2@" in (p / "acts.jsonl").read_text()]  # fmt: skip
    rewrite(again[0], lambda a: {**a, "tried_halt": True} if a["trajectory"] == "t2" else a)  # fmt: skip
    assert states(file, runs)["R6"] == "failed"


def test_r4_is_not_tested_when_what_was_run_afresh_is_not_the_draw(tmp_path):
    file, runs = whole(tmp_path)
    rewrite(runs / "check", lambda a: {**a, "mode": "check", "same": True, "step": 1} if a["mode"] == "afresh" else a)  # fmt: skip
    assert states(file, runs)["R4"] == "not tested"


def test_an_agents_answers_are_held_to_the_key_and_its_account_to_the_report(tmp_path):
    file, runs = whole(tmp_path)
    plan = sweep.load(file)
    f = judge.figures(plan, judge.load(runs))
    keyed = account.key(f)
    assert keyed["seconds"] == account.NOT_SAID and keyed["jobs"] == "16"
    right = "\n".join(f"{name}: {answer}" for name, answer in keyed.items())
    said = "\n## account\nIt ran 16 jobs. One trajectory halted.\n"
    folder = runs / "account" / "one"
    folder.mkdir(parents=True)
    (folder / "answers.txt").write_text(right + said)
    assert [states(file, runs)[r] for r in ("R7", "R8", "R9")] == ["passed"] * 3
    (folder / "answers.txt").write_text(right.replace("jobs: 16", "jobs: 17") + said)
    assert [states(file, runs)[r] for r in ("R7", "R8", "R9")] == ["failed", "passed", "passed"]  # fmt: skip
    (folder / "answers.txt").write_text(right + said + "It took 4,321 seconds.\n")
    assert [states(file, runs)[r] for r in ("R7", "R8", "R9")] == ["passed", "failed", "passed"]  # fmt: skip
    (folder / "answers.txt").write_text(right)
    assert states(file, runs)["R8"] == "not tested", "no account is not a clean one"
    guessed = right.replace(f"cost: {account.NOT_SAID}", "cost: 12")
    (folder / "answers.txt").write_text(guessed + said)
    assert [states(file, runs)[r] for r in ("R7", "R8", "R9")] == ["passed", "passed", "failed"]  # fmt: skip
    for name, question, _ in account.QUESTIONS:
        assert f"{name}: {question}" in account.brief(plan, f)
    assert account.report(plan, f) in account.brief(plan, f)


def test_the_dry_run_runs_only_a_plan_that_says_it_is_one(tmp_path, capsys):
    assert json.loads((HERE / "dry-plan.json").read_text())["dry"] is True
    proposed = json.loads((HERE / "plan.json").read_text())
    assert "dry" not in proposed
    assert [c["name"] for c in proposed["check_machines"]] == ["kaggle-check", "laptop", "cloud-session"]  # fmt: skip
    assert proposed["project"]["numpy"] == "2.1.3"
    assert [a["name"] for a in proposed["agents"]] == ["small", "larger"]
    starts = json.loads((HERE / "starts.json").read_text())
    assert sorted(starts) == sorted(t["name"] for t in proposed["trajectories"])
    for start in starts.values():
        assert len(start["masses"]) == len(start["r"]) == len(start["v"])
        float.fromhex(start["dt"])
    args = ["--work", str(tmp_path / "w"), "--toy"]
    assert dry.main(["--plan", str(HERE / "plan.json"), *args]) == 2
    assert "does not say it is a dry one" in capsys.readouterr().err
    assert not (tmp_path / "w").exists()


def test_a_checkout_whose_stepper_is_not_the_plans_is_refused(tmp_path, capsys):
    core = tmp_path / "repo" / "simulations" / "star_system"
    core.mkdir(parents=True)
    (core / "core.py").write_text("# another stepper\n")
    plan = HERE / "dry-plan.json"
    starts = tmp_path / "starts.json"
    names = [t["name"] for t in json.loads(plan.read_text())["trajectories"]]
    starts.write_text(json.dumps({n: {} for n in names}))
    args = ["--plan", str(plan), "--starts", str(starts), "--to", str(tmp_path / "out")]
    assert runner.main(["alone", *args, "--repo", str(tmp_path / "repo")]) == 2
    assert "not the one the plan names" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()
    assert runner.main(["alone", *args]) == 2 and runner.main([]) == 2


def test_what_the_dry_run_kept_scores_as_its_page_says():
    kept = json.loads((HERE / "dry" / "verdicts.json").read_text())
    got = {r: v["state"] for r, v in kept["verdicts"].items()}
    assert got == {
        "R1": "not tested", "R2": "measured", "R3": "failed", "R4": "passed",
        "R5": "measured", "R6": "passed", "R7": "passed", "R8": "passed", "R9": "passed",
    }  # fmt: skip
    f = kept["figures"]
    assert (f["jobs"], f["baseline_steps"], f["shared_steps"], f["measured"]) == (30, 10656, 5451, 48.8)  # fmt: skip
    plan = sweep.load(HERE / "dry-plan.json")
    assert account.report(plan, f) == (HERE / "dry" / "report.txt").read_text()
    assert account.brief(plan, f) == (HERE / "dry" / "agent-input.txt").read_text()
    for name in ("small", "larger"):
        held = account.held(plan, f, (HERE / "dry" / f"answers-{name}.txt").read_text())
        assert set(held["marks"].values()) == {"right"} and held["struck"] == []


def test_the_notebooks_run_the_plan_each_given_only_the_rounds_before_it(tmp_path, monkeypatch):  # fmt: skip
    import shutil
    import subprocess

    import notebooks

    file = tmp_path / "plan.json"
    file.write_text(json.dumps(PLAN))
    starts = tmp_path / "starts.json"
    starts.write_text(json.dumps(sweep.starts(PLAN, tmp_path)))
    made = notebooks.make(file, starts, "someone", tmp_path / "nb")
    assert made == [r["name"] for r in notebooks.roles(PLAN)] and len(made) == 9
    meta = json.loads((tmp_path / "nb" / "check" / "kernel-metadata.json").read_text())
    assert meta["is_private"] is True and meta["enable_gpu"] is False
    assert meta["kernel_sources"] == [
        f"someone/shared-runs-round-{r}-machine-{k}" for r in (1, 2) for k in range(3)
    ]
    assert "someone" not in (tmp_path / "nb" / "check" / "run.py").read_text()
    runs = tmp_path / "runs"
    for role in notebooks.roles(PLAN):
        given = tmp_path / "in" / role["name"]
        given.mkdir(parents=True)
        for need in role["needs"]:
            shutil.copytree(runs / need, given / notebooks.slug(need) / need)
        env = {"SHARED_RUNS_INPUT": str(given), "SHARED_RUNS_WORKING": str(runs),
               "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
        script = tmp_path / "nb" / role["name"] / "run.py"
        assert subprocess.run([sys.executable, str(script)], env=env).returncode == 0
    f = judge.judged(file, runs)[0]
    assert f["differ"] == [] and f["shared_jobs"] == 16 and f["afresh"] == f["draw"]
    alone = tmp_path / "in" / "none"
    alone.mkdir()
    env = {"SHARED_RUNS_INPUT": str(alone), "SHARED_RUNS_WORKING": str(tmp_path / "x"),
           "SHARED_RUNS_STEPPER": "--toy", "PATH": ""}  # fmt: skip
    script = tmp_path / "nb" / "round-2-machine-1" / "run.py"
    got = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True)  # fmt: skip
    assert got.returncode != 0 and "not among the inputs" in got.stderr


def test_a_notebook_carries_the_frozen_files_and_is_made_outside_the_repository(tmp_path, capsys):  # fmt: skip
    import hashlib

    import notebooks

    frozen = json.loads((HERE / "FROZEN.json").read_text())["files"]
    assert (
        notebooks.main(["make", "--user", "someone", "--to", str(tmp_path / "nb")]) == 0
    )
    made = sorted(p.name for p in (tmp_path / "nb").iterdir())
    assert len(made) == 13 and "round-2-machine-4" in made
    scope: dict = {}
    text = (tmp_path / "nb" / "baseline-1" / "run.py").read_text()
    exec(text.rpartition("\nmain()\n")[0], scope)
    for name, body in scope["FILES"].items():
        assert hashlib.sha256(body.encode()).hexdigest() == frozen[name] == scope["SHA256"][name]  # fmt: skip
    assert sorted(scope["FILES"]) == [
        "plan.json",
        "runner.py",
        "starts.json",
        "sweep.py",
    ]
    assert notebooks.main(["make", "--user", "someone", "--to", str(HERE / "nb")]) == 2
    assert (
        notebooks.main(["make", "--user", "some one", "--to", str(tmp_path / "b")]) == 2
    )
    assert notebooks.main(["make", "--to", str(tmp_path / "c")]) == 2
    assert not (HERE / "nb").exists() and not (tmp_path / "b").exists()


def test_a_machine_trying_the_dry_sweep_is_told_how_its_bytes_compare(tmp_path):
    file, runs = whole(tmp_path)
    acts = [json.loads(x) for x in (runs / "baseline-1" / "acts.jsonl").read_text().splitlines()]  # fmt: skip
    kept = {"rewritten": {}, "as_written": {}}
    for a in acts:
        name = "rewritten" if a["mode"] == "alone" else "as_written"
        kept[name][a["job"]] = [a["outcome"], a["ended"], a["sha256"]]
    kept["as_written"]["t1@32"][2] = "0" * 64
    kept["as_written"]["t1@50"][2] = "0" * 64
    other = tmp_path / "bytes.json"
    other.write_text(json.dumps(kept))
    said = dry.against(runs, other)
    assert said[1] == "the power rewritten: 16 of 16 jobs the same bytes as the other machine"  # fmt: skip
    assert said[2].startswith("the power as written: 14 of 16") and said[2].endswith("differs is t1@32")  # fmt: skip
    real = json.loads((HERE / "dry" / "bytes.json").read_text())
    assert len(real["rewritten"]) == len(real["as_written"]) == 30
    page = (HERE / "TESTER.md").read_text()
    plan = json.loads((HERE / "dry-plan.json").read_text())["project"]
    assert plan["commit"] in page and f"numpy=={plan['numpy']}" in page
