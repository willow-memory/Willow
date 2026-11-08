<!-- willow-addon
section: Keeping track
line: One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that find nothing.
source: bot
added: 2026-10-24
writes: nothing
network: none
role: page
tags: everyday
looks-for: coming-up, stale
output: report
-->
# digest

One page of what your folder needs from you.

```
python adapters/stdlib/digest/digest.py --box DIR [--days N] [--json]

digest: populated, 1 waiting, 1 gone stale, 1 coming up, 1 asked again
## Waiting for you
  proposal:f391…a7ff  30 October (why: the note)
## Gone stale
  bins.txt:1          Thursday night
## Coming up (next 14 days)
  car.txt:1           2026-10-30  The car insurance renews on 2026-10-30.
## Asked again
  record.jsonl        a question asked 2 times, never answered
```

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying what it found, then a group for each
section with something in it, each row where, then what. `--json` gives the
same report as one JSON object. A suggestion's where is its whole subject
(cut short above), the one `python kernel.py seal --box BOX <where>` approves.

| Section | What it lists |
|---|---|
| Waiting for you | Suggestions that passed the kernel's door and wait for your approval, each with its why and the line that approves it |
| Gone stale | Approved answers whose cited passage changed or went (the [stale](../stale/) add-on's check) |
| Coming up | Dates in your files in the next N days, 14 unless `--days` says (the [coming-up](../coming-up/) add-on's) |
| Asked again | Questions asked more than once that your folder never answered. Counted, not shown, because the record keeps no words. A words list may help. |

Each section is in one of three states, never collapsed into one another:
something to show, a group of rows; nothing, left out; or couldn't look,
said with why on the first line (for instance, when the stale add-on was
deleted). The rest still show. Nothing anywhere is `empty`, said as "nothing
waits on you"; nothing found but a section it couldn't look at is
`unreachable`, not empty.

It writes nothing, not even the row `kernel.py out` appends, so the record's
tip doesn't move while you read it. That's [willow-bot's `peek`](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/api.py), which shows
the morning screen's NEEDS YOU without writing a row. The
[browse](../browse/) page uses it for its front page, and willow-bot's
`needs` prints its page of sections said in words (`render`), not the report.

Exit codes, the kernel's: 0 nothing waits on you (`empty`, or `populated`
with only dates and questions); 42 a suggestion waits, or an approval went
stale (`populated`), or a section couldn't be looked at and nothing else was
found (`unreachable`); 2 refused.

**Uses:** the kernel's `read`, `sealed`, `chunks` and `config`; the stale
and coming-up add-ons' own functions.

**Never:** writes to the record or the box, or approves anything.
