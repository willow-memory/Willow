<!-- willow-addon
section: Your own words
line: One words list made from several: a master of what is true in every box and a layer for each matter, remade when any of them changes.
source: new
added: 2026-11-19
version: 0.1.0
writes: to
network: none
role: words
-->
# words-layers

A box's words list made from a master list and the layers that box needs.

```
python adapters/stdlib/words-layers/words_layers.py make --from LIST [--from LIST ...] --to MADE
python adapters/stdlib/words-layers/words_layers.py check --from LIST [--from LIST ...] --to MADE
```

**Why layers.** A box takes one words list, named when the box is made. One
list for everything goes wrong quickly: "step" is an instruction in one pile
and a stack's step in the next, so a line that helps one box misleads
another. A list for each box goes wrong the other way: the words that are
true everywhere are written out in each, and corrected in one. So keep
several lists, each an ordinary words list:

- a **master**, of what is true in every box: your shorthand, your spellings;
- a **layer** for each matter or project, with that pile's own words.

**`make`** writes MADE as those lists one after another, in the order you
give them, each under a line naming its file and the SHA-256 of what it
held. MADE is the file the box names. It is made, never edited: change a
layer and make it again.

```
made: <stacks>/project/words.txt, 22 words from 3 layers; changed: master.txt, kaggle.txt, project.txt
  in more than one layer, read together: deadline (master.txt, kaggle.txt)
```

- **A word on two layers means both.** The kernel already reads a word that
  is on two lines as the two lines together, so nothing is overridden: the
  master's `deadline = due, expires` and a layer's `deadline = timeline`
  make `deadline` read as all three. Each such word is listed, since that is
  where two lists meet and where a wrong sense would come from.
- **It writes only when something changed**, and says which: `made`,
  `remade` with the layers that changed or were taken out, or `current`.
- **MADE is readable only by you**, as the kernel asks of a words list.

**`check`** writes nothing. It says whether MADE is what `make` would write
now: `current`, `stale`, or `not made yet`.

As the first step of a stack, `make` keeps a project's list in step with
the master every time the stack runs.

**Refused, and nothing written:** a layer that is missing or is not a words
list, named with its line; a MADE that is there and was not made by this,
which is someone's own list and is left as it is; a MADE that is a folder or
whose folder isn't there.

**What it can't do.** It can't give a list to a box that was made without
one: a box names its list when it is made. And it knows nothing of what a
word means, so it can't tell you a master line is wrong for one pile; the
"in more than one layer" lines are the place to look.

Exit codes, the kernel's: `make` 0 made, remade or current; `check` 0
current, 42 stale or not made yet; 2 refused.

**Uses:** the kernel's `parse_words` and exit codes.

**Never:** writes anything but MADE (and, while writing it, a scratch file
beside it); changes a layer; writes over a list it didn't make; reads a box
or the key.
