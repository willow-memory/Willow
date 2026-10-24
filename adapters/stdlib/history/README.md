<!-- willow-addon
section: Trust and proof
line: Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, trust, everyday
-->
# history

Your record, read out in plain sentences.

    python adapters/stdlib/history/history.py --box DIR [--days N]

    2026-10-24
      08:00  You asked a question. Nothing in your folder held it.
      08:01  You asked a question again (2nd time). Nothing in your folder held it.
      09:20  A suggestion was handed in for dentist.md. It waits for you.
      09:21  You approved the suggestion for dentist.md.

The record keeps no words, so neither does this:
- A question is known by its fingerprint, which is how it can say "again".
- An answer is known by the places it came from (`dentist.txt:1`).
- An approval is named by the file it writes, never by its text.

A row of a kind it doesn't know is named, not guessed: "A verdict row,
written by ci."

`--days N` keeps the last N days. A record that doesn't verify is refused,
since a history read past a break could tell you something that didn't
happen.

**Uses:** the kernel's `read`; the suggestions' paths in the box.

**Never:** writes anything, or shows a question's words or an answer's text.
