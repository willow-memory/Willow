"""door.py: the shared memory with a door on it, counted and not run, to see
what falls when there is more of everything.

    python demo/shared-runs/door/door.py count --plan PLAN --stops FILE
        [--scale N] [--rounds R] [--signers S] [--enrolled E]
        [--check C] [--draw D] [--liar ROUND [--tip]] [--seed TEXT] [--json]
    python demo/shared-runs/door/door.py tables --plan PLAN --stops FILE [--seeds N]

It steps nothing. It counts the steps a sweep would take, by the rules
runner.py runs by: a job goes on from the latest kept state at or before
its length, a state is kept every `spacing` steps and at a job's end, a
trajectory belongs to the machine its name picks. FILE says where each
trajectory stops, as a baseline found it. Counted this way the first
study's own shared run comes to its 336,379 steps, and each of its ten
machine runs to its own count: a test holds that, so what is counted
here at other sizes is the same arithmetic and not a guess.

`--scale N` runs N copies of the plan's trajectories. `--rounds R` deals
the jobs over R rounds of the plan's machines.

Then the door, as demo/wards and the phone-keys proposal have it. Each
round's machines are run by signers, S of them taking turns, the first E
enrolled:

    enrolled   what it keeps is gone on from at once. After each round one
               kept state in C is stepped again, and one served job in D
               run afresh.
    unknown    what it keeps is held: nothing goes on from it until an
               enrolled machine has stepped every state of that round
               again and found them the same. Then the signer has earned
               its standing, and is treated as enrolled from the next
               round.

`--check 0` or `--draw 0` leaves that check out. `--liar ROUND` has one
signer turn one kept state over in that round; with `--tip` it is the
last state of a trajectory that still has longer jobs to come, the one
most likely to be gone on from.
What is found is recalled: the states that came after it are thrown
away, the jobs that went on from them are run again, and the signer's
standing is lost.

`tables` counts what the page beside this says: the first study's own
check as it was drawn, then the sweep at larger sizes, with strangers
among the signers, and with one lie told at six levels of checking.

It says what was stepped, what the checking cost, what was thrown away
and done again, the saving that is left, and the wrong jobs handed out
and never found. Exit codes, the kernel's: 0 counted; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "study"))
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2


def scaled(plan: dict, stops: dict[str, int], n: int) -> tuple[dict, dict[str, int]]:
    """The plan with n copies of each trajectory, and where each stops."""
    if n == 1:
        return plan, stops
    many, where = [], {}
    for i in range(n):
        for t in plan["trajectories"]:
            name = t["name"] if i == 0 else f"{t['name']}~{i}"
            many.append({**t, "name": name})
            if t["name"] in stops:
                where[name] = stops[t["name"]]
    return {**plan, "trajectories": many}, where


def picked(seed: str, names: list, one_in: int) -> set:
    if not one_in:
        return set()
    order = sorted(names, key=lambda x: sweep.h(f"{seed}:{x}"))
    return set(order[: -(-len(order) // one_in)]) if order else set()


def count(plan: dict, stops: dict[str, int], signers: int | None = None, enrolled: int | None = None,
          check: int | None = None, draw: int | None = None, liar: int | None = None,
          seed: str = "the door", tip: bool = False) -> dict:  # fmt: skip
    """The sweep counted round by round, with a door on the memory."""
    machines, spacing = plan["machines"], plan["spacing"]
    signers = signers or machines
    enrolled = signers if enrolled is None else enrolled
    check = plan["check_one_in"] if check is None else check
    draw = plan["draw_one_in"] if draw is None else draw
    earned = set(range(enrolled))
    kept: dict[
        str, dict[int, tuple[int, bool]]
    ] = {}  # trajectory -> step -> (signer, wrong)
    halted: set[str] = set()
    went: dict[
        tuple[str, int], list[tuple[str, int]]
    ] = {}  # a state -> jobs that went on from it
    out = {"stepped": 0, "checking": 0, "again": 0, "held_rounds": 0, "jobs": 0,
           "wrong_handed_out": 0, "wrong_found": 0, "lies_told": 0, "lies_found": 0,
           "states_kept": 0, "per_run": [], "found_in_round": None, "standing_lost": 0}  # fmt: skip
    wrong_jobs: dict[str, tuple[str, int]] = {}
    alone = 0
    for job, name, n in sweep.jobs(plan):
        alone += min(n, stops.get(name, n))
    out["alone"] = alone
    lied = False
    for r, round_jobs in enumerate(sweep.dealt(plan)):
        new: list[
            tuple[str, int, int]
        ] = []  # states kept this round: (trajectory, step, signer)
        served: list[tuple[str, str, int]] = []
        for k in range(machines):
            who = (k + r * machines) % signers
            stepped = 0
            for job, name, n in (j for j in round_jobs if sweep.owner(plan, j[1]) == k):
                have = kept.setdefault(name, {0: (-1, False)})
                stop = stops.get(name)
                target = min(n, stop) if name in halted else n
                at = max(x for x in have if x <= target)
                reach = target if stop is None else min(target, stop)
                wrong = have[at][1]
                stepped += reach - at
                for x in [
                    *range(at - at % spacing + spacing, reach + 1, spacing),
                    reach,
                ]:
                    if x not in have:
                        have[x] = (who, wrong)
                        new.append((name, x, who))
                if stop is not None and n > stop:
                    halted.add(name)
                went.setdefault((name, at), []).append((job, reach - at))
                if at:
                    served.append((job, name, at))
                if wrong:
                    wrong_jobs[job] = (name, at)
                out["jobs"] += 1
            out["per_run"].append(stepped)
            out["stepped"] += stepped
        out["states_kept"] += len(new)
        if liar == r + 1 and not lied and new:
            pool = new
            if tip:  # the last state of a trajectory that still has longer jobs to come
                tips = {n: max(steps) for n, steps in kept.items()}
                ahead = {j[1] for later in sweep.dealt(plan)[r + 1 :] for j in later
                         if j[2] > tips.get(j[1], 10**12)}  # fmt: skip
                tips = {n: x for n, x in tips.items() if n in ahead}
                pool = [s for s in new if tips.get(s[0]) == s[1]] or new
            name, step, who = sorted(
                pool, key=lambda s: sweep.h(f"{seed}:lie:{s[0]}@{s[1]}")
            )[0]
            kept[name][step] = (who, True)
            out["lies_told"], lied = 1, True
        # the door, after the round
        found: set[tuple[str, int]] = set()
        for who in sorted({s[2] for s in new}):
            mine = [s for s in new if s[2] == who]
            if who in earned:
                looked = picked(f"{seed}:{r}", [(a, b) for a, b, _ in mine], check)
            else:
                looked = {(a, b) for a, b, _ in mine}
                out["held_rounds"] += 1
            for name, step in looked:
                before = max(x for x in kept[name] if x < step)
                out["checking"] += step - before
                if kept[name][step][1] and not kept[name][before][1]:
                    found.add((name, step))
            if who not in earned and not any(f in looked for f in found):
                earned.add(who)
        for job, name, at in picked(f"{seed}:afresh:{r}", served, draw):
            out["checking"] += min(int(job.rpartition("@")[2]), stops.get(name, 10**12))
            if job in wrong_jobs:
                first = min(x for x in kept[name] if kept[name][x][1])
                found.add((name, first))
        for name, step in found:
            out["lies_found"] += 1
            out["found_in_round"] = r + 1
            who = kept[name][step][0]
            if who in earned:
                earned.discard(who)
                out["standing_lost"] += 1
            for x in [x for x in kept[name] if x >= step and kept[name][x][1]]:
                for job, steps in went.pop((name, x), []):
                    if job in wrong_jobs:
                        del wrong_jobs[job]
                        out["wrong_found"] += 1
                    out["again"] += steps + (x - max(y for y in kept[name] if y < step))
                del kept[name][x]
    out["wrong_handed_out"] = out["wrong_found"] + len(wrong_jobs)
    out["wrong_never_found"] = len(wrong_jobs)
    spent = out["stepped"] + out["checking"] + out["again"]
    out["saving"] = round(100 * (1 - out["stepped"] / alone), 1)
    out["saving_after_the_door"] = round(100 * (1 - spent / alone), 1)
    out["checking_share"] = round(100 * out["checking"] / alone, 1)
    return out


def as_run(plan: dict, stops: dict[str, int]) -> dict:
    """The first study's own check, counted as runner.py draws it: one kept
    state in `check_one_in` of all of them stepped again, and one served
    job in `draw_one_in` run afresh, both by the plan's draw seed."""
    spacing, kept, halted, took = plan["spacing"], {}, set(), []
    for round_jobs in sweep.dealt(plan):
        for k in range(plan["machines"]):
            for job, name, n in (j for j in round_jobs if sweep.owner(plan, j[1]) == k):
                have, stop, known = (
                    kept.setdefault(name, {0}),
                    stops.get(name),
                    name in halted,
                )
                target = min(n, stop) if known else n
                at = max(x for x in have if x <= target)
                reach = target if stop is None else min(target, stop)
                have.update(
                    [*range(at - at % spacing + spacing, reach + 1, spacing), reach]
                )
                if stop is not None and n > stop:
                    halted.add(name)
                if at or known:
                    took.append(job)
    states = sorted(f"{t}@{x}" for t, steps in kept.items() for x in steps if x)
    checked = 0
    for state in sweep.drawn(plan["draw_seed"], states, plan["check_one_in"]):
        t, _, x = state.rpartition("@")
        checked += int(x) - max(y for y in kept[t] if y < int(x))
    length = {j: (name, n) for j, name, n in sweep.jobs(plan)}
    afresh = 0
    for job in sweep.drawn(plan["draw_seed"], took, plan["draw_one_in"]):
        name, n = length[job]
        afresh += min(n, stops.get(name, n))
    return {"states": len(states), "state_checks": checked, "afresh": afresh}


LEVELS = (
    ("every state, no job afresh", 1, 0),
    ("every state and every served job", 1, 1),
    ("as the study: a state in 8, a job in 10", 8, 10),
    ("a state in 8, no job afresh", 8, 0),
    ("a state in 64, a job in 100", 64, 100),
    ("nothing", 0, 0),
)


def tables(plan0: dict, stops0: dict[str, int], seeds: int) -> dict:
    """What is counted for the page: size, strangers, and how much is checked."""

    def run(scale: int, rounds: int, **kw) -> dict:
        plan, stops = scaled(plan0, stops0, scale)
        return count({**plan, "rounds": rounds}, stops, **kw)

    def few(g: dict) -> dict:
        keys = ("jobs", "alone", "stepped", "saving", "checking_share", "saving_after_the_door",
                "states_kept", "held_rounds")  # fmt: skip
        return {k: g[k] for k in keys}

    out: dict = {"size": {}, "strangers": {}, "checked": {}}
    for scale, rounds in ((1, 2), (10, 2), (10, 10), (100, 10)):
        out["size"][f"{scale} times, {rounds} rounds"] = few(run(scale, rounds))
    for signers, enrolled in ((25, 25), (25, 20), (25, 10), (25, 0), (50, 0)):
        out["strangers"][f"{enrolled} of {signers} enrolled"] = few(run(10, 10, signers=signers, enrolled=enrolled))  # fmt: skip
    for name, c, d in LEVELS:
        told = [
            run(10, 10, check=c, draw=d, liar=3, tip=True, seed=f"s{i}")
            for i in range(seeds)
        ]
        honest = run(10, 10, check=c, draw=d)
        out["checked"][name] = {
            "lies": seeds, "found": sum(g["lies_found"] for g in told),
            "wrong_jobs_handed_out": sum(g["wrong_handed_out"] for g in told),
            "never_found": sum(g["wrong_never_found"] for g in told),
            "checking_share": honest["checking_share"],
            "saving_after_the_door": honest["saving_after_the_door"],
        }  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    if argv[:1] == ["tables"] and len(argv) in (5, 7):
        opts = dict(zip(argv[1::2], argv[2::2]))
        try:
            plan = sweep.load(Path(opts["--plan"]))
            stops = json.loads(Path(opts["--stops"]).read_text(encoding="utf-8"))
            got = {"the first study's own check": as_run(plan, stops), **tables(plan, stops, int(opts.get("--seeds", 60)))}  # fmt: skip
        except (OSError, ValueError, KeyError) as why:
            print(f"refused: {why!r}", file=sys.stderr)
            return REFUSED
        print(json.dumps(got, indent=1))
        return 0
    opts: dict = {"json": False, "tip": False}
    it = iter(argv[1:])
    for a in it:
        if a in ("--plan", "--stops", "--scale", "--rounds", "--signers", "--enrolled",
                 "--check", "--draw", "--liar", "--seed") and a[2:] not in opts:  # fmt: skip
            opts[a[2:]] = next(it, "")
        elif a in ("--json", "--tip"):
            opts[a[2:]] = True
        else:
            opts = {}
            break
    if argv[:1] != ["count"] or not opts.get("plan") or not opts.get("stops"):
        print(USAGE, file=sys.stderr)
        return REFUSED
    try:
        plan = sweep.load(Path(opts["plan"]))
        stops = json.loads(Path(opts["stops"]).read_text(encoding="utf-8"))
        plan, stops = scaled(plan, stops, int(opts.get("scale", 1)))
        if "rounds" in opts:
            plan = {**plan, "rounds": int(opts["rounds"])}
        num = {
            k: int(opts[k])
            for k in ("signers", "enrolled", "check", "draw", "liar")
            if k in opts
        }
        got = count(
            plan, stops, seed=opts.get("seed", "the door"), tip=opts["tip"], **num
        )
    except (OSError, ValueError, KeyError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    got.pop("per_run")
    if opts["json"]:
        print(json.dumps(got, indent=1, sort_keys=True))
    else:
        print(f"{got['jobs']} jobs; alone {got['alone']} steps; stepped {got['stepped']}, a saving of {got['saving']}%")  # fmt: skip
        print(f"the door: checking {got['checking']} steps ({got['checking_share']}% of alone), done again {got['again']}; saving left {got['saving_after_the_door']}%")  # fmt: skip
        print(f"states kept {got['states_kept']}; rounds a signer's work was held and all stepped again: {got['held_rounds']}")  # fmt: skip
        if got["lies_told"]:
            print(f"lies told {got['lies_told']}, found {got['lies_found']} (round {got['found_in_round']}); wrong jobs handed out {got['wrong_handed_out']}, never found {got['wrong_never_found']}")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
