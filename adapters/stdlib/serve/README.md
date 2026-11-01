<!-- willow-addon
section: Assistants
line: The one file an AI model may read: only the passages you approved, under ids it can't guess, and nothing else.
source: bot
added: 2026-10-26
writes: record, to
network: none
tags: no-install, offline, writes-output, trust, assistant
-->
# serve

The one markdown file a model reads — only the scope a human sealed. The
model never sees a box; holding the file is the permission. The shape and the
reasoning are the design note, `docs/design/serve.md`.

    python adapters/stdlib/serve/serve.py scope --box DIR [--now TS]
    python adapters/stdlib/serve/serve.py --box DIR --to FILE [--now TS]

## scope — propose what to serve

`scope` takes the passages the last bite served, groups them into **pools**
(by where each came from), orders the pools by **peak** — how many passages
stack in each, tallest first — and prints that card. It then proposes the set
through the kernel, so you can seal its one subject with your key:

    python kernel.py seal --box DIR proposal:<subject>

It writes only the kernel's proposal row, and it never seals. With no bite
served yet, it says so and does nothing.

## the write form — serve the sealed scope

Given a sealed scope, the write form writes the served file to `--to`. It
reads the seal **through the kernel** (`sealed`), so it never touches your
key, and a forged seal is never served. The file is markdown:

    # served: N passages a human sealed

    ## where-a-pool-came-from
    - `opaque-id`  human-sealed
      ```
      the sealed passage's text
      ```

A `##` heading per pool, peaks first; under it each passage as its `where`, an
**opaque per-run id** (a fresh serve key each run, so ids can't be guessed or
linked across runs), its trust label, and the text. No record hash, no row
number: nothing the model could count or reverse. It writes nowhere inside the
box or your folder.

**Without a sealed scope it serves nothing and says so** — it fails closed.
A scope counts only while its proposal file is still the bytes you sealed
(the kernel's `standing`): one widened or changed after the seal serves
nothing.

This first cut seals through willow's own key; the `pgp`-verify seal the
design note names (a script checks the signature, the model never sees the
key) is a separate step. Exit codes, the kernel's: 0 served, or a scope
proposed with nothing left waiting; 42 nothing to scope yet, or a scope waits
on your seal; 2 refused (a bad command line, a broken record, or — for the
write form — no sealed scope).
