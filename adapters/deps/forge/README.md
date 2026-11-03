<!-- willow-addon
section: Assistants
line: A sentence in, the add-ons it names or means out, as a plan with its forks for the Forge's checkpoint to resolve and the person to seal before anything runs.
source: new
added: 2026-11-03
needs: forge-play; Apache-2.0
floor: forge-play 0.10.0; the rule names 0.1.0, its first release, but the card box this reads the cards with arrived in 0.10.0
writes: record
network: none
-->
# forge

What you want done, in your own words, matched to the add-ons here by
[the Forge](https://github.com/forge-play/Forge), the engine that refuses a
confident wrong answer; what you settle, on your record, under your key.

    python adapters/deps/forge/suggest.py suggest --box DIR "read my email and tell me when the boiler is due"

    cards   325 built, 192 ideas, read beside this script
    fork    “email” could be:
              apple-mail       Apple Mail's .emlx messages, read as mail reads an .eml. (writes to; network none)
              mail             Email in .eml and mbox, as text. (writes to; network none)
    fork    “due” could be:
              coming-up        Dates written in your files in the next N days. (writes nothing; network none)
              renewals         What renews when, from your files. (writes nothing; network none)
    2 forks wait on you

    python adapters/deps/forge/suggest.py propose --box DIR "read my email and tell me when the boiler is due" \
        --choose email=mail --choose due=coming-up --why "email=the flat's mail is mbox"

    proposed  proposal:3f1c…  forge/decisions/willow-email.json  mail
    proposed  proposal:a90d…  forge/decisions/willow-due.json  coming-up
    proposed  proposal:77be…  forge/stack.md  mail, coming-up
    3 waiting on your seal: python kernel.py seal --box DIR proposal:...

The Forge's card box reads every card beside this script, built or still an
idea, as a row for its keyword scan: a card's name, and the lines of
`ui/search-words.txt` that point at it, are what a sentence can hit. Four
things come out of `suggest`:

- **a step**: an add-on the sentence reaches and nothing else does, as one
  line for a [stack](../../stdlib/stack/) file;
- **a fork**: one word that reaches several add-ons, with the cards as the
  options and their lines and promises as the tradeoffs. That is a decision
  for the Forge's checkpoint to put to you once and remember;
- **sealed**: a fork you settled before, read from your record through the
  kernel, which serves it only while its seal proves under your key and the
  proposal still hashes to what you sealed. It is a step now, and you are
  not asked twice. One whose card no longer does that word here is said to
  be stale, and asked again;
- **an idea**: an add-on you named that isn't built yet.

A stack you sealed for these very words comes first, as the kernel serves
any sealed answer, and nothing is asked.

`propose` settles the open forks with `--choose WORD=NAME` and your reason
with `--why WORD=...`, and hands the result to the kernel's door: one
proposal per settled fork, under the words `forge decision willow-WORD`, and
one for the stack, under your sentence. Each carries the card's name, line,
path and SHA-256, so what you seal is what you were shown. Nothing is an
answer until you seal it with your key, and nothing runs. The Forge reads a
sealed decision back the same way, by asking the kernel for those words
(`forge.willow_record`), so one record serves both.

`suggest --json` prints the whole: the cards counted, the steps, the forks,
what is sealed, the ideas, and `plan`, a document the Forge's `plan_shape`
validates and its `decision_extract` turns into decisions. A fork carries no
recommendation and no confidence: nothing is guessed, and no made-up 0.5 is
scored. When a real sentence misses, add a line to `ui/search-words.txt`;
when one maps wrong, argue the line.

Exit codes, the kernel's: 0 steps found and nothing waits on you, or a
sealed stack for these words; 42 a fork waits on you, nothing was named, or
your seal is waited on; 2 refused (a bad command line, a folder that isn't a
box or whose record doesn't verify, a fork left unsettled or settled with an
option not on offer, a stack sealed for these words already, forge-play
missing or older than 0.10).

**Needs:** forge-play 0.10 or newer, which needs Python 3.11 or newer.

**Uses:** the kernel's `bite` and `propose`, so every question and every
suggestion is a row; its `sealed` and `standing`, so a seal is believed only
on the kernel's word; its exit codes.

**Never:** seals, reads the key (the kernel reads it, to check a proof),
writes anything but through the kernel, ranks, or asks a model. `suggest`
writes nothing at all. The forks are yours to settle, and the seal is yours.
