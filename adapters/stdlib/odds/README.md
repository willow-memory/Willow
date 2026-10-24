<!-- willow-addon
section: Play
line: Exact odds, as fractions, for a game's dice and tables: what each outcome's chance really is.
source: bot
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, play
-->
# odds

What a roll's chances really are, exactly.

    python adapters/stdlib/odds/odds.py 2d6
    python adapters/stdlib/odds/odds.py 1d20+3 --at-least 15
    python adapters/stdlib/odds/odds.py 2d6 --bands 10,7

| Ask | Gets |
|---|---|
| `2d6` | every total, with its chance as a fraction and a percentage |
| `--at-least 15` | the chance of 15 or more |
| `--bands 10,7` | each band's chance, highest first: 10+, 7-9, 6 or less (a 2d6 game's strong, weak and miss) |

Dice notation: `2d6`, `1d20+3`, `3d6-2`, `1d8+1d6`, `d6`, with spaces around
`+` and `-` if you like. Up to 100 dice of 2 to 1,000 sides. Every chance is
a fraction until it's printed, counted over every way the dice can fall, so
the chances add up to exactly 1.

**Where it comes from:** willow-bot's odds, which counts 2d6 plus a stat
over its 36 outcomes for its own game, with exact fractions. This counts any
dice the same way.

**Never:** reads or writes anything.
