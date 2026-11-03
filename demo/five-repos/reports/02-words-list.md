# The words list, and the stack rebuilt with it, 2026-11-03

`five-words.txt`: 89 question words, each read as the other repos' words
(`vault = record, box, ledger, chain, store, receipts`), both directions,
in the kernel's own format, readable only by its owner, kept outside the
box. The box was made fresh with it on `init`, so fair-merge and
claim-check read it from the box, and the two scan steps were given it
with `--words`. Same stack as before, so the two pages compare line for
line. Run time 2 min 9 s; flagged steps fell from 6 to 4.

## What the list fixed

| asked of Willow | before | after | what came back |
|---|---|---|---|
| redential: vault chain, verify, backdated segment | empty | populated | tip-pin's test of a bite dropped and the chain rehashed, and the seal row's `bite_key`. The exact need. |
| naturalconv: download documents from urls | empty | populated | wayback's `captures(url, ...)`. The right add-on. |
| glapagos: decision log within 72 hours | empty | populated | CONSTITUTION V.4b and its decision-class table. Near. |
| glapagos: dashboard with a language toggle | empty | populated | browse's card. Near. |
| claim: secret scan of the payload before output or upload | some parts | all parts, 3 places | `upload = submit` bridged it; redential-cli holds the whole claim. Real. |

Two of the nine newly answered needs are the thing itself, two are near,
and one claim now closes. Two needs stayed empty (socratic's grades,
glapagos's consent): no mapping reaches them because Willow has nothing
there, which is the honest answer.

## What the list cost

Four of the nine new answers are noise the list let in: `0600 = owner,
readable` served pile-serve's socket mode; `signature = import, pattern`
served risky-code and dialect; `question = bite, bank = list` served a
symptoms card; `dataset = files, corpus` served three reader cards.

The ideas asked of the other four went from 19 found to 36, and 15 of the
17 new ones are word matches only (`cycle`, `kids`, `kiosk`, `movie`,
`time-capsule`). `record = log, history` and `key = token, secret` are the
lines that did it: they make most of redential-cli answer most of Willow's
trust ideas.

One claim closed falsely. "Every dataset has a manifest, provenance,
licence and checksums" now reports all parts at `Willow/CHANGELOG.md:1904`,
a line about `.gitattributes` and line endings, because five broad
mappings each found a word there. The kernel still demanded half the
words; the list made more words count. That is the rule working as
written, and the reason a words list is the person's to prune.

## The next rebuild

Keep the specific bridges and cut the broad ones. Cut: `dataset`,
`document`, `documents`, `question`, `questions`, `bank`, `0600`,
`permissions`, `signature`, `signatures`, `record`, `key`, `words`,
`folder`, `pile`, `agent`. Keep: `vault`, `receipt`, `backdated`,
`anchor`, `head`, `bundle`, `submit`, `upload`, `download`, `url`,
`checksum`, `checksums`, `manifest`, `provenance`, `seal`, `sealed`,
`approved`, `hash`, `chain`, `slug`, `taxonomy`, `vocabulary`. Rebuilt
with that list, the two real answers and the closed claim should hold,
the false claim should reopen, and the ideas count should fall back toward
the 19 that were real.

## Files

| file | what |
|---|---|
| `five-words.txt` | the list |
| `compare.md` | the stack, scan steps now taking `--words` |
| `five-stack.out` | this run's page; the previous run is `runs-20261103T011746Z.out` |
| `needs-answers.jsonl`, `needs-answers-before.jsonl` | scan's answers with and without the list |
| `ideas-answers.jsonl`, `ideas-answers-before.jsonl` | the same for the 192 ideas |
