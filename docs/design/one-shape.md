# Design note: one shape, at every size

**Status: a shape written down, drafted 2026-11-11. Nothing here is sealed,
nothing is law, and most of it is not built.** It was drafted by an AI
session from what the maintainer said across one conversation, which began
with supercomputers and ended in this repository. Where their words set the
direction they are quoted. Everything else is the session's reading of
them, and theirs to cut. It builds on two earlier notes: the repo as a box,
[repo-index.md](repo-index.md), and a sealed stack served to a model,
[serve.md](serve.md).

## The idea, in one line

> What was written is kept apart from what was asked of it. An answer says
> which of the two it came from, and what kind of thing that was, or it
> says it doesn't know. What isn't there is kept too, as a gap, with
> whatever was planted in it.

The maintainer's claim is that this one shape holds at every size, from one
person's folder to every machine there is, and that the year's work has
been whittling it at the small sizes first.

## Where it came from

The conversation started from a view of supercomputing:

> "I think supercomputer is doing the wrong thing."
>
> "Remembering over recomputing, and shared computing."

Most time on the large machines goes to many similar runs, not one great
one: the same model with other starting values, the same calculation for
the next candidate. A result is published as a paper and the run behind it
is not kept in a form the next group can trust, so the next group runs it
again. The machines are shared only by a queue. The claim is that a result
should be remembered under a name made from its inputs, by whoever
computed it, and found by whoever needs it next.

## The shape, in four parts

1. **The pile and the record are apart.** The pile is what was written.
   The record is what was asked of it, what was suggested and what was
   approved. The kernel only reads the pile and only appends to the record.
2. **An answer names where it came from, or refuses.** A passage is served
   with its file and line. A suggestion is held until a person seals it.
   When the files don't hold an answer, that is said.
3. **A thing says what kind it is.** Written to be read, made from other
   things by a script, made up for a test, an idea not built, an account of
   what was done. Kinds answer as equals unless something keeps them apart.
4. **A gap is kept, and a seed is not served as a plant.** The maintainer's
   words: "I think knowledge grows from the gaps, and the seeds in them."
   A question that found nothing, a thing that was tried and failed, an
   idea written down where it was met: each is worth keeping, labelled as
   what it is.

## The sizes

| size | where the shape stands | how far it is whittled |
|---|---|---|
| one person's folder | the kernel: a pile, a record, a seal | built; six kernels held to the same test cases |
| one add-on | a card that promises what it writes, a guard that holds its tests to that | built |
| one study | sources, questions and pass rules frozen before anything is asked | built, and used in the demos |
| two people | a sealed answer sent with its proof, checked by whoever receives it | built as add-ons; little used yet |
| this repository | the repo asked of itself, as a box | begun on the day of this note |
| a field of specialists | results, failures and gaps shared under names made from their inputs | not built |
| every machine | "Anything with a chip and a wire." | a sketch |

The last row, in the maintainer's words: "Use what's in the buildings.
Think about the piles of things that could be wired together all running a
kernel and a stack."

## What a day of running it on itself showed

The stack in [demo/kept](../../demo/kept/README.md) asked this repository
what it remembers. What follows is from that folder's report, and each
number is one a step printed.

**The shape held where it was tried.** An index read once and kept
answered 48 questions in three seconds, where one question through the
kernel takes ten. A simulation run twice gave the same bytes both times, so
the second run bought nothing. A file's name, computed from its bytes
alone, was the name git gives it.

**The repository does not yet hold itself to it.**

- **It found itself.** Once the stack's own report was committed into the
  folder it asks, the stack answered from its report. The count of
  questions held whole rose from 16 to 25, and a question that had found
  nothing was answered with the sentence saying it found nothing. The pile
  is now pinned to a commit from before the report existed.
- **Its kinds answer as equals.** Of the sixteen top answers, four came
  from a list a script makes, three from the changelog, three from a card,
  two from tests, two from files nothing declares, one from code and one
  from a made-up person's file. An idea for an add-on was served as if the
  add-on were built.
- **Its record forgets its own work.** After 28 steps the record held two
  rows. What the steps found is in a folder beside it, on no chain.
- **Its core has no kind.** The kinds add-on counts 1,778 files, and 178
  that nothing declares: the kernel, its ports, its test cases and its law
  among them.

**A rule held when it was a check, and not when it was a page.** The same
session was stopped by the docs test, the version check, lint and the guard
on an add-on's writes. It was not stopped from putting a stack inside the
folder it asks, from running add-ons beside the stack, or from writing the
person's wants for them, though a guide rules out all three. An agent
follows a page until the page is out of its sight. A check stops it every
time.

## What the larger sizes would need

None of this is built. It is the list the conversation arrived at.

- **A name for the inputs.** A friend's project, science_bitch, gives each
  simulation setup a SHA-256 over its whole saved description. The
  star-system add-on now writes that name on its page, and only when the
  setup it names builds the system that was run.
- **A lookup before a run.** Nothing here yet keeps a result under its
  inputs' name and asks for it before computing. The stack add-on comes
  nearest, when it goes on with a run that was cut off.
- **The near miss.** An exact name finds only an exact match. A run that
  differs after its fifth year shares its first five with another, if each
  step is named by what led to it.
- **The failure, kept.** What was tried and did not work is the largest
  body of computed knowledge that is thrown away.
- **The kind, carried.** Measured, simulated, derived from either, or
  learned from any of them. A memory that mixes these teaches a model from
  another model's guesses.
- **Agreement by construction.** Two machines agree to the last bit only
  when the runtime is the same bytes on both. The wasm add-on is built on
  that.
- **A role for every chip.** Running a job is dear and checking a sealed
  result is nearly free. Not every machine computes: some keep, some
  check, some carry.
- **A standing yes.** The seal is one person approving one thing. A
  thousand jobs an hour needs a permission given once, within limits, and
  that is a change to the law.

## What this note does not decide

- **The law.** Nothing here amends the constitution or loosens the seal.
- **The kernel's rank.** Kinds are an add-on's to use. The kernel serves a
  passage when it holds half the question's words, and that stands.
- **Who keeps a field's memory.** For one person the answer is that they
  do, on their own machine, under their own key. For a field it is open.
- **Whether the outside is as described.** What is said here of
  supercomputing and of other fields is the session's account from
  memory. No source in this repository backs it, and none was fetched.

## The order of work, proposed

Each step is of use where it stands, which is the only order the larger
sizes can be reached in.

1. **Count the kinds.** Done on the day of this note, as the kinds add-on.
2. **A rule for each kind, as a check.** A report does not sit in the pile
   it reports on. A made file names what it was made from. An idea is never
   served as built.
3. **A run on the record.** One row for a stack's run: which steps ran, on
   what, and the hash of what each printed.
4. **The lookup.** A step's output kept under a name made from the add-on,
   its arguments and the bytes it was given, and asked for before it runs.
5. **Two machines.** One runs a job in a fixed runtime and seals what it
   printed. The other needs the same job, asks, and checks the seal.
