<!-- willow-addon
section: Play
line: What each character carries, uses up and is hurt by, written in plain words a line at a time, read back as a sheet night to night.
source: new
added: 2026-11-23
version: 0.1.0
writes: record
network: none
role: tools
uses: lines-veils
from: shape, https://github.com/rudi193-cmd/die-namic-games, Apache-2.0
-->
# carry-sheet

What the characters carry, use up and come through, written down the way
the table says it, and read back as each one's sheet, from one night to the
next.

    python adapters/stdlib/carry-sheet/carry_sheet.py --box DIR write --names "Tamsin,Oro" "Tamsin finds a rope"
    Tamsin carries a rope   (row 41)

    python adapters/stdlib/carry-sheet/carry_sheet.py --box DIR write --names "Tamsin,Oro" "Oro is hurt by a club"
    Oro is still hurt (by a club)   (row 42)

    python adapters/stdlib/carry-sheet/carry_sheet.py --box DIR sheet
    Tamsin carries a rope
    Oro is still hurt (by a club)

**A line** is a name from `--names` (commas between them), then what
changed, then the thing or how:

| Change | Words it knows |
|---|---|
| carry | finds, gets, picks up, takes, gains, is given, buys, carries (and their past) |
| spend | uses, uses up, loses, spends, drops, gives away, breaks (and their past) |
| hurt | is hurt, gets hurt, is wounded, is poisoned, is cursed |
| heal | is healed, heals, is better, is fine, rests |

A carry or a spend needs a thing ("Tamsin finds" isn't a line). A line that
doesn't start with one of the names and a word it knows is refused, and
nothing is written: it never guesses who, or what changed.

**On the record**, each change is a `table-carry` row: `char`, `change`
and `what`, as written. Nothing is ever taken off: a thing used is a later
row, and a sheet is every row about that character, read in order, so it
carries over between nights and between the parts of a story. A wound lasts
until a line says they're healed, and healing clears every wound at once. A
thing is matched by its words, an article or a plural aside, so "uses the
ropes" spends "a rope" (lines-veils' `words` and `same`), and a thing
nobody carries is simply not there to spend.

`sheet --name NAME` prints that one's sheet; with no `--name`, every
character the record has a change for, in the order they were first met.

**Exit codes**, the kernel's: 0 done; 2 refused, with why (a line it can't
read, a folder that isn't a box, a record that doesn't verify, a command
line it hasn't).

**Source:** Die-Namic's table, whose carry module this is, rebuilt here; it
keeps its rows as [lending](../lending/) keeps a loan (every line stays, a
return listed after it) and [livestock](../livestock/) an animal's
treatments.

**Uses:** [lines-veils](../lines-veils/)' `words` and `same`; the kernel's
`append` and `read`.

**Never:** guesses a name or a change, takes a row off the record, reads
your key, or goes online.
