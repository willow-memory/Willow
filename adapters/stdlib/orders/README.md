<!-- willow-addon
section: Reading more kinds of files
line: Amazon's order history and other shops' CSV exports: what you bought, when, and for how much.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# orders

What you bought, searchable by item, day and price.

    python adapters/stdlib/orders/orders.py mirror --from FOLDER --to MIRROR

Each item of an order-history CSV is a dated line, oldest first:

    2024-03-02  Basil seeds, 3 packets  GBP 4.50  (order 026-1234567-8901234)
    2024-03-09  Garden twine  GBP 6.99  (order 026-7654321-0987654)

A file is an order history when its header has a date column (`Order Date` or
`Date`), a column naming the item (`Product Name`, `Title`, `Item` or
`Description`) and one for what it cost (`Total Owed`, `Item Total`, `Total`,
`Amount` or `Price`): Amazon's current and older exports and the order exports of
many other shops. The first column of each kind is used. The order number and
currency follow when the file has `Order ID` and `Currency` columns. A date that
reads either way round (03/04/2024) is never guessed: the row is written without
a day. Addresses, payment cards and email addresses are not copied. Any other CSV
is skipped and counted.

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
