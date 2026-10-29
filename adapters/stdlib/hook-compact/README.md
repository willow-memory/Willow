<!-- willow-addon
section: Assistants
line: A PreCompact hook that prints what the record still holds open, seals waiting and questions unanswered, so it survives the assistant's summary.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, assistant, hooks
-->
# hook-compact

Before an assistant's conversation is summarised, says what the record still
holds open, so it is not lost in the summary.

```
python adapters/stdlib/hook-compact/hook_compact.py --box DIR

Before this conversation is summarised, the person's willow box still holds open:
- 2 suggestions waiting for their seal (only the person approves; an assistant never does):
  - Six hours of sun. (why: the garden notes)
- 1 question asked more than once and never answered (2 times).
Keep these in the summary.
```

A summary keeps what the assistant chose to keep, and what a box is waiting
on is easy to drop. This reads the box the way [digest](../digest/) does and
prints two things. **The seals waiting** are the suggestions that passed the
door and that the person has neither sealed nor declined, each by its answer
and its reason (five listed, then a count). **The questions unanswered** are
those asked twice or more that were never served an answer and never answered
by an approval; the record keeps no question's words, so only how many times
each was asked is said. A quiet box prints nothing at all.

Whether a host takes a PreCompact hook's output into its summary is the
host's to say; this only prints. [hook-start](../hook-start/) hands the same
facts back when the next session opens.

It writes nothing, not even the row `kernel.py out` appends, so the record's
tip does not move; it never reads the key; and what it says is a fact, not a
command to approve anything.

Exit codes: 0 printed (or nothing to say); 2 refused (a record that doesn't
verify, a bad command line). A hook should fail open here: a refusal prints
its reason on standard error and adds nothing.

**Uses:** [digest](../digest/)'s sections, and through it the kernel's `read`,
`sealed` and `declined`.

**Never:** approves, declines or writes anything; reads the key.
