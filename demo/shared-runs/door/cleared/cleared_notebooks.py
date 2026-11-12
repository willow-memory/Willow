"""cleared_notebooks.py: the grown sweep with two places nobody enrolled and a check after every round that clears them, as Kaggle notebooks.

    python demo/shared-runs/door/cleared/cleared_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets a folder for each notebook, in the order they are pushed:

    round-R-machine-K   round R of place K, given that place's earlier rounds
                        and, at places 1 and 3, the clearing of the round before
    clear-R-K           after round R, for places 1 and 3: the states that
                        place has kept that no clearing has yet looked at,
                        stepped again by a checker the ring knows
    check-K             at the end, every kept state and halt of place K's
                        rounds, stepped again

Places 0, 2 and 4 sign with identities the ring holds. Places 1 and 3
sign every round with an identity made for that round alone, which the
ring does not hold. Each `clear` is carried on from the one before
(machine.py's `--from`), so it steps only what is new, and its seal
names every folder of that place looked at so far; the next round takes
them all on its word.

The middle of the door, then: between every signer enrolled
(door/grown) and nobody known (door/unknown). What it costs is the
clearings, and what they buy is everything the strangers remember.

The notebook's script is the door's own (door/kaggle/door_notebooks.py).
NAME is the Kaggle account; it goes only into DIR, which is refused if
it is inside this repository.

Exit codes, the kernel's: 0 made; 2 refused.
"""

from __future__ import annotations

import json
import re
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROWN = HERE.parent / "grown"
sys.path.insert(0, str(GROWN))
import grown_notebooks as grown  # noqa: E402

door = grown.door
USAGE = __doc__.split("\n\n")[1]
REFUSED = 2
STRANGERS = (1, 3)


def roles(plan: dict) -> list[dict]:
    out: list[dict] = []
    places, last = range(plan["machines"]), plan["rounds"]
    for r in range(1, last + 1):
        for k in places:
            before = [f"round-{q}-machine-{k}" for q in range(1, r)]
            cleared = [f"clear-{r - 1}-{k}"] if k in STRANGERS and r > 1 else []
            name = f"round-{r}-machine-{k}"
            out.append({"name": name, "mode": "shared", "machine": k, "round": r,
                        "needs": [*before, *cleared], "memory": [*before, *cleared], "ends": [0],
                        "place": name if k in STRANGERS else f"place {k}"})  # fmt: skip
        if r == last:
            break
        for k in STRANGERS:
            sofar = [f"round-{q}-machine-{k}" for q in range(1, r + 1)]
            role = {"name": f"clear-{r}-{k}", "mode": "check", "needs": list(sofar), "memory": sofar,
                    "ends": [0], "place": f"checker {k}"}  # fmt: skip
            if r > 1:
                role["from"] = f"clear-{r - 1}-{k}"
                role["needs"].append(role["from"])
            out.append(role)
    for k in places:
        own = [f"round-{r}-machine-{k}" for r in range(1, last + 1)]
        out.append({"name": f"check-{k}", "mode": "check", "needs": own, "memory": own, "ends": [0],
                    "place": f"check {k}"})  # fmt: skip
    return out


def slug(name: str) -> str:
    return f"shared-runs-cleared-{name}"


def enrolled(place: str) -> bool:
    return not place.startswith("round-")


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
    ring = {
        door.ed25519.public(bytes.fromhex(s)).hex(): p
        for p, s in seeds.items()
        if enrolled(p)
    }
    to.mkdir(parents=True)
    for role in every:
        folder = to / role["name"]
        folder.mkdir()
        (folder / "run.py").write_text(door.script(role, files, ring, seeds[role["place"]]), encoding="utf-8")  # fmt: skip
        said = door.metadata(role, user)
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
        made = make(Path(opts.get("plan") or GROWN / "plan.json"),
                    Path(opts.get("starts") or GROWN / "starts.json"), opts["user"], to)  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}, to push in the order of order.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
