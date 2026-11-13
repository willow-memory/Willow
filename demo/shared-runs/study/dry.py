"""dry.py: the whole plan on one machine, with a sweep of made-up setups,
to find the wiring's breaks before anything is frozen.

    python demo/shared-runs/study/dry.py --plan PLAN --work DIR (--repo DIR | --toy)
        [--against FILE]

It does what the study's machines would, in the study's order, each as a
process of its own given only folders: the starts made once; the baseline
twice, each also running the project as it is written; each round's
machines at once, a later round given the rounds before it; then a check
that is given every round. Then it writes what an agent would be handed:
the reports, the brief and the key.

It runs only a plan that says it is a dry one: the study's sweep is not run
before it is frozen, and never by this. Nothing here is a result.

With `--against`, it then says how many jobs came to the same bytes here
as on the machine that kept FILE (dry/bytes.json is this study's), with
the project's one power rewritten and as it is written, and where the
first difference falls. That is the dry run's whole use to someone
trying it on a machine of their own.

DIR is made, outside this repository, and everything is written under it.
Then judge.py reads `DIR/runs`. Exit codes, the kernel's: 0 run; 2 refused
(a bad command line, a plan that isn't a dry one, a step that failed).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import account  # noqa: E402
import judge  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]


def against(runs: Path, file: Path) -> list[str]:
    """This machine's first baseline held to another machine's kept bytes:
    for each way of running, the jobs that agree and the first that don't."""
    theirs = json.loads(file.read_text(encoding="utf-8"))
    here = json.loads(
        (runs / "baseline-1" / "machine.json").read_text(encoding="utf-8")
    )
    acts = [
        json.loads(line)
        for line in (runs / "baseline-1" / "acts.jsonl").read_text().splitlines()
    ]
    out = [f"this machine: {here.get('kind')}, NumPy {here.get('numpy')}"]
    for mode, name in (("alone", "rewritten"), ("native", "as_written")):
        mine = {a["job"]: [a["outcome"], a["ended"], a["sha256"]] for a in acts if a["mode"] == mode}  # fmt: skip
        both = sorted(set(mine) & set(theirs[name]))
        differ = [j for j in both if mine[j] != theirs[name][j]]
        said = f"the power {name.replace('_', ' ')}: {len(both) - len(differ)} of {len(both)} jobs the same bytes as the other machine"  # fmt: skip
        if differ:
            first = min(differ, key=lambda j: (int(j.rpartition("@")[2]), j))
            said += f"; the shortest that differs is {first}"
        out.append(said)
    return out


def main(argv: list[str]) -> int:
    opts: dict = {"toy": False}
    it = iter(argv)
    for a in it:
        if a in ("--plan", "--work", "--repo", "--against") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        elif a == "--toy":
            opts["toy"] = True
        else:
            print(USAGE, file=sys.stderr)
            return 2
    if not opts.get("plan") or not opts.get("work") or bool(opts.get("repo")) == opts["toy"]:  # fmt: skip
        print(USAGE, file=sys.stderr)
        return 2
    work = Path(opts["work"]).resolve()
    try:
        plan = sweep.load(Path(opts["plan"]))
        if plan.get("dry") is not True:
            raise ValueError("this plan does not say it is a dry one")
        if work.is_relative_to(HERE.parents[2]):
            raise ValueError("the work folder must be outside the repository")
        starts = sweep.starts(plan, Path(opts.get("repo") or "."))
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return 2
    runs = work / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (work / "starts.json").write_text(json.dumps(starts, indent=1) + "\n")
    stepper = ["--toy"] if opts["toy"] else ["--repo", opts["repo"]]
    base = ["--plan", opts["plan"], "--starts", str(work / "starts.json"), *stepper]

    def runner(mode: str, to: str, *more: str):
        return subprocess.Popen(
            [sys.executable, str(HERE / "runner.py"), mode, *base, "--to", str(runs / to), *more]
        )  # fmt: skip

    def wait(procs) -> bool:
        return all(p.wait() == 0 for p in list(procs))

    ok = wait(runner("alone", f"baseline-{b}") for b in (1, 2))
    ok = ok and wait(runner("native", f"baseline-{b}") for b in (1, 2))
    given: list[str] = []
    for r in range(1, plan["rounds"] + 1):
        ok = ok and wait(
            runner("shared", f"round-{r}-machine-{k}", "--machine", str(k), "--round", str(r), *given)
            for k in range(plan["machines"])
        )  # fmt: skip
        for k in range(plan["machines"]):
            given += ["--memory", str(runs / f"round-{r}-machine-{k}")]
    ok = ok and wait([runner("check", "check", *given)])
    ok = ok and wait([runner("native", "check")])
    if not ok:
        print("refused: a step of the dry run failed; see above", file=sys.stderr)
        return 2
    f = judge.figures(plan, judge.load(runs))
    (work / "report.txt").write_text(account.report(plan, f), encoding="utf-8")
    (work / "brief.txt").write_text(account.brief(plan, f), encoding="utf-8")
    (work / "key.json").write_text(json.dumps(account.key(f), indent=1) + "\n")
    print(f"run: {len(list(runs.iterdir()))} machine runs under {runs}")
    print(f"an agent's whole input is {work / 'brief.txt'}; its answers go in")
    print(f"{runs / 'account'}/NAME/answers.txt, and then judge.py reads {runs}")
    if opts.get("against"):
        for line in against(runs, Path(opts["against"])):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
