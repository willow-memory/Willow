"""combat.py -- a real 5e combat engine for the Aetheris table. Python 3.9+.

Came in from Die-Namic's ``the-table/aetheris5e/combat.py`` (514823c), its
rules unchanged: initiative (d20+init, stable), multiattack, attack vs AC
with advantage/disadvantage from blindness, nat-20 crit (double damage dice),
damage resistance (typed + the Warden's nonmagical-weapon halving), recharge
abilities (d6 at start of turn, recharge on 5-6), AoE saves (full/half or a
condition), Override-Pulse stun, Salt-Spray blind, the Bruiser's Overheat
self-hazard, the Rogue's once-per-turn Sneak Attack, and the Fighter's Action
Surge + one superiority die. Gridless: everyone is "in range". Drop at 0 HP
(no death saves). Round cap 50 -> declared a stalemate.

The engine OWNS no dice: every roll draws from the ``random.Random`` it is
handed. play_fight5e.py hands it one whose every draw is a die from the
tower; ``simulate`` hands it ``random.Random(i)`` for round i of a sweep, so a
balance run is reproducible and is never a fight on the record. A fight's
events go to the ``sink`` it is given (``sink.snapshot(state, note=)``); the
engine writes nothing itself.

What was left behind: the one-script record (``the_table.host``) and the
``fight`` mode that wrote to it; play_fight5e.py keeps a fight on the
kernel's record instead.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import statblocks  # noqa: E402

# dice notation is the MIT `dice` library's, through the dice5e seam
from dice5e import crit_expr as _double_dice  # noqa: E402
from dice5e import d20  # noqa: E402
from dice5e import total as roll  # noqa: E402


# ── engine ───────────────────────────────────────────────────────────────────


class Combat:
    def __init__(self, combatants, rng: random.Random, sink=None, log=None):
        self.cs = combatants
        self.rng = rng
        self.sink = sink
        self.log = log or (lambda *_: None)
        self.round = 0

    def living(self, side=None):
        return [
            c for c in self.cs if c["hp"] > 0 and (side is None or c["side"] == side)
        ]

    def _record(self, note, state):
        self.log(note)
        if self.sink is not None:
            self.sink.snapshot(state, note=note)

    def _resisted(self, target, dmg, dtype, magical):
        bps = {"bludgeoning", "piercing", "slashing"}
        if dtype in target["resist_types"]:
            return dmg // 2, True
        if target.get("resist_nonmagical_bps") and dtype in bps and not magical:
            return dmg // 2, True
        return dmg, False

    def _apply_damage(self, target, dmg, dtype, magical):
        dmg, resisted = self._resisted(target, dmg, dtype, magical)
        target["hp"] = max(0, target["hp"] - dmg)
        return dmg, resisted

    def attack(self, attacker, target, atk):
        adv = target["blind_turns"] > 0  # blinded target -> attackers have advantage
        dis = attacker["blind_turns"] > 0  # blinded attacker -> disadvantage
        total, nat = d20(self.rng, atk["atk"], adv=adv, dis=dis)
        if nat != 20 and (nat == 1 or total < target["ac"]):
            self._record(
                f"{attacker['name']} misses {target['name']} with {atk['name']} "
                f"(d20={total} vs AC {target['ac']})",
                {
                    "kind": "attack",
                    "by": attacker["name"],
                    "vs": target["name"],
                    "atk": atk["name"],
                    "total": total,
                    "hit": False,
                },
            )
            return
        crit = nat == 20
        dmg = roll(_double_dice(atk["dmg"]) if crit else atk["dmg"], self.rng)
        extra = ""
        # Sneak Attack: once per turn, on a hit, if the attacker has it.
        if attacker.get("sneak_attack") and not attacker["used_sneak_this_turn"]:
            sa_expr = (
                _double_dice(attacker["sneak_attack"])
                if crit
                else attacker["sneak_attack"]
            )
            sa = roll(sa_expr, self.rng)
            dmg += sa
            attacker["used_sneak_this_turn"] = True
            extra += f" +sneak {sa}"
        # One superiority die (Battle Master) on a hit while dice remain.
        if attacker.get("sup_dice", 0) > 0:
            sd = roll("1d8", self.rng)
            dmg += sd
            attacker["sup_dice"] -= 1
            extra += f" +superiority {sd}"
        dealt, resisted = self._apply_damage(target, dmg, atk["type"], atk["magical"])
        tag = f"{' CRIT' if crit else ''}{' (resisted)' if resisted else ''}"
        self._record(
            f"{attacker['name']} hits {target['name']} with {atk['name']} for {dealt}{tag}"
            f"{extra} (d20={total} vs AC {target['ac']}); {target['name']} at {target['hp']}/{target['max_hp']}",
            {
                "kind": "attack",
                "by": attacker["name"],
                "vs": target["name"],
                "atk": atk["name"],
                "total": total,
                "hit": True,
                "crit": crit,
                "dmg": dealt,
                "resisted": resisted,
                "target_hp": target["hp"],
            },
        )
        if target["hp"] == 0:
            self._record(
                f"{target['name']} falls.", {"kind": "down", "who": target["name"]}
            )

    def save(self, creature, ability, dc, disadvantage=False):
        total, nat = d20(self.rng, creature["saves"].get(ability, 0), dis=disadvantage)
        return (nat == 20 or (nat != 1 and total >= dc)), total

    def use_aoe(self, attacker, special):
        targets = self.living("party" if attacker["side"] == "foe" else "foe")
        eff = special["effect"]
        self._record(
            f"{attacker['name']} uses {special['name']} — {special['flavor']}",
            {"kind": "special", "by": attacker["name"], "name": special["name"]},
        )
        for t in targets:
            disadv = special.get("aether_implant_disadv") and t.get("aether_implant")
            saved, total = self.save(
                t, special["save"], special["dc"], disadvantage=disadv
            )
            if eff == "damage":
                dmg = roll(special["dmg"], self.rng)
                if saved and special.get("half_on_save"):
                    dmg //= 2
                dealt, resisted = self._apply_damage(
                    t, dmg, special.get("type", "force"), True
                )
                self._record(
                    f"  {t['name']} {'saves' if saved else 'FAILS'} ({total} vs DC {special['dc']}) "
                    f"— takes {dealt}{' (resisted)' if resisted else ''}; {t['hp']}/{t['max_hp']}",
                    {
                        "kind": "save",
                        "who": t["name"],
                        "vs": special["name"],
                        "saved": saved,
                        "dmg": dealt,
                        "hp": t["hp"],
                    },
                )
                if t["hp"] == 0:
                    self._record(
                        f"  {t['name']} falls.", {"kind": "down", "who": t["name"]}
                    )
            else:
                if not saved:
                    if eff == "stun":
                        t["skip_turns"] = max(t["skip_turns"], 1)
                    elif eff == "blind":
                        t["blind_turns"] = max(t["blind_turns"], 2)
                past = {"stun": "stunned", "blind": "blinded"}.get(eff, eff)
                self._record(
                    f"  {t['name']} {'saves' if saved else 'FAILS — ' + past} "
                    f"({total} vs DC {special['dc']})",
                    {
                        "kind": "save",
                        "who": t["name"],
                        "vs": special["name"],
                        "saved": saved,
                        "effect": None if saved else eff,
                    },
                )

    def _pick_target(self, attacker):
        foes = self.living("party" if attacker["side"] == "foe" else "foe")
        return min(foes, key=lambda c: c["hp"]) if foes else None

    def take_turn(self, c):
        if c["hp"] <= 0:
            return
        # recharge specials
        for sp in c["specials"]:
            if sp.get("recharge") and not sp.get("available"):
                if roll("1d6", self.rng) >= 5:
                    sp["available"] = True
        # stun: skip a turn
        if c["skip_turns"] > 0:
            c["skip_turns"] -= 1
            self._record(
                f"{c['name']} is stunned and loses its turn.",
                {"kind": "stunned_skip", "who": c["name"]},
            )
            return
        c["used_sneak_this_turn"] = False
        # Overheat self-hazard (Bruiser) at start of turn if below half.
        for sp in c["specials"]:
            if sp.get("self_hazard") and c["hp"] * 2 < c["max_hp"]:
                saved, total = self.save(c, sp["save"], sp["dc"])
                if not saved:
                    dmg = roll(sp["dmg"], self.rng)
                    c["hp"] = max(0, c["hp"] - dmg)
                    self._record(
                        f"{c['name']} overheats — {dmg} force ({c['hp']}/{c['max_hp']})",
                        {
                            "kind": "overheat",
                            "who": c["name"],
                            "dmg": dmg,
                            "hp": c["hp"],
                        },
                    )
                    if c["hp"] == 0:
                        self._record(
                            f"{c['name']} burns out.",
                            {"kind": "down", "who": c["name"]},
                        )
                        return

        def _act():
            # Prefer an available AoE special when it hits 2+ enemies.
            enemies = self.living("party" if c["side"] == "foe" else "foe")
            for sp in c["specials"]:
                if (
                    sp.get("shape") == "aoe"
                    and sp.get("available")
                    and len(enemies) >= 2
                ):
                    self.use_aoe(c, sp)
                    if sp.get("recharge"):
                        sp["available"] = False
                    return
            melee = c["attacks"][0]
            for _ in range(c["multiattack"]):
                target = self._pick_target(c)
                if target is None:
                    return
                self.attack(c, target, melee)

        _act()
        # Action Surge: a second action, once.
        if c.get("action_surge") and self.living(
            "party" if c["side"] == "foe" else "foe"
        ):
            c["action_surge"] = False
            self._record(
                f"{c['name']} uses Action Surge — a second action.",
                {"kind": "action_surge", "who": c["name"]},
            )
            _act()
        if c["blind_turns"] > 0:
            c["blind_turns"] -= 1

    def run(self, cap=50):
        order = sorted(
            self.cs,
            key=lambda c: (d20(self.rng, c["init"])[0], c["init"]),
            reverse=True,
        )
        self._record(
            "initiative: " + ", ".join(c["name"] for c in order),
            {"kind": "initiative", "order": [c["name"] for c in order]},
        )
        while self.living("party") and self.living("foe") and self.round < cap:
            self.round += 1
            self._record(f"— round {self.round} —", {"kind": "round", "n": self.round})
            for c in order:
                if not (self.living("party") and self.living("foe")):
                    break
                self.take_turn(c)
        party, foe = self.living("party"), self.living("foe")
        if party and not foe:
            outcome = "party"
        elif foe and not party:
            outcome = "foe"
        else:
            outcome = "stalemate"
        return {
            "outcome": outcome,
            "rounds": self.round,
            "party_survivors": [c["name"] for c in party],
            "foe_survivors": [c["name"] for c in foe],
        }


# ── modes ────────────────────────────────────────────────────────────────────


def simulate(encounter: str, rounds: int) -> dict:
    wins = {"party": 0, "foe": 0, "stalemate": 0}
    total_rounds = 0
    party_surv = 0
    tpk = 0
    n_party = len([1 for _ in statblocks.ENCOUNTERS[encounter]["party"]])
    for seed in range(rounds):
        cs = statblocks.build_encounter(encounter)
        res = Combat(cs, random.Random(seed)).run()
        wins[res["outcome"]] += 1
        total_rounds += res["rounds"]
        party_surv += len(res["party_survivors"])
        if not res["party_survivors"]:
            tpk += 1
    return {
        "encounter": encounter,
        "runs": rounds,
        "wins": wins,
        "avg_rounds": total_rounds / rounds,
        "avg_party_survivors": party_surv / rounds,
        "party_size": n_party,
        "tpk": tpk,
    }


def _fmt_sim(s):
    r = s["runs"]
    L = [
        "=" * 70,
        f"AETHERIS 5e COMBAT · {s['encounter']} · {r} runs · seeds 0..{r - 1}",
        f"  {statblocks.ENCOUNTERS[s['encounter']]['desc']}",
        "=" * 70,
        f"  party wins : {s['wins']['party']:4d}  ({100 * s['wins']['party'] / r:5.1f}%)  "
        + "█" * round(40 * s["wins"]["party"] / r),
        f"  party loss : {s['wins']['foe']:4d}  ({100 * s['wins']['foe'] / r:5.1f}%)",
        f"  stalemate  : {s['wins']['stalemate']:4d}  ({100 * s['wins']['stalemate'] / r:5.1f}%)",
        f"  avg rounds : {s['avg_rounds']:.1f}",
        f"  avg party survivors: {s['avg_party_survivors']:.2f} of {s['party_size']}",
        f"  total party wipes (TPK): {s['tpk']}  ({100 * s['tpk'] / r:.1f}%)",
        "=" * 70,
    ]
    return "\n".join(L)
