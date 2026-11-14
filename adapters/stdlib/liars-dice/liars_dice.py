"""liars_dice.py: Liar's Dice played on the record, cups lifted, every cup dice's own row. Python 3.9+.

    python adapters/stdlib/liars-dice/liars_dice.py --box DIR new
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR show
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR bid QUANTITY FACE
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR call
    python adapters/stdlib/liars-dice/liars_dice.py --box DIR check

Four seats, north, east, south and west, five dice each. Each round every
seat still in throws its cup, and each throw is the dice add-on's own roll
row, seeded by the record's tip, so nobody picks the faces. The cups are
open: the throws are on the record as they fall.

A bid (`bid 3 5`) says there are at least that many of that face on the
whole table, ones wild except in a bid on ones. The round's opener bids;
then each seat in turn raises, more dice, or as many of a higher face, or
calls the last bid (`call`). On a call the face is counted: if the bid
holds, the caller loses a die; if not, the bidder does. A seat with none
left is out. The loser opens the next round, or the next seat still in;
the last seat with dice wins.

Each round, bid and call is a row through the kernel's own `append`.
`check` plays every game on the record again from its first row: every
cup dice's own throw, thrown straight before its round; every bid one the
rules allow by the seat whose turn it was; every call counted as the dice
give. The first that isn't is named.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "dice"))
import dice  # noqa: E402
import kernel  # noqa: E402

DICE = HERE.parent / "dice" / "dice.py"
OPEN, ROUND, BID, CALL = "liars-dice-open", "liars-dice-round", "liars-dice-bid", "liars-dice-call"  # fmt: skip
KINDS = (OPEN, ROUND, BID, CALL)
WHO = "liars-dice"
SEATS = ("north", "east", "south", "west")
EACH = 5


# ── the rules ────────────────────────────────────────────────────────────────
def counted(faces: list[int], face: int) -> int:
    """game-lab's count_face: ones wild, unless the bid is on ones."""
    return sum(1 for d in faces if d == face or (face != 1 and d == 1))


def above(bid: tuple | None, q: int, f: int, total: int) -> bool:
    """game-lab's bids_above: more dice, or as many of a higher face."""
    cq, cf = bid or (0, 0)
    return 1 <= q <= total and 1 <= f <= 6 and (q > cq or (q == cq and f > cf))


class Game:
    """A game of Liar's Dice as its rows say it went; ValueError at the first
    row the rules don't allow."""

    def __init__(self):
        self.dice, self.round, self.opener = [EACH] * 4, 0, 0
        self.cups, self.bid, self.bidder, self.turn = None, None, None, 0
        self.last, self.over = None, False

    def seats_in(self) -> list[int]:
        return [s for s in range(4) if self.dice[s] > 0]

    def total(self) -> int:
        return sum(self.dice)

    def after(self, seat: int) -> int:
        return next(
            (seat + k) % 4 for k in range(1, 5) if self.dice[(seat + k) % 4] > 0
        )

    def throws_wanted(self) -> list[tuple[int, str]]:
        """(seat, dice) for the cups the next round throws, in seat order."""
        return [(s, f"{self.dice[s]}d6") for s in self.seats_in()]

    def start(self, cups: dict[int, list[int]]) -> None:
        if self.over or self.cups is not None:
            raise ValueError(
                "the game is over" if self.over else "this round isn't called yet"
            )
        if sorted(cups) != self.seats_in() or any(
            len(cups[s]) != self.dice[s] for s in cups
        ):
            raise ValueError("a round throws every cup still in, each its own dice")
        self.round += 1
        self.cups, self.bid, self.bidder, self.turn = cups, None, None, self.opener

    def raise_(self, seat: int, q: int, f: int) -> None:
        self._seat(seat)
        if not above(self.bid, q, f, self.total()):
            low = "" if self.bid is None else f" over {self.bid[0]} {self.bid[1]}s"
            raise ValueError(
                f"{q} {f}s isn't a bid{low}: 1 to {self.total()} dice, faces 1 to 6"
            )
        self.bid, self.bidder, self.turn = (q, f), seat, self.after(seat)

    def call(self, seat: int) -> dict:
        self._seat(seat)
        if self.bid is None:
            raise ValueError("there is no bid to call: the opener bids")
        q, f = self.bid
        count = counted([d for s in self.seats_in() for d in self.cups[s]], f)
        loser = seat if count >= q else self.bidder
        self.dice[loser] -= 1
        self.last = {"bid": [q, f], "bidder": SEATS[self.bidder], "count": count, "loser": SEATS[loser]}  # fmt: skip
        self.cups = None
        if len(self.seats_in()) == 1:
            self.over = True
        else:
            self.opener = loser if self.dice[loser] else self.after(loser)
        return self.last

    def _seat(self, seat: int) -> None:
        if self.over:
            raise ValueError(f"the game is over ({self.result()})")
        if self.cups is None:
            raise ValueError("no round is thrown")
        if seat != self.turn:
            raise ValueError(f"it is {SEATS[self.turn]}'s turn")

    def result(self) -> str:
        return f"{SEATS[self.seats_in()[0]]} won" if self.over else "on"


def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def faces_of(row: dict) -> list[int]:
    return [abs(f) for group in row["faces"] for f in group]


def cups_of(rows: list[dict], r: dict, g: Game) -> dict[int, list[int]]:
    """The cups a round row names: dice's rows straight before it, one a seat."""
    want = g.throws_wanted()
    rolls = r.get("rolls")
    if rolls != list(range(r["n"] - len(want), r["n"])):
        raise ValueError(f"its cups aren't the {len(want)} throws straight before it")
    cups = {}
    for (seat, spec), n in zip(want, rolls):
        if rows[n].get("kind") != "roll" or rows[n].get("dice") != spec:
            raise ValueError(f"row {n} isn't a {spec} throw for {SEATS[seat]}")
        cups[seat] = faces_of(rows[n])
    if r.get("cups") != {SEATS[s]: f for s, f in cups.items()}:
        raise ValueError("its cups aren't what dice threw")
    return cups


def replay(rows: list[dict], game: dict) -> Game:
    """The game its rows make, or ValueError naming the first row that isn't."""
    g = Game()
    for r in game["rows"]:
        where = f"row {r['n']} (game {game['open']['n']})"
        try:
            if r["kind"] == ROUND:
                g.start(cups_of(rows, r, g))
                if r.get("round") != g.round or r.get("opener") != SEATS[g.opener]:
                    raise ValueError(
                        f"it is round {g.round}, opened by {SEATS[g.opener]}"
                    )
            elif r["kind"] == BID:
                q, f = r.get("quantity"), r.get("face")
                if not (type(q) is int and type(f) is int):
                    raise ValueError(
                        "a bid is a quantity and a face, both whole numbers"
                    )
                g.raise_(SEATS.index(r.get("seat")), q, f)
            else:
                said = g.call(SEATS.index(r.get("seat")))
                if (
                    any(r.get(k) != v for k, v in said.items())
                    or r.get("result") != g.result()
                ):
                    raise ValueError(f"the dice say {said['count']} counted, {said['loser']} loses a die, {g.result()}")  # fmt: skip
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"{where}: {e}") from None
    return g


def check(rows: list[dict]) -> tuple[int, str | None]:
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
        try:
            replay(rows, g)
        except ValueError as e:
            return held, str(e)
        held += 1
    return held, None


# ── the commands ─────────────────────────────────────────────────────────────
def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def throw_round(box: Path, game_n: int, g: Game, ts: str) -> dict:
    """Throw every cup still in, each dice's own row, then the round's row."""
    rolls = []
    for _, spec in g.throws_wanted():
        got = subprocess.run([sys.executable, str(DICE), "--box", str(box), "roll", spec, "--now", ts],
                             capture_output=True, text=True, check=False)  # fmt: skip
        rows, _ = kernel.read(box / "record.jsonl")
        if got.returncode != 0 or rows[-1].get("kind") != "roll":
            raise RuntimeError(
                "dice refused the throw: " + (got.stderr or got.stdout).strip()
            )
        rolls.append(rows[-1])
    cups = {SEATS[s]: faces_of(r) for (s, _), r in zip(g.throws_wanted(), rolls)}
    return kernel.append(box, ts, ROUND, who=WHO, game=game_n, round=g.round + 1, opener=SEATS[g.opener],
                         rolls=[r["n"] for r in rolls], cups=cups)  # fmt: skip


def current(box: Path):
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (replay(rows, gs[-1]) if gs else None)


def picture(g: Game) -> str:
    out = []
    for s in range(4):
        cup = " ".join(map(str, sorted(g.cups.get(s, [])))) if g.cups else ""
        out.append(f"{SEATS[s]:<6} {g.dice[s]} dice   {cup if g.dice[s] else 'out'}")
    if g.last:
        L = g.last
        out.append(f"\nlast call: {L['bidder']} bid {L['bid'][0]} {L['bid'][1]}s, {L['count']} counted, {L['loser']} lost a die")  # fmt: skip
    if g.over:
        out.append(f"\nthe game is over: {g.result()}")
    elif g.bid is None:
        out.append(
            f"\nround {g.round}, {g.total()} dice: {SEATS[g.turn]} opens with a bid"
        )
    else:
        out.append(f"\nround {g.round}, {g.total()} dice: {SEATS[g.bidder]} bid {g.bid[0]} {g.bid[1]}s; {SEATS[g.turn]} raises or calls")  # fmt: skip
    return "\n".join(out)


def cmd_new(box: Path, ts: str) -> int:
    rows, gm, g = current(box)
    if gm is not None and not g.over:
        return fail(f"the game opened at row {gm['open']['n']} isn't over")
    op = kernel.append(box, ts, OPEN, who=WHO, seats=list(SEATS), each=EACH)
    try:
        r = throw_round(box, op["n"], Game(), ts)
    except RuntimeError as e:
        return fail(str(e))
    print(
        f"new game at row {op['n']}, round 1 thrown at row {r['n']}: north opens with a bid"
    )
    return kernel.ALIVE


def cmd_bid(box: Path, q: str, f: str, ts: str) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    if not (q.isdigit() and f.isdigit()):
        return fail(f"{q} {f} isn't a bid: a quantity and a face, like bid 3 5")
    seat = g.turn
    try:
        g.raise_(seat, int(q), int(f))
    except ValueError as e:
        return fail(str(e))
    row = kernel.append(box, ts, BID, who=WHO, game=gm["open"]["n"], round=g.round, seat=SEATS[seat], quantity=int(q), face=int(f))  # fmt: skip
    print(
        f"{SEATS[seat]} bids {q} {f}s   (row {row['n']}); {SEATS[g.turn]} raises or calls"
    )
    return kernel.ALIVE


def cmd_call(box: Path, ts: str) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    seat = g.turn
    try:
        said = g.call(seat)
    except ValueError as e:
        return fail(str(e))
    row = kernel.append(box, ts, CALL, who=WHO, game=gm["open"]["n"], round=g.round, seat=SEATS[seat], result=g.result(), **said)  # fmt: skip
    q, f = said["bid"]
    print(f"{SEATS[seat]} calls {said['bidder']}'s {q} {f}s: {said['count']} counted, {said['loser']} loses a die   (row {row['n']})")  # fmt: skip
    if g.over:
        print(f"the game is over: {g.result()}")
        return kernel.ALIVE
    try:
        r = throw_round(box, gm["open"]["n"], g, ts)
    except RuntimeError as e:
        return fail(str(e))
    print(f"round {r['round']} thrown at row {r['n']}: {r['opener']} opens with a bid")
    return kernel.ALIVE


def cmd_show(box: Path) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    print(picture(g))
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    s = "s" if held != 1 else ""
    if why:
        return fail(f"{why} ({held} game{s} before it held)")
    print(f"{held} game{s} of liar's dice on the record; every one holds.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    shape = (verb in ("new", "show", "call", "check") and len(args) == 1) or (verb == "bid" and len(args) == 3)  # fmt: skip
    if not opts.get("--box") or not shape:
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
    _, why = check(rows)
    if why:
        return fail(f"the games on the record don't hold: {why}; check names it")
    if verb == "show":
        return cmd_show(box)
    ts = opts.get("--now") or kernel.now()
    if verb == "bid":
        return cmd_bid(box, args[1], args[2], ts)
    return {"new": cmd_new, "call": cmd_call}[verb](box, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
