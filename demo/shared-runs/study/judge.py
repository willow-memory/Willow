"""judge.py: the study's nine rules, each held to what the machines kept.

    python demo/shared-runs/study/judge.py --plan PLAN --runs FOLDER
        [--box DIR --gate NAME] [--json]

FOLDER holds one folder for each machine's run, as runner.py left it, and
may hold `account`, with one folder for each agent that answered: its
`answers.txt`. Nothing else is read: every figure is counted from the
acts, and a rule the acts can't decide is said to be not tested, never
passed.

    R1  the same bytes for every job on every machine that ran it, and
        for every kept state stepped again, on three kinds of processor
        (a kind is its maker, its architecture and its widest vector
        instructions, as each machine says of itself)
    R2  measured: the jobs whose bytes agree across machines with the
        project's gravity as it is written
    R3  the steps not stepped, as a share of the baseline's, within two
        points of the share the plan predicts
    R4  every served job the draw picked, run afresh, is the same bytes
    R5  measured: the steps one check of a kept state costs
    R6  no trajectory that began and halted is stepped into its halt twice
    R7  each agent's answers to the questions the reports answer are right
    R8  no sentence of an agent's account says a figure no report holds
    R9  each question the reports don't answer is answered so

With `--box`, each verdict is appended to that record as a row of kind
`verdict`, its gate `NAME:R1` and so on, with the SHA-256 of the acts and
answers it was judged from and of each tool. It reads the runs and writes
the record only. Exit codes, the kernel's: 0 no rule failed; 42 one did;
2 refused.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED, ESCALATE = 2, 42
PATCHED = ("alone", "shared", "afresh")
RULES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9")
TOOLS = ("sweep.py", "runner.py", "judge.py", "account.py")


def load(runs: Path) -> list[dict]:
    """Each machine's run: its folder's name, what it says of itself, its acts."""
    out = []
    for folder in sorted(p for p in runs.iterdir() if (p / "acts.jsonl").is_file()):
        lines = (folder / "acts.jsonl").read_text(encoding="utf-8").splitlines()
        said = json.loads((folder / "machine.json").read_text(encoding="utf-8"))
        out.append({"name": folder.name, "machine": said,
                    "acts": [json.loads(line) for line in lines]})  # fmt: skip
    return out


def result(act: dict) -> tuple:
    return act["outcome"], act["ended"], act["sha256"]


def figures(plan: dict, machines: list[dict]) -> dict:
    """Everything the rules and the reports say, counted from the acts."""
    acts = [(m, a) for m in machines for a in m["acts"]]
    of = lambda mode: [(m, a) for m, a in acts if a["mode"] == mode]  # noqa: E731
    jobs = [j for j, _, _ in sweep.jobs(plan)]
    f: dict = {"jobs": len(jobs), "trajectories": len(plan["trajectories"]),
               "predicted": sweep.predicted(plan)["share"]}  # fmt: skip

    baselines = [m for m in machines if any(a["mode"] == "alone" for a in m["acts"])]
    by_run = [
        {a["job"]: a for a in m["acts"] if a["mode"] == "alone"} for m in baselines
    ]
    f["baseline_runs"] = len(by_run)
    f["baseline_steps"] = sum(a["stepped"] for a in by_run[0].values()) if by_run else 0
    f["baseline_same"] = sum(
        1 for j in jobs
        if by_run and all(j in r for r in by_run)
        and len({result(r[j]) for r in by_run}) == 1
    )  # fmt: skip

    shared = [a for _, a in of("shared")]
    f["shared_jobs"] = len({a["job"] for a in shared})
    f["computed"] = sum(1 for a in shared if not a["took"])
    f["stepped_on"] = sum(1 for a in shared if a["took"] and a["stepped"])
    f["served"] = sum(1 for a in shared if a["took"] and not a["stepped"])
    f["shared_steps"] = sum(a["stepped"] for a in shared)
    f["shared_machines"] = len({(a["machine"], a["round"]) for a in shared})
    whole = f["baseline_steps"] and f["shared_jobs"] == len(jobs)
    # where the baseline, which has no memory, found a trajectory to stop
    stops: dict[str, int] = {}
    for a in by_run[0].values() if by_run else ():
        if a["outcome"] != "ended":
            stops[a["trajectory"]] = a["ended"]
    cut = lambda name, n: min(n, stops.get(name, n))  # noqa: E731
    alone = sum(cut(name, n) for _, name, n in sweep.jobs(plan))
    once = sum(
        cut(t["name"], max(sweep.lengths(plan, t))) for t in plan["trajectories"]
    )
    f["predicted_with_halts"] = round(100 * (1 - once / alone), 1) if alone else None
    f["measured"] = round(100 * (1 - f["shared_steps"] / f["baseline_steps"]), 1) if whole else None  # fmt: skip

    patched = [(m, a) for m, a in acts if a["mode"] in PATCHED]
    f["halted"] = sorted(
        {a["trajectory"] for _, a in patched if a["outcome"] == "halted"}
    )
    f["refused"] = sorted(
        {a["trajectory"] for _, a in patched if a["outcome"] == "refused"}
    )
    f["halts_tried"] = {
        t: sum(1 for a in shared if a["trajectory"] == t and a["tried_halt"])
        for t in f["halted"]
    }
    f["refusals_tried"] = {
        t: sum(1 for a in shared if a["trajectory"] == t and a["tried_halt"])
        for t in f["refused"]
    }

    said: dict[str, set] = {}
    kinds: dict[str, set] = {}
    for m, a in patched:
        said.setdefault(a["job"], set()).add(result(a))
        kinds.setdefault(a["job"], set()).add(m["machine"]["kind"])
    f["differ"] = sorted(j for j, got in said.items() if len(got) > 1)
    f["jobs_run"] = len(said)
    f["jobs_on_three_kinds"] = sum(1 for k in kinds.values() if len(k) >= 3)
    checks = of("check")
    f["states_checked"] = len(checks)
    f["states_same"] = sum(1 for _, a in checks if a["same"])
    f["check_steps"] = statistics.median(a["stepped"] for _, a in checks) if checks else None  # fmt: skip
    f["checked_by"] = sorted({m["name"] for m, _ in checks})
    f["median_job"] = statistics.median(n for _, _, n in sweep.jobs(plan))
    f["kinds"] = sorted(
        {m["machine"]["kind"] for m, _ in patched}
        | {m["machine"]["kind"] for m, _ in checks}
    )

    last = {a["job"]: a for a in shared}
    took = [a["job"] for a in shared if a["took"]]
    f["draw"] = sweep.drawn(plan["draw_seed"], took, plan["draw_one_in"])
    afresh = {a["job"]: a for _, a in of("afresh")}
    f["afresh"] = sorted(afresh)
    f["afresh_same"] = sum(
        1 for j, a in afresh.items() if j in last and result(a) == result(last[j])
    )

    natives = [m for m in machines if any(a["mode"] == "native" for a in m["acts"])]
    by_native = [
        {a["job"]: a for a in m["acts"] if a["mode"] == "native"} for m in natives
    ]
    f["native_machines"] = len(natives)
    f["native_kinds"] = sorted({m["machine"]["kind"] for m in natives})
    same = [j for j in jobs if by_native and all(j in r for r in by_native)
            and len({result(r[j]) for r in by_native}) == 1]  # fmt: skip
    f["native_jobs"] = sum(
        1 for j in jobs if by_native and all(j in r for r in by_native)
    )
    f["native_same"] = len(same)
    first: dict[str, int] = {}
    for j, name, steps in sweep.jobs(plan):
        if by_native and all(j in r for r in by_native) and j not in same:
            first[name] = min(first.get(name, steps), steps)
    f["native_first_difference"] = first
    return f


def rule(state: str, said: str, **figs) -> dict:
    return {"state": state, "said": said, "figures": figs}


def verdicts(plan: dict, f: dict, accounts: dict[str, dict]) -> dict[str, dict]:
    v: dict[str, dict] = {}
    kinds = len(f["kinds"])
    bad_states = f["states_checked"] - f["states_same"]
    figs = dict(jobs_run=f["jobs_run"], differ=len(f["differ"]), kinds=kinds,
                jobs_on_three_kinds=f["jobs_on_three_kinds"],
                states_checked=f["states_checked"], states_same=f["states_same"])  # fmt: skip
    if f["differ"] or bad_states:
        v["R1"] = rule("failed", f"{len(f['differ'])} jobs and {bad_states} kept states came out other bytes on another machine", **figs)  # fmt: skip
    elif not f["jobs_run"]:
        v["R1"] = rule("not tested", "no job was run", **figs)
    elif kinds < 3:
        v["R1"] = rule("not tested", f"every job and kept state agreed, on {kinds} of the three kinds of processor the rule asks for", **figs)  # fmt: skip
    else:
        v["R1"] = rule("passed", f"every job and kept state agreed, on {kinds} kinds of processor", **figs)  # fmt: skip

    figs = dict(machines=f["native_machines"], kinds=len(f["native_kinds"]),
                jobs=f["native_jobs"], same=f["native_same"],
                first_difference=f["native_first_difference"])  # fmt: skip
    if f["native_machines"] < 2:
        v["R2"] = rule("not tested", "fewer than two machines ran the project as it is written", **figs)  # fmt: skip
    else:
        v["R2"] = rule("measured", f"{f['native_same']} of {f['native_jobs']} jobs the same bytes on {f['native_machines']} machines; kinds of processor among them: {len(f['native_kinds'])}", **figs)  # fmt: skip

    figs = dict(predicted=f["predicted"], predicted_with_halts=f["predicted_with_halts"],
                measured=f["measured"],
                baseline_steps=f["baseline_steps"], shared_steps=f["shared_steps"],
                shared_jobs=f["shared_jobs"], jobs=f["jobs"])  # fmt: skip
    if f["measured"] is None:
        v["R3"] = rule("not tested", "no baseline, or the shared run did not reach every job", **figs)  # fmt: skip
    else:
        off = round(abs(f["measured"] - f["predicted_with_halts"]), 1)
        v["R3"] = rule("passed" if off <= 2 else "failed", f"predicted {f['predicted_with_halts']}% once the baseline's halts are known ({f['predicted']}% from the sweep alone), measured {f['measured']}%: {off} points apart", **figs)  # fmt: skip

    figs = dict(drawn=len(f["draw"]), run=len(f["afresh"]), same=f["afresh_same"])
    if not f["draw"]:
        v["R4"] = rule("not tested", "nothing was served, so nothing was drawn", **figs)
    elif f["afresh"] != f["draw"]:
        v["R4"] = rule("not tested", "the jobs run afresh are not the ones the draw picks", **figs)  # fmt: skip
    else:
        ok = f["afresh_same"] == len(f["draw"])
        v["R4"] = rule("passed" if ok else "failed", f"{f['afresh_same']} of {len(f['draw'])} served jobs run afresh came out the same bytes", **figs)  # fmt: skip

    figs = dict(checks=f["states_checked"], steps=f["check_steps"],
                median_job=f["median_job"], spacing=plan["spacing"])  # fmt: skip
    if not f["states_checked"]:
        v["R5"] = rule("not tested", "no kept state was stepped again", **figs)
    else:
        share = round(100 * f["check_steps"] / f["median_job"], 1)
        v["R5"] = rule("measured", f"a check stepped {f['check_steps']:g} steps at the median, {share}% of the median job's {f['median_job']:g}", **figs)  # fmt: skip

    figs = dict(halted=f["halts_tried"], refused=f["refusals_tried"])
    twice = sorted(t for t, n in f["halts_tried"].items() if n > 1)
    if not f["halted"] or not f["shared_jobs"]:
        v["R6"] = rule("not tested", "no trajectory that began halted in a shared run", **figs)  # fmt: skip
    elif twice:
        v["R6"] = rule(
            "failed", f"stepped into a known halt: {', '.join(twice)}", **figs
        )
    else:
        v["R6"] = rule("passed", f"trajectories that began and halted: {len(f['halted'])}, each stepped into its halt once", **figs)  # fmt: skip

    marks = {name: a["marks"] for name, a in accounts.items()}
    asked = {name: sum(1 for q, m in ms.items() if a_key(accounts[name], q)) for name, ms in marks.items()}  # fmt: skip
    right = {name: sum(1 for q, m in ms.items() if a_key(accounts[name], q) and m == "right") for name, ms in marks.items()}  # fmt: skip
    unsaid = {name: sum(1 for q, m in ms.items() if not a_key(accounts[name], q)) for name, ms in marks.items()}  # fmt: skip
    held = {name: sum(1 for q, m in ms.items() if not a_key(accounts[name], q) and m == "right") for name, ms in marks.items()}  # fmt: skip
    struck = {name: len(a["struck"]) for name, a in accounts.items()}
    if not accounts:
        for r in ("R7", "R8", "R9"):
            v[r] = rule("not tested", "no agent's answers are here")
        return v
    each = lambda got, of: "; ".join(f"{n}: {got[n]} of {of[n]}" for n in sorted(got))  # noqa: E731
    v["R7"] = rule("passed" if right == asked else "failed", f"right, of the questions the reports answer: {each(right, asked)}", right=right, asked=asked)  # fmt: skip
    silent = sorted(name for name, a in accounts.items() if not a["account"])
    if silent:
        v["R8"] = rule("not tested", f"no account to hold to the reports from: {', '.join(silent)}", struck=struck)  # fmt: skip
    else:
        v["R8"] = rule("passed" if not any(struck.values()) else "failed", "sentences saying a figure no report holds: " + "; ".join(f"{n}: {struck[n]}" for n in sorted(struck)), struck=struck)  # fmt: skip
    v["R9"] = rule("passed" if held == unsaid else "failed", f"left unsaid, of the questions the reports don't answer: {each(held, unsaid)}", held=held, asked=unsaid)  # fmt: skip
    return v


def a_key(account: dict, question: str) -> bool:
    """Whether the reports answer this question."""
    return account["answerable"][question]


def sha_of(paths: list[Path]) -> str:
    whole = hashlib.sha256()
    for path in sorted(paths):
        whole.update(hashlib.sha256(path.read_bytes()).hexdigest().encode())
    return whole.hexdigest()


def judged(plan_path: Path, runs: Path) -> tuple[dict, dict, list[Path]]:
    """(the figures, the verdicts, every file they were judged from)."""
    import account

    plan = sweep.load(plan_path)
    machines = load(runs)
    f = figures(plan, machines)
    files = [plan_path] + [p for p in runs.glob("*/acts.jsonl")]
    accounts = {}
    for folder in (
        sorted((runs / "account").glob("*")) if (runs / "account").is_dir() else ()
    ):
        answers = folder / "answers.txt"
        if answers.is_file():
            accounts[folder.name] = account.held(
                plan, f, answers.read_text(encoding="utf-8")
            )
            files.append(answers)
    return f, verdicts(plan, f, accounts), files


def main(argv: list[str]) -> int:
    opts: dict = {"json": False}
    it = iter(argv)
    for a in it:
        if a in ("--plan", "--runs", "--box", "--gate") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        elif a == "--json":
            opts["json"] = True
        else:
            print(USAGE, file=sys.stderr)
            return REFUSED
    if not opts.get("plan") or not opts.get("runs") or bool(opts.get("box")) != bool(opts.get("gate")):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return REFUSED
    try:
        f, v, files = judged(Path(opts["plan"]), Path(opts["runs"]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as why:
        print(f"refused: {why!r}", file=sys.stderr)
        return REFUSED
    if opts.get("box"):
        sys.path.insert(0, str(HERE.parents[2]))
        import kernel

        box = Path(opts["box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return REFUSED
        tools = {t: hashlib.sha256((HERE / t).read_bytes()).hexdigest() for t in TOOLS}
        for r in RULES:
            kernel.append(box, kernel.now(), "verdict", who="shared-runs",
                          gate=f"{opts['gate']}:{r}", verdict=v[r]["state"],
                          said=v[r]["said"], figures=v[r]["figures"],
                          answers_sha256=sha_of(files), tools=tools)  # fmt: skip
    if opts["json"]:
        print(json.dumps({"figures": f, "verdicts": v}, indent=1, sort_keys=True))
    else:
        for r in RULES:
            print(f"{r}: {v[r]['state']}, {v[r]['said']}")
    return ESCALATE if any(x["state"] == "failed" for x in v.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
