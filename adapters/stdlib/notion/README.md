<!-- willow-addon
section: Reading more kinds of files
line: Notion's export zip, Markdown and CSV, as plain text with each page's title and path.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# notion

Your Notion workspace, searchable by page, path and database row.

    python adapters/stdlib/notion/notion.py mirror --from FOLDER --to MIRROR

Point it at the zip Notion's export gives you: it is read as the zip it is,
without unpacking it, and so is a zip nested inside it (large exports come in
parts). Each page and database is written with its path:

    page: Garden / Veg / Tomato notes

    Created: March 2, 2024 8:15 AM
    Plant out after the last frost.

    table: Garden / Seed orders
    Name | Qty | Supplier
    Basil | 3 | Seeds Ltd

The path is the page's folders and title with Notion's 32-digit ids taken off,
joined with " / ". A page's first heading is its title and is not repeated; the
Markdown is otherwise kept as written. A database's CSV keeps its header and
rows, cells joined with " | ". Images and other files are not copied. A zip
whose pages are not named with Notion's ids is skipped and counted, and a member over 5 MB is left out, and a zip of more than 20,000 members is not read.

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
