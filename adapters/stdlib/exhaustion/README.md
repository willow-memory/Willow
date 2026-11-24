<!-- willow-addon
section: Play
line: What a level of exhaustion does to a roll, a speed and a hit point maximum, by SRD 5.1 or 5.2, kept apart.
source: new
added: 2026-11-23
version: 0.1.0
writes: nothing
network: none
role: tools
from: shape, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0
-->
# exhaustion

A character worn out by a forced march or a night without sleep: what that
does at the table, by the rules, and nothing made up.

    python adapters/stdlib/exhaustion/exhaustion.py 2 --speed 30 --hp-max 21
    SRD 5.2, level 2
    worn out (2): every d20 roll -4, speed -10 feet
    d20 tests: -4
    checks: normal; attacks: normal; saves: normal
    speed: 30 feet, 20 worn out
    hit point maximum: 21, 21 worn out
    after a long rest: level 1

    python adapters/stdlib/exhaustion/exhaustion.py 4 --edition 5.1
    SRD 5.1, level 4
    worn out (4): disadvantage on ability checks, speed halved, disadvantage on attacks and saves, hit point maximum halved
    d20 tests: +0
    checks: disadvantage; attacks: disadvantage; saves: disadvantage
    after a long rest: level 3

**The two editions say different things about the same word**, so both are
kept, named, and never mixed; 5.2 unless `--edition 5.1` is asked for.

| | SRD 5.1 | SRD 5.2 |
|---|---|---|
| a d20 test | disadvantage on ability checks from level 1; on attacks and saves from 3 | 2 off per level |
| speed | halved (rounded down) from level 2; 0 from level 5 | 5 feet off per level, never below 0 |
| hit point maximum | halved from level 4, at least 1 | unchanged |
| level 6 | death | death |
| a long rest | one level off | one level off |

5.1's food and drink before a rest eases a level are not modelled.

**As code:** `d20_modifier`, `roll_mode`, `speed_change`, `hp_max`, `dead`,
`after_long_rest` and `said`, each taking the level and the edition, for a
table that applies the effect to its own rolls. A level outside 0 to 6, an
edition or kind of roll it doesn't know, a speed below 0 or a maximum below
1 is refused by name, never guessed.

**Source:** the rules as SRD 5.1 and SRD 5.2 read (CC-BY-4.0), as Die-Namic's
game box first wrote them down, with dndwright's conditions catalog (5.1's
wording) and srd_5e's exhaustion rule (5.2's) read beside them; written
afresh, nothing copied.

**Uses:** the kernel's exit codes: 0 said; 2 refused.

**Never:** reads or writes a box, applies the effect to a roll itself, or
goes online.
