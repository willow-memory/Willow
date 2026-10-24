<!-- willow-addon
section: Keeping track
line: Things you lent, to whom and when, and which are still out.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# lending

What you lent, to whom, and whether your files say it came back.

    python adapters/stdlib/lending/lending.py --box DIR

    OUT        good drill  to Teo  since 2026-08-30  no return written
               2026-08-30  notes/2026-08-30.md:2   Lent Teo my good drill.
    PART BACK  Foxfire set  to Mara  since 2026-10-01  parts out: 2 of 3
               2026-10-01  notes/2026-10-01.md:1   Mara borrowed the Foxfire set (3 volumes).
               2026-10-24  notes/2026-10-25.md:1   2026-10-24 Mara gave back volumes 1 and 3.  (filed 2026-10-25)
    BACK?      cake pan  from Priya  back, no loan written
               2026-08-30  notes/2026-08-30.md:3   Priya returned the cake pan.
    BACK       ladder  to Dev  2026-08-02 to 2026-08-30

A line counts when it says you **lent** or **loaned** something, someone
**borrowed** it, you **got** it **back from** them, or they **returned**,
**gave back** or **brought back** it. The person is the capitalised word;
"lent Mara the set" and "lent the set to Mara" are the same loan.

- **Every line stays.** A loan is shown with each line about it, in the order
  they happened, with its file and line. A return doesn't replace the loan; it
  is listed under it.
- **A thing in parts is out until every part is.** "The Foxfire set
  (3 volumes)" is three parts; "gave back volumes 1 and 3" leaves part 2 out.
  One label on a box of three is how a part goes missing.
- **Absence is said as what it is.** No line saying it came back is "no
  return written": your files don't say it's back, which is not the same as
  saying it isn't. A return with no loan before it is listed too, as "back,
  no loan written", not dropped.
- **Two dates are two facts.** A line's own date and the date its file is
  named for can differ (a note written up the next morning). When they do,
  both are shown and neither is picked.

Out comes first, then part back, then returns with no loan, then back; within
each, oldest first.

**Exit codes:** 0 found some; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `dates`, `newest`, `words` and `config`.

**Never:** writes anything, or guesses that something came back.
