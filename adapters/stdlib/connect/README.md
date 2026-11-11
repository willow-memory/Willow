<!-- willow-addon
section: Assistants
line: What a model on this machine says connects two passages of yours, in a few sentences, each number and name it gives checked against them.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: loopback
role: suggests
output: report
uses: say
-->
# connect

What a model on this machine says connects two passages of yours, in a few sentences, each number and name it gives checked against them.

    python adapters/stdlib/connect/connect.py --box DIR --first PLACE --second PLACE [--model TAG] [--host HOST:PORT] [--chars N] [--timeout SECONDS] [--json]
    python adapters/stdlib/connect/connect.py --box DIR --pairs FILE [the same options]

    connect: populated, 1 pair: 1 connection said, every number and name in it is in the passages
    ## invoices.txt:1 and work/log.csv:98, by llama3.2:3b
      invoices.txt:1   overdue INV-2026-011 Larkfield Community Theatre $640.00 due 2026-06-27
      work/log.csv:98  2026-05-28, Larkfield Community Theatre, Wurlitzer studio upright, service visit, 640.00, INV-2026-011
      said             The first is an overdue invoice and the second is the service visit it bills: the same theatre, invoice number INV-2026-011 and amount.
      checked          every number and name it gives is in one of the two passages, and it speaks of both

Code finds where a thing is. It can say two places belong together only
when they share a number or a name. A small model can say why: asked one
plain question about two passages, it answers in a few sentences. This
asks it, and checks the part of the answer that can be checked.

## The one question

A PLACE is a file of your folder and a line in it, as every report writes
one: `notes/iou.txt:3`. The passage is the kernel's own, the one that
holds that line. The model is asked this and nothing more:

    What's the connection between these two?

    First: (the first passage)

    Second: (the second passage)

    Answer in a few plain sentences, under 500 characters.

There are no rules and no format in it, because small models don't follow
those. What they can do is answer a plain question briefly.

**Short is the point.** `--chars N` sets the 500. Asked for about 500
words, the same models find a connection between any two things, a text
about goulash and a van's oil change among them. Held to a few sentences
they say the one thing they see, or that there is none.

## What is checked, and what can't be

- **Numbers and names.** Every number in the answer, and every word with a
  capital letter or a digit in it, is looked for in the two passages. One
  found in neither is named: the model added it. `640` and `640.00` are
  the same number.
- **Both ends.** An answer that uses no word belonging to one of the two
  passages alone is named too: it has described one end, not connected
  them.
- **Not checked: the reading itself.** Who did what, what caused what,
  whether the two really belong together. That is the model's, shown as
  the model's, and yours to judge. A name that opens a sentence is also
  missed, since any first word has a capital.

A pair with something to look at makes the exit code 42, so a stack flags
it.

## Many pairs

`--pairs FILE` is one pair a line: two places with a tab between them.
Blank lines and lines that start with `#` are skipped. Each pair is a
group of the report, in the file's order.

## The model is on this machine, or it isn't asked

The model is [Ollama](https://ollama.com)'s, asked the way the
[say](../say/) add-on asks it: on `127.0.0.1`, `localhost` or `::1` only.
`--host` (or `OLLAMA_HOST`) at any other address is not asked. `--model`
is the tag, `llama3.2:3b` unless you give one. `--timeout` is the seconds
to wait for one answer, 60 unless you give more. When nothing answers, the
report is `unreachable` with the reason.

## It writes nothing

It reads the two files and asks the model on this machine. Nothing goes
on your record, and it makes no suggestion to approve: the kernel lets a
suggestion cite only what your last question was served, and two passages
picked by hand are not that. A connection is printed, and kept only where
a stack keeps its run.

It prints [a report](../ci/README.md#the-report-contract); `--json` gives
the same as one JSON object.

Exit codes, the kernel's: 0 every pair has a connection said and nothing
to look at; 42 an answer names something neither passage holds or speaks
of one passage only, a place has no passage, or the model couldn't be
asked; 2 refused.
