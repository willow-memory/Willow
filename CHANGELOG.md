# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. A release turns
`Unreleased` into `vX.Y.Z · YYYY-MM-DD` ([CONTRIBUTING.md](CONTRIBUTING.md)
says how). The first was v0.1.0.

## Unreleased

### Added

- `hosts`, an add-on that holds the assistants which take an MCP server as one
  table (where each one's settings live, and the shape it wants) and prints the
  lines that register mcp-lite with any of them: `hosts.py list`, then
  `hosts.py show NAME --box DIR`. The twelve add-ons for one assistant each
  (aider, codex-cli, copilot, cursor, emacs, gemini-cli, jetbrains, opencode,
  vim, vscode, windsurf, zed) now take their `--box DIR` handling from it, and
  the seven that register mcp-lite take their row from its table too, so a
  later assistant is a row, not a script. Each prints the same bytes as
  before; a test in each holds the one `hosts` it imports against a decoy of
  the same name, which kills the `sys.path` break that was accepted for seven of
  them, so those entries are gone from the mutants add-on's accepted list. Prints only: no box
  written, no key, no network.

- `ci-cache`, an add-on that reads a folder's lockfiles and prints a cache key
  per ecosystem (pip, npm, .NET, Maven), so a CI run caches each one's
  downloads keyed on the files that pin them and skips the reinstall when the
  pins haven't changed. The key is the SHA-256 over each lockfile's path and
  the hash of its bytes, so the same pins give the same key on any machine and
  a changed pin a new one. Hidden folders and `node_modules` are not walked. It
  reads the folder and prints; writes nothing, reads no box or key, no network.
  (#51)

- `parallel`, an add-on that runs a reader over several folders at once, across
  every CPU core, into one mirror. Where a reader mirrors one folder of files
  into plain-text passages, `parallel --reader NAME --from ONE --from TWO ...
  --to MIRROR` runs it on each folder concurrently into `MIRROR/<folder name>`,
  so a big mirror of many sources builds in a fraction of the time. Each folder
  is mirrored whole by the reader, so a sub-mirror is byte-for-byte the reader's
  own output — a reader that looks across a folder (backlinks) still sees all of
  it; splitting one folder between workers would give the wrong bytes, so whole
  folders run in parallel instead. Writes only under `--to` (through the
  readers), reads no box or key, no network. (#49)

- `index-cache`, an add-on that keeps a folder's `scan` index between runs and
  rebuilds it only when the folder changed. It holds a manifest beside the
  index — each read file's path and the SHA-256 of its text — and on each run
  hashes the folder's files: when every indexed file still matches it leaves
  the index as it is (no passage re-read, ask it with `scan`); when a file was
  added, edited or removed it rebuilds through `scan` and says what moved. The
  files it hashes are exactly the ones the kernel reads into an index, so a
  dotfile or a binary changing never forces a rebuild. Writes only under
  `--to`, reads no box or key, no network. (#48)

- `star-system`, a deps add-on that adapts a friend's project —
  [science_bitch](https://github.com/AllHailSeizure/science_bitch) — into
  willow: it imports and runs that project's own `star_system` simulation
  (Newtonian N-body gravity, a fixed-step Yoshida integrator) from a `--repo`
  checkout and writes what it computes as cited markdown — each body's Kepler
  period and how well the run conserves energy, angular momentum and linear
  momentum, the same invariants the project's tests check. Fixed-step and
  deterministic, so the same inputs give the same bytes. Reads the checkout,
  writes only `--to`, no box, no key, no network. Needs `numpy` (BSD-3-Clause,
  floored at 2.1.0 for a Python-3.13 wheel); the tests run against a minimal
  stand-in checkout so the deps gate needs no network. (#47)

- `fast-tests`, a deps add-on that runs the test suite across every core with
  pytest-xdist — the same tests the serial run runs, one worker per core (or
  `--jobs N`), in a fraction of the time, with a footer naming the workers,
  cores and wall time. It only runs the suite and reports: no box, no file
  (pytest's caches are off), no network (xdist's workers talk over pipes), and
  approves nothing. Needs `pytest-xdist` (MIT); its floor is raised to `3.0.2`
  because every 2.x imports `py.log`, long gone from pytest, so a 2.x pin
  installs on today's Python but cannot run a suite. (#46)
- `stack`, an add-on that makes one document from a stack of add-on steps over
  a box: a markdown stack file names pools (`##` headings) and steps
  (`- NAME -- ARGS` lines, with `{box}` replaced by the box path), and `stack`
  runs every step and composes what each prints — a `##` section per pool, each
  step's output fenced under it, ordered tallest-first so the peaks are what a
  reader meets first. The step list is open; each step is held to its own card
  by the guard, so `stack` writes no box, reads no key and approves nothing.
  The input side of the serve layer in `docs/design/serve.md`, the heterogeneous
  counterpart to `across`. (#45)
- Three ideas added to `adapters/planned.json`: `repo-index` (this repository
  as its own deterministic box), `serve-piles` (serve grouped on all four W's,
  not where alone) and `novelty` (a new add-on's combination checked for
  whether it has been assembled before). (#45)
- `demo/craft-assembly`, a study: the storytold Craft apps, the AI-built
  clones of Photoshop, Premiere and the rest, taken apart with no model
  anywhere. Fifteen apps and six commits of their shared library go into one
  store of pieces, each file once by its SHA-256, and are rebuilt from it to
  their pinned git trees; five apps and the seven library crates they share
  are then assembled into one Cargo workspace by seven written rules, and held
  to building and testing as each app does alone. Frozen before each run, its
  pass rules kernel verdict rows. Run 3, from the third freeze, held every
  rule: all 134 packages that build alone build in it, and all 127 that pass
  their tests alone pass them in it; runs 1 and 2, which failed, are kept
  beside it. CI runs its tools on sources it makes, as `demo:craft-assembly`.
  Its full report, REPORT.md, is written by its report.py from the committed
  files alone, every number counted, and checked by the kernel's `read`,
  `xref` and `claim-check`, the same bytes every run. (#44)
- `serve`, an add-on that writes the one markdown file a model reads: only
  the passages a human sealed, grouped into pools with the peaks first, by
  opaque per-run ids, with no record hash or row number — the model never
  sees a box, and holding the file is the permission. `scope` proposes what
  to serve from the last bite (for the human to seal with their key); the
  write form serves the sealed scope and fails closed without one. It reads
  the seal through the kernel, never the key, and never seals. First cut of
  the serve layer in `docs/design/serve.md`. (#43)
- `across`, an add-on that makes one document across several boxes rather
  than one: it runs a document add-on (`digest`, `export`, `timeline` or
  `readings`) over every box a `--boxes` list or repeated `--box` names, and
  composes their parts under a heading per box, every line still cited by its
  box, file and line. It writes no box, reads no key and approves nothing. (#41)
- `typos`, an add-on that reads a misspelt word of a question as your files
  spell it, one edit inside the word (its first and last letters kept), the
  most-held spelling first, and prints the question as read for you to ask:
  it never asks for you, and writes nothing. Six letters and up, measured on
  the demo questions. Planned with rapidfuzz; one edit needs nothing
  installed. From willow-bot's one script's typo rung. (#40)
- `accents`, an add-on that reads a word typed without its accent ("zoe") as
  your files write it ("zoë"), both ways round, and with `words` prints the
  words-list lines that make the kernel read them so every time. (#40)
- `risky-code`, an add-on that finds lines of code matching a known-dangerous
  pattern — command injection, `eval`/`exec`, sql concatenation, insecure
  deserialization, broken tls, ssrf, path traversal, template injection, xss
  sinks, weak crypto, dangerous config, xxe — across Python, JavaScript, PHP,
  Java, Go and Ruby, each cited by file and line as a lead to read, not proof.
  A sibling to `secrets-audit`; offline, read-only. (#38)
- `demo/redteam`, a frozen study that composes seven read-only add-ons
  (`secrets-audit`, `advisories`, `install-scripts`, `typosquat`, `pins`,
  `outdated`, `risky-code`) into one authorized-recon pass over a committed
  planted-weakness target, with the intel it needs frozen alongside so it
  reads the same every run. (#38)
- `demo/novelty.py`, a reusable check every demo can run: it asks willow's
  own search — `similar` over the idea pile and the kernel's `rank` over
  every demo's README — whether a combination of pieces has been put
  together before. (#38)
- `repo-pile`: a list of public repositories made into a box you can ask.
  Each is cloned, kept only when its own licence file grants one an
  Apache-2.0 project can use (anything else, or none, is left out and said
  why), and its docs made the pile; the kernel makes the box, and scan
  indexes the docs and the whole source. Then ask, bite, quote, report,
  check and backup are willow's own add-ons over it, what they print
  scrubbed by privacy. It never reads the key or seals. (#37)
- `demo/bernadette`, a fourth person built blind, her files in the raw formats
  her apps would leave (.eml and .mbox, .ics and .vcf, WhatsApp and Telegram,
  an Obsidian vault, .docx, .xlsx and .odt, Kindle and .epub, PDFs), and
  `demo/bernadette/stack.py`, which takes them through every layer of willow at once: each
  reader, `start`, the look-ahead add-ons, her twenty questions, `privacy`,
  an assistant over `mcp-lite`, and, once she seals, `stale`, `export`,
  `session-seal`, `backup`, `diverge` and `verify`. CI runs it as
  `demo:stack`; STRIP.md scores it, misses included. (#34)
- `session-seal`, an add-on that bundles a session's rows, by number,
  kind and hash and never their words, and proposes the bundle through the
  kernel's own bite and propose, so it waits on the person's seal like any
  suggestion: one seal over a whole session. Ported from willow-bot's one
  script, with the kernel's seal standing in for Nestor's. (#34)
- `latent`, a deps add-on that ranks a `scan` index by meaning (TF-IDF then a
  truncated SVD), so a question reaches a passage that shares its sense without
  sharing its words; offline, it downloads no model. Needs numpy, pinned and
  floor-tested. (#35)
- `typosquat`, an add-on that reads your lockfiles and a downloaded list of
  popular package names and flags any dependency whose name is one edit off a
  popular one — an insert, delete, substitution, or a swap of two adjacent
  letters (optimal string alignment), the common typosquat shapes. Offline;
  reuses `advisories`' lockfile reader. (#35)
- `install-scripts`, an add-on that lists the `preinstall`/`install`/
  `postinstall` scripts the packages under a `node_modules` folder would run
  on install, each cited by file and line, so arbitrary install-time code is
  visible before you trust it. Offline, read-only. (#35)
- `pins`, an add-on that reads package.json and requirements.txt and names the
  dependencies declared as a version range that no lockfile pins to an exact
  version — the ones a maintainer may want to lock. Offline; reuses
  `advisories`' lockfile reader. (#35)
- `outdated`, an add-on that reads your lockfiles and a downloaded registry
  index (npm, PyPI, crates.io metadata) and says how old each locked
  dependency is, flagging the ones that are yanked, deprecated, or from a
  project two years without a release. Offline; reuses `advisories`' lockfile
  reader; `--now` makes a run repeatable. (#35)
- `advisories`, an add-on that reads your lockfiles (npm, PyPI, crates.io) and
  a downloaded OSV or GitHub advisory database, offline, and says which locked
  dependency a known advisory names, and since when -- matching a version by
  the advisory's own version list or its numeric ranges, and naming what it
  can't compare rather than guessing. (#35)
- `demo/php2shell/pipeline.py`, a runner that composes the PHP2Shell method end
  to end (kernel, BM25 and the latent ranker) in one command; a runner, not an
  add-on, and not part of CI. (#35)
- `kernel.py decline`, the person's No: proved with their key like a seal,
  it is never offered again by `out`, `browse` or `digest`, and can't be
  sealed after; `verify` names a No that doesn't prove. On Windows the
  record is now locked with `msvcrt`. Both were in LIMITS.md, and the three
  ports do the same. (#32)
- `hook-fail-closed`, `hook-fuzz`, `hook-pin` and `hook-replay`: a hook
  that crashes, hangs or prints what can't be read blocks the tool instead
  of letting it run; thirteen fixed bad inputs thrown at a hook, each one
  that breaks it named; a hook runs only as the bytes you approved, pinned on
  the record; and every hook answer a row of hashes, run again by `check`.
  (#21)
- `kernel.rank` takes `top` and `dated`, so an add-on that lists every
  match, or an index that has the dates already, no longer sets the
  kernel's globals for a call; its filter is public as `kernel.holding`.
  No answer changes: the vectors regenerate with only the kernel's hash
  different. `similar near` also counts against the entry, so a long new
  line finds a short entry it contains. (#20)
- Thirty-seven ideas on the add-on list, nothing built: hooks whose answers
  are code, never judgment (hook-fail-closed, hook-fuzz, hook-pin,
  hook-replay, hook-shell and others), the store behind willow-bot's pile
  (pile-rank, pile-serve, pile-gold, fair-merge), and the tools LLMs use
  (instruction-files, llms-txt, mcp-by-hash, schema-check, cassettes). (#19)
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
- `gaps`: where a log you keep stops. The days a folder of daily notes, a
  reading log or a diary skipped are said as gaps: a spacing more than three
  times the log's typical one. A log with too few dates is said, an undated
  file beside it is said, and a gap is "no entry written", never "nothing
  happened". (#30)
- `timeline`: one matter from your folder (a dispute, an illness, a
  tenancy), chosen by words, as a dated list of every line of the passages
  that hold them, each cited by file and line, written to one file to hand
  on. A line's own date and its file's are both shown when they differ;
  undated lines are kept, after the dated ones; nothing is merged. (#28)
- `lending`, what you lent, to whom and when, and which are still out: a
  thing in parts is out until every part is back, a loan with no return
  line is "no return written", and a line's own date and its file's are
  both shown when they differ. (#27)
- `contradictions`, two lines saying the same thing with a different date
  or amount, side by side, each cited, neither picked. Two lines are about
  the same thing when they share two words and half the shorter's; records
  of one kind (invoices numbered alike, a form's field, a list's items) and
  lines written on different days are counted and left alone. Dates are the
  kernel's own reading. (#29)
- `slow-tests`, an add-on that reads a folder of pytest's JUnit XML files, one
  per run, and names the slowest tests and files in the latest. It flags a
  test that got slower by a printed rule (more than 2x and 1 s over the
  median of its earlier passes), and says, rather than drops, a test that is
  missing from the latest run or was skipped. Runs go by file name, never by
  file time; it writes nothing. (#25)
- `restack`, your branches put back on top of main: each rebased in a
  scratch worktree, the conflicts in the files the repo makes or only adds
  to (the add-on list, CHANGELOG.md, FILES.md, `COMMANDS`, the idea list)
  settled by the repo's own rules and tools, any other one stopping that
  branch untouched, and nothing moved until `test_docs.py` passes. (#22)
- `test-shards`, an add-on that splits the test run into parts by each test's
  time in an earlier run (pytest's JUnit XML), so the CI jobs finish about
  together. It learns the suite as it is now, places a test with no past
  time at the median and says so, and prints any one part for a job to run. (#26)
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

- `kernel.py`'s common words, which never count toward holding a question,
  now hold "anything", "something", "nothing", "everything" and the
  "-one", "-body" and "-where" words: they name no topic. "did i promise
  siobhan anything" found nothing, since no file says "anything"; it now
  serves the promise. On the sixty demo questions, two answers change, both
  for the better. The vectors regenerate; the ports read the list from them. (#40)
- `privacy` withholds passwords: one typed after its label (`password: x`,
  `pw x`), the second half of a login pair (`user / x`), and, in a file named
  as a list of them, every value that looks like one (six or more
  characters, a letter and a digit). `secrets-audit` lists the same. (#40)
- The `calendar` reader says on a recurring event's first line that it
  repeats, and how (`(yearly, from this date)`), and says `(cancelled)` on a
  cancelled one, so a line quoted from it can't pass for this year's date.
  `coming-up` counts each repeat in its window (a rule's FREQ, INTERVAL,
  UNTIL and COUNT; one with BY parts isn't guessed) and a birthday every
  year. (#40)
- `demo/bernadette`'s stack asks a question again as `typos` and `accents`
  read it, and its STRIP.md says what each fix changed; it also corrects a
  finding it had wrong (question 19 missed on "anything", not an accent). (#40)

- `privacy` also withholds a national phone number written from its 0 in
  groups (`0113 555 0122`, `07700 900123`: 10 or 11 digits), and a bank
  number after its label (sort code, account number, acct, a/c, routing),
  keeping the label so the line still reads. Its card already said bank
  numbers; only IBANs were caught. Found when repo-pile was run on the demo
  lives, where 64 phone numbers and 121 bank numbers got through; on 3,165
  docs from 44 public repositories neither shape matched anything. (#37)
- CI ends sooner, in the same gates. `ci.py run` takes a gate's name,
  `--without GATE` and `--shard K/N` (cut by `test-shards`' split), so
  `tests:strip`, which ran the add-ons' tests a second time in each tests job,
  has a job of its own on each Python, and the mutants run in four shards.
  `github.py check` holds every gate to exactly one job. A pull request's
  `first` job runs what `test-impact` says its change reaches, cheapest first,
  and a failing job writes `ci-why`'s reading of its log to the run's summary.
  (#36)
- `claude-code`'s prompt hook says it couldn't read the prompt when it
  gets JSON that isn't an object, or JSON nested past Python's depth, where
  it crashed with a traceback; `hook-fuzz` found it. (#21)
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

### Fixed

- CI pins its workflow to `ubuntu-24.04`. `ubuntu-latest` rolled to Ubuntu
  26.04, for which the setup-python action has no Python 3.9 build, so the
  `tests (3.9)` and `strip (3.9)` jobs failed at setup on every pull request;
  `kernel.py` promises 3.9+, so the runner is pinned to an image that still
  carries it rather than 3.9 dropped from the matrix. (#39)
- `kernel.words` composes text (NFC) before it splits it, so an é saved as
  e and a combining accent, as macOS often saves it, holds the é a person
  types; before, it split into "cafe" and a stray mark, and the question
  found nothing. The three ports compose by tables `vectors/gen.py` reads
  out of Python, so no runtime's Unicode version decides a word, and the
  vectors hold every composed character decomposed. (#33)

### Changed

- `AGENTS.md` now cautions, in the mutants step, to run
  `adapters/stdlib/mutants/mutants.py` only after the add-on's `COMMANDS`
  line exists and on a clean tree: a mutant counts as killed when the run's
  tests exit non-zero, so an add-on not yet in `COMMANDS` (or a stray
  uncommitted add-on folder) fails the contract test and marks every mutant
  killed — a false pass CI later exposes as the real survivors. (#50)

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
