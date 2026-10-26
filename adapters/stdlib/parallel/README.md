<!-- willow-addon
section: Reading more kinds of files
line: A reader run over several folders at once, across every CPU core, so a big mirror of many sources builds in a fraction of the time.
source: new
added: 2026-10-26
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# parallel

A reader (like [notes](../notes/) or [mail](../mail/)) turns one folder of files
into a mirror of plain-text passages the kernel can search. Reading a big
collection is the slow step, and
a collection is usually **many** folders — vaults, exports, inboxes.
`parallel` runs the reader on each folder at once, one worker per core.

    python adapters/stdlib/parallel/parallel.py --reader NAME \
        --from FOLDER [--from FOLDER ...] --to MIRROR [--jobs auto|N]

Each folder is mirrored into `MIRROR/<folder name>` by the reader itself, so a
sub-mirror is byte-for-byte the reader's own output — a reader that looks across
a folder (notes' backlinks, say) still sees all of it, because the whole folder
goes to one worker. The folders must have **distinct names**, since each is a
sub-mirror under `MIRROR`. `--jobs` is `auto` (one worker per core, the default)
or a positive number; the output is the readers' own, so the same folders give
the same bytes at any job count.

Why many folders and not one split folder: a reader takes a whole folder, and
some readers read across it (backlinks, link graphs), so splitting one folder
between workers would give each an incomplete view and the wrong bytes. Running
whole folders in parallel keeps every reader correct.

## what it reads and writes

It runs the readers and sums what they wrote; it writes only under `--to`
(through the readers), reads no box or key, and reaches no network. The guard
holds it to `writes: to` and `network: none` while its tests run.

Exit codes, the kernel's: `0` some folder had something to read; `42` none did;
`2` refused (a bad command line, an unknown reader, a `--from` that is not a
folder, two folders with the same name, a folder and mirror that hold each
other, or a reader that refused).
