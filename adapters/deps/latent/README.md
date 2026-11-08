<!-- willow-addon
section: Finding things
line: Finds code by meaning, not just matching words, using scan's index: a question reaches code that says the same thing another way.
source: new
added: 2026-10-24
needs: numpy; BSD-3-Clause
floor: numpy 2.1.0; the 2020 rule names 1.19, which has no wheel for Python 3.13 (the version the deps CI job runs), and 2.1.0 is the first that does
writes: nothing
network: none
role: tools
uses: scan
-->
# latent

Rank a [scan](../../stdlib/scan/) index's passages by meaning instead of by
words.

    python adapters/deps/latent/latent.py rank --index INDEX \
        [--changed-from INDEX] [--only FILE] [--top N] \
        ("your question" | --questions FILE)

The kernel, and scan's BM25, match words: ask "memory exhausted" and they
miss code that says "out of memory". This ranks by latent semantic analysis
— TF-IDF over the index's passages, then a truncated SVD — so terms that
keep the same company (a synonym pair, a word and its abbreviation) sit
close, and a question reaches a passage that shares its sense without sharing
its words. It downloads no model; the meaning comes from the passages
themselves.

It reads an index scan built, never a folder. `--changed-from INDEX` ranks
only the passages that index lacks, as scan's own does, so a release can be
asked about only what its fix changed. Each answer is a JSON line like
scan's, each passage with its rank, file and line.

**Many questions, one build.** `--questions FILE` asks every question in
FILE, in scan's format (one a line, or `name<TAB>question`; `#` starts a
comment), and builds the space once for them all. A line each, with its
`question` name. Ten questions cost one build, not ten.

**After a word search.** `--only FILE` ranks only the passages FILE names,
so another add-on picks a few hundred and latent orders them by meaning.
It reads:

- scan's JSON lines (`scan.py scan --rank bm25 --top 300 ...`), or latent's
  own, taking every served passage's id;
- [ripgrep](../ripgrep/)'s and [code-shape](../code-shape/)'s `path:line
  id  text` lines, whose 12-character ids it matches to the index's whole
  ones;
- one id a line.

It skips any other line, such as a summary. A FILE that names no passage of
the index is refused, since it was likely made from another folder. If only
some of its ids are missing, it says how many and ranks the rest. The
trade: ranked only among what the words found, a passage that shares none
of the question's words is reached only if the word search picked it, so
ask the search for its synonyms too (several `--questions`, or ripgrep
more than once into one FILE). With `--questions`, every question ranks
within the same FILE.

**Not the kernel's answer.** Ranked by meaning, it serves passages a `bite`
would not, so nothing it prints can be cited into an approval; it is a way to
find where to look, read then against the files. On willow's PHP2Shell demo
it put the fix's code in the top three more often than BM25 did
(demo/php2shell): 84% against 80% over the four releases, and 94% against 88%
on the two CVEs disclosed after any model was trained.

**How:** builds the TF-IDF matrix of the passages, L2-normalises each row,
keeps up to 200 SVD dimensions (fewer when there are fewer passages or
terms), and ranks by cosine to the question in that reduced space. The same
index and question give the same order every run.

**How big:** the matrix is dense, passages × terms × 8 bytes, and it is
built for every run (once for all of `--questions`), so a big index costs
minutes and gigabytes each time. latent refuses (exit 2), before allocating anything, an index whose
matrix would pass **512 MiB**, saying how many passages and terms it holds
and the memory it would need. On a 4-core, 15 GiB machine, over a scan index
of willow's own repo, the build took (each question after it took well under a second):

| passages | terms | matrix | time | peak memory |
|---:|---:|---:|---:|---:|
| 2,000 | 5,546 | 0.08 GiB | 4 s | 0.6 GiB |
| 4,000 | 6,661 | 0.20 GiB | 17 s | 1.4 GiB |
| 6,000 | 7,778 | 0.35 GiB | 42 s | 2.5 GiB |
| 8,000 | 8,745 | 0.52 GiB | 86 s | 3.8 GiB |
| 12,000 | 9,918 | 0.89 GiB | 224 s | 6.0 GiB (now refused) |

Peak memory runs about seven times the matrix, and time grows with the
square of the passages. Before the bound, on the same size of machine and
scan indexes repo-pile built over public repositories' code, 21,897 passages
took 34 minutes and 9.7 GB for one question, and 60,031 (47,257 terms, a
21.1 GiB matrix) stopped on numpy's allocation error. To ask a big index, rank only what
changed with `--changed-from`, or only what a word search found with
`--only`; the bound counts what both leave. Or index less.

**Needs:** numpy, pinned in `requirements.txt` and floored in
`requirements-floor.txt`; tested at both.

**Uses:** scan's `Index` and `passages`, and the kernel's `words` and `echo`.

**Exit codes:** 0 something ranked; 42 nothing shared a sense, or the index
held too little; 2 refused (a bad command line, not an index, numpy
missing, an `--only` FILE that names no passage of the index, or a matrix
past 512 MiB — never a quiet skip). With `--questions`, 0 when any
question ranked something.

**Never:** writes anything, reads a folder, reads the key, or goes online.
