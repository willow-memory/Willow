# Design note: `serve` — a sealed stack, served to a model, on markdown

**Status: proposal, drafted 2026-10-26. Nothing here is sealed.** It builds
nothing and approves nothing; it writes down a shape to agree before any
code. The decisions it leans on are the operator's, already made in
willows-grove; this note adapts them to willow's kernel and add-ons.

Reading, in order, behind this:

- [willows-grove: one-script README](https://github.com/willow-memory/willows-grove/blob/main/docs/design/one-script/README.md)
  — "Where the reading lands", the stack, "Serve, first cut", and "the model
  writes markdown, the human doesn't".
- [willows-grove: one-box README](https://github.com/willow-memory/willows-grove/blob/main/docs/design/one-box/README.md)
  — the box, the rules that bind every phase.
- [willows-grove: one-box four-pieces-join](https://github.com/willow-memory/willows-grove/blob/main/docs/design/one-box/four-pieces-join.md)
  — one script, serve, one hook, one key, and what one-box adds to serve.
- [willow-bot: the first cut of serve](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/serve.py)
  — serve as it stands in the bot.

## The one guarantee

> Code proposes a **stack of piles**; the card shows the joins across them;
> the human **seals that one hash**. The model then reads **one markdown
> file** — the four W's and a named payload, by ids it can't guess, hashes
> withheld, each part labelled *human-sealed* or *untrusted* — and holding
> the file is the permission. It never sees a box, and it fails closed and
> loud.

Everything below serves that sentence. Each line of it is a rule the grove
has already settled; this note only says how willow keeps it.

## The contract (taken as fixed)

1. **Serve writes only the in-scope parts** to the one file the model reads.
   A part out of scope is not named, counted or marked.
2. **The scope is a stack of piles.** A *pile* is one who / what / when /
   where group of record rows, grouped exactly (nothing judged; a row that
   lacks a W is in no pile). A pile's *receipt* is its group key and each
   row's number and hash, checked against the chain before anything serves.
3. **The card lists the joins.** Every who, what, day and where that two or
   more piles share is named: joining is the model's job, so these are the
   joins it *will* make, and the human judges the combination before sealing
   (the mosaic rule).
4. **The human seals one hash.** The seal binds to that exact set; a seal
   over a different set covers nothing.
5. **A trust label on every part:** `human-sealed` when the record holds the
   human's seal over that part's hash, re-checked; else `untrusted`. The
   label is read from the record, never from the part, so pooled text
   arrives as data, never as instructions.
6. **The view is not the record.** Row numbers, prev-hashes, content digests
   and receipts stay on the record's side. The model gets the W's and a
   named payload, full-width hashes withheld, so it can't count, name or
   reverse what it wasn't served.
7. **Ids are keyed with a serve key made fresh each check-in** — never the
   content hash, never the seal key. They hold for the session and can't be
   enumerated or linked across sessions.
8. **Fails closed and loud.** No sealed scope, a seal that covers nothing, a
   part without a receipt, no serve key: nothing serves, and the file says
   why. Empty is not unreachable; the three states never collapse.
9. **Reading is open for people; the model reads only what's served.** The
   public-repository rule still holds for humans; serve is the model's door.

## The two senses of "stack", and how they join

The word "stack" does two jobs, and the design turns on seeing they are the
same object from two sides:

- **The operator composes a stack of add-on steps.** On the command line, a
  stack is a list of add-on runs, each an add-on and whatever arguments it
  allows after a lone `--`:

  ```
  serve --box DIR --stack mystack.md
  # mystack.md, one step a row:
  #   pgp    -- --verify scope.sig      # the seal check; the key is never seen
  #   git    -- log --oneline -n 20     # a source step
  #   digest -- --days 7                # any add-on, run with what it allows
  ```

  The step list is **open**: any add-on can be a step — built in, or one a
  user writes for the purpose — run with whatever arguments it allows after
  the lone `--`. `pgp`, `git`, a content step, the pile itself: the stack
  doesn't fix the set, and serve doesn't care which add-on produced a part,
  only that the part carries its receipt and trust label. This is the same
  move the new [`across`](../../adapters/stdlib/across/) add-on already makes
  — run add-ons and compose what they print — only here the steps are
  heterogeneous and one of them is the seal check.

- **Serve groups the result into a stack of piles.** What the steps produce
  becomes record rows; `serve` groups those by the four W's into piles,
  proposes the scope, lists the joins, and the human seals the one hash. The
  model then reads the view.

So: *add-on steps gather the content; piles and the seal make it safe to
serve.* The operator's stack is the input; the sealed stack of piles is what
the model is actually shown.

## Why markdown

The operator's rule: the model writes markdown (headings, tables, lists); the
human writes plain text. So **markdown-shape is a cross-check on who authored
a part**, and every shape a serve relies on gets one fixed test — the
grove's markdown-testing idea. Concretely for willow:

- The **stack file is markdown** (a list, or a table of steps), so it reads
  and diffs as prose and a test can hold its shape.
- The **served file is markdown**: the W's as headings, the payload as a
  fenced block or table, the trust label and the (opaque) id on each part.
- A small set of **shape tests** check that a served part is well-formed
  markdown of the expected kind, and that nothing outside the shape leaks
  (no full-width hash, no row number).

## The seal check (`pgp`), and never the key

The step that authorises is a verify, not a signer. The human seals the
scope's hash with their own PGP key, in their own gpg/agent, outside willow.
The `pgp` step runs `gpg --verify` on that detached signature over the scope
hash:

- It needs only the signer's **public** key, so willow never reads a private
  key — the guard's "never the key" holds, and the write-guard is satisfied
  because verification reads nothing under the box's `key`.
- The model is served the view only: never the key, never the signature.
- Stdlib has no OpenPGP, so `pgp` shells out to the `gpg` program, the way
  willow already treats programs-not-packages (`github` → `gh`, `repo-pile`
  and `restack` → `git`). Its card would say `network: none` and name `gpg`.

If the verify fails, nothing serves, and the file says so (fails closed).

## Where this lands in willow

willow's `kernel.py` already has `bite`, `propose`, `seal` and `verify`, but
**not** `piles`, `scope`, `serve`, the `view`, or a serve key. The closest
thing shipped is `mcp-lite`, which serves a box to an assistant *unscoped* —
it hands over tools, not a sealed stack of piles. The planned `hook-cite`
idea ("refuse a claim citing a passage the box never served it") is the same
family: it only works once serve records what it served, by id.

**Decided: a `serve` add-on, over the kernel** (operator, 2026-10-26). The
add-on holds `piles`/`scope`/`view`/the serve key; it reads the record
through the kernel, runs the steps (including `pgp`), groups the piles, and
writes the markdown file. The kernel is not touched, so the one-way arrow
holds and the sealed, pre-AI core stays as small as it is.

The cost of that choice is that the serve key and the view's redaction — the
two security-load-bearing parts — live in the add-on rather than beside the
seals. So the add-on carries the weight the kernel would have: it stays tiny
and readable, the guard holds it to `writes: to` / `network: none` and "never
the key", and the markdown **shape tests** (below) are what prove the view
withholds what it must. A part that can't be served under those rules isn't
served (fails closed).

## What must stay true (willow's own rules)

- **The arrow points one way.** `serve` is an add-on; the kernel never names
  it. (If the kernel grows a primitive, it is a general one, not a hook into
  any add-on.)
- **Never approve.** Code proposes the stack and verifies the seal; it never
  writes a seal and never reads the person's key. The human's `gpg` seal is
  the only authority.
- **What the card doesn't list, it can't do**, and **no add-on widens its own
  reach** — the guard holds `serve` and `pgp` to their cards like any other.
- **Fails closed and loud**, three states never collapsed, as everywhere
  else in willow.

## Open questions for the operator

Two still open; the rest are settled or held, below.

1. **The stack file's markdown shape** — a plain markdown list of
   `addon -- args` rows, friendlier to hand-write, or a table with a column
   per field (step, args), rigid and easiest to shape-test? (See "Why
   markdown".)
2. **The four W's on willow's records.** `piles` groups by exact W, but the
   kernel's rows carry `who`, a timestamp (`when`, as the day) and content —
   not an explicit "what" or "where". What plays them: a bite's subject for
   "what" and a cited passage's path for "where", or does piling start with
   the W's willow already has (`who`, day) and the rest arrive when rows
   carry them?

## Settled, and held

- **Serve is an add-on**, not a kernel change (decided 2026-10-26; see "Where
  this lands in willow").
- **The step list is open** — any add-on, built in or user-written, run with
  its own arguments (decided 2026-10-26; see "The two senses of 'stack'").
- **The model's one door is held.** Serve is the model's only read, so it
  wants a hook that narrows Read to the served file. The bot has such a hook
  and the grove removed one; neither was judged strong enough, so the hook is
  a separate, larger discussion and out of scope for this note.

## Not in this note

It seals nothing, builds nothing, and retires no grove phase. It names what
willow would grow to keep a guarantee the grove already settled, so the shape
can be agreed before any code is written.
