<!-- willow-addon
section: Keeping track
line: Questions you keep asking: "asked 4 times; approve an answer?"
source: bot
added: 2026-10-23
writes: nothing
network: none
role: page
output: report
-->
# again

The questions you keep asking, counted from the record.

    python adapters/stdlib/again/again.py --box DIR [--json]
    python adapters/stdlib/again/again.py --box DIR "your words"

    again: populated, 2 questions asked more than once, 1 at an offer
    ## make it standing? approve an answer for it, and it's served as yours
      question 88d54226abec  asked 3 times, last 2026-10-22, answered from garden.md:1
    ## noticed
      question c54b2d86a630  asked 2 times, last 2026-10-20, nothing in your folder answered it

The record keeps a question as the SHA-256 of its words, never the words, so
this can't print a question back; give it your words and it says how often
you've asked that one.

**Every repeat**, the form with no words, prints [a report](../ci/README.md#the-report-contract),
the shape every report add-on shares: a line saying what it found, then a
group per rung (at an offer, noticed, standing), each row the question's key
and how often it was asked, when last, and what answered it. `--json` gives
the same report as one JSON object. No question asked twice is `empty`. The
form with your words prints its own lines, not a report.

**The ladder** is [willow-bot's](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/ladder.py): asked once, answered; twice, noticed; three
times, and every third time after, offered. An approved answer is the standing
one, and once there is one the offer stops. Offering is all it does: approving
stays yours.

**Exit codes:** 0 nothing waits on you (no repeat, or none at an offer); 42 a
question is at an offer; 2 refused.

**Uses:** the kernel's `read` and `bite_key`.

**Never:** writes anything, or approves.
