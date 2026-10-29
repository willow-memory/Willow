<!-- willow-addon
section: Keeping track
line: Receipts and warranties: when the dishwasher's cover ends, and where its receipt is.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# warranties

Receipts and warranties: when the dishwasher's cover ends, and where its
receipt is.

```
python adapters/stdlib/warranties/warranties.py --box DIR [--now TS]

Kettle      ended 2026-01-10 (292 days ago)  bought 2025-01-10  receipt: not found
Dishwasher  ended 2026-03-02 (241 days ago)  bought 2024-03-02  receipt: receipts/dishwasher.txt
Oven        ends 2026-10-30 (in 1 day)  receipt: not found
3 warranties
```

**What counts.** A line that says warranty, guarantee or guaranteed and names
a thing at its start ("Dishwasher, bought 2024-03-02, 2 year warranty"; "Fridge:
warranty until 2027-05-01"; "2025-01-10 Kettle - 1 year guarantee"). The thing
is the words before the first comma, colon, dash, bracket or word like
"bought", "extended" or "warranty".

**When the cover ends** is the date the line says after "until", "till",
"expires", "ends", "valid to" or "through"; else the day bought plus the length
the line says (2 year, 18 months, three years). The day bought is the date
after "bought", "purchased" or "from", else the line's own day, read as the
kernel reads one (its `newest`), else the nearest date written above it in its
file, else the date its file is named for. A line with no way to place the end
is not listed; a day such as 06/12/2024, which reads either way round, is never
guessed, so a certificate that gives only that is not listed either (on
willow's Teodora demo, her boiler's certificate is one).

**Where its receipt is** is what the line says after "receipt" ("receipt: red
folder"), else a file of yours whose path names a receipt and the thing, else
"not found". Nothing is guessed from how the words look.

When a thing has several lines the latest one counts. Soonest to end first,
measured from `--now` (an ISO timestamp, the kernel's kind; today if not
given). [renewals](../renewals/) lists the expiries your documents state;
this works out the end of a cover from the day bought, and finds the receipt.

It only reads. Exit codes, the kernel's: 0 warranties found; 42 none; 2
refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and the
[car](../car/) add-on's `entries`, `to_date` and `add_months`.

**Never:** changes your files; writes anything, even the record.
