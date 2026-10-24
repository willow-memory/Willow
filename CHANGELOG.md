# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. A release turns
`Unreleased` into `vX.Y.Z · YYYY-MM-DD` ([CONTRIBUTING.md](CONTRIBUTING.md)
says how). The first was v0.1.0.

## Unreleased

### Added

- `web-pages`, a reader for saved web pages, .html and .mhtml: each page's
  paragraphs, headings and list items as paragraphs, under the address it
  came from, or `address: not in the file`. (#18)
- `policy-watch`, an add-on that fetches a terms or policy page each time
  it runs, through snapshot, and says what changed since the last copy,
  sentence by sentence, through clauses. (#18)
- `claim-check`, an add-on that checks a claim against your sources part
  by part: the passages holding every part, those holding the most short of
  that with what they lack, and the parts no file names. (#18)
- `misquote`, an add-on for a quote that is almost in your files: the
  passage holding most of its words in order, and the words it drops, adds
  or changes; quote-check's "not there" made specific. (#18)
- `snapshot`, an add-on that fetches a page or file once into a folder, as
  it came, with its address, the time and its SHA-256 on a hidden line the
  kernel never serves; what couldn't be fetched gets its line too, and
  `check` re-hashes offline. `wayback` finds the Wayback Machine's copy of a
  page in a window of days, saves it as a snapshot and compares it byte for
  byte, saying "no capture" and "couldn't reach it" as themselves. (#16)
- `clauses`, a reader that writes a policy, contract or web page as one
  sentence a passage (wrapped PDF text joined back, page headings kept), so
  an answer lands on the clause; `diff` lists two versions' reworded, added
  and removed sentences. (#16)
- `demo/google-privacy-2026-10-16`, a real policy change: Google's privacy
  policy before and after 16 October 2026, asked in the reporters' words,
  frozen by hash before it ran, with blind rewordings, null questions and an
  absence test, recorded on a kernel record. 11 of 12 pass rules pass. The
  sources are fetched once and kept by hash, not in the repo; CI checks only
  that the frozen files still match. Three ideas from it go on the list:
  `claim-check`, `misquote` and `policy-watch`. (#16)
- `test-impact`, an add-on for maintainers that takes a change (paths from git
  against a base ref, and any you name) and says which of the repo's checks it
  can reach, in ci's own gate names, cheapest and closest first: the
  add-on's tests, `adapters/stdlib/ci/test_contract.py` narrowed to it, the docs test, its
  mutants. It builds the import graph with `ast` and adds a few written rules
  for what imports can't show. A change it can't place runs everything, and it
  always says the full suite still runs after. (#23)
- `ci-why`, an add-on that reads a red CI log (what `ci.py run` printed, or a
  job's raw log) and prints only each failing block: the pytest test, its
  assertion and place, a stale or surviving mutant, a ruff rule and line, a
  traceback's last frame. It reads the CI record when given one to know which
  checks failed, never counts an unreachable check as failing, and says
  "couldn't find a failing block" (exit 42) apart from "the log says it
  passed". It reads only, and goes nowhere. (#24)
- `scan`, an add-on that indexes a folder once and then answers a list of
  questions in seconds with the kernel's own answers, narrowing only which
  passages `rank` looks at. It adds `--changed-from` (ask only what changed
  between two indexes), `--todo`, and `--rank bm25`. (#15)
- `demo/php2shell`, a real bug worked as a demo: whether asking the changed
  code points at the PHP2Shell fix, tested seven ways, each frozen by hash
  before it ran and recorded on a kernel record. Runs go online and are not
  in CI; CI checks only that the frozen files still match. (#15)
- Get started, keep it safe, take it with you: `start` sets willow up in one
  step (the box by the kernel's own init, the key, the starter words, then
  how to open, launch and back it up); `backup` writes the box as one zip
  and keeps it only once every byte and the copied record's chain check
  out, never reading the key or putting it beside it; `history` reads the
  record out in plain sentences, places and counts, never the words;
  `print` writes an answer as a page with its sources, and `--large` in big,
  high-contrast type (the large-print idea, as a switch); `words-it` and
  `words-nl`. (#14)
- Look after your folder, from what willow-bot already does: `secrets-audit`
  lists passwords, keys and card numbers sitting in plain files by file and
  line, never the value; `changed` keeps what's new, edited or deleted as
  fingerprint rows, the first check whole and each later one only what
  changed; `xref` checks every link and file:line in your files is still
  there; `diverge` finds where two copies part, a backup zip included, by
  record row, file and line, and never reads a key. (#14)
- Play, from what willow-bot already plays: `odds` gives any dice's exact
  chances as fractions, with at-least and bands; `horoscope` reads the day
  by the SHA-256 of name and date, the bot's lines kept for `--coder`;
  `dice` rolls on the record from its tip with the bot's seeded stream, and
  `check` throws every roll again; `life` plays Conway's Game of Life as
  one row, its fate named, and `check` plays it again. mutants.py now
  leaves out only a demo's generated life/ folder when it copies the
  repo, not every folder of that name, so an add-on named life is
  mutated like any other. (#14)
- Three hundred and thirty-two ideas on the add-on list, nothing built: readers for what
  people use now (Pocket, Instapaper, wallabag, Karakeep, Joplin, jrnl,
  Journiv, WriteFreely, ArchiveBox, Slack, Discord, Signal, Mastodon,
  Bluesky, Google Takeout, subtitles, AI agents' session files) and tools
  around those agents (memory-import, line-origin, session-cost,
  transcript-redact, agents-md-check); willow inside projects its
  maintainer contributes to (basic-memory, codebase-memory, hermes, mex,
  redential, sigmap, lessons) and beside their own (almanac, corpus-lens,
  homestead, jeles, nestor, oakenscroll, quiet-corner, reconciler,
  safe-app, sap-gate); and for everyday life (family-tree, goodreads,
  letterboxd, listening, recipes, strava, texts, car, garden, gifts,
  milestones, pets, school, subscriptions, tax-year, trips, warranties,
  memoir, in-case, timeline, print, large-print, share); and around the
  forges: readers for GitHub, GitLab and Forgejo exports, gh's JSON, CI
  logs and SARIF, codeowners and advisories, willow's repo on gitlab,
  forgejo and sourcehut, mirror, git-notes, signed-commits, issue-answer,
  pr-context and quote-review; and around npm, PyPI and crates.io:
  readers for lockfiles, SBOMs and installed packages' own docs,
  upgrade-notes, outdated, licenses, provenance, package-contents,
  install-scripts, typosquat, pins, and the kernel and its ports on pypi,
  npm, nuget, maven and crates; and a hundred and ten more across the
  board: readers from Notion, Evernote, Zotero and Jupyter to X, Reddit,
  Matrix, medical records and shell history; nine more languages' common
  words; trackers from habits and symptoms to contracts and livestock;
  notary, witness, sync and forget; desktop, tui, launcher, Telegram,
  email, braille and Anki; quiz, daily-word and tarot; and fuzz, bench,
  Go and Swift ports; and twenty-four rebuilt from what willow-bot built
  by hand: diverge, xref, snapshot, session-seal, retire, lore, rules,
  game-master, odds, beacon, predictions, joins, market-calls, predict,
  ladder, scope and code-first from its one script, and horoscope, losc,
  contribute, contributions, upstream-desk, welcome and ci-why from the
  bot itself; and fifty-six from willow-bot's own idea list:
  search rungs (bm25, ripgrep, by-function, code-shape, symbols, rerank,
  kiwix), the record in the world's formats (merkle, opentimestamps,
  ids, prov, ro-crate, in-toto, wayback, cloudevents), bets on the
  world's data (weather, quakes, pageviews, the front page, tides),
  games with known answers (tic-tac-toe to reversi), and the stupid
  pile (lunatic, spurious, roll-for-merge); and forty-seven more: for
  education (Moodle, Canvas and Classroom exports, past papers, lesson
  plans and standards, gradebook, rubric, support plans, socratic), for
  speed (index-cache, watch, parallel, warm, quantized, night-batch,
  fast-tests, test-impact, test-shards, ci-cache, compiled, pypy), and
  why-not, ask-later, family-box, handoff, box-health, emergency-card
  and others. (#13)
- No terminal, no English required: `browse`, your folder in your web
  browser on 127.0.0.1 (ask, read each answer at its file and line, approve
  a suggestion with a click through the kernel's own `seal`; a secret per
  start, Host and Origin checked, never framed, no scripts), with a
  `launcher` for a double-click file on macOS, Windows and Linux; `digest`,
  one page of what waits on you, what went stale, what's coming up and
  what keeps finding nothing, writing nothing; and `words-de`, `words-es`,
  `words-fr` and `words-pt`, which take a language's common words out of a
  question before the kernel's bite. (#12)
- CLI adapters, sixteen add-ons with nothing to install: `pipe` (JSON lines,
  or grep's file:line: text), `mcp-lite` (the mcp add-on's tools, the
  protocol by hand), `claude-code` (a prompt hook), `shell` (a willow
  command and completion for bash, zsh, fish, PowerShell and cmd), the
  settings that register mcp-lite with Codex CLI, Gemini CLI, Copilot,
  Cursor, Windsurf, Zed and OpenCode, and pipe's answers in Vim, Emacs, VS
  Code, JetBrains IDEs and Aider. (#11)
- `live` runs each way-in add-on through the real program it's for (bash,
  zsh, fish, PowerShell, Vim, Neovim, Emacs, Node for VS Code's matcher,
  Codex CLI, Gemini CLI, OpenCode, Copilot CLI, Claude Code and MCP
  Inspector), in a box under a folder with a space in its name: works,
  fails, or not here. CI gains a `tools` job that installs each at a pinned
  version, one gate a check, where a program that isn't there fails the
  job. Its first run found, fixed here before release: VS Code's matcher
  misread a passage quoting a file:line of its own, and Claude Code's hook
  and add line, Aider's run line and JetBrains' parameters split a path
  with a space. (#11)
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

- `live` has a `chrome` check: a page saved by headless Chrome, over its
  DevTools pipe with no library, as .mhtml and as drawn, read by web-pages.
  Its first run found web-pages garbling Chrome's .mhtml, whose page part
  names no charset; fixed, with a test of Chrome's exact form. (#18)
- `test-impact` places a demo's test reached by import by its folder, as it
  places a demo's files, not php2shell's alone; the study's CI row is
  `demo:google-privacy-2026-10-16`, by that rule. (#16)
- CI runs once per change: on pushes to main only, so a pull request no
  longer runs twice (once for its branch's push, once for the pull
  request), and a newer commit on a pull request cancels the run it
  replaces; main's runs are never cancelled. `github.py check` holds both.
  (#31)
- `adapters/stdlib/mutants/mutants.py` runs each mutant without Python's bytecode cache, so a
  same-size break can no longer run the previous mutant's code and pass as
  a survivor; and it no longer breaks the `__main__` guard, which the
  contract test already holds. (#11)
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
