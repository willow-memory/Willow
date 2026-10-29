# willow

[![CI](https://github.com/willow-memory/Willow/actions/workflows/ci.yml/badge.svg)](https://github.com/willow-memory/Willow/actions/workflows/ci.yml)
[![Python 3.9 to 3.14](https://img.shields.io/badge/python-3.9%20to%203.14-blue)](.github/workflows/ci.yml)
[![Licence: Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue)](LICENSE)

**Ask questions of your own files, and get back only what you wrote or what
you approved.**

*A pure kernel for private knowledge, plus the add-ons you choose.
Plant it and everything grows.*

willow is two things:

1. **The kernel.** `kernel.py` is a single Python file that searches a folder
   you choose, answers in your files' own lines with the file and line number
   for each, and refuses to guess when your files don't hold an answer.
   Answers from anywhere else (an AI model, a script, another person) are held
   until you approve them with a private key. Every step is written to a
   tamper-evident log you can audit at any time.
2. **Add-ons.** An open place for the parts you choose, or write yourself:
   they read more kinds of files (PDFs, email, chats, office documents), track
   what matters (dates coming up, forecasts, flashcards, a care log), keep
   approved answers honest, and let AI assistants hand in suggestions they can
   never approve themselves. [See every add-on.](ADDONS.md)

Run the kernel alone, or assemble your own local stack. The kernel is the
seed: complete on its own, and it needs nothing from what grows from it. The
arrow points one way: an add-on uses the kernel, and the kernel never names an
add-on, so it runs the same if you delete every one.

- **One file, no dependencies:** Python 3.9 or newer, standard library only.
  Copy `kernel.py` anywhere and run it.
- **Local only:** it has no network code at all, and a test enforces that.
- **Extractive only:** an answer is passages from your files, each with its
  file and line, or it says it doesn't know.
- **Verifiable:** the log is a hash chain. An edit to one past entry is
  detected, and a forged approval is never accepted. A whole chain rewritten
  and re-hashed from the edit onward is not detected on its own; see
  [LIMITS.md](LIMITS.md).
- **Portable:** reimplemented in Java, TypeScript and C#, and all four are held
  to the same 4,668 test cases.

**Contents:** [Your first five minutes](#your-first-five-minutes) · [What it is not](#what-it-is-not) · [Building on it](#building-on-it) · [What you can build on it](#what-you-can-build-on-it) · [How it works](#how-it-works) · [Commands](#commands) · [Guarantees, and the tests behind them](#guarantees-and-the-tests-behind-them) · [Where it falls short](#where-it-falls-short) · [How it's verified](#how-its-verified) · [What's in this repo](#whats-in-this-repo) · [Licence](#licence)


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


## What it is not

- Not a RAG framework that tries to do everything for you.
- Not a system that generates answers: it quotes your files, and anything an
  assistant suggests waits for you.
- Not something that needs a server, an account or an API key.
- Not a project that hides its rules. [CONSTITUTION.md](CONSTITUTION.md) holds
  the rules the code is written to enforce, [DECISIONS.md](DECISIONS.md) why
  the design is the way it is, and [LIMITS.md](LIMITS.md) what it falls short
  of.


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
never changes it. Here is a taste of each kind; every add-on, built and still
an idea, is in [ADDONS.md](ADDONS.md), and [CONTRIBUTING.md](CONTRIBUTING.md)
says how to pick one up:

<!-- willow:summary -->
- **Reading more kinds of files:** PDFs, email, chats, calendars, notes and office files, as text it can search. For example [pdf](adapters/deps/pdf/) and [mail](adapters/stdlib/mail/).
- **Finding things:** more ways to look: every match, this date in past years, an exact quote, by meaning, past typos. For example [on-this-day](adapters/stdlib/on-this-day/) and [quote-check](adapters/stdlib/quote-check/).
- **Your own words:** teaching it the words you use, so a question finds what your files call it. For example [nicknames](adapters/stdlib/nicknames/) and [abbreviations](adapters/stdlib/abbreviations/).
- **Keeping track:** dates coming up, numbers over time, to-dos, care logs, invoices, forecasts and flashcards. For example [coming-up](adapters/stdlib/coming-up/) and [subscriptions](adapters/stdlib/subscriptions/).
- **Trust and proof:** answers you can check later: exports, stale answers, what changed, signed and encrypted records. For example [stale](adapters/stdlib/stale/) and [tip-pin](adapters/stdlib/tip-pin/).
- **Privacy and safety:** phone numbers, card numbers and keys hidden in answers, or found sitting in files. For example [privacy](adapters/stdlib/privacy/) and [secrets-audit](adapters/stdlib/secrets-audit/).
- **Assistants:** AI assistants that can ask and suggest, but never approve. For example [claude-code](adapters/stdlib/claude-code/) and [mcp](adapters/deps/mcp/).
- **Ways to use it:** other ways in: pipes, your shell and your editor, plain sentences, a page on this machine, answers read aloud. For example [browse](adapters/stdlib/browse/) and [print](adapters/stdlib/print/).
- **Play:** seeded, replayable games on the record, such as dice and the Game of Life. For example [quiz](adapters/stdlib/quiz/) and [life](adapters/stdlib/life/).
- **For maintainers:** the repo's own tools: CI, the list, tests that can fail. For example [mutants](adapters/stdlib/mutants/) and [ci](adapters/stdlib/ci/).
<!-- /willow:summary -->

<!-- willow:front show=pick week=2026-W44 -->
**Add-on of the week**

**[words-pt](adapters/stdlib/words-pt/)** — Portuguese common words ("o", "e").

*Drawn for 2026-W44: SHA-256 of "willow add-on of the week 2026-W44", modulo the 221 built add-ons in name order.*

[Every add-on, 221 built of 470, and how to add one: ADDONS.md](ADDONS.md)
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
