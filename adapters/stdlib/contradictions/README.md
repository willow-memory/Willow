<!-- willow-addon
section: Trust and proof
line: Two passages that disagree about the same date or amount, side by side.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# contradictions

Two lines in your folder that say the same thing but give a different date or
a different amount, side by side.

    python adapters/stdlib/contradictions/contradictions.py --box DIR

    AMOUNT  rent, flat
            lease.md:1  $1,200        Rent for the flat is $1,200 a month.
            notes.md:1  1250 dollars  Rent for the flat is 1250 dollars a month now.
    DATE    wedding, dinner
            mail/ana.txt:2  2026-06-19  Reminder: the wedding dinner is on 19/06/2026.
            plans.md:3      2026-06-12  The wedding dinner is on 2026-06-12.
    2 disagreements, 4 lines with a date or an amount read; neither side is picked.

**Neither side is picked.** Both lines are shown as written, with their file
and line, in file order: never by which is newer, never merged, never
rewritten. Which one is right, or whether both are, is yours to say.

**The same thing, by a rule you can check.** Take each line's own words,
leaving out small words like "the" and "on" (the kernel's list), numbers,
units, months and weekdays. Two lines say the same thing when they share at
least two of those words, and at least half the shorter line's (as the
kernel matches words: "tomato" and "tomatoes" are one). "Note to self: the
MOT for the van is due on 2026-11-03" and "Rang the garage. Van MOT is due
2026-11-10" are the same thing. One word in common is a label ("Date:",
"Rent is"), not a subject, so "Rent is $900" and "Rent is $950" are left
alone.

**Records of one kind are left alone, and counted.** Most dates and amounts
that differ in a folder are not a disagreement: they are invoices, tax years
and receipts, each with its own. So these are never compared:

- **Files named alike but numbered differently:** INV-0012.txt and
  INV-0013.txt, one year's tax summary and the next.
- **A subject said in the same words on three lines or more:** a form's
  field ("Total due:" on every invoice) or a table's rows. The cost: a date
  said three times, once wrongly, isn't shown.
- **Two items one after the other in a list:** "* Nearside front tyre worn
  to 1.8mm" and "* Offside front tyre worn to 2.0mm".

- **A date is the kernel's reading**, its `newest`: 2026-06-12, 20260612, or
  a day and month either way round when one is over 12 (19/06/2026). 03/04/2026
  could be March or April, so it is never read, never guessed.
- **An amount is a number with a currency or a unit**: $, €, £, ¥ before it
  ($1,200, €45), or after it a currency (USD, dollars, euros), a percent, or
  a weight, length, volume or time (kg, lb, km, miles, ml, hours, days,
  years...). Only one unit is compared with itself, so "40 euros" and "€45"
  disagree, "2 kg" and "2 lb" don't. $1,200 and $1200.00 are one amount. The
  dot is the decimal point; "$5k", "$1.2 million" and ranges like "5-10 kg"
  aren't read.
- **One line, one value.** A line giving two dates ("moved from 2026-05-01
  to 2026-05-08") or two different amounts of one unit isn't read for them.
- **When it was written is not what it says.** A date starting a line is its
  stamp. Two lines written on different days (by that stamp, a date heading
  above them, or a file named for the day) are a log's entries or a plan that
  changed, which this can't tell from a mistake: they are left alone, and the
  count of them is said.

**What it can't see:** meaning. Two lines that say the same thing in wholly
other words ("the ceremony is on 2026-06-12" and "we marry on 2026-06-19")
are not matched, and two different things said in much the same words are:
"Ed paid $40 for gas" and "Jo paid $55 for gas", or two dentist
appointments. Side by side, a person sees which is which at once. It reads one line at a time, so a date said in the line
before isn't joined to it.

Nothing to read is "Nothing in your folder states a date or an amount this
can read"; lines read but none disagreeing is "No two lines saying the same
thing disagree", with how many were read.

**Exit codes:** 0 found some; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `stem`, `FUNCTION`,
`HOLD` and `config`.

**Never:** writes anything, says which side is right, or reads a date it
would have to guess.
