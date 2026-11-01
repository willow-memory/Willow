<!-- willow-addon
section: Ways to use it
line: One page made from several add-ons run in the order you list them, their results grouped so the biggest come first.
source: new
added: 2026-10-26
writes: nothing
network: none
tags: no-install, offline, read-only, interface
-->
# stack

One document from a **stack of add-on steps** over a box. Where
[`across`](../across/) runs one document add-on over many boxes, `stack` runs
many heterogeneous steps over one box and composes what each prints — pooled,
and ordered tallest-first. It is the input side of the serve layer in
`docs/design/serve.md`: the operator's stack, before any seal.

    python adapters/stdlib/stack/stack.py --box DIR --stack FILE

## the stack file

A markdown file, pools and steps:

    ## a pool heading
    - digest -- --box {box}
    - export -- --box {box}

    ## another pool
    - timeline -- --box {box} --to {box}-notes "mould landlord"

A `##` heading opens a **pool**; each `- NAME -- ARGS` line under it is a
**step** — the add-on NAME run with the ARGS after the lone `--`. `{box}`
anywhere in a step's args is replaced with the `--box` path, so a step that
reads the box names it and a step that doesn't (a `git` or `pgp` step) leaves
it out. Blank lines, lines beginning `#` (but not `##`), and any other prose
are skipped, so a stack file reads as markdown; a step before any pool is
refused. A worked example is `adapters/stdlib/stack/example.md`; seven more,
each for a different kind of folder, are in `adapters/stdlib/stack/examples/`.

## pools and peaks

The order is the stacking order — **peaks first**. Each step's **mass** is how
many non-blank lines it printed; a pool's mass is its steps' together. Pools,
and the steps within them, run tallest first, because mass is what decides
attention: the reader meets the biggest stack first. The document is markdown —
a `##` per pool, each step's output fenced under it, a step flagged `(exit N)`
when it didn't run clean.

## what it does and doesn't

The step list is **open**: any add-on, built in or user-written, can be a step.
`stack` doesn't care which add-on produced a part — it runs the step, takes
what it printed, and composes. Each step is held to **its own card** by the
guard, so `stack` itself writes no box, reads no key and approves nothing (the
one-way arrow, a box to a document); a step's own reach is the step's card, not
this one. `stack` names `network: none` for its own run.

Exit codes, the kernel's: `0` nothing in the stack waits on you; `42` a step
flagged something (or refused), its output shown and flagged; `2` refused — a
bad command line, a box that isn't a kernel box, an unreadable or empty stack,
or a step whose add-on isn't here.
