<!-- willow-addon
section: Reading more kinds of files
line: Jira's issue export, CSV or XML: each issue, comment and status change as dated passages.
source: new
added: 2026-10-29
writes: to
network: none
-->
# jira

Your Jira issues, searchable by key, status, person and comment.

    python adapters/stdlib/jira/jira.py mirror --from FOLDER --to MIRROR

Each issue is a dated passage, oldest first:

    GARDEN-12 (Open, Bug) 2024-03-02 ana -> ben: Tomatoes want more sun [garden, urgent]
      The bed by the fence is shaded after noon.
      comment 2024-03-03 ben: Move them to bed 2.

The first line has the key, status and type, the day created, who reported it and
who it is assigned to (when it says), the summary and the labels. The description
follows, with its HTML taken off as the kernel reads a page, and then the
comments. Both exports are read: the XML (an RSS file of items with a key) and
the CSV (with `Summary` and `Issue key` columns, repeated `Labels` and `Comment`
columns allowed). Jira's exports hold no history of status changes, so none is
written. Attachments, links, sprints and custom fields are not copied. Any other
XML or CSV is skipped and counted, and a file that declares entities is not
read.

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
