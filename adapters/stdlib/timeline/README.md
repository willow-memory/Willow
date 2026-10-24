<!-- willow-addon
section: Trust and proof
line: A dated timeline of one matter (a dispute, an illness, a tenancy), every line cited, to hand to a lawyer, doctor or council.
source: new
added: 2026-10-24
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# timeline

One matter from your folder, a dispute, an illness, a tenancy, as a dated
list of the lines about it, each with the file and line it came from. Made to
hand to someone who needs the story in order: a lawyer, a doctor, a council.

    python adapters/stdlib/timeline/timeline.py --box DIR --to FILE "mould landlord"

    2026-03-01  tenancy/log.md:3         2026-03-01 Reported the mould in the back bedroom.
    2026-03-01  tenancy/log.md:4         The landlord said someone would come.  (date from line 3)
    2026-03-09  letters/2026-03-10.md:1  2026-03-09 Wrote to the landlord about the mould.  (filed 2026-03-10)
    2026-04-02  tenancy/2026-04-02.md:1  Still no visit from the landlord; mould spreading.  (date from file name)
    undated     tenancy/misc.md:1        The landlord's number is in the blue book. Mould spray under the sink.

You choose the matter with words, the way you ask a question. Every passage
of your folder that holds them, by the kernel's own rule (half or more of
your words, in the passage or its folder's name, with your words list if
you have one), gives all of its lines, oldest first.

- **Every line is cited.** Each one has its file and line number, so whoever
  reads it can go and check.
- **Nothing is merged or reworded.** Lines are as you wrote them. A note
  that appears in two files is listed twice, at both places.
- **It never guesses a date.** A line is dated by the date it says. A date
  that reads either way round, like 11/03/2026, is not read at all. A line
  that starts with a date was written then; one that names several dates
  anywhere else is placed at the latest. Either way, it says so. A line
  that says no date takes the nearest date written above it in its file,
  and says which line; one with neither takes its file's name, and says so.
- **Two dates are two facts.** A line's own date and the date its file is
  named for can differ (a letter written up the next day). When they do,
  both are shown, and the line is placed by its own.
- **Undated lines stay.** They come after the dated ones, by file and line,
  marked "undated": your files don't say when, and the timeline says that.

The file starts with your words and how many lines are dated and undated. It
holds no clock time and no folder paths beyond your files' own names, so the
same folder gives the same bytes.

**Exit codes:** 0 written; 42 nothing holds the words, so nothing is
written; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `words`, `toks`, `held_by`,
`HOLD`, `FUNCTION`, `read_words` and `config`.

**Never:** changes your files; writes anywhere but FILE; writes FILE inside
your folder or the box, or over a file that's already there. FILE is
readable only by you.
