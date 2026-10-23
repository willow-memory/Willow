<!-- willow-addon
section: Finding things
line: Every matching passage, ranked, not just the top three.
source: box
added: 2026-10-23
writes: nothing
network: none
tags: no-install, offline, read-only, search
-->
# all

Every passage that holds your question, ranked, not just the top three.

    python adapters/stdlib/all/all.py --box DIR [--top N] "your words"

It ranks with the kernel's own `rank`, the same rule, order and words list,
so its first three are always exactly the three the kernel serves. The output
is JSON like a bite's, each passage with its rank and a `count`.

**How:** the kernel's `rank` stops at its `TOP` (3); this lifts that for one
call, in its own process, and puts it back. `kernel.py` is never changed.

**Exit codes:** 0 something holds the question; 42 nothing does; 2 refused.

**Uses:** the kernel's `config`, `read_words`, `chunks`, `rank`, `echo` and
`read`.

**Never:** writes to the record: it serves nothing an approval can cite.
