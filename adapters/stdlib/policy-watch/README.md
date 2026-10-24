<!-- willow-addon
section: Keeping track
line: A terms or policy page fetched each time you run it, by snapshot, and what changed since last time, sentence by sentence, by clauses.
source: new
added: 2026-10-24
writes: to
network: the page you name, fetched each time you run it
tags: no-install, online, writes-output, tracking, policies
-->
# policy-watch

A terms or policy page, fetched each time you run it, and what changed since
the last copy, sentence by sentence.

    python adapters/stdlib/policy-watch/policy_watch.py --url URL --to FOLDER

    saved     20261019T090000Z-terms   56 bytes   sha256 …
    changed         since 20261018T090000Z-terms:
    reworded  1 -> 1   (3 of 5 words kept)
      - We keep data.
      + We keep data, unless asked.
    added     1   We sell nothing.
    removed   1   We delete it on request.

Companies change their terms with an email few people read. Run this from
a scheduler and it keeps a copy of the page each time, through the
[snapshot](../snapshot/) add-on, named by the time it was fetched
(`20261024T090000Z-privacy`), with its address, time and SHA-256. It then
compares the new copy with the last copy of the same address and says one
of:

- `first copy`: nothing to compare yet;
- `unchanged`: the same bytes;
- `same words`: the bytes differ (a new script, a new link), every
  sentence is the same;
- `changed`: each sentence reworded, added or removed, by
  [clauses](../clauses/)' comparison, with the line each starts on.

A page served as HTML is read as its blocks, anything else as plain text. A
page that isn't UTF-8 text, such as a PDF, is compared by its bytes only,
and it says so: put copies through the [pdf](../../deps/pdf/) add-on and
`clauses diff` for their sentences. A page that can't be fetched is written
down as snapshot writes it, and is never taken for a copy. Every copy is
kept, so any two can be compared again later.

**What it was built for:** Google's privacy policy changed on 1 and 16
October 2026, and the change people argued about was one sentence; see
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/).

**Exit codes:** 0 the first copy, or nothing changed; 42 something changed,
or the page couldn't be fetched; 2 refused.

**Uses:** the snapshot add-on's `save`, `lines` and `name_for`; the clauses
add-on's `read`, `clauses` and `compare`; the kernel's exit codes.

**Never:** goes anywhere but the address given, writes outside FOLDER, or
changes a copy it saved before.
