# Design note: one way to version everything

**Status: proposal, drafted 2026-11-09. Nothing here is built.** The
operator's: standard versioning across all of willow, the law, its
amendments, every add-on and every idea, because no base is ever finished.
However good the base, someone can add to it, and will find something to
add.

## The idea, in one line

Every thing willow keeps carries a `MAJOR.MINOR.PATCH` version, moved by the
same rule as the code's releases, by the pull request that changes it.

## The rule

Standard semantic versioning, the one `CONTRIBUTING.md` already gives
releases:

- **major:** something that relied on it can no longer rely on it;
- **minor:** something added;
- **patch:** a fix, or wording that changes nothing.

Below 1.0, anything may still change, so a breaking change is a minor step,
as the standard says. Nothing is pushed to 1.0, and nothing is held back
from it: when a thing's promises have settled in practice, it crosses to
1.0 the way any project does, by its author's judgment when the time comes.
1.0 is not an end. There is always 1.0.1.

## What carries one

| Thing | Where it lives | Starts at | Major | Minor | Patch |
|---|---|---|---|---|---|
| The code | a release, `vX.Y.Z`, in CHANGELOG.md and CITATION.cff | v0.1.0, as now | a record, a command or an exit code changes so an older script or record can't follow | a command, an option, an add-on | fixes only |
| The law | its draft number, `Draft X.Y.Z` | 0.15.0 (Draft 0.15 as it stands) | a clause no longer promises what something relied on; never Article 0, which no amendment reaches (VIII.3) | a new clause, or a clause made to promise more | wording that leaves the meaning alone |
| An amendment | its header: the draft it makes, and its `bump` | | | | |
| An idea | its entry in `adapters/planned.json`: `version` | 0.0.1 | | | each change to the entry |
| An add-on | its card: `version` | 0.1.0, its first build | its promises (`writes`, `network`, `hands`) widen, or its command line or exit codes change so an old script breaks: minor below 1.0 | a new option or ability | a fix |

The kernel needs no number of its own. Every record row already carries its
SHA-256, which answers what a number can't, exactly which bytes wrote the
row, and its human-facing version is the release's.

Today's starting points: the 187 ideas at 0.0.1, the 350 built add-ons at
0.1.0, and the law at 0.15.0. Its history keeps the numbers it was made
under, Drafts 0.1 to 0.15; the next is the first with three parts.

## One step per pull request

A pull request moves each thing it touches once, by the size of the largest
change it makes to that thing. Four new clauses in one pull request are one
minor step for the law, not four, though each stays its own amendment: the
piece is the pull request ([pieces](pieces.md)). So the amendments on this
branch, III.6, IV.10, V.10 and VI.8, make Draft 0.16.0 together.

## How it is held

Each check compares the pull request with main:

- **The law:** `constitution/amend.py check` reads each amendment's `bump`
  and holds the draft it makes to the step from the last one; several
  amendments in one pull request share the one draft.
- **Add-ons and ideas:** `adapters/stdlib/readme/readme.py check` refuses a
  card or an idea that changed without a version step, a step that skips
  (0.1.0 to 0.3.0), and a widened promise taken as a patch.
- **Releases:** `test_docs.py`, as now, holds CHANGELOG.md and CITATION.cff
  to the same number.

A check can say a step is missing or too small. It can't say a thing has
reached 1.0; that is a person's call.

## What it changes

- `constitution/amend.py`: three-part drafts, a `bump` field, one draft for
  the amendments of one pull request. The amendments already made keep
  their headers; nothing leaves the record.
- `adapters/README.md` and `adapters/stdlib/readme/readme.py`: `version` on every card and idea,
  with the rule above; one pull request gives the 537 their starting
  numbers.
- `CONTRIBUTING.md`: the Releases section names the rule as the one for
  everything.
- This branch's four amendments: renumbered from Drafts 0.16 to 0.19 to one
  Draft 0.16.0, once `constitution/amend.py` takes it.

## The order of work

1. This note.
2. The law's numbering in `constitution/amend.py`, then this branch's amendments as one
   Draft 0.16.0.
3. Versions for ideas and add-ons: the field, the 537 starting numbers and
   the check, as a pull request of its own.
