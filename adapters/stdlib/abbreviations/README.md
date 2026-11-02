<!-- willow-addon
section: Your own words
line: Your own shorthand, written down once (appt, Rx, w/c), so a question finds either form.
source: new
added: 2026-10-27
writes: to
network: none
-->
# abbreviations

To the kernel a word is its letters, so "appt" isn't "appointment". This
reads a question's shorthand as your files write it, either way round, and
writes the words-list lines that make it last.

    python adapters/stdlib/abbreviations/abbreviations.py --box DIR "when is the appointment"
    read appointment as appt: 2 passages hold it
    ask:  when is the appt

    python adapters/stdlib/abbreviations/abbreviations.py lines --box DIR --to FILE
    wrote 4 words-list lines to FILE

**How a word is read.** A word of your question that no file holds is
looked up in a small table of common shorthand (appt, tmrw, mtg, rx, thurs,
the months, the street words), both ways round: "appointment" finds the
files' "appt", and "appt" finds their "appointment". It's read as the form
the most passages hold, a tie going to the first in sorted order, and the
question as read is printed, for you to ask: it never asks for you. A word
your files hold, or your words list already reads, is left alone.

**`lines` is the lasting fix.** One
[words-list](../../../docs/how-it-works.md) line for each shorthand of the
table your files write only one way, the word you'd type on the left,
written to FILE for you to read before you keep them. Add the lines you
agree with to your words list, and the kernel reads each one that way every
time, by itself. On willow's demo folders Teodora's files say only "appt",
so she gets `appointment = appt`; Bernadette writes hers out, so she gets
`appt = appointment`; Odile's `dr` is offered as doctor and as drive, which
is exactly why the lines are read before they're kept.

**The table is this file's, not yours to teach here**: a shorthand of your
own goes straight in your words list. Shorthand the kernel splits at a
slash (w/c, b/c) is out of its reach, and so out of this one's, said here
so the silence isn't a pass. It suggests, never decides.

Spelling slips are [typos](../typos/)'s, and accents
[accents](../accents/)'s, so no two of the three read the same word.

FILE is written once, readable only by you, never inside your folder or the
box, and never over a file that's already there. Exit codes, the kernel's,
as accents uses them: 0 every word is held, or a reading is offered
(`lines`: written); 42 a word nothing covers, or no shorthand in your files
to write; 2 refused.

**Uses:** the kernel's `chunks`, `words`, `toks`, `holds`, `held_by`,
`FUNCTION`, `read_words` and `config`.

**Never:** changes your files; writes anywhere but FILE; asks the question
for you; reads a word your files or words list already hold.
