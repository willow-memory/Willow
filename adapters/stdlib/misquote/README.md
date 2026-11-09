<!-- willow-addon
section: Finding things
line: A quote that is almost in your files: the closest passage, and the words it adds, drops or changes, so a misquote shows as one.
source: new
added: 2026-10-24
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
-->
# misquote

A quote that is almost in your files: the closest passage, and how the
quote differs from it.

    python adapters/stdlib/misquote/misquote.py --box DIR "the quote" [--json]

    misquote: populated, closest passage holds 34 of 34 words, in order
    ## dropped
      policy.txt:203  Google: your files have it here; the quote doesn't

It prints [a report](../ci/README.md#the-report-contract): a line saying
how close the closest passage is, then a group per kind of difference, each
row where the passage is and what differs. `--json` gives the same report as
one JSON object.

[quote-check](../quote-check/) says whether a quote is in your files. When it
isn't, the useful question is whether it nearly is: a word dropped, a word
changed, two sentences run together. misquote finds the passage holding the
most of the quote's words in the quote's order, and lists what differs:

- **dropped**: your file has it there, and the quote leaves it out;
- **added**: the quote has it, and your file doesn't;
- **changed**: the quote's words, then the ones your file has in their place.

`as written` (a row, with the line `the quote is in your files as written`) means the quote's words are there in order: quote-check's
"verbatim" or "same words". A passage is the closest only when it holds at
least half the quote's words in order; if none does, it says nothing is
close, rather than offering a weak match. Words are split the kernel's way,
case aside, and each is shown as the file spells it. A tie goes to the
passage where the words sit closer together.

**What it was built for:** in
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/),
quote-check said shattered.io's block quote of Google's privacy policy was
in neither version. misquote says what happened: every one of its 34 words
is in the new clause, in order, and the clause also says "Google" before
"Photos", which the quote dropped.

**Exit codes and states:** `populated`, 0: the quote is in your files as
written; `populated`, 42: it isn't, and the closest passage differs, which
waits on you; `empty`, 0: nothing is close, so there is nothing to compare;
2 refused. 42 never means "found nothing".

**Uses:** the kernel's `chunks`, `config` and `WORD`, and Python's
`difflib`.

**Never:** writes anything.
