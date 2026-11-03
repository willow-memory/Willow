<!-- willow-addon
section: Finding things
line: Your files sorted into your own categories, by the phrases you gave each: what's where, and what nothing of yours reached.
source: new
added: 2026-11-03
writes: nothing
network: none
output: report
tags: categories
-->
# sort

Your files, sorted into your own categories by the phrases you say mean
each one. The first rung of a sorting of a folder: what fixed phrases can
place is placed, and what they can't is said, never guessed.

```
python adapters/stdlib/sort/sort.py --box DIR --categories FILE [--json]

sort: populated, 4 files: 2 sorted into 2 categories, 1 in more than one, 1 unsorted
## health
  letters/clinic.txt  2 hits: appointment, prescription
## money
  bank/may.txt        3 hits: bank statement 2, invoice
## more than one
  notes/june.md       money 1, health 1
## unsorted
  ideas.md            no phrase of yours
```

**FILE is yours:** one category a line, its name, a colon, and the phrases
that mean it, commas between; a line beginning `#` is a note.

```
money:  invoice, receipt, bank statement
health: prescription, appointment, blood test
```

**How a file is placed.** Each file the kernel reads is sorted by its
passages. A phrase counts where its words come in order, each word matched
as the kernel matches it (its own words and stems, so "invoices" is
"invoice"). A file goes to the category whose phrases it holds most. One
that holds two categories as much is listed under **more than one**, with
each count, for you to choose; one that holds none is **unsorted**. A file
the kernel can't read (a PDF before its reader, an image) isn't here at all:
[box-health](../box-health/) counts those.

**What it leaves to the next rung.** The unsorted and the more-than-one are
what a meaning search or a local model can suggest a place for, through the
kernel's propose, and a person seals; the seal is the correction a learning
sorter keeps, and it's on your record.

**What you sealed comes first.** A file whose category you sealed (a
suggestion [sort-ask](../sort-ask/) made, kept on your record under your
key) goes where your seal says, "sealed by you", before any phrase; a
suggestion still waiting, or one whose bytes changed since you sealed it,
places nothing. That seal is the correction a learning sorter keeps.

It prints [a report](../ci/README.md#the-report-contract), and `--json`
gives the same report as one JSON object.

Exit codes, the kernel's: 0 every file sorted (populated) or none to sort
(empty); 42 a file is in more than one or unsorted, which waits on you; 2
refused (a bad command line, no box, a FILE with no category in it).

**Uses:** the kernel's `chunks`, `words`, `stem` and `config`.

**Never:** writes anything; guesses a category no phrase of yours reached;
reads a file the kernel doesn't.
