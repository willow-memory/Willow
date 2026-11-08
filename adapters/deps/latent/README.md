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
        [--changed-from INDEX] [--top N] "your question"

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
rebuilt for every question, so a big index costs minutes and gigabytes each
time. latent refuses (exit 2), before allocating anything, an index whose
matrix would pass **512 MiB**, saying how many passages and terms it holds
and the memory it would need. On a 4-core, 15 GiB machine, over a scan index
of willow's own repo, one question took:

| passages | terms | matrix | time | peak memory |
|---:|---:|---:|---:|---:|
| 2,000 | 5,546 | 0.08 GiB | 4 s | 0.6 GiB |
| 4,000 | 6,661 | 0.20 GiB | 17 s | 1.4 GiB |
| 6,000 | 7,778 | 0.35 GiB | 42 s | 2.5 GiB |
| 8,000 | 8,745 | 0.52 GiB | 86 s | 3.8 GiB |

Peak memory runs about seven times the matrix, and time grows with the
square of the passages. Past the bound it only got worse: on scan indexes
repo-pile built over public repositories, 21,897 passages ran one question
past 22 minutes at 9.7 GB without printing, and 60,031 (47,257 terms, a
21.1 GiB matrix) failed to allocate. To ask a big index, rank only what
changed with `--changed-from`, which the bound counts after, or index less.

**Needs:** numpy, pinned in `requirements.txt` and floored in
`requirements-floor.txt`; tested at both.

**Uses:** scan's `Index` and `passages`, and the kernel's `words` and `echo`.

**Exit codes:** 0 something ranked; 42 nothing shared a sense, or the index
held too little; 2 refused (a bad command line, not an index, numpy
missing, or a matrix past 512 MiB — never a quiet skip).

**Never:** writes anything, reads a folder, reads the key, or goes online.
