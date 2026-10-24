# Every file

Every file in the repo, and what it is. `test_docs.py` fails if this tree and
the repo ever disagree. [README.md](README.md) shows the top of it.

```
willow/
├── kernel.py                 the whole program (about 910 lines)
├── test_kernel.py            its tests
├── test_docs.py              holds every doc to the files that exist, and the trees to the repo
├── test_docs_fires.py        plants a violation for each docs check and makes sure it fails
├── test_strip.py             takes away GitHub, then every add-on, and shows what's left still passes
├── README.md                 the front page: what it does, a first try, one add-on, and where to read more
├── FILES.md                  this file
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
│   ├── test_eternity.py      each eternity clause, attacked, and refused by the kernel
│   ├── coverage.py           which clauses are cited where, generated, never tabled
│   ├── test_coverage.py      its tests
│   ├── declarations.json     the verdicts, kept by hand; none recorded yet
│   ├── reach.json            each clause no code cites, answered: out of reach, or open, and why
│   ├── amend.py              how an amendment enters the law, and the check that holds it there
│   ├── test_amend.py         its tests: each way the law and its amendments could drift, refused
│   ├── amendments/           every amendment made here, one file each, numbered in turn
│   │   ├── 0001.md           VIII.4, always a draft: made Draft 0.10
│   │   ├── 0002.md           VIII.1, propose, check, accept: made 0.11
│   │   ├── 0003.md           VIII.3, Article 0 strengthened only by clauses that cite it: made 0.12
│   │   ├── 0004.md           IV.9, a check that cannot fail is no check: made 0.13
│   │   ├── 0005.md           VI.7, every change carries its account: made 0.14
│   │   └── 0006.md           VIII.2, the emergency door on a timer: made 0.15
│   └── README.md             what the kernel answers for, and what it doesn't claim
├── adapters/                 add-ons built on top of kernel.py
│   ├── README.md             the rules every add-on follows
│   ├── planned.json          the add-ons not built yet, as this README lists them
│   ├── stdlib/               add-ons that need nothing beyond Python
│   │   ├── again/
│   │   │   ├── again.py      the questions you keep asking, counted from the record
│   │   │   ├── test_again.py
│   │   │   └── README.md
│   │   ├── aider/
│   │   │   ├── aider.py          the /run line that brings answers into Aider's chat
│   │   │   ├── test_aider.py
│   │   │   └── README.md
│   │   ├── all/
│   │   │   ├── all.py        every passage that holds a question, in the kernel's order
│   │   │   ├── test_all.py
│   │   │   └── README.md
│   │   ├── backup/
│   │   │   ├── backup.py     your record in one zip, every byte and the chain checked; never the key
│   │   │   ├── test_backup.py
│   │   │   └── README.md
│   │   ├── books/
│   │   │   ├── books.py      Kindle highlights and .epub text, as passages
│   │   │   ├── test_books.py
│   │   │   └── README.md
│   │   ├── browse/
│   │   │   ├── browse.py     your folder in your browser, on 127.0.0.1: ask, read, approve with a click
│   │   │   ├── test_browse.py
│   │   │   └── README.md
│   │   ├── calendar/
│   │   │   ├── cal.py        .ics events and .vcf contacts, as dated lines
│   │   │   ├── test_calendar.py
│   │   │   └── README.md
│   │   ├── changed/
│   │   │   ├── changed.py    what's new, edited or deleted since the last check, as fingerprint rows
│   │   │   ├── test_changed.py
│   │   │   └── README.md
│   │   ├── chats/
│   │   │   ├── chats.py      WhatsApp and Telegram exports, a dated line a message
│   │   │   ├── test_chats.py
│   │   │   └── README.md
│   │   ├── ci/
│   │   │   ├── ci.py         this repo's checks as verdict rows on a kernel record
│   │   │   ├── changelog.py  a change beyond the docs adds its entry to CHANGELOG.md, and names a bug it fixed
│   │   │   ├── bugs.py       makes BUGS.md from the tests marked as known bugs
│   │   │   ├── whose.py      which commit wrote these lines, or with a host's host.json which pull request
│   │   │   ├── guard/
│   │   │   │   └── sitecustomize.py  holds each add-on to its card while its tests run
│   │   │   ├── test_ci.py    its tests: the same record every run, and every state
│   │   │   ├── test_guard.py the guard's tests: each broken promise caught
│   │   │   ├── test_contract.py  what every add-on promises alike, held for all of them
│   │   │   ├── test_changelog.py  changelog.py's tests: owed, not owed, and in the wrong place
│   │   │   ├── test_bugs.py  bugs.py's tests: strict marks only, and the list made from them
│   │   │   ├── test_whose.py whose.py's tests: commits, merges, squashes, another host, places refused
│   │   │   └── README.md     its card: gates, states, the guard and exit codes
│   │   ├── ci-why/
│   │   │   ├── ci_why.py     the failing block of a red CI log, plain: the test, the assertion, the line to act on
│   │   │   ├── test_ci_why.py
│   │   │   └── README.md
│   │   ├── claude-code/
│   │   │   ├── hook.py           Claude Code's prompt hook: cited passages at each prompt; setup prints it
│   │   │   ├── test_hook.py
│   │   │   └── README.md
│   │   ├── codex-cli/
│   │   │   ├── codex_cli.py      the config.toml lines that register mcp-lite with Codex CLI
│   │   │   ├── test_codex_cli.py
│   │   │   └── README.md
│   │   ├── coming-up/
│   │   │   ├── coming_up.py  dates in your files in the next few days
│   │   │   ├── test_coming_up.py
│   │   │   └── README.md
│   │   ├── copilot/
│   │   │   ├── copilot.py        the mcp.json lines that register mcp-lite with Copilot, in VS Code and its CLI
│   │   │   ├── test_copilot.py
│   │   │   └── README.md
│   │   ├── cursor/
│   │   │   ├── cursor.py         the mcp.json lines that register mcp-lite with Cursor
│   │   │   ├── test_cursor.py
│   │   │   └── README.md
│   │   ├── dice/
│   │   │   ├── dice.py       dice rolled on the record, seeded by its tip; check throws every roll again
│   │   │   ├── test_dice.py
│   │   │   └── README.md
│   │   ├── digest/
│   │   │   ├── digest.py     one page of what waits on you, gone stale, coming up; writes nothing
│   │   │   ├── test_digest.py
│   │   │   └── README.md
│   │   ├── diverge/
│   │   │   ├── diverge.py    where two copies part: records by row, files, then the first line
│   │   │   ├── test_diverge.py
│   │   │   └── README.md
│   │   ├── emacs/
│   │   │   ├── emacs.py          an M-x willow command: answers in a grep-mode buffer
│   │   │   ├── test_emacs.py
│   │   │   └── README.md
│   │   ├── export/
│   │   │   ├── export.py     approved answers and the question log, as Markdown or CSV
│   │   │   ├── test_export.py
│   │   │   └── README.md
│   │   ├── gemini-cli/
│   │   │   ├── gemini_cli.py     the settings.json lines that register mcp-lite with Gemini CLI
│   │   │   ├── test_gemini_cli.py
│   │   │   └── README.md
│   │   ├── github/
│   │   │   ├── github.py     what the repo needs from GitHub: a security report's comment, .github/ held to the repo
│   │   │   ├── host.json     how GitHub titles the merge of a pull request, for whose.py --host
│   │   │   ├── test_github.py
│   │   │   └── README.md     its card: and .github/ belongs to it
│   │   ├── history/
│   │   │   ├── history.py    your record in plain sentences, places and counts, never the words
│   │   │   ├── test_history.py
│   │   │   └── README.md
│   │   ├── horoscope/
│   │   │   ├── horoscope.py  a daily reading picked by the SHA-256 of name and date
│   │   │   ├── test_horoscope.py
│   │   │   └── README.md
│   │   ├── jetbrains/
│   │   │   ├── jetbrains.py      an external tool for JetBrains IDEs: answers as links to file and line
│   │   │   ├── test_jetbrains.py
│   │   │   └── README.md
│   │   ├── life/
│   │   │   ├── life.py       Conway's Game of Life as one row; check plays it again
│   │   │   ├── test_life.py
│   │   │   └── README.md
│   │   ├── live/
│   │   │   ├── live.py       each way-in add-on run through its real program: works, fails, or not here
│   │   │   ├── test_live.py
│   │   │   └── README.md
│   │   ├── mail/
│   │   │   ├── mail.py       .eml and .mbox, with sender, date and subject
│   │   │   ├── test_mail.py
│   │   │   └── README.md
│   │   ├── mcp-lite/
│   │   │   ├── server.py         the mcp add-on's three tools, the protocol by hand, nothing to install
│   │   │   ├── test_server.py
│   │   │   └── README.md
│   │   ├── mutants/
│   │   │   ├── mutants.py    breaks each add-on's code on purpose and checks its tests notice
│   │   │   ├── accepted.json the breaks that change nothing a person could notice, each with why
│   │   │   ├── test_mutants.py
│   │   │   └── README.md
│   │   ├── notes/
│   │   │   ├── notes.py      Obsidian and Logseq vaults, links and backlinks kept
│   │   │   ├── test_notes.py
│   │   │   └── README.md
│   │   ├── office/
│   │   │   ├── office.py     .docx, .odt, .pptx, .xlsx and .ods, as text
│   │   │   ├── test_office.py
│   │   │   └── README.md
│   │   ├── odds/
│   │   │   ├── odds.py       exact odds for any dice, as fractions
│   │   │   ├── test_odds.py
│   │   │   └── README.md
│   │   ├── on-this-day/
│   │   │   ├── on_this_day.py what your files say happened on this date in other years
│   │   │   ├── test_on_this_day.py
│   │   │   └── README.md
│   │   ├── opencode/
│   │   │   ├── opencode.py       the opencode.json lines that register mcp-lite with OpenCode
│   │   │   ├── test_opencode.py
│   │   │   └── README.md
│   │   ├── pipe/
│   │   │   ├── pipe.py           questions in, one answer a line out: JSON lines, or grep's file:line: text
│   │   │   ├── test_pipe.py
│   │   │   └── README.md
│   │   ├── plain/
│   │   │   ├── plain.py      the kernel's answer as sentences
│   │   │   ├── test_plain.py
│   │   │   └── README.md
│   │   ├── print/
│   │   │   ├── print.py      an answer as a page to print, with its sources; --large for big type
│   │   │   ├── test_print.py
│   │   │   └── README.md
│   │   ├── privacy/
│   │   │   ├── privacy.py    personal data and keys withheld from what a question prints
│   │   │   ├── test_privacy.py
│   │   │   └── README.md
│   │   ├── quote-check/
│   │   │   ├── quote_check.py is this exact quote in my files, and where
│   │   │   ├── test_quote_check.py
│   │   │   └── README.md
│   │   ├── readings/
│   │   │   ├── readings.py   notes beside an answer: numbers over time, dates gone by
│   │   │   ├── test_readings.py
│   │   │   └── README.md     its card: what it adds, uses and never does
│   │   ├── readme/
│   │   │   ├── readme.py     builds this README's generated sections from the cards
│   │   │   ├── test_readme.py
│   │   │   └── README.md     its card: sections, the draw, what it reads
│   │   ├── scan/
│   │   │   ├── scan.py       indexes a folder once, then asks it a list of questions, the kernel's way
│   │   │   ├── test_scan.py  holds its answers to the kernel's, every ranking vector included
│   │   │   └── README.md
│   │   ├── secrets-audit/
│   │   │   ├── secrets_audit.py passwords, keys and card numbers in plain files, by file and line
│   │   │   ├── test_secrets_audit.py
│   │   │   └── README.md
│   │   ├── shell/
│   │   │   ├── shell.py          a willow command and tab completion for bash, zsh, fish, PowerShell and cmd
│   │   │   ├── test_shell.py
│   │   │   └── README.md
│   │   ├── similar/
│   │   │   ├── similar.py    what's already on the list near a new idea
│   │   │   ├── test_similar.py
│   │   │   └── README.md
│   │   ├── stale/
│   │   │   ├── stale.py      approved answers whose cited passage changed or went
│   │   │   ├── test_stale.py
│   │   │   └── README.md
│   │   ├── start/
│   │   │   ├── start.py      set up in one step: the box, the key and the starter words, then what next
│   │   │   ├── test_start.py
│   │   │   └── README.md
│   │   ├── starter-words/
│   │   │   ├── words.txt     a first-day words list, in the kernel's format
│   │   │   ├── starter.py    copies it where yours will live, readable only by you
│   │   │   ├── test_starter_words.py
│   │   │   └── README.md
│   │   ├── surprise/
│   │   │   ├── surprise.py   one passage drawn by a seeded stream, replayable
│   │   │   ├── test_surprise.py
│   │   │   └── README.md
│   │   ├── test-impact/
│   │   │   ├── impact.py     which of this repo's checks a change can reach, closest first, in ci's gate names
│   │   │   ├── test_impact.py
│   │   │   └── README.md
│   │   ├── test-shards/
│   │   │   ├── shards.py     splits the test run into parts by each test's past time
│   │   │   ├── test_shards.py
│   │   │   └── README.md
│   │   ├── timeline/
│   │   │   ├── timeline.py   one matter's lines by date, each cited, written to one file
│   │   │   ├── test_timeline.py
│   │   │   └── README.md
│   │   ├── todo/
│   │   │   ├── todo.py       things marked to do, oldest first
│   │   │   ├── test_todo.py
│   │   │   └── README.md
│   │   ├── vim/
│   │   │   ├── vim.py            a :Willow command: answers in the quickfix list
│   │   │   ├── test_vim.py
│   │   │   └── README.md
│   │   ├── vscode/
│   │   │   ├── vscode.py         a VS Code task: answers in the Problems panel
│   │   │   ├── test_vscode.py
│   │   │   └── README.md
│   │   ├── windsurf/
│   │   │   ├── windsurf.py       the mcp_config.json lines that register mcp-lite with Windsurf
│   │   │   ├── test_windsurf.py
│   │   │   └── README.md
│   │   ├── words-de/
│   │   │   ├── words_de.py   a question in German, its common words out, then the kernel's bite
│   │   │   ├── test_words_de.py
│   │   │   └── README.md
│   │   ├── words-es/
│   │   │   ├── words_es.py   a question in Spanish, its common words out, then the kernel's bite
│   │   │   ├── test_words_es.py
│   │   │   └── README.md
│   │   ├── words-fr/
│   │   │   ├── words_fr.py   a question in French, its common words out, then the kernel's bite
│   │   │   ├── test_words_fr.py
│   │   │   └── README.md
│   │   ├── words-it/
│   │   │   ├── words_it.py   a question in Italian, its common words out, then the kernel's bite
│   │   │   ├── test_words_it.py
│   │   │   └── README.md
│   │   ├── words-nl/
│   │   │   ├── words_nl.py   a question in Dutch, its common words out, then the kernel's bite
│   │   │   ├── test_words_nl.py
│   │   │   └── README.md
│   │   ├── words-pt/
│   │   │   ├── words_pt.py   a question in Portuguese, its common words out, then the kernel's bite
│   │   │   ├── test_words_pt.py
│   │   │   └── README.md
│   │   ├── xref/
│   │   │   ├── xref.py       each link and file:line in your files checked, still there
│   │   │   ├── test_xref.py
│   │   │   └── README.md
│   │   └── zed/
│   │       ├── zed.py            the settings.json lines that register mcp-lite with Zed
│   │       ├── test_zed.py
│   │       └── README.md
│   └── deps/                 add-ons that need something installed
│       ├── README.md         what one must declare: pins, floors, licences, network
│       ├── mcp/
│       │   ├── server.py     your folder for any MCP client: ask and suggest, never approve
│       │   ├── requirements.txt  mcp, pinned
│       │   ├── requirements-floor.txt  mcp at its floor, also tested
│       │   ├── test_mcp_server.py
│       │   └── README.md
│       └── pdf/
│           ├── pdf.py        text out of PDFs, a headed paragraph a page
│           ├── requirements.txt  pypdf, pinned
│           ├── requirements-floor.txt  pypdf at its floor, also tested
│           ├── test_pdf.py
│           └── README.md
├── ports/                    kernel.py rewritten in other languages
│   ├── java/
│   │   └── Kernel.java       JDK 11+, standard library only
│   ├── ts/
│   │   ├── kernel.ts         Node 14+, standard library only
│   │   ├── package.json      TypeScript and Node's types, to compile it
│   │   ├── package-lock.json
│   │   └── tsconfig.json
│   └── csharp/
│       ├── Kernel.cs         .NET 5+, no packages
│       └── Kernel.csproj
├── vectors/                  what keeps the four implementations identical
│   ├── gen.py                reads the test cases out of kernel.py
│   ├── cases.json            4,463 cases, with the answers kernel.py gives
│   ├── kernel_tables.json    Python's Unicode and HTML rules, so ports don't use their own
│   ├── compare.py            runs every port against the cases and each other's logs
│   ├── test_vectors.py       fails if the cases are stale or a port disagrees
│   └── README.md             how the ports were built and what testing them found
├── docs/
│   ├── tour.md               the first five minutes, in full: a question, a gap, her words, an approval
│   └── how-it-works.md       what it reads, how it ranks, the key, the record, approvals
├── demo/                     three made-up people, and one real bug, to try it on
│   ├── odile/                piano tuner and beekeeper, caring for her father
│   │   ├── make_life.py      writes her files into life/, the same bytes every run
│   │   ├── CHARACTER.md      who she is and how her life is written down
│   │   ├── PLANTED.md        the needs hidden in her files, and the traps
│   │   ├── STRIP.md          her questions, and what kernel.py found and missed
│   │   └── names.txt         everyone named in her files, written by make_life.py
│   ├── hollis/               built blind, by an agent that never saw the code
│   │   ├── make_life.py
│   │   ├── CHARACTER.md
│   │   ├── PLANTED.md
│   │   ├── QUESTIONS.md      the questions he would ask, written before any run
│   │   └── STRIP.md
│   ├── teodora/              built blind, from a different line of work
│   │   ├── make_life.py
│   │   ├── CHARACTER.md
│   │   ├── PLANTED.md
│   │   ├── QUESTIONS.md
│   │   └── STRIP.md
│   └── php2shell/            a real bug: the PHP2Shell result, tested seven ways
│       ├── README.md         the claim, the threats, what is frozen, each phase's results
│       ├── FROZEN.json       the SHA-256 of each frozen file, and of the tools when frozen
│       ├── releases.json     PHP's releases and the security commits, pinned by hash
│       ├── make_trees.py     fetches them from php-src, and checks them without git
│       ├── score.py          the frozen hit rule: did a passage land on the fix?
│       ├── score2.py         the second hit rule: also an added run's neighbouring lines
│       ├── phase2.py         the null tests: random draws, null questions, wrong pairs, baselines
│       ├── phase1.py         the blind questions, under both rules, ranked by the kernel and BM25
│       ├── phase3.py         out of sample: seven other CVEs, fetched as git stores them, asked blind
│       ├── phase3.json       those CVEs' releases and fix commits, pinned by hash
│       ├── phase4.py         before the fix: the whole release, ranked three ways, recall at k
│       ├── phase5.py         robustness: rewording, top-k, a words list, and leakage
│       ├── phase6.py         reproducibility: every release, five Pythons, four kernels, a second labeller
│       ├── test_php2shell.py holds the frozen files to their hashes, and the tools to their word
│       ├── results/
│       │   └── phase6-labels.json  the independent labellers' yes or no, item by item
│       └── questions/
│           ├── author.txt    the first look's eight questions, labelled as the author's
│           ├── blind-a.txt   eight written blind, as a security engineer, from the advisories
│           ├── blind-b.txt   eight written blind, as a sysadmin, from one news article
│           ├── blind-c.txt   eight written blind, as terse keywords, from the advisories
│           ├── phase3.txt    eight a CVE for phase 3's seven, written blind
│           ├── reword.txt     the author's eight, rephrased five ways each, blind
│           └── advisory-words.txt  a words list of acronyms the advisories expand
│           └── null.txt      fifty questions with nothing to do with the bug
├── .github/
│   ├── workflows/
│   │   ├── ci.yml            runs adapters/stdlib/ci/ci.py one part a job, tests on Python 3.9 to 3.14
│   │   ├── law.yml           every Monday, the law's check: an expired emergency amendment fails it
│   │   └── security.yml      posts the github add-on's comment on a security report
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug.yml           the form for something wrong
│   │   ├── idea.yml          the form for an add-on idea: the same fields as planned.json
│   │   ├── security.yml      the form for a security problem, in public
│   │   └── config.yml        a link to the contributing rules
│   ├── pull_request_template.md  what a pull request says, and what to check before opening one
│   └── dependabot.yml        weekly updates for the workflow's actions, never the add-ons' pins
├── .gitignore                generated files and build output
├── .gitattributes            every file checked out with LF line endings, on every system
├── .editorconfig             the same line endings and indents, for editors
├── ruff.toml                 lint settings
└── LICENSE                   Apache-2.0
```
