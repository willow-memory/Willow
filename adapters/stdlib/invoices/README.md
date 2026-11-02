<!-- willow-addon
section: Keeping track
line: For freelancers: invoices and payments matched by the id pattern you give, never guessed.
source: new
added: 2026-11-01
writes: nothing
network: none
uses: amounts, bank
-->
# invoices

The invoices you sent, which are paid and which are overdue, matched to
their payments by the invoice number alone.

    python adapters/stdlib/invoices/invoices.py --box DIR --id 'INV-\d+' [--now TS]

    overdue  INV-0427  Bramble & Bean Ltd  £680.00  due 2026-07-30, 84 days ago
             invoice   work/invoices/invoice_ledger.csv:228
             last said email/2026-10-06_outstanding-invoices.eml:11
    not due  INV-0440  Fernside Dog Grooming  £173.25  due 2026-10-30, in 8 days
             invoice   work/invoices/invoice_ledger.csv:241

    same sum, no invoice named: check these by hand, never counted as paid
      INV-0434  £520.00  bank/northbank_current_2026-09.csv  2026-09-02  520.00  HPS LTD BACS

    240 invoices: 234 paid, 4 overdue (£2,660.00), 2 not due (£731.00).

`--id` is how your invoice numbers are written, as a regular expression. An
invoice is found by its number in a CSV ledger row (its amount, due date,
client, invoice date, and paid date or status, by column names in any case)
or in a file named for it (its `Total`, `Payment due`, `Invoice date` or
`Date`, and `Bill to` lines). An invoice that gives terms instead of a due
date (`Net 30`, `due within 14 days`) is due that many days after its own
date, as written. Each sum keeps its own currency, and totals in two
currencies are added up apart.

**Paid means a line names it as paid.** A paid date or a status of paid in
its ledger row; money in on a bank statement whose line quotes the number
(`DEPOSIT … REF INV-2022-014`); or any other line with the number and a word
of payment (paid, received, remittance, settled) and none that says
otherwise (unpaid, outstanding, overdue, owed, chase). An amount, a payee or
a date never matches a payment to an invoice: that is the promise.

**What it can't match, it shows.** Clients often pay without quoting your
number. For each unpaid invoice, a bank credit (read by [bank](../bank/)) or
a line in a file that speaks of payment, with the same sum, on or after the
invoice's date, naming no invoice, is listed under its own heading, to check
by hand. It is never counted as paid, so a credit that only looks like one
can't hide an invoice that is still owed.

Overdue invoices come first, oldest due first, each with the latest line
that names it (your last reminder, often). An unpaid invoice due before the
first bank statement in your folder can't be shown paid either way, so it
is not called overdue: those are named together on one line. A due date
that reads either way round (09/11/2026) is not guessed, as the kernel never
guesses one: that invoice says "due date unread".

**Exit codes:** 0 invoices found; 42 none numbered like `--id`; 2 refused
(no box, a pattern that isn't one, or one that matches an empty string).

**Uses:** the kernel's `newest`, `config` and exit codes; bank's
`from_csv` and `amount`; amounts' `sums`.

**Never:** matches a payment by amount, payee or date; writes anything; goes
online.
