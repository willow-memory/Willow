<!-- willow-addon
section: Finding things
line: When the answer is 'not enough to say', which words found nothing, and what kind of file would have answered.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# why-not

Why a question got "not enough to say".

A bite that finds nothing says only that, and the person is left guessing:
is the thing not in the files, or is it there under another name? This asks
the same question of the same folder, the kernel's own way, and says why.

    python adapters/stdlib/why-not/why_not.py --box DIR "when does the frost come in autumn"

    when does the frost come in autumn
      frost   held by 1 passage: diary.txt:3
      come    no passage holds it
      autumn  no passage holds it
    A passage has to hold 2 of the 3 words at once.
    The nearest it came:
      diary.txt:3  holds 1 (frost); lacks come, autumn
    What would have answered it: a dated note, an event or a deadline, with the date on the line.

| It says | How |
|---|---|
| each word that counts, and how many passages hold it | the kernel leaves "when", "does", "the" and their kind out; a word holds where it, or its plain form, is a word of the passage or of its path |
| the share a passage needs | the kernel's: half of the words, rounded up |
| the nearest passages | the three holding the most words, which they held and which they lacked |
| a close spelling | for a word nothing holds, a word in your files 80% alike, with the words-list line that would teach it: radiater = radiator |
| the kind of file that would have answered | from the question's opening: when, how much or how many, who, where, why, how, what |

If your files do hold the question it says so, and where, and stops. The
box's own words list is read as the bite reads it, and a list that doesn't
read is refused.

It asks without asking: nothing is written, so the record does not hold one
more question. It cannot say what the files *should* hold, only what they do
not, and the kind of file is a hint from the question's first word, not a
reading of its meaning.

Exit codes, the kernel's: 0 your files do hold it; 42 they don't, and this
says why; 2 refused.

**Uses:** the kernel's `chunks`, `rank`, `toks` and `held_by`.

**Never:** writes anything, not even a record row.
