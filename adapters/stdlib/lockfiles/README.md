<!-- willow-addon
section: Reading more kinds of files
line: Lockfiles as passages (package-lock.json, pnpm-lock.yaml, poetry.lock, uv.lock, Cargo.lock, go.sum): each package and its locked version.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# lockfiles

Your lockfiles, searchable by package and version.

    python adapters/stdlib/lockfiles/lockfiles.py mirror --from FOLDER --to MIRROR

Seven lockfiles are read, by their names: package-lock.json, yarn.lock,
pnpm-lock.yaml, Cargo.lock, poetry.lock, uv.lock and go.sum. Each is a heading
and a line for each locked package, in name order:

    lockfile: package-lock.json (npm), 3 packages
    lodash 4.17.21
    left-pad 1.3.0
    left-pad 0.0.3

A package locked at two versions is two lines, and a repeated line is written
once. Integrity hashes, resolved addresses and dependency lists are not copied.
Python 3.9 has no TOML reader, so the three TOML lockfiles are read by their
package blocks' name and version lines, and pnpm and yarn by the shape of their
package keys. A file with no package is skipped and counted.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
