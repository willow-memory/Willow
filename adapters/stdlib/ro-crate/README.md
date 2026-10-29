<!-- willow-addon
section: Trust and proof
line: A box snapshot as an RO-Crate research object Zenodo can read: each file with its hash and licence.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# ro-crate

Your box as a research object another tool can read.

An RO-Crate is a folder of files with one description of them in JSON-LD,
which repositories such as Zenodo and the tools around research objects
understand. This writes your box as one: the files it searches, the record,
the suggestions and the answers you approved, each file described with its
hash and its licence.

    python adapters/stdlib/ro-crate/ro_crate.py --box DIR --to FOLDER --licence CC-BY-4.0
    wrote FOLDER/willow-crate-20261029-100000.zip: 396 files, 12 rows; licence: CC-BY-4.0

The zip holds:

| In the zip | What |
|---|---|
| ro-crate-metadata.json | the description: every file with its SHA-256, size, kind and licence, and the crate's date |
| files | your folder's files, as they are, hidden ones left out |
| record.jsonl | the record, so the chain can be checked |
| proposals and written | the suggestions handed in and the answers you approved |

The description names the record's tip (the hash of its last row) and the
number of rows, so the crate pins the record as it stood; restore the zip as
a box and run `kernel.py verify` to check it. Names in the description are
links, so a space is %20, while the zip keeps the plain name.

`--licence` names the licence every file is offered under: an SPDX identifier
such as CC-BY-4.0 or CC0-1.0, or a link. It is never guessed. Without one the
crate says none, and so does the output, and a repository will ask you.

Your key is not in it and this never reads it; neither is the box's settings
file, which says where the key lives. A FOLDER inside the box or your files,
or the key's own folder, is refused. The copy is checked before it is kept:
every file's bytes and hash match the description, or it is deleted and the
run fails. The same box and `--now` give the same bytes, and a crate is never
written over another.

**What it doesn't do:** upload anything, or check that a licence suits your
files. Your files are yours to license; this copies what you name.

Exit codes, the kernel's: 0 written and checked; 2 refused (a record that
doesn't verify, a FOLDER it won't use, a bad command line).

**Uses:** the kernel's `read` and `config`.

**Never:** reads the key, changes the box, or writes anywhere but FOLDER.
