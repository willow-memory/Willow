<!-- willow-addon
section: Keeping track
line: Questions you keep asking: "asked 4 times; approve an answer?"
source: bot
added: 2026-10-23
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# again

The questions you keep asking, counted from the record.

    python adapters/stdlib/again/again.py --box DIR
    python adapters/stdlib/again/again.py --box DIR "your words"

    asked 3 times, last 2026-10-22, answered from garden.md:1
      make it standing? approve an answer for it, and it's served as yours

The record keeps a question as the SHA-256 of its words, never the words, so
this can't print a question back; give it your words and it says how often
you've asked that one.

**The ladder** is willow-bot's: asked once, answered; twice, noticed; three
times, and every third time after, offered. An approved answer is the standing
one, and once there is one the offer stops. Offering is all it does: approving
stays yours.

**Exit codes:** 0 nothing waits on you; 42 a question is at an offer; 2
refused.

**Uses:** the kernel's `read` and `bite_key`.

**Never:** writes anything, or approves.
