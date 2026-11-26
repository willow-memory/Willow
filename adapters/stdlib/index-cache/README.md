<!-- willow-addon
section: Finding things
line: Keeps scan's index between runs and rebuilds it only when a file in your folder actually changed.
source: new
added: 2026-10-26
version: 0.2.0
writes: to
network: none
role: makes
tags: index
uses: batch-ask
-->
# index-cache

[`batch-ask`](../batch-ask/) indexes a folder once so questions are fast; on a big folder
that first read is the slow step. But a folder usually hasn't changed since last
time, and then the index already on disk is still the right one. `index-cache`
keeps a small manifest beside the index — each read file's path and the
SHA-256 of its text — and rebuilds only when the folder actually changed.

    python adapters/stdlib/index-cache/index_cache.py --from FOLDER --to INDEX
    python adapters/stdlib/index-cache/index_cache.py --from @LIST --to INDEX
    python adapters/stdlib/index-cache/index_cache.py --box BOX --to INDEX

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

## only what moved is read

Beside each file's hash the manifest keeps its details on disk (its size,
its modification and change times, its inode) and when the run began. A
later run reads again only a file whose details moved, so a check of
thousands of unchanged files takes a second, not a read of all of them. A
file whose details were last seen changing within two seconds of a run's
start is read again regardless, since it could change again inside the
clock's tick and look the same (git's "racy" files). The change time can't
be set back, so an edit that keeps a file's size and puts its modification
time back is still seen. The index's own files are known whole the same
way: by their details as the run that wrote them left them, and read again
only when those moved.

## a list of files, where they are kept

`--from @LIST` keeps the index of the files a list names (one path a line,
as `gather --point` writes it), read where they are kept, the way a box laid
with `kernel.py init --from NAME=@LIST` reads them (CONST-VI-9). Each file is
named by its path from the folder the listed files share, and its passages
are the kernel's own (`list_chunks`), so the index answers with the same
passages that box does. Only the listed files are hashed: a file beside them
the list leaves out never forces a rebuild, and a listed file that is gone
counts as removed. An index may sit beside the listed files; one that would
hold the list, or a file it names, is refused.

## a whole box

`--box BOX` keeps the index of everything a box reads: its pile folder and
each source, a folder or a list, named as the kernel names the box's
passages (the source's name, a slash, and the path: `pile_of_box`). A box laid from several
places is then asked from one index with the passages its own bite reads;
[claude-code](../claude-code/)'s hook answers from it. For a box with only
a pile it is that folder's index and manifest, so one made with
`--from PILE` stays current. It reads the box's settings file only, never
its record or its key, and refuses an index inside the box or inside, or
holding, anything the box reads.

## what it reads and writes

It reads the folder and writes only under `--to` (the index, and a small
manifest file beside it); it writes no box, reads no key, and reaches no network.
The guard holds it to `writes: to` and `network: none` while its tests run.

Exit codes, the kernel's: `0` the index is current or was rebuilt; `42` the
folder has nothing to read; `2` refused (a bad command line, a `--from` that is
not a folder, or an index and folder that would hold each other).
