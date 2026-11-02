<!-- willow-addon
section: Finding things
line: Your approved answers used as a test: each question asked again, scored by how often the search puts the passage that held it in its top five.
source: box
added: 2026-10-28
writes: record
network: none
tags: pile
-->
# pile-gold

Your seals are the best test willow has. When you seal an answer, the record
ties it to the question it answered, and the proposal names the passages it
cites. Those passages held the answer, by your word. `pile-gold` asks your
questions again and counts how many of those passages each search puts in
its top five.

    python adapters/stdlib/pile-gold/pile_gold.py --box DIR --questions FILE
        [--store STORE] [--now TS]

The record keeps no words, only each question's key, so the questions come
from FILE: one a line, optionally `name<TAB>question`, blank and `#` lines
skipped, as [scan](../scan/) reads them. A question is matched to its seals
by `kernel.bite_key`, so "When is the BOILER serviced?" finds the seal made
for "when is the boiler serviced".

    boiler: kernel 1, pile-rank 1 of 1
    kernel     found 7 of 9 approved passages in the top 5
    pile-rank  found 8 of 9 approved passages in the top 5
    recorded at row 41

Two searches are scored: the kernel's own `rank`, and
[pile-rank](../pile-rank/). The count is over every approved passage, not
averaged per question. A cited passage no longer in the folder (its words
changed or went) is counted as gone, not as a miss. Only sealed answers
count: one still waiting, or one you declined, is no gold.

This is what pile-sweep's passage sizes (still an idea) and any new
rank will be measured against: the questions you actually ask, with the
answers you actually approved.

## Your key and your record

Seals are read through the kernel's `sealed` and `standing`, which check
each against your key: a forged seal is no gold. This add-on never reads the
key itself and never writes a seal. It appends one row, kind `gold`, through
the kernel's `append`: the counts, the number of questions, and the SHA-256
of FILE. No question, no passage, no word goes on the record. When no
question has a sealed answer it says so and records nothing.

## What it reads and writes

It reads the box's record, its proposals and its folder (or a
[pile-store](../pile-store/) store while it matches the folder), and your
words list if the box has one, as the kernel would. It writes only the
record, through the kernel, and reaches no network. Exit codes, the
kernel's: `0` scored and recorded; `42` no question has a sealed answer,
nothing recorded; `2` refused (a bad command line, not a box, a broken
record, or a FILE that can't be read).
