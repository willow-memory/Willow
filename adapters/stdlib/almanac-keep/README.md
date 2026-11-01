<!-- willow-addon
section: Reading more kinds of files
line: An Almanac entry's best permitted copy, from the publisher or its ranked recovery list, fetched into your folder with its SHA-256.
source: new
added: 2026-11-01
writes: to
network: the copy's address, fetched once
tags: no-install, online, writes-output, file-reader
-->
# almanac-keep

An [Almanac](https://github.com/almanac-data) entry's best permitted copy,
fetched into a folder of yours.

    python adapters/stdlib/almanac-keep/keep.py --catalog FILE --id ID --to FOLDER

    kept      epa-ejscreen.html   from: wayback, timestamped, captured 2025-02-04
              sha256 …   (the almanac has no fingerprint to compare)

An Almanac is a catalog, not a host: each entry points at a public dataset
where its publisher keeps it, and when one is lost, the entry's `recovery`
list says where copies are, ranked by how verifiable each is. The Almanac
points; you keep. This fetches one copy into FOLDER through the
[snapshot](../snapshot/) add-on, so you hold it, with its address, time and
SHA-256.

It tries, in order, and keeps the first that answers:

1. the publisher's own address, when the entry's status is `live` or `frozen`;
2. each recovery copy, best authenticity first: hash-verified,
   cross-archive, timestamped, asserted. A copy marked `excluded` is never
   tried, and one marked `review` only with `--review`.

A Wayback Machine capture is fetched raw (its `id_` address), the page as it
was archived rather than inside the archive's toolbar, so its bytes can be
compared with the entry's fingerprint. The output says whether they match.

The file is named by the entry's id, with an extension from its type, and
fetched once: run it again into the same folder and it refuses. Each try is a
line in the snapshot log, including the copies that didn't answer, with
`almanac_id` and `copy` saying where it came from. Point a box at FOLDER to
ask questions of what you kept.

FILE is a vertical's catalog.json (the [almanac](../almanac/) add-on reads
the same file).

**Exit codes:** 0 kept a copy; 42 nothing permitted to try, or nothing that
was tried answered; 2 refused (no such catalog or id, or the name is already
in FOLDER).

**Uses:** the snapshot add-on's `save` and `lines`, and the kernel's exit
codes.

**Never:** tries a copy marked `excluded`, writes outside FOLDER, or changes
the catalog.
