# Five repos compared by a stack, no agent, 2026-11-03

Fresh box over the five repos, then `compare.md`: 35 steps in 7 pools, all
kernel search. `similar` asked Willow's own add-on list what is near each
repo's idea; `fair-merge` and `claim-check` asked the five the same
questions in turn; `duplicates` found literal shared text; `scan` indexed
each repo once, asked the four non-Willow repos all 192 of Willow's unbuilt
ideas, and asked Willow 21 needs the other four state. Run time 1 min 53 s.
Nothing was written into any repo; the record verifies.

| file | what |
|---|---|
| `compare.md` | the stack |
| `five-stack.out` | the page, 6,850 lines |
| `ideas.txt`, `needs.txt` | the two question lists scan was given |
| `ideas-answers.jsonl`, `needs-answers.jsonl` | scan's answers, one JSON line per question per index |

## 1. What they share

**Literal text.** Of 1,002 passages said in two or more files, 39 cross a
repo boundary, and every one is the Apache-2.0 licence: Willow and
redential-cli carry the full text, glapagos the short header. socratic-fork
is MIT and shares no line with anyone. NaturalConv has no LICENSE file at
all, so by Willow's own repo-pile rule (keep only repos under a licence an
Apache-2.0 project can use) it is the one of the five Willow could not take
code from.

**One idea, four repos.** The strongest shared thing is an append-only,
hash-chained log. fair-merge served it from each in turn:
- Willow: `CONSTITUTION.md:104`, the Ledger, and the kernel's record (built).
- redential-cli: `docs/rfc-13-anchor-schema-draft.md:162`, a receipt chain
  linked by `prev_receipt_hash` (schema and fixtures only, no code in src).
- glapagos: `docs/architecture/ARCHITECTURE.md:159`, "append-only log with
  cryptographic chaining" (prose only, no hashing code in src).
- socratic-fork: `grades/enterprise.md:23`, an append-only audit trail as a
  grade row (a question, by design).

**The same promise in two products.** "Source code never leaves the
machine" is held in all its words only by redential-cli, in five places.
Willow says it in other words: `test_kernel.py:358`, the test that the
kernel has no network module. claim-check shows that gap exactly: Willow's
passages lack "source", redential-cli's CHANGELOG lacks it too.

**Also shared, by passage:** deterministic bytes across runs (Willow's ci
rows; redential-cli `src/scan.ts:165`, "byte-identical output across runs");
a test gate on merging (redential-cli's privacy tests, glapagos CHARTER 5.2,
Willow's CI); a written constitution (Willow's "the law the code is written
to enforce", glapagos's institutional one). NaturalConv found nothing on
every question. glapagos found nothing on seven of ten.

## 2. What they can solve for each other

**Willow for redential-cli.** RFC 13's vault is a hash-chained receipt file
with a head hash, a verify, and a negative fixture for a backdated segment.
Willow's kernel is that, built and tested: `record.jsonl`, `verify`, plus
`tip-pin` (the record's end kept where the record can't reach, which is
the backdated-segment case), `merkle` (prove one row with a handful of
hashes) and the `opentimestamps` idea (anchor the newest hash). scan served
the Ledger and the opentimestamps idea for "append-only record anchored by a
hash"; it served nothing for the words "vault receipt backdated", which is a
vocabulary gap, not an absence.

**redential-cli for Willow.** `redential` is already an idea on Willow's
list: "the bundle redential-cli's scan makes, written to the record before
you submit it, so what left your machine can be checked later." scan served
it from `test/submit.test.ts:209` and `docs/scan.md:172`. The bundle is a
JSON file, the record takes rows, and the privacy tests already define what
may be in it. That is the shortest add-on of the lot. redential-cli's
`signatures/*.json` (imports and config files per library) are also the
only versioned signature database among the five; Willow has nothing like
it, and `similar` confirmed nothing on the list is close.

**Willow for glapagos.** DATA-GOVERNANCE.md requires a manifest, provenance,
an open licence and SHA-256 checksums for every dataset. The manifest
schema `data/schemas/dataset-manifest-v1.json` has `license` and
`provenance` and no checksum field. Willow's `ro-crate` add-on writes
"every file with its SHA-256, size, kind and licence" as a zip any archive
reads, which is the missing piece. The chained audit log in ARCHITECTURE.md
is the kernel's record again.

**socratic-fork for Willow.** `socratic` is on Willow's list too: "asks you
questions about your own notes instead of answering, each citing the
passage it asked from." socratic-fork's 697 questions in 15 domains are a
question bank Willow has no equivalent of (scan of Willow for "question
bank by domain" and "decision cards" came back empty). The grade chain
`mvp → production → enterprise` is the one thing scan kept serving for
Willow's `second-opinion` and `synonyms` ideas, which says more about
shared words than shared purpose.

**Willow for NaturalConv.** The whole repo is one script that downloads
documents from a list of URLs. Willow's `snapshot` fetches a page once into
a folder with its address, time and SHA-256, and `wayback` compares it with
the archive's copy. That turns the download into a cited, re-checkable
source, which is what a dataset's grounding documents want.

## 3. Which unbuilt Willow ideas the other repos already hold a piece of

192 ideas asked of four indexes: 19 found a passage somewhere.

| hits | repo |
|---|---|
| 24 | redential-cli |
| 14 | socratic-fork |
| 2 | glapagos |
| 0 | NaturalConv |

The ones where the match is the idea, not just its words:
- **redential** ← redential-cli itself (above).
- **socratic** ← socratic-fork itself (above).
- **signed-commits** ("which commits are signed, and by whose key") ←
  redential-cli `docs/faq.md:3` and `schema/bundle.v1.json`, its
  attribution and ownership logic.
- **by-function** ("code read by function and class, so a hit names the
  function it's in") ← redential-cli's proof graph, `src/proof-graph/infer.ts`.
  `similar` placed this next to the built `codebase-memory` and the `sigmap`
  idea, the one neighbour it found for any of the ten sentences.
- **repro** ("a release built twice, byte for byte the same") ←
  redential-cli `test/proof-graph/anchors.test.ts:386`, its determinism tests.
- **git-notes** and **pr-context** ← redential-cli `src/git.ts`, which
  already handles unborn HEADs and per-path commit attribution.
- **gitlab** ← redential-cli's host-kind detection, `signatures/infra/`.

The rest (`food-log`, `memoir`, `speak`, `safe-app`, `teams`, `signal`) are
word matches and nothing more.

## 4. Did the stack give almost everything?

Yes for where words meet, and that is most of it: the shared log, the
shared promise, the two repos already on Willow's list, the schema missing
its checksums, the two designs with no code behind them. All of it is
cited to file and line and any of it can be rerun.

What it could not do is translate. Eleven of the 21 needs came back empty
because each repo names the same thing differently: redential says vault
and receipt where Willow says record and row, NaturalConv says download
where Willow says snapshot. The kernel serves a passage only when it holds
half the question's words, on purpose, so a different vocabulary reads as
absence. `similar near` has the same limit: eight of ten sentences found
"nothing on the list is close" even though two of the repos are on the
list by name, because the sentences were longer than the lines.

The fix is Willow's own and needs no agent: a words list for the box
(`kernel.py init --words FILE`, the thing nicknames and abbreviations
write), mapping each repo's words to the others' (vault = record, receipt =
row, download = snapshot, bundle = export). Rebuilt with that list, the
same stack would answer the eleven empties. That is the next rebuild.
