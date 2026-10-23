<!-- willow-addon
section: Your own words
line: A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic).
source: new
added: 2026-10-23
writes: to
network: none
tags: no-install, offline, writes-output, words
-->
# starter-words

A first-day words list: on day one, a person's words aren't their files'
words, and a words list is how the kernel learns yours. This is one to start
from.

    python adapters/stdlib/starter-words/starter.py copy --to ~/my-words.txt
    python kernel.py init --box my-record --pile FOLDER --key my.key --words ~/my-words.txt

`words.txt` is in the kernel's own format: one of your words, then the words
your files might use, a comma between. It covers money, dates, health, home
and car, and people and work. Copy it, keep what fits your files, cut the
rest. `copy` writes it readable only by you (the kernel refuses a list others
can read) and never overwrites.

**What it does on a stranger's folder, measured.** On the two blind
characters' questions about money owed:

- Teodora, "how much do I still owe dev": nothing without a list; with this
  one, her chat where "Dev says he can lend us some till Jan", because her
  files say lend, never owe.
- Hollis, "who still owes me money": still nothing. His debt is in invoices
  and bank lines, and "still" and "money" aren't in them, so no passage holds
  enough of the question.

A starter list is general by design. Tuning it to these two folders would fit
them the way the readings once fitted the first character.

**Uses:** the kernel's `parse_words` (a list it would refuse is never copied).

**Never:** overwrites a file, or writes one anyone else can read.
