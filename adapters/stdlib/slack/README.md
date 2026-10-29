<!-- willow-addon
section: Reading more kinds of files
line: Slack's export zip: one dated line per message, with channel and author.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# slack

Your Slack workspace export, searchable by day, channel and author.

    python adapters/stdlib/slack/slack.py mirror --from FOLDER --to MIRROR

Point it at the zip a Slack export gives you: it is read as the zip it is,
without unpacking it to disk. Each message is a dated line, oldest first:

    2024-03-02 08:15  #garden  ana: Six hours of sun, @Ben Ruiz?
    2024-03-02 08:16  #garden  Ben Ruiz: See the guide @here

The author is the user's display name (else the real name, else the name) and
the channel is its folder name. Slack's own markup is read as words: a user as
@name, a channel as #name, a link as its label, `<!here>` as @here, and the
entities as the characters. Joins, leaves, topic changes and similar messages
are left out; files and reactions are not copied. A zip that is not a Slack
export is skipped and counted, and a member over 5 MB is left out, and a zip of more than 20,000 members is not read.

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
