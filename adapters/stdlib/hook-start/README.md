<!-- willow-addon
section: Assistants
line: A SessionStart hook that hands the assistant what needs you, read the way digest reads it, so opening a session writes nothing.
source: bot
added: 2026-10-29
writes: nothing
network: none
role: guards
tags: hooks
uses: digest
-->
# hook-start

An assistant that opens a session knows what is waiting on you.

When a session starts, this tells the assistant what the box is waiting on,
read the way [digest](../digest/) reads it: the suggestions that passed the
door and wait for your approval, the approved answers whose source went
stale, and the dates coming up. It prints the JSON a SessionStart hook reads.

    python adapters/stdlib/hook-start/hook_start.py --box DIR [--days N]

What the assistant is given is digest's
[report](../ci/README.md#the-report-contract) under this add-on's name, then
whose it is and, when a suggestion waits, who approves:

    hook-start: populated, 1 waiting, 1 gone stale, 1 coming up
    ## Waiting for you
      proposal:f391…a7ff  30 October (why: the note)
    ## Gone stale
      bins.txt:1          Thursday night
    ## Coming up (next 14 days)
      car.txt:1           2026-10-30  The car insurance renews on 2026-10-30.

    That is what the person's willow box is waiting on. Say so when it fits;
    only the person approves, and an assistant never does.

The report rides inside the hook's JSON (`hookSpecificOutput`,
`additionalContext`), so what it prints is not itself a report: a box with
nothing to say (an empty report, or one that couldn't look) prints nothing at
all, so a quiet box adds nothing to the session, and it exits 0 whatever it
found, since a hook that exits 42 has what it printed dropped. A section the
digest couldn't look at is said on the report's first line rather than
guessed at. Up to five rows of a group are listed and the rest counted;
questions asked again are left to digest. The record keeps no question's
words, so a suggestion is shown by its answer and its reason, as `digest`
shows it.

It writes nothing, not even the row `kernel.py out` appends, so opening a
session never moves the record's tip. It never reads the key. The line about
approval is a fact for the assistant, not a command: only you approve.

To use it, put the command where the assistant's settings name a SessionStart
hook, with your box's folder after `--box`.

Exit codes: 0 printed (or nothing to say); 2 refused (a record that doesn't
verify, a bad command line), with the reason on standard error and nothing
added to the session.

**Uses:** the digest add-on's sections and its report (`report_of`,
`report_text`).

**Never:** writes anything, approves anything, or reads the key.
