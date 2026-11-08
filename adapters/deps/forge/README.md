<!-- willow-addon
section: Assistants
line: A sentence in, the add-ons it means out: a plan with its forks, for the Forge's checkpoint to settle and the person to seal before it runs.
source: new
added: 2026-11-03
needs: forge-play; Apache-2.0
floor: forge-play 0.10.0; the rule names 0.1.0, its first release, but the card box this reads the cards with arrived in 0.10.0
writes: record, to
network: none
role: repo
output: report
uses: stack
looks-for: ci
runs-in: repo
-->
# forge

What you want done, in your own words, matched to the add-ons here by
[the Forge](https://github.com/forge-play/Forge), the engine that refuses a
confident wrong answer; what you settle, on your record, under your key.

    python adapters/deps/forge/suggest.py suggest --box DIR "read my email and tell me when the boiler is due" [--json | --plan]

    forge: populated, 2 forks wait on you
    ## fork “email”
      adapters/stdlib/apple-mail/README.md  apple-mail: Apple Mail's .emlx messages, read as mail reads an .eml. (writes to; network none)
      adapters/stdlib/mail/README.md        mail: Email in .eml and mbox, as text. (writes to; network none)
    ## fork “due”
      adapters/stdlib/coming-up/README.md   coming-up: Dates written in your files in the next N days. (writes nothing; network none)
      adapters/stdlib/renewals/README.md    renewals: What renews when, from your files. (writes nothing; network none)

    python adapters/deps/forge/suggest.py propose --box DIR "read my email and tell me when the boiler is due" \
        --choose email=mail --choose due=coming-up --why "email=the flat's mail is mbox"

    forge: populated, 3 waiting on your seal: python kernel.py seal --box DIR proposal:...
      forge/decisions/willow-email.json  proposal:3f1c…  mail for “email”
      forge/decisions/willow-due.json    proposal:a90d…  coming-up for “due”
      forge/stack.md                     proposal:77be…  a stack: mail, coming-up

The Forge's card box reads every card beside this script, built or still an
idea, as a row for its keyword scan: a card's name, and the lines of
`ui/search-words.txt` that point at it, are what a sentence can hit. The
report (the report contract, in the ci add-on's card) has a group per kind
of thing, each row the card and what it says:

- **steps**: an add-on the sentence reaches and nothing else does, one
  line for a [stack](../../stdlib/stack/) file, `NAME -- ARGS`, where ARGS
  is the add-on's own good command line as the [ci](../../stdlib/ci/)
  add-on's contract holds it (`{box}` for your record, your folder filled
  in, `{tmp}` for a folder `build` makes, the contract's pinned `--now`
  taken off); with the ci add-on absent, every step takes `--box {box}` and
  the plan says so; or a fork you settled
  before, read from your record through the kernel, which serves it only
  while its seal proves under your key and the proposal still hashes to
  what you sealed. It is a step now, and you are not asked twice;
- **fork “word”**: one word that reaches several add-ons, the cards as the
  options and their lines and promises as the tradeoffs. That is a decision
  for the Forge's checkpoint to put to you once and remember;
- **stale seals, asked again**: a seal whose card no longer does that word
  here (the alias file changed, say);
- **ideas**: an add-on you named that isn't built yet.

A stack you sealed for these very words comes first, as the kernel serves
any sealed answer, and nothing is asked.

`propose` settles the open forks with `--choose WORD=NAME` and your reason
with `--why WORD=...`, and hands the result to the kernel's door: one
proposal per settled fork, under the words `forge decision willow-WORD`, and
one for the stack, under your sentence. Each carries the card's name, line,
path and SHA-256, so what you seal is what you were shown. Its report is
one row per proposal: where it will be written, and what waits. Nothing is
an answer until you seal it with your key, and nothing runs. The Forge reads
a sealed decision back the same way, by asking the kernel for those words
(`forge.willow_record`), and its build loop proposes under the same words,
so one record serves both: a fork the Forge settled with you is a step here,
and a fork you settled here is the Forge's auto band. The first standing
seal for a decision is the one kept, as the kernel keeps it; a later one
waits its turn until the first no longer stands.

    python adapters/deps/forge/suggest.py build --box DIR "read my email and tell me when the boiler is due" --to ~/my-stack

    forge: populated, 2 of 2 steps built into ~/my-stack, page at ~/my-stack/page.md; 0 flagged, 0 left out
    ## built
      adapters/stdlib/mail/       mail: contract held; tests unreachable (no --python with pytest given); ran: clean
      adapters/stdlib/coming-up/  coming-up: contract held; tests unreachable (no --python with pytest given); ran: clean

To share a stack you sealed, with your reasons, see
[stack-share](../../stdlib/stack-share/).

`build` runs the stack you sealed for these words, and nothing else. It
reads the sealed stack from your record, never from a file you could edit;
puts each step's add-on into the folder named with `ui/assemble.py`, which
hashes every file onto the stack's own record and checks each contract;
writes the stack file beside it; and runs the [stack](../../stdlib/stack/)
add-on over your box, keeping the page at `<STACK>/page.md`. A step it can't
copy (one that works only in this repository) is said under `left out`,
never guessed at. A deps add-on goes in under `adapters/deps/`, with its
packages unchecked, since build names no Python: its step is flagged until
you add them. It refuses while no stack is sealed for these
words: the seal is the one gate between a suggestion and a run. The folder's
parent must exist; it makes no folder but the one you named.

`--json` prints the same report as one JSON object. `suggest --plan` prints
the whole as the Forge reads it: the cards counted, the steps, the forks,
what is sealed, the ideas, and `plan`, a document the Forge's `plan_shape`
validates, its `decision_extract` turns into decisions and its `build_loop`
resolves. A fork carries no recommendation and no confidence: nothing is
guessed, and no made-up 0.5 is scored. When a real sentence misses, add a
line to `ui/search-words.txt`; when one maps wrong, argue the line.

Exit codes, the report's: 0 steps found and nothing waits on you, a stack
sealed for these words, or nothing named (`empty`); 42 a fork waits on you
or your seal is waited on (`populated`), or forge-play missing or older than
0.10 (`unreachable`, said in the report); 2 refused (a bad command line, a
folder that isn't a box or whose record doesn't verify, a fork left
unsettled or settled with an option not on offer, a stack sealed for these
words already, a card beside this script that won't read).

**Needs:** forge-play 0.10 or newer, which needs Python 3.11 or newer.

**Uses:** the kernel's `bite` and `propose`, so every question and every
suggestion is a row; its `sealed` and `standing`, so a seal is believed only
on the kernel's word; its exit codes; `ui/assemble.py` and the stack add-on,
to build and run what you sealed.

**Never:** seals, reads the key (the kernel reads it, to check a proof),
writes anything but through the kernel or under the folder you name, runs a
stack you didn't seal, ranks, or asks a model. `suggest` writes nothing at
all. The forks are yours to settle, and the seal is yours.
