"""session.py: a session at the table played by code, as far as it goes without the person. Python 3.9+.

    python demo/game-box/session.py --table DIR [--world NAME] [--now TS]
    python demo/game-box/session.py --table DIR [--world NAME] offer CHARACTER "FACT"
    python demo/game-box/session.py --table DIR canon

The game master's bookkeeping, done by code: every action beat is rolled for
the character whose turn it is, leaning into the approach the beat suggests,
and every decision is handed in for the seal. Then it stops. Only whoever
holds the key moves a decision, with the kernel's own `seal` or `decline`;
run this again after and it settles their answer and plays on to the next.
A story played to its end prints what the table made true: each ruling,
sealed or declined, and the line each roll gave.

A roll can turn the story: a beat with a `when` is played only if the beat
it names came out its way, so a missed riddle leads somewhere a solved one
doesn't. The rulings put to the person are the ones the story reached.

`offer` is a player bringing something to the table on the night, as their
character: "a guest walks in". It is handed in for the seal, and the story
goes on while it waits. Once the GM seals or declines it, the next run
writes their answer down before it plays on, and a sealed offer is canon.

`canon` is the table's memory: every ruling sealed on this record whose seal
still holds, in the order they were sealed, and every one declined. It reads
only seals, never the worlds, so what it says is what the person made true.

NAME is a world in DIR/worlds (lantern-fair unless said). The story is
opened if it isn't yet. This never seals, declines or reads the key, and
writes only through game-master, which writes through dice and the kernel.

Exit codes, the kernel's: 0 the story is played to its end; 42 a decision
waits on the seal; 2 refused.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GM_DIR = ROOT / "adapters" / "stdlib" / "game-master"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GM_DIR))
import game_master as gm  # noqa: E402
import kernel  # noqa: E402

GM = GM_DIR / "game_master.py"


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def step(
    box: Path, world_file: Path, now: str, *argv: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GM), "--box", str(box), *argv, "--world", str(world_file), "--now", now],
        capture_output=True, text=True,
    )  # fmt: skip


def recap(world: dict, game: dict) -> list[str]:
    """What the table made true, beat by beat: each roll's line, each ruling."""
    beats = {(sc["id"], b["id"]): b for sc, b in gm.flat(world)}
    out = []
    for row in game["beats"]:
        b = beats[(row["scene"], row["beat"])]
        if row["beat_kind"] == "action":
            out.append(
                f"  {row['scene']}::{row['beat']}  {row['band']:<6} {b['outcomes'][row['band']]}"
            )
        else:
            fact = b["proposes"]["fact"]
            out.append(f"  {row['scene']}::{row['beat']}  {row['verdict']:<6} {fact}")
    return out


def canon(box: Path, worlds: Path) -> int:
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    titles = {}
    for f in sorted(worlds.glob("*.json")):
        try:
            w = gm.load_world(f)
        except gm.WorldError:
            continue
        titles[w["id"]] = w["title"]
    true, no = [], []
    for g in gm.games(rows):
        where = titles.get(g["open"].get("world"), g["open"].get("world"))
        said = [(a, a["fact"]) for a in g["asks"]]
        said += [(o, f"{o['fact']}  [offered by {o['by']}]") for o in g["offers"]]
        for a, fact in said:
            what, got = gm.ruling(box, rows, a["subject"])
            if what == "sealed":
                true.append(
                    (got["n"], f"  {fact}   ({where}, sealed at row {got['n']})")
                )
            elif what == "declined":
                no.append(
                    (
                        got["n"],
                        f"  not: {fact}   ({where}, declined at row {got['n']})",
                    )
                )
    if not true and not no:
        print("nothing is canon at this table yet: nothing has been sealed")
        return kernel.ESCALATE
    print("what this table holds true:")
    print("\n".join(line for _, line in sorted(true)) or "  nothing sealed yet")
    if no:
        print("what it said no to:")
        print("\n".join(line for _, line in sorted(no)))
    return kernel.ALIVE


def answered(box: Path, rows: list[dict], game: dict) -> bool:
    """Whether the GM has sealed or declined an offer not yet written down."""
    return any(gm.ruling(box, rows, o["subject"])[0] in ("sealed", "declined") for o in gm.unheard(game))  # fmt: skip


def offer(box: Path, world_file: Path, now: str, who: str, fact: str) -> int:
    done = step(box, world_file, now, "offer", who, fact)
    print((done.stdout or done.stderr).rstrip(), file=sys.stdout if done.stdout else sys.stderr)  # fmt: skip
    return done.returncode


def play(box: Path, world_file: Path, now: str) -> int:
    try:
        world = gm.load_world(world_file)
    except gm.WorldError as e:
        return fail(str(e))
    rows, game, err = gm.current(box, world)
    if err and "open first" in err:
        opened = step(box, world_file, now, "open")
        if opened.returncode == kernel.REFUSED:
            return fail(opened.stderr.strip())
        print(opened.stdout.rstrip())
        rows, game, err = gm.current(box, world)
    if err:
        return fail(err)
    if answered(box, rows, game):  # the GM answered an offer: write it down first
        heard = step(box, world_file, now, "settle")
        if heard.returncode == kernel.REFUSED:
            return fail(heard.stderr.strip())
        print(heard.stdout.rstrip())
        rows, game, err = gm.current(box, world)
    while not gm.finished(game, world):
        sc, b, char = gm.now_in(world, game)
        if b["kind"] == "action":
            done = step(box, world_file, now, "act", b["suggests"])
        else:
            asked = [
                a
                for a in game["asks"]
                if (a["scene"], a["beat"]) == (sc["id"], b["id"])
            ]
            done = step(box, world_file, now, "settle" if asked else "ask")
        if done.returncode == kernel.REFUSED:
            return fail(f"{sc['id']}::{b['id']}: {done.stderr.strip()}")
        print(done.stdout.rstrip())
        if done.returncode == kernel.ESCALATE:
            return kernel.ESCALATE
        rows, game, err = gm.current(box, world)
        if err:
            return fail(err)
    print(f"\n{world['title']}, played to its end: {gm.tally(game)}")
    print("\n".join(recap(world, game)))
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--table", "--world", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--table") or not (
        args in ([], ["canon"]) or (len(args) == 3 and args[0] == "offer")
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    table = Path(opts["--table"])
    box = table / "record"
    world_file = table / "worlds" / f"{opts.get('--world') or 'lantern-fair'}.json"
    if not (box / "kernel.json").exists():
        return fail(f"{table} isn't a table laid by open_table.py")
    if args == ["canon"]:
        return canon(box, table / "worlds")
    if not world_file.exists():
        return fail(f"no world {world_file.stem!r} in {world_file.parent}")
    if args:
        return offer(
            box, world_file, opts.get("--now") or kernel.now(), args[1], args[2]
        )
    return play(box, world_file, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
