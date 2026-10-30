<!-- willow-addon
section: Reading more kinds of files
line: LinkedIn's data export: messages, posts and connections as dated lines.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# linkedin

Your LinkedIn messages, posts, comments and connections, searchable by day and person.

    python adapters/stdlib/linkedin/linkedin.py mirror --from FOLDER --to MIRROR

Four of the export's CSV files are read, each told by its header, and their
rows are written, oldest first, as dated lines:

    2024-03-02 08:15  message Ana Lopez -> Ben Ruiz: [Garden talk] Are you coming on Saturday?
    2024-03-03  connected with Ana Lopez (Gardener, Garden Co)
    2024-03-04  post: Planted out the tomatoes. https://example.org/guide
    2024-03-05  comment: Congratulations!

Messages (`CONVERSATION ID`, `FROM`, `TO`, `DATE`, `CONTENT`), connections
(`First Name`, `Connected On`), shares (`Date`, `ShareCommentary`) and comments
(`Date`, `Message`). The connections file starts with a few lines of notes before
its header, which are skipped. Email addresses, profile addresses and the other
columns are not copied; any other CSV is skipped and counted.

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
