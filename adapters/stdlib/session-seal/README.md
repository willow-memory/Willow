<!-- willow-addon
section: Trust and proof
line: One seal at the end of a session, over everything asked and approved in it: yes, these were my actions.
source: bot
added: 2026-10-24
version: 0.4.0
looks-for: claude-code, index-cache
writes: record
network: none
role: tools
output: report
-->
# session-seal

At the end of a session, one seal over all of it, instead of one for every
step: yes, these were my actions.

    python adapters/stdlib/session-seal/session_seal.py --box DIR
    session rows 0 to 2: 3 rows, 1 bite: empty, 1 bite: served, 1 boot
    waiting on your seal (row 5): proposal:1e65daef…
      seal it:  python kernel.py seal --box DIR proposal:1e65daef…
      or leave it unsealed: the rows stay on the record either way

    python adapters/stdlib/session-seal/session_seal.py --box DIR check [--json]
    session-seal: populated, 1 sessions: 1 sealed, 0 waiting, 0 broken; 1 rows since, not yet bundled
    ## sealed
      rows 0 to 2  proposal:1e65daef…

`check` prints [a report](../ci/README.md#the-report-contract), the shape
every report add-on shares: a line counting the sessions, then a group per
state (broken, waiting on your seal, sealed), each row the session's rows and
its subject, a waiting one with the command that seals it. `--json` gives
the same report as one JSON object. No session yet is `empty`. Bundling a
session, the form without `check`, prints its own lines, not a report.

**A session** is the record's rows since the last one was bundled, from
row 0 the first time. Its bundle holds every row by number, kind and hash,
and a count of what came of them (`bite: served`, `bite: empty`,
`proposal: pass`). No words: the record keeps none, so the bundle can't,
but for one thing you hand it. `--with FILE`, a JSON list of what you said
to correct the assistant this session (50 at most, each 2,000 characters at
most), puts those in the bundle in your own words, and the claim says how
many: so a session and its corrections are sealed once, together, rather
than a card each. They are your words, read on the seal page before you
seal; nothing of your folder goes in with them.

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

**A big folder:** the bite reads every file, so on tens of thousands a
close waits half a minute. Name an index of the folder that
[index-cache](../index-cache/) keeps current, and the bite is answered from
it by [claude-code](../claude-code/)'s indexed bite, the same row on the
record, in seconds:

    python adapters/stdlib/session-seal/session_seal.py --box DIR --index INDEX

An index that isn't current, or those add-ons not here, and the kernel
reads the folder, as without one.

**A log beside the box.** A log kept a line a row, each line naming the
hash of the one before it, shows a cut or an edit anywhere but at its end:
the last line has no later one to vouch for it. Name it, and where it ended
goes in the bundle, its lines and the hash of the last, so your seal pins it:

    python adapters/stdlib/session-seal/session_seal.py --box DIR --log FILE
    python adapters/stdlib/session-seal/session_seal.py --box DIR check --log FILE
    session-seal: populated, 1 sessions: 1 sealed, 0 waiting, 0 broken; 1 rows since, not yet bundled; your log: holds
    ## your log
      rows 0 to 1: 3 lines  holds: 0 lines since

`check --log` holds the log to the last sealed session that names one:
`holds` (with the lines since), `cut short`, or `rewritten` at the line it
ended, the last two exit 42. A session waiting on your seal is no one's word
yet, so until one is sealed it says `not sealed yet`. The log is read for
its lines' hashes, never its words.

`check` reads each session back: `sealed`, `waiting`, or `broken` when its
bundle's file no longer hashes to its subject or its rows no longer match
the record's, row for row. A seal row whose proof doesn't hold under your
key counts for nothing, as in `kernel.py verify`.

Exit codes, the kernel's: 0 nothing waits (for `check`, every session
sealed, or none yet); 42 a session waits on your seal, or (for `check`) a
bundle is broken: something found, for you to look at, so a report; 2
refused (a record that doesn't verify, a bad command line).

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/session.py),
where checkout bundles the session from its check-in and proposes it to
Nestor as one draft pair. Here the kernel's own proposal and seal stand in
for Nestor's, and a session runs from the last bundle, since a kernel box
has no check-in.
