"""board.py: a fight drawn from its rows: who's hurt, who's down, whose turn. Python 3.9+.

Came in from Die-Namic's ``box/board.py`` (514823c), reading play-fight5e's
row kinds in place of Die-Namic's fight.py's.

A fight play_fight5e.py kept is every blow a row, and each row's state says what
changed: an attack and the hit points it left, a save and its damage, a
fall, a stun, a turn lost. That is enough to draw the fight as it stood
at the end of any round, with nothing played again and no dice: the
fighters come from the encounter's own stat blocks (aetheris5e's
statblocks.py, plain data), and every change after that from the rows.

    ⚔️  the party ambushed by 4 Scorched Belt Raiders, round 2 of 4

      The party                          Their side
      Sena Koll       ██████░░░░ 12/20   Raider #1      ░░░░░░░░░░  0/22  ✖ down
      ...

      Turn order: Sena Koll ▶ Raider #3 · Tide-touched Scout · ...

It reads the rows and draws; it writes nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import statblocks  # noqa: E402

OPEN, BLOW, END = "encounter-open", "encounter-blow", "encounter-end"
WIDE = 10  # an HP bar's cells


def fighters(encounter: str) -> list[dict]:
    """Each fighter as the fight began: name, side, hp, max_hp, ac."""
    return [
        {
            "name": c["name"],
            "side": c["side"],
            "hp": c["hp"],
            "max_hp": c["max_hp"],
            "ac": c["ac"],
            "down": False,
            "stunned": False,
            "blinded": False,
        }
        for c in statblocks.build_encounter(encounter)
    ]


def state(rows: list[dict], fight: int, upto: int | None = None) -> dict:
    """The fight opened at row FIGHT as it stood after round UPTO (its end
    if None): {desc, round, rounds, order, next, fighters, outcome}."""
    opened = next(r for r in rows if r["kind"] == OPEN and r["n"] == fight)
    who = {f["name"]: f for f in fighters(opened["encounter"])}
    order: list[str] = []
    rnd, last = 0, None
    for r in rows:
        if r.get("fight") != fight or r["kind"] != BLOW:
            continue
        s = r["state"]
        k = s.get("kind")
        if k == "round":
            if upto is not None and s["n"] > upto:
                break
            rnd = s["n"]
            for f in who.values():
                f["blinded"] = False  # a blinding lasts its round
        elif k == "initiative":
            order = list(s["order"])
        elif k == "attack":
            last = s["by"]
            if s.get("hit") and s["vs"] in who:
                who[s["vs"]]["hp"] = s["target_hp"]
        elif k in ("save", "overheat") and s.get("who") in who:
            if "hp" in s:
                who[s["who"]]["hp"] = s["hp"]
            if s.get("effect") == "stun":
                who[s["who"]]["stunned"] = True
            if s.get("effect") == "blind":
                who[s["who"]]["blinded"] = True
        elif k == "stunned_skip" and s.get("who") in who:
            who[s["who"]]["stunned"] = False
            last = s["who"]
        elif k == "down" and s.get("who") in who:
            who[s["who"]]["down"] = True
            who[s["who"]]["hp"] = 0
        elif k in ("special", "action_surge"):
            last = s.get("by") or s.get("who") or last
    ended = next(
        (r for r in rows if r["kind"] == END and r.get("fight") == fight), None
    )
    rounds = ended["result"]["rounds"] if ended else rnd
    up = [n for n in order if not who.get(n, {}).get("down")]
    nxt = None
    if last in order and up:
        k = order.index(last)
        nxt = next((order[(k + i) % len(order)] for i in range(1, len(order) + 1) if order[(k + i) % len(order)] in up), None)  # fmt: skip
    done = ended is not None and (upto is None or upto >= rounds)
    return {"desc": opened.get("desc") or opened["encounter"], "round": rnd, "rounds": rounds, "order": order,
            "next": None if done else nxt, "fighters": list(who.values()),
            "outcome": ended["result"]["outcome"] if done else None}  # fmt: skip


def bar(hp: int, most: int) -> str:
    full = round(WIDE * hp / most) if most else 0
    full = 1 if hp > 0 and full == 0 else full  # standing is never an empty bar
    return "█" * full + "░" * (WIDE - full)


def line(f: dict, w: int) -> str:
    tags = ["✖ down"] if f["down"] else [t for t in ("stunned", "blinded") if f[t]]
    hp = f"{f['hp']:>3}/{f['max_hp']:<3}"
    return (f"{f['name']:<{w}} {bar(f['hp'], f['max_hp'])} {hp}" + (f" {' '.join(tags)}" if tags else "")).rstrip()  # fmt: skip


def draw(s: dict) -> str:
    """The board, as text a table can read across."""
    said = {"party": "the party won", "foe": "the party fell", "stalemate": "neither side fell"}  # fmt: skip
    head = f"⚔️  {s['desc']}, round {s['round']} of {s['rounds']}" + (f": {said.get(s['outcome'], s['outcome'])}" if s["outcome"] else "")  # fmt: skip
    w = max(len(f["name"]) for f in s["fighters"])
    party = [line(f, w) for f in s["fighters"] if f["side"] == "party"]
    foes = [line(f, w) for f in s["fighters"] if f["side"] == "foe"]
    out = [head, "", "  The party", *[f"    {x}" for x in party], "", "  Their side", *[f"    {x}" for x in foes]]  # fmt: skip
    if s["order"]:
        down = {f["name"] for f in s["fighters"] if f["down"]}
        names = [("▶ " if n == s["next"] else "") + n + (" ✖" if n in down else "") for n in s["order"]]  # fmt: skip
        out += ["", "  Turn order: " + " · ".join(names)]
    return "\n".join(out)
