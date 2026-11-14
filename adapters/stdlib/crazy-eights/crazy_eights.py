"""crazy_eights.py: Crazy Eights played on the record, hands open, the deal seeded. Python 3.9+.

    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR new
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR show
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR play CARD [SUIT]
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR draw
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR pass
    python adapters/stdlib/crazy-eights/crazy_eights.py --box DIR check

Four seats, north, east, south and west. The deck is shuffled from willow's
seeded stream (sha256-stream v1), seeded by the record's tip: five cards to
each seat, one turned up to start the pile, the rest the stock. The hands
are open: every card, and the stock's order, is on the record from the deal.

On a turn the seat plays a card that matches the suit to follow or the top
card's rank; an 8 is wild, and names the suit to follow (`play 8H S`). A
seat with nothing it can play draws one card, and goes again; with nothing
to play and no stock, it passes. The first seat to play its last card
wins. Four passes in a row with no stock and the hand is stalled: nobody
wins.

Cards are written rank then suit: 2C, 10H (or TH), JD, QS, KC, AH. A suit
is C, D, H or S.

The deal, each card played, each draw and each pass is a row through the
kernel's own `append`. `check` plays every game on the record again from
its first row: every deal what its seed gives, every card one the rules
allow by the seat whose turn it was, every draw and pass one the seat had
to make, and every ending the one the cards give. The first that isn't is
named.

Exit codes, the kernel's: 0 done, or every game holds; 2 refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

DEAL, PLAY, DRAW, PASS = "crazy-eights-deal", "crazy-eights-play", "crazy-eights-draw", "crazy-eights-pass"  # fmt: skip
KINDS = (DEAL, PLAY, DRAW, PASS)
WHO = "crazy-eights"
GENERATOR = "sha256-stream/v1"
SEATS = ("north", "east", "south", "west")
SUITS = "CDHS"
RANKS = {"J": 11, "Q": 12, "K": 13, "A": 14, "T": 10}
HAND, STALL = 5, 4
CARD = re.compile(r"^(10|[2-9TJQKA])([CDHS])$")


class Stream:
    """willow-bot's onescript/stream.py Stream (see the dice add-on)."""

    def __init__(self, seed: bytes):
        self.seed, self.n = seed, 0

    def u32(self) -> int:
        d = hashlib.sha256(self.seed + self.n.to_bytes(8, "big")).digest()
        self.n += 1
        return int.from_bytes(d[:4], "big")

    def below(self, k: int) -> int:
        cap = (1 << 32) - (1 << 32) % k
        while (x := self.u32()) >= cap:
            pass
        return x % k

    def shuffled(self, items) -> list:
        out = list(items)
        for i in range(len(out) - 1, 0, -1):  # Fisher-Yates, drawn from the stream
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out


# ── the cards ────────────────────────────────────────────────────────────────
def deck() -> list[tuple[int, str]]:
    return [(r, s) for s in SUITS for r in range(2, 15)]


def name(card: tuple[int, str]) -> str:
    r, s = card
    return {11: "J", 12: "Q", 13: "K", 14: "A"}.get(r, str(r)) + s


def card_of(text: str) -> tuple[int, str]:
    m = CARD.match(str(text).strip().upper())
    if not m:
        raise ValueError(f"{text!r} isn't a card: write 2C, 10H, QS, AH")
    return RANKS.get(m.group(1)) or int(m.group(1)), m.group(2)


def dealt(seed: str) -> dict:
    """What `seed` deals: four hands of five, the card turned up, the stock
    in the order it is drawn (the last first, as game-lab draws)."""
    cards = Stream(seed.encode()).shuffled(deck())
    stock = cards[HAND * 4 :]
    return {"hands": [cards[i * HAND : (i + 1) * HAND] for i in range(4)], "top": stock[0], "stock": stock[1:]}  # fmt: skip


def legal(hand: list, top: tuple, suit: str) -> list:
    """The cards a seat may play: game-lab's is_legal, rule for rule."""
    return [c for c in hand if c[0] == 8 or c[1] == suit or c[0] == top[0]]


# ── a game, replayed ─────────────────────────────────────────────────────────
class Game:
    """A hand of Crazy Eights as its rows say it went; ValueError at the
    first row the rules don't allow."""

    def __init__(self, seed: str):
        d = dealt(seed)
        self.hands, self.top, self.stock = d["hands"], d["top"], d["stock"]
        self.suit, self.turn, self.passes = self.top[1], 0, 0
        self.winner, self.over = None, False

    def can_play(self) -> list:
        return legal(self.hands[self.turn], self.top, self.suit)

    def _seat(self, seat: int) -> None:
        if self.over:
            raise ValueError(f"the hand is over ({self.result()})")
        if seat != self.turn:
            raise ValueError(f"it is {SEATS[self.turn]}'s turn")

    def play(self, seat: int, card: tuple, call: str | None) -> None:
        self._seat(seat)
        if card not in self.hands[seat]:
            raise ValueError(f"{SEATS[seat]} doesn't hold {name(card)}")
        if card not in self.can_play():
            raise ValueError(f"{name(card)} doesn't follow {name(self.top)} with {self.suit} to follow")  # fmt: skip
        if card[0] == 8 and call not in tuple(SUITS):
            raise ValueError("an 8 names the suit to follow: C, D, H or S")
        if card[0] != 8 and call is not None:
            raise ValueError("only an 8 names a suit")
        self.hands[seat].remove(card)
        self.top, self.suit, self.passes = card, call if card[0] == 8 else card[1], 0
        if not self.hands[seat]:
            self.winner, self.over = seat, True
        else:
            self.turn = (seat + 1) % 4

    def draw(self, seat: int) -> tuple:
        self._seat(seat)
        if self.can_play():
            raise ValueError(f"{SEATS[seat]} can play, so doesn't draw: {' '.join(name(c) for c in self.can_play())}")  # fmt: skip
        if not self.stock:
            raise ValueError("the stock is empty: pass")
        card = self.stock.pop()
        self.hands[seat].append(card)
        return card

    def pass_(self, seat: int) -> None:
        self._seat(seat)
        if self.can_play() or self.stock:
            raise ValueError(f"{SEATS[seat]} " + ("can play" if self.can_play() else "draws first"))  # fmt: skip
        self.passes += 1
        self.turn = (seat + 1) % 4
        self.over = self.passes >= STALL

    def result(self) -> str:
        if not self.over:
            return "on"
        return f"{SEATS[self.winner]} won" if self.winner is not None else "stalled"


def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == DEAL:
            out[r["n"]] = {"deal": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def replay(rows: list[dict], game: dict) -> Game:
    """The hand its rows make, or ValueError naming the first row that isn't."""
    d = game["deal"]
    where = f"row {d['n']}"
    try:
        before = rows[d["n"] - 1]["hash"] if d["n"] else kernel.GENESIS
        if d.get("seed") != before:
            raise ValueError("its seed isn't the hash of the row before it")
        g = Game(d["seed"])
        want = dealt(d["seed"])
        shown = {"hands": [[name(c) for c in h] for h in want["hands"]], "top": name(want["top"]), "stock": [name(c) for c in want["stock"]]}  # fmt: skip
        if any(d.get(k) != v for k, v in shown.items()):
            raise ValueError("its cards aren't what its seed deals")
        for r in game["rows"]:
            where = f"row {r['n']} (game {d['n']})"
            seat = SEATS.index(r.get("seat"))
            if r["kind"] == PLAY:
                g.play(seat, card_of(r.get("card")), r.get("call"))
            elif r["kind"] == DRAW:
                if name(g.draw(seat)) != r.get("card"):
                    raise ValueError("its card isn't the one on top of the stock")
            else:
                g.pass_(seat)
            if r.get("result", "on") != g.result():
                raise ValueError(
                    f"it says {r.get('result')!r}; the cards say {g.result()!r}"
                )
    except (ValueError, KeyError, TypeError) as e:
        raise ValueError(f"{where}: {e}") from None
    return g


def check(rows: list[dict]) -> tuple[int, str | None]:
    held, dealt_at = 0, set()
    for r in rows:
        if r["kind"] == DEAL:
            dealt_at.add(r["n"])
        elif r["kind"] in KINDS and r.get("game") not in dealt_at:
            return held, f"row {r['n']}: its game isn't a game dealt before it"
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


def picture(g: Game) -> str:
    out = [
        f"{s:<6} {' '.join(name(c) for c in g.hands[i])}" for i, s in enumerate(SEATS)
    ]
    out.append(f"\npile: {name(g.top)}, {g.suit} to follow; stock: {len(g.stock)}")
    if g.over:
        out.append(f"the hand is over: {g.result()}")
    else:
        ok = g.can_play()
        what = " ".join(name(c) for c in ok) if ok else ("draw" if g.stock else "pass")
        out.append(f"{SEATS[g.turn]} to play: {what}")
    return "\n".join(out)


def current(box: Path):
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (replay(rows, gs[-1]) if gs else None)


def cmd_new(box: Path, ts: str) -> int:
    rows, gm, g = current(box)
    if gm is not None and not g.over:
        return fail(f"the hand dealt at row {gm['deal']['n']} isn't over")
    seed = rows[-1]["hash"] if rows else kernel.GENESIS
    d = dealt(seed)
    row = kernel.append(box, ts, DEAL, who=WHO, seats=list(SEATS), seed=seed, generator=GENERATOR,
                        hands=[[name(c) for c in h] for h in d["hands"]], top=name(d["top"]),
                        stock=[name(c) for c in d["stock"]])  # fmt: skip
    print(f"dealt at row {row['n']}: {name(d['top'])} turned up, north to play")
    return kernel.ALIVE


def cmd_move(box: Path, verb: str, args: list[str], ts: str) -> int:
    rows, gm, g = current(box)
    if gm is None:
        return fail("no hand is dealt: start one with new")
    seat, fields = g.turn, {}
    try:
        if verb == "play":
            card = card_of(args[0])
            call = args[1].upper() if len(args) > 1 else None
            g.play(seat, card, call)
            fields = {"card": name(card), **({"call": call} if call else {})}
            said = f"plays {name(card)}" + (f", {call} to follow" if call else "")
        elif verb == "draw":
            fields = {"card": name(g.draw(seat))}
            said = f"draws {fields['card']}"
        else:
            g.pass_(seat)
            said = "passes"
    except ValueError as e:
        return fail(str(e))
    row = kernel.append(box, ts, {"play": PLAY, "draw": DRAW, "pass": PASS}[verb], who=WHO,
                        game=gm["deal"]["n"], seat=SEATS[seat], result=g.result(), **fields)  # fmt: skip
    print(f"{SEATS[seat]} {said}   (row {row['n']})")
    if g.over:
        print(f"the hand is over: {g.result()}")
    return kernel.ALIVE


def cmd_show(box: Path) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no hand is dealt: start one with new")
    print(picture(g))
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    s = "s" if held != 1 else ""
    if why:
        return fail(f"{why} ({held} hand{s} before it held)")
    print(f"{held} hand{s} of crazy eights on the record; every one holds.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    shape = (verb in ("new", "show", "draw", "pass", "check") and len(args) == 1) or (verb == "play" and len(args) in (2, 3))  # fmt: skip
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
        return fail(f"the hands on the record don't hold: {why}; check names it")
    if verb == "show":
        return cmd_show(box)
    ts = opts.get("--now") or kernel.now()
    if verb == "new":
        return cmd_new(box, ts)
    return cmd_move(box, verb, args[1:], ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
