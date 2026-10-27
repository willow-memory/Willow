<!-- willow-addon
section: Keeping track
line: Who owes whom, from the IOUs in your notes and messages, each cited.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# debts

Every line of your folder that speaks of money owed, as a dated listing,
oldest first, each with the sum it names and where it is: the footy debt in
a chat, the IOU in a notebook, the "first £100 back" that answers it.

```
python adapters/stdlib/debts/debts.py --box DIR

2023-04-17  $10   chats/mags.txt:3   Terry says Gerry owes him $10 from the footy
2025-02-28  £100  chats/teo.txt:9    first £100 paid back, thank you again x
undated     -     notes.md:4         I still owe Dev for the mixer
3 lines speak of debts: 2 with a sum, 1 undated
```

**What speaks of a debt.** A line saying one of the owing words — owe, owes,
owed, owing, IOU, repay and its forms, paid back, pay back — or saying lent
or borrowed with a sum of money on the same line. The sum is read as
[amounts](../amounts/) reads one (a number written with its currency, never
a bare number); a line that names none shows a dash, since the debt is
written and the amount is the line's to say. Things lent and returned — the
drill, the cake pan — are [lending](../lending/)'s; money is this one's, so
the two never read the same line twice.

**Nothing is netted.** Who owes whom is what each line says, in its own
words: a "paid back" line is listed beside the debt it answers, dated, and
whether anything still stands is your files' story to finish, not a balance
this invents. A debt your files state twice is listed twice, as Bernadette's
footy debt is: Terry says it every year, and the listing says so.

**Dated as the files say.** A line's date is the latest it says, read as the
kernel reads one (its `newest`; 11/03/2026, either way round, is never
guessed); a line that says none takes the nearest date written above it in
its own file, else the date its file is named for, and the listing says
which. Undated debts come last: your files don't say when.

On willow's demo folders, Bernadette's five lines include Gerry's $10 footy
debt three times over three years and a rematch owed at the pub (no sum, a
dash); Teodora's two include the mixer she still owes Dev for; Odile's folder
speaks of none, and it says so.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 debts spoken of; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and the amounts
add-on's reading of a sum.

**Never:** changes your files; writes anything, even the record; nets a
balance or settles a debt; reads a lent drill as money.
