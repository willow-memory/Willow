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
