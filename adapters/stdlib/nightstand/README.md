<!-- willow-addon
section: Keeping track
line: Set heavy things down, pick up one bite: at most one thing in hand, and nothing deleted.
source: new
added: 2026-11-01
writes: record
network: none
tags: no-install, offline, records, tracking
-->
# nightstand

Set heavy things down at night, pick up one bite in the morning. It is not a
task list; it keeps three rules a task list doesn't.

    python adapters/stdlib/nightstand/nightstand.py --box DIR down --weight heavy "sort out the tax return"
    python adapters/stdlib/nightstand/nightstand.py --box DIR down --weight light "water the ferns"
    python adapters/stdlib/nightstand/nightstand.py --box DIR one
    python adapters/stdlib/nightstand/nightstand.py --box DIR pick one "fill the watering can"
    python adapters/stdlib/nightstand/nightstand.py --box DIR show

    in hand: 2  light   water the ferns
        bite: fill the watering can
    down (1), the first is what `one` offers:
         1  heavy   sort out the tax return
    done 0, archived 0

1. **At most one thing is in hand.** `pick` while another is held writes the
   put-down into its own row (`displaces`), so there is no instant with two.
2. **You work the bite, not the thing.** `pick` takes one line, the one piece
   you owe the thing today, and refuses to write without it.
3. **Nothing is deleted.** There is no delete. A thing ends `done` or
   `archived`, and every step it took stays a row.

**The moves**, each one `nightstand` row through the kernel's own `append`:
`down` (the words and a weight, `light`, `medium` or `heavy`, default
`medium`), `pick ROW|one BITE`, `back` (set the held thing down, progress
kept), `done` (finish the held thing), `archive ROW` (a thing that is down).
A thing's number is the row that set it down. `one` says what to pick when
you don't know where to start: the lightest, then the oldest. Asking writes
nothing.

**State is never stored.** `show` replays the rows (`--all` adds the done and
archived, with how often each was picked up). `check` replays them under the
same rules and names the first row that breaks one: a pick-up with no bite, a
put-down that isn't the thing actually held, a move the thing can't make from
where it is, a number that is no thing. Every other command refuses a record
that breaks a rule, so the add-on never writes onto one.

**Choices where the store app differs.** The store's *The Nightstand* lets
the bite be skipped (Enter) and then overwrites the old bite with nothing.
Here a bite is required: the rule is a mechanism, not a habit, and every
earlier bite stays in its row. `done` is only from in hand, and `archive`
only from down, as the store's keys are; a thing in hand is set back first. A
bad weight is refused, not turned into `medium`.

**Limits.** The words and bites are written in the record as typed, so the
box is as private as your box. Two people writing at once could each pick up
a thing; `check` shows it, it cannot prevent it, because the kernel locks
only the append. A thing's weight is chosen when it is set down and never
changes.

**Never:** deletes or rewrites a row, holds two things, or takes a bite-less
pick-up.
