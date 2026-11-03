<!-- willow-addon
section: Assistants
line: A sentence in, the add-ons it names or means out, as a plan with its forks for the Forge's checkpoint to resolve and the person to seal before anything runs.
source: new
added: 2026-11-03
needs: forge-play; Apache-2.0
floor: forge-play 0.10.0; the rule names 0.1.0, its first release, but the card box this reads the cards with arrived in 0.10.0
writes: nothing
network: none
output: report
-->
# forge

What you want done, in your own words, matched to the add-ons here by
[the Forge](https://github.com/forge-play/Forge), the engine that refuses a
confident wrong answer.

    python adapters/deps/forge/suggest.py --box DIR "read my email and tell me when the boiler is due" [--json | --plan]

    forge: populated, 2 forks wait on you
    ## fork “email”
      adapters/stdlib/apple-mail/README.md  apple-mail: Apple Mail's .emlx messages, read as mail reads an .eml. (writes to; network none)
      adapters/stdlib/mail/README.md        mail: Email in .eml and mbox, as text. (writes to; network none)
    ## fork “due”
      adapters/stdlib/coming-up/README.md   coming-up: Dates written in your files in the next N days. (writes nothing; network none)
      adapters/stdlib/renewals/README.md    renewals: What renews when, from your files. (writes nothing; network none)

The Forge's card box reads every card beside this script, built or still an
idea, as a row for its keyword scan: a card's name, and the lines of
`ui/search-words.txt` that point at it, are what a sentence can hit. The
report (the report contract, in the ci add-on's card) has a group per kind
of thing, each row the card and what it says:

- **steps**: an add-on the sentence reaches and nothing else does, one
  line for a [stack](../../stdlib/stack/) file;
- **fork “word”**: one word that reaches several add-ons, the cards as the
  options and their lines and promises as the tradeoffs. That is a decision
  for the Forge's checkpoint to put to you once and remember, so the next
  time you say "email" you are confirmed, not re-asked;
- **ideas**: an add-on you named that isn't built yet.

`--json` prints the same report as one JSON object. `--plan` prints the
whole as the Forge reads it: the cards counted, the steps, the forks, the
ideas, and `plan`, a document the Forge's `plan_shape` validates, its
`decision_extract` turns into decisions and its `build_loop` resolves. A
fork carries no recommendation and no confidence: nothing is guessed, and no
made-up 0.5 is scored. When a real sentence misses, add a line to
`ui/search-words.txt`; when one maps wrong, argue the line.

Exit codes, the report's: 0 steps found and nothing waits on you, or
nothing named (`empty`); 42 a fork waits on you (`populated`), or forge-play
missing or older than 0.10 (`unreachable`, said in the report); 2 refused (a
bad command line, a folder that isn't a box or whose record doesn't verify,
a card beside this script that won't read).

**Needs:** forge-play 0.10 or newer, which needs Python 3.11 or newer.

**Uses:** the kernel's exit codes, and `kernel.read` to see the box is one.

**Never:** writes the record or anything else, proposes, seals, reads the
key, ranks, or asks a model. The forks are yours to settle; proposing the
settled plan onto your record is the next add-on's job.
