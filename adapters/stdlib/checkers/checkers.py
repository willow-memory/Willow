"""checkers.py: checkers (English draughts) played on the record, the table's ruler sealing a draw. Python 3.9+.

    python adapters/stdlib/checkers/checkers.py --box DIR new
    python adapters/stdlib/checkers/checkers.py --box DIR show
    python adapters/stdlib/checkers/checkers.py --box DIR move 11-15
    python adapters/stdlib/checkers/checkers.py --box DIR resign
    python adapters/stdlib/checkers/checkers.py --box DIR offer
    python adapters/stdlib/checkers/checkers.py --box DIR settle
    python adapters/stdlib/checkers/checkers.py --box DIR check

The code knows the rules, and only the rules: a move it refuses is not a move,
and a side with no piece or no move left has lost. What the rules leave to the
people at the table, a draw, is theirs: `offer` hands "this game is a draw" in
through the kernel's own `bite` and `propose` and stops, and only the seal of
whoever holds the box's key ends the game drawn. This never calls a draw
itself, at any count of moves.

The squares are numbered 1 to 32 as checkers notation numbers them: black on
1 to 12 moves first, down the board, white on 21 to 32 moves up. A move is
`11-15`; a jump is `15x24`, and a jump of several pieces names each landing,
`15x24x31`, or just where it starts and ends when only one jump does that.
Jumping is a must, a man jumps forward only, and a man crowned on the far
row ends its move there. A king (`B`, `W`) moves and jumps one square either
way.

Each move, a resignation, a draw handed in and its ruling, is one row
written through the kernel's own `append`. `check` plays every game on the
record again from its first row: every move must be one the rules allow, by
the side whose turn it was; every ending the one the board gives; and every
draw a seal that holds under the key. The first row that doesn't is named.

Exit codes, the kernel's: 0 done, or every game holds; 42 a draw waits on
the seal; 2 refused: a move the rules don't allow, a record that doesn't
verify, a game that doesn't hold.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
OPEN, MOVE, RESIGN = "checkers-open", "checkers-move", "checkers-resign"
ASK, RULING = "checkers-ask", "checkers-ruling"
KINDS = (OPEN, MOVE, RESIGN, ASK, RULING)
WHO = "checkers"
SIDES = ("black", "white")
NOTATION = re.compile(r"^([1-9][0-9]?)(?:(-)([1-9][0-9]?)|((?:x[1-9][0-9]?)+))$")


# ── the board ────────────────────────────────────────────────────────────────
def place(sq: int) -> tuple[int, int]:
    """Square 1 to 32 as (row, column): row 0 is black's back row."""
    r, i = divmod(sq - 1, 4)
    return r, 2 * i + (1 if r % 2 == 0 else 0)


def square(r: int, c: int) -> int | None:
    """The square number at (row, column), or None off the board or on a light square."""
    if not (0 <= r < 8 and 0 <= c < 8) or (r + c) % 2 == 0:
        return None
    return r * 4 + c // 2 + 1


def start() -> dict[int, str]:
    return {**{s: "b" for s in range(1, 13)}, **{s: "w" for s in range(21, 33)}}


def side_of(piece: str) -> str:
    return "black" if piece.lower() == "b" else "white"


def steps(piece: str) -> tuple[tuple[int, int], ...]:
    """The diagonals a piece may move along: a man forward only, a king both ways."""
    down, up = ((1, -1), (1, 1)), ((-1, -1), (-1, 1))
    if piece.isupper():
        return down + up
    return down if piece == "b" else up


def crowned(piece: str, sq: int) -> bool:
    """A man on the far row is crowned there."""
    row = place(sq)[0]
    return (piece == "b" and row == 7) or (piece == "w" and row == 0)


def jumps(board: dict, path: tuple, piece: str, taken: frozenset) -> list[tuple]:
    """Every whole jump from the end of `path`, as (path, taken, piece after).
    A piece is jumped once; a man crowned mid-jump stops there."""
    r, c = place(path[-1])
    out = []
    for dr, dc in steps(piece):
        over, land = square(r + dr, c + dc), square(r + 2 * dr, c + 2 * dc)
        if over is None or land is None or land in board or over in taken:
            continue
        if over not in board or side_of(board[over]) == side_of(piece):
            continue
        after, more = path + (land,), taken | {over}
        if crowned(piece, land):
            out.append((after, more, piece.upper()))
            continue
        cont = jumps(board, after, piece, more)
        out += cont or [(after, more, piece)]
    return out


def legal(board: dict, side: str) -> list[tuple]:
    """Every move `side` may make, as (path, taken, piece after). A jump, if there
    is one, is a must."""
    mine = sorted(s for s, p in board.items() if side_of(p) == side)
    caps = []
    for s in mine:
        piece = board[s]
        rest = {
            k: v for k, v in board.items() if k != s
        }  # the square it leaves is empty
        caps += jumps(rest, (s,), piece, frozenset())
    if caps:
        return caps
    simple = []
    for s in mine:
        piece, (r, c) = board[s], place(s)
        for dr, dc in steps(piece):
            to = square(r + dr, c + dc)
            if to is not None and to not in board:
                simple.append(
                    (
                        (s, to),
                        frozenset(),
                        piece.upper() if crowned(piece, to) else piece,
                    )
                )
    return simple


def written(move: tuple) -> str:
    path, taken, _ = move
    return "x".join(map(str, path)) if taken else f"{path[0]}-{path[1]}"


def apply(board: dict, move: tuple) -> dict:
    path, taken, piece = move
    out = {k: v for k, v in board.items() if k != path[0] and k not in taken}
    out[path[-1]] = piece
    return out


def find(board: dict, side: str, text: str) -> tuple:
    """The one legal move `text` names, or ValueError saying which moves there are."""
    m = NOTATION.match(text.strip())
    allowed = legal(board, side)
    names = ", ".join(written(mv) for mv in allowed) or "none"
    if not m:
        raise ValueError(f"{text!r} isn't a move: write 11-15, 15x24 or 15x24x31")
    nums = [int(m.group(1))] + (
        [int(m.group(3))] if m.group(2) else [int(x) for x in m.group(4)[1:].split("x")]
    )
    if any(not 1 <= n <= 32 for n in nums):
        raise ValueError(f"{text!r}: the squares are 1 to 32")
    is_jump = not m.group(2)
    hits = [mv for mv in allowed if bool(mv[1]) == is_jump and list(mv[0]) == nums]
    if not hits and is_jump and len(nums) == 2:  # start and end only
        hits = [mv for mv in allowed if mv[1] and (mv[0][0], mv[0][-1]) == tuple(nums)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise ValueError(f"{text} could be {', '.join(written(h) for h in hits)}: name each landing")  # fmt: skip
    if allowed and allowed[0][1] and not is_jump:
        raise ValueError(f"{text}: a jump is a must; {side} may play {names}")
    raise ValueError(f"{text} isn't a move {side} may make; {side} may play {names}")


def ending(board: dict, to_move: str) -> str:
    """'on', or who won: a side with no piece or no move left has lost."""
    if not legal(board, to_move):
        return f"{SIDES[1 - SIDES.index(to_move)]} won"
    return "on"


def picture(board: dict) -> str:
    lines = []
    for r in range(8):
        cells = []
        for c in range(8):
            s = square(r, c)
            cells.append(" " if s is None else board.get(s, "."))
        lines.append(" ".join(cells) + f"   {r * 4 + 1:>2}-{r * 4 + 4}")
    return "\n".join(lines)


# ── what the record says ─────────────────────────────────────────────────────
def games(rows: list[dict]) -> list[dict]:
    """Each game: its open row, then its rows in the order written."""
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def state(game: dict) -> dict:
    """The board, whose turn, how many moves, how it stands, and a draw waiting."""
    board, ply, result, waiting = start(), 0, "on", None
    for r in game["rows"]:
        if r["kind"] == MOVE:
            board = apply(board, find(board, SIDES[ply % 2], r["move"]))
            ply += 1
            result = ending(board, SIDES[ply % 2])
        elif r["kind"] == RESIGN:
            result = f"{SIDES[1 - SIDES.index(r['side'])]} won"
        elif r["kind"] == ASK:
            waiting = r
        elif r["kind"] == RULING:
            waiting = None
            if r["verdict"] == "sealed":
                result = "draw"
    return {"board": board, "ply": ply, "to_move": SIDES[ply % 2], "result": result,
            "waiting": waiting}  # fmt: skip


def draw_proposal(game_n: int, ply: int) -> dict:
    """What `offer` hands in, the same every time for this game and move."""
    return {"path": f"checkers/{game_n}/draw-after-{ply}.txt",
            "data": f"The game of checkers opened at row {game_n} is a draw after {ply} moves.",
            "cites": [],
            "claim": f"the players at the table offer a draw in the game opened at row {game_n}, after {ply} moves"}  # fmt: skip


def ruling(box: Path, rows: list[dict], subj: str) -> tuple[str, dict | str]:
    """('sealed' | 'declined', the person's row) while its proof holds;
    ('broken', why) for a seal whose proposal is not what was sealed;
    ('open', '') while nobody has said."""
    yes, no = kernel.sealed(box, rows).get(subj), kernel.declined(box, rows).get(subj)
    if yes and (not no or yes["n"] < no["n"]):
        why = kernel.standing(box, rows, subj, yes)[2]
        return ("broken", why) if why else ("sealed", yes)
    if no:
        return "declined", no
    return "open", ""


def current(rows: list[dict]) -> dict | None:
    """The latest game, or None if none was opened."""
    gs = games(rows)
    return gs[-1] if gs else None


def check(box: Path, rows: list[dict]) -> tuple[int, str | None]:
    """(how many games hold, why the first that doesn't fails, or None)."""
    held, opened = 0, set()
    for r in rows:
        if r["kind"] == OPEN:
            opened.add(r["n"])
        elif r["kind"] in KINDS and r.get("game") not in opened:
            return held, f"row {r['n']}: its game isn't a game opened before it"
    for g in games(rows):
        board, ply, result, waiting = start(), 0, "on", None
        n = g["open"]["n"]
        for r in g["rows"]:
            where = f"row {r['n']} (game {n})"
            if result != "on":
                return held, f"{where}: the game was already over ({result})"
            if r["kind"] in (MOVE, RESIGN) and waiting:
                return held, f"{where}: a draw waited on the seal; nothing is played until it's settled"  # fmt: skip
            if r["kind"] == MOVE:
                if r.get("side") != SIDES[ply % 2]:
                    return held, f"{where}: it was {SIDES[ply % 2]}'s turn"
                try:
                    mv = find(board, SIDES[ply % 2], str(r.get("move")))
                except ValueError as e:
                    return held, f"{where}: {e}"
                if written(mv) != r["move"]:
                    return held, f"{where}: {r['move']} isn't written as the move it is, {written(mv)}"  # fmt: skip
                board, ply = apply(board, mv), ply + 1
                result = ending(board, SIDES[ply % 2])
                if r.get("result") != result:
                    return held, f"{where}: the board says {result}, the row says {r.get('result')}"  # fmt: skip
            elif r["kind"] == RESIGN:
                if r.get("side") != SIDES[ply % 2]:
                    return (
                        held,
                        f"{where}: only the side to move, {SIDES[ply % 2]}, resigns",
                    )
                result = f"{SIDES[1 - ply % 2]} won"
                if r.get("result") != result:
                    return held, f"{where}: a resignation by {r['side']} is {result}"
            elif r["kind"] == ASK:
                if waiting:
                    return held, f"{where}: a draw was already waiting"
                subj = kernel.subject_of(draw_proposal(n, ply))
                if r.get("subject") != subj or r.get("ply") != ply:
                    return held, f"{where}: it isn't the draw this game handed in after {ply} moves"  # fmt: skip
                if not any(p["kind"] == "proposal" and p.get("subject") == subj and p.get("verdict") == "pass"
                           for p in rows[: r["n"]]):  # fmt: skip
                    return held, f"{where}: the draw never passed the kernel's door"
                waiting = r
            elif r["kind"] == RULING:
                if not waiting or r.get("subject") != waiting["subject"]:
                    return held, f"{where}: a ruling on no draw this game handed in"
                what, got = ruling(box, rows[: r["n"]], waiting["subject"])
                if what in ("open", "broken"):
                    why = "nobody sealed or declined it" if what == "open" else f"its seal is broken: {got}"  # fmt: skip
                    return held, f"{where}: a ruling, but {why}"
                if r.get("verdict") != what or r.get("ruling_row") != got["n"]:
                    return (
                        held,
                        f"{where}: the person's answer is {what} at row {got['n']}",
                    )
                waiting = None
                if what == "sealed":
                    result = "draw"
        held += 1
    return held, None


# ── the commands ─────────────────────────────────────────────────────────────
def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def on_now(box: Path) -> tuple[list[dict], dict | None, dict | None, str | None]:
    """(rows, the game, its state, why not) for the game being played."""
    rows, _ = kernel.read(box / "record.jsonl")
    g = current(rows)
    if g is None:
        return rows, None, None, "no game is open: start one with new"
    st = state(g)
    if st["result"] != "on":
        return rows, g, st, f"the game is over ({st['result']}): start another with new"
    return rows, g, st, None


def cmd_new(box: Path, ts: str) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    g = current(rows)
    if g is not None and state(g)["result"] == "on":
        return fail(f"the game opened at row {g['open']['n']} isn't over; play it, resign, or offer a draw")  # fmt: skip
    row = kernel.append(box, ts, OPEN, who=WHO, first="black")
    print(picture(start()))
    print(f"\nnew game at row {row['n']}: black moves first")
    return kernel.ALIVE


def cmd_show(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    g = current(rows)
    if g is None:
        return fail("no game is open: start one with new")
    st = state(g)
    print(picture(st["board"]))
    print(f"\ngame at row {g['open']['n']}, after {st['ply']} moves: {st['result']}")
    if st["waiting"]:
        print(f"a draw waits on the seal: {st['waiting']['subject']}")
    elif st["result"] == "on":
        moves = ", ".join(written(m) for m in legal(st["board"], st["to_move"]))
        print(f"{st['to_move']} to move: {moves}")
    return kernel.ALIVE


def cmd_move(box: Path, text: str, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if st["waiting"]:
        return fail("a draw waits on the seal; settle it before anyone moves")
    try:
        mv = find(st["board"], st["to_move"], text)
    except ValueError as e:
        return fail(str(e))
    board = apply(st["board"], mv)
    result = ending(board, SIDES[(st["ply"] + 1) % 2])
    row = kernel.append(box, ts, MOVE, who=WHO, game=g["open"]["n"], ply=st["ply"],
                        side=st["to_move"], move=written(mv), result=result)  # fmt: skip
    print(picture(board))
    print(f"\n{st['to_move']} {written(mv)}: {result}   (row {row['n']})")
    return kernel.ALIVE


def cmd_resign(box: Path, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if st["waiting"]:
        return fail("a draw waits on the seal; settle it first")
    result = f"{SIDES[1 - st['ply'] % 2]} won"
    row = kernel.append(box, ts, RESIGN, who=WHO, game=g["open"]["n"], ply=st["ply"],
                        side=st["to_move"], result=result)  # fmt: skip
    print(f"{st['to_move']} resigns: {result}   (row {row['n']})")
    return kernel.ALIVE


def cmd_offer(box: Path, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if st["waiting"]:
        return fail(f"a draw already waits on the seal: {st['waiting']['subject']}")
    n, ply = g["open"]["n"], st["ply"]
    prop = draw_proposal(n, ply)
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "proposal.jsonl"
        f.write_text(json.dumps(prop) + "\n", encoding="utf-8")
        for argv in (["bite", f"checkers draw game {n} after {ply}"], ["propose", "--file", str(f)]):  # fmt: skip
            done = subprocess.run([sys.executable, str(KERNEL), argv[0], "--box", str(box), "--now", ts, *argv[1:]],
                                  capture_output=True, text=True)  # fmt: skip
            if done.returncode == kernel.REFUSED:
                return fail(f"the kernel's {argv[0]}: {done.stderr.strip()}")
    subj = kernel.subject_of(prop)
    if f"pass  {subj}" not in done.stdout:
        return fail("the kernel's door refused the draw: " + done.stdout.strip())
    row = kernel.append(box, ts, ASK, who=WHO, game=n, ply=ply, subject=subj)
    print(f"a draw after {ply} moves, handed in as {subj} (row {row['n']}); it waits on the table's ruler:")  # fmt: skip
    print(f"  python kernel.py seal --box {box} {subj}      (a draw)")
    print(f"  python kernel.py decline --box {box} {subj}   (play on)")
    return kernel.ESCALATE


def cmd_settle(box: Path, ts: str) -> int:
    rows, g, st, err = on_now(box)
    if err:
        return fail(err)
    if not st["waiting"]:
        return fail("no draw waits; offer one first")
    subj = st["waiting"]["subject"]
    what, got = ruling(box, rows, subj)
    if what == "broken":
        return fail(f"{subj} was sealed, but its proposal {got}; nothing moves")
    if what == "open":
        print(f"{subj} waits on the seal or the decline; nothing moves.")
        return kernel.ESCALATE
    row = kernel.append(box, ts, RULING, who=WHO, game=g["open"]["n"], subject=subj,
                        verdict=what, ruling_row=got["n"])  # fmt: skip
    said = "a draw" if what == "sealed" else "declined: play on"
    print(f"the ruling (row {got['n']}): {said}   (row {row['n']})")
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(box, rows)
    if why:
        return fail(f"{why} ({held} game{'s' if held != 1 else ''} before it held)")
    print(
        f"{held} game{'s' if held != 1 else ''} of checkers on the record; every one holds."
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
    bare = (
        verb in ("new", "show", "resign", "offer", "settle", "check") and len(args) == 1
    )
    if not opts.get("--box") or not (bare or (verb == "move" and len(args) == 2)):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return fail("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    ts = opts.get("--now") or kernel.now()
    if verb == "check":
        return cmd_check(box)
    held, why = check(box, rows)
    if why:
        return fail(f"the games on the record don't hold: {why}; check names it")
    if verb == "show":
        return cmd_show(box)
    if verb == "move":
        return cmd_move(box, args[1], ts)
    return {"new": cmd_new, "resign": cmd_resign, "offer": cmd_offer, "settle": cmd_settle}[verb](box, ts)  # fmt: skip


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
