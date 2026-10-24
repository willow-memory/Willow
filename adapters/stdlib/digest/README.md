<!-- willow-addon
section: Keeping track
line: One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that keep finding nothing.
source: bot
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, tracking, everyday
-->
# digest

One page of what your folder needs from you.

    python adapters/stdlib/digest/digest.py --box DIR [--days N]

| Section | What it lists |
|---|---|
| Waiting for you | Suggestions that passed the kernel's door and wait for your approval, each with its why and the line that approves it |
| Gone stale | Approved answers whose cited passage changed or went (the [stale](../stale/) add-on's check) |
| Coming up | Dates in your files in the next N days, 14 unless `--days` says (the [coming-up](../coming-up/) add-on's) |
| Asked again | Questions asked more than once that your folder never answered. Counted, not shown, because the record keeps no words. A words list may help. |

Each section is in one of three states, never collapsed into one another:
something to show; nothing, said as nothing; or couldn't look, said with
why (for instance, when the stale add-on was deleted). The rest still show.

It writes nothing, not even the row `kernel.py out` appends, so the record's
tip doesn't move while you read it. That's willow-bot's `peek`, which shows
the morning screen's NEEDS YOU without writing a row. The
[browse](../browse/) page uses it for its front page.

Exit codes, the kernel's: 0 nothing waits on you; 42 a suggestion waits, or
an approval went stale; 2 refused.

**Uses:** the kernel's `read`, `sealed`, `chunks` and `config`; the stale
and coming-up add-ons' own functions.

**Never:** writes to the record or the box, or approves anything.
