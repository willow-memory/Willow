<!-- willow-addon
section: Ways to use it
line: Answers as sentences instead of JSON, each with its file and line.
source: new
added: 2026-10-23
-->
# plain

The kernel's answer as sentences instead of JSON, for a person reading it.

    python adapters/stdlib/plain/plain.py bite --box DIR [--now TS] "your words"

    From mail/2026-03-20-county.txt, line 12:
        The proposed determination limits the above well to in-house
        ...

An approved answer is printed as yours, a passage that only asks the question
back is said to, and when nothing holds the question it says so, then the
kernel's notes on where to look.

**Uses:** the kernel's `main` (its own bite: the record and the exit code are
the kernel's).

**Never:** writes to the record, changes what is served, or hides a refusal:
a refusal passes through as the kernel wrote it.
