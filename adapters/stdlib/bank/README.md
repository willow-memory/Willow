<!-- willow-addon
section: Reading more kinds of files
line: Bank CSV and OFX statements as dated lines, with spending by month.
source: new
added: 2026-10-29
writes: to
network: none
-->
# bank

Your bank statements, searchable by day, payee and amount, with the months added up.

    python adapters/stdlib/bank/bank.py mirror --from FOLDER --to MIRROR

Each transaction of a statement is a dated line, oldest first, and the months
are added up under them:

    2024-03-02  -45.20  TESCO STORES 3241
    2024-03-05  2000.00  ACME PAYROLL

    monthly totals
    2024-03  spent 45.20  received 2000.00  net 1954.80  (2 transactions)

An OFX or QFX statement is read by its `STMTTRN` entries (date posted, amount,
name and memo), in the SGML form banks usually send or in XML. A CSV is a
statement when its header has, named in any case, a date column, a description
column, and either a signed `Amount` or a pair of money out and money in
columns. A negative amount is money spent. A date is read as the kernel reads one, so one that reads either way
round (03/04/2024) is never guessed: that row is written without a day and left
out of the months. Account numbers, balances and the rest are not copied. Any
other CSV is skipped and counted.

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
