# Want finders: which way in finds the card

A person says what they want in their own words. Willow has three ways to
turn that sentence into an add-on card, and this study asks each of them the
same wants, whose right card was written down first.

| finder | what it is | where |
|---|---|---|
| `suggest` | the Forge's keyword scan over card names and the lines of `ui/search-words.txt` | [the forge add-on](../../adapters/deps/forge/) |
| `similar` | the kernel's own search over each card's one line | [similar](../../adapters/stdlib/similar/)'s `near` |
| `canvas` | BM25 over each whole card; a card you named first, then one a word of yours usually means | `Canvas.search` in [ui/canvas.py](../../ui/canvas.py) |

The forge add-on is where [stacks, for agents](../../docs/agents/stacks.md)
says a chain of add-ons starts, so how often it finds the card is how often
that chain starts in the right place.

## What is frozen

[FROZEN.json](FROZEN.json) holds the SHA-256 of the two files below, and
[test_want_finders.py](test_want_finders.py) holds them to it. A change to
either is a new freeze, in a commit of its own, with its reason.

- [wants.json](wants.json): ten wants, each with the card or cards that answer
  it here and where the want came from. One (W10) has no card here, and is
  there to see which finder can say so.
- [score.py](score.py): the three finders, each taken at its word, and the
  hit rule. A finder's offer is the first five names it gives, in its order.
  A want hits at k when a right card is in the first k offered; a want with
  no right card hits when nothing is offered.

The rules, per finder: **R1** hits at 1 and **R5** hits at 5, over the nine
wants with a card; **R0** the want with none, offered nothing. Each is a
`verdict` row on a box outside the repository, with the SHA-256 of
`wants.json` and of the files the finder ran:

    python kernel.py init --box BOX --pile PILE --key KEY
    python demo/want-finders/score.py run --box BOX
    python kernel.py verify --box BOX

`suggest` needs forge-play 0.10 or newer; without it, its rows say
`unreachable` and count no hit.

## What came before the freeze

Said plainly, since a study's numbers are only as good as what was known
when its questions were written:

- **The wants were asked before they were frozen.** On 2026-11-16 an agent
  session (Claude, at the operator's desk, working on the Forge) wrote these
  ten sentences from the Forge's open problems and put them to `suggest` and
  `similar` by hand, then to the canvas's search. That is why this study
  exists: `suggest` found the right card for none of them. The sentences in
  `wants.json` are the ones asked, word for word. The right cards were
  written down by the same session as it read those first answers.
- **The right cards are a proposal.** They are an agent's reading of the
  cards, not the person's. Any of them is theirs to change, as a new freeze.
- **The same ten were asked of willow at 2026-11-04 (`2fbdd3c0`) and just
  before the renames of 2026-11-14 (`0e0f7ebe`).** `suggest` found none of
  them at either. The renames didn't cause the misses.

## What the dry run could see

`score.py run --dry` asks nonsense in place of every want, with its rows
named `want-finders:dry:...`. It ran once before the freeze, on a scratch
box: every finder offered nothing for every want, so each scored R1 0/9, R5
0/9 and R0 1/1, nine verdict rows went on the box, and `kernel.py verify`
held. That shows the wiring, the rows and the hashes. It could not show a
real offer being read, since nonsense is offered nothing:
`test_a_suggest_report_is_read_as_its_offers` holds that on suggest's own
report shape instead.

## Results

### 2026-11-16, the first scored run

On the freeze (`f8f0c9f7`), with forge-play 0.10.0, one run on a fresh box
outside the repository; what it printed is
[results/2026-11-16.txt](results/2026-11-16.txt). `kernel.py verify` on
that box: "the chain holds: 10 rows, 0 sealed"; its last row is
`want-finders:R0:canvas`, hash `c8825bd5…cc1241`.

| finder | R1, hit at 1 | R5, hit at 5 | R0, nothing offered for W10 |
|---|---|---|---|
| suggest | 0 of 9 | 0 of 9 | no: offered `people` |
| similar | 6 of 9 | 6 of 9 | yes |
| canvas | 5 of 9 | 8 of 9 | no: offered five |

What failed, by finder:

- **suggest found none.** For seven wants it offered nothing; for three it
  offered a card that doesn't answer: W07 `digest`, `handover` and
  `repo-digest` (from the line `stands = handover, digest`), W09 `against`
  (the word "against"), W10 `people` (the word "people"). It reaches a card
  only by its name or an alias line, and the wants name neither.
- **similar missed W01, W05 and W07**, offering nothing for each. It reads
  only a card's one line, and those lines don't share half of the want's
  words. Its offers are short (three at most) and, when made, right first.
- **canvas missed only W07**, but put a card that shares one part of its name
  with a word of the want ahead of the right one: `noised-count` for
  "count" (W02, right at 2), `risky-code` for "code" (W04, at 4),
  `slow-tests` and `fast-tests` for "tests" (W06, at 3). It offers five for
  any sentence, so it can't say nothing (W10).
- **No finder found `stale-answers` for W07.**

Written after reading the results, not a frozen rule: similar's and canvas's
hits at 1 fall on different wants, and between them one or the other has
the right card first for eight of the nine.

### 2026-11-16, suggest with the close fork

The same freeze, after two changes: the canvas's search moved into similar
as `Want` (this study printed the first run's results byte for byte on that
code), and the forge add-on's `suggest` asks it when a sentence names no
card and no alias line reaches one, offering its first three built cards
as the `close` fork, the first recommended, with `none` beside them. One
run on the same box as the first; what it printed is
[results/2026-11-16-close.txt](results/2026-11-16-close.txt). `kernel.py
verify`: "the chain holds: 19 rows, 0 sealed"; the last row is
`want-finders:R0:canvas`, hash `94f83c6b…bbca2f41`.

| finder | R1, hit at 1 | R5, hit at 5 | R0, nothing offered for W10 |
|---|---|---|---|
| suggest | 4 of 9 (was 0) | 6 of 9 (was 0) | no: offered `people` |
| similar | 6 of 9 | 6 of 9 | yes |
| canvas | 5 of 9 | 8 of 9 | no: offered five |

What changed, and what didn't:

- **Four wants now find their card first through suggest**: W01
  (`forecast-ask`), W03 (`decisions`), W05 (`tip-pin`, which similar
  misses) and W08 (`stack-bridges`). W02 has it at 2 and W06 at 3, behind
  cards that share one part of their name with a word of the want, as on
  the canvas.
- **W09 is still `against`, and W07 still `digest`, `handover` and
  `repo-digest`.** The scan found a card by a word ("against"; the alias
  line `stands = handover, digest`), so the search was never asked: a
  wrong name or alias hit keeps the close fork from forming.
- **W04 misses by one place.** `mutants` is the search's fourth; the fork
  takes three built cards.
- **`none` is offered with every close fork**, and score.py reads it as a
  name; it is never a right card, so it moves no score.

### 2026-11-16, a step the search doesn't place near is asked about

The same freeze, after one more change to `suggest`: a card the scan
reached alone, by name or alias line, is a step only while similar's search
has it in its first twelve for the sentence; one it puts nowhere near joins
the close fork instead, after the search's own cards, its row saying it was
named but isn't close. One run on the same box; what it printed is
[results/2026-11-16-doubt.txt](results/2026-11-16-doubt.txt). `kernel.py
verify`: "the chain holds: 28 rows, 0 sealed"; the last row is
`want-finders:R0:canvas`, hash `5ffe298d…0465aa5a2`.

| finder | R1, hit at 1 | R5, hit at 5 | R0 |
|---|---|---|---|
| suggest | 5 of 9 (was 4) | 7 of 9 (was 6) | no: offered `people` |
| similar | 6 of 9 | 6 of 9 | yes |
| canvas | 5 of 9 | 8 of 9 | no |

- **W09 moved, and only W09.** "against" is an ordinary word to the search
  (similar's `HOW` list), so the card `against` is nowhere in its first
  twelve; the fork is now `model-exam`, `forge`, `translate`, `against`,
  `none`, and `model-exam` is first.
- **W07 is unchanged, and was always going to be.** Its scan hit is a fork
  (`stands`), not a step, and a fork is already asked; and the search
  doesn't find `stale-answers` either. The fix the repository's own rule
  names is an alias line, written when a real sentence misses; W07 is this
  study's sentence, and a line written to pass it would only be the study
  grading itself.
- **W10 is unchanged.** "people" is a card's whole name, and the search
  agrees: it is named.
- **It costs a second only when there is a step to check.** On this
  machine, a sentence with only forks took 0.30 s, as before; one with a
  named step 1.15 s, against 0.33 s before: building the search once.
