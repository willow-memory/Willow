"""grown_notebooks.py: the sweep grown ten times as Kaggle notebooks: ten rounds, each place given only its own earlier rounds, a check a place.

    python demo/shared-runs/door/grown/grown_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets a folder for each notebook, in the order they are pushed:

    round-R-machine-K   round R of place K, given that place's earlier rounds
    check-K             every kept state and halt of place K's rounds, stepped again

A place's trajectories are its own in every round, so a round needs no
other place's work, and a check of one place needs only that place's
folders: no notebook is given more than the plan's rounds as inputs.

The notebook's script is the door's own (door/kaggle/door_notebooks.py):
it carries the plan, the starts, sweep.py, runner.py, machine.py and
ed25519.py, each held to its SHA-256, and calls machine.py. Each place
signs with an identity made here for this run, as does each check;
every notebook carries the ring. NAME is the Kaggle account; it goes
only into DIR, which is refused if it is inside this repository.

Exit codes, the kernel's: 0 made; 2 refused.
"""

from __future__ import annotations

import json
import re
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "kaggle"))
import door_notebooks as door  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2


def roles(plan: dict) -> list[dict]:
    out: list[dict] = []
    places = range(plan["machines"])
    for r in range(1, plan["rounds"] + 1):
        for k in places:
            before = [f"round-{q}-machine-{k}" for q in range(1, r)]
            out.append({"name": f"round-{r}-machine-{k}", "mode": "shared", "machine": k, "round": r,
                        "needs": before, "memory": before, "ends": [0], "place": f"place {k}"})  # fmt: skip
    for k in places:
        own = [f"round-{r}-machine-{k}" for r in range(1, plan["rounds"] + 1)]
        out.append({"name": f"check-{k}", "mode": "check", "needs": own, "memory": own, "ends": [0],
                    "place": f"check {k}"})  # fmt: skip
    return out


def slug(name: str) -> str:
    return f"shared-runs-grown-{name}"


def metadata(role: dict, user: str) -> dict:
    said = door.metadata(role, user)
    said.update(id=f"{user}/{slug(role['name'])}", title=slug(role["name"]),
                kernel_sources=[f"{user}/{slug(n)}" for n in role["needs"]])  # fmt: skip
    return said


def make(plan_path: Path, starts_path: Path, user: str, to: Path) -> list[str]:
    plan = door.sweep.load(plan_path)
    files = door.carried(
        plan_path.read_text(encoding="utf-8"), starts_path.read_text(encoding="utf-8")
    )
    if set(json.loads(files["starts.json"])) != {
        t["name"] for t in plan["trajectories"]
    }:
        raise ValueError("the starts are not this plan's")
    every = roles(plan)
    seeds = {
        p: secrets.token_bytes(32).hex() for p in sorted({r["place"] for r in every})
    }
    ring = {door.ed25519.public(bytes.fromhex(s)).hex(): p for p, s in seeds.items()}
    to.mkdir(parents=True)
    for role in every:
        folder = to / role["name"]
        folder.mkdir()
        (folder / "run.py").write_text(door.script(role, files, ring, seeds[role["place"]]), encoding="utf-8")  # fmt: skip
        (folder / "kernel-metadata.json").write_text(json.dumps(metadata(role, user), indent=1) + "\n")  # fmt: skip
    (to / "ring.json").write_text(json.dumps(ring, indent=1) + "\n")
    (to / "order.txt").write_text("\n".join(r["name"] for r in every) + "\n")
    return [r["name"] for r in every]


def main(argv: list[str]) -> int:
    opts: dict = {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--user", "--to", "--plan", "--starts") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        else:
            opts = {}
            break
    if argv[:1] != ["make"] or not opts.get("user") or not opts.get("to"):
        print(USAGE, file=sys.stderr)
        return REFUSED
    to = Path(opts["to"]).resolve()
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", opts["user"]):
            raise ValueError("NAME is not a Kaggle account's name")
        if to.is_relative_to(HERE.parents[3]):
            raise ValueError("DIR is inside the repository; an account's name and a run's keys are not kept here")  # fmt: skip
        if to.exists():
            raise ValueError(f"{to} is already there")
        made = make(Path(opts.get("plan") or HERE / "plan.json"),
                    Path(opts.get("starts") or HERE / "starts.json"), opts["user"], to)  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}, to push in the order of order.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
