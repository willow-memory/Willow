<!-- willow-addon
section: Reading more kinds of files
line: A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# mastodon

Your Mastodon or Pixelfed posts, searchable by day.

    python adapters/stdlib/mastodon/mastodon.py mirror --from FOLDER --to MIRROR

Each post you made is a dated line, oldest first:

    2024-03-02 08:15  Planted out the tomatoes today.
    2024-03-03 19:40  [cw: gardening] The slugs are winning. (reply)  [image: slug on a leaf]

The post's HTML is read as the kernel reads a page: tags out, entities read. A
content warning is kept in front in brackets, a reply is marked, and an
attachment's description (its alt text) is kept as [image: ...] or
[attachment: ...]. Boosts and likes are not your words and are left out, as are
the media files. Only an ActivityPub outbox (a JSON object with `orderedItems`)
is read; other JSON is skipped and counted.

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
