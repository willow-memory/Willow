# Security

Willow's whole job is to be trusted with someone's own files, so a way around
any of its promises is a security problem, and is welcome.

## What counts

- an approval accepted without the person's key, or a forged one served as
  approved;
- a past row of the record changed, removed or reordered without `verify`
  saying so;
- the key read, copied or printed by anything but the kernel's own `seal`
  and `verify`;
- an original file changed, when the pile is only ever read;
- an add-on going online, writing outside what its card says, or writing the
  record except through the kernel, without the guard catching it;
- anything that sends a person's files, questions or answers anywhere.

A wrong answer, a missed passage or a slow search is a bug, not a security
problem: open an issue for those.

## How to report one

In public, with the **A security problem** issue form. Willow runs only on
your own machine and has no server to attack, so there is nothing for a
private report to protect, and a public one reaches everyone who needs to
know at once: whoever runs it, and whoever wrote the lines at fault.

Say what you did, what happened, and what you expected, with the smallest
made-up folder and commands that show it. **Leave out anything from your own
files.**

If you can, name the lines at fault, as `PATH:FIRST-LAST`. A workflow
(`.github/workflows/security.yml`) looks each one up with git blame, finds
the pull request that wrote it (`adapters/stdlib/ci/whose.py`), and names
that pull request's author on the report. That is so they hear about it
from the start, not to blame them: the lines are a place to begin.

The fix goes under `### Fixed` in [CHANGELOG.md](CHANGELOG.md) and names
the report, and who found it if they'd like to be named.

## What's supported

The `main` branch. There are no releases yet, so a fix lands there.
