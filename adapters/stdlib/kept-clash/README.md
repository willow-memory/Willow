<!-- willow-addon
section: Trust and proof
line: Sealed answers people sent you, side by side: one thing given two dates, times or amounts, or one word defined two ways.
source: new
added: 2026-11-19
version: 0.1.0
writes: nothing
network: none
role: page
uses: share, contradictions
-->

# kept-clash

The answers other people sealed and sent you, read side by side. `share`
gives you each package one at a time, and your own record holds only that one
arrived, not what it said; `contradictions` reads only your own folder. This
reads the packages you kept, and sets two answers that disagree next to each
other, each with who sealed it. Neither is picked.

    python adapters/stdlib/kept-clash/kept_clash.py PATH [PATH ...]

A PATH is a package file, or a folder: every `.pkg` file under it, hidden
folders not read. A package is read only if `share check` says it holds; one
that doesn't is named, with why, and left out. For each that holds, its
answer, its reason, the passages it cites (`notes.md:12`) and the key of the
one who sealed it are listed; a package passed on is read at its core, so the
key is the sealer's, with how many times it was forwarded.

    package:395adab752a3…  from key 8f81cbe4…  (64 hex), 2026-03-12T14:48:00Z
      answer: The program schedule says integration day began at 08:00.
        why: schedule.md, line 4
        cites schedule.md:4
    ...
    TIME    says, integration, began
            package:395adab752a3… key 8f81cbe42a8d…  08:00  (answer) The program schedule says ...
            package:9a04ad57e06f… key 4d5d8190b177…  09:00  (answer) The gate log says ...
    1 disagreement, 2 packages given, 2 hold, 2 answers read; neither side is picked; a kept answer is its sender's seal, never yours.

**Neither side is picked.** Both are shown as written, never merged, never
ranked by who sent them or when. Which is right, or whether both are, is
yours to say. A kept answer is its sender's seal and nothing of yours: only
you seal, through the kernel, from your own files.

**The same thing, by `contradictions`' rule.** Sentences (the answer's and
its reason, split at `. ! ?`) from two different answers say the same thing
when they share at least two words and at least half the shorter one's, the
kernel's way, leaving out small words, numbers, units, months and weekdays.
One word in common is a label, not a subject. The pair then disagree when:

- **DATE**: each sentence states one date (the kernel's `newest`: 2026-06-12,
  19/06/2026; 03/04/2026 is never guessed) and the two differ;
- **TIME**: each states one clock time and the two differ, read on the 24-hour
  clock (`9:00`, `09:00`, `9pm` is 21:00, `9 am`); never a time zone;
- **AMOUNT**: each states one amount of one unit ($, €, kg, hours and the
  rest of `contradictions`' list) and the two differ; $1,200 and $1200.00 are
  one amount. A sentence with two different dates, times or amounts of one
  kind is not read for that kind.

**The same word, defined two ways.** A sentence shaped *TERM is/are/means a
KIND ...* defines TERM ("An operator is a process that runs the gate"). Two
such sentences, from different answers, defining the same TERM (one to three
words, the kernel's stems) disagree when the KIND words (those after the
article, up to *who, that, which, of, for, in, with ...*) have no word in
common: "an operator is a process" and "an operator is a person" are shown as
`WORD`; "a person" and "a human person" are not. The cost: two names for one
kind ("a process" and "a procedure") are shown too, and a definition not
written in that shape isn't read. Side by side, a person sees which is which.
It does not compare two things said in other words that aren't a definition
("we marry on ..." and "the ceremony is on ...").

**Left out, and said.** A package that doesn't hold; a file that isn't a
package; a package that a package you kept `--replaces` (the correction is
read, the first is not, so a correction is not "a disagreement" with what it
fixes); the same answer kept twice (read once); and pairs in a form's field (a
subject said in the same words on three sentences or more, as in
`contradictions`), counted. Two sentences of one answer never disagree with
each other.

**What it can't tell you:** that a key is the person you think it is, or that
a package holds everything its sender sealed (`share`'s own limits). A
disagreement is a place to look, not a verdict.

**Exit codes:** 0 found some; 42 none (no package, none that holds, or none
disagreeing, each said); 2 refused.

**Uses:** `share`'s `read_package`, `problems`, `layers` and `package_id`;
`contradictions`' reading of an amount, its words and its rule for one
subject; the kernel's `newest`, `words`, `stem`, `subject_of` and `config`.

**Never:** reads your seal key or any key; writes a seal, a `received` row or
anything at all; goes online; picks a side; or counts a received answer as
yours.
