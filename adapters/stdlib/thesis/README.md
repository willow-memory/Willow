<!-- willow-addon
section: Trust and proof
line: A thesis's claims, each tied to the source that backs it, and a list of the ones with none.
source: new
added: 2026-11-01
version: 0.1.0
writes: nothing
network: none
role: tools
uses: claim-check
output: report
-->
# thesis

A document's claims, each put to your sources, and the ones no passage holds.

    python adapters/stdlib/thesis/thesis.py --box DIR FILE [--top N] [--json]

    thesis: populated, 3 claims; 1 held, 2 short; 1 skipped
    ## short
      thesis.md:5   Basil likes shade and cold.  nearest: garden.md:5 lacks cold  no file has: cold
      thesis.md:12  Slugs eat lettuce.  nearest: no part held  every part is somewhere, none in one place
    ## held
      garden.md:1   line 3  Tomatoes want six hours of sun.

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares; `--json` gives the same report as one JSON object. The
short claims come first, each at its own line in FILE, with the nearest
passages and what no file has; the held ones follow, each at the passage
that holds it, with the claim's line in FILE.

Every sentence of FILE is a claim, placed at the line it starts on. Each goes
to [claim-check](../claim-check/), which asks your folder for the passages
holding all of its parts. A claim with one is `held`, and the first such
passage is named (`(+2)` when more hold it). A claim with none is `short`,
with the nearest passage (`--top`, 1) and what it lacks, naming the parts no
file has. claim-check is the
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

**Exit codes:** 0 `empty` (no claim to check) or `populated` with every claim
holding a passage; 42 `populated` with some claim short, which waits for you;
2 refused (no box, not a text file, over the kernel's file size,
a words list that doesn't read).

**Uses:** claim-check's `parts` and `check`, and the kernel's `chunks`,
`config`, `read_words` and `MAX_FILE`.

**Never:** writes anything, or reads the key.
