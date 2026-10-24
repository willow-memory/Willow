<!-- willow-addon
section: Trust and proof
line: Where two copies of a folder or a box part, a backup zip included, narrowed to the first row, file and line that differ.
source: bot
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, trust, everyday
-->
# diverge

Where two copies part: your box and its backup, two copies of a folder,
yesterday's zip and today's.

    python adapters/stdlib/diverge/diverge.py ~/willow/box /media/usb/willow-backup-20261024-093000.zip

    records: the same for 41 rows, then B runs on 1 more
    only in A:  written/dentist.md
    differ:     notes/todo.txt (first at line 3)
      A: Call the bank
      B: Call the bank on Monday

Each side is a folder or a `.zip`. It narrows level by level:

| Level | What it says |
|---|---|
| records | when both hold a record: how many rows they share, then the row where they part, or which runs on past the other. Rows are compared whole, so an edited row parts them even if its `hash` field wasn't touched. |
| files | the files only one side holds, and those both hold that differ |
| line | in the first file that differs, the first line that does, from each side |

Hidden folders are left out, as the kernel leaves them out. A key is never
read: a file that a box's kernel.json names as its key is skipped if it
sits inside what's compared (as [start](../start/) puts it, beside the box).
"The same" means every file, byte for byte.

**Where it comes from:** [willow-bot's diverge](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/diverge.py), which finds where two
branches or two boxes' chains part.

Exit codes, the kernel's: 0 the same; 42 they differ; 2 refused.

**Never:** reads a key, or writes anything.
