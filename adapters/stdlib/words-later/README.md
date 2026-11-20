<!-- willow-addon
section: Your own words
line: A box made again with a words list it lacked, its record kept as it was, since a box takes its words only when it is made.
source: new
added: 2026-11-19
version: 0.1.0
writes: to
network: none
role: words
-->
# words-later

A box made again with a words list it lacked, its record kept as it was.

```
python adapters/stdlib/words-later/words_later.py make --box OLD --words LIST --to NEW
python adapters/stdlib/words-later/words_later.py check --box DIR
```

**Why.** A box takes its words list when it is made, with `init --words`. A
box made without one has no way to be given one afterwards, and making it
afresh would start a new record and leave every answer sealed on the old one
behind.

**`make`** writes NEW, a box that reads the same pile and sources with the
same key as OLD, names LIST as its words list, and holds OLD's record byte
for byte:

```
made: <stacks>/money/box-with-words, with <stacks>/money/box's record as it was (212 rows), reading <stacks>/money/words.txt (41 words)
<stacks>/money/box is as it was. To put the new box in its place, when you choose:
  mv <stacks>/money/box <stacks>/money/box.before-words
  mv <stacks>/money/box-with-words <stacks>/money/box
```

- **The record is not touched.** Nothing is added and nothing changed, so
  every row hashes as it did and every seal still proves under the same key.
  `verify` on NEW says what it said on OLD.
- **OLD is not touched either.** It is yours to keep or put away. The two
  lines that put NEW in its place are printed and never run: a stack, a
  page or a hook that names OLD's folder goes on reading OLD until you run
  them.
- **From then on** a question asked of NEW is read through LIST, and each
  ask's row carries the list's hash, as in any box made with one.
- **Nothing before that is rewritten.** An answer sealed without a list was
  sealed without one, and the record still says so.

LIST can be a list [words-layers](../words-layers/) makes, so a box given
its words late still follows the master.

**`check`** says whether a box names a words list and whether the kernel
can read it: for finding the boxes that were made without one.

**Refused, and nothing written:** an OLD that isn't a box, whose record
doesn't verify, or that already names a list (it says which); a LIST the
kernel wouldn't take (not a words list, readable beyond its owner, inside
either box); a NEW that is there, or whose folder isn't.

**What it can't do.** It can't change the list a box already names: that
box's list is edited where it is, or made by words-layers. And it doesn't
find what leans on OLD's folder for you.

Exit codes, the kernel's: `make` 0 made; `check` 0 it names a list the
kernel reads, 42 it names none; 2 refused.

**Uses:** the kernel's `read`, `read_words` and exit codes.

**Never:** changes OLD, its record or its settings; adds a row to any
record; reads the key (it copies the name of the key file, as OLD's settings
give it, and never opens it); moves a box.
