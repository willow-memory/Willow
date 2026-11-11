"""sweep.py: the sweep as a plan file writes it: its jobs, who steps which,
what memory should save, and which served results are run afresh.

    python demo/shared-runs/study/sweep.py say PLAN
    python demo/shared-runs/study/sweep.py starts PLAN --repo DIR

A plan names trajectories and the lengths each is run to. A job is one
trajectory run to one length, named `trajectory@steps`. Everything here is
worked out from the plan's own words, before any job is run:

    the deal       the jobs in an order nobody chose (each job's name,
                   hashed with the plan's deal seed), cut into rounds
    the owner      the machine a trajectory belongs to: its name, hashed
    the prediction the steps a sweep need not step when every trajectory
                   is stepped once, to its longest job, as a share of the
                   steps of every job run alone
    the draw       of a list of names, the one in N the plan's draw seed
                   picks

`say` prints them. `starts` builds each trajectory's start with the
project's own `make_system`, in the checkout at DIR, and prints it as exact
numbers (each float in hex), so every machine begins from the same bytes
and none builds a start itself. It steps nothing.

It reads the plan and writes nothing. Exit codes, the kernel's: 0 said;
2 refused (a bad command line, a plan that isn't one, a checkout that
isn't the project's).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    """The plan, or ValueError saying what it lacks."""
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    for name in ("machines", "rounds", "spacing", "draw_one_in", "check_one_in"):
        if type(plan.get(name)) is not int or plan[name] < 1:
            raise ValueError(f"the plan's {name} must be a whole number above 0")
    for name in ("deal_seed", "draw_seed"):
        if not isinstance(plan.get(name), str) or not plan[name]:
            raise ValueError(f"the plan names no {name}")
    names = [t.get("name") for t in plan.get("trajectories") or []]
    if not names or len(set(names)) != len(names) or not all(names):
        raise ValueError("the plan's trajectories need a name each, no two the same")
    for t in plan["trajectories"]:
        steps = lengths(plan, t)
        if not steps or any(type(n) is not int or n < 1 for n in steps):
            raise ValueError(f"{t['name']}: its lengths must be whole numbers above 0")
        if len(set(steps)) != len(steps):
            raise ValueError(f"{t['name']}: a length is given twice")
    return plan


def lengths(plan: dict, trajectory: dict) -> list[int]:
    return trajectory.get("lengths") or plan.get("lengths") or []


def jobs(plan: dict) -> list[tuple[str, str, int]]:
    """(the job's name, its trajectory, its steps), in the plan's order."""
    return [
        (f"{t['name']}@{n}", t["name"], n)
        for t in plan["trajectories"]
        for n in lengths(plan, t)
    ]


def dealt(plan: dict) -> list[list[tuple[str, str, int]]]:
    """The jobs of each round: every job once, in the order its name's hash
    with the deal seed gives, cut into rounds as evenly as it goes."""
    order = sorted(jobs(plan), key=lambda j: h(f"{plan['deal_seed']}:{j[0]}"))
    rounds = plan["rounds"]
    return [
        [j for i, j in enumerate(order) if i * rounds // len(order) == r]
        for r in range(rounds)
    ]


def owner(plan: dict, trajectory: str) -> int:
    """The machine a trajectory belongs to, in every round."""
    return int(h(trajectory), 16) % plan["machines"]


def mine(plan: dict, machine: int, round_: int) -> list[tuple[str, str, int]]:
    """The jobs one machine runs in one round, in the order they were dealt."""
    return [j for j in dealt(plan)[round_] if owner(plan, j[1]) == machine]


def predicted(plan: dict) -> dict:
    """What memory should save, from the plan alone: every job alone steps
    its own length; with a memory each trajectory is stepped once, to its
    longest job. A trajectory that halts shortens both; where it halts
    isn't in the plan, so judge.py takes it from the baseline, which has
    no memory, and holds the shared run to the share that leaves."""
    alone = sum(n for _, _, n in jobs(plan))
    once = sum(max(lengths(plan, t)) for t in plan["trajectories"])
    return {"alone": alone, "once": once, "share": round(100 * (1 - once / alone), 1)}


def as_dealt(plan: dict) -> int:
    """The steps the shared run steps if nothing halts, counted and not
    run: each job, in the order it is dealt, goes on from the latest state
    kept at or before its length. A short job dealt after a longer one
    steps on from the last kept state before it, so the order costs a
    little, and how little turns on the spacing."""
    kept: dict[str, set[int]] = {}
    stepped = 0
    for round_jobs in dealt(plan):
        for _, name, n in round_jobs:
            have = kept.setdefault(name, {0})
            at = max(k for k in have if k <= n)
            stepped += n - at
            have.update(range(at - at % plan["spacing"], n + 1, plan["spacing"]))
            have.add(n)
    return stepped


def drawn(seed: str, names: list[str], one_in: int) -> list[str]:
    """One in `one_in` of the names, rounded up: the ones whose hash with the
    seed comes first. The same names and seed give the same draw."""
    order = sorted(set(names), key=lambda n: h(f"{seed}:{n}"))
    return sorted(order[: -(-len(order) // one_in)]) if order else []


def starts(plan: dict, repo: Path) -> dict:
    """{a trajectory's name: its start as exact numbers}: masses, positions,
    velocities and the step, each float in hex. A trajectory that says
    `toy` is its own start. `dt_times` makes the step that many times the
    one the project picks, for a setup meant to be too coarse to run."""
    out, core = {}, None
    for t in plan["trajectories"]:
        if "toy" in t:
            out[t["name"]] = {"toy": t["toy"]}
            continue
        if core is None:
            sys.path.insert(0, str(repo))
            try:
                from simulations.star_system import core
            except Exception as why:
                raise ValueError(f"{repo} is not a checkout of the project: {why}")
        system = core.make_system(t["star"], tuple(t["planets"]), t.get("distances"))
        out[t["name"]] = {
            "masses": [float(x).hex() for x in system.masses],
            "r": [[float(x).hex() for x in row] for row in system.r],
            "v": [[float(x).hex() for x in row] for row in system.v],
            "dt": float(system.dt * t.get("dt_times", 1)).hex(),
        }
    return out


def say(plan: dict) -> str:
    p = predicted(plan)
    out = [
        f"{len(jobs(plan))} jobs over {len(plan['trajectories'])} trajectories, "
        f"{plan['machines']} machines, {plan['rounds']} rounds, "
        f"a state kept every {plan['spacing']} steps",
        f"alone: {p['alone']} steps; each trajectory once: {p['once']}; "
        f"predicted saving {p['share']}%",
        f"in the order dealt, if nothing halts: {as_dealt(plan)} steps, "
        f"a saving of {round(100 * (1 - as_dealt(plan) / p['alone']), 1)}%",
    ]
    for r, round_jobs in enumerate(dealt(plan)):
        for m in range(plan["machines"]):
            took = [j[0] for j in round_jobs if owner(plan, j[1]) == m]
            out.append(f"round {r + 1}, machine {m}: {len(took)} jobs")
    for m in range(plan["machines"]):
        owned = [t["name"] for t in plan["trajectories"] if owner(plan, t["name"]) == m]
        out.append(f"machine {m} owns {len(owned)}: {', '.join(owned) or 'none'}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    try:
        if len(argv) == 2 and argv[0] == "say":
            print(say(load(Path(argv[1]))))
            return 0
        if len(argv) == 4 and argv[0] == "starts" and argv[2] == "--repo":
            print(json.dumps(starts(load(Path(argv[1])), Path(argv[3])), indent=1))
            return 0
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(USAGE, file=sys.stderr)
    return REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
