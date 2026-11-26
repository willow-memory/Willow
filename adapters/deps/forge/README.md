<!-- willow-addon
section: Assistants
line: A sentence in, the add-ons it means out: a plan with its forks, for the Forge's checkpoint to settle and the person to seal before it runs.
source: new
added: 2026-11-03
version: 0.6.0
needs: forge-play; Apache-2.0
floor: forge-play 0.13.0; the rule names 0.1.0, its first release, but a fork left for later, several picks, blind forks and their confidence are the Forge's from 0.13.0 (willow_record, forks)
writes: record, to
network: none
role: repo
output: report
uses: stack, similar
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
      forge/stack.md                     proposal:77be…  a stack: mail, coming-up, todo, duplicates, contradictions, people

The Forge's card box reads every card beside this script, built or still an
idea, as a row for its keyword scan: a card's name, and the lines of
`ui/search-words.txt` that point at it, are what a sentence can hit. The
words list holds one word to a key, so what a word cannot say is a small
table at the top of `suggest.py`, applied to the scan's hits before the plan
(and so the same for every verb): "back" reaches backup only with "up" within
a word or two ("back up", "back it up"), so "the deposit is due back" does
not, and the hit then says the phrase it came from; "things to do", "still
have to do", "left to do", "to-do" and "to do list" name todo. Bare "to do"
does not, as it is in "what do I want to do with this folder". The
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
  options and their lines and promises as the tradeoffs, and `none` beside
  them, for when the alias line that offered them points wrong. That is a
  decision for the Forge's checkpoint to put to you once and remember, keyed
  by the word, so it holds for any sentence that says it;
- **stale seals, asked again**: a seal whose card no longer does that word
  here (the alias file changed, say);
- **ideas**: an add-on you named that isn't built yet;
- **fork “close”**: when your words name no card and no alias line reaches
  one, what [similar](../../stdlib/similar/)'s search (`Want`, the canvas's
  search) points at: up to three built cards, the first recommended (with
  a confidence once your seals have measured one; see `scores`), each
  row saying it is close and not named, and `none` beside them. A card your
  words reach alone, by name or alias line, is a step only while that
  search agrees it is near them (in its first twelve); one it puts nowhere
  near ("against" in "score a model against the answers", which reaches the
  pull request card `against`) joins this fork instead, its row saying it
  was named but isn't close. A fork's options are never doubted: they are
  already asked. Pointing is
  not answering, so it is a fork and never a step. Its decision is this
  sentence's own, so a seal for these words settles no other sentence;
  `--choose close=none`, sealed, keeps the miss on your record and runs
  nothing, and the next time the report says so. Its proposal keeps what
  you were shown: the cards in their order, the one recommended, where your
  pick fell, and the matcher that ranked them, known by what it ranks (the
  SHA-256 of the cards its search puts first for ten fixed sentences), so
  an edit that moves no card keeps its count and one that moves any starts
  a new one.

  **One close fork in five is blind**, by the hash of your words, so asking
  again gets the same: its cards in an order of their own, nothing
  recommended and no confidence said, the heading saying so, and each
  card's row its own line and promises and one note the same on every
  row, never the search's reason for it ("email usually means", "the words
  of its name are in yours"): those come in the search's order and would
  say which it put first. A
  recommendation you can see is one you can follow, and a pick that follows
  it says how far you trust the search, not how often it is right; a blind
  pick says only the second. Its proposal keeps the search's order, where
  your pick fell in it, the order you saw, the search's first (as
  `search_first`; its `recommended` is empty, since nothing was), and the
  confidence it kept unsaid. The Forge's plan gets no recommendation for it
  either, so its checkpoint has nothing to show.

      forge: populated, 1 fork waits on you
      ## fork “close”: nothing named that the search agrees with; these are close to what you said
        adapters/deps/noised-count/README.md        noised-count: ...; close, not named: a word of yours is part of its name; recommended, the search's first; no confidence yet: 0 of 5 blind close picks sealed on this matcher
        adapters/stdlib/assistant-scores/README.md  assistant-scores: ...; close, not named: uses often each, suggestion seal
        adapters/stdlib/forecast-ask/README.md      forecast-ask: ...; close, not named: uses count often
        none                                        none: none of these does it: sealed, the miss is on your record and nothing runs

A stack you sealed for these very words comes first, as the kernel serves
any sealed answer, and nothing is asked.

**More than one.** A fork isn't one or none: any card might be the one,
and more than one often is. `--choose WORD=A,B` (or `--choose WORD=A` given
again with B) takes several, as one decision and one proposal: the one the
search put highest is `chose`, the rest `also`, each with its card pinned,
and every one is a step of the stack, in the order you named them. `none`
and `not-now` stand alone. A close fork is scored on `chose`, so taking a
second card along with the search's first neither helps nor hurts its
score.

**What next.** `next --stacks FOLDER` says what could go in after what you
have: the steps of the stack you sealed for these words (or, before one is
sealed, what the words reach), held against every stack file under FOLDER,
your own. For each card you don't have it counts how often your stacks put
it beside a step you do. It looks beside the steps your words or picks
brought, not the defaults (a default your words named is one your words
brought, and is looked beside), and scores each card by how much more often it
sits beside those steps than in your stacks at large, so one that is in
nearly every stack, and so beside everything, is not offered:

      ## what your stacks put beside them, most often first
        adapters/stdlib/people/README.md  people: Everyone your files name ... ; with mail in 3 of 3

Counting and nothing else: no model and no search. It says what you have
done before, never what might be good, and a card no stack of yours puts
with any of your steps is not offered.

Counting can only offer what you have already done, so a second group, said
apart, gives the rest a first chance: built cards that are in none of your
stacks and that the catalogue's own search puts near your words or near a
step you have, each saying what it is near. A default your words did not name is not looked beside:
it suits any folder, so what is near it says nothing of what you are after.
Once you take one and seal it, it is in a stack of yours, and the counting
knows it. It writes nothing and asks nothing.

**Not now.** Every fork has a second way out, beside `none`:
`--choose WORD=not-now` leaves it undecided, and says so on your record.
Not deciding is a decision: it is a proposal of its own, with your reason,
under its own question ("forge not now willow-WORD"), sealed or declined
like any other. The fork's own question stays unanswered, so the fork stays
open, is offered again, and nothing is scored; the other steps and settled
forks still make a stack. Neither it nor a pick you haven't sealed goes
quiet: the report says each fork you said not now to, and each pick that
waits on your seal, and a stack sealed without its pick says which is left.

      ## picked, not sealed yet
        forge/decisions/willow-email.json  mail for “email”, proposed at row 4; it waits on your seal, and nothing is scored until then

**Defaults.** The add-ons named in `defaults.txt`, beside the script, go in
every stack it proposes, after the steps your words reached: todo, coming-up,
duplicates, contradictions and people, each there because it suits any
folder and not because of a word. They print as a group of their own:

      ## defaults: in every stack, not asked and not scored
        adapters/stdlib/todo/README.md  todo: TODO, FIXME and "need to" lines ... ; open items left in your own files, oldest first

- **Never an option of the `close` fork**, so picking one is never scored
  as the search being right.
- **One your words reached is that step**, and one a word's fork offers
  stays yours to pick; neither is a default too.
- **They ride with a stack and never make one.** With no step and no fork
  there is still nothing to run, and `none` alone still runs nothing.
- **The list is yours to edit:** a name, two spaces, why it is there. A line
  naming no built add-on is said and left out. `--defaults FILE` reads a
  list of your own and `--defaults none` proposes with none; give `propose`
  what you gave `suggest`.

`propose` settles the open forks with `--choose WORD=NAME` and your reason
with `--why WORD=...`, and hands the result to the kernel's door: one
proposal per settled fork, under the words `forge decision willow-WORD`, and
one for the stack, under your sentence. Each carries the card's name, line,
path and SHA-256, so what you seal is what you were shown. The stack is a
page of wants, each above the step that answers it: a short head line (what
you said, the add-on, what you chose it over and your reason, in your words),
the card's own line, then the step. They are numbered in the order they run,
under up to three headings, each only when it has a step:

      ## for “read my email and tell me when the boiler is due”
      ## what you chose
      ## in every stack

      Want 2: “due”: coming-up, not renewals, because it has the dates.
      coming-up: Dates written in your files in the next N days: appointments, renewals, deadlines.
      - coming-up -- --box {box}

The first holds what your words reached, the second each fork you settled,
the third the defaults. Cut any want, or add your own (a want in your words,
then the add-on that answers it), and it is your stack. The stack add-on
reads only the headings and the `-` steps, and heads each step's page with
the lines above it, so the why goes with the step. Its report is
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

    python adapters/deps/forge/suggest.py scores --box DIR [--json]

    forge: populated, 2 close forks settled by your seal; the first taken 1 of 2
    ## by rank
      rank 1  first, the recommendation: 1 of 2
      rank 2  second: 0 of 2
      rank 3  third: 0 of 2
      none    none of them: 1 of 2
    ## by matcher
      ranks 8390ca66e35c  the first taken 1 of 2
    ## its confidence
      now      no confidence yet: 1 of 5 blind close picks sealed on this matcher
      blind    its first taken 1 of 1 blind
      in view  its first taken 0 of 1 with the recommendation in view
    ## each
      forge/decisions/willow-close-….json  “…”: tip-pin, rank 1 of tip-pin, hook-pin, weights-pin (row 9)

Every fork's proposal keeps what you were shown, a word's as well as the
search's: the cards in their order, the one recommended (only the close
fork has one), where your pick fell, and the matcher it was ranked by.

`scores` reads the forks you settled back off your record: only the ones
you sealed that still stand, through the kernel's `sealed` and `standing`.
For the close fork it is how often the search's first card was the one you
took, counted by place and kept apart per matcher, so a change that moves
a card starts a count of its own. For a word's fork
it is how often that word's alias line offered a card you took, and how
often you said none: a word that keeps getting none is a line of
ui/search-words.txt to argue. The blind close picks are the matchmaker's
measured hit rate, and the only thing a close fork's confidence is made
from. Once you have sealed five blind close picks on one matcher, the next
close fork says you took the search's first k of n and states (k+1)/(n+2)
as its confidence: five of five is 0.86, never a certainty, and a rate
under one half says no confidence (the Forge states one only in the
direction it believes). Before that, or under half, the fork says why it
has none, and the Forge records no prediction. A pick made with the
recommendation in view counts toward neither the confidence nor its
score; `scores` sets its rate beside the blind one, and the gap between
them is how often you took the search's first because it was said. Each
blind fork keeps the confidence it had, and `scores` scores those against
what you took with the Forge's own calibration: its Brier score (0 is
foresight, 0.25 a coin at one half), the mean said and how often the first
was taken. It writes nothing.

A blind fork costs you the hint, so it is one in five and no more, and the
confidence waits on five of them: about twenty-five close forks. Picks you
sealed under forge 0.3 count toward none of it: they were all made in view,
and under a matcher known by its bytes. They stay in `scores`' rank and
matcher groups, under that old matcher's name. The blind
ones are known by the hash of their words, so a sentence put another way
may come out in view; and the search is the same program for anyone who
runs it, so a blind fork hides its order from a glance, not from someone
set on knowing it. What was predicted is kept on the proposal with your
pick, not committed on the record before it: proving it came first is the
cup's (a commitment made when a fork is posed and opened after the pick,
as willow's dice are to have it), and not built here.

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
resolves. A word's fork carries no confidence: no made-up 0.5 is scored.
Only the `close` fork carries a recommendation, the search's first, and a
confidence only once your seals have measured one, so the Forge's build
loop records a prediction only when there is something to score. When a real sentence misses, add a
line to `ui/search-words.txt`; when one maps wrong, argue the line.

Exit codes, the report's: 0 steps found and nothing waits on you, a stack
sealed for these words, nothing named (`empty`), or `scores`; 42 a fork waits on you
or your seal is waited on (`populated`), or forge-play missing or older than
0.10 (`unreachable`, said in the report); 2 refused (a bad command line, a
folder that isn't a box or whose record doesn't verify, a fork left
unsettled or settled with an option not on offer, a stack sealed for these
words already, a card beside this script that won't read).

**Needs:** forge-play 0.10 or newer, which needs Python 3.11 or newer.

**Uses:** the kernel's `bite` and `propose`, so every question and every
suggestion is a row; its `sealed` and `standing`, so a seal is believed only
on the kernel's word; its exit codes; `ui/assemble.py` and the stack add-on,
to build and run what you sealed; similar's `Want`, to point when nothing is
named.

**Never:** seals, reads the key (the kernel reads it, to check a proof),
writes anything but through the kernel or under the folder you name, runs a
stack you didn't seal, ranks on its own (what similar's search ranks is only
ever the `close` fork's options), or asks a model. `suggest` writes nothing at
all. The forks are yours to settle, and the seal is yours.
