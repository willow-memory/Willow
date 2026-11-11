<!-- willow-addon
section: Trust and proof
line: A sentence said about your boxes, checked by code: each cite served, each box cited, no word or number the boxes lack, your words exact.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: none
role: suggests
output: report
from: code, https://github.com/willow-memory/willows-grove, Apache-2.0
-->
# say-check

A sentence said about your boxes, checked by code: each cite served, each box cited, no word or number the boxes lack, your words exact.

    python adapters/stdlib/say-check/say_check.py --sentence "TEXT" --boxes FILE [--you "your line"] [--earlier FILE] [--json]

    say-check: populated, struck: 1 of 4 checks failed
      every cite was served      held
      every box cited            held
      nothing the boxes lack     failed: 140 is no box's
      your words quoted exactly  nothing quoted

A model may say what code found, in one sentence you would rather read. It
may not add to it. This holds a sentence to the boxes it was said about. A
sentence that fails any check is struck, and whatever asked shows code's
own line in its place. The model is a writer, never an authority.

A box is one thing code found: a row of a report, a passage, a count. Each
has a tag, and the sentence cites the box a fact came from: `[b4]`.

## The four checks

| Check | It holds when |
|---|---|
| every cite was served | each tag the sentence cites is a box it was given |
| every box cited | each box it was given is cited |
| nothing the boxes lack | every number is a box's number, and every word is a box's word, a glue word, or a function word |
| your words quoted exactly | anything in double quotes is in your own line, word for word |

- **Glue words** are the few free ones a sentence may add: morning, oh,
  and, also, still, both, heads up, no rush, looks like, anytime, got it.
  They carry no fact.
- **Function words** are a, the, is, of, to and their like.
- **Any form of a box's word is the box's word,** by its ending: waiting
  for waits, tests for tested. A different word for the same thing is not:
  with a box that says "126 tests pass", "succeed" fails.
- **Accents are folded,** so cafe reads as café. A word in a script the
  boxes don't hold fails.
- **Your quoted words are yours,** so they aren't held to the boxes. A
  number inside a quote still is: a quote is no way to get a figure past
  them.
- **A sentence with no word in it,** only tags and numbers, is not one.

Each check that fails says what failed: the number, the words, the tag,
the quote.

## The boxes

`--boxes FILE` is JSON, one of two shapes:

- a list of boxes, each `{"id": "b1", "text": "its words"}`;
- [a report](../ci/README.md#the-report-contract), as any report add-on
  prints with `--json`. Its rows become boxes b1, b2, ... in order, each
  its `where` and its `what`.

`--you "your line"` is what you asked, for the quote check. `--earlier
FILE` is boxes shown earlier in the same sitting, in the same shapes. A
sentence may cite one of those, and need not; an earlier box's words count
only when the sentence cites it, so an earlier fact can't be said without
its tag.

The example beside this, `example-boxes.json`, is the two boxes above:

    python adapters/stdlib/say-check/say_check.py --boxes adapters/stdlib/say-check/example-boxes.json \
        --sentence "You need to ratify the work order [b5]. PR 712's still waiting, 140 tests pass [b4]."

## What it can't catch

It checks words and numbers, not what the sentence means. "Nothing is
served, so no one sealed it" passes when every word is in the boxes, even
if the boxes say it the other way round. It keeps a model from adding
facts. It does not make a sentence true.

It reads the files it is given and writes nothing. It asks no model and
reaches no network. It prints a report; `--json` gives the same as one
JSON object.

Exit codes, the kernel's: 0 every check held; 42 the sentence is struck;
2 refused.

The checks are [willows-grove](https://github.com/willow-memory/willows-grove)'s,
from the part of it that says boxes aloud. Left behind there: its checks of
code references against a code graph, and of quotes against the one
script's record, which willow doesn't have.
