<!-- willow-addon
section: Finding things
line: Rebuilds pile-store's saved passages after each change, one build at a time, so your next question doesn't wait for it.
source: bot
added: 2026-10-28
writes: to
network: none
tags: no-install, offline, writes-output, search, pile
-->
# pile-build

[pile-store](../pile-store/) builds a store when you ask. `pile-build` is what
a hook or a timer calls after a change, so the store is current before the
next question comes:

    python adapters/stdlib/pile-build/pile_build.py --from FOLDER --to STORE [--background]

- **One build at a time.** It locks the store's folder (opened read-only, so
  the lock writes nothing). A second call waits, says `waiting` on stderr,
  then finds the store current and does nothing.
- **Until it matches.** The folder can change while it is being read. After
  each build it checks again and builds again, up to three times; a folder
  still changing after that is reported `stale`, exit 42.
- **`--background`** starts itself detached and returns at once, naming the
  process, so a hook never waits on a build.

Without `fcntl` (Windows) there is no lock: two builds may both run, and each
still replaces the store whole, so no reader meets half of one.

## Not the key

willow-bot's builder took orders that said where the key was. This one is
told only the folder and the store; it never reads, holds or names the key.
The idea's line said so; the card's line drops it.

## What it reads and writes

It reads the folder and writes only `--to`, through pile-store (the store,
and while building a scratch file beside it); it writes no box, reads no
key, and reaches no network. It refuses to overwrite a `--to` that is there
and is not a pile store. Exit codes, the kernel's: `0` the store is current,
or a background build was started; `42` the folder has nothing to read, or
it kept changing through three builds; `2` refused (a bad command line, a
`--from` that is not a folder, a store inside the folder, a `--to` whose
folder is missing, or a `--to` that is not a pile store).
