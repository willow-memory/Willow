"""hearts.py: Hearts played on the record, hands open, the deal seeded. Python 3.9+.

    python adapters/stdlib/hearts/hearts.py --box DIR new
    python adapters/stdlib/hearts/hearts.py --box DIR show
    python adapters/stdlib/hearts/hearts.py --box DIR pass SEAT CARD CARD CARD
    python adapters/stdlib/hearts/hearts.py --box DIR play CARD
    python adapters/stdlib/hearts/hearts.py --box DIR deal
    python adapters/stdlib/hearts/hearts.py --box DIR check

Four seats, north, east, south and west, and the standard game. Each hand
is dealt from willow's seeded stream (sha256-stream v1), seeded by the
record's tip, so nobody stacks the deck. The hands are open: every card is
on the record from the deal, as a table playing face up.

A hand begins with each seat passing three cards (`pass west 2C QS AH`):
to the left, then the right, then across, and every fourth hand none. Then
the 2C leads; every seat follows the suit led if it can; hearts can't be
led until one has been played, unless a seat holds nothing else; and no
heart or the QS goes on the first trick unless a seat has nothing else.
`play` plays the card of the seat whose turn it is. The highest card of
the suit led takes the trick and leads the next. Each heart taken is a
point and the QS thirteen; a seat that takes all thirteen hearts and the QS
shoots the moon, and every other seat takes 26. `deal` deals the next
hand. When a hand ends with a seat on 100 or more, the game is over, and
the lowest score wins.

Cards are written rank then suit: 2C, 10H (or TH), JD, QS, KC, AH.

Each deal, pass and card played is a row through the kernel's own
`append`. `check` plays every game on the record again from its first
row: every deal what its seed gives, every pass three cards of the seat's
own, every card one the rules allow by the seat whose turn it was, and the
scores the tricks give. The first that isn't is named.

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

OPEN, DEAL, PASS, PLAY = "hearts-open", "hearts-deal", "hearts-pass", "hearts-play"
KINDS = (OPEN, DEAL, PASS, PLAY)
WHO = "hearts"
GENERATOR = "sha256-stream/v1"
SEATS = ("north", "east", "south", "west")
SUITS = "CDHS"
RANKS = {"J": 11, "Q": 12, "K": 13, "A": 14, "T": 10}
QUEEN, TWO_CLUBS = (12, "S"), (2, "C")
TO = {0: "left", 1: "right", 2: "across", 3: "held"}
END = 100
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
    m = CARD.match(text.strip().upper())
    if not m:
        raise ValueError(f"{text!r} isn't a card: write 2C, 10H, QS, AH")
    rank = RANKS.get(m.group(1)) or int(m.group(1))
    return rank, m.group(2)


def points(card: tuple[int, str]) -> int:
    return 1 if card[1] == "H" else 13 if card == QUEEN else 0


def dealt(seed: str) -> list[list[tuple[int, str]]]:
    """The four hands `seed` deals, each sorted: the same every time."""
    cards = Stream(seed.encode()).shuffled(deck())
    return [sorted(cards[i * 13 : (i + 1) * 13], key=lambda c: (SUITS.index(c[1]), c[0])) for i in range(4)]  # fmt: skip


def direction(hand_no: int) -> int:
    return hand_no % 4  # 0 left, 1 right, 2 across, 3 held


def target(seat: int, way: int) -> int:
    return {0: (seat + 1) % 4, 1: (seat - 1) % 4, 2: (seat + 2) % 4}.get(way, seat)


def legal(hand: list, trick: list, broken: bool, first: bool) -> list:
    """The cards a seat may play: game-lab's legal_plays, rule for rule."""
    if not trick:
        if first and TWO_CLUBS in hand:
            return [TWO_CLUBS]
        if not broken:
            plain = [c for c in hand if c[1] != "H"]
            return plain or list(hand)
        return list(hand)
    led = trick[0][1][1]
    follow = [c for c in hand if c[1] == led]
    if follow:
        return follow
    if first:
        safe = [c for c in hand if points(c) == 0]
        return safe or list(hand)
    return list(hand)


# ── a game, replayed ─────────────────────────────────────────────────────────
class Game:
    """A game of Hearts as its rows say it went; ValueError at the first row
    the rules don't allow."""

    def __init__(self):
        self.scores, self.hand_no, self.over = [0, 0, 0, 0], -1, False
        self.hands, self.passes, self.trick, self.taken = None, {}, [], None
        self.broken, self.tricks, self.leader, self.phase = False, 0, 0, "deal"

    def deal(self, seed: str) -> None:
        if self.over:
            raise ValueError("the game is over")
        if self.phase != "deal":
            raise ValueError("this hand isn't played out yet")
        self.hand_no += 1
        self.hands = dealt(seed)
        self.passes, self.trick, self.broken, self.tricks = {}, [], False, 0
        self.taken = [[] for _ in range(4)]
        self.phase = "pass" if direction(self.hand_no) != 3 else "play"
        if self.phase == "play":
            self._lead()

    def give(self, seat: int, cards: list) -> None:
        if self.phase != "pass":
            raise ValueError("no cards are being passed now")
        if seat in self.passes:
            raise ValueError(f"{SEATS[seat]} has passed already")
        if (
            len(cards) != 3
            or len(set(cards)) != 3
            or any(c not in self.hands[seat] for c in cards)
        ):
            raise ValueError(f"{SEATS[seat]} passes three cards of its own")
        self.passes[seat] = cards
        if len(self.passes) == 4:
            way = direction(self.hand_no)
            for s, cs in self.passes.items():
                for c in cs:
                    self.hands[s].remove(c)
            for s, cs in self.passes.items():
                self.hands[target(s, way)].extend(cs)
            for h in self.hands:
                h.sort(key=lambda c: (SUITS.index(c[1]), c[0]))
            self.phase = "play"
            self._lead()

    def _lead(self) -> None:
        self.leader = next(i for i in range(4) if TWO_CLUBS in self.hands[i])

    def to_play(self) -> int:
        return (self.leader + len(self.trick)) % 4

    def play(self, seat: int, card: tuple) -> None:
        if self.phase != "play":
            raise ValueError(
                "no card is played now"
                if self.phase == "deal"
                else "the passes aren't all in"
            )
        if seat != self.to_play():
            raise ValueError(f"it is {SEATS[self.to_play()]}'s turn")
        ok = legal(self.hands[seat], self.trick, self.broken, self.tricks == 0)
        if card not in ok:
            raise ValueError(f"{name(card)} isn't a card {SEATS[seat]} may play; it may play {' '.join(name(c) for c in ok)}")  # fmt: skip
        self.hands[seat].remove(card)
        self.broken = self.broken or card[1] == "H"
        self.trick.append((seat, card))
        if len(self.trick) < 4:
            return
        led = self.trick[0][1][1]
        winner = max((t for t in self.trick if t[1][1] == led), key=lambda t: t[1][0])[
            0
        ]
        self.taken[winner] += [c for _, c in self.trick]
        self.trick, self.leader, self.tricks = [], winner, self.tricks + 1
        if self.tricks == 13:
            self._score()

    def _score(self) -> None:
        got = [sum(points(c) for c in t) for t in self.taken]
        moon = next((i for i in range(4) if got[i] == 26), None)
        if moon is not None:
            got = [0 if i == moon else 26 for i in range(4)]
        self.last = got
        self.scores = [a + b for a, b in zip(self.scores, got)]
        self.phase = "deal"
        self.over = max(self.scores) >= END

    def result(self) -> str:
        if not self.over:
            return "on"
        low = min(self.scores)
        won = [SEATS[i] for i in range(4) if self.scores[i] == low]
        return " and ".join(won) + (" won" if len(won) == 1 else " tied")


def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def replay(rows: list[dict], game: dict) -> Game:
    """The game its rows make, or ValueError naming the first row that isn't."""
    g = Game()
    for r in game["rows"]:
        where = f"row {r['n']} (game {game['open']['n']})"
        try:
            if r["kind"] == DEAL:
                before = rows[r["n"] - 1]["hash"] if r["n"] else kernel.GENESIS
                if r.get("seed") != before:
                    raise ValueError("its seed isn't the hash of the row before it")
                g.deal(r["seed"])
                if r.get("hand") != g.hand_no or r.get("hands") != [[name(c) for c in h] for h in dealt(r["seed"])]:  # fmt: skip
                    raise ValueError("its hands aren't what its seed deals")
            elif r["kind"] == PASS:
                g.give(
                    SEATS.index(r.get("seat")), [card_of(c) for c in r.get("cards", [])]
                )
            elif r["kind"] == PLAY:
                g.play(SEATS.index(r.get("seat")), card_of(str(r.get("card"))))
                if r.get("scores") not in (None, g.scores):
                    raise ValueError(
                        f"its scores aren't what the tricks give, {g.scores}"
                    )
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"{where}: {e}") from None
    return g


def check(rows: list[dict]) -> tuple[int, str | None]:
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


def picture(g: Game) -> str:
    out = []
    for i, s in enumerate(SEATS):
        hand = " ".join(name(c) for c in (g.hands[i] if g.hands else []))
        out.append(f"{s:<6} {g.scores[i]:>3}   {hand}")
    if g.trick:
        out.append("trick: " + "  ".join(f"{SEATS[s]} {name(c)}" for s, c in g.trick))
    return "\n".join(out)


def current(box: Path):
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (replay(rows, gs[-1]) if gs else None)


def write_deal(box: Path, rows: list[dict], game_n: int, g: Game, ts: str) -> dict:
    seed = rows[-1]["hash"] if rows else kernel.GENESIS
    hands = [[name(c) for c in h] for h in dealt(seed)]
    return kernel.append(box, ts, DEAL, who=WHO, game=game_n, hand=g.hand_no + 1, seed=seed,
                         generator=GENERATOR, way=TO[direction(g.hand_no + 1)], hands=hands)  # fmt: skip


def cmd_new(box: Path, ts: str) -> int:
    rows, gm, g = current(box)
    if gm is not None and not g.over:
        return fail(f"the game opened at row {gm['open']['n']} isn't over")
    op = kernel.append(box, ts, OPEN, who=WHO, seats=list(SEATS), to=END)
    rows, _ = kernel.read(box / "record.jsonl")
    d = write_deal(box, rows, op["n"], Game(), ts)
    print(f"new game at row {op['n']}, hand 1 dealt at row {d['n']}: pass {d['way']}")
    return kernel.ALIVE


def cmd_deal(box: Path, ts: str) -> int:
    rows, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    if g.over or g.phase != "deal":
        return fail(
            f"the game is over ({g.result()})"
            if g.over
            else "this hand isn't played out yet"
        )
    d = write_deal(box, rows, gm["open"]["n"], g, ts)
    print(f"hand {d['hand']} dealt at row {d['n']}: " + ("no pass" if d["way"] == "held" else f"pass {d['way']}"))  # fmt: skip
    return kernel.ALIVE


def cmd_show(box: Path) -> int:
    rows, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    print(picture(g))
    if g.over:
        print(f"\nthe game is over: {g.result()}")
    elif g.phase == "deal":
        print(f"\nhand {g.hand_no + 2} to deal: deal")  # hand_no counts from 0
    elif g.phase == "pass":
        waiting = [SEATS[s] for s in range(4) if s not in g.passes]
        print(
            f"\nhand {g.hand_no + 1}: pass {TO[direction(g.hand_no)]}; waiting on {', '.join(waiting)}"
        )
    else:
        s = g.to_play()
        ok = legal(g.hands[s], g.trick, g.broken, g.tricks == 0)
        print(
            f"\nhand {g.hand_no + 1}, trick {g.tricks + 1}: {SEATS[s]} to play {' '.join(name(c) for c in ok)}"
        )
    return kernel.ALIVE


def cmd_pass(box: Path, seat: str, cards: list[str], ts: str) -> int:
    rows, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    if seat not in SEATS:
        return fail(f"{seat!r} isn't a seat: {', '.join(SEATS)}")
    try:
        cs = [card_of(c) for c in cards]
        g.give(SEATS.index(seat), cs)
    except ValueError as e:
        return fail(str(e))
    row = kernel.append(box, ts, PASS, who=WHO, game=gm["open"]["n"], hand=g.hand_no, seat=seat, cards=[name(c) for c in cs])  # fmt: skip
    print(f"{seat} passes {' '.join(name(c) for c in cs)}   (row {row['n']})" + ("; every pass is in, the 2C leads" if g.phase == "play" else ""))  # fmt: skip
    return kernel.ALIVE


def cmd_play(box: Path, text: str, ts: str) -> int:
    rows, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    if g.over:
        return fail(f"the game is over ({g.result()})")
    try:
        card = card_of(text)
        seat = g.to_play()
        g.play(seat, card)
    except ValueError as e:
        return fail(str(e))
    fields = {"scores": g.scores} if g.phase == "deal" else {}
    row = kernel.append(box, ts, PLAY, who=WHO, game=gm["open"]["n"], hand=g.hand_no, seat=SEATS[seat], card=name(card), **fields)  # fmt: skip
    print(f"{SEATS[seat]} plays {name(card)}   (row {row['n']})")
    if g.phase == "deal":
        print(f"hand {g.hand_no + 1} scored {g.last}: " + ", ".join(f"{s} {v}" for s, v in zip(SEATS, g.scores)))  # fmt: skip
        if g.over:
            print(f"the game is over: {g.result()}")
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    if why:
        return fail(f"{why} ({held} game{'s' if held != 1 else ''} before it held)")
    print(
        f"{held} game{'s' if held != 1 else ''} of hearts on the record; every one holds."
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
    shape = (verb in ("new", "show", "deal", "check") and len(args) == 1) or (verb == "play" and len(args) == 2) or (verb == "pass" and len(args) == 5)  # fmt: skip
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
    held, why = check(rows)
    if why:
        return fail(f"the games on the record don't hold: {why}; check names it")
    ts = opts.get("--now") or kernel.now()
    if verb == "show":
        return cmd_show(box)
    if verb == "play":
        return cmd_play(box, args[1], ts)
    if verb == "pass":
        return cmd_pass(box, args[1], args[2:], ts)
    return {"new": cmd_new, "deal": cmd_deal}[verb](box, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
