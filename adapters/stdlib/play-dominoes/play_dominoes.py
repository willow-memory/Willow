"""play_dominoes.py: All Fives dominoes played on the record, the boneyard seeded. Python 3.9+.

    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR new
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR show [--seat SEAT]
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR play TILE [ARM]
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR draw
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR pass
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR auto
    python adapters/stdlib/play-dominoes/play_dominoes.py --box DIR check

Two seats, north and south, a double-six set, nine tiles each. Each hand's
tiles are shuffled from willow's seeded stream (sha256-stream v1, the one
dice uses), seeded by the hash of the row before the deal, so nobody
shuffles. The rest is the boneyard.

The first double played is the spinner: tiles go against its four arms,
left, right, up and down, in any order. A seat that can play must; one
that can't draws until it can, and passes when the boneyard is empty. After
every play the open ends are counted, and a count that is a multiple of five
scores itself. A hand ends when a seat plays its last tile, or when nobody
can play; then the seat out, or the seat holding fewer pips, scores the
other's pips to the nearest five. The game is over the moment a seat holds
250.

Each deal, play, draw and pass is a row through the kernel's own `append`.
`check` plays every game on the record again from its first row. The first
row that isn't what the tiles allow is named.

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

OPEN, DEAL, PLAY, DRAW, PASS = "dominoes-open", "dominoes-deal", "dominoes-play", "dominoes-draw", "dominoes-pass"  # fmt: skip
KINDS = (OPEN, DEAL, PLAY, DRAW, PASS)
WHO = "dominoes"
GENERATOR = "sha256-stream/v1"
SEATS = ("north", "south")
HAND, TARGET = 9, 250
ARMS = ("left", "right", "up", "down")
TILE = re.compile(r"^([0-6])\s*[|:\-/]?\s*([0-6])$")


# ── the seeded stream ────────────────────────────────────────────────────────
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


# ── the tiles ────────────────────────────────────────────────────────────────
def tiles() -> list[tuple[int, int]]:
    return [(a, b) for a in range(6, -1, -1) for b in range(a, -1, -1)]


def name(t: tuple[int, int]) -> str:
    return f"{t[0]}|{t[1]}"


def tile_of(text: str) -> tuple[int, int]:
    m = TILE.match(str(text).strip())
    if not m:
        raise ValueError(f"{text!r} isn't a tile: write 6|5, 6-5 or 65")
    a, b = int(m.group(1)), int(m.group(2))
    return (max(a, b), min(a, b))


def pips(hand: list) -> int:
    return sum(a + b for a, b in hand)


def to_five(n: int) -> int:
    """To the nearest five: 7 is 5, 8 is 10."""
    return (n + 2) // 5 * 5


def dealt(seed: str) -> dict:
    """What `seed` deals: two hands of nine, and the boneyard in the order it
    is drawn."""
    ts = Stream(seed.encode()).shuffled(tiles())
    return {"hands": [ts[:HAND], ts[HAND : 2 * HAND]], "boneyard": ts[2 * HAND :]}


def lead_of(hands: list[list], winner: int | None) -> tuple[int, tuple | None]:
    """Who leads a hand, and with what: the seat that went out last hand leads
    any tile; otherwise the highest double leads, or, with no double dealt,
    the heaviest tile."""
    if winner is not None:
        return winner, None
    held = [(t, s) for s, h in enumerate(hands) for t in h]
    doubles = [(t, s) for t, s in held if t[0] == t[1]]
    t, s = max(doubles) if doubles else max(held, key=lambda x: (pips([x[0]]), x[0]))
    return s, t


# ── the layout ───────────────────────────────────────────────────────────────
class Layout:
    """The tiles on the table: a lead, and four arms going out from it. Each
    tile on an arm is (inner, outer). The first double is the spinner; up and
    down go out from it, and are there only once it is."""

    def __init__(self):
        self.lead = None
        self.arms = {a: [] for a in ARMS}
        self.spinner = None  # None, "lead", or (arm, index) on the left or right arm

    def spinner_tile(self):
        if self.spinner == "lead":
            return self.lead
        return (
            None
            if self.spinner is None
            else self.arms[self.spinner[0]][self.spinner[1]]
        )

    def open_arms(self) -> list[str]:
        return list(ARMS) if self.spinner is not None else ["left", "right"]

    def end(self, arm: str) -> int:
        """The pip a tile played on `arm` must match."""
        if self.arms[arm]:
            return self.arms[arm][-1][1]
        if arm in ("up", "down"):
            return self.spinner_tile()[0]
        return self.lead[0] if arm == "left" else self.lead[1]

    def fits(self, t: tuple) -> list[str]:
        if self.lead is None:
            return ["lead"]
        return [a for a in self.open_arms() if self.end(a) in t]

    def place(self, t: tuple, arm: str) -> None:
        if arm == "lead":
            self.lead = t
            if t[0] == t[1]:
                self.spinner = "lead"
            return
        e = self.end(arm)
        placed = (e, t[1] if t[0] == e else t[0])
        self.arms[arm].append(placed)
        if self.spinner is None and t[0] == t[1]:
            self.spinner = (arm, len(self.arms[arm]) - 1)

    def count(self) -> int:
        """The open ends added up: a double at an end counts both halves, and
        so does the spinner, while either side of it along the line is open."""
        if self.lead is None:
            return 0
        total = 0
        for arm in ("left", "right"):
            if self.arms[arm]:
                a, b = self.arms[arm][-1]
                total += a + b if a == b else b
            elif self.lead[0] == self.lead[1]:
                total += (
                    0
                    if (arm == "right" and not self.arms["left"])
                    else 2 * self.lead[0]
                )
            else:
                total += self.lead[0] if arm == "left" else self.lead[1]
        for arm in ("up", "down"):
            if self.arms[arm]:
                a, b = self.arms[arm][-1]
                total += a + b if a == b else b
        return total


# ── a game, replayed ─────────────────────────────────────────────────────────
class Game:
    """A game of All Fives as its rows say it went: its hands, the layout and
    the scores; ValueError at the first move the rules don't allow."""

    def __init__(self):
        self.scores, self.hand_no, self.winner = [0, 0], 0, None
        self.hands, self.boneyard, self.layout = None, [], None
        self.turn, self.must_lead, self.last_out = 0, None, None
        self.ended, self.over, self.last_hand = True, False, None

    def deal(self, seed: str) -> None:
        if self.over:
            raise ValueError("the game is over")
        if not self.ended:
            raise ValueError("the hand before it isn't over")
        d = dealt(seed)
        self.hands, self.boneyard, self.layout = d["hands"], d["boneyard"], Layout()
        self.turn, self.must_lead = lead_of(self.hands, self.last_out)
        self.hand_no, self.ended = self.hand_no + 1, False

    def can_play(self, seat: int) -> list[tuple]:
        return [t for t in self.hands[seat] if self.layout.fits(t)]

    def _seat(self, seat: int) -> None:
        if self.over:
            raise ValueError(f"the game is over ({self.result()})")
        if self.ended:
            raise ValueError("no hand is dealt")
        if seat != self.turn:
            raise ValueError(f"it is {SEATS[self.turn]}'s turn")

    def play(self, seat: int, t: tuple, arm: str | None) -> tuple[str, int]:
        """Play `t`; the arm it went on, and what it scored."""
        self._seat(seat)
        if t not in self.hands[seat]:
            raise ValueError(f"{SEATS[seat]} doesn't hold {name(t)}")
        if self.must_lead is not None and t != self.must_lead:
            raise ValueError(f"{name(self.must_lead)} leads this hand")
        fits = self.layout.fits(t)
        if not fits:
            raise ValueError(f"{name(t)} doesn't fit an open end")
        if arm is None:
            if len(fits) > 1:
                raise ValueError(f"{name(t)} fits {' and '.join(fits)}: say which")
            arm = fits[0]
        elif fits == ["lead"]:
            arm = "lead"
        elif arm not in fits:
            raise ValueError(f"{name(t)} doesn't fit the {arm} end")
        self.layout.place(t, arm)
        self.hands[seat].remove(t)
        self.must_lead = None
        c = self.layout.count()
        scored = c if c and c % 5 == 0 else 0
        self.scores[seat] += scored
        self._after(seat)
        return arm, scored

    def draw(self, seat: int) -> tuple:
        self._seat(seat)
        if self.can_play(seat):
            raise ValueError(f"{SEATS[seat]} can play, so doesn't draw")
        if not self.boneyard:
            raise ValueError("the boneyard is empty: pass")
        t = self.boneyard.pop(0)
        self.hands[seat].append(t)
        return t

    def pass_(self, seat: int) -> None:
        self._seat(seat)
        if self.can_play(seat) or self.boneyard:
            raise ValueError(
                f"{SEATS[seat]} "
                + ("can play" if self.can_play(seat) else "draws first")
            )
        self._after(seat)

    def _after(self, seat: int) -> None:
        """The turn passes, and the hand or game ends when the tiles say so."""
        other = 1 - seat
        if self.scores[seat] >= TARGET:
            return self._end("target", seat, 0)
        if not self.hands[seat]:
            return self._end("out", seat, to_five(pips(self.hands[other])))
        if not self.boneyard and not self.can_play(0) and not self.can_play(1):
            held = [pips(h) for h in self.hands]
            if held[0] == held[1]:
                return self._end("blocked", None, 0)
            low = held.index(min(held))
            return self._end("blocked", low, to_five(held[1 - low]))
        self.turn = other

    def _end(self, how: str, seat: int | None, points: int) -> None:
        self.ended, self.last_out = True, seat if how == "out" else None
        if seat is not None:
            self.scores[seat] += points
        self.last_hand = {"how": how, "seat": None if seat is None else SEATS[seat], "points": points}  # fmt: skip
        if seat is not None and self.scores[seat] >= TARGET:
            self.over, self.winner = True, seat

    def result(self) -> str:
        if self.over:
            return f"{SEATS[self.winner]} won"
        return "hand over" if self.ended else "on"


def games(rows: list[dict]) -> list[dict]:
    out: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == OPEN:
            out[r["n"]] = {"open": r, "rows": []}
        elif r["kind"] in KINDS and r.get("game") in out:
            out[r["game"]]["rows"].append(r)
    return list(out.values())


def deal_fields(seed: str, g: Game) -> dict:
    """What a deal row holds, from the game just dealt."""
    return {"hand": g.hand_no, "seed": seed, "generator": GENERATOR,
            "hands": [[name(t) for t in h] for h in g.hands],
            "boneyard": [name(t) for t in g.boneyard], "leader": SEATS[g.turn],
            "lead": None if g.must_lead is None else name(g.must_lead)}  # fmt: skip


def said(g: Game) -> dict:
    """How the game stands after a move, as its row says it."""
    return {"scores": list(g.scores), "result": g.result()}


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
                want = deal_fields(r["seed"], g)
                if any(r.get(k) != v for k, v in want.items()):
                    raise ValueError("its tiles aren't what its seed deals")
                continue
            seat = SEATS.index(r.get("seat"))
            if r["kind"] == PLAY:
                arm, scored = g.play(seat, tile_of(r.get("tile")), r.get("arm"))
                if r.get("arm") != arm or r.get("scored") != scored:
                    raise ValueError(f"it scored {scored} on the {arm} arm")
            elif r["kind"] == DRAW:
                if name(g.draw(seat)) != r.get("tile"):
                    raise ValueError("its tile isn't the next in the boneyard")
                continue
            else:
                g.pass_(seat)
            if any(r.get(k) != v for k, v in said(g).items()):
                raise ValueError(f"it says {r.get('scores')} {r.get('result')!r}; the tiles say {g.scores} {g.result()!r}")  # fmt: skip
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
    for gm in games(rows):
        try:
            replay(rows, gm)
        except ValueError as e:
            return held, str(e)
        held += 1
    return held, None


# ── a seat played by a fixed rule ────────────────────────────────────────────
def chosen(g: Game, seat: int) -> tuple[tuple, str]:
    """The play `auto` makes: what scores most, then the heaviest tile, then
    the first arm in left, right, up, down. It reads no hand but its own."""
    best = None
    for t in g.can_play(seat):
        if g.must_lead is not None and t != g.must_lead:
            continue
        for arm in g.layout.fits(t):
            trial = Layout()
            trial.lead, trial.spinner = g.layout.lead, g.layout.spinner
            trial.arms = {a: list(v) for a, v in g.layout.arms.items()}
            trial.place(t, arm)
            c = trial.count()
            key = (
                c if c and c % 5 == 0 else 0,
                pips([t]),
                t,
                -ARMS.index(arm) if arm in ARMS else 0,
            )
            if best is None or key > best[0]:
                best = (key, t, arm)
    return best[1], best[2]


# ── the commands ─────────────────────────────────────────────────────────────
def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def arm_line(L: Layout, arm: str) -> str:
    """An arm from the lead out, each tile inner|outer; the spinner in braces."""
    return " ".join(
        ("{%d|%d}" if L.spinner == (arm, i) else "[%d|%d]") % t
        for i, t in enumerate(L.arms[arm])
    )


def picture(g: Game, only: int | None) -> str:
    L, out = g.layout, []
    if L.lead is None:
        out.append("the table is empty")
    else:
        lead = f"[{L.lead[0]}|{L.lead[1]}]"
        out.append(f"lead  {'{' + lead[1:-1] + '}' if L.spinner == 'lead' else lead}")
        for arm in L.open_arms():
            out.append(f"{arm:<5} {arm_line(L, arm) or '-'}   end {L.end(arm)}")
        out.append(f"count {L.count()}")
    out.append("")
    for s in range(2):
        if only is None or only == s:
            out.append(
                f"{SEATS[s]:<6} {' '.join(name(t) for t in sorted(g.hands[s], reverse=True))}"
            )
        else:
            out.append(f"{SEATS[s]:<6} {len(g.hands[s])} tiles")
    out.append(f"boneyard {len(g.boneyard)}")
    out.append(f"score  north {g.scores[0]}, south {g.scores[1]}  (to {TARGET})")
    if g.over:
        out.append(f"the game is over: {g.result()}")
    elif not g.ended:
        lead = f", leading {name(g.must_lead)}" if g.must_lead else ""
        out.append(f"{SEATS[g.turn]} to play{lead}")
    return "\n".join(out)


def current(box: Path):
    rows, _ = kernel.read(box / "record.jsonl")
    gs = games(rows)
    return rows, (gs[-1] if gs else None), (replay(rows, gs[-1]) if gs else None)


def deal_next(box: Path, game_n: int, g: Game, ts: str) -> dict:
    rows, _ = kernel.read(box / "record.jsonl")
    seed = rows[-1]["hash"] if rows else kernel.GENESIS
    g.deal(seed)
    return kernel.append(box, ts, DEAL, who=WHO, game=game_n, **deal_fields(seed, g))


def told_deal(row: dict) -> str:
    lead = f" with {row['lead']}" if row["lead"] else ""
    return f"hand {row['hand']} dealt at row {row['n']}: {row['leader']} leads{lead}"


def told_end(g: Game) -> list[str]:
    h = g.last_hand
    if h["how"] == "out":
        line = f"{h['seat']} is out: scores {h['points']} for the pips left"
    elif h["how"] == "target":
        line = f"{h['seat']} reaches {TARGET}"
    elif h["seat"] is None:
        line = "blocked, the pips tied: nobody scores"
    else:
        line = f"blocked: {h['seat']} holds fewer pips and scores {h['points']}"
    return [line, f"score  north {g.scores[0]}, south {g.scores[1]}"]


def cmd_new(box: Path, ts: str) -> int:
    _, gm, g = current(box)
    if gm is not None and not g.over:
        return fail(f"the game opened at row {gm['open']['n']} isn't over")
    op = kernel.append(
        box, ts, OPEN, who=WHO, seats=list(SEATS), each=HAND, target=TARGET
    )
    row = deal_next(box, op["n"], Game(), ts)
    print(f"new game at row {op['n']}; " + told_deal(row))
    return kernel.ALIVE


def move(
    box: Path, gm: dict, g: Game, verb: str, seat: int, ts: str, t=None, arm=None
) -> str:
    """Make one move on the record; what it said."""
    fields = {}
    if verb == "play":
        arm, scored = g.play(seat, t, arm)
        fields = {"tile": name(t), "arm": arm, "scored": scored, **said(g)}
        words = f"plays {name(t)} on the {arm}" if arm != "lead" else f"leads {name(t)}"
        words += f", {g.layout.count()} counted" + (
            f": scores {scored}" if scored else ""
        )
    elif verb == "draw":
        fields = {"tile": name(g.draw(seat))}
        words = "draws " + fields["tile"]
    else:
        g.pass_(seat)
        fields, words = said(g), "passes"
    row = kernel.append(box, ts, {"play": PLAY, "draw": DRAW, "pass": PASS}[verb], who=WHO,
                        game=gm["open"]["n"], seat=SEATS[seat], **fields)  # fmt: skip
    return f"{SEATS[seat]} {words}   (row {row['n']})"


def after(box: Path, gm: dict, g: Game, ts: str) -> None:
    if not g.ended:
        return
    for line in told_end(g):
        print(line)
    if g.over:
        print(f"the game is over: {g.result()}")
    else:
        print(told_deal(deal_next(box, gm["open"]["n"], g, ts)))


def cmd_move(box: Path, verb: str, args: list[str], ts: str) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    try:
        if verb == "play":
            arm = args[1].lower() if len(args) > 1 else None
            if arm is not None and arm not in ARMS:
                raise ValueError(f"{arm!r} isn't an arm: left, right, up or down")
            print(move(box, gm, g, "play", g.turn, ts, tile_of(args[0]), arm))
        else:
            print(move(box, gm, g, verb, g.turn, ts))
    except ValueError as e:
        return fail(str(e))
    after(box, gm, g, ts)
    return kernel.ALIVE


def cmd_auto(box: Path, ts: str) -> int:
    """The seat to play plays by the fixed rule: draws until it can, passes
    when it can't, and says only what it did."""
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    try:
        g._seat(g.turn)
    except ValueError as e:
        return fail(str(e))
    seat, drew = g.turn, 0
    while not g.can_play(seat) and g.boneyard:
        g.draw(seat)
        kernel.append(box, ts, DRAW, who=WHO, game=gm["open"]["n"], seat=SEATS[seat], tile=name(g.hands[seat][-1]))  # fmt: skip
        drew += 1
    if drew:
        print(f"{SEATS[seat]} draws {drew} tile{'s' if drew > 1 else ''}")
    if g.can_play(seat):
        t, arm = chosen(g, seat)
        print(move(box, gm, g, "play", seat, ts, t, arm))
    else:
        print(move(box, gm, g, "pass", seat, ts))
    after(box, gm, g, ts)
    return kernel.ALIVE


def cmd_show(box: Path, seat: str | None) -> int:
    _, gm, g = current(box)
    if gm is None:
        return fail("no game is open: start one with new")
    if seat is not None and seat not in SEATS:
        return fail(f"{seat!r} isn't a seat: north or south")
    print(picture(g, None if seat is None else SEATS.index(seat)))
    return kernel.ALIVE


def cmd_check(box: Path) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    held, why = check(rows)
    s = "s" if held != 1 else ""
    if why:
        return fail(f"{why} ({held} game{s} before it held)")
    print(f"{held} game{s} of dominoes on the record; every one holds.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--seat"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    shape = (verb in ("new", "show", "draw", "pass", "auto", "check") and len(args) == 1) or (verb == "play" and len(args) in (2, 3))  # fmt: skip
    if not opts.get("--box") or not shape or ("--seat" in opts and verb != "show"):
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
        return cmd_show(box, opts.get("--seat"))
    ts = opts.get("--now") or kernel.now()
    if verb == "new":
        return cmd_new(box, ts)
    if verb == "auto":
        return cmd_auto(box, ts)
    return cmd_move(box, verb, args[1:], ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
