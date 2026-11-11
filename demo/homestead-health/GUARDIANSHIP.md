# Holding a record for someone else: what the pile says

Written 2026-11-11 from the box [README.md](README.md) describes, by
putting [ten questions](guardian-questions.txt) to it and then reading
the files it pointed at. What the homestead repositories say is given as
theirs, at the commits in [sources.json](sources.json). What it might
mean for willow is marked as a proposal, and is nobody's decision yet.

## What was asked, and what came back

All ten were served a passage ([results/guardian-asks.txt](results/guardian-asks.txt)).
Three came straight to the health plan's own paragraphs on the matter:
who holds a child's record, what the household holds as guardian, and
the open decision on minor consent. The other seven were served passages
that hold the question's words and not its answer. Two of those matter,
because the pile has no answer to give:

- **Who decides for an adult who cannot decide.** Nothing in these
  repositories takes it up.
- **Can one person hold a key for another.** Nothing either. The passage
  served was about a storage key, the same word for another thing.

## What the homestead design holds

Read from the health plan in the engine's repository.

1. **For a minor, the operator is guardian and holds the file.** The
   design's founding premise is one operator a household, and the question
   it asks is never "which person may see this" but "what crosses a
   boundary". For a child's ordinary records the premise holds.
2. **Minor-consent care breaks the premise, and the plan says so.** Where
   the law lets a minor consent to certain care alone, the parent is not
   entitled to that record. The plan calls this "an entitlement edge
   inside the household" and says plainly that no rung expresses it:
   "rungs score surfaces, not principals".
3. **The answer for now is scope.** The module holds what the household
   lawfully holds. A minor-consent record is out of scope, and written
   down as out of scope.
4. **Its absence is not shown.** By the design's rule that "a refusal is
   information at the rung of the thing refused", a screen saying
   something about this child is withheld would disclose the very
   category it protects.
5. **Turning eighteen is a handoff, never a deletion.** The record is
   exported with a stated purpose, logged like any export, and handed to
   the person it is about. What stays behind is the household's own
   record of what it did as guardian.
6. **The full answer is left open**, as the plan's largest undecided
   matter, with another project's `guardian_of` edges named as the place
   to start. That project is not in this pile.

A seventh thing turned up by accident. A passage in the engine's safety
review says the app has no isolation between people in one household,
and gives that as the reason two adults there cannot each keep their
own.

## What that might mean for willow

Proposals, for the maintainer.

- **A box a person is the edge homestead says it lacks.** Homestead
  scores what may cross to a screen, a model or an export, with one
  operator behind all of it. Willow's unit is a box under one person's
  key. A teenager's own box, on their own key, is a record the parent's
  box cannot open and does not know of. That answers point 4 as well:
  nothing is rendered as withheld, because nothing in the parent's box
  refers to it.
- **Guardianship would then be a box held for someone, with a day it is
  handed over.** Homestead's handoff maps onto things willow has: the
  record goes out, the grown child starts a box on a key of their own,
  and the guardian's record stays the guardian's, saying what they did.
  What willow lacks is any word for "this box is held on another's
  behalf", so nothing today could say whose it is or when it changes
  hands.
- **Neither design has the adult who cannot decide.** A child's
  guardian is known from the start and the handoff has a date. An
  adult's incapacity arrives without warning and may end. That is the
  case the emergency card answers in part, and it is the one to think
  about next.
- **What must not be built to solve it** is a second way to read a
  person's key. Willow's rule that code never reads the key is the thing
  both designs agree on, in different words.
