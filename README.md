# willow

[![CI](https://github.com/willow-memory/Willow/actions/workflows/ci.yml/badge.svg)](https://github.com/willow-memory/Willow/actions/workflows/ci.yml)
[![Python 3.9 to 3.14](https://img.shields.io/badge/python-3.9%20to%203.14-blue)](.github/workflows/ci.yml)
[![Licence: Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue)](LICENSE)

**Ask questions of your own files, and get back only what you wrote or what
you approved.**

`kernel.py` is a single Python file that searches a folder you choose, answers
in your files' own lines with the file and line number for each, and refuses
to guess when your files don't hold an answer. Answers from anywhere else (an
AI model, a script, another person) are held until you approve them with a
private key. Every step is written to a tamper-evident log you can audit at
any time.

- **One file, no dependencies:** Python 3.9 or newer, standard library only.
  Copy `kernel.py` anywhere and run it.
- **Local only:** it has no network code at all, and a test enforces that.
- **Verifiable:** the log is a hash chain. An edit to one past entry is
  detected, and a forged approval is never accepted. A whole chain rewritten
  and re-hashed from the edit onward is not detected on its own; see
  [LIMITS.md](LIMITS.md).
- **Portable:** reimplemented in Java, TypeScript and C#, and all four are held
  to the same 4,668 test cases.

**Built to be built on.** Add-ons read more kinds of files (PDFs, email,
chats, office documents), track what matters (dates coming up, forecasts,
flashcards, a care log), keep approved answers honest, and let AI assistants
hand in suggestions they can never approve themselves.
[See every add-on.](ADDONS.md)

**Contents:** [Your first five minutes](#your-first-five-minutes) · [Building on it](#building-on-it) · [What you can build on it](#what-you-can-build-on-it) · [How it works](#how-it-works) · [Commands](#commands) · [Guarantees, and the tests behind them](#guarantees-and-the-tests-behind-them) · [Where it falls short](#where-it-falls-short) · [How it's verified](#how-its-verified) · [What's in this repo](#whats-in-this-repo) · [Licence](#licence)


## Your first five minutes

Nothing to install beyond Python. Check it works, then ask questions of a
made-up beekeeper's six years of notes:

```
$ git clone https://github.com/willow-memory/Willow && cd Willow
$ python kernel.py test
kernel: the eight beats held
$ python demo/odile/make_life.py
$ python kernel.py init --box odile-record --pile demo/odile/life --key odile.key
$ python kernel.py bite --box odile-record "how are the bees"
```

The answer is up to three passages from her files, each with its file and
line. [The full five minutes](docs/tour.md) goes on: a question her files
don't answer, teaching it her words, and approving an answer with the key.


## Building on it

**Add-ons** go in `adapters/stdlib/` if they need nothing beyond Python, or
`adapters/deps/` if they need something installed, tested at its pins and
at its floor (each package's last 2020 release, or its first). An add-on may use
`kernel.py`; `kernel.py` never uses an add-on, and runs the same without any.
An add-on writes to the log only through `kernel.py`, so `verify` still holds.
Each one has its code, a card saying what it's for and what it never does, and
tests that CI runs. The card opens with a short header (section, one line,
source, date added) that [What you can build on it](#what-you-can-build-on-it)
is generated from. To build a planned one, take its entry out of
`adapters/planned.json` in the same change. The rules are in
[adapters/README.md](adapters/README.md). What every change follows, add-on or not, is in
[CONTRIBUTING.md](CONTRIBUTING.md).

**Ports** to another language go in `ports/` and must pass
`python vectors/compare.py` with zero unexplained differences. Go and Rust are
the obvious next ones; [vectors/README.md](vectors/README.md) explains how the
existing three were made to agree.



## What you can build on it

Everything beyond the kernel is an add-on: a folder beside it that uses it and
never changes it. Here is what's built, and what's still an idea that anyone
can pick up ([CONTRIBUTING.md](CONTRIBUTING.md) says how):

<!-- willow:summary -->
- **Reading more kinds of files:** PDFs, email, chats, calendars, notes and office files, as text it can search. Built: [books](adapters/stdlib/books/), [calendar](adapters/stdlib/calendar/), [chats](adapters/stdlib/chats/), [clauses](adapters/stdlib/clauses/), [jrnl](adapters/stdlib/jrnl/), [mail](adapters/stdlib/mail/), [notes](adapters/stdlib/notes/), [office](adapters/stdlib/office/), [parallel](adapters/stdlib/parallel/), [pdf](adapters/deps/pdf/), [snapshot](adapters/stdlib/snapshot/), [star-system](adapters/deps/star-system/), [subtitles](adapters/stdlib/subtitles/), [web-pages](adapters/stdlib/web-pages/). Ideas: *agent-transcript, almanac, apple-notes, archivebox, bank, bibtex, bluesky, bookmarks, canvas, chordpro, ci-logs, code-comments, codebase-memory, confluence, corpus-lens, day-one, discord, dotfiles, evernote, family-tree, forgejo-dump, gh-json, git-history, github-archive, gitlab-export, goodreads, google-classroom, google-keep, health, home-sensors, homestead, instapaper, irc, jira, joplin, journiv, jupyter, karakeep, latex, lessons, letterboxd, linkedin, listening, location-history, lockfiles, logs, man-pages, manifests, mastodon, matrix, mediawiki, medical-records, meta-archive, moodle, music-library, musicxml, notion, ocr, orders, package-docs, past-papers, pgn, photos, places, pocket, quiet-corner, readwise, recipes, reddit, rtf, sarif, sbom, screenplay, scripture, scrivener, sheets, shell-history, sigmap, signal, slack, steam, strava, takeout, teams, texts, trello, voice, wallabag, writefreely, x-archive, zotero*.
- **Finding things:** more ways to look: every match, this date in past years, an exact quote, by meaning, past typos. Built: [all](adapters/stdlib/all/), [amounts](adapters/stdlib/amounts/), [codeowners](adapters/stdlib/codeowners/), [duplicates](adapters/stdlib/duplicates/), [fair-merge](adapters/stdlib/fair-merge/), [first-mention](adapters/stdlib/first-mention/), [fuzzy-dates](adapters/stdlib/fuzzy-dates/), [index-cache](adapters/stdlib/index-cache/), [latent](adapters/deps/latent/), [misquote](adapters/stdlib/misquote/), [on-this-day](adapters/stdlib/on-this-day/), [people](adapters/stdlib/people/), [pile-build](adapters/stdlib/pile-build/), [pile-gold](adapters/stdlib/pile-gold/), [pile-rank](adapters/stdlib/pile-rank/), [pile-rungs](adapters/stdlib/pile-rungs/), [pile-serve](adapters/stdlib/pile-serve/), [pile-store](adapters/stdlib/pile-store/), [pile-sweep](adapters/stdlib/pile-sweep/), [quote-check](adapters/stdlib/quote-check/), [reading-level](adapters/stdlib/reading-level/), [said](adapters/stdlib/said/), [scan](adapters/stdlib/scan/), [surprise](adapters/stdlib/surprise/), [typos](adapters/stdlib/typos/), [why-not](adapters/stdlib/why-not/). Ideas: *bm25, by-function, code-first, code-shape, crosswalk, kiwix, meaning, my-lessons, promises, record-sql, rerank, ripgrep, standards, symbols, upgrade-notes, vectors, watch*.
- **Your own words:** teaching it the words you use, so a question finds what your files call it. Built: [abbreviations](adapters/stdlib/abbreviations/), [accents](adapters/stdlib/accents/), [nicknames](adapters/stdlib/nicknames/), [starter-words](adapters/stdlib/starter-words/), [words-ar](adapters/stdlib/words-ar/), [words-cy](adapters/stdlib/words-cy/), [words-de](adapters/stdlib/words-de/), [words-es](adapters/stdlib/words-es/), [words-fr](adapters/stdlib/words-fr/), [words-it](adapters/stdlib/words-it/), [words-nl](adapters/stdlib/words-nl/), [words-pl](adapters/stdlib/words-pl/), [words-pt](adapters/stdlib/words-pt/), [words-ru](adapters/stdlib/words-ru/), [words-sv](adapters/stdlib/words-sv/), [words-tr](adapters/stdlib/words-tr/). Ideas: *dialect, memoir, stems, synonyms, tatoeba, vocab, words-hi, words-ja, words-zh*.
- **Keeping track:** dates coming up, numbers over time, to-dos, care logs, invoices, forecasts and flashcards. Built: [across](adapters/stdlib/across/), [again](adapters/stdlib/again/), [coming-up](adapters/stdlib/coming-up/), [debts](adapters/stdlib/debts/), [digest](adapters/stdlib/digest/), [gaps](adapters/stdlib/gaps/), [habits](adapters/stdlib/habits/), [lending](adapters/stdlib/lending/), [outdated](adapters/stdlib/outdated/), [policy-watch](adapters/stdlib/policy-watch/), [readings](adapters/stdlib/readings/), [renewals](adapters/stdlib/renewals/), [stack](adapters/stdlib/stack/), [symptoms](adapters/stdlib/symptoms/), [todo](adapters/stdlib/todo/). Ideas: *ask-later, attendance, baby-log, budget, car, care, contracts, crowd, cycle, flashcards, foia, food-log, forecasts, garden, gifts, gradebook, grant-report, home-upkeep, hours, inventory, invoices, job-hunt, lab-notebook, livestock, market-calls, mileage, milestones, minutes, mood, oakenscroll, pets, predict, reading-log, rubric, school, session-cost, subscriptions, support-plan, syllabus, tax-year, trips, upstream-desk, warranties*.
- **Trust and proof:** answers you can check later: exports, stale answers, what changed, signed and encrypted records. Built: [backup](adapters/stdlib/backup/), [box-health](adapters/stdlib/box-health/), [changed](adapters/stdlib/changed/), [claim-check](adapters/stdlib/claim-check/), [contradictions](adapters/stdlib/contradictions/), [diverge](adapters/stdlib/diverge/), [export](adapters/stdlib/export/), [history](adapters/stdlib/history/), [ids](adapters/stdlib/ids/), [in-toto](adapters/stdlib/in-toto/), [licenses](adapters/stdlib/licenses/), [merkle](adapters/stdlib/merkle/), [prov](adapters/stdlib/prov/), [session-seal](adapters/stdlib/session-seal/), [stale](adapters/stdlib/stale/), [timeline](adapters/stdlib/timeline/), [tip-pin](adapters/stdlib/tip-pin/), [wayback](adapters/stdlib/wayback/), [xref](adapters/stdlib/xref/). Ideas: *encrypt, family-box, git-notes, handoff, in-case, jeles, line-origin, losc, mirror, nestor, notary, opentimestamps, paper-key, pgp, provenance, quote-review, redential, report, retire, ro-crate, sap-gate, signed-commits, sync, thesis, time-capsule, witness*.
- **Privacy and safety:** phone numbers, card numbers and keys hidden in answers, or found sitting in files. Built: [a11y-check](adapters/stdlib/a11y-check/), [advisories](adapters/stdlib/advisories/), [install-scripts](adapters/stdlib/install-scripts/), [package-contents](adapters/stdlib/package-contents/), [pii-audit](adapters/stdlib/pii-audit/), [privacy](adapters/stdlib/privacy/), [risky-code](adapters/stdlib/risky-code/), [secrets-audit](adapters/stdlib/secrets-audit/), [transcript-redact](adapters/stdlib/transcript-redact/), [typosquat](adapters/stdlib/typosquat/). Ideas: *forget, kids, scrub, student-records*.
- **Assistants:** AI assistants that can ask and suggest, but never approve. Built: [aider](adapters/stdlib/aider/), [claude-code](adapters/stdlib/claude-code/), [codex-cli](adapters/stdlib/codex-cli/), [copilot](adapters/stdlib/copilot/), [cursor](adapters/stdlib/cursor/), [gemini-cli](adapters/stdlib/gemini-cli/), [hook-fail-closed](adapters/stdlib/hook-fail-closed/), [hook-fuzz](adapters/stdlib/hook-fuzz/), [hook-leaks](adapters/stdlib/hook-leaks/), [hook-pin](adapters/stdlib/hook-pin/), [hook-replay](adapters/stdlib/hook-replay/), [hook-shell](adapters/stdlib/hook-shell/), [hook-start](adapters/stdlib/hook-start/), [hosts](adapters/stdlib/hosts/), [instruction-files](adapters/stdlib/instruction-files/), [mcp](adapters/deps/mcp/), [mcp-lite](adapters/stdlib/mcp-lite/), [opencode](adapters/stdlib/opencode/), [serve](adapters/stdlib/serve/), [windsurf](adapters/stdlib/windsurf/), [zed](adapters/stdlib/zed/). Ideas: *assistant-scores, basic-memory, cassettes, claude, hermes, hook-checks, hook-cite, hook-compact, hook-errors, hook-feedback, hook-guard, hook-handoff, hook-impact, hook-read-first, hook-sequence, hook-stop, hook-tiers, hooks-elsewhere, issue-answer, ladder, local-model, mcp-by-hash, memory-import, mex, model-fit, night-batch, openai-compatible, persona-card, plain-language, quantized, same-way, schema-check, second-opinion, serve-piles, silence-log, translate*.
- **Ways to use it:** other ways in: pipes, your shell and your editor, plain sentences, a page on this machine, answers read aloud. Built: [browse](adapters/stdlib/browse/), [emacs](adapters/stdlib/emacs/), [jetbrains](adapters/stdlib/jetbrains/), [pipe](adapters/stdlib/pipe/), [plain](adapters/stdlib/plain/), [print](adapters/stdlib/print/), [repo-pile](adapters/stdlib/repo-pile/), [shell](adapters/stdlib/shell/), [start](adapters/stdlib/start/), [vim](adapters/stdlib/vim/), [vscode](adapters/stdlib/vscode/). Ideas: *anki, annotations, badge, braille, calendar-out, cloudevents, datasette, deep-links, desktop, dictate, email-ask, emergency-card, home-assistant, kiosk, launcher, llms-txt, obsidian, pr-context, qr, rss-out, safe-app, share, socratic, speak, static-search, telegram-bot, tui, warm*.
- **Play:** seeded, replayable games on the record, such as dice and the Game of Life. Built: [daily-word](adapters/stdlib/daily-word/), [dice](adapters/stdlib/dice/), [horoscope](adapters/stdlib/horoscope/), [life](adapters/stdlib/life/), [odds](adapters/stdlib/odds/), [quiz](adapters/stdlib/quiz/), [tarot](adapters/stdlib/tarot/). Ideas: *art-of-the-day, beacon, chess-puzzle, connect-four, dice5e, front-page, game-master, gutenberg, hanoi, horoscope-grades, ink-story, joins, lore, lunatic, mastermind, movie, nim, ninety-percent, oracle-text, pageviews, pile-poetry, predictions, quake-bets, real-sky, reversi, roll-for-merge, rules, sokoban, spurious, tic-tac-toe, tides, todays-place, weather-bet*.
- **For maintainers:** the repo's own tools: CI, the list, tests that can fail. Built: [agents-md-check](adapters/stdlib/agents-md-check/), [bench](adapters/stdlib/bench/), [bot-venv](adapters/stdlib/bot-venv/), [ci](adapters/stdlib/ci/), [ci-cache](adapters/stdlib/ci-cache/), [ci-memo](adapters/stdlib/ci-memo/), [ci-why](adapters/stdlib/ci-why/), [fast-tests](adapters/deps/fast-tests/), [github](adapters/stdlib/github/), [live](adapters/stdlib/live/), [mutants](adapters/stdlib/mutants/), [pins](adapters/stdlib/pins/), [profile](adapters/stdlib/profile/), [readme](adapters/stdlib/readme/), [restack](adapters/stdlib/restack/), [similar](adapters/stdlib/similar/), [slow-tests](adapters/stdlib/slow-tests/), [test-impact](adapters/stdlib/test-impact/), [test-shards](adapters/stdlib/test-shards/). Ideas: *ci-baseline, ci-bets, code-stats, compiled, contribute, contributions, crates, docs-i18n, forgejo, fuzz, gitlab, go, maven, novelty, npm, nuget, property-tests, pypi, pypy, reconciler, repo-index, repro, sourcehut, swift, welcome*.
<!-- /willow:summary -->

<!-- willow:front show=pick week=2026-W44 -->
**Add-on of the week**

**[history](adapters/stdlib/history/)** — Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words.

*Drawn for 2026-W44: SHA-256 of "willow add-on of the week 2026-W44", modulo the 158 built add-ons in name order.*

[Every add-on, 158 built of 470, and how to add one: ADDONS.md](ADDONS.md)
<!-- /willow:front -->


## How it works

```
your folder ──read on every question──▶ paragraphs ──ranked──▶ top 3 passages
(--pile)                                                          │
                                                                  ▼
suggested answers ──checked──▶ held, waiting ──you approve──▶ given as the answer
(propose)          (cites must be       (out lists them)   (seal, with your key)
                    passages just shown)
                                  every step ──▶ hash-chained log (--box)
```

Your folder is read fresh on every question; nothing is copied or indexed.
A passage must hold at least half of the question's uncommon words, rarer
words count for more, newer comes before older on a tie, and the top three
come back with their file and line. A suggested answer must cite
passages just shown, and waits until you approve it with your key. Every step
goes on a hash-chained log that `verify` checks.

[How it works, in full](docs/how-it-works.md): what it reads, how it ranks,
your key, the record folder, and suggestions and approvals.


## Commands

```
python kernel.py init    --box DIR --pile FOLDER --key FILE [--words FILE]
python kernel.py bite    --box DIR "your question"
python kernel.py propose --box DIR --file SUGGESTIONS.jsonl
python kernel.py seal    --box DIR proposal:<sha256>
python kernel.py decline --box DIR proposal:<sha256>
python kernel.py verify  --box DIR
python kernel.py out     --box DIR
python kernel.py test
```

| Command | Does |
|---|---|
| `init` | creates the record folder and your key, and links your folder |
| `bite` | answers a question: an approved answer if there is one, else up to three passages from your files |
| `propose` | takes suggested answers and holds the ones that pass |
| `seal` | approves one suggestion with your key |
| `decline` | turns one down, with your key: it isn't offered again |
| `verify` | checks every line of the log, every approval and every No |
| `out` | lists what is waiting for your approval |
| `test` | runs the whole cycle in a temporary folder and checks eight properties |

The commands that write to the log also take `--now TIMESTAMP`, to fix the
time recorded (for scripts and tests).

The exit code is meant for scripts and for other programs calling it:

| Code | Means |
|---|---|
| `0` | a person said it: your files hold it, or you approved it |
| `42` | not enough to say a person said it: nothing matched, or something waits on you |
| `2` | refused: a bad command, a key or record that isn't right, a log that has been changed |


## Guarantees, and the tests behind them

Each is a test that fails if it stops being true. The clause is the one in
[CONSTITUTION.md](CONSTITUTION.md) it holds, or none, for a promise of
willow's own.

| Guarantee | Clause | Enforced by |
|---|---|---|
| Uses only Python's own library, and never an add-on | none | `test_kernel.py` fails on any other import, `adapters` included |
| Never goes online | none | `test_kernel.py` parses the file and fails on any network module, `eval`, `exec`, `compile` or `__import__` |
| Never stores your words | none | the log is checked for the question's and answer's words after a full cycle |
| Never gives a suggestion as an answer until it's approved | `CONST-0-1`, `CONST-0-2` | `kernel.py test`: a suggestion without a seal is listed as waiting, not given |
| Never accepts a forged approval | `CONST-0-4` | `kernel.py test`: a seal with the right shape and a re-hashed chain is still rejected |
| Never serves an approval for a question you didn't seal it for | `CONST-0-4` | `test_kernel.py`: a record rewritten and re-hashed can't change, strip or re-point the question a seal names |
| Never writes past a change | `CONST-0-5` | `kernel.py test`: one edited field in one past line, and every command refuses |
| What no one decided is yours: nothing matched, or something waits on you, is exit 42 | `CONST-0-6` | `constitution/test_eternity.py`: nothing found, an answer waiting and a seal that doesn't prove each end at 42, never 0 |
| Same answer every run | none | the ranking is checked under different hash seeds |
| Every add-on keeps its card's promises: what it writes, where it goes online | `CONST-0-3` | the guard watches every process an add-on's tests start, and fails a breach even one the add-on catches and hides |
| Every add-on's tests can fail | none | each add-on's code is broken on purpose a few ways (`mutants`); a break its tests miss fails CI, unless it's listed as harmless with the reason |
| Every add-on refuses a bad command line, and every reader keeps the same contract | none | one test holds them all to it (`adapters/stdlib/ci/test_contract.py`) |


### The law above them

These guarantees answer to a written law, [CONSTITUTION.md](CONSTITUTION.md),
a draft not yet ratified. Its first article, the eternity clause, is six
things no amendment may ever loosen: no one is the witness to their own work,
no one ratifies their own proposal, no one widens their own reach, a reserved
decision needs the human key, the record is never rewritten, and whatever no
one decided goes to the person.

The law names no code; the code names the law. Each kernel line that enforces
a clause cites it by its Trace ID (`CONST-0-4`), and
[constitution/](constitution/) attacks each of the six against the kernel and
checks it is refused. A coverage report, rebuilt every CI run, lists every
clause and where it is cited, and says why for each it found nothing for.


## Where it falls short

It matches words, not meanings: ask "who owes me money" when your files say
"invoice outstanding" and it finds nothing until a words list connects them.
That, English being built in, and the cost of having no index are in
[LIMITS.md](LIMITS.md), with what it doesn't do on purpose
and why ([DECISIONS.md](DECISIONS.md)). Known bugs, each shown by a test,
are in [BUGS.md](BUGS.md).

It was tested blind. For three of the four characters, a separate AI agent
that never saw the code wrote the files, the needs hidden in them, and the
questions the person would ask; the answers were then scored against what was
hidden. It found what was asked in the files' own
words and missed the rest. The fourth of them, Bernadette, wrote her files in
her apps' raw formats and was run through every add-on at once, readers to
backups (`demo/bernadette/stack.py`). The full results, misses included, are
in `demo/*/STRIP.md`.


## How it's verified

- **CI is built on the kernel.** `python adapters/stdlib/ci/ci.py run` runs every
  check (lint, the tests, every port, every demo) and writes each one as a
  verdict row on a kernel record, which `verify` then checks like any other.
  A tool that isn't installed is recorded as unreachable, never as a pass.
  It is deterministic: the same files give the same record, byte for byte.
  CI runs the same script on every pull request and every push to main, with the tests on Python 3.9 through
  3.14, and keeps each job's record as an artifact. The verdicts are draft;
  merging is the person's call. See [adapters/stdlib/ci](adapters/stdlib/ci/).
- **Four implementations, one behaviour.** `vectors/gen.py` reads 4,668 cases
  out of `kernel.py`, covering canonical JSON, word splitting, HTML text,
  ranking, dates, word forms and every refusal. The Java, TypeScript and C#
  ports must give byte-identical answers. Then the same session runs through
  all four command lines, and every implementation's log is verified by every
  other.
- **The tests were tested.** Bugs were planted deliberately in copies of the
  ports (sorting by UTF-16 instead of code points, floating-point scores, a
  BOM dropped by Node's decoder, and more). A case was added for each one the
  tests missed. The table is in [vectors/README.md](vectors/README.md).
- **The docs are tested too.** `test_docs.py` fails if a doc names a file
  that doesn't exist, if the file tree in [FILES.md](FILES.md) misses a file or
  lists one that isn't there, or if a number in this README (the case count, the kernel's
  length, the size of Odile's files, the Python versions) stops matching the
  repo. A demo write-up that cites a question must cite one its person asked,
  in that question's own words. And `test_docs_fires.py` plants a
  violation for each of those checks in a copy of the repo, and fails if
  the check doesn't catch it.
- **Old runtimes, not assumed:** the tests and every port have also been run
  on Python 3.9.0, JDK 11, Node 14 and .NET 5, all from 2020.


## What's in this repo

The top of it. [FILES.md](FILES.md) lists every file and what it is, and
`test_docs.py` fails if either one and the repo ever disagree.

```
willow/
├── kernel.py                 the whole program (about 1,080 lines)
├── test_kernel.py            its tests
├── test_docs.py              holds every doc to the files that exist, and the trees to the repo
├── test_docs_fires.py        plants a violation for each docs check and makes sure it fails
├── test_strip.py             takes away GitHub, then every add-on, and shows what's left still passes
├── README.md                 this file
├── FILES.md                  every file in the repo, and what it is
├── ADDONS.md                 every add-on, built and planned, generated from their cards
├── CONTRIBUTING.md           the rules every change follows, and how to show it does
├── AGENTS.md                 for AI agents: what CI catches when CONTRIBUTING is missed
├── CLAUDE.md                 one line: read AGENTS.md
├── CODE_OF_CONDUCT.md        how we treat each other
├── SECURITY.md               what counts as a security problem, and how to report it in public
├── CHANGELOG.md              what changed, by pull request, and each release
├── CITATION.cff              how to cite willow; names the newest release once there is one
├── BUGS.md                   the known bugs, made from the tests that show them
├── DECISIONS.md              what's settled, why, and what holds it
├── LIMITS.md                 what willow doesn't do, on purpose or not yet
├── CONSTITUTION.md           the law the kernel is written to enforce (always a draft; now 0.15)
├── constitution/             the checks that answer to it
├── adapters/                 add-ons built on top of kernel.py
├── ports/                    kernel.py rewritten in other languages
├── vectors/                  what keeps the four implementations identical
├── demo/                     four made-up people, and one real bug, to try it on
├── docs/                     the full first five minutes, and how it works in full
├── .github/                  CI, the issue forms, the pull request template: the GitHub add-on's
├── .gitignore                generated files and build output
├── .gitattributes            every file checked out with LF line endings, on every system
├── .editorconfig             the same line endings and indents, for editors
├── ruff.toml                 lint settings
└── LICENSE                   Apache-2.0
```

## Licence

Apache-2.0. See [LICENSE](LICENSE).
