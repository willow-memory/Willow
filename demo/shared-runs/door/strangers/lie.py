"""lie.py: a sealed folder made to lie, and sealed again by its own signer: one kept state changed, one halt that is no halt.

    python demo/shared-runs/door/strangers/lie.py --run OUT --plan PLAN --starts STARTS
        --machine K --id IDFILE --to FILE

OUT is a folder machine.py left for machine K's first round. Two things
in its memory are changed, each chosen so that the next round would
lean on it:

    a state   the kept state that the longest later job of one of its
              trajectories would go on from: its first byte turned over
    a halt    on another of its trajectories, one that does not halt: a
              halt written at the last kept state before its longest
              later job

Then the seal is made again over the changed files and signed with
IDFILE, as a liar with its own key would. FILE, outside OUT, says what
was changed, for whoever judges. This is for a study of a door; it is
of use against nothing that does not already check.

Exit codes, the kernel's: 0 changed and sealed; 2 refused (a bad
command line, a folder with no seal, no state or no trajectory to lie
about).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for place in (HERE.parent, HERE.parents[1] / "study", HERE):
    sys.path.insert(0, str(place))
import machine  # noqa: E402
import runner  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]


def lie(out: Path, plan: dict, starts: dict, k: int, seed: bytes) -> dict:
    doc = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    said = {"power": doc.get("power")}
    rows = [
        json.loads(x)
        for x in (out / "memory.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    kept: dict[str, list[int]] = {}
    for row in rows:
        if "step" in row:
            kept.setdefault(row["trajectory"], []).append(row["step"])
    halts = {row["trajectory"] for row in rows if "halt" in row}
    later: dict[str, int] = {}
    for r in range(1, plan["rounds"]):
        for _, name, steps in sweep.mine(plan, k, r):
            later[name] = max(later.get(name, 0), steps)
    # the trajectories it could lie about: its own, not halting, with a later job past a kept state
    could = []
    for name, longest in sorted(later.items(), key=lambda x: (-x[1], x[0])):
        tid = runner.identity(starts[name], said)
        before = [s for s in kept.get(tid, []) if s < longest]
        if tid not in halts and before:
            could.append((name, tid, max(before)))
    if len(could) < 2:
        raise machine.Refuse("no two trajectories here to lie about")
    (halt_name, halt_tid, halt_at), (state_name, state_tid, state_at) = (
        could[0],
        could[1],
    )
    for row in rows:
        if row.get("trajectory") == state_tid and row.get("step") == state_at:
            first = int(row["state"][:2], 16) ^ 0xFF
            row["state"] = f"{first:02x}" + row["state"][2:]
    rows.append({"trajectory": halt_tid, "halt": halt_at})
    (out / "memory.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    )
    doc["files"] = {name: machine.sha(out / name) for name in machine.FILES}
    doc.pop("sig", None)
    doc["signer"] = machine.ed25519.public(seed).hex()
    doc["sig"] = machine.ed25519.sign(seed, machine.canon(doc)).hex()
    (out / "manifest.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return {"state": [state_name, state_at], "halt": [halt_name, halt_at]}


def main(argv: list[str]) -> int:
    opts: dict = {}
    it = iter(argv)
    for a in it:
        if (
            a in ("--run", "--plan", "--starts", "--machine", "--id", "--to")
            and a[2:] not in opts
        ):
            opts[a[2:]] = next(it, "")
        else:
            opts = {}
            break
    if len(opts) != 6 or not opts["machine"].isdigit():
        print(USAGE, file=sys.stderr)
        return 2
    try:
        plan = sweep.load(Path(opts["plan"]))
        starts = json.loads(Path(opts["starts"]).read_text(encoding="utf-8"))
        told = lie(
            Path(opts["run"]),
            plan,
            starts,
            int(opts["machine"]),
            machine.read_id(Path(opts["id"])),
        )
    except (OSError, ValueError, KeyError, machine.Refuse) as why:
        print(f"refused: {why}", file=sys.stderr)
        return 2
    Path(opts["to"]).write_text(json.dumps(told, sort_keys=True) + "\n")
    print(json.dumps(told, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
