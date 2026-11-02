<!-- willow-addon
section: Trust and proof
line: A thesis's claims, each tied to the source that backs it, and a list of the ones with none.
source: new
added: 2026-11-01
writes: nothing
network: none
uses: claim-check
-->
# thesis

A document's claims, each put to your sources, and the ones no passage holds.

    python adapters/stdlib/thesis/thesis.py --box DIR FILE [--top N]

    line 3    held   garden.md:1   Tomatoes want six hours of sun.
    line 5    short  garden.md:5 lacks cold   Basil likes shade and cold.
    3 claims; 1 held, 2 short; 1 skipped
    without a passage holding every part:
      line 5    no file has: cold
      line 12   every part is somewhere, none in one place

Every sentence of FILE is a claim, placed at the line it starts on. Each goes
to [claim-check](../claim-check/), which asks your folder for the passages
holding all of its parts. A claim with one is `held`, and the first such
passage is named (`(+2)` when more hold it). A claim with none is `short`,
with the nearest passage (`--top`, 1) and what it lacks; the list at the end
is all the short ones, naming the parts no file has. claim-check is the
one-claim view; this is the whole document.

- **Sentences**: split at `.`, `!` or `?` and a space, except after a short
  list of abbreviations (`Co.`, `Dr.`, `etc.`); a bullet or numbered item
  starts a new one. Headings, fenced code and indented blocks are not claims.
  It reads prose: a bulleted line of commands is still put to the sources.
- **Lacks** names at most eight missing parts, then how many more.
- **Skipped**: a sentence with fewer than two parts (its words less the
  common ones) is only counted; one part cannot be checked part by part.

**Held is where to read, not a verdict.** A passage holding every part may
deny the claim ("we never scan email for ads"), and one holding some may back
it in other words. The firm finding is `no file has`: nothing in your folder
names that part. The word "backs" in the idea is not what this can say; it
says where to look, and the person reads and decides.

**Exit codes:** 0 every claim has a passage holding all its parts; 42 some
has none; 2 refused (no box, not a text file, over the kernel's file size,
a words list that doesn't read).

**Uses:** claim-check's `parts` and `check`, and the kernel's `chunks`,
`config`, `read_words` and `MAX_FILE`.

**Never:** writes anything, or reads the key.
