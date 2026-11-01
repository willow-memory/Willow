<!-- willow-addon
section: Finding things
line: Keeps scan's index between runs and rebuilds it only when a file in your folder actually changed.
source: new
added: 2026-10-26
writes: to
network: none
tags: no-install, offline, writes-output, search, index
-->
# index-cache

[`scan`](../scan/) indexes a folder once so questions are fast; on a big folder
that first read is the slow step. But a folder usually hasn't changed since last
time, and then the index already on disk is still the right one. `index-cache`
keeps a small manifest beside the index — each read file's path and the
SHA-256 of its text — and rebuilds only when the folder actually changed.

    python adapters/stdlib/index-cache/index_cache.py --from FOLDER --to INDEX

On each run it hashes the folder's files and compares them to the manifest:

- **current** — every file the index was built from is still there with the
  same hash, and nothing was added: the index is left as it is, no passage is
  re-read, and you ask it with `scan` as before.
- **rebuilt** — a file was added, edited or removed: it rebuilds the index
  (through `scan`) and writes the new manifest, saying what moved
  (`+N new, ~N changed, -N removed`).

The files it hashes are exactly the ones the kernel reads into an index — text,
UTF-8, not hidden, under the size cap — so a dotfile or a binary changing never
forces a rebuild. An index made by another `kernel.py` is rebuilt, since its
passages were the other kernel's.

## what it reads and writes

It reads the folder and writes only under `--to` (the index, and a small
manifest file beside it); it writes no box, reads no key, and reaches no network.
The guard holds it to `writes: to` and `network: none` while its tests run.

Exit codes, the kernel's: `0` the index is current or was rebuilt; `42` the
folder has nothing to read; `2` refused (a bad command line, a `--from` that is
not a folder, or an index and folder that would hold each other).
