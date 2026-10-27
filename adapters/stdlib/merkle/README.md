<!-- willow-addon
section: Trust and proof
line: A Merkle tree over the record, so one row can be proven with a handful of hashes, not the whole file.
source: new
added: 2026-10-27
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# merkle

The record's chain proves the whole file: to check one row you read every
row. A Merkle tree over the same lines proves any one row with about
log-many hashes, so a row can be shown to someone who holds only the root —
a friend, a lawyer, a future you — without sending the record.

```
python adapters/stdlib/merkle/merkle.py root  --box DIR
root b14c9d8e... over 177 rows

python adapters/stdlib/merkle/merkle.py prove --box DIR --row 100 --to FILE
row 100 of 177: a proof of 8 hashes to FILE

python adapters/stdlib/merkle/merkle.py check --proof FILE --root b14c9d8e...
row 100 of 177 stands under your root.
```

**The root is worth a line of your notebook.** Keep it where you keep your
[tip-pin](../tip-pin/): a root held outside the box is what a proof answers
to. `check` needs no box — it rehashes the proof's own line and folds the
sibling hashes — and alone it only shows self-consistency, so alone it exits
42: whether the root it reaches is your record's, only your own copy of the
root can say. With `--root` it answers plainly, and a row that doesn't stand
is refused, never shrugged at.

**The tree, exactly.** A leaf is SHA-256 over a zero byte and the row's own
line (the record's canonical JSON, newline off); a node is SHA-256 over a
one byte and its two children, left then right, so a leaf can never pose as
a node and left can never pose as right; a level's odd last node rises
unchanged. The record's chain is checked before any proof is cut, so a
proof over a broken record proves nothing but the break. The same record
gives the same root anywhere; one row changed, added or dropped gives
another root.

On a real record — this repo's own CI box of 177 verdict rows — any one
verdict's proof is 8 hashes, and the numbers above are that run's.

Nothing here writes the record or reads the key; the chain stays the
record's spine, and [tip-pin](../tip-pin/) stays how the tip is held. FILE
is written once, readable only by you, never inside your folder or the box,
never over a file that exists. Exit codes, the kernel's: 0 the root printed,
the proof written, or the row stands; 42 a proof alone, with no root of
yours to answer to; 2 refused, a proof that doesn't hold together among the
refusals.

**Uses:** the kernel's `read`, `canon` and `config`.

**Never:** writes the record or anything but FILE; reads the key; cuts a
proof over a broken chain; says a lone proof is more than self-consistent.
