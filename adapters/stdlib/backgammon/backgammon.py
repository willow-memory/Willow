"""backgammon.py: backgammon played on the record, the dice thrown by dice. Python 3.9+.

    python adapters/stdlib/backgammon/backgammon.py --box DIR new
    python adapters/stdlib/backgammon/backgammon.py --box DIR show
    python adapters/stdlib/backgammon/backgammon.py --box DIR roll
    python adapters/stdlib/backgammon/backgammon.py --box DIR move "24/18 13/11"
    python adapters/stdlib/backgammon/backgammon.py --box DIR resign
    python adapters/stdlib/backgammon/backgammon.py --box DIR check

Two sides, white and black, fifteen checkers each, every point counted
from the mover's own side: 24 is the far end, 1 to 6 is home, `bar` is the
bar and `off` is borne off. `new` throws the opening roll, one die each
(again on a tie), and the higher plays both. After that, each turn is
`roll`, then `move`. Every throw is dice's own `roll` row, seeded by the
record's tip, so nobody picks the faces.

A move names every checker it moves, in order, as `from/to`: `24/18 13/11`,
`bar/22`, `6/off`, a hit marked or not (`13/7*`). The rules are the game's,
held whole: a doublet is played four times; a turn must use as many dice as
it can, and when only one of two can be used, the larger if it can; a
checker on the bar enters before any other moves; a point held by two or
more of the other side is closed; borne off only from home, by the exact
number or a higher one from the highest point. A side with no legal move
writes `move none`. Fifteen off wins: a single game, a gammon (the loser
bore none off) or a backgammon (none off and one still on the bar or in
the winner's home), worth 1, 2 or 3.

Each opening, throw, move and resignation is a row through the kernel's own
`append`. `check` plays every game on the record again from its first row:
every throw what its seed gives, every move one the rules allow with that
throw, every ending the one the board gives. The first that isn't is named.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "dice"))
import dice  # noqa: E402
import kernel  # noqa: E402

DICE = HERE.parent / "dice" / "dice.py"
OPEN, ROLL, MOVE, RESIGN = "backgammon-open", "backgammon-roll", "backgammon-move", "backgammon-resign"  # fmt: skip
KINDS = (OPEN, ROLL, MOVE, RESIGN)
WHO = "backgammon"
SIDES = ("white", "black")
START = {24: 2, 13: 5, 8: 3, 6: 5}
STEP = re.compile(r"^(bar|\d{1,2})/(off|\d{1,2})\*?$")
BAR, OFF = 25, 0


# ── the board ────────────────────────────────────────────────────────────────
def new_side() -> dict:
    return {"pts": dict(START), "bar": 0, "off": 0}


def other(side: str) -> str:
    return SIDES[1 - SIDES.index(side)]


def copy(state: dict) -> dict:
    return {s: {"pts": dict(v["pts"]), "bar": v["bar"], "off": v["off"]} for s, v in state.items()}  # fmt: skip


def home(me: dict) -> bool:
    return me["bar"] == 0 and all(c == 0 for p, c in me["pts"].items() if p > 6)


def closed(them: dict, to: int) -> bool:
    """Whether my point `to` is held by two or more of theirs (their 25-to)."""
    return them["pts"].get(25 - to, 0) >= 2


def single(state: dict, side: str, die: int) -> list[tuple[int, int]]:
    """Every (from, to) one die moves for `side` in this state."""
    me, them = state[side], state[other(side)]
    if me["bar"]:
        to = 25 - die
        return [] if closed(them, to) else [(BAR, to)]
    out = []
    high = max((p for p, c in me["pts"].items() if c), default=0)
    for p in sorted((p for p, c in me["pts"].items() if c), reverse=True):
        to = p - die
        if to >= 1:
            if not closed(them, to):
                out.append((p, to))
        elif home(me) and (to == 0 or p == high):
            out.append((p, OFF))
    return out


def play(state: dict, side: str, frm: int, to: int) -> dict:
    """The state after one checker moves: a hit sends theirs to the bar."""
    s = copy(state)
    me, them = s[side], s[other(side)]
    if frm == BAR:
        me["bar"] -= 1
    else:
        me["pts"][frm] -= 1
    if to == OFF:
        me["off"] += 1
    else:
        if them["pts"].get(25 - to, 0) == 1:
            them["pts"][25 - to] = 0
            them["bar"] += 1
        me["pts"][to] = me["pts"].get(to, 0) + 1
    for v in s.values():
        v["pts"] = {p: c for p, c in v["pts"].items() if c}
    return s


def turns(state: dict, side: str, faces: list[int]) -> list[tuple[tuple, tuple]]:
    """Every whole turn as (the moves, the dice they used, in order); only those
    using as many dice as can be used, and, of two dice of which only one can
    be used, the larger when it can be."""
    dice_ = faces * 2 if len(faces) == 2 and faces[0] == faces[1] else list(faces)
    found: list[tuple[tuple, tuple]] = []

    def go(st, left, moves, used):
        found.append((tuple(moves), tuple(used)))
        for i, d in enumerate(left):
            if d in left[:i]:
                continue  # the same face twice gives the same moves
            for frm, to in single(st, side, d):
                go(play(st, side, frm, to), left[:i] + left[i + 1 :], moves + [(frm, to)], used + [d])  # fmt: skip

    go(state, dice_, [], [])
    most = max(len(m) for m, _ in found)
    best = [(m, u) for m, u in found if len(m) == most]
    if most == 1 and len(set(dice_)) == 2:
        larger = [(m, u) for m, u in best if u[0] == max(dice_)]
        best = larger or best
    return best


def written(moves: tuple) -> str:
    def at(p):
        return "bar" if p == BAR else "off" if p == OFF else str(p)

    return " ".join(f"{at(f)}/{at(t)}" for f, t in moves) or "none"


def parse(text: str) -> tuple:
    if text.strip() == "none":
        return ()
    steps = []
    for word in text.split():
        m = STEP.match(word)
        if not m:
            raise ValueError(f"{word!r} isn't a move: write 24/18, bar/22 or 6/off")
        frm = BAR if m.group(1) == "bar" else int(m.group(1))
        to = OFF if m.group(2) == "off" else int(m.group(2))
        if not (1 <= frm <= 25 and 0 <= to <= 24 and to < frm):
            raise ValueError(
                f"{word!r}: a checker moves from a higher point to a lower one"
            )
        steps.append((frm, to))
    return tuple(steps)


def find(state: dict, side: str, faces: list[int], text: str) -> tuple:
    """The legal turn `text` writes, as (its moves, the state after), or
    ValueError saying what the dice allow."""
    want = parse(text)
    legal = turns(state, side, faces)
    for moves, _ in legal:
        if moves == want:
            s = state
            for frm, to in moves:
                s = play(s, side, frm, to)
            return moves, s
    # the same checkers in another order are the same turn
    for moves, _ in legal:
        if sorted(moves) == sorted(want):
            s = state
            for frm, to in moves:
                s = play(s, side, frm, to)
            return moves, s
    some = ", ".join(sorted({written(m) for m, _ in legal})[:6])
    raise ValueError(
        f"{text!r} isn't a turn {side} may play with {faces}; {side} may play: {some}"
    )


def ending(state: dict, mover: str) -> tuple[str, int]:
    """('on', 0), or who won and the points: 1, a gammon 2, a backgammon 3."""
    me, them = state[mover], state[other(mover)]
    if me["off"] < 15:
        return "on", 0
    if them["off"]:
        return f"{mover} won", 1
    behind = them["bar"] or any(c and p >= 19 for p, c in them["pts"].items())
    return (f"{mover} won a backgammon", 3) if behind else (f"{mover} won a gammon", 2)


def picture(state: dict) -> str:
    rows = []
    for side in SIDES:
        s = state[side]
        pts = " ".join(f"{p}:{c}" for p, c in sorted(s["pts"].items(), reverse=True))
        rows.append(
            f"{side:<6} {pts or '(none on the board)'}   bar {s['bar']}   off {s['off']}"
        )
    rows.append("each side's points are its own: 24 the far end, 1 to 6 home")
    return "\n".join(rows)


# ── what the record says ─────────────────────────────────────────────────────
def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def faces_of(rows: list[dict], n: int) -> list[int]:
    roll = rows[n]
    return [abs(f) for group in roll["faces"] for f in group]


def state_of(rows: list[dict], game: dict) -> dict:
    """The board, whose turn, the throw waiting to be played, and how it stands."""
    st = {"white": new_side(), "black": new_side()}
    o = game["open"]
    side, faces, result = o["first"], list(o["dice"]), "on"
    for r in game["rows"]:
        if r["kind"] == ROLL:
            faces = list(r["dice"])
        elif r["kind"] == MOVE:
            _, st = find(st, side, faces, r["move"])
            result, _ = ending(st, side)
            side, faces = other(side), None
        elif r["kind"] == RESIGN:
            result = f"{other(r['side'])} won"
    return {"board": st, "to_move": side, "faces": faces, "result": result}


def check(rows: list[dict]) -> tuple[int, str | None]:
    """(how many games hold, why the first that doesn't fails, or None)."""
    _, why = dice.check(rows)
    if why:
        return 0, why
    held, opened = 0, set()
    for r in rows:
        if r["kind"] == OPEN:
            opened.add(r["n"])
        elif r["kind"] in KINDS and r.get("game") not in opened:
            return held, f"row {r['n']}: its game isn't a game opened before it"
    for g in games(rows):
        o = g["open"]
        rolls = o.get("rolls") or []
        if not rolls or any(not isinstance(n, int) or n >= o["n"] or rows[n].get("dice") != "2d6" for n in rolls):  # fmt: skip
            return held, f"row {o['n']}: its opening isn't 2d6 throws before it"
        throws = [faces_of(rows, n) for n in rolls]
        if any(a != b for a, b in throws[:-1]) or throws[-1][0] == throws[-1][1]:
            return held, f"row {o['n']}: an opening throws again only on a tie, and ends on two different dice"  # fmt: skip
        w, b = throws[-1]
        first = "white" if w > b else "black"
        if o.get("first") != first or o.get("dice") != [w, b]:
            return (
                held,
                f"row {o['n']}: the opening throw says {first} plays {w} and {b}",
            )
        st = {"white": new_side(), "black": new_side()}
        side, faces, result = first, [w, b], "on"
        for r in g["rows"]:
            where = f"row {r['n']} (game {o['n']})"
            if result != "on":
                return held, f"{where}: the game was already over ({result})"
            if r["kind"] == ROLL:
                if faces is not None:
                    return (
                        held,
                        f"{where}: a throw while {side}'s last one waits to be played",
                    )
                n = r.get("roll_row")
                if not isinstance(n, int) or n != r["n"] - 1 or rows[n].get("kind") != "roll" or rows[n].get("dice") != "2d6":  # fmt: skip
                    return held, f"{where}: not straight after the 2d6 it names"
                if r.get("side") != side or list(r.get("dice", [])) != faces_of(
                    rows, n
                ):
                    return (
                        held,
                        f"{where}: not {side}'s throw, or not what the dice gave",
                    )
                faces = faces_of(rows, n)
            elif r["kind"] == MOVE:
                if faces is None:
                    return held, f"{where}: a move before {side} threw"
                if r.get("side") != side:
                    return held, f"{where}: it was {side}'s turn"
                try:
                    moves, st = find(st, side, faces, str(r.get("move")))
                except ValueError as e:
                    return held, f"{where}: {e}"
                if written(moves) != r["move"]:
                    return held, f"{where}: {r['move']} isn't written as the turn it is, {written(moves)}"  # fmt: skip
                result, points = ending(st, side)
                if r.get("result") != result or r.get("points", 0) != points:
                    return (
                        held,
                        f"{where}: the board says {result}, the row says {r.get('result')}",
                    )
                side, faces = other(side), None
            elif r["kind"] == RESIGN:
                if r.get("side") != side:
                    return held, f"{where}: only {side}, whose turn it is, resigns"
                result = f"{other(side)} won"
                if r.get("result") != result:
                    return held, f"{where}: a resignation by {side} is {result}"
        held += 1
    return held, None


# ── the commands ─────────────────────────────────────────────────────────────
def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def throw(box: Path, ts: str) -> tuple[dict | None, str]:
    """dice's own 2d6 roll row, seeded by the record's tip."""
    got = subprocess.run([sys.executable, str(DICE), "--box", str(box), "roll", "2d6", "--now", ts],
                         capture_output=True, text=True, check=False)  # fmt: skip
    rows, _ = kernel.read(box / "record.jsonl")
    if got.returncode != 0 or not rows or rows[-1].get("kind") != "roll":
        return None, "dice refused the throw: " + (got.stderr or got.stdout).strip()
    return rows[-1], ""


def current(box: Path) -> tuple[list[dict], dict | None, dict | None]:
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (state_of(rows, gs[-1]) if gs else None)


def cmd_new(box: Path, ts: str) -> int:
    rows, g, st = current(box)
    if g is not None and st["result"] == "on":
        return fail(
            f"the game opened at row {g['open']['n']} isn't over; play it or resign"
        )
    throws = []
    while True:
        roll, why = throw(box, ts)
        if roll is None:
            return fail(why)
        throws.append(roll["n"])
        w, b = (abs(f) for f in roll["faces"][0])
        print(
            f"opening throw: white {w}, black {b}"
            + ("   (a tie: again)" if w == b else "")
        )
        if w != b:
            break
    first = "white" if w > b else "black"
    row = kernel.append(box, ts, OPEN, who=WHO, rolls=throws, first=first, dice=[w, b])
    print(picture({"white": new_side(), "black": new_side()}))
    print(f"\nnew game at row {row['n']}: {first} plays {w} and {b} first")
    return kernel.ALIVE


def cmd_show(box: Path) -> int:
    rows, g, st = current(box)
    if g is None:
        return fail("no game is open: start one with new")
    print(picture(st["board"]))
    print(f"\ngame at row {g['open']['n']}: {st['result']}")
    if st["result"] == "on":
        if st["faces"] is None:
            print(f"{st['to_move']} to throw: roll")
        else:
            legal = turns(st["board"], st["to_move"], st["faces"])
            some = sorted({written(m) for m, _ in legal})
            print(f"{st['to_move']} to play {st['faces']}: {len(some)} way{'s' if len(some) != 1 else ''}, as {', '.join(some[:6])}")  # fmt: skip
    return kernel.ALIVE


def on_now(box: Path):
    rows, g, st = current(box)
    if g is None:
        return rows, g, st, "no game is open: start one with new"
    if st["result"] != "on":
        return rows, g, st, f"the game is over ({st['result']}): start another with new"
    return rows, g, st, None


def cmd_roll(box: Path, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if st["faces"] is not None:
        return fail(f"{st['to_move']} has {st['faces']} to play: move first")
    roll, why = throw(box, ts)
    if roll is None:
        return fail(why)
    faces = [abs(f) for f in roll["faces"][0]]
    row = kernel.append(box, ts, ROLL, who=WHO, game=g["open"]["n"], side=st["to_move"], roll_row=roll["n"], dice=faces)  # fmt: skip
    legal = turns(st["board"], st["to_move"], faces)
    print(
        f"{st['to_move']} throws {faces[0]} and {faces[1]}   (rows {roll['n']}, {row['n']})"
    )
    if not legal[0][0]:
        print("no legal move: write move none")
    return kernel.ALIVE


def cmd_move(box: Path, text: str, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if st["faces"] is None:
        return fail(f"{st['to_move']} hasn't thrown: roll first")
    try:
        moves, after = find(st["board"], st["to_move"], st["faces"], text)
    except ValueError as e:
        return fail(str(e))
    result, points = ending(after, st["to_move"])
    row = kernel.append(box, ts, MOVE, who=WHO, game=g["open"]["n"], side=st["to_move"],
                        move=written(moves), result=result, points=points)  # fmt: skip
    print(picture(after))
    print(f"\n{st['to_move']} {written(moves)}: {result}" + (f", {points} point{'s' if points != 1 else ''}" if points else "") + f"   (row {row['n']})")  # fmt: skip
    return kernel.ALIVE


def cmd_resign(box: Path, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    result = f"{other(st['to_move'])} won"
    row = kernel.append(box, ts, RESIGN, who=WHO, game=g["open"]["n"], side=st["to_move"], result=result)  # fmt: skip
    print(f"{st['to_move']} resigns: {result}   (row {row['n']})")
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    if why:
        return fail(f"{why} ({held} game{'s' if held != 1 else ''} before it held)")
    print(
        f"{held} game{'s' if held != 1 else ''} of backgammon on the record; every one holds."
    )
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    bare = verb in ("new", "show", "roll", "resign", "check") and len(args) == 1
    if not opts.get("--box") or not (bare or (verb == "move" and len(args) == 2)):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return fail("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    if verb == "check":
        return cmd_check(box)
    held, why = check(rows)
    if why:
        return fail(f"the games on the record don't hold: {why}; check names it")
    ts = opts.get("--now") or kernel.now()
    if verb == "show":
        return cmd_show(box)
    if verb == "move":
        return cmd_move(box, args[1], ts)
    return {"new": cmd_new, "roll": cmd_roll, "resign": cmd_resign}[verb](box, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
