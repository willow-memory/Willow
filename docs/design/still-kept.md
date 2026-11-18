# Design note: still-kept, is this project still looked after

**Status: an idea, 2026-11-18; nothing is built.** One entry on
`adapters/planned.json`.

## The idea, in one line

Point it at a repo or package and it prints whether anyone is still looking
after it. It only prints.

## Why it is missing

`outdated`, `advisories` and `licenses` ask whether a version is old, has a
known hole, or has a licence you can use. None asks whether a person is still
there to fix the next one. The research behind
[skill-picks](skill-picks.md) found that stars and install counts say how
well known a project is, not whether it is kept up, and a README can say
"deprecated" while its star count stays high (openai/skills did).

## What it reads

- Date of the last commit and the last release, read from the source, never
  from a badge.
- A deprecation or archive notice in the README or the repo's settings.
- How many different people committed in the last year, and whether one
  person did nearly all of it.
- Whether recent issues and pull requests got an answer, and how long it took.
- Whether the owner changed lately. A new owner on an old project is worth
  a line.

## What it says

A short plain verdict (kept, quiet, one person, abandoned) with the numbers
under it, so a reader can disagree. It never says safe or unsafe: that is a
different question.

## Edges

- Online only to read public repositories (`api.github.com`).
- Small stable projects look quiet and are fine. A quiet verdict says so
  instead of calling them abandoned.
- It is the part `skill-picks`, `server-picks` and `which-one` would share.
