"""nightstand.py: set heavy things down, pick up one bite. Python 3.9+.

    python adapters/stdlib/nightstand/nightstand.py --box DIR down [--weight W] [--now TS] WHAT...
    python adapters/stdlib/nightstand/nightstand.py --box DIR one
    python adapters/stdlib/nightstand/nightstand.py --box DIR pick [--now TS] ROW|one BITE...
    python adapters/stdlib/nightstand/nightstand.py --box DIR back [--now TS]
    python adapters/stdlib/nightstand/nightstand.py --box DIR done [--now TS]
    python adapters/stdlib/nightstand/nightstand.py --box DIR archive [--now TS] ROW
    python adapters/stdlib/nightstand/nightstand.py --box DIR show [--all]
    python adapters/stdlib/nightstand/nightstand.py --box DIR check

Three rules, each a mechanism and not a habit:

1. At most one thing is in hand. `pick` while another is held writes the
   put-down into the same row (`displaces`), so there is no instant with two.
2. You work the bite, not the thing. `pick` takes a bite, one line saying the
   one piece you owe the thing today, and refuses to write without one.
3. Nothing is deleted. There is no delete: a thing ends `done` or `archived`,
   and every step it took stays a row.

Every move is one `nightstand` row through the kernel's own append: `down`
(the thing's words and its weight, light, medium or heavy), `pick`, `back`,
`done`, `archive`. A thing's number is the row that set it down. `one` names
what to pick when you don't know: the lightest, then the oldest. The state is
never stored; `show` replays the rows. `check` replays them under the same
rules and names the first row that breaks one.

Exit codes, the kernel's: 0 done; 2 refused: nothing to do, a move the thing
can't make from where it is, a bite left out, a record that doesn't verify,
or a record that breaks a rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "nightstand"
WHO = "nightstand"
WEIGHTS = ("light", "medium", "heavy")
ACTS = ("down", "pick", "back", "done", "archive")
USAGE = __doc__.split("\n\n")[1]


class Broken(ValueError):
    """A move, or a row, that the three rules don't allow."""


def replay(rows: list[dict]) -> dict[int, dict]:
    """Every thing by number, its state rebuilt from the rows; Broken at the
    first row that breaks a rule. Rows of other kinds are not ours to read."""
    things: dict[int, dict] = {}
    held: int | None = None
    for r in rows:
        if r.get("kind") != KIND:
            continue
        n, act, t = r["n"], r.get("act"), r.get("thing")
        if act == "down":
            what, weight = r.get("what"), r.get("weight")
            if not isinstance(what, str) or not what.strip():
                raise Broken(f"row {n}: a thing set down with no words")
            if weight not in WEIGHTS:
                raise Broken(f"row {n}: weight {weight!r} isn't light, medium or heavy")
            things[n] = {"id": n, "what": what, "weight": weight, "status": "down",
                         "bite": None, "pickups": 0, "bites": []}  # fmt: skip
            continue
        if act not in ACTS:
            raise Broken(f"row {n}: {act!r} isn't a move")
        if t not in things:
            raise Broken(f"row {n}: {act} names row {t!r}, which is no thing")
        thing = things[t]
        if act == "pick":
            bite = r.get("bite")
            if not isinstance(bite, str) or not bite.strip():
                raise Broken(f"row {n}: picked up with no bite (rule 2)")
            if thing["status"] != "down":
                raise Broken(f"row {n}: thing {t} is {thing['status']}, not down")
            if r.get("displaces") != held:
                raise Broken(f"row {n}: puts down {r.get('displaces')!r} while {held!r} is in hand (rule 1)")  # fmt: skip
            if held is not None:
                things[held]["status"] = "down"
            held = t
            thing.update(status="in_hand", bite=bite, pickups=thing["pickups"] + 1)
            thing["bites"].append(bite)
        elif act in ("back", "done"):
            if thing["status"] != "in_hand":
                raise Broken(f"row {n}: {act} on thing {t}, which is {thing['status']}, not in hand")  # fmt: skip
            held = None
            thing["status"] = "down" if act == "back" else "done"
        else:  # archive
            if thing["status"] != "down":
                raise Broken(f"row {n}: archive on thing {t}, which is {thing['status']}, not down")  # fmt: skip
            thing["status"] = "archived"
    return things


def in_hand(things: dict[int, dict]) -> dict | None:
    held = [t for t in things.values() if t["status"] == "in_hand"]
    return held[0] if held else None


def waiting(things: dict[int, dict]) -> list[dict]:
    """The things down, in the order `one` would hand them."""
    rank = {w: i for i, w in enumerate(WEIGHTS)}
    down = [t for t in things.values() if t["status"] == "down"]
    return sorted(down, key=lambda t: (rank[t["weight"]], t["id"]))


def check(rows: list[dict]) -> tuple[int, str | None]:
    """(how many things the rows tell of, why the first bad row is bad or None)."""
    try:
        return len(replay(rows)), None
    except Broken as e:
        return 0, str(e)


def line(t: dict) -> str:
    return f"{t['id']:>4}  {t['weight']:<6}  {t['what']}"


def show(things: dict[int, dict], everything: bool) -> str:
    out, held = [], in_hand(things)
    if held:
        out += [f"in hand: {line(held).strip()}", f"    bite: {held['bite']}"]
    else:
        out.append("in hand: nothing")
    down = waiting(things)
    out.append(f"down ({len(down)}), the first is what `one` offers:")
    out += [f"  {line(t)}" for t in down]
    count = {s: sum(t["status"] == s for t in things.values()) for s in ("done", "archived")}  # fmt: skip
    out.append(f"done {count['done']}, archived {count['archived']}")
    if everything:
        for t in things.values():
            if t["status"] in count:
                out.append(f"  {line(t)}  [{t['status']}, picked up {t['pickups']}]")
    return "\n".join(out)


def parse(argv: list[str]) -> tuple[dict, list[str]] | None:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--weight"):
            opts[a] = next(it, "")
        elif a == "--all":
            opts[a] = True
        elif a.startswith("--"):
            return None
        else:
            args.append(a)
    return opts, args


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    got = parse(argv)
    if not got or not got[0].get("--box") or not got[1]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    opts, (cmd, *rest) = got
    shape = {"down": len(rest) >= 1, "pick": len(rest) >= 1, "archive": len(rest) == 1,
             "one": not rest, "back": not rest, "done": not rest, "show": not rest,
             "check": not rest}  # fmt: skip
    if not shape.get(cmd) or ("--weight" in opts and cmd != "down"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify:\n  " + "\n  ".join(breaks))
    count, why = check(rows)
    if why:
        return refuse(f"the record breaks a rule: {why}")
    if cmd == "check":
        print(f"{count} things on the record; every row keeps the three rules.")
        return kernel.ALIVE
    things = replay(rows)
    held, fields = in_hand(things), {}
    if cmd == "show":
        print(show(things, bool(opts.get("--all"))))
        return kernel.ALIVE
    if cmd == "one":
        down = waiting(things)
        if not down:
            return refuse("nothing is waiting on the nightstand")
        print(line(down[0]).strip())
        return kernel.ALIVE
    if cmd == "down":
        weight = opts.get("--weight", "medium")
        what = " ".join(rest).strip()
        if weight not in WEIGHTS:
            return refuse(f"weight {weight!r} isn't light, medium or heavy")
        if not what:
            return refuse("a thing needs words")
        fields = {"what": what, "weight": weight}
    elif cmd == "pick":
        down = waiting(things)
        if rest[0] == "one":
            if not down:
                return refuse("nothing is waiting on the nightstand")
            target = down[0]["id"]
        elif rest[0].isdigit():
            target = int(rest[0])
        else:
            return refuse(f"{rest[0]!r} is neither a row number nor `one`")
        bite = " ".join(rest[1:]).strip()
        if not bite:
            return refuse("name the one bite: you work the bite, not the thing")
        if target not in things or things[target]["status"] != "down":
            state = things[target]["status"] if target in things else "no thing"
            return refuse(f"row {target} is {state}, not down")
        fields = {"thing": target, "bite": bite, "displaces": held["id"] if held else None}  # fmt: skip
    elif cmd == "archive":
        target = int(rest[0]) if rest[0].isdigit() else -1
        if target not in things or things[target]["status"] != "down":
            state = things[target]["status"] if target in things else "no thing"
            return refuse(f"row {rest[0]} is {state}, not down")
        fields = {"thing": target}
    else:  # back, done
        if not held:
            return refuse(f"{cmd}: nothing is in hand")
        fields = {"thing": held["id"]}
    row = kernel.append(box, opts.get("--now") or kernel.now(), KIND, who=WHO, act=cmd, **fields)  # fmt: skip
    print(f"{cmd}: {fields.get('what') or fields.get('bite') or 'thing ' + str(fields['thing'])}   (row {row['n']})")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
