"""runner.py: what one machine does in the study: run jobs alone, run its
share with the memory, check what the memory holds, or run the project as
it is written. Python 3.9+; NumPy only with `--repo`.

    python demo/shared-runs/study/runner.py MODE --plan PLAN --starts STARTS --to OUT
        (--repo DIR | --toy) [--machine K --round R] [--memory DIR ...]

MODE is one of:

    alone    every job of the plan from its start, with no memory
    shared   the jobs dealt to machine K in round R, with the memory of
             each DIR (an earlier machine's OUT) and its own
    check    of the memory in each DIR: one kept state in N stepped again
             from the kept state before it, and one served job in N run
             afresh from its start, each N and its seed the plan's
    native   the longest job of each trajectory with the project's gravity
             as it is written, saying the bytes at each job's length

Every mode but `native` runs the project with one power in its gravity
written as a product and a square root, changed in memory and never in the
project's files; `--toy` puts a made-up stepper of whole numbers in the
project's place, for tests.

The memory keeps a trajectory's state every `spacing` steps and at each
job's end, under a name made from the trajectory's start and the step
count, and keeps where a trajectory halted. A job goes on from the latest
kept state at or before its length, and is never stepped into a halt the
memory knows.

OUT gets three files: what the machine says of itself (its processor,
system, Python and NumPy; never its name), what it did, one line an act,
and what it kept. The last two are added to and never rewritten. It writes
nowhere else. Exit codes, the kernel's: 0 done; 2 refused (a bad command
line, a plan or starts that don't fit, no such checkout).
"""

from __future__ import annotations

import hashlib
import json
import platform
import struct
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2
MODES = ("alone", "shared", "check", "native")


class Halt(Exception):
    """The stepper would not take the next step; the state is as it was."""


class Toy:
    """A made-up stepper of whole numbers: the same on every machine, with a
    step it refuses when its start says so."""

    said = {"stepper": "toy"}

    def begin(self, start: dict) -> dict:
        t = start["toy"]
        return {"x": t["seed"], "n": 0, "halts_after": t.get("halts_after")}

    def step(self, s: dict) -> None:
        if s["halts_after"] is not None and s["n"] >= s["halts_after"]:
            raise Halt
        s["x"] = (s["x"] * 6364136223846793005 + 1442695040888963407) % 2**64
        s["n"] += 1

    def pack(self, s: dict) -> bytes:
        return struct.pack("<QQ", s["x"], s["n"])

    def unpack(self, start: dict, data: bytes) -> dict:
        x, n = struct.unpack("<QQ", data)
        return {"x": x, "n": n, "halts_after": start["toy"].get("halts_after")}


class Project:
    """The project's own System, from the checkout: stepped by its own
    `step`, one whole step at a time. `as_written` leaves its gravity alone;
    otherwise `d2**1.5` is `d2*np.sqrt(d2)`, in memory."""

    def __init__(self, repo: Path, as_written: bool, core_sha256: str | None = None):
        file = repo / "simulations" / "star_system" / "core.py"
        if not file.is_file():
            raise ValueError(f"{repo} is not a checkout of the project")
        got = hashlib.sha256(file.read_bytes()).hexdigest()
        if core_sha256 and got != core_sha256:
            raise ValueError("the checkout's stepper is not the one the plan names")
        sys.path.insert(0, str(repo))
        try:
            import numpy as np
            from simulations.star_system import core
        except Exception as why:
            raise ValueError(f"{repo} is not a checkout of the project: {why}")
        self.np, self.core = np, core
        self.said = {
            "stepper": "project",
            "core_sha256": got,
            "numpy": np.__version__,
            "power": "as written" if as_written else "a product and a square root",
        }
        if not as_written:
            G = core.G

            def accelerations(self):
                sources = np.flatnonzero(self.masses > 0)
                delta = self.r[None, sources, :] - self.r[:, None, :]
                d2 = np.sum(delta**2, axis=-1)
                d2[sources, np.arange(len(sources))] = np.inf
                pull = self.masses[None, sources] / (d2 * np.sqrt(d2))
                return G * np.sum(delta * pull[:, :, None], axis=1)

            core.System.accelerations = accelerations

    def _array(self, rows):
        return self.np.array([[float.fromhex(x) for x in row] for row in rows])

    def begin(self, start: dict):
        masses = self.np.array([float.fromhex(x) for x in start["masses"]])
        return self.core.System(
            masses, self._array(start["r"]), self._array(start["v"]),
            float.fromhex(start["dt"]),
        )  # fmt: skip

    def step(self, s) -> None:
        try:
            s.step()
        except ValueError:
            raise Halt

    def pack(self, s) -> bytes:
        return (
            s.r.astype("<f8").tobytes()
            + s.v.astype("<f8").tobytes()
            + struct.pack("<d", s.time)
        )

    def unpack(self, start: dict, data: bytes):
        s = self.begin(start)
        n = len(s.masses) * 16
        s.r = self.np.frombuffer(data[:n], dtype="<f8").reshape(-1, 2).copy()
        s.v = self.np.frombuffer(data[n : 2 * n], dtype="<f8").reshape(-1, 2).copy()
        s.time = struct.unpack("<d", data[2 * n :])[0]
        return s


def identity(start: dict, said: dict) -> str:
    """A trajectory's name in the memory: its start and what steps it."""
    return sweep.h(json.dumps([start, said.get("power")], sort_keys=True))


class Memory:
    """Kept states by trajectory and step, and where a trajectory halted.
    What it is given it only reads; what it keeps goes to one file."""

    def __init__(self, given: list[Path], out: Path | None):
        self.states: dict[str, dict[int, bytes]] = {}
        self.halts: dict[str, int] = {}
        self.out = out
        for folder in given:
            path = folder / "memory.jsonl"
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if "halt" in row:
                    self.halts[row["trajectory"]] = row["halt"]
                else:
                    self.states.setdefault(row["trajectory"], {})[row["step"]] = (
                        bytes.fromhex(row["state"])
                    )

    def _write(self, row: dict) -> None:
        if self.out is not None:
            with self.out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")

    def latest(self, tid: str, upto: int) -> tuple[int, bytes | None]:
        steps = [n for n in self.states.get(tid, ()) if n <= upto]
        return (max(steps), self.states[tid][max(steps)]) if steps else (0, None)

    def keep(self, tid: str, step: int, data: bytes) -> None:
        if step and step not in self.states.setdefault(tid, {}):
            self.states[tid][step] = data
            self._write({"trajectory": tid, "step": step, "state": data.hex()})

    def halted(self, tid: str, step: int) -> None:
        if tid not in self.halts:
            self.halts[tid] = step
            self._write({"trajectory": tid, "halt": step})


def run(
    stepper, start: dict, tid: str, steps: int, memory: Memory, spacing: int
) -> dict:
    """One job: on from the latest kept state, up to its length or to where
    the trajectory halts. What it took, what it stepped, where it ended."""
    known = memory.halts.get(tid)
    target = steps if known is None else min(steps, known)
    at, data = memory.latest(tid, target)
    state = stepper.begin(start) if data is None else stepper.unpack(start, data)
    n, tried, began = at, False, time.perf_counter()
    while n < target:
        try:
            stepper.step(state)
        except Halt:
            tried = True
            break
        n += 1
        if n % spacing == 0:
            memory.keep(tid, n, stepper.pack(state))
    packed = stepper.pack(state)
    memory.keep(tid, n, packed)
    if tried:
        memory.halted(tid, n)
    outcome = "ended" if n == steps else "halted" if n else "refused"
    return {
        "asked": steps, "from": at, "took": bool(at) or known is not None,
        "stepped": n - at, "ended": n, "outcome": outcome, "tried_halt": tried,
        "sha256": hashlib.sha256(packed).hexdigest(),
        "seconds": round(time.perf_counter() - began, 4),
    }  # fmt: skip


def processor() -> str:
    """The kind of processor, as the machine names it; never its own name."""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def machine(stepper) -> dict:
    said = {k: v for k, v in stepper.said.items() if k != "power"}
    return {"processor": processor(), "system": platform.system(),
            "python": platform.python_version(), **said}  # fmt: skip


def alone(plan, starts, stepper, act) -> None:
    for job, name, steps in sweep.jobs(plan):
        tid = identity(starts[name], stepper.said)
        got = run(stepper, starts[name], tid, steps, Memory([], None), plan["spacing"])
        act({"job": job, "trajectory": name, **got})


def shared(plan, starts, stepper, act, memory: Memory, k: int, round_: int) -> None:
    for job, name, steps in sweep.mine(plan, k, round_):
        tid = identity(starts[name], stepper.said)
        got = run(stepper, starts[name], tid, steps, memory, plan["spacing"])
        act({"job": job, "trajectory": name, "machine": k, "round": round_ + 1, **got})


def check(plan, starts, stepper, act, memory: Memory, given: list[Path]) -> None:
    names = {identity(starts[t["name"]], stepper.said): t["name"] for t in plan["trajectories"]}  # fmt: skip
    kept = sorted(
        f"{names[tid]}@{step}"
        for tid, states in memory.states.items()
        if tid in names
        for step in states
    )
    for state in sweep.drawn(plan["draw_seed"], kept, plan["check_one_in"]):
        name, _, step = state.rpartition("@")
        tid = next(t for t, n in names.items() if n == name)
        before = max((n for n in memory.states[tid] if n < int(step)), default=0)
        s = (
            stepper.unpack(starts[name], memory.states[tid][before])
            if before
            else stepper.begin(starts[name])
        )
        try:
            for _ in range(int(step) - before):
                stepper.step(s)
            same = stepper.pack(s) == memory.states[tid][int(step)]
        except Halt:
            same = False
        act({"mode": "check", "trajectory": name, "step": int(step), "from": before,
             "stepped": int(step) - before, "same": same})  # fmt: skip
    served = []
    for folder in given:
        for line in (folder / "acts.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("mode") == "shared" and row.get("took"):
                served.append(row["job"])
    steps_of = {job: (name, steps) for job, name, steps in sweep.jobs(plan)}
    for job in sweep.drawn(plan["draw_seed"], served, plan["draw_one_in"]):
        name, steps = steps_of[job]
        tid = identity(starts[name], stepper.said)
        got = run(stepper, starts[name], tid, steps, Memory([], None), plan["spacing"])
        act({"mode": "afresh", "job": job, "trajectory": name, **got})


def native(plan, starts, stepper, act) -> None:
    for t in plan["trajectories"]:
        name, memory = t["name"], Memory([], None)
        tid = identity(starts[name], stepper.said)
        for steps in sorted(sweep.lengths(plan, t)):
            got = run(stepper, starts[name], tid, steps, memory, plan["spacing"])
            act({"job": f"{name}@{steps}", "trajectory": name, **got})


def args_of(argv: list[str]) -> dict:
    if not argv or argv[0] not in MODES:
        raise ValueError(USAGE)
    opts: dict = {"mode": argv[0], "memory": [], "toy": False}
    it = iter(argv[1:])
    for a in it:
        if a in ("--plan", "--starts", "--to", "--repo", "--machine", "--round"):
            if a[2:] in opts:
                raise ValueError(USAGE)
            opts[a[2:]] = next(it, "")
        elif a == "--memory":
            opts["memory"].append(Path(next(it, "")))
        elif a == "--toy":
            opts["toy"] = True
        else:
            raise ValueError(USAGE)
    if not all(opts.get(k) for k in ("plan", "starts", "to")):
        raise ValueError(USAGE)
    if bool(opts.get("repo")) == opts["toy"]:
        raise ValueError(USAGE)
    if opts["mode"] == "shared":
        if not (opts.get("machine", "").isdigit() and opts.get("round", "").isdigit()):
            raise ValueError(USAGE)
        opts["machine"], opts["round"] = int(opts["machine"]), int(opts["round"])
    for folder in opts["memory"]:
        if not (folder / "memory.jsonl").is_file():
            raise ValueError(f"refused: {folder} holds no memory")
    if opts["mode"] == "check" and not opts["memory"]:
        raise ValueError("refused: a check needs a memory to check")
    return opts


def main(argv: list[str]) -> int:
    try:
        opts = args_of(argv)
        plan = sweep.load(Path(opts["plan"]))
        starts = json.loads(Path(opts["starts"]).read_text(encoding="utf-8"))
        if set(starts) != {t["name"] for t in plan["trajectories"]}:
            raise ValueError("refused: the starts are not this plan's")
        if opts["mode"] == "shared" and not (
            opts["machine"] < plan["machines"] and 1 <= opts["round"] <= plan["rounds"]
        ):
            raise ValueError("refused: no such machine or round in this plan")
        stepper = (
            Toy() if opts["toy"]
            else Project(Path(opts["repo"]), opts["mode"] == "native",
                         (plan.get("project") or {}).get("core_sha256"))
        )  # fmt: skip
    except (OSError, ValueError, json.JSONDecodeError) as why:
        print(why if str(why).startswith(("usage", "refused")) else f"refused: {why}", file=sys.stderr)  # fmt: skip
        return REFUSED
    out = Path(opts["to"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "machine.json").write_text(
        json.dumps(machine(stepper), sort_keys=True) + "\n"
    )
    (out / "memory.jsonl").touch()
    (out / "acts.jsonl").touch()
    mode = opts["mode"]

    def act(row: dict) -> None:
        with (out / "acts.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"mode": mode, **row}, sort_keys=True) + "\n")

    if mode == "alone":
        alone(plan, starts, stepper, act)
    elif mode == "native":
        native(plan, starts, stepper, act)
    else:
        memory = Memory(opts["memory"], out / "memory.jsonl")
        if mode == "shared":
            shared(
                plan, starts, stepper, act, memory, opts["machine"], opts["round"] - 1
            )
        else:
            check(plan, starts, stepper, act, memory, opts["memory"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
