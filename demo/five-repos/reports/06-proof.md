# Report 1: prove the box to the outside world, 2026-11-03

A fresh box over the five repos, with the pruned words list. Six findings
from the earlier stacks went in as suggestions, each citing the passages
a bite had just served. **None was sealed.** The seal and the decline
were refused by the session's permission classifier as self-approval, and
that refusal is Willow's own rule (code may search, suggest and record;
it never writes a seal and never reads the person's key), so the posture
for every task from here is propose and wait. The six are waiting in
`proof-box`; the first of them is the wrong version of the casebook
finding and is the one to decline.

One finding corrected itself on the way in. The bite for "does the
constitution link a casebook" served `constitution/README.md:103`, which
says the Casebook stays with willows-grove, another repository. So the
five `CASEBOOK.md` links are external on purpose, xref reads them as
broken because it checks this repo only, and the corrected suggestion
cites that line.

## The stack, 13 steps in 4 pools, 2.9 s

| step | what it made |
|---|---|
| fixity | 1,605 files hashed onto the record; a second run: all 1,605 match |
| merkle root | `4ee49b1e…` over 16 rows |
| merkle prove row 7 | a proof of 4 hashes to a file; `check` against the root: "row 7 stands under your root" |
| tip-pin pin | 16 rows pinned, tip `721b6966…`, to a file outside the box; `check`: holds |
| backup | one zip, 8 files, 16 rows, every byte and the chain checked before it was kept; the key not in it |
| restore-drill | the zip restored into scratch: 8 files, 16 rows, the chain holds |
| diverge box vs zip | the same, byte for byte |
| three-two-one | 3 copies on 3 kinds of storage, one away: holds |
| ro-crate | `willow-crate-….zip`, 1,612 files and 16 rows, 1,615 graph nodes, licence Apache-2.0 |
| prov | PROV-JSON: 16 activities (boot, bite, proposal, out, fixity), 21 entities, 2 agents |
| in-toto | 0 statements |
| ids | CONSTITUTION.md and each of its paragraphs as Software Heritage IDs and IPFS CIDs |

## Two copies tampered with, and which check caught which

| tampering | verify | diverge | merkle | tip-pin | three-two-one |
|---|---|---|---|---|---|
| one byte changed in row 7's text | row 7: chain broken, exit 2 | the same for 7 rows, then part at row 7 | refused, chain broken | not needed | not tested |
| the last two rows cut off, nothing else touched | the chain holds: 15 rows, exit 0 | the same for 15 rows, then A runs on 2 more | | cut short: 16 pinned, the box has 15, exit 42 | holds |

The second row is the point of tip-pin, and the record shows it: a record
cut short still verifies, and only the pin kept out of reach says so.

## What a stranger could verify

- That the record is the one we hold: the Merkle root, and any single
  row with four hashes, without being sent the record.
- That it hasn't been cut short since the pin was written.
- That the backup is the box, byte for byte, and restores.
- What each file is, by names the world already uses: a Software
  Heritage ID that matches the archive's whether or not the file is
  there, and an IPFS CID.
- What came from what: every bite, proposal and fixity row as PROV
  activities with their agents.

What they could not verify is any approval, because there is none. The
in-toto export is empty for that reason, and the PROV agents are two
pieces of software and no person. The moment a person seals one of the
six, in-toto gets its first statement and PROV its first human agent.

## Two leads

- **three-two-one counts a copy that is behind.** With the truncated
  copy as the away copy it still reports "3-2-1 holds", since a copy
  counts when its chain holds, and a chain cut short does. The zip is
  also one row behind the box by then. The card says this is the rule;
  a row-count column, or a line saying how far behind each copy is,
  would make it say what tip-pin says.
- **The first casebook suggestion passed with no cites.** A proposal
  whose `cites` is an empty list passes the "cites only from what the
  last bite returned" rule trivially. The kernel's contract may intend
  that; it means a suggestion can wait for a seal citing nothing.

## Files

`proof.md` (the stack), `proof/page.out` (the page), `proof/backup/`,
`proof/crate/`, `proof/prov.json`, `proof/row7.json`, `proof/tip.txt`,
`proof/tamper-a/` and `proof/tamper-b/` (the two tampered copies),
`proof-box/` (the box, six suggestions waiting).
