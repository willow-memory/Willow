<!-- willow-addon
section: Finding things
line: Your folder's passages kept in one file between questions, used only while the folder hasn't changed, so other add-ons don't re-read it every time.
source: bot
added: 2026-10-28
writes: to
network: none
tags: pile
-->
# pile-store

The kernel reads a folder into passages each time it is asked. The other pile
ideas (a rank over phrases, a process that holds the store open, a sweep of
passage sizes, a test from your approved answers) all want those passages read
once and kept. `pile-store` keeps them in one SQLite file:

    python adapters/stdlib/pile-store/pile_store.py --from FOLDER --to STORE [--check]

- **current**: the store was made from this folder, by this `kernel.py`,
  under the same reading limits (`MAX_FILE`, `MAX_CHUNK`, `SNIFF`), and every
  file it read still has the same SHA-256, with none added. It is left as it is.
- **built**: anything else, and it says which (`+1 new, ~0 changed, -0
  removed`, `made from another folder`, `made with another kernel.py`,
  `max_chunk changed`). The folder is read again into a scratch file and the
  store replaced whole, so a reader never meets half of one.

A text your folder holds in several places, a memo pasted every month, is
stored once and named from each place. `--check` says current or stale and
why, and writes nothing.

The files it hashes are the ones the kernel reads, through
[index-cache](../index-cache/)'s `manifest`: a dotfile or a binary changing
never makes the store stale.

## From another add-on

    sys.path.insert(0, "adapters/stdlib/pile-store")
    import pile_store

    pile = pile_store.load(STORE, FOLDER)   # None while it doesn't match
    why = pile_store.stale(STORE, FOLDER)   # None, or the reason

`load` gives the passages exactly as `kernel.chunks` reads them, in its order,
each with `date` as `kernel.dates` gives it, so `kernel.rank(pile, bite,
dated=lambda p: [c["date"] for c in p])` answers from the store as it would
from the folder. It opens the store read-only.

## The key

willow-bot's store also matched "the key". This one doesn't: it never reads
or names the key, and a store is only a copy of what the folder already holds,
so it has nothing to seal. A box's own seals stay the kernel's.

## What it reads and writes

It reads the folder and writes only `--to` (the store, and while building, a
scratch file beside it made with `tempfile`); it writes no box, reads no key,
and reaches no network. It refuses to overwrite a `--to` that is there and is
not a pile store. The guard holds it to `writes: to` and `network: none` while
its tests run.

Exit codes, the kernel's: `0` current or built; `42` the folder has nothing to
read, or, with `--check`, the store is stale; `2` refused (a bad command line,
a `--from` that is not a folder, a store inside the folder it reads, a
`--to` whose folder is missing, or a `--to` that is not a pile store).
