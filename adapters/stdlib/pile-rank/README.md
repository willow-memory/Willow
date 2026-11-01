<!-- willow-addon
section: Finding things
line: Finds passages that use your folder's own phrases ("sourdough bread"), not just the separate words, ranked without any AI model.
source: bot
added: 2026-10-28
writes: nothing
network: none
tags: no-install, offline, read-only, search, pile
-->
# pile-rank

A rank that knows your folder's phrases. "sourdough bread" is one term in a
folder that bakes, so a passage that says it outranks one that says "bread"
here and "sourdough" there.

    python adapters/stdlib/pile-rank/pile_rank.py --from FOLDER [--store STORE]
        [--top N] QUESTION...

## How it scores

Each passage is read as three fields: its **body**; its **title**, the file's
path and any `# heading` line; and its **question lines**, those ending in
`?`. A term is a word (split and with common words dropped the kernel's way,
in its plain form by `kernel.stem`) or a **pair** of such words side by side
in one clause of a line (no comma or full stop between), kept only when two
or more of the folder's texts use it. A pair one note happens to hold is not
a phrase of yours, and neither is "sourdough, bread".

BM25F: a term's count in each field, weighted (title 2, question lines 1.5,
body 1) and normalised by that field's length against its mean (b 0.75), is
summed, saturated (k1 1.2) and weighed by how rare the term is. Each text is
served once, at its first place. The answer is one JSON line with
`"ranked_by": "pile-rank"`, and each passage served names the phrases it
holds.

On Hollis's folder (`demo/hollis`) it reads 2,112 passages into 4,631
phrases in a third of a second, then answers in about a millisecond; "where
did I order the bass strings for mom's piano" serves his restoration log and
the invoice that say "bass strings" first.

## Where to look, not an answer

The kernel serves a passage only when it holds half the question's words,
so an answer the folder doesn't have is never invented. This serves its top
passages whatever they hold, as `scan --rank bm25` does: it points at where
to look. Its answers are not the kernel's, and say so.

## Its passages

With `--store`, from a [pile-store](../pile-store/) store while it still
matches the folder; otherwise the folder read as the kernel reads it. The
answer says which, `"read_from": "store"` or `"folder"`. A stale store is not
rebuilt: build it with pile-store.

From Python, `pile_rank.Ranker(passages)` counts a folder once and
`.rank(question, top)` answers any number of questions from it.

## What it reads and writes

It reads the folder and the store and writes nothing: no store, no box, no
key, and it reaches no network. Exit codes, the kernel's: `0` something was
served; `42` nothing holds a word of the question, or the folder has nothing
to read; `2` refused (a bad command line, or a `--from` that is not a
folder).
