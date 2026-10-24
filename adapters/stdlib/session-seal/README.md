<!-- willow-addon
section: Trust and proof
line: One seal at the end of a session, over everything asked and approved in it: yes, these were my actions.
source: bot
added: 2026-10-24
writes: record
network: none
tags: no-install, offline, records, trust
-->
# session-seal

At the end of a session, one seal over all of it, instead of one for every
step: yes, these were my actions.

    python adapters/stdlib/session-seal/session_seal.py --box DIR
    session rows 0 to 2: 3 rows, 1 bite: empty, 1 bite: served, 1 boot
    waiting on your seal (row 5): proposal:1e65daef…
      seal it:  python kernel.py seal --box DIR proposal:1e65daef…
      or leave it unsealed: the rows stay on the record either way

    python adapters/stdlib/session-seal/session_seal.py --box DIR check
    sealed   rows 0 to 2
    1 sessions: 1 sealed, 0 waiting, 0 broken; 1 rows since, not yet bundled

**A session** is the record's rows since the last one was bundled, from
row 0 the first time. Its bundle holds every row by number, kind and hash,
and a count of what came of them (`bite: served`, `bite: empty`,
`proposal: pass`). No words: the record keeps none, so the bundle can't.

**It can't approve anything.** The bundle goes in through the kernel's own
verbs: a bite asks `session FROM to TO`, and the bundle is proposed as the
answer to it, citing nothing. It waits, like any suggestion, for your seal
with `kernel.py seal` and your key. Sealed, the kernel writes it to
`written/sessions/<from>-<to>.json`, and asking `session FROM to TO` again
answers with it. Not sealing it is the No: the rows stay on the record to
be read, they just were never said to be yours. Then one `session` row says
which rows it covers and the subject to seal.

The bite and proposal it makes, and that `session` row, come after the
session they close, so no session holds its own bundle. The seal you make
lands in the next session, where it belongs: it is something you did then.

`check` reads each session back: `sealed`, `waiting`, or `broken` when its
bundle's file no longer hashes to its subject or its rows no longer match
the record's, row for row. A seal row whose proof doesn't hold under your
key counts for nothing, as in `kernel.py verify`.

Exit codes, the kernel's: 0 nothing waits; 42 a session waits on your seal;
2 refused (a record that doesn't verify, a broken bundle, a bad command
line).

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/session.py),
where checkout bundles the session from its check-in and proposes it to
Nestor as one draft pair. Here the kernel's own proposal and seal stand in
for Nestor's, and a session runs from the last bundle, since a kernel box
has no check-in.
