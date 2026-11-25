"""play_fight5e.py: the Aetheris setting's 5e encounters, fought on dice dropped in the tower, every blow a row. Python 3.9+.

    python adapters/deps/play-fight5e/play_fight5e.py list
    python adapters/deps/play-fight5e/play_fight5e.py --box DIR fight ENCOUNTER --to DIEDIR [--now TS]
    python adapters/deps/play-fight5e/play_fight5e.py --box DIR check
    python adapters/deps/play-fight5e/play_fight5e.py --box DIR board [--fight ROW] [--round N]
    python adapters/deps/play-fight5e/play_fight5e.py sim ENCOUNTER [--runs N]

`list` names the four encounters. `fight` plays one, by aetheris5e's rules
(combat.py: saves, resistances, recharging specials, stun and blind, Sneak
Attack, Action Surge), the party of three pregens against the encounter's
foes (statblocks.py). Every die the engine asks for is dropped in
dice-tower first, into DIEDIR (a folder that is already there), and brought
out at once, so its face is the tower's and no one's choice. On the record:
an `encounter-open` row, the tower's own rows, one `encounter-blow` per thing
that happened (its words, `note`, and what changed, `state`), and an
`encounter-end` with the result; each blow and the end name the tower rows
whose faces they used, under `dice`. It prints each blow.

`check` reads the record alone: the chain holds; every die out of the tower
holds to its drop, and none is still inside; each row's dice are dice out
of the tower, dropped after its encounter opened, none used twice; and the
encounter, fought again on those faces, gives every blow and the end as
written, with no die left over. `board` draws a fight from its rows (who's
hurt, who's down, stunned or blinded, the round, whose turn is next): the
last fight unless --fight names its open row, as it ended unless --round
says which round to stop at; it needs no dice. `sim` fights an encounter
many times on seeded dice (round i on random.Random(i), 500 unless --runs)
and says where it rolls out; it writes nothing, and is never a fight on the
record.

The machine rolls and remembers. What a fight means for a story is for the
people at the table to say: nothing here proposes or seals.

Exit codes, the kernel's: 0 done; 2 refused, with why.
"""

from __future__ import annotations

import contextlib
import io
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "dice-tower"))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "play-dice"))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "play-dice5e"))
sys.path.insert(0, str(HERE))

import board  # noqa: E402
import dice_tower as tower  # noqa: E402
import kernel  # noqa: E402
import statblocks  # noqa: E402

OPEN, BLOW, END, WHO = board.OPEN, board.BLOW, board.END, "play-fight5e"
ENGINE = "aetheris5e combat"
INSTALL = "pip install -r adapters/deps/play-fight5e/requirements.txt"
USAGE = __doc__.split("\n\n")[1]


def refuse(why: str) -> int:
    print(f"play-fight5e: {why}", file=sys.stderr)
    return kernel.REFUSED


def engine():
    """combat.py, or None when the dice library isn't installed."""
    try:
        import combat
    except ImportError:
        return None
    return combat


class OutOfFaces(RuntimeError):
    """The engine asked for a die nobody supplied. It is never guessed."""


class Faces:
    """Faces handed in, in the order the engine asks for them."""

    def __init__(self, faces: list[int]):
        self._faces = list(faces)
        self.drawn = 0

    def draw(self, sides: int) -> int:
        if not self._faces:
            raise OutOfFaces(f"a d{sides} was asked for and no face is left")
        face = self._faces.pop(0)
        if not 1 <= face <= sides:
            raise ValueError(f"{face} is not on a d{sides}")
        self.drawn += 1
        return face

    @property
    def left(self) -> int:
        return len(self._faces)


class TowerFaces:
    """Each die asked for, dropped in the tower and brought out; the out rows kept in order."""

    def __init__(self, box: Path, die_dir: Path, ts: str):
        self.box, self.die_dir, self.ts = box, die_dir, ts
        self.outs: list[int] = []
        self.n = len(list(die_dir.glob("die-*.json")))
        self.why = ""

    @property
    def drawn(self) -> int:
        return len(self.outs)

    def draw(self, sides: int) -> int:
        self.n += 1
        die = self.die_dir / ("die-" + str(self.n).zfill(4) + ".json")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:  # fmt: skip
            if tower.drop(self.box, f"1d{sides}", die, self.why, self.ts) != kernel.ALIVE:  # fmt: skip
                raise RuntimeError(f"the tower would not take a d{sides}: {err.getvalue().strip()}")  # fmt: skip
            rows, _ = kernel.read(self.box / "record.jsonl")
            if tower.out(self.box, rows, die, self.ts) != kernel.ALIVE:
                raise RuntimeError(f"the tower would not bring a d{sides} out: {err.getvalue().strip()}")  # fmt: skip
        rows, _ = kernel.read(self.box / "record.jsonl")
        self.outs.append(rows[-1]["n"])
        return int(rows[-1]["faces"][0][0])


class SaidRandom(random.Random):
    """The one generator the engine is given: every die is a face from the source.
    Any other kind of draw is refused, so none comes from anywhere but the source."""

    def __init__(self, faces):
        super().__init__(0)
        self.faces = faces

    def randint(
        self, a: int, b: int
    ) -> int:  # the engine rolls through randint(1, faces)
        if a != 1:
            raise ValueError("dice here run from 1")
        return self.faces.draw(b)

    def _not_a_die(self, *_a, **_k):
        raise RuntimeError("the engine asked for a draw that isn't a die")

    random = randrange = choice = choices = shuffle = sample = uniform = getrandbits = _not_a_die  # fmt: skip


class Kept:
    """The engine's sink: each blow as (note, state, how many dice were out by then)."""

    def __init__(self, faces):
        self.faces = faces
        self.blows: list[tuple[str, dict, int]] = []

    def snapshot(self, state, note=""):
        self.blows.append((note, json.loads(json.dumps(state)), self.faces.drawn))


def encounter_or_refuse(name: str) -> str | None:
    if name not in statblocks.ENCOUNTERS:
        return f"no encounter {name!r}: {', '.join(statblocks.ENCOUNTERS)}"
    return None


def play(combat, encounter: str, faces) -> tuple[list[tuple[str, dict, int]], dict]:
    """(every blow as (note, state, dice out after it), the result) of ENCOUNTER on FACES."""
    kept = Kept(faces)
    res = combat.Combat(statblocks.build_encounter(encounter), SaidRandom(faces), sink=kept).run()  # fmt: skip
    return kept.blows, json.loads(json.dumps(res))


def fight(combat, box: Path, encounter: str, die_dir: Path, ts: str) -> int:
    desc = statblocks.ENCOUNTERS[encounter]["desc"]
    opened = kernel.append(box, ts, OPEN, who=WHO, encounter=encounter, desc=desc, engine=ENGINE)  # fmt: skip
    src = TowerFaces(box, die_dir, ts)
    src.why = f"{encounter}, opened at row {opened['n']}"
    try:
        blows, res = play(combat, encounter, src)
    except RuntimeError as e:
        return refuse(f"the encounter opened at row {opened['n']} stopped: {e}")
    print(f"{desc}   (row {opened['n']})")
    at = 0
    for note, state, upto in blows:
        kernel.append(box, ts, BLOW, who=WHO, fight=opened["n"], note=note, state=state, dice=src.outs[at:upto])  # fmt: skip
        at = upto
        print(f"  {note}")
    end = kernel.append(box, ts, END, who=WHO, fight=opened["n"], result=res, dice=src.outs[at:])  # fmt: skip
    standing = ", ".join(res["party_survivors"] + res["foe_survivors"]) or "no one"
    print(f"{res['outcome'].upper()} in {res['rounds']} rounds; standing: {standing}   (rows {opened['n']}-{end['n']})")  # fmt: skip
    return kernel.ALIVE


def check(combat, rows: list[dict]) -> tuple[int, str | None]:
    """(how many encounters hold, why the first that doesn't fails)."""
    _held, inside, why = tower.check(rows)
    if why:
        return 0, why
    if inside:
        return 0, f"{len(inside)} {'die is' if len(inside) == 1 else 'dice are'} still in the tower"  # fmt: skip
    used: set[int] = set()
    held = 0
    for opened in (r for r in rows if r["kind"] == OPEN):
        n = opened["n"]
        bad = encounter_or_refuse(str(opened.get("encounter")))
        if bad:
            return held, f"row {n}: {bad}"
        mine = [r for r in rows if r["kind"] in (BLOW, END) and r.get("fight") == n]
        ends = [r for r in mine if r["kind"] == END]
        if len(ends) != 1 or mine[-1]["kind"] != END:
            return held, f"the encounter opened at row {n} has {len(ends)} endings on the record, not one at its end"  # fmt: skip
        faces = []
        for r in mine:
            for m in r.get("dice", []):
                out = rows[m] if isinstance(m, int) and 0 <= m < len(rows) else None
                if out is None or out["kind"] != tower.OUT:
                    return held, f"row {r['n']} names row {m}, which isn't a die out of the tower"  # fmt: skip
                if m in used:
                    return held, f"row {r['n']} uses the die out at row {m}, which another row used"  # fmt: skip
                used.add(m)
                if out["drop"] < n:
                    return held, f"row {r['n']} uses a die dropped at row {out['drop']}, before the encounter opened"  # fmt: skip
                faces.append(int(out["faces"][0][0]))
        src = Faces(faces)
        try:
            blows, res = play(combat, opened["encounter"], src)
        except (OutOfFaces, ValueError, RuntimeError) as e:
            return held, f"the encounter opened at row {n}: its dice don't make the fight: {e}"  # fmt: skip
        written = [(r["note"], r["state"]) for r in mine if r["kind"] == BLOW]
        again = [(note, state) for note, state, _ in blows]
        for i, (got, want) in enumerate(zip(written, again)):
            if got != want:
                row = [r for r in mine if r["kind"] == BLOW][i]["n"]
                return held, f"the encounter opened at row {n}: row {row}, {got[0]!r}, isn't what its dice give ({want[0]!r})"  # fmt: skip
        if len(written) != len(again) or ends[0]["result"] != res:
            return held, f"the encounter opened at row {n}: {len(written)} blows and its end on the record; its dice give {len(again)} blows and another end"  # fmt: skip
        if src.left:
            return held, f"the encounter opened at row {n} names {src.left} more dice than its fight throws"  # fmt: skip
        held += 1
    return held, None


def draw_board(rows: list[dict], fight_at: str, upto: str) -> int:
    opened = [r["n"] for r in rows if r["kind"] == OPEN]
    if not opened:
        return refuse("no encounter on the record")
    if (fight_at and not fight_at.isdigit()) or (upto and not upto.isdigit()):
        return refuse("--fight and --round are numbers")
    at = int(fight_at) if fight_at else opened[-1]
    if at not in opened:
        return refuse(f"row {at} doesn't open an encounter; encounters open at rows {', '.join(map(str, opened))}")  # fmt: skip
    print(board.draw(board.state(rows, at, int(upto) if upto else None)))
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--now", "--fight", "--round", "--runs"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args == ["list"] and len(opts) == 0:
        for name, e in statblocks.ENCOUNTERS.items():
            print(f"  {name:<10} {e['desc']}")
        return kernel.ALIVE
    if args[:1] == ["sim"] and len(args) == 2 and set(opts) <= {"--runs"}:
        runs = opts.get("--runs", "500")
        if not runs.isdigit() or int(runs) < 1:
            return refuse("--runs is a whole number of fights, 1 or more")
        bad = encounter_or_refuse(args[1])
        if bad:
            return refuse(bad)
        combat = engine()
        if combat is None:
            return refuse(f"this needs the dice library: {INSTALL}")
        print(combat._fmt_sim(combat.simulate(args[1], int(runs))))
        return kernel.ALIVE
    need = {"fight": 2, "check": 1, "board": 1}
    if not opts.get("--box") or not args or args[0] not in need or len(args) != need[args[0]] or (args[0] == "fight" and not opts.get("--to")):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    if args == ["board"]:
        return draw_board(rows, opts.get("--fight", ""), opts.get("--round", ""))
    combat = engine()
    if combat is None:
        return refuse(f"this needs the dice library: {INSTALL}")
    if args == ["check"]:
        held, why = check(combat, rows)
        if why:
            return refuse(why)
        print(f"{held} {'encounter' if held == 1 else 'encounters'} on the record; every blow holds")  # fmt: skip
        return kernel.ALIVE
    bad = encounter_or_refuse(args[1])
    if bad:
        return refuse(bad)
    die_dir = Path(opts["--to"])
    if not die_dir.is_dir():
        return refuse(f"{die_dir} isn't a folder; the dice go in one that is already there")  # fmt: skip
    return fight(combat, box, args[1], die_dir, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
