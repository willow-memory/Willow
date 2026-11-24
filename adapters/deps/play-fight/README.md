<!-- willow-addon
section: Play
line: A fight blow by blow on dice dropped in the tower, every blow a row, played again from the record to check it.
source: new
added: 2026-11-23
version: 0.1.0
needs: dndwright, which brings pydantic and PyYAML; MIT
floor: dndwright 0.5.0; the rule names 0.2.0, its first release, but the dice engine came in 0.3.0 and the combat and initiative rules in 0.5.0
writes: record, to
network: none
role: tools
uses: dice-tower
from: dep, https://github.com/sligara7/dndwright, MIT; shape, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0
-->
# play-fight

A fight at the table, blow by blow, the way the rules say, on dice nobody
chose: each die dropped in [dice-tower](../../stdlib/dice-tower/) before it is
thrown, and every blow a row on the record that a later check plays again.

    pip install -r adapters/deps/play-fight/requirements.txt
    python adapters/deps/play-fight/play_fight.py --box DIR fight --fighters <fighters>.json --to <dice folder>
    round 1: Tamsin attacks Raider, 22 against armor 12: 8 damage, Raider at 3
    round 1: Raider attacks Tamsin, 4 against armor 13: a miss
    ...
    the party side won in round 2

    python adapters/deps/play-fight/play_fight.py --box DIR check
    1 fight on the record, every one holds

**The fighters** are a JSON list, one object each:

    [{"name": "Tamsin", "side": "party", "hp": 14, "ac": 13, "init_mod": 0,
      "attack_bonus": 4, "damage": "1d6+2"},
     {"name": "Raider", "side": "foes", "hp": 11, "ac": 12, "init_mod": 1,
      "attack_bonus": 3, "damage": "1d6+1", "attacks": 2}]

`side` is `party` or `foes`; `attacks` is blows a turn, 1 if left out. A
field a fighter hasn't, one missing, a number that isn't whole, damage that
isn't dice, two fighters of one name, or a side with nobody on it is refused
by name, and nothing is written. Where the numbers come from (a story's own
characters, a stat block) is the table's to say: this takes them as given.

**The rules** are [dndwright](https://github.com/sligara7/dndwright)'s:
initiative, an attack roll against armor class, damage on a hit, the dice
doubled on a natural 20, a miss on a natural 1, a fighter down at 0 hit
points. Whom a fighter hits is the first one standing on the other side, in
the order the file lists them. The fight ends in the round the last of a side
goes down, or as a `stalemate` after 20 rounds. dndwright rolls through a
generator it is handed; here that generator is the tower, so it has no dice
of its own to fall back on.

**On the record:**

| Row | What it holds |
|---|---|
| `fight-begin` | the fighters, whole, and the dndwright version that ran the fight |
| `tower-drop`, `tower-out` | the tower's own, one pair a die, each drop saying what the die is for ("Tamsin attacks Raider") |
| `fight-row` | one per thing that happened, `init`, `blow`, `down` or `end`, under `row`; `fight` is the begin row's number, `dice` the tower rows its faces came from |

**`check` reads the record alone.** The kernel's chain holds. Every die out
of the tower holds to its drop, and none is left inside. Each fight row's
faces are the faces the tower brought out at the rows it names, from dice
dropped after the fight began, and no die is used twice. And the fight, played
again on those faces with the fighters its begin row names, comes out as
written. A blow changed in the file breaks the chain; a row written to a sound
chain with a blow changed, a face the tower didn't bring out, a row with no
tower dice behind it, a die used twice or dropped before the fight, and a fight
with no end are each refused, saying which row. A fight played again on
another dndwright than the one that wrote it says both when it differs.

**Limits, said plainly.** A die is dropped and brought out in the same
breath, when the engine asks for it: no one foresees or steers it, but the
moment between the drop and the out is not one held up to the table. Whoever
holds the die folder can look inside a die before it is out, as the tower's
own card says. No conditions, death saves, reactions, advantage, or a map.

**Needs:** dndwright 0.29.0 (MIT), pinned in [requirements.txt](requirements.txt),
which brings pydantic and PyYAML and needs Python 3.10 or newer (the kernel
itself runs on 3.9). Without it, every command refuses and names the install.
At its floor, 0.5.0, the same tests pass.

**Source:** Die-Namic's spike of a fight on dndwright, on the tower, on the
record, rebuilt here as an add-on, with each row naming the dice behind it in
place of the spike's rule that nothing else may use the tower during a fight.

**Uses:** [dice-tower](../../stdlib/dice-tower/)'s `drop`, `out` and `check`;
the kernel's `append` and `read`.

**Never:** proposes, seals, reads your key, writes a die file over another,
makes a folder, or goes online.
