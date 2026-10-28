<!-- willow-addon
section: Finding things
line: The passage size measured, not guessed: your box's own questions asked at several sizes, and the size that finds the most of their answers named.
source: bot
added: 2026-10-28
writes: nothing
network: none
tags: no-install, offline, read-only, search, pile
-->
# pile-sweep

The kernel cuts your folder into passages of at most 500 characters. Smaller
passages answer more exactly; larger ones hold more of a question's words.
Which suits your folder is something your own answers can settle.

    python adapters/stdlib/pile-sweep/pile_sweep.py --box DIR --questions FILE
        [--sizes 200,350,500,800,1200]

The answers are [pile-gold](../pile-gold/)'s: the passages your sealed
answers cite, for the questions in FILE that have one. A passage's id
changes with its size, so each answer is taken where it stands now, as its
file and its lines. At each size, an answer is found when a passage in the
top five overlaps those lines. Both the kernel's rank and
[pile-rank](../pile-rank/) are asked.

On a box over Hollis's folder (`demo/hollis`) with three sealed answers:

    3 questions, 3 approved passages, top 5
     size  kernel              pile-rank
      350  3 of 3, 67 lines    3 of 3, 71 lines
      500  3 of 3, 100 lines   2 of 3, 95 lines      <- the kernel's
     1200  3 of 3, 250 lines   2 of 3, 213 lines
    best for the kernel: 350; for pile-rank: 350

"lines" is how many lines the top five held, over every question. A larger
passage overlaps more by being larger, and costs more to read, so the best
size is the one that finds the most, then the one that reads the fewest
lines, then the kernel's own. Three answers measure little: the sweep is
only as good as the seals behind it.

## What it changes, and doesn't

Each size is read with the kernel's `MAX_CHUNK` set to it, in this process
only, and put back after; `kernel.py` is never changed. It names a size and
keeps nothing: the idea's line said the size was "kept", but changing the
kernel's size is the kernel's change to make, by a person, not an add-on's.

## What it reads and writes

It reads the box's record, its proposals and its folder, and your words list
if the box has one. Seals are read through the kernel's `sealed` and
`standing`, which check them against your key; it never reads the key. It
writes nothing and reaches no network. Exit codes, the kernel's: `0` swept;
`42` no question in FILE has a sealed answer still in the folder; `2`
refused (a bad command line, sizes under 50 or over the kernel's file cap,
not a box, a broken record, or a FILE that can't be read).
