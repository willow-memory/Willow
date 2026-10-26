# Design note: the repo as a box — one deterministic snapshot, many views

**Status: proposal, drafted 2026-10-26. Nothing here is sealed, and nothing
is built** (the operator: design against serve first). It extends the serve
note, [serve.md](serve.md), to willow's own growing repository: the add-ons,
their cards, and the lists that index them.

## The idea, in one line

The repo's index is **just another box** — a deterministic snapshot of the
repo made by the kernel, the way willow makes any box. The three things we
wanted from "indexing the repo" are not three features; they are three views
on that one box:

- **the add-on catalog** — the cards, grouped and searchable;
- **the whole repo, searchable** — ask / scan / quote over the snapshot;
- **CI and navigation speed** — the snapshot's index is the cache.

"All the same thing, with just another box added on." Build the box once,
deterministically, and each view is a read of it.

## Why a box, and why deterministic

willow already treats a folder as a box: the kernel takes a pile, writes a
record and a hash chain, and `verify` holds it. A box over the repo is the
same move pointed at the repo itself — its add-on cards and docs as the pile,
its code indexed by `scan`. Because the kernel hashes what it reads, the
snapshot is **reproducible**: the same repo state gives the same box, by
hash, so

- the index is **verifiable** (`kernel.py verify` on the box), not a cache
  you have to trust;
- two snapshots **compare** (`snapshot` and `diverge`, willow's "picture and
  compare"): the diff of yesterday's box and today's is exactly what the
  additions changed — a real index of growth, not a growing hand-kept list.

That is the answer to "lists growing without good indexing": the list stops
being the index. `FILES.md` stays the human's table of contents, but the
box — regenerated, hashed, diffable — is what you actually search and check.

## The custom stack (serve-style: pools and peaks, on markdown)

Indexing the repo is a **stack**, the serve kind: an open list of add-on
steps, composed, ordered by the pools-and-peaks of the stacking (see
[serve.md](serve.md)). This repo's own stack, committed, composes the
indexing add-ons willow already has:

- **`scan`** — index the cards, the docs, and the code (bm25 + the kernel's
  rank), so the whole repo answers a question.
- **`similar`** — the near-duplicate check over `adapters/planned.json` and
  the add-ons, so a new addition that overlaps an old one surfaces before it
  is built.
- **`readme`** — the catalog view (`ADDONS.md`), grouped by section; one
  rendering of the box, not a second source of truth.
- the consistency checks (`test_docs`'s tree, the card contract) as steps
  that must pass for the snapshot to seal.

The steps run why-free; a model step may attach a why on a proposal, as data
(serve's rule). Pools group the additions — by section, by tag, by the four
W's — and **peaks** put what stands out on top: the most-referenced add-on,
the section that grew most, the idea the most new cards cite. So the catalog
is not alphabetical noise; it is ordered by what is load-bearing.

## The four W's for a repo box

The same axes serve piles on, read for the repo:

- **who** — the add-on's author (its card, the commit).
- **when** — the day it was `added` (the card's `added:` line).
- **what** — its section and tags (and, for a question over the box, the
  `bite_key`), exact, not judged.
- **where** — the generic locator (serve's `where`): the add-on's path, or,
  for code pulled in by `repo-pile`, the source repo and blob. New kinds of
  source attach new `where`s without the index changing.

## What willow already has, and what it would grow

Shipped and reused as steps: `scan`, `similar`, `readme`, `snapshot`,
`diverge`, and `repo-pile` (which already builds a box from repositories —
willow pointed at willow is the degenerate case). Planned and on-point:
`index-cache` (keep the box's index between runs, re-read only files whose
hash changed) and `watch` (re-read a file the moment it changes) — together
they are the "CI and navigation speed" view, the incremental side of the one
box.

What's missing is the serve layer the stack composes through (piles, scope,
the view, the serve key) — so this note **waits on serve**. Until then, the
pieces exist but run one at a time; the stack is what makes them one
deterministic snapshot.

## Open, and not in this note

- **The stack's exact steps and order** for this repo — drafted above,
  settled when serve lands and the pools-and-peaks ordering is real code.
- **Whether the repo box is built in CI** (a snapshot per commit, diffable
  against the last) or on demand — a later call, tied to the CI-speed work.
- It builds nothing and seals nothing; it says how the indexing goal becomes
  one box and one stack, so the shape is agreed before code.
