<!-- willow-addon
section: Finding things
line: When the answer is 'not enough to say', which words found nothing, and what kind of file would have answered.
source: new
added: 2026-10-29
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
-->
# why-not

Why a question got "not enough to say".

A bite that finds nothing says only that, and the person is left guessing:
is the thing not in the files, or is it there under another name? This asks
the same question of the same folder, the kernel's own way, and says why.

    python adapters/stdlib/why-not/why_not.py --box DIR "when does the frost come in autumn" [--json]
    python adapters/stdlib/why-not/why_not.py --box DIR --questions FILE [--of SCANNED] [--json]

    why-not: populated, "when does the frost come in autumn": a passage has to hold 2 of the 3 words at once
    ## words
      frost         held by 1 passage: diary.txt:3
      come          no passage holds it
      autumn        no passage holds it
    ## the nearest it came
      diary.txt:3   holds 1 (frost); lacks come, autumn
    ## what would have answered it
      kind of file  a dated note, an event or a deadline, with the date on the line

**A whole list of questions.** `--questions FILE` takes a file of them, one
a line, or a name, a tab, then the question, the way [scan](../scan/) takes
them. Each question that finds nothing is explained under a heading of its
own, its name and the question; one your files do hold is left out:

    why-not: populated, 2 of 3 questions found nothing; each says why
    ## frost: when does the frost come in autumn
                   a passage has to hold 2 of the 3 words at once
      frost        held by 1 passage: diary.txt:3
      autumn       no passage holds it
      diary.txt:3  holds 1 (frost); lacks come, autumn

`--of SCANNED` hands it what scan already found: the lines scan printed for
that same file. Then only the questions scan said were empty are explained,
and none is asked twice. In a [stack](../stack/) that is an earlier step's
output, named by its number, `--of {01}`. Lines that aren't scan's are
refused, saying which line; so is a file with nothing in it.

It prints [a report](../ci/README.md#the-report-contract): a line saying the
question and the share a passage needs, then the words, the nearest
passages and the kind of file as rows. `--json` gives the same report as one
JSON object.

| It says | How |
|---|---|
| each word that counts, and how many passages hold it | the kernel leaves "when", "does", "the" and their kind out; a word holds where it, or its plain form, is a word of the passage or of its path |
| the share a passage needs | the kernel's: half of the words, rounded up |
| the nearest passages | the three holding the most words, which they held and which they lacked |
| a close spelling | for a word nothing holds, a word in your files 80% alike, with the words-list line that would teach it: radiater = radiator |
| the kind of file that would have answered | from the question's opening: when, how much or how many, who, where, why, how, what |

If your files do hold the question it says so, and where, in the first line
(an `empty` report: nothing to explain), and stops. The
box's own words list is read as the bite reads it, and a list that doesn't
read is refused.

It asks without asking: nothing is written, so the record does not hold one
more question. It cannot say what the files *should* hold, only what they do
not, and the kind of file is a hint from the question's first word, not a
reading of its meaning.

Exit codes and states: `empty` (0) your files do hold it, so there is nothing
to explain; `populated` (42) they don't, and the rows say why, which waits on
you; `unreachable` (42) every word is a common one, so it couldn't look; 2
refused. 42 never means "found nothing".

**Uses:** the kernel's `chunks`, `rank`, `toks` and `held_by`.

**Never:** writes anything, not even a record row.
