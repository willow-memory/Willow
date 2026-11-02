<!-- willow-addon
section: Trust and proof
line: The record exported as W3C PROV: what came from what, by which step, sealed by whom.
source: new
added: 2026-10-29
writes: to
network: none
-->
# prov

Your record, in the form provenance tools already read.

W3C PROV is the standard way to say what came from what, by which step, and
who was responsible. This writes the record as PROV-JSON, so any tool that
reads PROV can follow an approved answer back to the passages it came from
and to the person who approved it.

    python adapters/stdlib/prov/prov.py --box DIR --to FILE
    wrote FILE: 4 activities, 3 entities, 2 agents

| PROV | In the record |
|---|---|
| activity | every row: a bite, a proposal, a seal, a decline, and the rest |
| agent | who wrote a row: you (a person) for seals and declines, the kernel or an add-on otherwise |
| entity | a passage the files served, a suggestion, an approved answer |
| `used` | a bite used the passages it served; a seal or decline used the suggestion |
| `wasGeneratedBy` | a passing proposal made a suggestion; a seal made the answer |
| `wasDerivedFrom` | the answer came from its suggestion and from the passages it cites |
| `wasInformedBy` | a proposal was made under the bite before it |
| `wasAssociatedWith` | each row, to the agent that wrote it |

A seal is exported only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here), and its answer only
while the suggestion's file still holds the bytes you approved. A seal that
fails either is left out of the links and said on standard error, and the
rest is written. The record keeps no question's words, so neither does the
file: a question is its fingerprint, and a passage is its id and where it was.

The same record gives the same bytes. FILE is written once, readable only by
you, never over a file that exists. Exit codes, the kernel's: 0 written; 42
written, but a seal was left out and waits on you; 2 refused (including a
record that doesn't verify).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** reads your key, changes the record, or writes anywhere but FILE.
