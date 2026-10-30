<!-- willow-addon
section: Reading more kinds of files
line: Reddit's data export: your posts, comments and saved items as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# reddit

Your Reddit posts, comments and saved items, searchable by day and subreddit.

    python adapters/stdlib/reddit/reddit.py mirror --from FOLDER --to MIRROR

Three kinds of CSV in a Reddit data request are read, told by their headers,
and their rows written oldest first as dated lines:

    2024-03-02 08:15  r/gardening post: Tomatoes want more sun: The bed by the fence is shaded.
    2024-03-03 19:40  r/gardening comment: Move them to bed 2.
    saved https://www.reddit.com/r/gardening/comments/abc/tomatoes/

Posts (title and body), comments (body), and saved posts and comments, which are
a permalink and nothing else, so they have no date. Times are UTC as Reddit
writes them. IP addresses, vote and gilding data and the request's other files
are not copied. Any other CSV is skipped and counted.

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
