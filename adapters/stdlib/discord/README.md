<!-- willow-addon
section: Reading more kinds of files
line: Discord's data package: your messages, one dated line each, by server and channel.
source: new
added: 2026-10-29
writes: to
network: none
-->
# discord

Your Discord messages, searchable by day, server and channel.

    python adapters/stdlib/discord/discord.py mirror --from FOLDER --to MIRROR

Point it at the zip Discord's data package gives you: it is read as the zip it
is, without unpacking it. The messages you sent are dated lines, oldest first:

    2024-03-02 08:15  Garden Club #garden  Six hours of sun.
    2024-03-02 08:16  Direct Message with ben  See you Saturday.

A channel is named from its channel file (the server, then #channel) or, for a
direct message, from the package's message index; one with neither is
"channel" and its id. Both the older JSON and the newer CSV message files are
read. A message with only an attachment is written as "[attachment]". The
package holds only your own messages, so a line has no author. A zip that is
not a data package is skipped and counted, and a member over 5 MB is left out, and a zip of more than 20,000 members is not read.

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
