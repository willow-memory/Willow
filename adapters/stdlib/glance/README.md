<!-- willow-addon
section: Finding things
line: What a scan found, a line a question: where its best passage is, how it opens, and which of the question's words it lacks.
source: new
added: 2026-11-10
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
uses: scan
-->
# glance

What a scan found, a line a question: where its best passage is, how it opens, and which of the question's words it lacks.

    python adapters/stdlib/glance/glance.py --of SCANNED --questions FILE [--words FILE] [--json]

    glance: populated, 3 questions: 1 held whole, 1 in part, 1 found nothing
    ## found nothing
      3     where is the moon rocket
    ## held in part
      shed  1 of 2, lacks colour: shed.md:1  The shed is blue.
    ## held whole
      sun   garden/veg.md:1  Tomatoes want six hours of sun.

[scan](../scan/) asks a folder a list of questions in one go, and what it
prints is for a program: a line of JSON for each question, with every
passage whole. This is the same answers for a person. Each question is one
line: its name, where its best passage is, and how that passage opens. So a
wrong answer is seen at a glance, without opening a file.

SCANNED is a file holding the lines scan printed. FILE is the questions file
scan was given: one question a line, or `name<TAB>question`, with blank lines
and `#` lines skipped. A question with no name is named by its line number,
as scan names it. `--words` is the words list scan was given, if it was given
one.

**Three groups**, each printed only when it has a row:

- **found nothing:** no passage was served. The row is the question's name
  and the question.
- **held in part:** the best passage holds some of the question's words but
  not all. The row says how many, and which are missing: `1 of 2, lacks
  colour`. Then the place and the opening.
- **held whole:** the best passage holds every word. The row is the place
  and the opening.

The place is the file's last two path parts and the line. The opening is the
passage's first words, on one line, cut at about 90 characters with an
ellipsis. Only the best passage of each question is looked at, the first one
scan served.

**Why "held in part" matters.** A passage is served when it holds half of a
question's words. So a short question, of two words, is served by a passage
that holds just one of them. That is where a wrong answer comes from: the
shed question above was answered by a line about the shed that says nothing
of its colour. This group puts those first, the thinnest at the top: the
passages holding the smallest share of their question.

The words that count are the kernel's: common words (how, do, the) don't
count, a word asked twice counts once, a word in another form (owes, owing)
is held, and the words of the passage's path count as well as its text, as
they do when the kernel searches. With `--words`, a word your list reads
another way is not said to be lacking: with a list that reads colour as
blue, the shed question is held whole.

**It can't tell you an answer is wrong.** A passage can hold every word of a
question and still not answer it, and one that lacks a word may be just
right. It shows which answers to look at first, and the looking is yours.

**In a stack.** A step of a [stack](../stack/) can take what an earlier
step printed: `{01}` is the file the first step's output was kept in. So
scan is one step and this is the next, with the run kept in a folder:

    ## Asking
    - scan -- scan --index INDEX --questions FILE
    - glance -- --of {01} --questions FILE

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a first line counting the questions, then a group at a
time, each row a question's name and what was found. `--json` gives the same
report as one JSON object.

**Refused:** a command line it can't read; a file that can't be read; a
SCANNED that is empty, or holds a line that isn't one of scan's (the message
names the line); a words list that doesn't parse.

**Exit codes:** 0 every question was served, in part or whole; 42 a question
found nothing, and waits on you; 2 refused.

**Uses:** the kernel's `words`, `FUNCTION`, `toks`, `held_by` and
`parse_words`.

**Never:** writes anything. It reads the two or three files you name, and
doesn't open the files the passages came from.
