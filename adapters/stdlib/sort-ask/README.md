<!-- willow-addon
section: Finding things
line: A model on this machine suggests a category for each file your phrases didn't place, citing a passage, for your seal.
source: new
added: 2026-11-03
writes: record
network: loopback
role: suggests
uses: sort
output: report
-->
# sort-ask

The rung after [sort](../sort/): for each file your phrases left unsorted,
or in more than one category, a model on this machine suggests one of your
categories, citing the passage that shows it, and the kernel holds the
suggestion for your seal. Nothing is placed here.

```
python adapters/stdlib/sort-ask/sort_ask.py --box DIR --categories FILE \
    --model NAME [--url URL] [--limit N] [--now TS] [--json]

sort-ask: populated, 2 suggestions of 3 files asked about, by llama3.1:8b
## suggested
  allotment.txt    garden  (waits on your seal)
  health-note.txt  health  (waits on your seal)
## not suggested
  README.md        no category of yours, cited: NONE
```

**How each file is asked.** The kernel bites on the file's own opening
words, so the question is on your record and the file's passages are
served (its opening comes back as an echo, which is what the model should
read). The model is sent labelled facts and one plain question: your
categories with the phrases that mean them, the file's place, its served
passages numbered, and "Which one category is this file about? Answer with
one line: a name from the list and the passage that shows it". The example
in that line is never one of your categories: a small model copies the
example's name.

**Only a model here.** URL is Ollama's http://127.0.0.1:11434/v1 unless you
give another, and one off this machine (anything but a loopback address or
localhost) is refused before anything is sent. Asked at temperature 0 with
a fixed seed.

**What goes to the door.** An answer naming one of your categories (case
aside) and citing a passage the bite served is proposed: the file, the
category, the passage, and which model said so. Anything else is listed
under **not suggested** with why, and proposed to no one. A file a
suggestion already stands for, sealed or waiting, isn't asked again.
`--limit N` asks about the first N files, in sort's order.

**Which model.** Run your models over a few files you know the answer to
before trusting one: on one laptop, llama3.1:8b and mistral:7b put three
test files right; llama3.2:3b named whichever category came first;
qwen3:4b was right but spent minutes thinking.

It prints [a report](../ci/README.md#the-report-contract), and `--json`
gives the same report as one JSON object.

Exit codes, the kernel's: 0 nothing left to ask about (empty); 42
suggestions wait on your seal, or files were asked and none fitted
(populated), or the model didn't answer (unreachable); 2 refused
(a bad command line, a URL off this machine, no box, a FILE with no
category in it).

**Uses:** sort's own `categories`, `sort` and `placed`, and the kernel's
`chunks`, `words`, `bite` and `propose`.

**Never:** places a file; seals; asks a model off this machine; sends the
model anything but your categories and the passages a bite served.
