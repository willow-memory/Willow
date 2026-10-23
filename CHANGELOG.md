# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. There are no
releases yet; when there are, each gets its own heading here.

## Unreleased

### Added

- An open list of add-on ideas: anyone can add one to `adapters/planned.json`,
  or build one from it. `adapters/stdlib/similar/similar.py` shows what's
  already near an idea, and refuses one with the same line as another. (#3)
- Promises on every card and idea: what it writes and where it goes online.
  A guard holds every add-on to its card while its tests run, and fails a
  breach even one the add-on catches and hides. (#3)
- Tags on every add-on and idea, up to five; four filled in from the card,
  the rest the author's. (#3)
- `mutants`: each stdlib add-on's code broken on purpose a few ways in CI; a
  break its tests miss fails, unless listed as harmless with the reason. (#3)
- One contract test for every add-on's command line, and for every reader. (#3)
- A changelog line is owed by every pull request that changes more than the
  docs, ending with its number; CI checks it. (#3)
- `test_docs_fires.py`: each of the docs test's checks is shown to fail on a
  violation planted in a copy of the repo. (#3)
- `BUGS.md`, made from the tests that show each known bug, marked as
  expected to fail; a fix names the bug it fixes under Fixed, and CI checks
  that. (#3)
- `DECISIONS.md`, what's settled and what holds it, and `LIMITS.md`, what
  willow doesn't do. (#3)
- A test that the kernel imports only Python's own library, and no
  add-on. (#3)
- Security problems are reported in public. `adapters/stdlib/ci/whose.py`
  finds the commit behind any line with git alone, or with a host's
  host.json the pull request; on GitHub a workflow tags its author on
  the report. (#3)
- `adapters/stdlib/github/`: everything that needs GitHub, in one add-on
  with `.github/`, so it can be taken away, or another host added beside
  it. `test_strip.py` deletes it and `.github/`, then all of `adapters/`,
  and shows what's left still passes. (#3)
- The standard GitHub files, shaped from the willow repos' own conventions:
  a pull request template built on Evidence (receipts, not claims) and on
  what wasn't checked, issue
  forms for a bug and an idea, a code of conduct, a security policy, and
  Dependabot for the workflow's actions. (#3)

### Changed

- The full file tree moved from the README to `FILES.md`; the README shows
  the top level. `test_docs.py` holds both to the repo. (#3)
- The README's shortfalls moved to `LIMITS.md`, beside what willow
  doesn't do on purpose. (#3)
- `similar` matches on each entry's line and the tags a person chose, not
  the whole card, whose common words made unrelated add-ons look alike. (#3)
- The add-on list shows tags instead of emoji, and says in words what an
  add-on needs installed and where it goes online. (#3)
- `plain`, `privacy` and `readings` refuse a bad command line with their own
  usage, not the kernel's. (#3)
- Tests added where breaking the code went unnoticed: in books, chats,
  coming-up, office, on-this-day, readings, stale, surprise and todo. (#3)
- CI's records take out temp folders, so two failing runs give the same
  record too. (#3)

## 2026-10-23 · pull request #2

### Added

- Add-ons split into `adapters/stdlib/` (nothing to install) and
  `adapters/deps/` (pinned installs, each with its licence).
- The README's add-on list, generated from the add-ons' own cards.
- Readers for notes, mail, calendars, chats, books, office files and PDFs; an
  MCP server that can ask and suggest but never approve.
- Every dependency tested at its pin and at its floor: the last release of
  2020, or its first, or a higher one the card gives a reason for.
- `CONTRIBUTING.md`.

## 2026-10-23 · pull request #1

### Added

- `kernel.py`, its tests, the shared test vectors and the Java, TypeScript
  and C# ports.
- The README, with a file tree and a first five minutes, and a test that
  holds every doc to the files that exist.
- CI as one script on the kernel's own record.
