<!-- willow-addon
section: Finding things
line: Tries the strict word match first, then your folder's phrases, and says which one found the answer and why the others didn't.
source: bot
added: 2026-10-28
writes: nothing
network: none
tags: no-install, offline, read-only, search, pile
-->
# pile-rungs

A question climbs from the strictest way of looking to the loosest, and the
first rung that answers serves. Every rung it reached is in the answer, with
why it answered, came back empty, or was skipped.

    python adapters/stdlib/pile-rungs/pile_rungs.py --from FOLDER [--store STORE]
        [--top N] QUESTION...

1. **words**: the kernel's own `rank`. It serves a passage only when it holds
   half the question's words, so this rung's answer is the kernel's.
2. **phrases**: [pile-rank](../pile-rank/)'s BM25F, serving only passages
   that hold one of the folder's phrases the question uses. A question
   using none of them skips this rung.
3. **embedder**: none here. The standard library has none, and
   [latent](../../deps/latent/) needs numpy, so this rung is always skipped,
   and it says so.

The answer is one JSON line:

    {"question": "bass strings", "state": "populated", "rung": "words",
     "read_from": "folder",
     "rungs": [{"rung": "words", "state": "answered", "why": "held half of ['bass', 'strings']"},
               {"rung": "phrases", "state": "skipped", "why": "words answered"},
               {"rung": "embedder", "state": "skipped", "why": "words answered"}],
     "served": [...]}

A hook, pile-gold (still an idea), or a person reading it sees how far
the question went and why it stopped. On Hollis's folder (`demo/hollis`),
"who still owes me money" comes back empty at words (no passage holds two
of money, owes and still) and skips phrases (it uses none of his): that is
the honest answer, and the embedder rung is where it would go next.

Only the words rung's answer is the kernel's. A phrase answer points at where
to look.

## What it reads and writes

Passages come from a [pile-store](../pile-store/) store while it matches the
folder, else from the folder (`"read_from"` says which). It writes nothing:
no store, no box, no key, and it reaches no network. Exit codes, the
kernel's: `0` a rung answered; `42` none did, or the folder has nothing to
read; `2` refused (a bad command line, or a `--from` that is not a folder).
