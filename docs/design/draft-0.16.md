# Design note: Draft 0.16, four of willow's own promises made law

**Status: proposal, drafted 2026-11-06. Nothing here is in the law, and
nothing is built.** The operator chose the four clauses and one amendment
for all of them; the clause text below is a draft for the operator to
correct before it goes into the constitution. Entering it is the merge, and
the verdicts in `constitution/declarations.json` are the operator's to write.

## The idea, in one line

Four promises the README makes in its own name, with no clause behind them,
become clauses of the constitution, and each is held by a new beat of
`kernel.py test`: the eight beats become twelve.

## Where this started, and what checking it changed

A hand-off brief from an outside session, written with only part of the
repo to read, asked for five clauses and thirteen beats, and offered five
candidates from the README's guarantees table. Read against the repo, two
of the five were already law and the brief's process needed three
corrections:

| Candidate | What the repo shows | Outcome |
|---|---|---|
| Never serves an approval for a question you didn't seal it for | held under §0.4 already, by the tests on a seal's question in `test_kernel.py` | not a new clause: it would restate §0.4 |
| Never goes online; no `eval`, `exec`, `compile`, `__import__` | `test_it_never_dials_out` already cites III.1 and III.5 | already law; the README's row says *none* and should name them |
| Never stores your words | a promise of willow's own | **VI.8** below |
| Same answer under every hash seed | a promise of willow's own | **IV.10** below |
| Never imports an add-on | a promise of willow's own | **III.6** below, worded without naming code |

A fourth clause was added from the kernel's own tests rather than the
table: a person's no, proved like a seal and final (`decline`), which the
cycle exercises but none of the eight beats does. **V.10** below.

The README's *every add-on's tests can fail* row also says *none*, and is
IV.9 (a check that cannot fail is no check), in force since Draft 0.13. It
is not new either.

The corrections to the brief's process:

- **One amendment, one draft.** `constitution/amend.py` takes several
  clauses in one amendment's `clauses:` header, so the four enter as one
  amendment, the seventh in `constitution/amendments/`, and make Draft 0.16. Five amendments would have made
  0.16 to 0.20.
- **Twelve beats, not thirteen.** Four clauses, four beats; no candidate
  was padded in to make five.
- **The verdicts are the operator's.** Each new clause needs a verdict in
  `constitution/declarations.json`, kept by hand.

## The four clauses, drafted

Each is new text in its article; Article 0 and every existing clause are
untouched, and nothing is renumbered. Each strengthens Article 0 the only
way VIII.3 allows, by citing it.

### VI.8, the record keeps acts, not words

> **VI.8 — The record keeps acts, not words.** What a person asked, and
> what they were answered, is kept in the record by its hash and its place,
> never by its text. The record says that a question was asked, when, what
> it was served and what was done about it; the words stay in the person's
> files and the person's head. Raw, in VI.6, is every event unsmoothed, not
> every word kept: the hash is the event's raw form.

VI.6 says the record keeps every event raw. VI.8 has to say why a hash
does not break that: the event is the act of asking, not the words asked.
The operator should check that this reading of VI.6 is the one they mean.

*Beat 9.* After the whole cycle, the record's bytes hold none of the
questions' content words, and none of the proposals' data.

### IV.10, the same question, the same answer

> **IV.10 — The same question, the same answer.** Over the same files, the
> same question is answered by the same passages, in the same order, on
> every run and every machine. An order that rests on anything the files
> and the question do not hold — the hour, the process, the platform's
> chance — is no order, and a ranking that varies is refused as one.

*Beat 10.* The same bite, run in two processes under two different hash
seeds, serves the same passages in the same order, byte for byte.

### III.6, the core reaches nothing that extends it

> **III.6 — The core reaches nothing that extends it.** What extends the
> system uses its core; the core never loads, calls on or waits for an
> extension, and depends on nothing beyond the platform it runs on. With
> every extension removed it does the same work, the same way. A core that
> leans on an extension has widened its reach by the extension's (§0.3).

*Beat 11.* The kernel reads its own source and finds no import outside
the standard library and none of `adapters`. `test_strip.py` already holds
the other half: the kernel alone, with `adapters/` deleted, passes.

One risk to settle when it is built: the obvious test of "outside the
standard library" is `sys.stdlib_module_names`, which Python 3.9 doesn't
have, and the vectors record the beats passing on 3.9.0. The beat needs a
test that runs there too.

### V.10, a no is final

> **V.10 — A no is final.** A person's refusal is made with their key, as
> an approval is, and recorded. What they refused is not offered to them
> again, and is never approved over the refusal; a changed proposal is a
> new proposal and needs its own act. A refusal that does not prove under
> the person's key counts for nothing (§0.4), and what no one refused or
> approved is still the person's (§0.6).

*Beat 12.* In the cycle, the person declines one proposal: `out` stops
listing it, `seal` refuses it, and a decline whose proof is forged leaves
it waiting.

## What changes when it is built

| File | Change |
|---|---|
| `CONSTITUTION.md` | the four clauses, in Articles III, IV, V and VI; `amend.py write` fills in the draft number, the history row and the lineage step |
| the seventh file in `constitution/amendments/` | the same four texts under the amendment header: draft 0.16, the four clauses, a one-line summary |
| `constitution/declarations.json` | a verdict for each: **the operator's** |
| `kernel.py` | four beats in `test()`, each citing its clause at its line; "the twelve beats held" |
| `test_kernel.py` | the beat-count test renamed; tests that already hold these promises cite the new clauses |
| `constitution/test_eternity.py` | unchanged; it must still pass |
| `README.md` | the guarantees table names the new clauses (and III.1, III.5, IV.9 where it says *none* today); "the twelve beats held" |
| `DECISIONS.md`, `docs/tour.md`, `docs/agents/searching.md` | the beat count |
| `vectors/README.md` | **unchanged**: its row records a Python 3.9 run that checked eight beats, and stays true unless that run is made again |
| `LIMITS.md` | only if a clause narrows what willow does; none of the four is expected to |
| `changes/` | the fragment |

A new beat adds a check, not a behaviour, so `vectors/compare.py` and the
five ports should be unmoved; that is checked, not assumed.

## The checks it has to pass

- `python constitution/amend.py check`: Preamble and Article 0 unchanged
  to the byte, the amendment's text in the law word for word.
- `test_docs.py`: every clause the amendment adds cited by code and
  attacked by a test (VIII.4), and the docs' beat count matching.
- `python kernel.py test`: the twelve beats held; then `tests:kernel`,
  `tests:vectors`, `ports`, `test_strip.py` and the constitution's tests.
- The coverage report (`python constitution/coverage.py`) cites each of the
  four.
- Each new beat shown to fail on a planted break before it counts (IV.9):
  a question's words written into the record, a rank that follows the hash
  seed, an add-on import, a declined proposal offered again.

## What landed on main before it, checked

On 2026-11-06, nineteen pull requests merged on main, #251 to #272. Read
for what this amendment rests on:

- **None touches the law or the kernel.** No change to `CONSTITUTION.md`,
  `constitution/`, `kernel.py`, `test_kernel.py`, `DECISIONS.md`,
  `LIMITS.md`, the vectors or the ports. The only Trace ID added anywhere
  is VI.7's, in #271. The clauses above, their places in the articles and
  the eight beats they build on are as they were.
- **How the pull request is opened changed.** #263: the changelog entry is
  a fragment, `changes/+BRANCH.KIND.md`, renamed for the number by
  `adapters/stdlib/github/create_pr.py`; #271: CHANGELOG.md refuses a new entry. #264: the open
  pull requests are read before starting. This branch already keeps all
  three.
- **The open pull requests don't meet it.** Of the seven open, two touch
  `README.md`, both only the add-on count on one line; none touches the
  guarantees table, the beat count or the law.
- **The suggestions contract (#265)** gives every model proposer one claim
  form. It is an add-on contract, held by
  `adapters/stdlib/ci/test_contract.py`; it doesn't
  change what a seal or a decline is, so V.10 stands on the kernel as it is.

## The order of work

1. This note: the clauses, for the operator to correct.
2. The amendment: the four clauses in the law and in the seventh amendment
   file, `amend.py write`, and the verdicts from the operator.
3. The four beats in `kernel.py`, each shown to fail on its planted break.
4. The docs, the README's table and the beat count.
5. The full run, then the pull request; the merge is the operator's.
