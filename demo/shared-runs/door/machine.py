"""machine.py: one machine of a run at size, checked, logged, taken up again, sealed.

The first study's stepping, with a check before it starts, a log of
everything it does, a way to go on after it is stopped, a door on what
it is given, and a seal on what it leaves.

    python demo/shared-runs/door/machine.py MODE --plan PLAN --starts STARTS --to OUT
        (--repo DIR | --toy) [--machine K --round R] [--memory DIR ...]
        [--ring FILE] [--id FILE] [--budget SECONDS] [--canary N] [--one-in N]
        [--from DIR]
    python demo/shared-runs/door/machine.py verify --run OUT [--ring FILE]

MODE is `alone`, `shared` or `check`. The stepping is runner.py's own
steppers and its own rule for a job (on from the latest kept state at or
before its length, never into a halt the memory knows), so a job comes to
the bytes the first study's machines came to. What is added:

    before     it checks, and says each check in its log: the plan and the
               starts are each other's; the stepper is the one the plan
               names; there is room on the disk; and, when OUT already
               holds part of a run, that it is the same run of the same
               plan by the same code, on the same kind of processor. One that is not is refused.
    the log    `log.jsonl`: one line a thing done, each holding the hash
               of the line before, so a line changed or taken out shows.
    going on   run again with the same command and it goes on. A job that
               was done is not done again. A job cut off part way goes on
               from what it had kept, and its act says the whole of what
               it stepped and how many times it was taken up again. A
               last line torn by the cut is dropped, and that is logged.
               Where a machine comes back with an empty disk (Kaggle's
               do), `--from DIR` is what the run before left: it is
               copied into OUT first, and the run goes on from it.
    a budget   `--budget SECONDS`: after that long it stops clean, before
               its next job or inside one at a state it has just kept,
               and exits 42: run it again.
    a canary   every N jobs (`--canary`, 25) it steps one state it kept
               again from the one before. A machine that does not agree
               with itself stops, exit 2.
    the door   each `--memory` folder is another run's OUT. It is taken in
               only if it is whole (its seal's hashes are its files'), is
               this plan's by this code, and its signer is in `--ring` (a
               file of enrolled public keys) or an enrolled signer's check
               found every state of it the same. One that is whole but
               whose signer is not known is held: logged, and not gone on
               from. One that is not whole is refused, and the run stops.
    a seal     when it ends clean: `manifest.json`, the SHA-256 of each
               file it leaves, of the plan, the starts and the code, what
               it took in and what it held, signed with the key in `--id`
               (the share add-on's kind). With no `--id` it is left
               unsigned, and says so.

`check` steps kept states again from the state before them (the one before
in everything it was given, so a run that went on from another's state is
held to that state, and the other run to its own), every one unless
`--one-in N`, and steps up to every halt the memory names to see
it halt: a halt is not taken on a signer's word. It leaves no memory of
its own, and its seal names each folder it checked and what it found.

`verify` reads a finished OUT and says what holds: the seal, the log's
chain, the signer's standing against a ring.

Exit codes, the kernel's: 0 done, or it holds; 42 stopped at its budget,
or something was held; 2 refused, or it does not hold.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# beside it when it is carried alone; else where the repository keeps them
for place in (
    HERE.parent / "study",
    *(p / "adapters" / "stdlib" / "share" for p in HERE.parents[2:3]),
    HERE,
):
    sys.path.insert(0, str(place))
import runner  # noqa: E402
import sweep  # noqa: E402

try:
    import ed25519  # the share add-on's, carried beside this when it travels
except ImportError:  # pragma: no cover - only where the file was not carried
    ed25519 = None

USAGE = __doc__.split("\n\n")[2]
ALIVE, ESCALATE, REFUSED = 0, 42, 2
MODES = ("alone", "shared", "check")
GENESIS = "0" * 64
FILES = ("acts.jsonl", "memory.jsonl", "log.jsonl", "machine.json")


class Refuse(Exception):
    """Something that stops the run before it does harm."""


class Cut(Exception):
    """The budget ran out inside a job, at a state it had just kept."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(doc: dict) -> bytes:
    return json.dumps(
        doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def lines_of(path: Path) -> tuple[list[dict], bool]:
    """(the whole lines of a file kept one a line, whether a last line torn
    by a cut was dropped). The file is left holding only the whole ones."""
    if not path.exists():
        return [], False
    raw = path.read_bytes()
    rows, good = [], 0
    for line in raw.split(b"\n"):
        if not line:
            good += 1
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            break
        good += len(line) + 1
    torn = good < len(raw) and raw[good:].strip() != b""
    if torn or (raw and not raw.endswith(b"\n")):
        whole = b"".join(canon(r) + b"\n" for r in rows)
        path.write_bytes(whole)
    return rows, torn


def add(path: Path, row: dict) -> None:
    """One line on the end of a file, on the disk before anything goes on."""
    with path.open("ab") as f:
        f.write(canon(row) + b"\n")
        f.flush()
        os.fsync(f.fileno())


class Log:
    """What the machine did, one line a thing, each line holding the hash of
    the one before."""

    def __init__(self, path: Path):
        self.path = path
        rows, self.torn = lines_of(path)
        self.n = len(rows)
        self.tip = rows[-1]["hash"] if rows else GENESIS
        self.began = time.time()

    def say(self, what: str, **more) -> None:
        row = {"n": self.n, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "what": what, "prev": self.tip, **more}  # fmt: skip
        row["hash"] = hashlib.sha256(canon(row)).hexdigest()
        add(self.path, row)
        self.n, self.tip = self.n + 1, row["hash"]


def chain_holds(path: Path) -> tuple[bool, int]:
    """(whether every line of a log holds the hash of the one before and its
    own, how many lines)."""
    rows, torn = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            torn = True
    prev = GENESIS
    for i, row in enumerate(rows):
        body = {k: v for k, v in row.items() if k != "hash"}
        if row.get("prev") != prev or row.get("n") != i or row.get("hash") != hashlib.sha256(canon(body)).hexdigest():  # fmt: skip
            return False, len(rows)
        prev = row["hash"]
    return not torn, len(rows)


def read_id(path: Path | None) -> bytes | None:
    """A share add-on identity's secret half, or None."""
    if path is None:
        return None
    head, _, seed = path.read_text(encoding="utf-8").strip().partition(" ")
    if head != "ed25519" or len(seed) != 64:
        raise Refuse(f"{path} is not an identity the share add-on made")
    return bytes.fromhex(seed)


def ring_of(path: Path | None) -> dict[str, str] | None:
    """{an enrolled public key: whose}, or None when no ring was given."""
    if path is None:
        return None
    ring = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(ring, dict) or not all(len(k) == 64 for k in ring):
        raise Refuse(f"{path} is not a ring of public keys")
    return ring


def tools() -> dict[str, str]:
    """The SHA-256 of each file that decides what is stepped and kept."""
    out = {"machine.py": sha(HERE / "machine.py")}
    for name in ("runner.py", "sweep.py"):
        place = HERE / name if (HERE / name).exists() else HERE.parent / "study" / name
        out[name] = sha(place)
    return out


def held(folder: Path, ring: dict[str, str] | None, ours: dict, vouched: dict[str, str]) -> tuple[str, str]:  # fmt: skip
    """(how another run's folder stands at this door, why): `taken` to be
    gone on from, `held` whole but not known, `refused` not whole or not
    this plan's."""
    seal = folder / "manifest.json"
    if not seal.is_file():
        return "refused", "it has no seal: the run did not end, or is not one of these"
    doc = json.loads(seal.read_text(encoding="utf-8"))
    for name, want in doc.get("files", {}).items():
        if not (folder / name).is_file() or sha(folder / name) != want:
            return "refused", f"{name} is not the file its seal names"
    if not chain_holds(folder / "log.jsonl")[0]:
        return "refused", "its log does not hold"
    for key in ("plan", "starts", "tools", "power"):
        if doc.get(key) != ours[key]:
            return "refused", f"it is not this run's: its {key} is another"
    signer = doc.get("signer")
    if signer and ed25519 is not None and not signed(doc):
        return "refused", "its seal's signature does not hold"
    if ring is None:
        return "taken", "no ring was given, so whoever is whole is taken"
    if signer in ring:
        return "taken", f"its signer is enrolled: {ring[signer]}"
    this = hashlib.sha256(seal.read_bytes()).hexdigest()
    if this in vouched:
        return (
            "taken",
            f"every state of it was stepped again and found the same by {vouched[this]}",
        )
    return "held", "it is whole, and its signer is not one this door has enrolled"


def vouches(folders: list[Path], ring: dict[str, str] | None) -> dict[str, str]:
    """{a run's seal's SHA-256: the enrolled checker that found all of it the
    same}, from the check runs among the folders given. A run that went on
    from another's states is only as good as that other: it is vouched for
    only if each run it took in is among the folders, and is an enrolled
    signer's or is vouched for itself."""
    if ring is None:
        return {}
    found: dict[str, str] = {}
    seals: dict[str, dict] = {}
    for folder in folders:
        seal = folder / "manifest.json"
        if not seal.is_file():
            continue
        doc = json.loads(seal.read_text(encoding="utf-8"))
        seals[sha(seal)] = doc
        if (
            doc.get("mode") != "check"
            or doc.get("signer") not in ring
            or not signed(doc)
        ):
            continue
        for one in doc.get("checked", {}).values():
            if one["all_the_same"] and one["states"] == one["of"]:
                found[one["seal"]] = ring[doc["signer"]]
    while True:
        good = {
            s
            for s, d in seals.items()
            if s in found or (d.get("signer") in ring and signed(d))
        }
        lost = [
            s for s in found
            if s not in seals
            or any(v["how"] == "taken" and v["seal"] not in good for v in seals[s].get("took_in", {}).values())
        ]  # fmt: skip
        if not lost:
            return found
        for s in lost:
            del found[s]


def signed(doc: dict) -> bool:
    """Whether a seal's signature is its signer's over the rest of it."""
    if not doc.get("signer") or ed25519 is None:
        return False
    body = {k: v for k, v in doc.items() if k != "sig"}
    try:
        return ed25519.check(
            bytes.fromhex(doc["signer"]), canon(body), bytes.fromhex(doc.get("sig", ""))
        )
    except ValueError:
        return False


class Run:
    def __init__(self, opts: dict):
        self.opts = opts
        self.mode = opts["mode"]
        self.out = Path(opts["to"])
        self.plan_file, self.starts_file = Path(opts["plan"]), Path(opts["starts"])
        self.plan = sweep.load(self.plan_file)
        self.starts = json.loads(self.starts_file.read_text(encoding="utf-8"))
        self.out.mkdir(parents=True, exist_ok=True)
        carried = Path(opts["from"]) if opts.get("from") else None
        if (
            carried is not None
            and (carried / "run.json").is_file()
            and not (self.out / "run.json").exists()
        ):
            for name in (*FILES, "run.json", "begun.jsonl", "manifest.json"):
                if (carried / name).is_file():
                    shutil.copyfile(carried / name, self.out / name)
        self.log = Log(self.out / "log.jsonl")
        if carried is not None and not (self.out / "manifest.json").exists():
            self.log.say(
                "carried on from",
                folder=carried.name,
                had=(self.out / "run.json").exists(),
            )
        self.began = time.time()
        self.budget = float(opts["budget"]) if opts.get("budget") else None
        self.ring = ring_of(Path(opts["ring"]) if opts.get("ring") else None)
        self.seed = read_id(Path(opts["id"]) if opts.get("id") else None)
        self.took_in: dict[str, dict] = {}

    # ── before ──────────────────────────────────────────────────────────────
    def check(self, what: str, ok: bool, said: str = "") -> None:
        self.log.say("checked", check=what, holds=ok, said=said)
        if not ok:
            raise Refuse(f"{what}: {said}")

    def preflight(self) -> None:
        opts, plan = self.opts, self.plan
        self.check("python", sys.version_info >= (3, 9), sys.version.split()[0])
        names = {t["name"] for t in plan["trajectories"]}
        self.check("the starts are this plan's", set(self.starts) == names,
                   f"{len(self.starts)} starts, {len(names)} trajectories")  # fmt: skip
        if self.mode == "shared":
            ok = (
                opts["machine"] < plan["machines"]
                and 1 <= opts["round"] <= plan["rounds"]
            )
            self.check("the machine and the round are in the plan", ok,
                       f"machine {opts['machine']}, round {opts['round']}")  # fmt: skip
        try:
            self.stepper = (
                runner.Toy() if opts["toy"]
                else runner.Project(Path(opts["repo"]), False,
                                    **{k: (plan.get("project") or {}).get(k) for k in ("core_sha256", "numpy")})
            )  # fmt: skip
        except ValueError as why:
            self.check("the stepper is the plan's", False, str(why))
        self.check(
            "the stepper is the plan's",
            True,
            json.dumps(self.stepper.said, sort_keys=True),
        )
        free = shutil.disk_usage(self.out).free
        need = 2000 * sum(max(sweep.lengths(plan, t)) // plan["spacing"] + 12 for t in plan["trajectories"])  # fmt: skip
        self.check("there is room for what would be kept", free > need, f"{free} bytes free, about {need} wanted")  # fmt: skip
        self.ours = {
            "plan": sha(self.plan_file), "starts": sha(self.starts_file), "tools": tools(),
            "power": self.stepper.said.get("power"),
        }  # fmt: skip
        mine = {**self.ours, "mode": self.mode, "machine": opts.get("machine"), "round": opts.get("round"),
                "one_in": opts.get("one_in", 1)}  # fmt: skip
        was = self.out / "run.json"
        now = runner.machine(self.stepper)
        if was.exists():
            same = json.loads(was.read_text(encoding="utf-8")) == mine
            self.check("what is already here is this same run", same, self.out.name)
            kind = json.loads((self.out / "machine.json").read_text(encoding="utf-8"))[
                "kind"
            ]
            self.check("this is the kind of processor that began it", kind == now["kind"],
                       f"began on {kind}, this is {now['kind']}")  # fmt: skip
        else:
            was.write_text(json.dumps(mine, sort_keys=True) + "\n")
            (self.out / "machine.json").write_text(
                json.dumps(now, sort_keys=True) + "\n"
            )
        (self.out / "memory.jsonl").touch()
        (self.out / "acts.jsonl").touch()

    # ── the door ────────────────────────────────────────────────────────────
    def door(self) -> list[Path]:
        given = [Path(p) for p in self.opts["memory"]]
        spoken = vouches(given, self.ring)
        taken = []
        for folder in given:
            if (folder / "run.json").is_file() and json.loads((folder / "run.json").read_text()).get("mode") == "check":  # fmt: skip
                continue
            how, why = held(folder, self.ring, self.ours, spoken)
            seal = folder / "manifest.json"
            self.took_in[folder.name] = {"how": how, "why": why,
                                         "seal": sha(seal) if seal.is_file() else None}  # fmt: skip
            self.log.say("at the door", folder=folder.name, how=how, why=why)
            if how == "refused":
                raise Refuse(f"{folder.name} is refused at the door: {why}")
            if how == "taken":
                taken.append(folder)
        return taken

    # ── stepping ────────────────────────────────────────────────────────────
    def over_budget(self) -> bool:
        return self.budget is not None and time.time() - self.began >= self.budget

    def job(
        self, job: str, name: str, steps: int, memory: runner.Memory, begun: dict
    ) -> dict:
        """One job, by runner.py's rule, kept so that it can be taken up again."""
        stepper, start, spacing = self.stepper, self.starts[name], self.plan["spacing"]
        tid = runner.identity(start, stepper.said)
        known = memory.halts.get(tid)
        target = steps if known is None else min(steps, known)
        at, data = memory.latest(tid, target)
        state = stepper.begin(start) if data is None else stepper.unpack(start, data)
        first = begun.get(job)
        if first is None:
            first = {
                "job": job,
                "from": at,
                "took": bool(at) or known is not None,
                "again": 0,
            }
        else:
            first = {**first, "again": first["again"] + 1}
        begun[job] = first
        add(self.out / "begun.jsonl", first)
        n, tried, clock = at, False, time.perf_counter()
        while n < target:
            try:
                stepper.step(state)
            except runner.Halt:
                tried = True
                break
            n += 1
            if n % spacing == 0:
                memory.keep(tid, n, stepper.pack(state))
                if n < target and memory.out is not None and self.over_budget():
                    raise Cut(job, n)
        packed = stepper.pack(state)
        memory.keep(tid, n, packed)
        if tried:
            memory.halted(tid, n)
        outcome = "ended" if n == steps else "halted" if n else "refused"
        return {
            "asked": steps, "from": first["from"], "took": first["took"], "stepped": n - first["from"],
            "ended": n, "outcome": outcome, "tried_halt": tried, "taken_up_again": first["again"],
            "sha256": hashlib.sha256(packed).hexdigest(), "seconds": round(time.perf_counter() - clock, 4),
        }  # fmt: skip

    def canary(self, memory: runner.Memory, name: str) -> None:
        """One state this machine kept, stepped again from the one before."""
        start = self.starts[name]
        tid = runner.identity(start, self.stepper.said)
        steps = sorted(memory.states.get(tid, ()))
        if not steps:
            return
        step = steps[-1]
        before = steps[-2] if len(steps) > 1 else 0
        s = self.stepper.unpack(start, memory.states[tid][before]) if before else self.stepper.begin(start)  # fmt: skip
        try:
            for _ in range(step - before):
                self.stepper.step(s)
            same = self.stepper.pack(s) == memory.states[tid][step]
        except runner.Halt:
            same = False
        self.log.say("canary", trajectory=name, step=step, same=same)
        if not same:
            raise Refuse(
                f"this machine does not agree with itself: {name} at step {step}"
            )

    def step_jobs(self) -> int:
        plan, mode = self.plan, self.mode
        taken = self.door() if mode == "shared" else []
        acts, torn_acts = lines_of(self.out / "acts.jsonl")
        _, torn_memory = lines_of(self.out / "memory.jsonl")
        begun_rows, _ = lines_of(self.out / "begun.jsonl")
        done = {a["job"] for a in acts}
        begun = {row["job"]: row for row in begun_rows}
        if torn_acts or torn_memory or self.log.torn:
            self.log.say("a line torn by a cut was dropped", acts=torn_acts, memory=torn_memory, log=self.log.torn)  # fmt: skip
        self.log.say("going on" if done or begun else "starting", mode=mode, done=len(done),
                     cut_off=sorted(set(begun) - done))  # fmt: skip
        if mode == "alone":
            jobs = sweep.jobs(plan)
        else:
            jobs = sweep.mine(plan, self.opts["machine"], self.opts["round"] - 1)
        every = int(self.opts.get("canary") or 25)
        memory = runner.Memory([*taken, self.out], self.out / "memory.jsonl") if mode == "shared" else None  # fmt: skip
        since = 0
        for job, name, steps in jobs:
            if job in done:
                continue
            if self.over_budget():
                self.log.say(
                    "stopped at the budget", done=len(done), left=len(jobs) - len(done)
                )
                return ESCALATE
            mem = memory if memory is not None else runner.Memory([], None)
            try:
                got = self.job(job, name, steps, mem, begun)
            except Cut as cut:
                self.log.say("stopped at the budget", done=len(done), left=len(jobs) - len(done),
                             inside=cut.args[0], kept_to=cut.args[1])  # fmt: skip
                return ESCALATE
            row = {"mode": mode, "job": job, "trajectory": name, **got}
            if mode == "shared":
                row.update(machine=self.opts["machine"], round=self.opts["round"])
            add(self.out / "acts.jsonl", row)
            done.add(job)
            since += 1
            if since >= every and memory is not None:
                self.canary(memory, name)
                since = 0
                self.log.say("so far", done=len(done), of=len(jobs), seconds=round(time.time() - self.began, 1))  # fmt: skip
        return ALIVE

    # ── checking ────────────────────────────────────────────────────────────
    def check_states(self) -> int:
        given = [Path(p) for p in self.opts["memory"]]
        one_in = int(self.opts.get("one_in") or 1)
        acts, _ = lines_of(self.out / "acts.jsonl")
        seen = {(a["of"], a["trajectory"], a["step"], a["mode"]): a for a in acts}
        runs = [f for f in given if (f / "memory.jsonl").is_file()]
        self.all = runner.Memory(runs, None)
        names = {runner.identity(self.starts[t["name"]], self.stepper.said): t["name"] for t in self.plan["trajectories"]}  # fmt: skip
        self.log.say(
            "going on" if acts else "starting",
            mode="check",
            done=len(acts),
            folders=len(given),
        )
        self.found: dict[str, dict] = {}
        for folder in given:
            how, why = held(folder, None, self.ours, {})
            self.log.say("at the door", folder=folder.name, how=how, why=why)
            if how == "refused":
                raise Refuse(f"{folder.name} is refused at the door: {why}")
            memory = runner.Memory([folder], None)
            states = sorted(
                (names[t], x)
                for t, xs in memory.states.items()
                if t in names
                for x in xs
            )
            pick = set(
                sweep.drawn(
                    self.plan["draw_seed"], [f"{n}@{x}" for n, x in states], one_in
                )
            )
            stepped = same = 0
            for name, step in states:
                if f"{name}@{step}" not in pick:
                    continue
                key = (folder.name, name, step, "check")
                if key in seen:
                    row = seen[key]
                else:
                    if self.over_budget():
                        self.log.say("stopped at the budget", folder=folder.name)
                        return ESCALATE
                    row = self.one_state(folder.name, memory, name, step)
                    add(self.out / "acts.jsonl", row)
                stepped += 1
                same += bool(row["same"])
            halts = sorted((names[t], k) for t, k in memory.halts.items() if t in names)
            halts_hold = 0
            for name, at in halts:
                key = (folder.name, name, at, "halt-check")
                if key in seen:
                    row = seen[key]
                else:
                    row = self.one_halt(folder.name, memory, name, at)
                    add(self.out / "acts.jsonl", row)
                halts_hold += bool(row["same"])
            self.found[folder.name] = {
                "seal": sha(folder / "manifest.json"), "of": len(states), "states": stepped, "same": same,
                "halts": len(halts), "halts_that_halt": halts_hold,
                "all_the_same": same == stepped and halts_hold == len(halts),
            }  # fmt: skip
            self.log.say(
                "checked a folder", folder=folder.name, **self.found[folder.name]
            )
        return ALIVE

    def one_state(self, of: str, memory: runner.Memory, name: str, step: int) -> dict:
        start = self.starts[name]
        tid = runner.identity(start, self.stepper.said)
        before = max((x for x in self.all.states[tid] if x < step), default=0)
        s = self.stepper.unpack(start, self.all.states[tid][before]) if before else self.stepper.begin(start)  # fmt: skip
        try:
            for _ in range(step - before):
                self.stepper.step(s)
            same = self.stepper.pack(s) == memory.states[tid][step]
        except runner.Halt:
            same = False
        return {"mode": "check", "of": of, "trajectory": name, "step": step, "from": before,
                "stepped": step - before, "same": same}  # fmt: skip

    def one_halt(self, of: str, memory: runner.Memory, name: str, at: int) -> dict:
        """A halt the memory names, stepped up to: it must be reached, and
        the step after it must not be taken."""
        start = self.starts[name]
        tid = runner.identity(start, self.stepper.said)
        before = max((x for x in self.all.states.get(tid, {}) if x <= at), default=0)
        s = self.stepper.unpack(start, self.all.states[tid][before]) if before else self.stepper.begin(start)  # fmt: skip
        halts = False
        try:
            if at < 0:
                raise runner.Halt
            for _ in range(at - before):
                self.stepper.step(s)
            try:
                self.stepper.step(s)
            except runner.Halt:
                halts = True
        except runner.Halt:
            halts = False
        return {"mode": "halt-check", "of": of, "trajectory": name, "step": at, "from": before,
                "stepped": at - before, "same": halts}  # fmt: skip

    # ── after ───────────────────────────────────────────────────────────────
    def seal(self) -> None:
        acts, _ = lines_of(self.out / "acts.jsonl")
        self.log.say(
            "ended", acts=len(acts), seconds=round(time.time() - self.began, 1)
        )
        doc = {
            **self.ours, "mode": self.mode, "machine": self.opts.get("machine"), "round": self.opts.get("round"),
            "acts": len(acts), "log_tip": self.log.tip, "log_lines": self.log.n,
            "files": {name: sha(self.out / name) for name in FILES},
            "took_in": self.took_in,
            "kind": json.loads((self.out / "machine.json").read_text())["kind"],
        }  # fmt: skip
        if self.mode == "check":
            doc["checked"] = self.found
        if self.seed is not None and ed25519 is not None:
            doc["signer"] = ed25519.public(self.seed).hex()
            doc["sig"] = ed25519.sign(self.seed, canon(doc)).hex()
        else:
            doc["signer"] = None
        (self.out / "manifest.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n"
        )

    def go(self) -> int:
        if (self.out / "manifest.json").exists():
            print(f"{self.out} is ended and sealed; nothing was done")
            return ALIVE
        self.preflight()
        code = self.check_states() if self.mode == "check" else self.step_jobs()
        if code == ALIVE:
            self.seal()
            if any(v["how"] == "held" for v in self.took_in.values()):
                return ESCALATE
        return code


def verify(run: Path, ring: dict[str, str] | None) -> tuple[int, list[str]]:
    """(the exit code, what holds and what does not) for a finished run."""
    said = []
    seal = run / "manifest.json"
    if not seal.is_file():
        return REFUSED, ["no seal: the run did not end"]
    doc = json.loads(seal.read_text(encoding="utf-8"))
    bad = [
        n
        for n, want in doc["files"].items()
        if not (run / n).is_file() or sha(run / n) != want
    ]
    said.append("every file is the one its seal names" if not bad else f"not the files its seal names: {', '.join(bad)}")  # fmt: skip
    holds, n = chain_holds(run / "log.jsonl")
    tip = (
        json.loads((run / "log.jsonl").read_text().splitlines()[-1])["hash"]
        if n
        else GENESIS
    )
    log_ok = holds and n == doc["log_lines"] and tip == doc["log_tip"]
    said.append(
        f"the log holds, {n} lines"
        if log_ok
        else "the log does not hold, or is not the one sealed"
    )
    signer, sig_ok = doc.get("signer"), True
    if signer:
        body = {k: v for k, v in doc.items() if k != "sig"}
        sig_ok = ed25519 is not None and ed25519.check(bytes.fromhex(signer), canon(body), bytes.fromhex(doc.get("sig", "")))  # fmt: skip
        said.append(
            "the seal's signature holds"
            if sig_ok
            else "the seal's signature does not hold"
        )
    else:
        said.append("the seal is not signed")
    if not bad and log_ok and sig_ok:
        if ring is None:
            return ALIVE, said
        if signer in ring:
            return ALIVE, [*said, f"its signer is enrolled: {ring[signer]}"]
        return ESCALATE, [*said, "its signer is not one this ring has enrolled"]
    return REFUSED, said


def args_of(argv: list[str]) -> dict:
    if not argv or argv[0] not in (*MODES, "verify"):
        raise Refuse(USAGE)
    opts: dict = {"mode": argv[0], "memory": [], "toy": False}
    it = iter(argv[1:])
    for a in it:
        if a in ("--plan", "--starts", "--to", "--repo", "--machine", "--round", "--ring", "--id",
                 "--budget", "--canary", "--one-in", "--run", "--from"):  # fmt: skip
            key = a[2:].replace("-", "_")
            if key in opts:
                raise Refuse(USAGE)
            opts[key] = next(it, "")
        elif a == "--memory":
            opts["memory"].append(next(it, ""))
        elif a == "--toy":
            opts["toy"] = True
        else:
            raise Refuse(USAGE)
    if opts["mode"] == "verify":
        if not opts.get("run"):
            raise Refuse(USAGE)
        return opts
    if (
        not all(opts.get(k) for k in ("plan", "starts", "to"))
        or bool(opts.get("repo")) == opts["toy"]
    ):
        raise Refuse(USAGE)
    if opts["mode"] == "shared":
        if not (opts.get("machine", "").isdigit() and opts.get("round", "").isdigit()):
            raise Refuse(USAGE)
        opts["machine"], opts["round"] = int(opts["machine"]), int(opts["round"])
    if opts["mode"] == "check" and not opts["memory"]:
        raise Refuse("refused: a check needs a memory to check")
    return opts


def main(argv: list[str]) -> int:
    run = None
    try:
        opts = args_of(argv)
        if opts["mode"] == "verify":
            code, said = verify(Path(opts["run"]), ring_of(Path(opts["ring"]) if opts.get("ring") else None))  # fmt: skip
            print("\n".join(said))
            return code
        run = Run(opts)
        return run.go()
    except Refuse as why:
        if run is not None:
            run.log.say("refused", why=str(why))
        text = str(why)
        print(
            text if text == USAGE or text.startswith("refused") else f"refused: {text}",
            file=sys.stderr,
        )
        return REFUSED
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as why:
        print(f"refused: {why!r}", file=sys.stderr)
        return REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
