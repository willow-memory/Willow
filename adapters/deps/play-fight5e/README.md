<!-- willow-addon
section: Play
line: Tabletop combat run from stat blocks on dice5e's rolls, every attack on the record and replayable.
source: new
added: 2026-11-23
version: 0.1.0
needs: dice, which brings pyparsing; MIT
floor: dice 3.1.1
writes: record, to
network: none
role: tools
uses: dice-tower, play-dice, play-dice5e
from: code, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0; code, https://github.com/willow-memory/willow-bot, Apache-2.0
-->
# play-fight5e

A 5e fight at the table, with a setting's own stat blocks and named
encounters, by rules that go past an attack and its damage: saves,
resistances, recharging specials, stun and blind, Sneak Attack, Action Surge.
Every die is dropped in [dice-tower](../../stdlib/dice-tower/) before it is
thrown, every blow is a row on the record, and a later check fights the
encounter again from those rows alone.

    pip install -r adapters/deps/play-fight5e/requirements.txt
    python adapters/deps/play-fight5e/play_fight5e.py list
      warden     the full party vs a Mind-Forge Warden (the gallery's guardian wakes)
      enforcers  the party vs a Concord press-gang: 2 Enforcers + an Aether Construct
      raiders    the party ambushed by 4 Scorched Belt Raiders
      bruiser    the party vs an Engine-Blooded Bruiser and a Tide-Touched Scout

    python adapters/deps/play-fight5e/play_fight5e.py --box DIR fight warden --to <dice folder>
    the full party vs a Mind-Forge Warden (the gallery's guardian wakes)   (row 1)
      initiative: Tide-touched Scout, Mind-Forge Warden, Sena Koll, Warforged
      — round 1 —
      Mind-Forge Warden uses Override Pulse — a 15-ft pulse; INT save or stunned
      ...
    PARTY in 5 rounds; standing: Tide-touched Scout, Warforged   (rows 1-143)

    python adapters/deps/play-fight5e/play_fight5e.py --box DIR check
    1 encounter on the record; every blow holds

    python adapters/deps/play-fight5e/play_fight5e.py --box DIR board [--fight ROW] [--round N]
    python adapters/deps/play-fight5e/play_fight5e.py sim raiders [--runs N]

**The rules** are aetheris5e's ([combat.py](combat.py)), kept as they were
where they came from: initiative (d20 plus initiative, stable), multiattack,
an attack against armor class with advantage against a blinded target and
disadvantage for a blinded attacker, a natural 20 doubling the damage dice,
typed resistance (the Bruiser halves force) and the Warden's halving of
nonmagical weapons, recharging specials (a d6 at the start of a turn,
back on 5 or 6), area saves for half damage or a condition (Override
Pulse's stun, Salt Spray's blindness), the Bruiser's Overheat, the Scout's
once-a-turn Sneak Attack, the Warforged's Action Surge and superiority dice.
Gridless: everyone is in range. A fighter drops at 0 hit points, with no
death saves; a fight past 50 rounds is a stalemate. Each attacker strikes
the foe with the fewest hit points.

**The fighters** are [statblocks.py](statblocks.py)'s: the setting's six
stat blocks and three level-3 pregens, in four named encounters. Each is
made fresh for every fight.

**The dice** are the tower's. The engine draws every die through a generator
it is handed; here every draw is a die dropped in the tower and brought out,
so no face is anyone's choice. A draw that isn't a die is refused, so none
comes from anywhere else. Dice notation is the [dice](https://pypi.org/project/dice/)
library's (MIT), through [dice5e.py](dice5e.py)'s seam, which rolls the simple
forms itself on the drawn faces and lets the library validate them.

**On the record:**

| Row | What it holds |
|---|---|
| `encounter-open` | the encounter, its words, and the engine |
| `tower-drop`, `tower-out` | the tower's own, one pair a die |
| `encounter-blow` | one per thing that happened: its words (`note`), what changed (`state`), the fight's open row (`fight`), and the tower rows whose faces it used (`dice`) |
| `encounter-end` | the result: who won, in how many rounds, who stands; and any dice thrown after the last blow |

**`check` reads the record alone.** The kernel's chain holds. Every die out
of the tower holds to its drop, and none is left inside. Each row's dice are
dice out of the tower, dropped after the encounter opened, none used twice.
And the encounter, fought again on those faces, gives every blow and the end
as written, with no die left over. A blow changed in the file breaks the
chain; on a sound chain, a blow changed, dropped or added, an ending lost,
rows with no dice behind them, a die used twice, dropped before the
encounter, or left over, and a die still in the tower are each refused,
saying which row.

**`board`** draws a fight from its rows: each fighter's hit points as a bar,
who's down, stunned or blinded, the round, whose turn is next. It needs no
dice and plays nothing again. The last encounter on the record unless
`--fight` names its open row, as it ended unless `--round` says which round
to stop at.

**`sim`** fights an encounter many times on seeded dice (fight i on
`random.Random(i)`, 500 unless `--runs`) and says where it rolls out: party
wins, losses, stalemates, rounds, survivors. It writes nothing; a sweep is
for balancing a setting, never a fight on the record.

**Limits, said plainly.** A die is dropped and brought out in the same
breath, when the engine asks for it: no one foresees or steers it, but the
moment between the drop and the out is not one held up to the table.
Whoever holds the die folder can look inside a die before it is out, as the
tower's own card says. The encounters are the Aetheris setting's; another
setting's stat blocks need a statblocks file of their own.

**Needs:** dice 4.0.0 (MIT), pinned in [requirements.txt](requirements.txt),
which brings pyparsing. Without it, `fight`, `check` and `sim` refuse and
name the install; `list` and `board` need nothing. At its floor, 3.1.1, the
same tests pass.

**Source:** Die-Namic's aetheris5e (its combat engine and stat blocks, the
table's board, and the board's and engine's tests), and the dice seam from
willow-bot's one-script, both
Apache-2.0; their licences are [LICENSE-die-namic-games](LICENSE-die-namic-games)
and [LICENSE-willow-bot](LICENSE-willow-bot). What stayed behind: the
one-script record those wrote to, and the seed taken from the row before a
fight, which the tower's dice replace.

**Uses:** [dice-tower](../../stdlib/dice-tower/)'s `drop`, `out` and
`check`, which roll through [play-dice5e](../../stdlib/play-dice5e/) and
[play-dice](../../stdlib/play-dice/); the kernel's `append` and `read`.

**Never:** proposes, seals, reads your key, writes a die file over another,
makes a folder, or goes online.
