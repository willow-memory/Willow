# Every file

Every file in the repo, and what it is. `test_docs.py` fails if this tree and
the repo ever disagree. [README.md](README.md) shows the top of it.

```
willow/
├── kernel.py                 the whole program (about 1,080 lines)
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
│   │   ├── a11y-check/
│   │   │   ├── a11y_check.py what trips a screen reader in the documents: images without descriptions, headings out of order
│   │   │   ├── test_a11y_check.py
│   │   │   └── README.md
│   │   ├── abbreviations/
│   │   │   ├── abbreviations.py  a question's shorthand read as the files write it, either way; words-list lines
│   │   │   ├── test_abbreviations.py
│   │   │   └── README.md
│   │   ├── accents/
│   │   │   ├── accents.py    a word typed without its accent, read as the files write it; words-list lines
│   │   │   ├── test_accents.py
│   │   │   └── README.md
│   │   ├── across/
│   │   │   ├── across.py     one document across several boxes: each box's digest, export, timeline or readings, composed
│   │   │   ├── test_across.py
│   │   │   └── README.md
│   │   ├── advisories/
│   │   │   ├── advisories.py locked dependencies matched to a downloaded OSV advisory database, offline
│   │   │   ├── test_advisories.py
│   │   │   └── README.md
│   │   ├── again/
│   │   │   ├── again.py      the questions you keep asking, counted from the record
│   │   │   ├── test_again.py
│   │   │   └── README.md
│   │   ├── agents-md-check/
│   │   │   ├── agents_md_check.py   the commands and paths AGENTS.md or CLAUDE.md name that the repo no longer has
│   │   │   ├── test_agents_md_check.py
│   │   │   └── README.md
│   │   ├── aider/
│   │   │   ├── aider.py          the /run line that brings answers into Aider's chat
│   │   │   ├── test_aider.py
│   │   │   └── README.md
│   │   ├── all/
│   │   │   ├── all.py        every passage that holds a question, in the kernel's order
│   │   │   ├── test_all.py
│   │   │   └── README.md
│   │   ├── amounts/
│   │   │   ├── amounts.py    every sum of money in the files, dated by its line, the date above or the file's name
│   │   │   ├── test_amounts.py
│   │   │   └── README.md
│   │   ├── backup/
│   │   │   ├── backup.py     your record in one zip, every byte and the chain checked; never the key
│   │   │   ├── test_backup.py
│   │   │   └── README.md
│   │   ├── bench/
│   │   │   ├── bench.py       how fast the kernel reads and ranks piles of set sizes, per release
│   │   │   ├── test_bench.py
│   │   │   └── README.md
│   │   ├── books/
│   │   │   ├── books.py      Kindle highlights and .epub text, as passages
│   │   │   ├── test_books.py
│   │   │   └── README.md
│   │   ├── bot-venv/
│   │   │   ├── bot_venv.py       does willow-bot's venv, or any named, have what CI needs; the line that runs CI with it
│   │   │   ├── test_bot_venv.py
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
│   │   │   ├── cores.py      ci.py's run as its shards at once on this machine, a record each, shown together
│   │   │   ├── guard/
│   │   │   │   └── sitecustomize.py  holds each add-on to its card while its tests run
│   │   │   ├── test-times.json  seconds each add-on test file took, to cut the add-ons' tests into even chunks
│   │   │   ├── test_ci.py    its tests: the same record every run, and every state
│   │   │   ├── test_guard.py the guard's tests: each broken promise caught
│   │   │   ├── test_contract.py  what every add-on promises alike, held for all of them
│   │   │   ├── test_changelog.py  changelog.py's tests: owed, not owed, and in the wrong place
│   │   │   ├── test_bugs.py  bugs.py's tests: strict marks only, and the list made from them
│   │   │   ├── test_whose.py whose.py's tests: commits, merges, squashes, another host, places refused
│   │   │   ├── test_cores.py cores.py's tests: every gate once across the shards, refusals that run nothing
│   │   │   └── README.md     its card: gates, states, the guard and exit codes
│   │   ├── ci-cache/
│   │   │   ├── ci_cache.py    a cache key per ecosystem from a repo's lockfiles, so CI skips the reinstall
│   │   │   ├── test_ci_cache.py
│   │   │   └── README.md
│   │   ├── ci-memo/
│   │   │   ├── ci_memo.py    a gate whose inputs' bytes are unchanged keeps its verdict: pin a run's keys, plan the rest
│   │   │   ├── test_ci_memo.py
│   │   │   └── README.md
│   │   ├── ci-why/
│   │   │   ├── ci_why.py     the failing block of a red CI log, plain: the test, the assertion, the line to act on
│   │   │   ├── test_ci_why.py
│   │   │   └── README.md
│   │   ├── claim-check/
│   │   │   ├── claim_check.py  a claim, part by part: what holds it all, some of it, and what no file names
│   │   │   ├── test_claim_check.py
│   │   │   └── README.md
│   │   ├── claude-code/
│   │   │   ├── hook.py           Claude Code's prompt hook: cited passages at each prompt; setup prints it
│   │   │   ├── test_hook.py
│   │   │   └── README.md
│   │   ├── clauses/
│   │   │   ├── clauses.py    a long document as one sentence a passage, and a sentence-by-sentence diff
│   │   │   ├── test_clauses.py
│   │   │   └── README.md
│   │   ├── codeowners/
│   │   │   ├── codeowners.py   who owns a file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo
│   │   │   ├── test_codeowners.py
│   │   │   └── README.md
│   │   ├── codex-cli/
│   │   │   ├── codex_cli.py      the config.toml lines that register mcp-lite with Codex CLI
│   │   │   ├── test_codex_cli.py
│   │   │   └── README.md
│   │   ├── coming-up/
│   │   │   ├── coming_up.py  dates in your files in the next few days
│   │   │   ├── test_coming_up.py
│   │   │   └── README.md
│   │   ├── contradictions/
│   │   │   ├── contradictions.py  two lines saying the same thing with a different date or amount, side by side
│   │   │   ├── test_contradictions.py
│   │   │   └── README.md
│   │   ├── copilot/
│   │   │   ├── copilot.py        the mcp.json lines that register mcp-lite with Copilot, in VS Code and its CLI
│   │   │   ├── test_copilot.py
│   │   │   └── README.md
│   │   ├── cursor/
│   │   │   ├── cursor.py         the mcp.json lines that register mcp-lite with Cursor
│   │   │   ├── test_cursor.py
│   │   │   └── README.md
│   │   ├── daily-word/
│   │   │   ├── daily_word.py the day's word from the folder's own words, six guesses marked on the record
│   │   │   ├── test_daily_word.py
│   │   │   └── README.md
│   │   ├── debts/
│   │   │   ├── debts.py      lines speaking of money owed, dated and cited, the sum as written, never netted
│   │   │   ├── test_debts.py
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
│   │   ├── duplicates/
│   │   │   ├── duplicates.py    passages saying the same thing in two files, the newest copy named when it can be
│   │   │   ├── test_duplicates.py
│   │   │   └── README.md
│   │   ├── emacs/
│   │   │   ├── emacs.py          an M-x willow command: answers in a grep-mode buffer
│   │   │   ├── test_emacs.py
│   │   │   └── README.md
│   │   ├── export/
│   │   │   ├── export.py     approved answers and the question log, as Markdown or CSV
│   │   │   ├── test_export.py
│   │   │   └── README.md
│   │   ├── first-mention/
│   │   │   ├── first_mention.py  when the files first mention something: the earliest dated line that holds every word
│   │   │   ├── test_first_mention.py
│   │   │   └── README.md
│   │   ├── fuzzy-dates/
│   │   │   ├── fuzzy_dates.py  dates that admit doubt, read with the doubt kept, in EDTF
│   │   │   ├── test_fuzzy_dates.py
│   │   │   └── README.md
│   │   ├── gaps/
│   │   │   ├── gaps.py       where a log you keep stops: the days it skipped, said as gaps
│   │   │   ├── test_gaps.py
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
│   │   ├── habits/
│   │   │   ├── habits.py     streaks from the short lines written day after day, runs and misses by plain counting
│   │   │   ├── test_habits.py
│   │   │   └── README.md
│   │   ├── history/
│   │   │   ├── history.py    your record in plain sentences, places and counts, never the words
│   │   │   ├── test_history.py
│   │   │   └── README.md
│   │   ├── hook-fail-closed/
│   │   │   ├── hook_fail_closed.py a hook that crashes, hangs or says what can't be read blocks the tool
│   │   │   ├── test_hook_fail_closed.py
│   │   │   └── README.md
│   │   ├── hook-fuzz/
│   │   │   ├── hook_fuzz.py      bad input thrown at a hook, and each one that breaks it named
│   │   │   ├── test_hook_fuzz.py
│   │   │   └── README.md
│   │   ├── hook-leaks/
│   │   │   ├── hook_leaks.py   a PreToolUse hook that refuses a write or command holding a key, password or card number, naming only the kind
│   │   │   ├── test_hook_leaks.py
│   │   │   └── README.md
│   │   ├── hook-pin/
│   │   │   ├── hook_pin.py       a hook runs only as the bytes you approved, pinned on the record
│   │   │   ├── test_hook_pin.py
│   │   │   └── README.md
│   │   ├── hook-replay/
│   │   │   ├── hook_replay.py    every hook answer a row of hashes, and each one run again
│   │   │   ├── test_hook_replay.py
│   │   │   └── README.md
│   │   ├── hook-shell/
│   │   │   ├── hook_shell.py   a command split as the shell splits it, quotes, variables and chains included, before a rule judges it
│   │   │   ├── test_hook_shell.py
│   │   │   └── README.md
│   │   ├── hook-start/
│   │   │   ├── hook_start.py   a SessionStart hook that tells the assistant what waits on the person, read the way digest reads it
│   │   │   ├── test_hook_start.py
│   │   │   └── README.md
│   │   ├── horoscope/
│   │   │   ├── horoscope.py  a daily reading picked by the SHA-256 of name and date
│   │   │   ├── test_horoscope.py
│   │   │   └── README.md
│   │   ├── hosts/
│   │   │   ├── hosts.py          one table of assistants that take an MCP server, and the lines that register willow with each
│   │   │   ├── test_hosts.py
│   │   │   └── README.md
│   │   ├── ids/
│   │   │   ├── ids.py        each file and passage by its Software Heritage ID and one-chunk IPFS CID
│   │   │   ├── test_ids.py
│   │   │   └── README.md
│   │   ├── in-toto/
│   │   │   ├── in_toto.py   each approved answer as an in-toto Statement, its subject hashed from the file written
│   │   │   ├── test_in_toto.py
│   │   │   └── README.md
│   │   ├── index-cache/
│   │   │   ├── index_cache.py  a folder's scan index kept between runs, rebuilt only when a file's hash changed
│   │   │   ├── test_index_cache.py
│   │   │   └── README.md
│   │   ├── install-scripts/
│   │   │   ├── install_scripts.py  the install scripts node_modules would run (preinstall, install, postinstall), by file and line
│   │   │   ├── test_install_scripts.py
│   │   │   └── README.md
│   │   ├── instruction-files/
│   │   │   ├── instruction_files.py   which instruction files each coding agent would load for a folder, in order, with size and hash
│   │   │   ├── test_instruction_files.py
│   │   │   └── README.md
│   │   ├── jetbrains/
│   │   │   ├── jetbrains.py      an external tool for JetBrains IDEs: answers as links to file and line
│   │   │   ├── test_jetbrains.py
│   │   │   └── README.md
│   │   ├── jrnl/
│   │   │   ├── jrnl.py       jrnl journals mirrored, each stamped entry one dated passage
│   │   │   ├── test_jrnl.py
│   │   │   └── README.md
│   │   ├── lending/
│   │   │   ├── lending.py    what you lent, and what your files say came back
│   │   │   ├── test_lending.py
│   │   │   └── README.md
│   │   ├── licenses/
│   │   │   ├── licenses.py   the licence of every installed Python and npm package, and which are copyleft, by file and line
│   │   │   ├── test_licenses.py
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
│   │   ├── merkle/
│   │   │   ├── merkle.py     a Merkle tree over the record: one row proven with a handful of hashes
│   │   │   ├── test_merkle.py
│   │   │   └── README.md
│   │   ├── misquote/
│   │   │   ├── misquote.py   a quote almost in your files: the closest passage, and what differs
│   │   │   ├── test_misquote.py
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
│   │   ├── outdated/
│   │   │   ├── outdated.py   how old each locked dependency is, and which are yanked, deprecated or unmaintained
│   │   │   ├── test_outdated.py
│   │   │   └── README.md
│   │   ├── package-contents/
│   │   │   ├── package_contents.py   what a wheel, sdist, npm tarball or crate holds, and the code it runs on install, by file and line
│   │   │   ├── test_package_contents.py
│   │   │   └── README.md
│   │   ├── parallel/
│   │   │   ├── parallel.py   a reader run over several folders at once, across cores, into one mirror
│   │   │   ├── test_parallel.py
│   │   │   └── README.md
│   │   ├── people/
│   │   │   ├── people.py     everyone the files name, by what they do with a name, and each one's every mention
│   │   │   ├── test_people.py
│   │   │   └── README.md
│   │   ├── pii-audit/
│   │   │   ├── pii_audit.py  the personal numbers in the files, checked never guessed, shown masked
│   │   │   ├── test_pii_audit.py
│   │   │   └── README.md
│   │   ├── pile-build/
│   │   │   ├── pile_build.py  the store built after each change, behind a lock, until it matches the folder
│   │   │   ├── test_pile_build.py
│   │   │   └── README.md
│   │   ├── pile-gold/
│   │   │   ├── pile_gold.py   your sealed answers as a test of the search, scored as recall at five
│   │   │   ├── test_pile_gold.py
│   │   │   └── README.md
│   │   ├── pile-rank/
│   │   │   ├── pile_rank.py   BM25F over words and the folder's own word pairs, titles and questions weighted
│   │   │   ├── test_pile_rank.py
│   │   │   └── README.md
│   │   ├── pile-rungs/
│   │   │   ├── pile_rungs.py  a question climbs words, phrases, embedder; each rung says why it answered or stopped
│   │   │   ├── test_pile_rungs.py
│   │   │   └── README.md
│   │   ├── pile-serve/
│   │   │   ├── pile_serve.py  the passages held warm by one process, asked over a Unix socket in milliseconds
│   │   │   ├── test_pile_serve.py
│   │   │   └── README.md
│   │   ├── pile-store/
│   │   │   ├── pile_store.py  a folder's passages in one SQLite file, each repeat once, used only while it matches
│   │   │   ├── test_pile_store.py
│   │   │   └── README.md
│   │   ├── pile-sweep/
│   │   │   ├── pile_sweep.py  your sealed answers asked at several passage sizes, the best one named
│   │   │   ├── test_pile_sweep.py
│   │   │   └── README.md
│   │   ├── pins/
│   │   │   ├── pins.py       version ranges in package.json or requirements.txt that no lockfile pins
│   │   │   ├── test_pins.py
│   │   │   └── README.md
│   │   ├── pipe/
│   │   │   ├── pipe.py           questions in, one answer a line out: JSON lines, or grep's file:line: text
│   │   │   ├── test_pipe.py
│   │   │   └── README.md
│   │   ├── plain/
│   │   │   ├── plain.py      the kernel's answer as sentences
│   │   │   ├── test_plain.py
│   │   │   └── README.md
│   │   ├── policy-watch/
│   │   │   ├── policy_watch.py  a policy page fetched each run, and what changed since, sentence by sentence
│   │   │   ├── test_policy_watch.py
│   │   │   └── README.md
│   │   ├── print/
│   │   │   ├── print.py      an answer as a page to print, with its sources; --large for big type
│   │   │   ├── test_print.py
│   │   │   └── README.md
│   │   ├── privacy/
│   │   │   ├── privacy.py    personal data and keys withheld from what a question prints
│   │   │   ├── test_privacy.py
│   │   │   └── README.md
│   │   ├── prov/
│   │   │   ├── prov.py   the record as W3C PROV-JSON: what came from what, by which step, sealed by whom
│   │   │   ├── test_prov.py
│   │   │   └── README.md
│   │   ├── quiz/
│   │   │   ├── quiz.py       a passage of your own writing with a word missing, cut and scored on the record
│   │   │   ├── test_quiz.py
│   │   │   └── README.md
│   │   ├── quote-check/
│   │   │   ├── quote_check.py is this exact quote in my files, and where
│   │   │   ├── test_quote_check.py
│   │   │   └── README.md
│   │   ├── reading-level/
│   │   │   ├── reading_level.py  how hard each file reads: Flesch by the book, counted as written, easiest first
│   │   │   ├── test_reading_level.py
│   │   │   └── README.md
│   │   ├── readings/
│   │   │   ├── readings.py   notes beside an answer: numbers over time, dates gone by
│   │   │   ├── test_readings.py
│   │   │   └── README.md     its card: what it adds, uses and never does
│   │   ├── readme/
│   │   │   ├── readme.py     builds this README's generated sections from the cards
│   │   │   ├── test_readme.py
│   │   │   └── README.md     its card: sections, the draw, what it reads
│   │   ├── renewals/
│   │   │   ├── renewals.py   when each thing expires, from lines saying an expiry word and their own date
│   │   │   ├── test_renewals.py
│   │   │   └── README.md
│   │   ├── repo-pile/
│   │   │   ├── repo_pile.py  public repos made into a box: cloned, licence-gated, their docs the pile, indexed
│   │   │   ├── test_repo_pile.py
│   │   │   └── README.md
│   │   ├── restack/
│   │   │   ├── restack.py    your branches back on top of main, the repo's own conflicts settled
│   │   │   ├── test_restack.py
│   │   │   └── README.md
│   │   ├── risky-code/
│   │   │   ├── risky_code.py  lines of code matching a known-dangerous pattern, by file and line, as leads to read
│   │   │   ├── test_risky_code.py
│   │   │   └── README.md
│   │   ├── said/
│   │   │   ├── said.py       who said what, read by shape (a chat's stamp, a speech verb, quotation marks), dated
│   │   │   ├── test_said.py
│   │   │   └── README.md
│   │   ├── scan/
│   │   │   ├── scan.py       indexes a folder once, then asks it a list of questions, the kernel's way
│   │   │   ├── test_scan.py  holds its answers to the kernel's, every ranking vector included
│   │   │   └── README.md
│   │   ├── secrets-audit/
│   │   │   ├── secrets_audit.py passwords, keys and card numbers in plain files, by file and line
│   │   │   ├── test_secrets_audit.py
│   │   │   └── README.md
│   │   ├── serve/
│   │   │   ├── serve.py       the one markdown file a model reads: only a human-sealed scope, pooled, peaks first, by unguessable ids
│   │   │   ├── test_serve.py
│   │   │   └── README.md
│   │   ├── session-seal/
│   │   │   ├── session_seal.py one seal over a session's rows, proposed through the kernel
│   │   │   ├── test_session_seal.py
│   │   │   └── README.md
│   │   ├── shell/
│   │   │   ├── shell.py          a willow command and tab completion for bash, zsh, fish, PowerShell and cmd
│   │   │   ├── test_shell.py
│   │   │   └── README.md
│   │   ├── similar/
│   │   │   ├── similar.py    what's already on the list near a new idea
│   │   │   ├── test_similar.py
│   │   │   └── README.md
│   │   ├── slow-tests/
│   │   │   ├── slow_tests.py each test's time over several runs, the slowest named, any that got slower flagged
│   │   │   ├── test_slow_tests.py
│   │   │   └── README.md
│   │   ├── snapshot/
│   │   │   ├── snapshot.py   a page or file fetched once, with its address, time and SHA-256
│   │   │   ├── test_snapshot.py
│   │   │   └── README.md
│   │   ├── stack/
│   │   │   ├── stack.py       one document from a stack of add-on steps over a box, pooled and peaks-first
│   │   │   ├── test_stack.py
│   │   │   ├── example.md
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
│   │   ├── subtitles/
│   │   │   ├── subtitles.py  .srt and .vtt transcripts mirrored, each cue a line cited by its start
│   │   │   ├── test_subtitles.py
│   │   │   └── README.md
│   │   ├── surprise/
│   │   │   ├── surprise.py   one passage drawn by a seeded stream, replayable
│   │   │   ├── test_surprise.py
│   │   │   └── README.md
│   │   ├── symptoms/
│   │   │   ├── symptoms.py   one symptom's dated diary, turns marked only where the line says one, each cited
│   │   │   ├── test_symptoms.py
│   │   │   └── README.md
│   │   ├── tarot/
│   │   │   ├── tarot.py      a tarot spread dealt by the record's tip, replayable by anyone, meaning nothing by itself
│   │   │   ├── test_tarot.py
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
│   │   ├── tip-pin/
│   │   │   ├── tip_pin.py    where the record ends, pinned outside the box; found cut short or rewritten
│   │   │   ├── test_tip_pin.py
│   │   │   └── README.md
│   │   ├── todo/
│   │   │   ├── todo.py       things marked to do, oldest first
│   │   │   ├── test_todo.py
│   │   │   └── README.md
│   │   ├── transcript-redact/
│   │   │   ├── transcript_redact.py  a transcript's keys, home paths and emails taken out, each removal listed
│   │   │   ├── test_transcript_redact.py
│   │   │   └── README.md
│   │   ├── typos/
│   │   │   ├── typos.py      a misspelt word read as the files spell it, one edit inside, offered not asked
│   │   │   ├── test_typos.py
│   │   │   └── README.md
│   │   ├── typosquat/
│   │   │   ├── typosquat.py  dependency names a letter off a popular one, checked against a top-packages list
│   │   │   ├── test_typosquat.py
│   │   │   └── README.md
│   │   ├── vim/
│   │   │   ├── vim.py            a :Willow command: answers in the quickfix list
│   │   │   ├── test_vim.py
│   │   │   └── README.md
│   │   ├── vscode/
│   │   │   ├── vscode.py         a VS Code task: answers in the Problems panel
│   │   │   ├── test_vscode.py
│   │   │   └── README.md
│   │   ├── wayback/
│   │   │   ├── wayback.py    the Wayback Machine's copy of a page, saved and compared byte for byte
│   │   │   ├── test_wayback.py
│   │   │   └── README.md
│   │   ├── web-pages/
│   │   │   ├── web_pages.py  saved .html and .mhtml as their paragraphs, under the address they came from
│   │   │   ├── test_web_pages.py
│   │   │   └── README.md
│   │   ├── windsurf/
│   │   │   ├── windsurf.py       the mcp_config.json lines that register mcp-lite with Windsurf
│   │   │   ├── test_windsurf.py
│   │   │   └── README.md
│   │   ├── words-ar/
│   │   │   ├── words_ar.py   a question in Arabic, its common words out, then the kernel's bite
│   │   │   ├── test_words_ar.py
│   │   │   └── README.md
│   │   ├── words-cy/
│   │   │   ├── words_cy.py   a question in Welsh, its common words out, then the kernel's bite
│   │   │   ├── test_words_cy.py
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
│   │   ├── words-pl/
│   │   │   ├── words_pl.py   Polish questions without Polish's common words, then the kernel's own bite
│   │   │   ├── test_words_pl.py
│   │   │   └── README.md
│   │   ├── words-pt/
│   │   │   ├── words_pt.py   a question in Portuguese, its common words out, then the kernel's bite
│   │   │   ├── test_words_pt.py
│   │   │   └── README.md
│   │   ├── words-ru/
│   │   │   ├── words_ru.py   a question in Russian, its common words out, then the kernel's bite
│   │   │   ├── test_words_ru.py
│   │   │   └── README.md
│   │   ├── words-sv/
│   │   │   ├── words_sv.py   Swedish questions without Swedish's common words, then the kernel's own bite
│   │   │   ├── test_words_sv.py
│   │   │   └── README.md
│   │   ├── words-tr/
│   │   │   ├── words_tr.py   a question in Turkish, its common words out, then the kernel's bite
│   │   │   ├── test_words_tr.py
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
│       ├── fast-tests/
│       │   ├── fast_tests.py  the test suite across every core with pytest-xdist, in a fraction of the time
│       │   ├── requirements.txt  pytest-xdist, pinned
│       │   ├── requirements-floor.txt  pytest-xdist at its floor, also tested
│       │   ├── test_fast_tests.py
│       │   └── README.md
│       ├── latent/
│       │   ├── latent.py     ranks a scan index by meaning (TF-IDF + SVD), offline
│       │   ├── requirements.txt  numpy, pinned
│       │   ├── requirements-floor.txt  numpy at its floor, also tested
│       │   ├── test_latent.py
│       │   └── README.md
│       ├── mcp/
│       │   ├── server.py     your folder for any MCP client: ask and suggest, never approve
│       │   ├── requirements.txt  mcp, pinned
│       │   ├── requirements-floor.txt  mcp at its floor, also tested
│       │   ├── test_mcp_server.py
│       │   └── README.md
│       ├── pdf/
│       │   ├── pdf.py        text out of PDFs, a headed paragraph a page
│       │   ├── requirements.txt  pypdf, pinned
│       │   ├── requirements-floor.txt  pypdf at its floor, also tested
│       │   ├── test_pdf.py
│       │   └── README.md
│       └── star-system/
│           ├── star_system.py  a friend's star-system sim (science_bitch) run deterministically, as cited passages
│           ├── requirements.txt  numpy, pinned
│           ├── requirements-floor.txt  numpy at its floor, also tested
│           ├── test_star_system.py
│           ├── README.md
│           └── example_repo/   a minimal stand-in checkout so the tests need no network
│               └── simulations/
│                   ├── __init__.py
│                   └── star_system/
│                       ├── __init__.py
│                       ├── core.py    a plain velocity-Verlet stand-in, not the real integrator
│                       └── data.py    a tiny stand-in catalog
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
│   ├── cases.json            4,668 cases, with the answers kernel.py gives
│   ├── kernel_tables.json    Python's Unicode and HTML rules, so ports don't use their own
│   ├── compare.py            runs every port against the cases and each other's logs
│   ├── test_vectors.py       fails if the cases are stale or a port disagrees
│   └── README.md             how the ports were built and what testing them found
├── docs/
│   ├── tour.md               the first five minutes, in full: a question, a gap, her words, an approval
│   ├── how-it-works.md       what it reads, how it ranks, the key, the record, approvals
│   └── design/
│       ├── repo-index.md     proposal: the repo as one deterministic-snapshot box, indexed by a custom serve-style stack
│       └── serve.md          proposal: a sealed stack of piles served to a model, on markdown (the grove's serve, in willow)
├── demo/                     four made-up people, a real bug, a real policy change and programs taken apart, to try it on
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
│   ├── bernadette/           built blind, in her apps' raw formats, and run through the whole stack
│   │   ├── make_life.py      her mail, calendars, chats, vault, office files, Kindle and PDFs, the same bytes every run
│   │   ├── CHARACTER.md
│   │   ├── PLANTED.md        written by make_life.py --planted, from the table --check holds
│   │   ├── QUESTIONS.md
│   │   ├── STRIP.md          what each need came to, and what each layer of the stack did
│   │   ├── stack.py          her files through every reader, start, the finders, privacy, an MCP assistant, and the trust add-ons
│   │   └── test_stack.py     holds the stack to the states STRIP.md scores
│   ├── novelty.py           the reusable novelty check: have these pieces been put together before?
│   ├── test_novelty.py      a novel description reads as novel, one an existing demo holds as prior art
│   ├── redteam/             a frozen recon composition over a planted target, scanned for novelty
│   │   ├── README.md         the composition, what is planted, what is frozen, the novelty check
│   │   ├── FROZEN.json       the SHA-256 of every source, and the finding expected from each section
│   │   ├── recon.py          runs seven read-only add-ons over the target in an attacker's order
│   │   ├── test_redteam.py   holds the sources to their hashes and the pass to its planted findings
│   │   ├── intel/            the offline intel the pass needs, committed so it reads the same every run
│   │   │   ├── popular.txt    the popular-names list typosquat checks against
│   │   │   ├── osv/
│   │   │   │   ├── PyPI/
│   │   │   │   │   └── GHSA-x84v-xcm2-53pg.json  the Requests credentials-leak advisory
│   │   │   │   └── npm/
│   │   │   │       └── GHSA-35jh-r3h4-6jhm.json  the lodash command-injection advisory
│   │   │   └── registry/
│   │   │       └── npm/
│   │   │           └── minimist.json  registry metadata showing minimist long abandoned
│   │   └── target/           the planted application, read-only
│   │       ├── package-lock.json  a vulnerable lodash, a misspelled reqeusts, an abandoned minimist
│   │       ├── requirements.txt   an unpinned flask and a vulnerable requests
│   │       ├── app/
│   │       │   ├── client.js    JS sinks: exec, eval, innerHTML, Math.random, TLS off
│   │       │   ├── config.py    a hardcoded AWS key and password, debug on
│   │       │   ├── legacy.php   PHP sinks: shell_exec, unserialize, SQL concat, echo, TLS off
│   │       │   ├── server.go    Go sinks: exec.Command, InsecureSkipVerify
│   │       │   ├── settings.py  debug on, wildcard CORS, a connection string, a JWT
│   │       │   └── views.py     Python sinks: shell, pickle, SQL format, eval, verify=False
│   │       └── node_modules/
│   │           └── evil-pkg/
│   │               └── package.json  a postinstall that pipes a remote script to a shell
│   ├── php2shell/            a real bug: the PHP2Shell result, tested seven ways
│   │   ├── README.md         the claim, the threats, what is frozen, each phase's results
│   │   ├── FROZEN.json       the SHA-256 of each frozen file, and of the tools when frozen
│   │   ├── releases.json     PHP's releases and the security commits, pinned by hash
│   │   ├── make_trees.py     fetches them from php-src, and checks them without git
│   │   ├── score.py          the frozen hit rule: did a passage land on the fix?
│   │   ├── score2.py         the second hit rule: also an added run's neighbouring lines
│   │   ├── phase2.py         the null tests: random draws, null questions, wrong pairs, baselines
│   │   ├── phase1.py         the blind questions, under both rules, ranked by the kernel and BM25
│   │   ├── phase3.py         out of sample: seven other CVEs, fetched as git stores them, asked blind
│   │   ├── phase3.json       those CVEs' releases and fix commits, pinned by hash
│   │   ├── phase4.py         before the fix: the whole release, ranked three ways, recall at k
│   │   ├── phase5.py         robustness: rewording, top-k, a words list, and leakage
│   │   ├── phase6.py         reproducibility: every release, five Pythons, four kernels, a second labeller
│   │   ├── pipeline.py       the whole method in one command: index, changed-from, rank three ways, score
│   │   ├── hold.py           not frozen: the kernel's hold rule against looser ones, on phase 3's CVEs
│   │   ├── test_php2shell.py holds the frozen files to their hashes, and the tools to their word
│   │   ├── results/
│   │   │   └── phase6-labels.json  the independent labellers' yes or no, item by item
│   │   └── questions/
│   │       ├── author.txt    the first look's eight questions, labelled as the author's
│   │       ├── blind-a.txt   eight written blind, as a security engineer, from the advisories
│   │       ├── blind-b.txt   eight written blind, as a sysadmin, from one news article
│   │       ├── blind-c.txt   eight written blind, as terse keywords, from the advisories
│   │       ├── phase3.txt    eight a CVE for phase 3's seven, written blind
│   │       ├── reword.txt     the author's eight, rephrased five ways each, blind
│   │       ├── advisory-words.txt  a words list of acronyms the advisories expand
│   │       └── null.txt      fifty questions with nothing to do with the bug
│   ├── craft-assembly/       the Craft apps taken apart into pieces, rebuilt exactly, and five assembled into one
│   │   ├── README.md         the claim, the threats, what is frozen, what was seen before each freeze, results
│   │   ├── REPORT.md         the full report, written by report.py from the files here, every number counted
│   │   ├── BACKGROUND.md     the research it answers: AI agents rebuilding large programs, from search summaries
│   │   ├── FROZEN.json       the SHA-256 of each frozen file, and of the tools when frozen
│   │   ├── sources.json      the 24 sources by address, commit and git tree hash
│   │   ├── composite.json    the five apps the composite assembles, and their library's address
│   │   ├── sources.py        fetches the sources by their pins, and checks each tree without git
│   │   ├── pieces.py         takes sources apart into one store of pieces, and rebuilds them from it
│   │   ├── compose.py        assembles one Cargo workspace from the store, by seven written rules
│   │   ├── conftest.py       gives the tests tomllib on Python 3.9 and 3.10, from pip's own tomli
│   │   ├── run.py            the stages and the five pass rules, as kernel verdict rows
│   │   ├── report.py         writes REPORT.md and results/checks.md from the committed files, the same bytes every run
│   │   ├── test_craft_assembly.py holds the frozen files to their hashes, and the tools to their word
│   │   ├── test_report.py    holds the report and its checks to what their files make
│   │   └── results/
│   │       ├── run-1.json    the first run's every outcome: the store, each rebuild, each package in both
│   │       ├── run-2.json    the second run's, from freeze 2: the same, and what the rules left out
│   │       ├── run-3.json    the third run's, from freeze 3: every rule held
│   │       ├── record.jsonl  a copy of the record the verdicts are rows on, without its key
│   │       └── checks.md     what the kernel, xref and claim-check say of the report
│   └── google-privacy-2026-10-16/  a real policy change: what Google's text says against what the news said
│       ├── README.md         the claim, the threats, what is frozen, how to reproduce, the results
│       ├── FROZEN.json       the SHA-256 of each frozen file, and of the tools when frozen
│       ├── sources.json      each source fetched, with its address, time and SHA-256
│       ├── fetch.py          saves the sources into a pile once, and checks them offline
│       ├── targets.json      the frozen hit rule: the clauses a question lands on, and what supports a claim
│       ├── study.py          every phase and pass rule: the versions, the changes, nulls, blind, absence
│       ├── test_google_privacy.py holds the frozen files to their hashes, and the rules to their word
│       └── questions/
│           ├── reporters.txt   the reporting's claim, in the reporters' own words
│           ├── claims.txt      "Google scans Gmail for ads", as the reporting words it
│           ├── policy-quotes.txt  the policy as each report quotes it
│           ├── blind-reporters.txt  the reporters' lines, reworded three ways, blind
│           ├── blind-claims.txt     the claims, reworded three ways, blind
│           └── null.txt        thirty questions about the policy with nothing to do with ads
├── .github/
│   ├── workflows/
│   │   ├── ci.yml            runs adapters/stdlib/ci/ci.py a part or a cut of one a job, tests on Python 3.9 to 3.14
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
