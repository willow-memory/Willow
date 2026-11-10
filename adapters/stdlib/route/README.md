<!-- willow-addon
section: Finding things
line: A question sent to the step whose job it is: money owed to debts and invoices, a date to what's coming up, the rest to the ask.
source: new
added: 2026-11-10
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
-->
# route

A question sent to the step whose job it is: money owed to debts and invoices, a date to what's coming up, the rest to the ask.

    python adapters/stdlib/route/route.py "who still owes me money" [--run FOLDER] [--kinds FILE] [--json]
    python adapters/stdlib/route/route.py --questions FILE [--run FOLDER] [--kinds FILE] [--json]

    route: populated, "who still owes me money": money owed (by "owe"); that is the job of debts and invoices
      debts     Who owes whom, from the IOUs in your notes and messages, each cited.
      invoices  For freelancers: invoices and payments matched by the id pattern you give, never guessed.

One box takes every question, and the kernel answers each the same way: it
gives you the passage holding the most of your words. That is right for a
thing you wrote down, like "ruth's phone number". It is wrong for "who still
owes me money". No one passage says that. It is a sum over many lines, and
an add-on, [debts](../debts/), already does that sum. This reads your
question, says what kind of question it is, and names the steps whose job
that kind is.

Each row is a step and what it does, in the words of its own card. A
question that fits no kind is "a thing you wrote down", and its step is
`ask`, the kernel's own answer:

    route: populated, "mom's goulash recipe": a thing you wrote down; that is the job of ask
      ask  The kernel's own answer: the passage holding the most of your words.

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares. `--json` gives the same report as one JSON object.

## The kinds are a file you can read

The kinds are in `kinds.txt`, beside the script. Give your own with
`--kinds FILE`. Each line is a kind, its cues, then its steps:

    money owed: owe, paid me, did * pay -> debts, invoices
    a date: when is, birthday, start date -> coming-up, ask

- **A cue is a word, in any of its forms.** `owe` finds owes, owed and
  owing. It is a whole word: `owe` is not found in "tower".
- **Or a few words that come together, in that order.** `paid me` is found
  in "has ruth paid me back", not in "paid by me".
- **`*` stands for any one word.** `did * pay` finds "did ruth pay".
- **The first line with a cue in your question wins.** So the narrower
  kinds go first. The report says which cue decided: `(by "owe")`.
- **A question with no cue** is a thing you wrote down, and goes to `ask`.
- Blank lines and lines that start with `#` are skipped. Capitals don't
  matter.

These are rules you can read, not a guess. The same question goes the same
way every time. When one takes a wrong turn, the report shows the cue that
sent it there, and the fix is a line to edit: take the cue out, make it
longer, or move its line down. The file that ships is a start, and yours to
change. A bare "when" is not a cue in it, so "the papers from when corinne
and I split the house" stays a thing you wrote down.

## What a run already found: `--run`

`--run FOLDER` is the folder a stack kept its run in
([stack](../stack/)'s `--to`). Beside each step it names, this shows the
file that run kept the step's output in, so your question lands on what was
already found:

    route: populated, "who still owes me money": money owed (by "owe"); that is the job of debts and invoices
      debts     Who owes whom, from the IOUs in your notes and messages, each cited.   mine/run/11-debts.txt
      invoices  For freelancers: invoices and payments matched by the id pattern you give, never guessed.

The file is `<NN>-<NAME>.txt`, the step's place in the stack and its name.
A step that ran more than once shows its last file. For `ask` it is the
run's glance, or else its scan. A step the run doesn't have gets nothing
added, as invoices above.

## Many questions at once: `--questions`

`--questions FILE` takes one question a line, or a name, a tab, then the
question. Blank lines and `#` lines are skipped. A question with no name is
named by its line number. There is a group for each kind, in the kinds
file's order, with "a thing you wrote down" last. A group opens with its
steps, each after `->`, then its questions:

    route: populated, 4 questions: 2 money owed, 1 a date, 1 a thing you wrote down
    ## money owed: 2
      -> debts      Who owes whom, from the IOUs in your notes and messages, each cited.
      -> invoices   For freelancers: invoices and payments matched by the id pattern you give, never guessed.
      3             who still owes me money
      late          has ruth paid me back
    ## a date: 1
      -> coming-up  Dates written in your files in the next N days: appointments, renewals, deadlines.
      -> ask        The kernel's own answer: the passage holding the most of your words.
      1             when's grace's birthday
    ## a thing you wrote down: 1
      -> ask        The kernel's own answer: the passage holding the most of your words.
      4             mom's goulash recipe

## What it doesn't do

It doesn't ask your files anything. It reads your question, the kinds file,
the cards of the add-ons it names, and the names of the files in a run. It
needs no box. A kind is a pointer to a step, not an answer: the answer is
what that step says when you run it. It doesn't run the step, and it writes
nothing.

A step that isn't an add-on in this copy of willow is still named, with
"not an add-on that is here", so a kinds file can't point at nothing
unseen.

**Refused:** a question and `--questions` together, or neither; two
questions (put yours in quotes); an option with no value; a question with
no words; a file that can't be read; a kinds file with a line that isn't
`kind: cue, cue -> step, step`, named by its number; a `--run` that isn't a
folder.

**Exit codes:** 0 routed; 42 a step it names isn't an add-on here; 2
refused.

**Uses:** the kernel's `stem`, so a cue finds a word's other forms as a
question does.

**Never:** asks your files anything, runs a step, or writes.
