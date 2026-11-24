"""play_fight.py: a fight blow by blow, on dice dropped in the tower, played again from the record to check it. Python 3.10+ (dndwright's).

    python adapters/deps/play-fight/play_fight.py --box DIR fight --fighters FILE --to DIEDIR [--now TS]
    python adapters/deps/play-fight/play_fight.py --box DIR check

`fight` plays one fight between the fighters FILE names, with dndwright's
rules: initiative, an attack against armor class, damage on a hit, twice the
dice on a natural 20, a fighter down at 0 hit points. Every die it asks for is
dropped in dice-tower first, into DIEDIR (a folder that is already there), and
brought out at once, so its face is the tower's and no one's choice. On the
record: a `fight-begin` row (the fighters whole, and the dndwright that ran
it), the tower's own rows, then one `fight-row` per thing that happened
(`init`, `blow`, `down`, `end`), each naming the tower rows its faces came
from. It prints each blow.

`check` reads the record alone: the chain holds; every die out of the tower
holds to its drop, and none is still inside; each fight row's faces are the
tower's, from dice dropped after the fight began, none used twice; and the
fight played again on those faces, with the fighters its begin row names,
comes out as written. A blow changed in the file breaks the chain; rows
written honestly with a blow changed, and no tower dice behind them, are
refused.

FILE is a JSON list, a fighter an object: `name`, `side` (`party` or
`foes`), `hp`, `ac`, `init_mod`, `attack_bonus`, `damage` (dice, `1d6+2`),
and `attacks`, blows a turn, 1 if left out. Whom a fighter hits is the first
one standing on the other side, in the order FILE lists them; a fight not over
in 20 rounds ends `stalemate`.

The machine rolls and remembers. What a fight means for a story is for the
people at the table to say: nothing here proposes or seals.

Exit codes, the kernel's: 0 done; 2 refused, with why.
"""

from __future__ import annotations

import contextlib
import io
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, fields
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "dice-tower"))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "play-dice"))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "play-dice5e"))

import dice_tower as tower  # noqa: E402
import kernel  # noqa: E402

BEGIN, ROW, WHO = "fight-begin", "fight-row", "play-fight"
SIDES = ("party", "foes")
MAX_ROUNDS = 20
DICE = re.compile(r"^\d*d\d+(?:[+-](?:\d*d\d+|\d+))*$")
INSTALL = "pip install -r adapters/deps/play-fight/requirements.txt"
USAGE = __doc__.split("\n\n")[1]


def refuse(why: str) -> int:
    print(f"play-fight: {why}", file=sys.stderr)
    return kernel.REFUSED


def dndwright():
    """dndwright's pieces the fight uses, or None when it isn't installed."""
    try:
        from dndwright.combat.combat import CombatantState, apply_damage
        from dndwright.combat.initiative import (
            InitiativeEntry,
            order_initiative,
            roll_initiative,
        )
        from dndwright.dice.engine import DiceEngine
    except ImportError:
        return None
    return {
        "CombatantState": CombatantState,
        "apply_damage": apply_damage,
        "InitiativeEntry": InitiativeEntry,
        "order_initiative": order_initiative,
        "roll_initiative": roll_initiative,
        "DiceEngine": DiceEngine,
        "version": metadata.version("dndwright"),
    }


class OutOfFaces(RuntimeError):
    """The engine asked for a die nobody supplied. It is never guessed."""


@dataclass(frozen=True)
class Fighter:
    name: str
    side: str
    hp: int
    ac: int
    init_mod: int
    attack_bonus: int
    damage: str
    attacks: int = 1


def fighters_from(data) -> list[Fighter]:
    """Fighters from a JSON list; ValueError naming the first thing wrong."""
    if not isinstance(data, list) or not data:
        raise ValueError("the fighters are a JSON list, one object a fighter")
    known = {f.name for f in fields(Fighter)}
    out, names = [], set()
    for i, d in enumerate(data, 1):
        if not isinstance(d, dict):
            raise ValueError(f"fighter {i} isn't an object")
        extra = sorted(set(d) - known)
        if extra:
            raise ValueError(f"fighter {i} has {', '.join(extra)}, which a fighter hasn't")  # fmt: skip
        missing = sorted(known - {"attacks"} - set(d))
        if missing:
            raise ValueError(f"fighter {i} has no {', '.join(missing)}")
        name = d["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"fighter {i} has no name")
        if name in names:
            raise ValueError(f"two fighters are named {name}")
        names.add(name)
        if d["side"] not in SIDES:
            raise ValueError(f"{name}'s side is {d['side']!r}, not party or foes")
        for k in ("hp", "ac", "init_mod", "attack_bonus", "attacks"):
            v = d.get(k, 1)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(f"{name}'s {k} isn't a whole number")
        if d["hp"] < 1 or d.get("attacks", 1) < 1:
            raise ValueError(f"{name} needs at least 1 hp and 1 attack")
        if not isinstance(d["damage"], str) or not DICE.match(d["damage"]):
            raise ValueError(f"{name}'s damage {d['damage']!r} isn't dice, as 1d6+2 is")  # fmt: skip
        out.append(Fighter(**d))
    for side in SIDES:
        if not any(f.side == side for f in out):
            raise ValueError(f"no fighter is on the {side} side")
    return out


class Faces:
    """Faces handed in, in the order the engine asks for them."""

    def __init__(self, faces: list[int]):
        self._faces = list(faces)

    def draw(self, sides: int) -> int:
        if not self._faces:
            raise OutOfFaces(f"a d{sides} was asked for and no face is left")
        face = self._faces.pop(0)
        if not 1 <= face <= sides:
            raise ValueError(f"{face} is not on a d{sides}")
        return face

    def say(self, why: str) -> None:
        """What the next die is for; a list of faces has nowhere to write it."""


class TowerFaces:
    """Each die asked for, dropped in the tower and brought out; the out rows kept in order."""

    def __init__(self, box: Path, die_dir: Path, ts: str):
        self.box, self.die_dir, self.ts = box, die_dir, ts
        self.why = ""
        self.outs: list[int] = []
        self.n = len(list(die_dir.glob("die-*.json")))

    def say(self, why: str) -> None:
        self.why = why

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
    """The one generator dndwright is given: every die is a face from the source."""

    def __init__(self, faces):
        super().__init__()
        self.faces = faces

    def randint(
        self, a: int, b: int
    ) -> int:  # dndwright rolls through randint(1, sides)
        if a != 1:
            raise ValueError("dice here run from 1")
        return self.faces.draw(b)


def fight(dw: dict, fighters: list[Fighter], faces) -> list[dict]:
    """The fight as rows: init, blow, down, end. `faces` is a list of ints, or a
    source with draw(sides) and say(why). Raises OutOfFaces when the faces run out."""
    src = faces if hasattr(faces, "draw") else Faces(faces)
    engine = dw["DiceEngine"](rng=SaidRandom(src))
    rows: list[dict] = []
    inits = {}
    for f in fighters:
        src.say(f"{f.name} rolls initiative")
        r = dw["roll_initiative"](engine, f.init_mod)
        inits[f.name] = r.total
        rows.append({"kind": "init", "who": f.name, "d20": r.roll, "total": r.total})
    entries = (dw["InitiativeEntry"](f.name, inits[f.name], dexterity_modifier=f.init_mod) for f in fighters)  # fmt: skip
    order = [e.name for e in dw["order_initiative"](entries)]
    by = {f.name: f for f in fighters}
    state = {f.name: dw["CombatantState"](current_hp=f.hp, max_hp=f.hp) for f in fighters}  # fmt: skip

    def standing(side: str) -> list[str]:
        return [f.name for f in fighters if f.side == side and state[f.name].current_hp > 0]  # fmt: skip

    for rnd in range(1, MAX_ROUNDS + 1):
        for name in order:
            me = by[name]
            if state[name].current_hp <= 0:
                continue
            other = SIDES[1] if me.side == SIDES[0] else SIDES[0]
            if not standing(other):
                rows.append({"kind": "end", "round": rnd, "winner": me.side})
                return rows
            for _ in range(me.attacks):
                foes = standing(other)
                if not foes:
                    break
                target = foes[0]
                src.say(f"{name} attacks {target}")
                atk = engine.roll_attack(modifier=me.attack_bonus, target_ac=by[target].ac)  # fmt: skip
                blow = {
                    "kind": "blow",
                    "round": rnd,
                    "who": name,
                    "target": target,
                    "d20": atk.roll.natural_roll,
                    "total": atk.roll.total,
                    "ac": by[target].ac,
                    "hit": bool(atk.is_hit),
                    "crit": bool(atk.roll.is_critical),
                }
                if atk.is_hit:
                    src.say(f"{name}'s damage to {target}")
                    dmg = engine.roll_damage(me.damage, is_critical=atk.roll.is_critical)  # fmt: skip
                    state[target], _ = dw["apply_damage"](state[target], dmg.roll.total)
                    blow.update(damage=dmg.roll.total, dice=list(dmg.roll.individual_rolls))  # fmt: skip
                blow["hp_after"] = state[target].current_hp
                rows.append(blow)
                if state[target].current_hp <= 0:
                    rows.append({"kind": "down", "who": target})
                    if not standing(other):  # the last of them: won in this round
                        rows.append({"kind": "end", "round": rnd, "winner": me.side})
                        return rows
    rows.append({"kind": "end", "round": MAX_ROUNDS, "winner": "stalemate"})
    return rows


def faces_of(row: dict) -> list[int]:
    """The faces one fight row says were thrown, in the order the fight asked for them."""
    if row["kind"] == "init":
        return [row["d20"]]
    if row["kind"] == "blow":
        return [row["d20"], *row.get("dice", [])]
    return []


def said(row: dict) -> str:
    """One fight row, in words."""
    k = row["kind"]
    if k == "init":
        return f"{row['who']} rolls {row['d20']} for initiative: {row['total']}"
    if k == "blow":
        head = f"round {row['round']}: {row['who']} attacks {row['target']}, {row['total']} against armor {row['ac']}"  # fmt: skip
        if not row["hit"]:
            return head + ": a miss"
        crit = ", a critical hit" if row["crit"] else ""
        return head + f"{crit}: {row['damage']} damage, {row['target']} at {row['hp_after']}"  # fmt: skip
    if k == "down":
        return f"{row['who']} is down"
    if row["winner"] == "stalemate":
        return f"no side won in {row['round']} rounds"
    return f"the {row['winner']} side won in round {row['round']}"


def play(dw: dict, box: Path, fighters: list[Fighter], die_dir: Path, ts: str) -> int:
    begun = kernel.append(box, ts, BEGIN, who=WHO, engine="dndwright " + dw["version"], fighters=[asdict(f) for f in fighters])  # fmt: skip
    src = TowerFaces(box, die_dir, ts)
    try:
        got = fight(dw, fighters, src)
    except RuntimeError as e:
        return refuse(f"the fight begun at row {begun['n']} stopped: {e}")
    outs = iter(src.outs)
    for r in got:
        dice = [next(outs) for _ in faces_of(r)]
        kernel.append(box, ts, ROW, who=WHO, fight=begun["n"], row=r, **({"dice": dice} if dice else {}))  # fmt: skip
        print(said(r))
    print(f"(the fight begins at row {begun['n']}; check it with: check)")
    return kernel.ALIVE


def check(dw: dict, rows: list[dict]) -> tuple[int, str | None]:
    """(how many fights hold, why the first that doesn't fails)."""
    _held, inside, why = tower.check(rows)
    if why:
        return 0, why
    if inside:
        return 0, f"{len(inside)} {'die is' if len(inside) == 1 else 'dice are'} still in the tower"  # fmt: skip
    used: set[int] = set()
    held = 0
    for begun in (r for r in rows if r["kind"] == BEGIN):
        n = begun["n"]
        got = [r for r in rows if r["kind"] == ROW and r.get("fight") == n]
        if not got or got[-1]["row"].get("kind") != "end":
            return held, f"the fight begun at row {n} has no end on the record"
        thrown = []
        for r in got:
            said_faces = faces_of(r["row"])
            dice = r.get("dice", [])
            if len(dice) != len(said_faces):
                return held, f"row {r['n']} says {len(said_faces)} faces and names {len(dice)} tower dice"  # fmt: skip
            for m, face in zip(dice, said_faces):
                out = rows[m] if isinstance(m, int) and 0 <= m < len(rows) else None
                if out is None or out["kind"] != tower.OUT:
                    return held, f"row {r['n']} names row {m}, which isn't a die out of the tower"  # fmt: skip
                if m in used:
                    return held, f"row {r['n']} uses the die out at row {m}, which another row used"  # fmt: skip
                used.add(m)
                if out["drop"] < n:
                    return held, f"row {r['n']} uses a die dropped at row {out['drop']}, before the fight began"  # fmt: skip
                if int(out["faces"][0][0]) != face:
                    return held, f"row {r['n']} says {face}; the tower brought out {out['faces'][0][0]} at row {m}"  # fmt: skip
            thrown += said_faces
        written = [r["row"] for r in got]
        try:
            again = fight(dw, [Fighter(**f) for f in begun["fighters"]], thrown)
        except (OutOfFaces, ValueError, TypeError) as e:
            return held, f"the fight begun at row {n}: its faces don't make a fight: {e}"  # fmt: skip
        if again != written:
            i = next((i for i, (a, b) in enumerate(zip(written, again)) if a != b), min(len(written), len(again)))  # fmt: skip
            ran = "dndwright " + dw["version"]
            other = f" (it was written by {begun.get('engine')}, played again on {ran})" if begun.get("engine") != ran else ""  # fmt: skip
            where = f"row {got[i]['n']}" if i < len(got) else "a row after its last"
            return held, f"the fight begun at row {n}: {where} doesn't come out as written{other}"  # fmt: skip
        held += 1
    return held, None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--fighters", "--to", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    need = {"fight": ("--fighters", "--to"), "check": ()}
    if not opts.get("--box") or len(args) != 1 or args[0] not in need or not all(opts.get(k) for k in need[args[0]]):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    dw = dndwright()
    if dw is None:
        return refuse(f"this needs dndwright, on Python 3.10 or newer: {INSTALL}")
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    if args == ["check"]:
        held, why = check(dw, rows)
        if why:
            return refuse(why)
        print(f"{held} {'fight' if held == 1 else 'fights'} on the record, every one holds")  # fmt: skip
        return kernel.ALIVE
    die_dir = Path(opts["--to"])
    if not die_dir.is_dir():
        return refuse(f"{die_dir} isn't a folder; the dice go in one that is already there")  # fmt: skip
    try:
        fighters = fighters_from(json.loads(Path(opts["--fighters"]).read_text(encoding="utf-8")))  # fmt: skip
    except OSError as e:
        return refuse(f"{opts['--fighters']} can't be read: {e.strerror}")
    except ValueError as e:
        return refuse(f"{opts['--fighters']}: {e}")
    return play(dw, box, fighters, die_dir, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
