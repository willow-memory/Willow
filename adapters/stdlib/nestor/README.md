<!-- willow-addon
section: Trust and proof
line: Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when.
source: new
added: 2026-10-31
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# nestor

Answers a person has checked in Nestor, from a copy of its store.

    python adapters/stdlib/nestor/nestor.py mirror --from FOLDER --to MIRROR

    tomatoes want sun
    checked by: ada
    when: 2026-10-01
    status: sealed

Walks FOLDER for SQLite files that hold Nestor's checked pairs (a verifier
named, not a draft). Each pair becomes one paragraph citing who checked it
and when. Signatures stay in the store: they are never copied into the
mirror. The original is only read, through SQLite's own read-only open.

Each store is written to MIRROR at the same relative path with .txt
added. A file that is not a Nestor store, or that holds no checked pair,
is skipped and counted. Point the kernel at MIRROR to ask what was
checked.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** writes inside FOLDER, copies a signature, or reads the key.
