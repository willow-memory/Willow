# Design note: which-one, two tools for the same job

**Status: an idea, 2026-11-18; nothing is built.** One entry on
`adapters/planned.json`.

## The idea, in one line

Give it two or more libraries or tools that do the same job; it prints them
side by side on upkeep, licence and fit, with the evidence under each row.
It only prints.

## Why it is missing

`model-shelf` and `model-fit` do this for models. For everything else people
choose by stars and a blog post. The research behind
[skill-picks](skill-picks.md) found star and install counts measure fame,
and ranked lists disagree with the pages they point at.

## What it reads

- The same signals as [still-kept](still-kept.md): last commit, owners,
  answered issues, deprecation notices.
- Licence, read from the repo, with a line when it differs from the
  package's own claim.
- What it needs installed, and how much the person's own files already use.
- Fit: the person's own words for the job, matched against each tool's README
  with the kernel's search, so the match is shown and not asserted.

## What it says

A table, a recommendation only where one row is plainly ahead, and the
evidence for each cell. When it is a close call it says so and stops.

## Edges

- Online only to read public repositories (`api.github.com`).
- It does not install anything or edit a project's dependency file.
