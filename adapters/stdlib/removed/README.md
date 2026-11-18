<!-- willow-addon
section: Trust and proof
line: A file you are about to delete or archive written on the record first: its name, size and SHA-256, never its words, so the hole stays.
source: new
added: 2026-11-18
version: 0.1.0
writes: record
network: none
role: makes
-->
# removed

Your files are yours to delete, archive or pack away. The record is
append-only, so it can keep the hole: that a file was there, what it was
called, how big it was and the fingerprint of what it held. Never what it
said.

    python adapters/stdlib/removed/removed.py --box DIR --root DIR [--how deleted|archived] [--to ARCHIVE] [--what TEXT] NAME [NAME ...]

    removed  notes/draft.md  412 bytes  9f2c41d0a7b3…
    row 57: 1 file, deleted

Run it **before** you take the files away: it reads each one to fingerprint
it, writes one `removed` row through the kernel's own `append`, and touches
nothing else. Taking the files away is yours, with whatever you use.

- **`--root`** is the folder the names are in. Each NAME is a file inside
  it, written on the row as given, so the row holds no path of your machine.
- **`--how`** says what you are doing with them: `deleted` (the default) or
  `archived`.
- **`--to ARCHIVE`** names the archive they went into, when there is one.
  The row keeps its file name and its SHA-256, so the archive can be held
  to the record later, and each file in it to its own fingerprint.
- **`--what`** is a word of your own for what these were (`shelf`, `drafts`).

A row is written once for all the names. If one can't be read, or isn't a
file inside `--root`, nothing is written.

This is not for the folder your box reads: [what-changed](../what-changed/)
says what was deleted there, on its own row. It is for everything else you
keep beside a record and one day clear out.

Exit codes, the kernel's: 0 the row is written; 2 refused (a record that
doesn't verify, a name that is not a file inside `--root`, a `--root` that
is the box or inside it, an archive that can't be read).

**Uses:** the kernel's `read`, `append`, `now` and its exit codes.

**Never:** deletes, moves or changes a file; reads a file's words into the
record; reads the key; names a file of the box itself.
