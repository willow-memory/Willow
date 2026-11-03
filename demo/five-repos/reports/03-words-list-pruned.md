# The pruned words list, four runs side by side, 2026-11-03

The list went from 89 lines to 22, then 24: the first cut took `head` and
`segment` with the broad lines, and the rebuild showed the vault-chain
need regress to a `head(` function in digest.py. Those two were specific
bridges, so they went back and the stack ran once more. Each run was a
fresh box over the five repos and the same 35-step stack. The final list
is `five-words.txt`; the broad one is kept as `five-words-broad.txt` and
the over-cut one as `five-words-pruned1.txt`.

## The 21 needs asked of Willow

| | no list | broad, 89 | pruned, 22 | pruned, 24 |
|---|---|---|---|---|
| answered | 10 | 19 | 12 | 12 |
| answered with the thing itself | 10 | 12 | 11 | 12 |
| answered with noise | 0 | 7 | 1 | 0 |
| empty | 11 | 2 | 9 | 9 |

The two the final list bridges, with what Willow serves:
- **redential-cli's vault chain** (verify, head hash, backdated segment):
  tip-pin's test of a bite dropped and the chain rehashed, which verify
  passes and the pin fails; tip-pin's card; the seal row's `bite_key`.
- **NaturalConv's download from a list of urls**: wayback's `captures`,
  snapshot's holds-or-CHANGED check, and almanac's archived copies with
  their fingerprints.

The nine that stay empty stay empty for the right reason. Willow has no
question bank, no decision cards, no grades, no dashboard with a language
toggle, no consent mechanism, no signature database, no token file with
its mode, and no dialogue dataset. The broad list answered seven of them
with unrelated passages. The pruned one says "not enough to say".

## The 192 ideas asked of the other four repos

| | no list | broad | pruned 22 | pruned 24 |
|---|---|---|---|---|
| ideas with a passage elsewhere | 19 | 36 | 22 | 22 |

The three the pruned list adds (`family-box`, `report`, `time-capsule`)
are word matches in redential-cli's FAQ and scan options, not the ideas.
The real nineteen from the first run are unchanged, and the seventeen the
broad list invented are gone.

## The seven claims

| claim | no list | broad | pruned 24 |
|---|---|---|---|
| source code never leaves the machine | all parts, redential-cli ×5 | ×6 | ×5 |
| secret scan of the payload before output or upload | some parts | all parts ×3 | all parts ×2 |
| every dataset has a manifest, provenance, licence and checksums | some parts | all parts, falsely | some parts, lacks dataset |
| the other four | some parts | some parts | some parts |

The one real gain holds: `upload = submit, send, seal, serve` lets
redential-cli's CHANGELOG and CLAUDE.md hold the whole secret-scan claim.
The false closure is gone: the `.gitattributes` line at CHANGELOG.md:1904
now lacks "dataset", as it should.

## What the 24 lines say

The list that holds is the one that names the same object in two
vocabularies and nothing else: vault, receipt, bundle, chain, hash,
checksum, manifest, provenance, slug, taxonomy, seal, approved, submit,
upload, download, anchor, head, segment, backdated. Every line cut was one
that named a kind of thing (dataset, document, question, record, key)
rather than a thing, and each of those made a whole class of passages
answer a question they don't.

## Files

| file | what |
|---|---|
| `five-words.txt` | the 24-line list the box now carries |
| `five-words-broad.txt`, `five-words-pruned1.txt` | the 89-line and 22-line lists |
| `five-stack.out` | this run's page; the four runs are `runs-20261103T011746Z.out` (no list), `…012538Z` (broad), `…013102Z` (22), `…013348Z` (24) |
| `needs-answers*.jsonl`, `ideas-answers*.jsonl` | scan's answers per run: `-before` (no list), `-broad`, `-pruned1`, and the current |
