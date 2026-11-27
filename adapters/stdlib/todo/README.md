<!-- willow-addon
section: Keeping track
line: TODO, FIXME and "need to" lines across the folder, oldest first.
source: box
added: 2026-10-23
version: 0.1.3
writes: nothing
network: none
role: page
output: report
-->
# todo

The things you wrote down to do, across your folder, oldest first.

```
python adapters/stdlib/todo/todo.py --box DIR [--json]

todo: populated, 2 lines marked to do, the oldest from 2021-05-14
  memos/2021-05-14_1502.txt:1  2021-05-14  Sold Teo's van. ... Need to call Mesa Mutual and take it off the policy.
## undated
  README.md:40                 TODO: fix the install step
```

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying how many and the oldest date, then a
row per line, the file and line and then its date and the line itself (cut
to 120 characters); the undated ones last, under their own heading.
`--json` gives the same report as one JSON object.

A line counts when it says TODO, FIXME, "need to", "don't forget" or "remember
to", or is an open checkbox. A mark counts as it is written to mark something:

| Mark | Counts | Doesn't |
|---|---|---|
| TODO, FIXME | in capitals: `TODO: fix the install step` | "the todo add-on", "Todo lists", and a file's name (TODO with a dot and an ending after it) |
| "need to" | opening a line or a sentence, or after I or we: "Sold the van. Need to call the insurer.", "I need to book the MOT" | "the file does not need to fit in memory", "you need to restart it" |
| "don't forget", "remember to" | anywhere in a line, in any case | |
| an open checkbox | `- [ ] buy strings` | a ticked one, and one that opens with a template's blank, `- [ ] {item}`: a form not yet filled in |
| any of them, in quotation marks | on a line that opens with who told you it: `Mum: "don't forget the bins"` | someone's words quoted: `- **The ask.** "I still need to sign it"`, and `"need to"` in a page about this report. Inside is an odd number of quotation marks before the mark, or none before and an odd number after (a quote opened on a line above) |

Each is dated by the kernel's own date for its
passage (the latest date in it, its file's name, or the log heading above it);
undated ones come last. The oldest open item is often the one that matters: a
thing said once and never done doesn't get newer.

**Exit codes:** 0 found some (`populated`) or none (`empty`); 2 refused.

**Uses:** the kernel's `chunks`, `dates` and `config`.

**Never:** writes anything.
