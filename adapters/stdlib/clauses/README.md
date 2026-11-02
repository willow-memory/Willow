<!-- willow-addon
section: Reading more kinds of files
line: A policy, contract or set of terms as one sentence a passage, so an answer lands on the clause, and what changed between two versions, sentence by sentence.
source: new
added: 2026-10-24
writes: to
network: none
tags: policies
-->
# clauses

A long document as one sentence a passage, and what changed between two
versions of it.

    python adapters/stdlib/clauses/clauses.py mirror --from FOLDER --to MIRROR
    python adapters/stdlib/clauses/clauses.py diff --old FILE --new FILE [--to FOLDER]
    python kernel.py init --box BOX --pile MIRROR --key KEY

The kernel reads a paragraph at a time, and one paragraph of a privacy
policy can hold ten promises. Asked "do they use my email for ads?", the
answer should be the one sentence that says so, not the paragraph around it.

**mirror** writes each .txt, .md, .html or .htm under FOLDER to
`MIRROR/<same path>.txt`, one sentence a paragraph:

- a web page is read as its blocks: paragraphs, headings, list items;
- the [pdf](../../deps/pdf/) add-on's mirror (lines wrapped at the page's
  width, under `== page N`) is read as wrapped lines. A short line, a
  heading or a paragraph's last, ends its block unless the next line goes on
  in lower case; a sentence cut by a page break is joined back, and the
  `== page N` heading is kept after it, so an answer still says the page;
- a sentence ends at `.`, `!` or `?` (a closing quote or bracket may
  follow) before a capital, a digit or an opening quote, but never after a
  short abbreviation (e.g., Inc., U.S.) or a single initial.

**diff** splits two versions the same way and lists what changed:

    reworded  old.txt:199 -> new.txt:203   (16 of 28 words kept)
      - We don’t show you personalized ads based on your content from Drive, Gmail, or Photos.
      + We don’t show you personalized ads based on your content from Drive, Gmail, or Google Photos, unless ...
    added     new.txt:189   For example, Search may process some of the data ...
    same      532 sentences (0 differ only in spacing or punctuation)

Two sentences are the same when they hold the same words in the same order,
split the kernel's way, case aside. A removed and an added sentence are
paired as *reworded* when they share at least half their words, the closest
pair first. Each place is the line its block starts on. `--to FOLDER` also
writes the new version's added and reworded sentences, as one file named
like the new one, so the kernel can be asked about only what changed.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER; the mirror and the
folder can't be inside each other; the same folder gives the same bytes; a
file that isn't UTF-8 text is skipped and counted.

**Can't:** read a PDF itself (the pdf add-on does, first). Where the PDF's
own text puts a label on the same line as a sentence (a glossary term, a
"Learn more" link), the two come out as one passage, and a diff may show
that as a rewording. Sentences are cut by punctuation, not grammar, so a
list run together without full stops is one passage.

**What it was built for:** Google's privacy policy of 16 October 2026, in
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/):
the two versions' PDFs, 36 pages each, became 557 and 564 passages. The
diff found 532 sentences the same and listed 16 entries: the effective date,
the ads paragraph's five (three reworded, two added), "Photos" become
"Google Photos", and the new "personalize content" entry's four lines.
The other five were the PDF's labels joined to a sentence, as said under
**Can't**.

**Exit codes:** mirror, 0 wrote at least one file, 42 nothing to read;
diff, 0 the same, 42 something changed; 2 refused.

**Uses:** the kernel's `words`, `SNIFF`, and `html_text`, the way it reads
a web page, so a line it names is the kernel's line.

**Never:** writes inside your folder or beside the versions it compares,
changes an original, or goes online.
