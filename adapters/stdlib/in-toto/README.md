<!-- willow-addon
section: Trust and proof
line: A sealed answer exported as an in-toto Statement, the envelope SLSA uses, so others can check it.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# in-toto

An approved answer, as the envelope supply-chain tools read.

An in-toto Statement says what an attestation is about (a subject, named and
hashed) and what is claimed of it. SLSA provenance is one; this is another.
This writes a Statement for each answer you approved, so someone with the
answer's file can check what it is, why it was given, and where on the chain
your approval sits.

    python adapters/stdlib/in-toto/in_toto.py --box DIR --to FILE
    wrote FILE: 1 statement

One JSON object a line, oldest approval first:

| Field | Holds |
|---|---|
| `subject` | the answer's file name and the sha256 of its bytes as they were written |
| `predicateType` | `urn:willow:seal:v1` |
| `predicate.claim` | why the suggestion was made |
| `predicate.cites` | each cited passage's id and where it was |
| `predicate.question` | the question it answers, by fingerprint |
| `predicate.sealedAt`, `sealRow`, `rowHash` | when you approved it, and the record row and hash that hold the approval |
| `predicate.suggestion` | the suggestion's subject |

These are Statements, not signed envelopes: signing takes your key, and no
add-on reads it. A signing tool makes a DSSE envelope from one. An approval
is exported only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file
still holds the bytes you approved; one that doesn't is left out and said on
standard error. The same record gives the same bytes.

FILE is written once, readable only by you, never over a file that exists.
Exit codes, the kernel's: 0 written; 42 written, but an approval was left
out and waits on you; 2 refused (including a record that doesn't verify).

**Uses:** the kernel's `read`, `sealed` and `standing`.

**Never:** reads your key, changes the record, or writes anywhere but FILE.
