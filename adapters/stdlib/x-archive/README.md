<!-- willow-addon
section: Reading more kinds of files
line: An X (Twitter) archive: your posts, replies and DMs as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
-->
# x-archive

Your X posts and direct messages, searchable by day.

    python adapters/stdlib/x-archive/x_archive.py mirror --from FOLDER --to MIRROR

An X archive keeps its data in .js files: JSON after an assignment, such as
`window.YTD.tweets.part0 = [ ... ]`. The two that are your words are written,
oldest first, as dated lines:

    2022-03-02 08:15  Planted out the tomatoes. https://example.org/guide
    2022-03-03 19:40  @ana the slugs are winning. (reply)
    2022-03-04 09:00  dm 12-34: 12: are you coming on Saturday?

A post's text has its entities read (&amp; is &) and each shortened t.co link
replaced by the address it stood for; times are UTC; a reply is marked. A direct
message line names the conversation and the sender's id, since the archive keeps
no names. The archive's other files (likes, followers and the rest) and any other
.js are skipped and counted. Media files and metrics are not copied.

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
