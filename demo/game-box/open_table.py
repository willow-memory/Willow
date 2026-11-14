"""open_table.py: a game table set up from the box, with nothing sealed. Python 3.9+.

    python demo/game-box/open_table.py open  --table DIR --key FILE [--now TS]
    python demo/game-box/open_table.py check --table DIR

`open` lays a fresh table in DIR, which must not exist yet: the box's own
pile copied to DIR/pile (the house rules and the table's check), the
worlds to DIR/worlds, and a kernel record started over the pile at
DIR/record. The worlds are kept out of the pile: they are the game master's
script, and what the record reads is what the table may ask about. The kernel makes the key at
FILE, for whoever rules the table; FILE must not be inside DIR, so the key is
never part of what the record reads. Then each house rule is handed in for
the seal (the rules add-on) and the story is opened (game-master), and it
stops: everything it proposed waits on the person who holds the key.

`check` runs the table's own check page, DIR/pile/check.md, through the
stack add-on: every game on the record played again from its first row, and
which house rules are sealed. Then the kernel verifies the chain.

This never seals, declines or reads the key, and writes the record only
through the kernel and the add-ons.

Exit codes, the kernel's: 0 done; 42 something waits on the seal, or the
check page flagged a step; 2 refused.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

TABLE = HERE / "table"
STDLIB = ROOT / "adapters" / "stdlib"
RULES = STDLIB / "rules" / "rules.py"
GM = STDLIB / "game-master" / "game_master.py"
STACK = STDLIB / "stack" / "stack.py"
WORLDS = HERE / "worlds"
WORLD = "lantern-fair.json"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def inside(path: Path, folder: Path) -> bool:
    try:
        path.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return False


def cmd_open(table: Path, key: Path, now: str) -> int:
    if table.exists():
        return fail(
            f"{table} is already there: a table is laid fresh, in a folder of its own"
        )
    if inside(key, table):
        return fail("the key goes outside the table, so the record never reads it")
    pile, box = table / "pile", table / "record"
    table.mkdir(parents=True)
    shutil.copytree(TABLE, pile)
    shutil.copytree(WORLDS, table / "worlds")  # the script stays out of the pile
    steps = (
        (
            "the record",
            [
                str(ROOT / "kernel.py"),
                "init",
                "--box",
                str(box),
                "--pile",
                str(pile),
                "--key",
                str(key),
                "--now",
                now,
            ],
        ),  # fmt: skip
        (
            "the house rules",
            [
                str(RULES),
                "propose",
                "--box",
                str(box),
                "--now",
                now,
                str(pile / "house-rules.md"),
            ],
        ),  # fmt: skip
        (
            "the story",
            [
                str(GM),
                "--box",
                str(box),
                "open",
                "--world",
                str(table / "worlds" / WORLD),
                "--now",
                now,
            ],
        ),  # fmt: skip
    )
    for what, argv in steps:
        done = run(*argv)
        if done.returncode == kernel.REFUSED:
            return fail(f"{what}: {(done.stderr or done.stdout).strip()}")
        print(f"## {what}\n{done.stdout.rstrip()}\n")
    rows, _ = kernel.read(box / "record.jsonl")
    waiting = [r["subject"] for r in rows if r["kind"] == "proposal" and r.get("verdict") == "pass"]  # fmt: skip
    print(
        f"the table is laid at {table}: {len(waiting)} waiting on the seal, nothing sealed."
    )
    print(f"whoever holds {key} rules the table; seal or decline each with")
    print(f"  python kernel.py seal --box {box} proposal:<id>")
    return kernel.ESCALATE if waiting else kernel.ALIVE


def cmd_check(table: Path) -> int:
    box, page = table / "record", table / "pile" / "check.md"
    if not (box / "kernel.json").exists() or not page.exists():
        return fail(f"{table} isn't a table laid by open")
    done = run(str(STACK), "--box", str(box), "--stack", str(page))
    print(done.stdout.rstrip())
    if done.returncode == kernel.REFUSED:
        return fail(f"the check page: {done.stderr.strip()}")
    chain = run(str(ROOT / "kernel.py"), "verify", "--box", str(box))
    print(chain.stdout.rstrip())
    if chain.returncode != kernel.ALIVE:
        return fail(f"the chain: {(chain.stderr or chain.stdout).strip()}")
    return done.returncode


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--table", "--key", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--table") or args not in (["open"], ["check"]):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    table = Path(opts["--table"])
    if args == ["check"]:
        return cmd_check(table)
    if not opts.get("--key"):
        return fail(
            "open needs --key: where the kernel makes the key for whoever rules the table"
        )
    return cmd_open(table, Path(opts["--key"]), opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
