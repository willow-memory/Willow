# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. A release turns
`Unreleased` into `vX.Y.Z · YYYY-MM-DD` ([CONTRIBUTING.md](CONTRIBUTING.md)
says how). The first was v0.1.0.

## Unreleased

### Added

- Twenty-two ideas on the add-on list, from what people are using now:
  readers for Pocket, Instapaper, wallabag, Karakeep, Joplin, jrnl,
  Journiv, WriteFreely, ArchiveBox, Slack, Discord, Signal, Mastodon,
  Bluesky, Google Takeout, subtitles and AI agents' session files; and
  memory-import, line-origin, session-cost, transcript-redact and
  agents-md-check. Ideas only: nothing is built.
- Seven ideas for willow inside projects its maintainer has contributed
  to: basic-memory, codebase-memory (codebase-memory-mcp), hermes (Hermes
  Agent), mex, redential (redential-cli), sigmap, and lessons (the Emerging
  Rule community library). Ideas only: nothing is built.
- CI's `similar` job keeps its list of what's near each added idea as the
  run's `similar` artifact, which willow-bot posts in its status comment on
  the pull request; `github.py check` holds the job to it. (#10)
- `CONSTITUTION.md`, willows-grove's Draft 0.9 byte for byte, unratified;
  this repo is its home. `kernel.py` cites the eternity clauses at the
  lines that enforce them (comments only; the vectors regenerated, the
  4,463 cases unchanged). (#4)
- `constitution/test_eternity.py` attacks each eternity clause through the
  kernel's own command line, and `constitution/coverage.py` reports which
  clauses are cited where, every CI run; `constitution/declarations.json` starts empty,
  since verdicts are the person's to record. CI gains `tests:constitution`
  and `tests:coverage`. (#4)
- The law, both ways, held by `test_docs.py`: every citation is a real
  clause; every clause the code cites, a test cites too; every clause is
  cited or answered in `constitution/reach.json` (out of reach, or open,
  with why); and each README guarantee names its clause. (#4)
- The constitution is always a draft, and amended here:
  `constitution/amendments/` holds each amendment, and
  `constitution/amend.py` writes the draft number, history row and lineage
  step each one makes, and refuses a change to the Preamble or Article 0, an
  edit to the record before it, or a clause text the law doesn't carry.
  `test_docs.py` refuses an amendment whose clauses no code and test both
  cite. The first, VIII.4 "Always a draft", makes Draft 0.10. (#4)
- Four more amendments, to Draft 0.14: VIII.1 becomes propose, check,
  accept; VIII.3 says Article 0 is strengthened only by clauses that cite
  it; IV.9, a check that cannot fail is no check, held by the mutants; and
  VI.7, every change carries its account, held by the changelog and
  known-bug checks. (#4)
- Emergency amendments, VIII.2 restated to Draft 0.15: an amendment with
  `expires:` enters by the same checks and merge, expires within 90 days,
  can't renew itself, and once expired fails every run until a full
  amendment keeps or undoes it. A weekly workflow, `.github/workflows/law.yml`, runs the
  law's check so an expired one is caught in a quiet repo too, and the
  GitHub add-on's check holds it scheduled. (#4)
- The checks from #1 to #3 cite the clauses they already enforced: the
  kernel's no-network test III.1 and III.5, the guard and the add-on cards
  II.1, and the generated pages VI.6. Their answers in `constitution/reach.json` go. (#4)

### Changed

- The changelog check skips Dependabot's pull requests, which can't write
  an entry; its updates aren't listed. The GitHub add-on's check fails if
  it skips anyone else. (#9)

## v0.1.0 · 2026-10-23

The first release: this section, and the two pull requests below it from
before releases began.

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
- `.gitattributes`, so every file is checked out with LF line endings
  everywhere: `kernel.py` hashes its own bytes into each record, and a
  Windows checkout turning them into CRLF would change that hash.
  `test_docs.py` checks it, and that no file holds a CRLF. (#3)
- `.editorconfig`, `CITATION.cff`, badges on the README (CI, Python,
  licence; the GitHub add-on checks the first two), and a release process
  in CONTRIBUTING.md; `test_docs.py` holds CITATION.cff to the newest
  release in this file. (#3)
- The standard GitHub files, shaped from the willow repos' own conventions:
  a pull request template built on Evidence (receipts, not claims) and on
  what wasn't checked, issue
  forms for a bug and an idea, a code of conduct, a security policy, and
  Dependabot for the workflow's actions. (#3)

### Changed

- The README is a front page: a contents line, a first try, a generated
  summary of what's built and what's still an idea in each area, one add-on
  feature that can be switched (`show=` on its marker), and summaries that
  link to `docs/tour.md`, `docs/how-it-works.md` and `ADDONS.md`, the full
  add-on list. `test_docs.py` holds the contents line to the sections. (#3)
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

### Fixed

- The clone command named the repo by its old name, `willow`; it is
  `Willow` now, and `cd willow` failed on a case-sensitive system. (#3)

- `privacy`'s test checked that "555" never reached the record, and failed
  whenever one of the record's hashes happened to contain it; it now checks
  for the planted phone number itself. (#3)

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
