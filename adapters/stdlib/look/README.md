<!-- willow-addon
section: Finding things
line: One question sent to the step whose job it is, and answered by the lines that step's kept run holds; your own notes by the kernel.
source: new
added: 2026-11-10
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
uses: route
-->
# look

One question sent to the step whose job it is, and answered by the lines that step's kept run holds; your own notes by the kernel.

    python adapters/stdlib/look/look.py "who still owes me money" --run FOLDER [--box BOX] [--kinds FILE] [--json]

    look: populated, "who still owes me money": money owed (by "owe"); 2 lines from debts and invoices
    ## debts: its 1 line (none holds still, money)
      mail/sent/2024-05-22_fwd_letter.eml:7  2024-05-22 $212.40 Dana - got a letter saying I owe $212.40
    ## invoices: its 1 line (none holds still, money)
      12-invoices.txt:1                      overdue INV-2026-011 Larkfield Community Theatre $640.00 due 2026-06-27, 117 days ago

One box takes every question. [route](../route/) says what kind of question
yours is, and which steps' job that kind is. This goes one step on and
answers it, from what a stack's kept run already found. "who still owes me
money" is no one passage in your files. It is what the debts and invoices
steps printed, so those lines are the answer.

`--run FOLDER` is the folder a stack kept its run in
([stack](../stack/)'s `--to`). Nothing is run again: this reads what each
step said when it ran.

## Which lines you see

- **Lines holding a word of your question come first**, the ones holding
  the most of them on top. "did lakeside pay" puts the Lakeside lines of a
  long list first. The heading says how many hold one.
- **Then the rest, as the step said them.** A short answer is shown whole.
- **The words that only said the kind aren't counted.** In "who still owes
  me money", owes is what sent it to debts; it doesn't pick a line.
- **Eight lines a step.** The heading says when there are more.
- **Each row is at a place you can check.** A line that names a place in
  your files, like `notes/iou.txt:3`, is shown at that place. A line that
  names none (a total, a heading) is shown at its line of the run's kept
  file.

## A thing you wrote down: `--box`

A question that fits no kind, like "mom's goulash recipe", is a thing you
wrote down, and some kinds name the ask beside their steps (a person, a
date). With `--box BOX` that part is asked of your files, and answered as
the kernel answers: up to three passages holding at least half your words.
When the best one lacks some, the heading says which:

    look: populated, "mom's goulash recipe": a thing you wrote down; 3 lines from your files
    ## your files: the passages holding the most of your words; the best holds 2 of 3, lacks recipe
      messages/sms_nell_2021.txt:55  [2021-06-29 10:38] Nell: send me grandma's goulash thing again?

A passage that lacks a word may still be the wrong one. It is shown so you
can tell at a glance. When your files hold nothing for it, the report is
empty and says so; [why-not](../why-not/) says why.

## What is left

Anything it couldn't answer from is a row under `left`, and the exit code
is 42, so a stack flags it:

- a step whose job it is that the run doesn't have (add it to the stack);
- a step that ran and said nothing;
- the ask, when you gave no `--box`;
- every step, when you gave no `--run`.

The kinds are route's: [its kinds file](../route/kinds.txt), or your own
with `--kinds FILE`.
A question sent the wrong way is a line to edit there.

It reads the kinds file, the run's kept files and, with `--box`, your
files. It writes nothing. It prints
[a report](../ci/README.md#the-report-contract); `--json` gives the same as
one JSON object.

Exit codes, the kernel's: 0 answered, or your files hold nothing for it;
42 something was left; 2 refused.
