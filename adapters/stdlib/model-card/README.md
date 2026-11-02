<!-- willow-addon
section: Assistants
line: A card naming the model behind an assistant (version or weights hash, where it runs, licence, known limits), with the card's hash on the record so each suggestion can say which model made it.
source: new
added: 2026-11-02
writes: record
network: none
uses: weights-card
-->
# model-card

A card naming the model behind an assistant, with the card's SHA-256 on the
record, so a suggestion can say which model made it and the card can't
change unseen.

```
python adapters/stdlib/model-card/model_card.py add --box DIR --from gemma.md [--now TS]
python adapters/stdlib/model-card/model_card.py check --box DIR --from gemma.md
python adapters/stdlib/model-card/model_card.py list --box DIR

added  Gemma 3 4b It  card=5d1f…  weights=9c1e…, runs at http://127.0.0.1:8080/v1  (row 7)
```

A card is a markdown file with a `willow-model` header, the one
[weights-card](../weights-card/) writes from a weights file, with what you
add by hand:

```
<!-- willow-model
name: Gemma 3 4b It
sha256: 9c1e…
runs: http://127.0.0.1:8080/v1
licence: gemma
limits: makes up dates; English only
-->
```

It must name the model (`name`) and say which one: the weights file's
`sha256`, or, for a hosted model with no file to hash, its `model version`.
A value written `not in the header` counts as not there. Anything under the
header (what it's good at, what it gets wrong) is yours to write.

**`add`** appends the SHA-256 of the card's bytes through the kernel's own
append, with the name, the weights' hash or version, and where it runs:
never the card's text. The same card again is `already there`; a changed
card under the same name is a new row, replacing the last. **`check`**
holds a card file to its name's latest row: `same`, `changed` or `never
added`. **`list`** says each name's latest card.

**What it doesn't do yet:** no assistant names its card's hash in what it
proposes, so a suggestion can't yet say which card stood behind it;
[openai-compatible](../openai-compatible/)'s claim names the model and the
endpoint, and [sent-log](../sent-log/) reads that.

Exit codes, the kernel's: 0 added or already there, the card the same, or
cards listed; 42 a card changed or never added, or none on the record; 2
refused (a bad command line, not a box, a record that doesn't verify, a
card that doesn't name its model or say which).

**Uses:** the kernel's `read`, `append` and exit codes;
[weights-card](../weights-card/)'s `header`, the one reader of the card
format, and weights-card itself in its tests.

**Never:** writes the card's text onto the record, changes the card, seals,
goes online, or reads your key.
