"""unknown_notebooks.py: the grown sweep where nobody is known, as Kaggle notebooks: every round held, nothing gone on from but a round's own work.

    python demo/shared-runs/door/unknown/unknown_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets the same notebooks as the grown sweep's (door/grown): ten
rounds for each place, each given its own place's earlier rounds, and a
check a place. One thing differs. Every round signs with an identity
made for that round alone, and the ring every notebook carries holds
none of them: it holds one key, which signs nothing. So each round is
whole and signed, and its signer is nobody the door knows; a later
round holds every folder it is given and steps from what it kept
itself. Nobody checks before the end, so nobody is ever cleared.

That is the far end of what a door can cost: a memory that is kept and
never trusted. The checks at the end look at every folder all the same,
to see that what was held was in fact right.

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


def roles(plan: dict) -> list[dict]:
    """The grown sweep's notebooks; a round that is given anything ends 42,
    having held it."""
    out = []
    for role in grown.roles(plan):
        role = dict(role)
        if role["mode"] == "shared":
            role["place"] = role["name"]
            role["ends"] = [42] if role["needs"] else [0]
        out.append(role)
    return out


def slug(name: str) -> str:
    return f"shared-runs-unknown-{name}"


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
    seeds = {r["place"]: secrets.token_bytes(32).hex() for r in every}
    nobody = door.ed25519.public(secrets.token_bytes(32)).hex()
    ring = {nobody: "a key that signs nothing"}
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
