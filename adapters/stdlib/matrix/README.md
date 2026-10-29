<!-- willow-addon
section: Reading more kinds of files
line: Element's room export, JSON or HTML: one dated line per message in each Matrix room.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# matrix

Your Matrix rooms, searchable by day, room and who said it.

    python adapters/stdlib/matrix/matrix.py mirror --from FOLDER --to MIRROR

Each message is a dated line, oldest first, with the room and who said it:

    2024-03-02 08:15  Garden Club  @ana:example.org: Six hours of sun.
    2024-03-02 08:16  Garden Club  * @ben:example.org waves

The time is the message's origin server time, in UTC. Plain messages, notices
and emotes are kept; an image or file message is written as its description,
for example `[image] tomato.png`; empty messages and every other event (joins,
topic changes, reactions, redactions) are left out. A room with no name is named
by its topic. Only the JSON export is read (not the HTML one); other JSON is
skipped and counted.

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
