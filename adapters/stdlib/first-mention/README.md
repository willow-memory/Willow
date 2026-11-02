<!-- willow-addon
section: Finding things
line: When your files first mention something, and the line that does.
source: new
added: 2026-10-27
writes: nothing
network: none
-->
# first-mention

When your files first mention something, and the line that does: the first
time the knee was trouble, when the mould began, when a name enters the
story.

    python adapters/stdlib/first-mention/first_mention.py --box DIR "mould"

    first mention of "mould": 2026-03-01
      tenancy/log.md:3  2026-03-01 Reported the mould in the back bedroom.
    48 mentions in 5 files, 2026-03-01 to 2026-09-02; 3 undated, which could be earlier

**What counts as a mention.** A line that itself holds every one of your
content words, each read the kernel's way: your words list, and a word's
plain form, so "owes" finds "owed" and, with a `mum = margaret` line, "mum"
finds Margaret. The line has to say it: a folder named dad holds the word
for asking a question, but writes no mention.

**How mentions are dated, and the first chosen.** A line's date is the
latest it says, read as the kernel reads one (its `newest`; `11/03/2026`,
either way round, is never guessed). A line that says none takes the
nearest date written above it in its own file, else the date its file is
named for, and the answer says which (`date from line 1`,
`date from file name`). The first mention is the earliest dated one, a tie
going to the first file and line in sorted order.

**What no date reaches is counted, never placed.** An undated mention could
be earlier than the answer, and the answer says so, with the count. When no
mention is dated at all, the first by file and line is shown, marked
undated: your files don't say when.

On willow's demo folders: Odile's files first mention "piano tuning" on
2020-11-03 (from a memo's file name), Hollis's "appraisal" on 2021-02-11, by
a line that itself recalls the first appraisal's date, and Teodora's
"physio" on 2024-05-14, a bank statement's card payment, with one undated
mention that could be earlier.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's: 0 a first mention found; 42 your files never mention it, or the
words are only common ones; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `forms`, `held_by`,
`FUNCTION`, `read_words` and `config`.

**Never:** changes your files; writes anything, even the record; places an
undated mention.
