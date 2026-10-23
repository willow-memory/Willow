# Changelog

What changed, newest first, by the pull request that changed it. There are no
releases yet; when there are, each gets its own heading here.

## Unreleased

### Added

- An open list of add-on ideas: anyone can add one to `adapters/planned.json`,
  or build one from it. `adapters/stdlib/similar/similar.py` shows what's
  already near an idea, and refuses one with the same line as another.
- Promises on every card and idea: what it writes and where it goes online.
  A guard holds every add-on to its card while its tests run, and fails a
  breach even one the add-on catches and hides.
- Tags on every add-on and idea, up to five; four filled in from the card,
  the rest the author's.
- `mutants`: each stdlib add-on's code broken on purpose a few ways in CI; a
  break its tests miss fails, unless listed as harmless with the reason.
- One contract test for every add-on's command line, and for every reader.
- The standard GitHub files: a pull request template, issue forms for a bug
  and an idea, a code of conduct, a security policy, support, code owners,
  and Dependabot for the workflow's actions.

### Changed

- The full file tree moved from the README to `FILES.md`; the README shows
  the top level. `test_docs.py` holds both to the repo.
- `similar` matches on each entry's line and the tags a person chose, not
  the whole card, whose common words made unrelated add-ons look alike.
- The add-on list shows tags instead of emoji, and says in words what an
  add-on needs installed and where it goes online.
- `plain`, `privacy` and `readings` refuse a bad command line with their own
  usage, not the kernel's.
- Tests added where breaking the code went unnoticed: in books, chats,
  coming-up, office, on-this-day, readings, stale, surprise and todo.
- CI's records take out temp folders, so two failing runs give the same
  record too.

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
