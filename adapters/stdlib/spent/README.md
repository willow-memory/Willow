<!-- willow-addon
section: Keeping track
line: How much you spent on one thing in a year, the money-out lines that say it added up, each cited so you can check it.
source: new
added: 2026-11-16
version: 0.1.0
writes: nothing
network: none
role: tools
uses: habits
-->
# spent

How much you spent on one thing in a year, the money-out lines that say it added up, each cited so you can check it.

    python adapters/stdlib/spent/spent.py --box DIR [--now TS] [--year calendar|financial[:MM]] "how much did we spend on electricity this year"

No one passage says what a year of electricity came to: it is a sum over the
lines of your statements, and the kernel serves one passage. This finds the
lines that spent money on what you named, adds them up, and lists every line
it added, with its file and line number, so each can be checked.

```
spent: electricity (electricity = energy, origin)
period: calendar 2026, 2026-01-01 to 2026-10-24 (so far)
2026-01-25  446.06  Bank/FY25-26.csv:124  25/01/2026,"-446.06","BPAY ORIGIN ENERGY 6631094"
2026-04-25  479.80  Bank/FY25-26.csv:50   25/04/2026,"-479.80","BPAY ORIGIN ENERGY 6631094"
2026-07-25  728.50  Bank/FY26-27.csv:77   25/07/2026,"-728.50","BPAY ORIGIN ENERGY 6631094"
total: 1,654.36 in 3 payments
```

**The words** are the question's words, less the words the kernel never
counts (how, much, did, we, on), the words that only say it is a sum (spend,
spent, pay, paid, total, cost, money) and the words that say the period (this,
last, year, financial, fiscal, fy, calendar). Give the question in quotes, or
just the thing: `"electricity"`. A line is counted only when it holds all of
them, the way the kernel holds a word (a plural counts), and through the
box's words list: with `electricity = energy, origin` in it, a line that says
ORIGIN ENERGY holds "electricity". Not half of them, as the kernel serves a
passage: a total with a line in it that never said the thing is a wrong
total. A line is judged on its own words, never on its file's name.

**Which lines.** A line that says its own date (never one borrowed from above;
a date that reads both ways, 03/04/2026, is never guessed) and writes an
amount to the cent (`45.20`, `-45.20`, `$9.00`, `£1,240.50`). It is money out
when the amount is written with a minus before it, as a statement writes it,
or sits in the money-out column of a statement whose header names one (Debit,
Paid out, Money out, Withdrawals). A plus is money in and is never added.
**An amount with no sign is never added either**: some banks write money in
unsigned (Teodora's bank does), and an email's "45.20" is only a price, so
the sign is the only thing that says it went out. Such a line is listed apart,
as is one that holds the words with a minus and no date it can read, and one
dated after `--now`, which is not spent yet. Each says why it was left out, and
the total is only what is written as money out. A total that leaves out a
payment you can see listed is one you can correct by hand; a total that adds
money in is wrong without saying.

**The period.** "this year" and "last year" in the question pick a calendar
year of `--now`; "financial year" (or "fiscal year", "fy") picks a financial
year, which starts on 1 July, as in Australia. `--year financial:4` starts it
on 1 April; the UK's tax year starts on 6 April, which a start month can't say,
so it is not that. `--year` says what a year is when the question doesn't, and
with no "this" or "last" it means this year. With neither, every date counts.
The period is always printed, and a year not yet over is counted up to `--now`
(its default is the clock; give one for the same output every time).
"Last month" is not a period here: only years.

**The same payment** on the same day, for the same amount and currency, in two
files (a statement and a copy, or its rows pasted into a note) is one payment
when the two lines say the same words or share a word besides the ones asked
for: counted once, the other file named beside it. Two equal lines in one file
are two payments, and two places that share only what you asked for ("cafe")
are two.

Amounts keep their currency: £, $ and € are each totalled on their own, and an
amount with no sign is a currency of its own (said so when there is more than
one). They are never added together.

On willow's demo folders: Bernadette's "electricity", with the words
`electricity = energy, origin` her own list holds, finds her four quarterly
Origin BPAYs of 2025-26 (2,206.28) and three of 2026 (1,654.36).

It only reads. **Exit codes**, the kernel's: 0 some money out was found; 42
none; 2 refused (no box, no question or more than one, a `--year` it doesn't
know, a `--now` with no date, a question with only words that say it is a sum,
a words list others can read).

**Uses:** the kernel's `chunks`, `newest`, `words`, `forms`, `held_by`,
`FUNCTION`, `config` and `read_words`, and [habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; adds money
in, or an amount that doesn't say which way it went; adds two currencies.
