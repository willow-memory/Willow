"""trusted_notebooks.py: the door met by a liar the ring trusts, as Kaggle notebooks: taken, then found, then held.

    python demo/shared-runs/door/trusted/trusted_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets a folder for each notebook, in the order they are pushed:

    round-1-machine-K          the first round, each place signing as itself;
                               every place is in the ring
    round-2-machine-K-before   the second round, by a taker the ring knows,
                               given its own place's first round
    check                      every kept state and halt of the five first
                               rounds, and of place 3's second, stepped again
    round-2-machine-3-after    place 3's second round again, given its first
                               round, the second round that went on from it,
                               and the check

Place 3 lies as it did among the strangers (strangers/lie.py: one kept
state changed, one halt that is no halt, sealed again with its own
key), but here its key is in the ring. So before anyone looks its
folder is taken, and wrong bytes go out. The question is what happens
after someone looks.

The notebook's script is the strangers run's own. Every identity is
made here, for this run and no other, and is nobody's key. NAME is the
Kaggle account; it goes only into DIR, which is refused if it is inside
this repository.

Exit codes, the kernel's: 0 made; 2 refused.
"""

from __future__ import annotations

import json
import re
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "strangers"))
import strangers_notebooks as base  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2
LIAR = 3


def roles(plan: dict) -> list[dict]:
    out: list[dict] = []
    places = range(plan["machines"])
    for k in places:
        out.append({"name": f"round-1-machine-{k}", "mode": "shared", "machine": k, "round": 1,
                    "needs": [], "memory": [], "ends": [0], "signs": f"place {k}", "lies": k == LIAR})  # fmt: skip
    for k in places:
        own = [f"round-1-machine-{k}"]
        out.append({"name": f"round-2-machine-{k}-before", "mode": "shared", "machine": k, "round": 2,
                    "needs": own, "memory": own, "ends": [0], "signs": f"taker {k}"})  # fmt: skip
    looked = [
        *(f"round-1-machine-{k}" for k in places),
        f"round-2-machine-{LIAR}-before",
    ]
    out.append({"name": "check", "mode": "check", "needs": looked, "memory": looked, "ends": [0],
                "signs": "checker"})  # fmt: skip
    given = [f"round-1-machine-{LIAR}", f"round-2-machine-{LIAR}-before", "check"]
    out.append({"name": f"round-2-machine-{LIAR}-after", "mode": "shared", "machine": LIAR, "round": 2,
                "needs": given, "memory": given, "ends": [42], "signs": f"taker {LIAR}"})  # fmt: skip
    return out


def slug(name: str) -> str:
    return f"shared-runs-trusted-{name}"


def make(plan_path: Path, starts_path: Path, user: str, to: Path) -> list[str]:
    plan = base.sweep.load(plan_path)
    files = {"plan.json": plan_path.read_text(encoding="utf-8"),
             "starts.json": starts_path.read_text(encoding="utf-8")}  # fmt: skip
    files.update(
        {n: (d / n).read_text(encoding="utf-8") for n, d in base.CARRIED.items()}
    )
    if set(json.loads(files["starts.json"])) != {
        t["name"] for t in plan["trajectories"]
    }:
        raise ValueError("the starts are not this plan's")
    seeds = {name: secrets.token_bytes(32).hex() for name in base.signers(plan)}
    ring = {base.ed25519.public(bytes.fromhex(s)).hex(): n for n, s in seeds.items()}
    every = roles(plan)
    to.mkdir(parents=True)
    for role in every:
        folder = to / role["name"]
        folder.mkdir()
        (folder / "run.py").write_text(base.script(role, files, ring, seeds[role["signs"]]), encoding="utf-8")  # fmt: skip
        said = base.metadata(role, user)
        said.update(id=f"{user}/{slug(role['name'])}", title=slug(role["name"]),
                    kernel_sources=[f"{user}/{slug(n)}" for n in role["needs"]])  # fmt: skip
        (folder / "kernel-metadata.json").write_text(json.dumps(said, indent=1) + "\n")
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
        made = make(Path(opts.get("plan") or base.STUDY / "plan.json"),
                    Path(opts.get("starts") or base.STUDY / "starts.json"), opts["user"], to)  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}, to push in the order of order.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
