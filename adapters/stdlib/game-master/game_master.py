"""game_master.py: a tabletop world played beat by beat, its rolls and the
person's rulings as rows on the record. Python 3.9+.

    python adapters/stdlib/game-master/game_master.py --box DIR open   --world W.json [--now TS]
    python adapters/stdlib/game-master/game_master.py --box DIR status --world W.json
    python adapters/stdlib/game-master/game_master.py --box DIR act STAT --world W.json [--now TS]
    python adapters/stdlib/game-master/game_master.py --box DIR ask    --world W.json [--now TS]
    python adapters/stdlib/game-master/game_master.py --box DIR settle --world W.json [--now TS]
    python adapters/stdlib/game-master/game_master.py --box DIR check [--world W.json]

A world is a JSON file (see README.md): stats, characters, places, and scenes
of beats. A beat is one of two kinds.

An action beat is `act STAT`: it rolls 2d6 with dice's own `roll` (the row is
seeded by the record's tip, so nobody picks the faces), adds the acting
character's stat, and reads the total as strong (10 or more), weak (7 to 9)
or miss (6 or less). The roll row and a `table-beat` row naming it go on the
record, and the beat's own line for that band is printed.

A decision beat is a ruling, and the game master's call is the person's, not
this code's. `ask` hands the beat's fact in as a proposal through the
kernel's own `bite` and `propose` and then waits. Nothing here can answer it:
the person runs `kernel.py seal` (yes) or `kernel.py decline` (no), and only
then does `settle` read their proof back (kernel.sealed, kernel.declined,
kernel.standing) and move on, writing a `table-beat` row that names the
seal's row. A name, a proposal file that was changed after the seal, or a
seal over a different beat or game moves nothing.

`check` replays the record without the world file: every roll is thrown
again from its seed (dice's check), every `table-beat` names the roll just
before it and adds up, and every ruling names a seal or a decline that holds
under the person's key. Given the world file too, it also checks the
sequence, the stats and the lines against the world.

Exit codes, the kernel's: 0 done (a roll made, a ruling moved past, every
row holds); 42 waiting on the person's seal; 2 refused.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "dice"))
sys.path.insert(0, str(HERE.parent / "odds"))
import dice  # noqa: E402
import kernel  # noqa: E402
import odds  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
DICE = HERE.parent / "dice" / "dice.py"
OPEN, ASK, BEAT = "table-open", "table-ask", "table-beat"
WHO = "game-master"
ROLL = "2d6"
BANDS = (("strong", 10), ("weak", 7), ("miss", None))  # 10+, 7-9, 6-


class WorldError(ValueError):
    """A world file that is not the format; the message says where."""


def band_of(total: int) -> str:
    return "strong" if total >= 10 else "weak" if total >= 7 else "miss"


# ── the world ───────────────────────────────────────────────────────────────
def _need(obj, keys, where):
    if not isinstance(obj, dict):
        raise WorldError(f"{where} must be a JSON object")
    missing = [k for k in keys if k not in obj]
    if missing:
        raise WorldError(f"{where} is missing {missing}")


def _is(value, kind, where):
    ok = (
        isinstance(value, int) and not isinstance(value, bool)
        if kind is int
        else isinstance(value, kind)
    )
    if not ok:
        raise WorldError(f"{where} must be a {kind.__name__}")


def _ids(items, where):
    seen = set()
    for i, it in enumerate(items):
        _need(it, ("id",), f"{where}[{i}]")
        _is(it["id"], str, f"{where}[{i}].id")
        if it["id"] in seen:
            raise WorldError(f"{where}[{i}] repeats the id {it['id']!r}")
        seen.add(it["id"])
    return seen


def validate(world) -> dict:
    """The world, or WorldError naming the first thing wrong and where."""
    _need(world, ("id", "title", "setting", "stats", "base_stat", "characters",
                  "places", "scenes"), "the world")  # fmt: skip
    for k in ("id", "title", "setting"):
        _is(world[k], str, f"world.{k}")
    _is(world["base_stat"], int, "world.base_stat")
    _is(world["stats"], list, "world.stats")
    if not world["stats"] or len(set(world["stats"])) != len(world["stats"]):
        raise WorldError("world.stats is a list of names, none repeated")
    for i, s in enumerate(world["stats"]):
        _is(s, str, f"world.stats[{i}]")
    for key in ("characters", "places", "scenes"):
        _is(world[key], list, f"world.{key}")
        if not world[key]:
            raise WorldError(f"world.{key} must not be empty")
    _ids(world["characters"], "characters")
    for i, c in enumerate(world["characters"]):
        w = f"characters[{i}]"
        _need(c, ("name", "role", "seat", "stats"), w)
        _is(c["name"], str, f"{w}.name")
        _is(c["role"], str, f"{w}.role")
        _is(c["seat"], bool, f"{w}.seat")
        _is(c["stats"], dict, f"{w}.stats")
        for name, v in c["stats"].items():
            if name not in world["stats"]:
                raise WorldError(f"{w}.stats names {name!r}, not one of the stats")
            _is(v, int, f"{w}.stats[{name!r}]")
    if not any(c["seat"] for c in world["characters"]):
        raise WorldError("a character must have seat: true; no one plays this world")
    places = _ids(world["places"], "places")
    for i, p in enumerate(world["places"]):
        _need(p, ("name",), f"places[{i}]")
        _is(p["name"], str, f"places[{i}].name")
    _ids(world["scenes"], "scenes")
    for i, sc in enumerate(world["scenes"]):
        w = f"scenes[{i}]"
        _need(sc, ("title", "place", "opening", "beats"), w)
        _is(sc["title"], str, f"{w}.title")
        if sc["place"] not in places:
            raise WorldError(f"{w}.place {sc['place']!r} is not one of the places")
        _is(sc["opening"], list, f"{w}.opening")
        for j, line in enumerate(sc["opening"]):
            _is(line, str, f"{w}.opening[{j}]")
        _is(sc["beats"], list, f"{w}.beats")
        if not sc["beats"]:
            raise WorldError(f"{w}.beats must not be empty")
        _ids(sc["beats"], f"{w}.beats")
        for j, b in enumerate(sc["beats"]):
            bw = f"{w}.beats[{j}]"
            _need(b, ("kind", "prompt"), bw)
            _is(b["prompt"], str, f"{bw}.prompt")
            if b["kind"] == "action":
                _need(b, ("suggests", "outcomes"), bw)
                if b["suggests"] not in world["stats"]:
                    raise WorldError(f"{bw}.suggests {b['suggests']!r} is not a stat")
                _need(b["outcomes"], [n for n, _ in BANDS], f"{bw}.outcomes")
                for n, _ in BANDS:
                    _is(b["outcomes"][n], str, f"{bw}.outcomes.{n}")
            elif b["kind"] == "decision":
                _need(b, ("proposes",), bw)
                _need(b["proposes"], ("fact", "proposed_by"), f"{bw}.proposes")
                _is(b["proposes"]["fact"], str, f"{bw}.proposes.fact")
                _is(b["proposes"]["proposed_by"], str, f"{bw}.proposes.proposed_by")
            else:
                raise WorldError(
                    f"{bw}.kind {b['kind']!r}: this reads 'action' and 'decision' beats only"
                )
    return world


def load_world(path: Path) -> dict:
    try:
        world = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise WorldError(f"{path} can't be read as JSON: {e}") from None
    return validate(world)


def world_sha(world: dict) -> str:
    return kernel.h256(kernel.canon(world))


def flat(world: dict) -> list[tuple[dict, dict]]:
    return [(sc, b) for sc in world["scenes"] for b in sc["beats"]]


def seated(world: dict) -> list[dict]:
    return [c for c in world["characters"] if c["seat"]]


def stat_of(world: dict, char: dict, stat: str) -> int:
    return char["stats"].get(stat, world["base_stat"])


# ── what the record says ────────────────────────────────────────────────────
def ruling(
    box: Path, rows: list[dict], subj: str
) -> tuple[str, dict] | tuple[str, str]:
    """('sealed' | 'declined', the person's row) while its proof holds; or
    ('broken', why) for a seal whose proposal file is not what was sealed;
    or ('open', '') while the person has said nothing."""
    yes, no = kernel.sealed(box, rows).get(subj), kernel.declined(box, rows).get(subj)
    if yes and (not no or yes["n"] < no["n"]):
        why = kernel.standing(box, rows, subj, yes)[2]
        return ("broken", why) if why else ("sealed", yes)
    if no:
        return "declined", no
    return "open", ""


def games(rows: list[dict], world_id: str | None = None) -> list[dict]:
    """Each game on the record: its open row, then its ask and beat rows."""
    out = {}
    for r in rows:
        if r["kind"] == OPEN and (world_id is None or r.get("world") == world_id):
            out[r["n"]] = {"open": r, "asks": [], "beats": []}
        elif r["kind"] in (ASK, BEAT) and r.get("game") in out:
            out[r["game"]]["asks" if r["kind"] == ASK else "beats"].append(r)
    return list(out.values())


def finished(game: dict, world: dict) -> bool:
    return len(game["beats"]) == len(flat(world))


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def seen_by(world: dict, k: int) -> dict:
    return seated(world)[k % len(seated(world))]


def line(world: dict, game: dict) -> str:
    return f"{world['title']} (game opened at row {game['open']['n']})"


# ── the game's one state: how many beats are done ───────────────────────────
def now_in(world: dict, game: dict) -> tuple[dict, dict, dict]:
    k = len(game["beats"])
    sc, b = flat(world)[k]
    return sc, b, seen_by(world, k)


def entering(world: dict, before: int, after: int) -> list[str]:
    """The lines a scene opens with when beat `after` starts a new scene."""
    fl = flat(world)
    if after >= len(fl) or (before >= 0 and fl[before][0] is fl[after][0]):
        return []
    sc = fl[after][0]
    return [f"-- {sc['title']} --", *sc["opening"]]


def band_lines(world: dict, char: dict, stat: str, mark: str = " ") -> str:
    bonus = stat_of(world, char, stat)
    got = odds.bands(
        odds.distribution(f"{ROLL}+{bonus}"), [10, 7]
    )  # strong, weak, miss
    parts = [f"{n} {p}" for (n, _), (_, p) in zip(BANDS, got)]
    return f"{mark} {stat:<10} {bonus:+d}   " + "   ".join(parts)


def tally(game: dict) -> str:
    act = [b for b in game["beats"] if b["beat_kind"] == "action"]
    rulings = [b for b in game["beats"] if b["beat_kind"] == "decision"]
    said = "; ".join(f"{b['scene']}::{b['beat']} {b['verdict']}" for b in rulings)
    counts = ", ".join(f"{sum(b['band'] == n for b in act)} {n}" for n, _ in BANDS)
    return f"{len(act)} rolled ({counts}); {len(rulings)} ruled [{said or 'none'}]"


# ── commands ────────────────────────────────────────────────────────────────
def current(box: Path, world: dict):
    """(rows, game, error): the latest game of this world, which must be the
    world on the file."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return rows, None, "the record doesn't verify: " + "; ".join(breaks)
    ours = games(rows, world["id"])
    if not ours:
        return rows, None, f"no game of {world['id']} on this record; open first"
    game = ours[-1]
    if game["open"].get("sha256") != world_sha(world):
        return rows, None, "this world file isn't the one the game opened with"
    return rows, game, None


def cmd_open(box: Path, world: dict, ts: str) -> int:
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    ours = games(rows, world["id"])
    if ours and not finished(ours[-1], world) and ours[-1]["open"].get("sha256") == world_sha(world):  # fmt: skip
        return fail(f"{world['id']} is already open at row {ours[-1]['open']['n']}; play it")  # fmt: skip
    row = kernel.append(box, ts, OPEN, who=WHO, world=world["id"], title=world["title"],
                        sha256=world_sha(world), seats=[c["id"] for c in seated(world)])  # fmt: skip
    print(f"{world['title']}\n{world['setting']}")
    print(*entering(world, -1, 0), sep="\n")
    print(f"(game opened at row {row['n']})")
    return kernel.ALIVE


def cmd_status(box: Path, world: dict) -> int:
    rows, game, err = current(box, world)
    if err:
        return fail(err)
    print(f"{line(world, game)}: {len(game['beats'])} of {len(flat(world))} beats done")
    if finished(game, world):
        print(f"finished: {tally(game)}")
        return kernel.ALIVE
    sc, b, char = now_in(world, game)
    place = next(p["name"] for p in world["places"] if p["id"] == sc["place"])
    print(f"scene {sc['id']} {sc['title']!r} at {place}")
    print(f"beat {b['id']} ({b['kind']}), {char['name']}'s turn: {b['prompt']}")
    if b["kind"] == "action":
        for s in world["stats"]:
            print(band_lines(world, char, s, "*" if s == b["suggests"] else " "))
        return kernel.ALIVE
    asked = [a for a in game["asks"] if (a["scene"], a["beat"]) == (sc["id"], b["id"])]
    if not asked:
        print(f"{b['proposes']['proposed_by']} would propose: {b['proposes']['fact']}")
        print("run ask to hand it in; it moves only on your seal")
        return kernel.ESCALATE
    what, _ = ruling(box, rows, asked[-1]["subject"])
    print(f"proposed as {asked[-1]['subject']}: {what}")
    return kernel.ALIVE if what != "open" else kernel.ESCALATE


def cmd_act(box: Path, world: dict, stat: str, ts: str) -> int:
    rows, game, err = current(box, world)
    if err:
        return fail(err)
    if finished(game, world):
        return fail("the story is finished")
    sc, b, char = now_in(world, game)
    if b["kind"] != "action":
        return fail(f"beat {b['id']} is a decision: it has no roll; ask, then wait for your seal")  # fmt: skip
    if stat not in world["stats"]:
        return fail(f"{stat!r} isn't a stat here: {', '.join(world['stats'])}")
    k = len(game["beats"])
    got = subprocess.run([sys.executable, str(DICE), "--box", str(box), "roll", ROLL, "--now", ts],
                         capture_output=True, text=True)  # fmt: skip
    rows, breaks = kernel.read(box / "record.jsonl")
    roll = rows[-1] if rows else {}
    if got.returncode != 0 or breaks or roll.get("kind") != "roll":
        return fail("dice refused the roll: " + (got.stderr or got.stdout).strip())
    bonus = stat_of(world, char, stat)
    total = roll["total"] + bonus
    band = band_of(total)
    row = kernel.append(box, ts, BEAT, who=WHO, game=game["open"]["n"], beat_kind="action",
                        scene=sc["id"], beat=b["id"], character=char["id"], stat=stat,
                        bonus=bonus, roll_row=roll["n"], roll=roll["total"], total=total,
                        band=band, text=b["outcomes"][band])  # fmt: skip
    print(f"{char['name']} tries {stat}: {dice.said(roll)}, {bonus:+d} {stat} = {total}: {band}   (rows {roll['n']}, {row['n']})")  # fmt: skip
    print(b["outcomes"][band])
    for text in entering(world, k, k + 1):
        print(text)
    if k + 1 == len(flat(world)):
        print(f"finished: {tally({**game, 'beats': [*game['beats'], row]})}")
    return kernel.ALIVE


def cmd_ask(box: Path, world: dict, ts: str) -> int:
    rows, game, err = current(box, world)
    if err:
        return fail(err)
    if finished(game, world):
        return fail("the story is finished")
    sc, b, char = now_in(world, game)
    if b["kind"] != "decision":
        return fail(f"beat {b['id']} is an action: act on it")
    if any((a["scene"], a["beat"]) == (sc["id"], b["id"]) for a in game["asks"]):
        return fail(f"{sc['id']}::{b['id']} is already asked; settle it once you've sealed or declined")  # fmt: skip
    p, n = b["proposes"], game["open"]["n"]
    prop = {"path": f"game/{world['id']}/{n}/{sc['id']}-{b['id']}.txt", "data": p["fact"],
            "cites": [], "claim": f"{p['proposed_by']} proposes this at {sc['id']}::{b['id']} of {world['id']} (game opened at row {n}): {b['prompt']}"}  # fmt: skip
    question = f"game-master {world['id']} {sc['id']}::{b['id']} game {n}"
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "proposal.jsonl"
        f.write_text(json.dumps(prop) + "\n", encoding="utf-8")
        for argv in (["bite", question], ["propose", "--file", str(f)]):
            done = subprocess.run([sys.executable, str(KERNEL), argv[0], "--box", str(box), "--now", ts, *argv[1:]],
                                  capture_output=True, text=True)  # fmt: skip
            if done.returncode == kernel.REFUSED:
                return fail(f"the kernel's {argv[0]}: {done.stderr.strip()}")
    subj = kernel.subject_of(prop)
    if f"pass  {subj}" not in done.stdout:
        return fail("the kernel's door refused the proposal: " + done.stdout.strip())
    row = kernel.append(box, ts, ASK, who=WHO, game=n, scene=sc["id"], beat=b["id"],
                        subject=subj, proposed_by=p["proposed_by"], fact=p["fact"])  # fmt: skip
    print(f"{p['proposed_by']} proposes: {p['fact']}")
    print(f"handed in as {subj} (row {row['n']}); it waits on you:")
    print(f"  python kernel.py seal --box {box} {subj}      (yes)")
    print(f"  python kernel.py decline --box {box} {subj}   (no)")
    return kernel.ESCALATE


def cmd_settle(box: Path, world: dict, ts: str) -> int:
    rows, game, err = current(box, world)
    if err:
        return fail(err)
    if finished(game, world):
        return fail("the story is finished")
    sc, b, char = now_in(world, game)
    asked = [a for a in game["asks"] if (a["scene"], a["beat"]) == (sc["id"], b["id"])]
    if b["kind"] != "decision" or not asked:
        return fail(f"beat {b['id']} has no proposal to settle; " + ("ask first" if b["kind"] == "decision" else "act on it"))  # fmt: skip
    subj = asked[-1]["subject"]
    what, got = ruling(box, rows, subj)
    if what == "broken":
        return fail(f"{subj} was sealed, but its proposal file {got}; nothing moves")
    if what == "open":
        print(f"{subj} waits on your seal or your decline; nothing moves.")
        return kernel.ESCALATE
    k = len(game["beats"])
    row = kernel.append(box, ts, BEAT, who=WHO, game=game["open"]["n"], beat_kind="decision",
                        scene=sc["id"], beat=b["id"], subject=subj, verdict=what,
                        ruling_row=got["n"], proposed_by=b["proposes"]["proposed_by"])  # fmt: skip
    print(f"{sc['id']}::{b['id']}: you {'sealed' if what == 'sealed' else 'declined'} it (row {got['n']}); recorded at row {row['n']}")  # fmt: skip
    for text in entering(world, k, k + 1):
        print(text)
    if k + 1 == len(flat(world)):
        print(f"finished: {tally({**game, 'beats': [*game['beats'], row]})}")
    return kernel.ALIVE


def check_game(
    box: Path, rows: list[dict], game: dict, world: dict | None
) -> str | None:
    """Why this game's rows don't hold, or None."""
    opened = game["open"]
    if world is not None and opened.get("sha256") != world_sha(world):
        return (
            f"game at row {opened['n']}: this world file isn't the one it opened with"
        )
    fl = flat(world) if world else None
    for k, r in enumerate(game["beats"]):
        at, where = r["n"], f"row {r['n']}"
        if r["n"] < opened["n"]:
            return f"{where}: before its game opened"
        if fl is not None:
            if k >= len(fl) or (r.get("scene"), r.get("beat")) != (fl[k][0]["id"], fl[k][1]["id"]):  # fmt: skip
                return f"{where}: not the beat the world has at place {k}"
            sc, b = fl[k]
            if r.get("beat_kind") != b["kind"]:
                return f"{where}: a {r.get('beat_kind')} row on a {b['kind']} beat"
        if r.get("beat_kind") == "action":
            roll = rows[at - 1] if at else {}
            if roll.get("kind") != "roll" or roll.get("dice") != ROLL or r.get("roll_row") != at - 1:  # fmt: skip
                return f"{where}: not straight after a {ROLL} roll it names"
            if r.get("roll") != roll["total"] or r.get("total") != roll["total"] + r.get("bonus", 0):  # fmt: skip
                return f"{where}: its total isn't the roll plus the stat"
            if r.get("band") != band_of(r["total"]):
                return f"{where}: {r['total']} isn't {r.get('band')}"
            if world is not None:
                char = seen_by(world, k)
                if (
                    r.get("character") != char["id"]
                    or r.get("stat") not in world["stats"]
                ):
                    return f"{where}: not {char['id']}'s turn or not a stat"
                if r["bonus"] != stat_of(world, char, r["stat"]) or r.get("text") != b["outcomes"][r["band"]]:  # fmt: skip
                    return f"{where}: its stat or its line isn't the world's"
        elif r.get("beat_kind") == "decision":
            ask = next((a for a in game["asks"] if a.get("subject") == r.get("subject")
                        and (a["scene"], a["beat"]) == (r.get("scene"), r.get("beat"))
                        and a["n"] < at), None)  # fmt: skip
            if ask is None:
                return f"{where}: a ruling with no proposal handed in before it"
            if not any(p["kind"] == "proposal" and p.get("subject") == r["subject"]
                       and p.get("verdict") == "pass" and p["n"] < ask["n"] for p in rows):  # fmt: skip
                return f"{where}: the kernel never passed {r['subject']}"
            what, got = ruling(box, rows, r["subject"])
            if what in ("open", "broken") or got["n"] != r.get("ruling_row") or r.get("verdict") != what or got["n"] >= at:  # fmt: skip
                return f"{where}: no {r.get('verdict')} of {r['subject']} by the person's key stands behind it"  # fmt: skip
            if world is not None and b["proposes"]["fact"] != ask.get("fact"):
                return f"{where}: the fact handed in isn't the world's"
        else:
            return f"{where}: neither an action nor a decision"
    return None


def cmd_check(box: Path, world: dict | None) -> int:
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return fail("the record doesn't verify: " + "; ".join(breaks))
    held, why = dice.check(rows)
    if why:
        return fail(f"{why} ({held} rolls before it held)")
    mine = games(rows, world["id"] if world else None)
    for g in mine:
        theirs = world if world and g["open"].get("world") == world["id"] else None
        if why := check_game(box, rows, g, theirs):
            return fail(why)
    beats = sum(len(g["beats"]) for g in mine)
    print(f"{len(mine)} game{'s' if len(mine) != 1 else ''}, {beats} beat{'s' if beats != 1 else ''}, "  # fmt: skip
          f"{held} roll{'s' if held != 1 else ''} on the record; every one holds.")  # fmt: skip
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--world", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if args else ""
    shape = verb in ("open", "status", "ask", "settle", "check") and len(args) == 1
    if not opts.get("--box") or not (shape or (verb == "act" and len(args) == 2)):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if verb != "check" and not opts.get("--world"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return fail("not a kernel box; init first")
    try:
        world = load_world(Path(opts["--world"])) if opts.get("--world") else None
    except WorldError as e:
        return fail(str(e))
    ts = opts.get("--now") or kernel.now()
    if verb == "check":
        return cmd_check(box, world)
    if verb == "open":
        return cmd_open(box, world, ts)
    if verb == "status":
        return cmd_status(box, world)
    if verb == "act":
        return cmd_act(box, world, args[1], ts)
    return (cmd_ask if verb == "ask" else cmd_settle)(box, world, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
