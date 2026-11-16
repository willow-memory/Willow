"""lies.py: a memory that has been lied to, and whether the checks find it.

    python demo/shared-runs/lies/lies.py say   --lies FILE --honest RUNS
    python demo/shared-runs/lies/lies.py run   --lies FILE --honest RUNS --work DIR (--repo DIR | --toy)
    python demo/shared-runs/lies/lies.py judge --lies FILE --work DIR [--box DIR --gate NAME] [--json]

RUNS is an honest run of a sweep, as the study's machines left it: the
baseline, and each machine's first round. FILE names the sweep's plan and
starts, the arms (how much is checked) and how many lies of each kind.

A trial is one lie told to one machine's first-round memory, in a copy:

    none       nothing is changed: the control
    one-bit    one bit of one kept state, anywhere on a trajectory
    last-bit   one bit of a trajectory's last kept state, the one a later
               job is most likely to go on from
    false-halt the memory says a trajectory halted where it did not
    no-halt    the memory forgets a halt that happened
    stepped-otherwise
               every state of a trajectory is what another way of stepping
               gives: a machine that did not do what the others did

Then the second round's machine is run on the lie, with the study's own
runner.py, and the study's own check after it. Nothing of the honest run
is written to. Which state, which trajectory and which bit are picked by
the lies file's seed, so `say` lists every trial before one is run.

`judge` holds seven rules to what the trials kept, the truth being the
honest baseline:

    L1  with no lie, nothing is found and no job is wrong
    L2  a lied-about state the check steps again is found
    L3  a wrong job the check runs afresh is found
    L4  with everything checked, every lie in a state is found
    L5  measured: the share of lies found at each arm's rates, by kind
    L6  measured: the wrong jobs a lie hands out, and the lies that reach none
    L7  a lie stays on its trajectory: no job on another comes out wrong

It writes DIR, which must be outside the repository, and with `--box` the
record. Exit codes, the kernel's: 0 said, run, or no rule failed; 42 a
rule failed; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "study"
sys.path.insert(0, str(STUDY))
import runner  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED, ESCALATE = 2, 42
KINDS = ("none", "one-bit", "last-bit", "false-halt", "no-halt", "stepped-otherwise")
IN_A_STATE = ("one-bit", "last-bit", "stepped-otherwise")
RULES = ("L1", "L2", "L3", "L4", "L5", "L6", "L7")
REWRITTEN = "a product and a square root"


class OtherToy(runner.Toy):
    """The made-up stepper with another multiplier: a machine that steps otherwise."""

    def step(self, s: dict) -> None:
        if s["halts_after"] is not None and s["n"] >= s["halts_after"]:
            raise runner.Halt
        s["x"] = (s["x"] * 6364136223846793007 + 1442695040888963407) % 2**64
        s["n"] += 1


def load(file: Path) -> dict:
    lies = json.loads(file.read_text(encoding="utf-8"))
    lies["plan_file"] = (file.parent / lies["plan"]).resolve()
    lies["starts_file"] = (file.parent / lies["starts"]).resolve()
    if not lies.get("seed") or not lies.get("arms"):
        raise ValueError("the lies file names no seed, or no arms")
    if set(lies.get("trials", {})) - set(KINDS):
        raise ValueError("the lies file names a kind of lie this does not tell")
    return lies


def memory_of(folder: Path) -> list[dict]:
    return [json.loads(x) for x in (folder / "memory.jsonl").read_text().splitlines()]


def acts_of(folder: Path) -> list[dict]:
    return [json.loads(x) for x in (folder / "acts.jsonl").read_text().splitlines()]


def picked(seed: str, names: list[str], n: int) -> list[str]:
    """The first n names in the order the seed gives them."""
    return sorted(set(names), key=lambda x: sweep.h(f"{seed}:{x}"))[:n]


def trials(lies: dict, plan: dict, starts: dict, honest: Path, toy: bool) -> list[dict]:
    """Every trial, from the lies file and the honest first round alone."""
    said = {} if toy else {"power": REWRITTEN}
    tid = {t["name"]: runner.identity(starts[t["name"]], said) for t in plan["trajectories"]}  # fmt: skip
    kept: dict[str, list[int]] = {}
    halted: dict[str, int] = {}
    for name, t in tid.items():
        rows = memory_of(honest / f"round-1-machine-{sweep.owner(plan, name)}")
        steps = sorted(r["step"] for r in rows if r["trajectory"] == t and "step" in r)
        halt = [r["halt"] for r in rows if r["trajectory"] == t and "halt" in r]
        if halt:
            halted[name] = halt[0]
        elif steps:
            kept[name] = steps
    out = []
    seed, want = lies["seed"], lies["trials"]

    def add(kind: str, name: str | None, step: int | None, machine: int) -> None:
        out.append({"n": len(out) + 1, "kind": kind, "trajectory": name, "step": step,
                    "machine": machine})  # fmt: skip

    for k in picked(seed + ":none", [str(m) for m in range(plan["machines"])], want.get("none", 0)):  # fmt: skip
        add("none", None, None, int(k))
    states = [f"{name}@{step}" for name, steps in kept.items() for step in steps]
    for state in picked(seed + ":one-bit", states, want.get("one-bit", 0)):
        name, _, step = state.rpartition("@")
        add("one-bit", name, int(step), sweep.owner(plan, name))
    for name in picked(seed + ":last-bit", list(kept), want.get("last-bit", 0)):
        add("last-bit", name, kept[name][-1], sweep.owner(plan, name))
    for name in picked(seed + ":false-halt", list(kept), want.get("false-halt", 0)):
        step = picked(seed + ":false-halt:" + name, [str(s) for s in kept[name]], 1)[0]
        add("false-halt", name, int(step), sweep.owner(plan, name))
    for name in picked(seed + ":no-halt", list(halted), want.get("no-halt", 0)):
        add("no-halt", name, halted[name], sweep.owner(plan, name))
    for name in picked(seed + ":stepped-otherwise", list(kept), want.get("stepped-otherwise", 0)):  # fmt: skip
        add("stepped-otherwise", name, kept[name][0], sweep.owner(plan, name))
    return out


def flipped(state: str) -> str:
    """A kept state with its lowest bit turned over."""
    data = bytearray(bytes.fromhex(state))
    data[0] ^= 1
    return data.hex()


def otherwise(stepper, start: dict, steps: list[int]) -> dict[int, str]:
    """{a step: the state another way of stepping reaches there}, as far as
    it runs."""
    out, s, n = {}, stepper.begin(start), 0
    try:
        for step in sorted(steps):
            while n < step:
                stepper.step(s)
                n += 1
            out[step] = stepper.pack(s).hex()
    except runner.Halt:
        pass
    return out


def tell(trial: dict, rows: list[dict], tid: str, other) -> list[dict]:
    """The first round's memory with this trial's lie told to it."""
    kind, step = trial["kind"], trial["step"]
    if kind in ("one-bit", "last-bit"):
        return [{**r, "state": flipped(r["state"])} if r["trajectory"] == tid
                and r.get("step") == step else r for r in rows]  # fmt: skip
    if kind == "false-halt":
        return rows + [{"trajectory": tid, "halt": step}]
    if kind == "no-halt":
        return [r for r in rows if not (r["trajectory"] == tid and "halt" in r)]
    if kind == "stepped-otherwise":
        wrong = other()
        return [{**r, "state": wrong[r["step"]]} if r["trajectory"] == tid
                and r.get("step") in wrong else r for r in rows]  # fmt: skip
    return rows


def result(act: dict) -> tuple:
    return act["outcome"], act["ended"], act["sha256"]


def run(
    lies: dict, honest: Path, work: Path, stepper_args: list[str], toy: bool
) -> int:
    plan = sweep.load(lies["plan_file"])
    starts = json.loads(lies["starts_file"].read_text(encoding="utf-8"))
    said = {} if toy else {"power": REWRITTEN}
    truth = {a["job"]: result(a) for a in acts_of(honest / "baseline-1") if a["mode"] == "alone"}  # fmt: skip
    other = OtherToy() if toy else runner.Project(Path(stepper_args[1]), True)
    work.mkdir(parents=True)
    kept = []
    for arm in lies["arms"]:
        arm_plan = work / f"plan-{arm['name']}.json"
        text = json.loads(lies["plan_file"].read_text(encoding="utf-8"))
        text.update(check_one_in=arm["check_one_in"], draw_one_in=arm["draw_one_in"])
        arm_plan.write_text(json.dumps(text) + "\n")
        for trial in trials(lies, plan, starts, honest, toy):
            k, name = trial["machine"], trial["trajectory"]
            here = work / arm["name"] / f"trial-{trial['n']:02d}"
            first = here / f"round-1-machine-{k}"
            shutil.copytree(honest / f"round-1-machine-{k}", first)
            tid = runner.identity(starts[name], said) if name else ""
            rows = memory_of(first)
            steps = [r["step"] for r in rows if r["trajectory"] == tid and "step" in r]
            told = tell(trial, rows, tid, lambda: otherwise(other, starts[name], steps))
            (first / "memory.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in told))  # fmt: skip
            base = ["--plan", str(arm_plan), "--starts", str(lies["starts_file"]), *stepper_args]  # fmt: skip
            for mode, to, more in (
                ("shared", f"round-2-machine-{k}", ["--machine", str(k), "--round", "2", "--memory", str(first)]),
                ("check", "check", ["--memory", str(first), "--memory", str(here / f"round-2-machine-{k}")]),
            ):  # fmt: skip
                got = subprocess.run([sys.executable, str(STUDY / "runner.py"), mode, *base,
                                      "--to", str(here / to), *more])  # fmt: skip
                if got.returncode != 0:
                    print(f"refused: {arm['name']} trial {trial['n']}: {mode} did not end clean", file=sys.stderr)  # fmt: skip
                    return REFUSED
            second = {a["job"]: a for a in acts_of(here / f"round-2-machine-{k}")}
            checks = acts_of(here / "check")
            stepped = [a for a in checks if a["mode"] == "check"]
            afresh = {a["job"]: a for a in checks if a["mode"] == "afresh"}
            lied = (
                {s for s in steps} if trial["kind"] == "stepped-otherwise"
                else {trial["step"]} if trial["kind"] in ("one-bit", "last-bit") else set()
            )  # fmt: skip
            wrong = sorted(j for j, a in second.items() if result(a) != truth[j])
            kept.append({
                **trial, "arm": arm["name"],
                "round_2_jobs": len(second),
                "wrong": [j for j in wrong if j.rpartition("@")[0] == name],
                "wrong_elsewhere": [j for j in wrong if j.rpartition("@")[0] != name],
                "lie_checked": sum(1 for a in stepped if a["trajectory"] == name and a["step"] in lied),
                "found_by_state": sum(1 for a in stepped if not a["same"]),
                "wrong_run_afresh": sorted(j for j in wrong if j in afresh),
                "found_by_afresh": sorted(j for j, a in afresh.items() if j in second and result(a) != result(second[j])),
                "halts_again": sum(1 for a in second.values() if a["trajectory"] == name and a["tried_halt"]),
            })  # fmt: skip
    (work / "trials.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in kept))  # fmt: skip
    print(f"run: {len(kept)} trials under {work}")
    return 0


def rule(state: str, said: str, **figs) -> dict:
    return {"state": state, "said": said, "figures": figs}


def found(t: dict) -> bool:
    return bool(t["found_by_state"] or t["found_by_afresh"])


def verdicts(lies: dict, rows: list[dict]) -> dict[str, dict]:
    v: dict[str, dict] = {}
    full = [a["name"] for a in lies["arms"] if a["check_one_in"] == 1 and a["draw_one_in"] == 1]  # fmt: skip
    none = [t for t in rows if t["kind"] == "none"]
    noisy = [t for t in none if found(t) or t["wrong"] or t["wrong_elsewhere"]]
    v["L1"] = (
        rule("not tested", "no trial told no lie") if not none
        else rule("failed" if noisy else "passed", f"{len(none) - len(noisy)} of {len(none)} trials with no lie found nothing and got every job right", trials=len(none), noisy=len(noisy))
    )  # fmt: skip
    checked = [t for t in rows if t["kind"] in IN_A_STATE and t["lie_checked"]]
    missed = [t for t in checked if not t["found_by_state"]]
    v["L2"] = (
        rule("not tested", "the check stepped no lied-about state again") if not checked
        else rule("failed" if missed else "passed", f"{len(checked) - len(missed)} of {len(checked)} lies whose state the check stepped again were found by it", checked=len(checked), missed=[t["n"] for t in missed])
    )  # fmt: skip
    rerun = [t for t in rows if t["wrong_run_afresh"]]
    slipped = [
        t for t in rerun if set(t["wrong_run_afresh"]) - set(t["found_by_afresh"])
    ]
    v["L3"] = (
        rule("not tested", "no wrong job was run afresh") if not rerun
        else rule("failed" if slipped else "passed", f"{len(rerun) - len(slipped)} of {len(rerun)} trials where a wrong job was run afresh had it found", trials=len(rerun), slipped=[t["n"] for t in slipped])
    )  # fmt: skip
    everything = [t for t in rows if t["arm"] in full and t["kind"] in IN_A_STATE]
    unfound = [t for t in everything if not found(t)]
    v["L4"] = (
        rule("not tested", "no arm checks everything") if not everything
        else rule("failed" if unfound else "passed", f"with everything checked, {len(everything) - len(unfound)} of {len(everything)} lies in a state were found", trials=len(everything), unfound=[t["n"] for t in unfound])
    )  # fmt: skip
    share: dict = {}
    harm: dict = {}
    for arm in (a["name"] for a in lies["arms"]):
        for kind in KINDS[1:]:
            mine = [t for t in rows if t["arm"] == arm and t["kind"] == kind]
            if mine:
                share[f"{arm}, {kind}"] = (
                    f"{sum(1 for t in mine if found(t))} of {len(mine)}"
                )
                harm[f"{arm}, {kind}"] = {
                    "lies": len(mine),
                    "reached_no_job": sum(1 for t in mine if not t["wrong"]),
                    "wrong_jobs": sum(len(t["wrong"]) for t in mine),
                    "wrong_jobs_where_nothing_was_found": sum(len(t["wrong"]) for t in mine if not found(t)),
                    "halts_again": sum(t["halts_again"] for t in mine),
                }  # fmt: skip
    v["L5"] = rule("measured" if share else "not tested", "lies found, by arm and kind: " + "; ".join(f"{k}: {n}" for k, n in share.items()), found=share)  # fmt: skip
    v["L6"] = rule("measured" if harm else "not tested", "wrong jobs handed out, by arm and kind: " + "; ".join(f"{k}: {h['wrong_jobs']} from {h['lies']} lies, {h['reached_no_job']} reaching none" for k, h in harm.items()), harm=harm)  # fmt: skip
    strayed = [t for t in rows if t["wrong_elsewhere"]]
    v["L7"] = rule("failed" if strayed else "passed" if rows else "not tested", f"{len(rows) - len(strayed)} of {len(rows)} trials left every other trajectory's jobs right", strayed=[t["n"] for t in strayed])  # fmt: skip
    return v


def main(argv: list[str]) -> int:
    opts: dict = {"toy": False, "json": False}
    it = iter(argv[1:])
    for a in it:
        if a in ("--lies", "--honest", "--work", "--repo", "--box", "--gate") and a[2:] not in opts:  # fmt: skip
            opts[a[2:]] = next(it, "")
        elif a in ("--toy", "--json"):
            opts[a[2:]] = True
        else:
            opts = {}
            break
    verb = argv[0] if argv else ""
    need = {"say": ("lies", "honest"), "run": ("lies", "honest", "work"), "judge": ("lies", "work")}  # fmt: skip
    if verb not in need or not all(opts.get(k) for k in need[verb]):
        print(USAGE, file=sys.stderr)
        return REFUSED
    try:
        lies = load(Path(opts["lies"]))
        if verb == "judge":
            work = Path(opts["work"])
            rows = [
                json.loads(x) for x in (work / "trials.jsonl").read_text().splitlines()
            ]
            v = verdicts(lies, rows)
            if opts.get("box"):
                sys.path.insert(0, str(HERE.parents[2]))
                import kernel

                box = Path(opts["box"])
                if not (box / "kernel.json").exists() or not opts.get("gate"):
                    raise ValueError("not a kernel box, or no gate named")
                tools = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (HERE / "lies.py", STUDY / "runner.py", STUDY / "sweep.py")}  # fmt: skip
                answers = hashlib.sha256(
                    (work / "trials.jsonl").read_bytes()
                ).hexdigest()
                for r in RULES:
                    kernel.append(box, kernel.now(), "verdict", who="shared-runs",
                                  gate=f"{opts['gate']}:{r}", verdict=v[r]["state"], said=v[r]["said"],
                                  figures=v[r]["figures"], answers_sha256=answers, tools=tools)  # fmt: skip
            if opts["json"]:
                print(
                    json.dumps(
                        {"trials": rows, "verdicts": v}, indent=1, sort_keys=True
                    )
                )
            else:
                for r in RULES:
                    print(f"{r}: {v[r]['state']}, {v[r]['said']}")
            return ESCALATE if any(x["state"] == "failed" for x in v.values()) else 0
        if bool(opts.get("repo")) == opts["toy"] and verb == "run":
            raise ValueError(USAGE)
        plan = sweep.load(lies["plan_file"])
        starts = json.loads(lies["starts_file"].read_text(encoding="utf-8"))
        honest = Path(opts["honest"])
        if verb == "say":
            toy = "toy" in next(iter(starts.values()))
            listed = trials(lies, plan, starts, honest, toy)
            for t in listed:
                where = f"{t['trajectory']} at step {t['step']}" if t["trajectory"] else "nothing"  # fmt: skip
                print(f"{t['n']:2}  {t['kind']:18} {where}; machine {t['machine']}")
            arms = ", ".join(f"{a['name']} (a state in {a['check_one_in']}, a served job in {a['draw_one_in']})" for a in lies["arms"])  # fmt: skip
            print(f"{len(listed)} trials an arm; arms: {arms}")
            return 0
        work = Path(opts["work"]).resolve()
        if work.exists() or work.is_relative_to(HERE.parents[2]):
            raise ValueError("the work folder must be new, and outside the repository")
        stepper = ["--toy"] if opts["toy"] else ["--repo", opts["repo"]]
        return run(lies, honest, work, stepper, opts["toy"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as why:
        print(
            why if str(why).startswith("usage") else f"refused: {why}", file=sys.stderr
        )
        return REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
