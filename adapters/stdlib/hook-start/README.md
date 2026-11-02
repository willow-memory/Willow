<!-- willow-addon
section: Assistants
line: A SessionStart hook that hands the assistant what needs you, read the way digest reads it, so opening a session writes nothing.
source: bot
added: 2026-10-29
writes: nothing
network: none
tags: hooks
-->
# hook-start

An assistant that opens a session knows what is waiting on you.

When a session starts, this tells the assistant what the box is waiting on,
read the way [digest](../digest/) reads it: the suggestions that passed the
door and wait for your approval, the approved answers whose source went
stale, and the dates coming up. It prints the JSON a SessionStart hook reads.

    python adapters/stdlib/hook-start/hook_start.py --box DIR [--days N]

What the assistant is given, in plain sentences:

    The person's willow box has 2 suggestions waiting for their approval. Say
    so when it fits; only the person approves, and an assistant never does.
      - Six hours of sun. (why: the garden notes)
    1 approved answer is stale: its source changed or went.
    Coming up (next 14 days): 2026-11-02 garden.md:4  Frost warning

A box with nothing to say prints nothing at all, so a quiet box adds nothing
to the session. A section the digest couldn't look at is left out rather than
guessed at. Up to five items of a section are listed and the rest counted; the
record keeps no question's words, so a suggestion is shown by its answer and
its reason, as `digest` shows it.

It writes nothing, not even the row `kernel.py out` appends, so opening a
session never moves the record's tip. It never reads the key. The line about
approval is a fact for the assistant, not a command: only you approve.

To use it, put the command where the assistant's settings name a SessionStart
hook, with your box's folder after `--box`.

Exit codes: 0 printed (or nothing to say); 2 refused (a record that doesn't
verify, a bad command line), with the reason on standard error and nothing
added to the session.

**Uses:** the digest add-on's four sections.

**Never:** writes anything, approves anything, or reads the key.
