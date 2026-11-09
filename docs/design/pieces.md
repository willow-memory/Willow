# Design note: every change a piece of the pile

**Status: proposal, drafted 2026-11-06. Nothing here is built.** It came
from the operator, and is written down here before the kernel half of
[Draft 0.16.0](draft-0.16.md) is built, because it is the first change
meant to enter this way.

## The idea, in one line

Each pull request is a small amendment: its code cites the clause it
answers to, the pull request drafts it, the add-ons check it, and accepting
it adds that one piece to a pile, which the kernel can be asked about like
any other. What nothing settled goes to the person, as exit 42.

## Why now: what landed today, read this way

On 2026-11-06 nineteen pull requests merged on main, #251 to #272. Each was
turned into one file of a pile, a box was made over it, and a stack of
add-ons was run against the box (the worked example below). Three things
showed:

- **The pieces already exist.** Each pull request carries its own account,
  one changelog fragment under `changes/` (#263), which is VI.7's *every
  change carries its account* in practice.
- **They don't cite.** One of the nineteen added a Trace ID (#271, VI.7's).
  The stack's step asking what touched the law found nothing and escalated:
  the right answer for that day, and also the gap, since a piece that
  doesn't say which clause it answers to can't be asked about by clause.
- **The pile was made by hand.** It lived in a session's scratch folder and
  goes when the session does.

## The four steps

1. **Cite.** A new piece names the clauses it answers to, by Trace ID. The
   citations go where VIII.4 and Appendix A already look: in the code at
   the line that enforces, and in the piece's account.
2. **Draft.** The pull request is the proposal: the change, its account and
   its citations together. Nothing in it is accepted by being written.
3. **Check.** The add-ons that already exist do the checking, many ways,
   before anything reaches a person: the guard holds every add-on to its
   card; the mutants show each test can fail (IV.9); the contracts, the
   coverage report, the docs tests, `duplicates`, `stale` and the rest each
   look at a different thing. None of this is new.
4. **Accept, or 42.** What the checks and the pile owner's rule settle
   enters the pile as a piece. What they don't settle is the person's
   (§0.6), and is shown to them as waiting, never passed through quietly.

## The pile owner's rule

Whose pile it is decides how a piece is accepted. On the operator's pile,
the operator's rule; on someone else's, theirs. The design fixes the steps,
not the policy. A rule says, for example:

- whether a merge accepts a piece, or a merged piece waits for the owner's
  seal;
- whether a piece that cites no clause is refused, or comes back as a 42;
- which checks must hold before a piece is offered at all.

The rule is kept the way the words list and the key are kept: by the owner,
where the steps it governs can't write it. A pipeline that could change the
rule it is judged by would be widening its own reach (§0.3).

## What the kernel holds, whatever the rule

- **No seal without the owner's act** (§0.2, §0.4). Where the rule says a
  merge accepts, the pile records that it was merged and by whom, as a
  merge, never written as a seal under anyone's key. Where the rule says
  the owner seals, the piece waits until they do, as any suggestion waits.
- **What no one decided is the person's** (§0.6): exit 42, not 0.
- **The record is never rewritten** (§0.5): a piece that is later undone
  is a new piece that says so; the first stays.

## How this sits beside amendments to the law

A piece that changes the law's own text is a full amendment, as now: a file
in `constitution/amendments/`, a new draft, `constitution/amend.py check`.
Every other piece cites the law and leaves its text alone. So nineteen
pull requests in a day are nineteen pieces, not nineteen drafts. Drafts
0.16.0 is one pull request: one piece, four amendments, one draft.

## What is new, and what is already there

| Step | Already there | New |
|---|---|---|
| Cite | Trace IDs in code; `constitution/coverage.py` finds them; VIII.4 for amendments | a piece's account names its clauses, and the owner's rule says what an uncited piece gets |
| Draft | the pull request; its changelog fragment (#263, #271) | nothing |
| Check | every gate CI runs, and the add-ons that check | nothing |
| Accept or 42 | the kernel's seal, decline and exit codes | the owner's rule, read before a piece is accepted |
| Into the pile | a box over any folder | each accepted piece written as one file of the pile, from git alone, so it works with no host (as `test_strip.py` requires of the rest) |

## The worked example

The pile of 2026-11-06 was made with a short script reading git alone: for
each merge on main's first-parent line, one file with the pull request's
title, its commits' messages (their trailers dropped), the files it changed,
its changelog fragment and the prose it added to markdown. A kernel box was
made over that folder, and `adapters/stdlib/stack/stack.py` ran eleven steps
against it in five pools: what it still owes (`todo`); how a pull request
is opened now, what touches the law, and the two contracts of the day
(`fair-merge`, one question each); what is said twice and who is named
(`duplicates`, `people`). Ten steps answered; the law step found nothing
and the stack ended at 42, as it should have.

## The order of work

1. This note.
2. The kernel half of Draft 0.16.0, entered as the first piece made this way:
   its account cites its clauses.
3. Where a piece's citations are written in its account, and the check that
   reads them.
4. The owner's rule: its file, and what each setting does.
5. The step that writes an accepted piece into the pile, from git, and the
   stack that asks the pile after each one.
