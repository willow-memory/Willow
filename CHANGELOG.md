# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. A release turns
`Unreleased` into `vX.Y.Z · YYYY-MM-DD` ([CONTRIBUTING.md](CONTRIBUTING.md)
says how). The first was v0.1.0.

## Unreleased

### Added

- `ci`'s `adapters/stdlib/ci/realdata.py run NAME` runs an add-on's COMMANDS
  line on every demo person's real folder, under the guard, failing on a
  traceback, a breach, a hang or an odd exit; create_pr.py runs it for each
  add-on a change touches, so AGENTS.md's real-data step is a command
- `ci`'s `adapters/stdlib/ci/times.py` keeps test-times.json to CI's own run:
  the tests job writes each tests:adapters gate's JUnit XML on a push to main,
  and `write --run latest` reads the last green run's
- `ci`'s `adapters/stdlib/ci/pypi_dates.py` keeps PyPI's upload dates for
  each deps floor pin and the floor rule's release in pypi-dates.json, which
  the floor test reads in place of a table typed into test_ci.py; `write`
  asks PyPI only for a pin the file lacks, and made.py runs it (#243)
- `ci`'s `adapters/stdlib/ci/made.py` makes again, or checks, every file a
  script makes: the add-on lists, BUGS.md, FILES.md, the lists kept A to Z
  and craft-assembly's report, which a change elsewhere left stale five
  times in CI. create_pr.py runs `write` as one step in place of four, so a
  generator added to its table is made in every pull request (#243)
- `ci`'s lint:py39 gate, `adapters/stdlib/ci/py39.py check`, names each use of
  what Python 3.10 and later added that ruff can't see (`write_text(newline=)`,
  `zip(strict=)`, `itertools.pairwise`, `isinstance(x, A | B)`), which failed
  CI's 3.9 run three times; ruff now also refuses an `int | None` annotation
  without `from __future__ import annotations` (FA102) (#244)
- `ci`: a demo folder with tests that no DEMO_TESTS row runs gets its own
  gate, `demo:FOLDER`, so a new demo's tests run in CI with no row written (#244)
- `ci`'s `adapters/stdlib/ci/commands.py suggest NAME` finds an add-on's
  line in test_contract.py's COMMANDS from its own usage lines, run as the
  contract test runs them, and `--write` puts it there A to Z; new.py's list
  of what's left names it (#244)
- `claude-code`'s prompt hook answers from scan's index with `--index`,
  while index-cache says the folder hasn't changed: the same passages and
  the same row on the record, in 2 s, not the 30 s the kernel takes to read
  the bot's 22,873 files at every prompt (#241)
- `ui/`'s `assemble.py remove NAME...` takes a piece out of a stack: its
  folder and its STACK.json entry, and one `remove` row on the record naming
  the files it held; not one a piece that stays imports, nor one whose files
  changed since it was put in (#240)
- `ui/` offers a reader for a kind of file the kernel can't read by the
  reader cards' `reads`, the ones reading the fewest kinds first, where it
  went by a table and words in a card's line (which offered zotero for a
  PDF) (#235)
- `ci`'s `adapters/stdlib/ci/order.py` keeps the lists people add to A to Z:
  COMMANDS, READERS, PILE_EXTRA and REPORT_COMMANDS in test_contract.py
  and ci.py's DEMO_TESTS, each entry with its comments, adapters/planned.json,
  FILES.md's folders kept A to Z, and demo/ always; `write` sorts them,
  `check` and its test hold the repo to it, and create_pr.py runs `write`.
  The tables and FILES.md's stdlib, deps and demo folders are sorted, CI's
  demo rows run A to Z, and a folder of ten or more with one pair in ten out
  of turn now counts as A to Z (#238)
- `ci`'s `adapters/stdlib/ci/new.py NAME` starts an add-on from its idea on
  adapters/planned.json: its folder, its card with the idea's entry as its
  header, a script that refuses every command line until it's built and a
  test holding that, the idea off the list, FILES.md and the add-on list
  written; it exits 42 with what's left for a person (#237)
- `ci`'s `adapters/stdlib/ci/files.py` keeps FILES.md's tree to the repo's
  files: `write` puts each new file in its folder's own order with what it
  says of itself (its docstring's first line, its title, `its card`) and
  takes out what's gone with its notes, its corners and bars kept right;
  `check` says what's out. github's create_pr.py runs `write` before it opens
  a pull request (#236)
- `reads` on every reader's card: the kinds of file it reads, by extension
  or by name (`.eml, .mbox`; `zotero.sqlite`), or `none`. `readme.py
  check` requires it of a built reader and of no other card, and
  ci/test_contract.py holds each kind to the reader's own code (#234)
- `ui/canvas.py`'s commands, the page's steps for an agent or a terminal:
  `make`, `pieces` (by role, each with why; `--role repo` the commands that
  work on willow's own repository), `needs`, `examples`, `plan` (prints the
  stack file the page would send), `look` and `propose`, which exits 42,
  waiting for your seal; there is no `seal`. Look it over shows the same
  stack file and commands, to copy (#233)
- `ui/` page: three panels, the steps on the left, the one you're on in the
  middle with its add-ons as cards to tick or drag in, and the stack on the
  right as a tree, what runs on your page apart from what's set up
  alongside; a willow look with a dark theme; undo; an example previewed in
  the tree before it's used; a piece traced in the tree on hover; Look it
  over as the last step. The steps are the cards' roles, and a piece with no
  options of its own runs on the page exactly when its role is page; what's
  first in a step is what the examples run, or the readers your folders'
  files need; it says that the page shows what says most first, so the
  order of its steps only breaks ties; "sealed" and "changed since you
  sealed it" come from the record, wherever the seal was made (#232)
- `role` on every add-on's card and every entry in adapters/planned.json:
  the part it plays in a stack (reads, words, page, suggests, ways, guards,
  makes, tools, repo), each said in adapters/README.md. `readme.py check`
  requires it, one of those, and holds `role: repo` to exactly the cards
  with `runs-in: repo` (#231)
- `bot-venv --find` lists every venv under a folder: inside willow-bot or
  out, its packages, the bot's lock for it (none, holds or drifted), and the
  services running from it, read from /proc; the steward's venv inventory
  and bot-venv are one card (#229)
- `github`'s `adapters/stdlib/github/create_pr.py` opens this branch's pull
  request by running `adapters/stdlib/github/create_pr.md`, a stack of the repo's own add-ons (restack, readme,
  bugs.py, lint, test-impact, against), then pushing, opening it,
  writing its number into its changelog entry and checking that; what a
  step makes is committed as tidy, and anything that needs a person stops
  it with 42, saying what. `test-impact run --narrow` leaves a change that
  reaches every gate to CI, and `test-impact` runs a group its plan names
  (`tests:strip`) as the gates ci.py runs for it, where it said "no such
  gate" and the strip test never ran in CI's first job (#230)
- `assemble.py add` puts a deps add-on (kart, forge, pdf) in a stack's
  adapters/deps/ when the --python named already has each package its floor
  names, at that version or newer; nothing is installed, and one missing or
  too old is refused, saying which (#225)
- `ci.py needs` says which gates this machine can't run, by what each needs,
  without running any, in under a second; AGENTS.md now asks it before a
  change, in place of running every gate as a baseline, and after a change,
  only the gates it can move (#224)
- `assemble.py kernel` puts this willow's kernel.py and vectors in a stack
  in place of the ones it was made with, only if the stack's record verifies
  under the new kernel and, with --python, every add-on's tests pass on it;
  else the old ones are back and nothing is written (#222)
- `sort-ask`, the rung after `sort`: a model on this machine, at a loopback
  address only, is asked which of your categories a file `sort` didn't place
  belongs in, given the passages the kernel served from it; only an answer
  naming one of your categories and citing a served passage is handed in, as
  a suggestion for your seal (#219)
- `kart`, a job someone sent you, run over your own folder in Kartikeya's
  sandbox: `take` puts a job that came in a share package at the kernel's
  door as a proposal of yours, and `run` runs only a job you sealed, under
  willow's own policy for Kartikeya's bubblewrap (your folder read-only,
  one scratch folder, no network, no environment, the box and key out of
  reach). A `ran` row records how it ended and its output's SHA-256, never
  the output, and the output waits on your seal before `share` can send it
  back. A job asking for the network is refused before it is even taken.
  `--shape numbers`, set by whoever runs a job, lets only whole numbers be
  proposed, so only aggregates leave; `gather` adds the numbers people sent
  back, one job, one result a chain, and proposes the totals.
  Its tests probe the sandbox from inside, through `run` itself.
  `demo/johnson/jobs.py` sends one job from Ines to Walt and Aurelie and
  brings back their sealed answers; CI's deps job installs bubblewrap and
  lets the runner make the user namespace it needs. (#216)
- `share`, sealed answers sent from one person's willow to another's:
  `id` makes an Ed25519 identity that is not the seal key, `send` packs
  answers you sealed for one person's public key, signed, with their cites'
  places and fingerprints but never your files' text, and `receive` checks
  every layer and writes what came in, good or not, on the receiver's
  chain. `forward` passes a package on inside a signed layer of your own
  that nobody can change, and `--replaces` sends a correction that each
  hop's `receive` routes to whoever got the old one. `witness` holds a
  record to the packages other people kept: each layer is signed over where
  its sender's record stood, so a record rewritten and re-hashed, which
  `verify` can't see, or cut short, is caught by anyone holding a package
  sent after the change. Three rules come from willow-gate: each layer
  says what it proves inside its signature (authenticity, never
  completeness); `rotate` changes a key loudly, signed by the old key and
  the new and carried in every later package, while any other key is
  refused; and `receive` names a key's rung (rookie, steady, veteran)
  earned from its packages that held on your own chain. Its keys are
  willow-gate's: `ed25519.pem` and `from_pem` carry an identity to and from
  PEM, and a message willow-gate's `message_integrity` signed, and one
  signed here that its `MessageVerifier` passed, are frozen in the tests.
  Ed25519 is written in the standard library
  (`adapters/stdlib/share/ed25519.py`), held to RFC 8032's vectors and to
  ones from an audited library. Its card promises `writes: record, to`
  where the idea said `to`: the `sent` and `received` rows are the point.
  The `share` idea comes off the list. `demo/johnson` passes one report
  between five people's willows, through a forged copy, a correction, a key
  rotated on the way, a rewritten record that four other people's
  packages catch, and three stacks sent to three people, two taken on under
  their own seal and run over their own folders and one declined, and CI
  runs it as `demo:share`. (#216)
- `sort`: your files sorted into your own categories by the phrases you gave
  each, in a file of your own (`name: phrase, phrase`); a tie is listed for
  you to choose and a file no phrase reaches is unsorted, never guessed. It
  prints a report, 42 when a file waits on you. (#206)
- `demo/five-repos`, five repositories through the stacks: the seven
  stacks a session built and rebuilt with each prompt over a folder of
  five repositories (this one among them), the 24-line words list that
  read one repo's words as the others', thirteen reports of what each
  stack found and got wrong, and two records copied without their keys,
  one holding ten suggestions that wait on a seal. Its test holds the
  stacks to add-ons that exist, the words list to the kernel's parser and
  the records' chains with nothing sealed; CI runs it as `demo:five-repos`.
  The session proposed and never sealed. (#211)
- `stack`: a ninth example, `adapters/stdlib/stack/examples/export.md`, a
  box handed to someone else: what the record says of itself, the hashes
  a stranger can check (the Merkle root, a pin, fixity), the envelopes the
  world reads (PROV, in-toto, an RO-Crate) and a backup that checks
  itself, each written under a folder beside the box. (#211)
- `stack`: an eighth example stack, `adapters/stdlib/stack/examples/repos.md`,
  for a folder of repositories cloned side by side: the audits over all of
  them at once (todo, risky-code, xref, pins, install-scripts, secrets-audit,
  pii-audit, a11y-check), one question each repo answers in turn through
  fair-merge, and what they say twice and whom they name. Made by running
  Willow's stacks over five repositories, this one among them. (#211)
- `git-history`: `mirror --from FOLDER --to MIRROR --messages` writes each
  commit without its diff, the day, subject and body only. A diff carries
  other people's dates and the kernel dates a line by the nearest date
  above it, so a commit pile with diffs was dated by what the diffs said:
  on this repository's own history, "privacy" was first mentioned in 1958,
  a demo character's birthday inside a diff. Messages alone are dated by
  the commit. (#211)
- `forge`, a deps add-on: a sentence in, the add-ons it names or means
  out, as a report in the one shape. A word that reaches several add-ons
  ("email": mail, apple-mail) is a fork with the cards as options, for the
  Forge's checkpoint to put to the person once and remember; `--plan`
  prints the same as a plan the Forge's `plan_shape` validates and its
  `build_loop` resolves. It recommends nothing and scores nothing. (#200)
  `propose` settles the forks and hands each, and the stack, to the kernel's
  door as a report of what waits, under the person's seal; `suggest` reads a
  sealed decision back through the kernel and asks nothing twice, keyed by
  decision type as the Forge asks for it, so a fork the Forge's build loop
  settled is a step here and one settled here is the Forge's auto band. Its
  promise is `writes: record`: every write is the kernel's. Needs forge-play
  0.10, whose card box reads these cards as rows for its keyword scan. (#201)
  `build` runs the stack the person sealed for a sentence, and nothing
  else: each step's add-on into a folder through `ui/assemble.py`, the
  stack file beside it, the stack add-on run over the box and its page
  kept, as a report of what was built, what ran and what was left out;
  the promise grows to `writes: record, to`. (#202)
  A step's line is the add-on's own good command line, read from the ci
  add-on's contract (`{box}` kept, the folder filled in, `{tmp}` a folder
  `build` makes, the pinned `--now` taken off), so a reader mirrors and an
  add-on with verbs runs its verb; without the contract every step takes
  `--box {box}` and the plan says so. (#203)
- `ci-memo`: a pull request runs only the mutants gates a change can reach,
  standing the rest on the record of main's last green run, and a push to
  main runs them all, so the merge's receipt stays whole. Four shards of 5
  to 19 minutes were a pull request's slowest job, though a change usually
  reaches one add-on's gate. The new `mutants-reach` job pins main's records
  against main's own tree, plans `mutants` (`plan` now takes part or gate
  names, and `pin` a folder of just `<box>/record.jsonl`, as an artifact is) and
  runs what needs it; with no green run to stand on it runs the whole part
  and says why in the summary. `github.py check` holds that a job skipped on
  pull requests has one that plans its gates. (#208)
- `against`, a pull request held to the other open ones: `against.py check
  --base REF HEAD OTHER ...` fails (exit 2) on a name both add, whether an
  add-on folder, an idea on `adapters/planned.json`, a `COMMANDS` key or a path
  in FILES.md. A file both change that cannot be merged is only said:
  `collides:` naming the pull request to merge first, or `settled:` for the
  files restack settles by rule. It also suggests the ideas of the other
  pull requests near yours. CI's `against` job runs it on every pull request
  against the others that are open, and CONTRIBUTING.md's rule is now to
  stack only when it names a reason. (#208)
- The report contract (`adapters/stdlib/ci/README.md`): an add-on that
  reports what it found prints one shape, `NAME: STATE, SAID` then rows of
  where and what by group, and the same as JSON with `--json`; `empty` exits
  0, so 42 never means found nothing. A card says `output: report`; `stack`
  asks such a step for its JSON and weighs it by its rows;
  `adapters/stdlib/ci/test_contract.py` holds each to it; `adapters/stdlib/ci/reports.py` surveys, scaffolds
  and checks add-ons in batches. pii-audit, risky-code, todo, advisories,
  install-scripts, package-contents, stale, again, session-seal check,
  predict score, forecasts score and digest print reports; hook-start hands
  the assistant digest's. (#197)
- `ports/rust`, a fifth port of `kernel.py`: Rust, the standard library
  only and no crates, following the Go port function for function. What
  Rust's library lacks is written in and held by the vectors: SHA-256 and
  HMAC (RFC 4231's cases), JSON as Python reads and writes it, base64, and a
  whole number of any size so the rank's scores compare exactly.
  `vectors/compare.py --port rust` holds it to all 4,668 vectors and the
  whole session, both ways, with zero unexplained differences; CI's ports
  job runs it as `ports:rust`. (#191)
- `ports/go`, a fourth port of `kernel.py`: Go 1.15+, the standard library
  only, following the Java port function for function with the scanners
  every port shares, Python's decisions read from `vectors/kernel_tables.json`,
  and `kernel.py`'s own `flock` on the record. `vectors/compare.py --port go`
  holds it to all 4,668 vectors and the whole session, both ways, with zero
  unexplained differences, and CI's ports job runs it as `ports:go`. The
  `go` idea comes off the list. (#191)
- `in-process`, suggestions from a GGUF model loaded inside the add-on
  itself through llama-cpp-python: `in_process.py ask --box DIR --model
  FILE.gguf "question"` is openai-compatible's bite-then-propose with no
  server and no port, the claim naming the file by name and SHA-256. Its
  tests run llama.cpp on a model of a few kilobytes that
  `adapters/deps/in-process/conftest.py` writes from seeded weights, so
  nothing is downloaded. Floor llama-cpp-python 0.2.29: a chat takes a
  seed from 0.2.15, and before 0.2.29 every quiet load opens /dev/null to
  write, which the guard holds. (#190)
- `dotfiles`, a reader that mirrors a dotfiles repository (bashrc, zshrc,
  gitconfig, tmux.conf, init.vim, .ini, .conf, .toml and their kind) as its
  settings: `dotfiles.py mirror --from FOLDER --to MIRROR`. Each setting is
  on its own line, in the file's own words (`EDITOR=nvim`, `core.editor =
  nvim`), every other line blank, so "where did I set my editor" lands on
  it. A value named or shaped like a secret is written `[withheld]`. Hidden
  files are skipped, so point it at the repository, not your home folder. (#189)
- `webarchive`, pages Safari saved as .webarchive as their readable text:
  `webarchive.py mirror --from FOLDER --to MIRROR` writes what web-pages
  writes for the same page (the address it came from, its title, its
  paragraphs), then each frame's text under the frame's own address.
  It reads the archive's charset, then the page's, then UTF-8; a file that
  isn't a web archive, or a saved PDF or picture, is skipped and counted. (#188)
- `apple-mail`: Apple Mail's .emlx and .partial.emlx messages as plain text,
  each read with mail's own code so it gives the same text as the same message
  saved as an .eml (sender, recipients, date and subject, then the body and the
  attachments' names). A message with no Date header takes Apple Mail's date
  received, in UTC; the run says how many, the text adds no word for it. A file whose byte count is malformed or which
  is shorter than it is skipped and counted. (#187)
- `shortcuts`: the link files dragged out of a browser onto a desktop or
  into a folder (Windows `.url`, macOS `.webloc`, Linux `.desktop`), each as
  the title its name gives and the address it holds; a Linux launcher as its
  name and the command it runs. A Windows `.lnk` is left alone. (#186)
- `opml`: OPML files from feed readers, podcast apps and outliners. A feed
  list is a line per feed, its title and addresses, each folder a passage
  headed by its name, and an Overcast export's episodes under their podcast;
  an outline is its items indented by depth with their notes, each top-level
  item with children a passage, cut at its children when it is too long for
  one. Only the file's own words are written. A file that declares a DTD or
  an entity is skipped and counted, never parsed, so an entity bomb is never
  expanded. (#185)
- `ris`: RIS citation exports (.ris, the export of EndNote, Zotero, Mendeley,
  Web of Science and Scopus), each reference as a passage that opens with its
  citation (authors, year, title, journal, volume, issue and pages), then its
  type code, doi, keywords, abstract and notes, with no label repeated in
  every passage. The year comes only from the date tags; a broken reference
  is skipped and counted in the file's closing passage. A .enw file is read as RIS or as EndNote's own tagged lines,
  by what it holds. (#184)
- `zotero`: your Zotero library from a copy of zotero.sqlite, each item, note
  and PDF annotation as a passage that begins with its citation (authors in
  Zotero's order, the year from the date field alone, the title, where it
  appeared). An annotation is quoted with its page and your comment; an ink
  or image one with no text is counted, not quoted. Only the library's own
  words and numbers are written, no labels or type words, so a question
  about something absent isn't answered by a word in every passage. The
  trash and RSS feeds are left out, and the file is opened read-only and
  immutable, so no journal appears beside it. (#183)
- `takeout`: Google Takeout's My Activity and YouTube watch and search
  history, JSON or HTML: each activity as its own dated line, in UTC as the
  file gives it, Google's title with a watch's channel and nothing added to
  every line; an HTML date in another language kept as written, never
  guessed; other JSON and HTML skipped and counted. (#181)
- `strava`, Strava's export and GPX files as dated lines: `python
  adapters/stdlib/strava/strava.py mirror --from FOLDER --to MIRROR` writes
  each run, ride and walk in activities.csv, a .gpx or a .tcx (gzipped or
  not) as a line with its start, name, distance and time, in the zone the
  file gives, never a guessed one, and no word of its own beside them.
  .fit files are skipped and counted. (#180)
- `pocket`: Pocket's export, now that Pocket is gone: the older
  ril_export.html and the 2025 CSVs, loose or read from the zip without
  unpacking it, as one dated line per saved article, oldest first, with its
  title, address, tags and whether it was read; other files left alone. (#179)
- `bookmarks`: browser bookmarks and history: the bookmark HTML export every
  browser writes, a Firefox backup (.json or .jsonlz4), Chrome's
  `Bookmarks` file, and copies of Firefox's `places.sqlite` and Chrome's
  `History`, opened read-only. Each bookmark is a passage with its day,
  title, address, folder, tags and description; each page visited is one
  passage with its last visit, visit count and the days it was visited. No
  label or other word stands on every passage, so a question about something
  the folder lacks isn't answered by one. (#178)
- `asciidoc`: AsciiDoc documents (.adoc, .asciidoc, and .asc when it isn't
  PGP armor) as the text they show, line for line, so a passage is cited by
  the file's own line. Titles, the document's own attributes as `name: value`,
  admonitions as `note:`, links with an outside address after their text,
  footnotes, lists and descriptions are kept; comments, delimiters, attribute
  lines and includes are blank; listing and source blocks stay as written. A
  table's line is its cells, the header row kept once rather than written onto
  every row, so no added word sits in every passage. (#177)
- `rst`: reStructuredText files as plain prose, line for line, Python
  standard library only. Titles keep their text and lose their adornment
  rows; admonitions read "note:" or "warning:"; code and literal blocks are
  kept as written; links, roles, substitutions, footnotes and fields read as
  their text; a table's rows are their cells. Nothing that would repeat on
  every passage is added: no title path, no header beside each value. (#176)
- `org`: Emacs Org-mode files as plain lines, line for line: the mirror has
  the source's lines, so a passage is cited by the .org file's own line.
  Org's markup comes off (stars, drawer and block lines, a timestamp's
  brackets and day name, link brackets, emphasis where Org reads it), a
  heading with only headings under it is said once on the headline below so
  each outline entry is its own passage, and a table's header begins the
  passage of its rows. It adds no word of its own: TODO, SCHEDULED, CLOCK and a
  property's name stay as written, and a test asks that no word but a date's
  digits is in most passages of a file. (#175)
- `json-paths`: any JSON or JSON Lines file as plain lines, one passage per
  record: each value beside its key, numbers digit for digit, each element
  of the first array too big for one passage (and each JSON Lines line) its
  own passage. A key in most of a file's records is left out, so a question
  pairing it with a word the file doesn't hold finds nothing. Bad files and
  bad lines are skipped and counted; a mirror over 1 MB is cut into parts. (#174)
- `text`: every .txt and .text file as UTF-8 the kernel reads whole, line
  for line. A Windows "Unicode" file (UTF-16 with its mark), UTF-32, and
  UTF-16 with no mark when every other byte is NUL are read; an old code page
  only when named with `--encoding`, never guessed. CR and CRLF become LF, a
  line over 500 characters (which the kernel cut short) is broken at spaces,
  and a file over 1 MB (which it dropped) is cut into parts; a hidden
  `.lines` map says where those lines go, so nothing is written into the text. (#173)
- `csv-rows`: CSV and TSV tables as one passage per row, numbered by the
  row's line in the file, with the header row kept once as the first
  passage, so a question about one row finds that row and not a run of 500
  characters. No word is written in every row, not even a header, so a
  question about something absent is answered by no row. The delimiter
  (comma, tab, semicolon or pipe) is chosen by one fixed rule; a first line
  holding a number is data, not a header; a wide row is cut at a cell so
  nothing is lost. A file not in UTF-8, with no data row or malformed is
  skipped and counted. (#172)
- `markdown`: any Markdown file as the text it shows, line for line, so a
  passage in the mirror is on the .md file's own line, and no word the file
  doesn't hold. Front matter as its values; a table's header once, at the
  head of the passage with its rows, and each row as its cells; links as their text with an outside address, images as
  their alt text, wikilinks as the text they show; emphasis, HTML, comments,
  escapes and footnote markers off; fenced code as written. (#171)
- `quantized`, the smallest local model that still gets your own questions
  right: `quantized.py --box DIR --questions FILE` has each model the local
  server offers (or each `--model`) sit model-exam's exam of your sealed
  answers, sorts them by the size Ollama's own list gives, and names the
  smallest that passes every marked question. Writes nothing. Built in
  stdlib, like local-model. (#168)
- `night-batch`, waiting questions asked of a local model in one run,
  stopped the moment you're back: `night_batch.py run --box DIR --questions
  FILE [--until TS]` asks each question as local-model does (bite, the
  first local server, a suggestion held for your seal), skips those sealed
  or already waiting, and stops before the next question once a row appears
  that the run didn't write (you bit, sealed or declined) or it is past
  `--until`. Built in stdlib, like local-model. (#167)
- `translate`, an answer you sealed translated by a model on this machine:
  `translate.py --box DIR --into LANGUAGE "question"` finds the answer you
  sealed for the question, has the first local server translate it keeping
  each `[n]`, and proposes it as the answer to "question in LANGUAGE" (never
  the original's question) with the original kept beside it, held for your
  seal. A translation whose citations differ from the original's is
  proposed to no one. Built in stdlib, like local-model. (#166)
- `local-model`, suggestions from a model on this machine only:
  `local_model.py servers` asks each local runtime's model list on its
  usual port (Ollama, LM Studio, llama.cpp, vLLM, KoboldCpp, Jan, GPT4All)
  and says what runs and what it offers; `ask --box DIR "question"` is
  openai-compatible's bite-then-propose, with the first running server and
  its first model when none is named, and a URL off this machine refused
  before anything is sent. Built in stdlib: the server is a program you
  run, reached over HTTP, not a package it imports. (#165)
- `model-drift`, frozen questions asked again of a model, flagging answers
  that change while its name and card stay the same: `model_drift.py freeze
  ... > frozen.json` prints the model's name, its card's SHA-256 and each
  answer with the passages served (writing nothing), and `again --frozen
  frozen.json` asks the same model now, flagging a changed answer as drift
  only when the passages, the name and the card all held still. (#164)
- `model-exam`, any model scored against the answers you sealed:
  `model_exam.py --box DIR --url URL --model NAME --questions FILE` asks
  each question you sealed an answer for (the kernel's `sealed` and
  `standing`), once, with openai-compatible's chat over what the kernel's
  `rank` serves now (no bite on the record), and passes a reply that cites a
  passage your answer cites and holds half the content words of the shorter
  of the two. Questions with no sealed answer are said and never asked.
  (#163)
- `same-way`, a local model asked each question several times and how
  often it flips: `same_way.py --box DIR --url URL --model NAME --questions
  FILE [--times N]` ranks each question against your folder as a bite would
  (nothing goes on the record), sends the passages served N times (three
  unless said) with openai-compatible's chat at temperature 0 and a fixed
  seed, and counts a change in the words or in what is cited as a flip. The
  URL must be on this machine; the idea's `this-machine` is promised as
  `loopback`. (#162)
- `model-card`, a card naming the model behind an assistant, its hash on
  the record: `model_card.py add --box DIR --from CARD` appends the SHA-256
  of a `willow-model` card (weights-card's header, with `runs`, `licence`
  and `limits` added by hand) through the kernel, with the model's name, its
  weights' hash or `model version`, and where it runs, never the card's
  text; `check` holds a card file to its row (`same`, `changed`, `never
  added`) and `list` says each name's latest. No assistant names its card in
  a suggestion yet; sent-log's card now says so. (#161)
- `model-fit`, whether this machine can run a local model before you
  download one: `model_fit.py check [--model FILE] [--measure]` reads
  memory, the CPU, each GPU (its own memory from the driver or
  `nvidia-smi`) and NPU from Linux's /proc and /sys, or macOS's
  `sysctl` with Apple silicon's GPU share, and says where a model of a
  weights file's or a weights-card's size fits (its weights and a fifth),
  or the most each place holds. `--measure` times a memory copy for a guess
  at tokens a second on the CPU. (#160)
- `model-shelf`, every model already on this machine before you download
  another: `model_shelf.py list [--home DIR]
  [--hash]` reads Ollama's manifests,
  LM Studio's, Jan's and GPT4All's folders (Linux, macOS and Windows places)
  and the Hugging Face cache (`OLLAMA_MODELS`, `HF_HUB_CACHE` and `HF_HOME`
  respected), one line per model with its runtime, name, size, quantization
  (by weights-card's header reader) and SHA-256: Ollama's and the cache's
  own content names, others only with `--hash`. The same weights under two
  names are said, and a runtime not on this machine says where it looked.
  (#159)
- `weights-pin`, a weights file held to the hash on its model card before
  it runs: `weights_pin.py --card CARD --from FILE` reads the `sha256` and
  `bytes` of a `willow-model` header (as weights-card writes one), compares
  the size first and then the whole file's SHA-256, and says `same` (0) or
  `differs` with both hashes and sizes (42), so `weights_pin.py ... &&
  llama-server ...` never runs a file that differs. The hash decides, never
  the file's name. It reads the card with weights-card's `header`. (#158)
- `weights-card`, a model card filled in from the weights file's own
  header: `weights_card.py --from FILE --to CARD` reads a GGUF (v2, v3) or
  safetensors header for the architecture, name, quantization (llama.cpp's
  name for `general.file_type`, or safetensors' types by parameters),
  context length, licence and parameter count, adds the whole file's SHA-256
  and size, and writes `not in the header` for what the file doesn't say.
  Only the file's name goes on the card, and `header()` reads one back for
  the add-ons that read cards. Checked against llama.cpp's own `gguf` reader
  on two real GGUF files. (#157)
- `ui/`, willow's own UI (v1): `python ui/canvas.py` opens a page on this
  machine that goes the way a person does. Choose your folders; see what the
  kernel alone makes of them, as counts, never a file's words or name; start
  from an example or pick add-ons, each coming with what its card uses;
  save a pick as a batch; look it over, seal it, put it together and start
  it. `ui/assemble.py` makes the stack from this willow, outside the
  repository. CI runs its tests as `tests:ui`. (#156)
- `warc`, web archives read without unpacking: each page a .warc, .warc.gz
  or .wacz captured (Heritrix, wget, the Internet Archive, Webrecorder) as a
  passage under its capture time, address and title, then its paragraphs.
  Records are read by their length; chunked, gzipped and deflated bodies are
  read, and revisits, requests, redirects, images, scripts and Brotli bodies
  are passed over and counted per file. (#182)
- Cards say what an add-on leans on: `uses` (the add-ons it needs beside it,
  to run or to be tested), `looks-for` (the ones it uses when they're there,
  saying so when they aren't) and `runs-in: repo` (a tool for willow's own
  repository). readme.py checks them and ADDONS.md says "Uses …"; 86 cards
  declare. `adapters/stdlib/ci/test_contract.py` fails code that reaches an
  add-on its card doesn't name, however it's spelled, and a new gate,
  `tests:alone` (`adapters/stdlib/ci/alone.py`), runs each add-on's tests in a
  copy holding only the kernel, the add-on and what it uses: 268 of 268 hold.
  (#155)
- `demo:teodora-words`: Teodora's whole blind folder against the starter
  words list, moved from starter-words' own tests to the demo. (#155)
- `game-master`, a tabletop story played beat by beat with its rolls and
  rulings as rows on the record: `game_master.py --box DIR act Grit --world
  W.json` rolls dice's 2d6 plus the character's stat and reads it strong, weak
  or miss; a decision beat is handed in through the kernel's `propose` with
  `ask` and moves only once you have run `kernel.py seal` (or `decline`) and
  `settle` has read your proof back. `check` throws every roll again and
  finds a ruling no seal of yours stands behind. One world format, action and
  decision beats only; the idea's writes and network promises are unchanged. (#153)
- `oakenscroll`: Oakenscroll's Office calibration ledger (what you believed,
  how hard, and how it resolved) as dated passages: each claim with its
  revisions, grade and note, and where it stands now. Reads every office.db
  under a folder, read-only and immutable; scores nothing (see `forecasts`). (#152)
- `flashcards`, your sealed approvals as flashcards: `flashcards.py --box DIR due`
  lists what to study, `review ID good` writes your grade as a record row and
  says when the card is next due. The schedule is FSRS-5 (MIT, written from
  its published formulas, default parameters) replayed from the grades, so a
  fixed `--now` reproduces it; `check` holds every row to the replay. (#151)
- `thesis`, a document's claims against your sources:
  `thesis.py --box DIR FILE` puts each sentence to claim-check and prints it
  held (a passage holds every part) or short (the nearest passage, what it
  lacks), then lists the short ones with the parts no file has. It finds where
  to read and never judges. Writes nothing; the standard library only. (#150)
- `sent-log`, which passages were handed to which model, and where to, read
  from the record: `sent_log.py --box DIR`. The record holds no model identity
  (a proposal row is the kernel's, and `model-card` is not built), so it reads
  the model and endpoint from a proposal's claim, only from a proposal file
  that is the bytes proposed, and says what it cannot see: a person's own
  suggestion looks the same, and an ask that cited nothing or failed leaves a
  bite with no proposal. Reads only. (#149)
- `folder-card`, a card for your folder itself: `folder_card.py --box DIR
  --to card.md --notes me.txt` writes each file's size, first and last date
  and fiction label, the files it could not read, and the gaps the `gaps`
  rule finds, each marked told or untold by the gaps you named in your notes,
  and each gap you named marked as shown or contradicted by the files. Your
  notes go in word for word. Written once, never over a file. (#148)
- `capture`, a note written into your folder in one line:
  `capture.py --to DIR --type idea --tags garden,veg "the note"` writes one
  file holding one paragraph, the note then its `type:` and `tags:` lines, so
  `bite` finds it by any of them. A missing folder or a box is refused, not
  made or written, a note too long for one passage is refused, and the file is
  created exclusively, so two captures never overwrite each other. Its card
  keeps the promise `writes: to`. (#147)
- `catgrid`, a cat in every row, column and colour region, played on the
  record: `catgrid.py --box DIR play --moves A1,B3` builds a 4 to 8 square
  board with exactly one answer from the bot's seeded stream (seeded by the
  record's tip unless you say), plays your moves against three hearts, and
  writes one row; `check` builds every board and plays every game again.
  It draws from sha256-stream rather than the source app's xorshift, and
  leaves out its hints, trivia, daily boards, duels and multi-cat boards. (#146)
- `decisions`, what you decided and what you ruled out, each with its reason:
  `decisions.py chose --box DIR --question Q --answer A --reason R` (with
  `--replaces ROW` to keep the lineage) and `no ... --never` or
  `--reopen-when CONDITION`, so a never is told from a not-yet when it is
  written; `reopen` records that a condition came true, and `ask QUESTION`
  reads back the answer that stands, what it replaced, every no and each
  condition to check. Rows stand unattested; the SAFE App Store
  `aristarchus`'s signing is not here, only your seal approves. (#145)
- `nightstand`, set heavy things down and pick up one bite: `down`, `pick`,
  `back`, `done` and `archive` as `nightstand` rows through the kernel, state
  only ever replayed from them. At most one thing is in hand (a pick-up names
  the thing it puts down, in the same row), every pick-up needs a bite, and
  there is no delete; `one` offers the lightest, oldest thing and `check`
  names the first row that breaks a rule. (#144)
- `weakest-link`, each approved answer worth its weakest cited input:
  `weakest_link.py --box DIR`. A passage marks itself `provenance: measured`,
  `fitted` or `assumed`; an approval is worth the min() of what it cites,
  never an average, and the weakest inputs are flagged to fix first. A cited
  passage that marks nothing is `unmarked`, and so is any answer citing one or
  a passage gone from the folder: recorded as its own value, never read as
  assumed. An approval citing no passage (session-seal's summaries) is
  `cites-nothing`, counted and not escalated. Rebuilt from the SAFE App
  Store's field-acoustics and kitchen-pudding; reads only. (#143)
- Six ideas added to `adapters/planned.json` from an audit of the SAFE App
  Store against willow, each checked with `similar near` first:
  `weakest-link` (inputs marked measured, fitted or assumed, the result worth
  its weakest), `nightstand` (one thing in hand, nothing deleted),
  `decisions` (a recorded no with its reason and what would reopen it),
  `catgrid` (a seeded logic grid with a unique answer; its rng is already the
  one script's xorshift), `fight5e` (combat from stat blocks on dice5e's
  rolls; the stat blocks' licence to be checked before it is built) and
  `capture` (a one-line note written into your folder). (#142)
- `dice5e`, full tabletop dice notation on the record:
  `dice5e.py --box DIR roll 4d6kh3` (or `adv+5`, `dis`, `2d20kl1`), seeded
  and drawn as dice is, every die written, kept or not; `check` throws every
  roll again. The standard library only, where the idea had named the MIT
  `dice` library. (#141)
- `rules`, a game's or a house's rules sealed section by section:
  `rules.py propose --box DIR FILE` proposes each heading's section as the
  answer to "rule NAME", and once you seal it the kernel itself answers that
  bite word for word (`rules.py ask NAME`). `list` says which are sealed,
  waiting, or changed in your folder since you sealed them. (#141)
- `market-calls`, market calls kept as forecasts' wagers, losers and all:
  `market_calls.py call --box DIR --p 0.7 SPY up 2026-11-06` (or
  `above:600`), one call per question and before 13:00 UTC on the close
  date; `close SYMBOL DATE CLOSE PREV_CLOSE` records the closes you read and
  proposes each call's outcome for your seal; `score` lists every call,
  right, wrong or open, with the Brier score. Offline: nothing fetches a
  price. (#141)
- `forecasts`, a prediction written down before the outcome:
  `forecasts.py wager --box DIR --p 0.8 CLAIM` keeps the p and the claim's
  hash, never its words; `settle ROW yes|no` proposes what happened through
  the kernel's door, and it counts only once you seal it; `score` gives the
  Brier and log scores and how often each band of confidence was right.
  The scores are willow-bot's one script's calibration module, unchanged. (#141)
- `jeles`, Jeles' nuggets as passages and your approved answers as Jeles
  nuggets: `jeles.py mirror --from FOLDER --to MIRROR` reads Jeles seed files
  and corpus stores (never a signature, a deleted record or a logged gap), and
  `jeles.py export --box DIR --questions FILE --to OUT.json` writes approvals
  as a Jeles seed file, each paired with a question only when its words hash
  to the key the approval was sealed under. Jeles installs them at its
  asserted rung: a willow seal is not a Nestor seal. (#139)
- `predict`, what a question will come to, written down before it is
  asked: `predict.py ask --box DIR QUESTION`. It counts what the box's
  earlier bites came to (sealed, served or empty), writes the likeliest as a
  `predict` row, then bites and writes a `graded` row; `predict.py score`
  says how often each answer held. A tie goes to `empty`. Ported back from
  willow-bot's one script, whose rebuild on willow's pieces now leans on
  serve, tip-pin and pile-rungs. (#138)
- `texts`, phone text messages and calls as one dated line per message:
  `texts.py mirror --from FOLDER --to MIRROR [--me NAME] [--tz ZONE]`.
  Reads an Android backup from SMS Backup & Restore (its messages, picture
  messages' words, and its call log) and an iPhone's messages database,
  known by what it holds under its hashed backup name and opened read-only.
  One section per conversation, a paragraph a day, so each passage the
  kernel serves is one day with one person. Built from a script written for
  a real folder of texts, with its names and time zone made options. (#137)
- `month-first`, for a folder you know writes dates month first:
  `month_first.py mirror --from FOLDER --to MIRROR` writes each text file
  with every 11/03/2026, 11/03/26 and Nov. 3rd, 2026 followed by its ISO
  form, so the kernel, which never guesses an order, and timeline, gaps and
  coming-up can place it. Not-dates (13/03/2026, Feb 30) and marked dates
  are left as they are, and so are the numbered dates of a file whose own
  dates say day first: 68 of teodora's English files. (#137)
- `invoices`, the invoices you sent matched to their payments by number
  alone: `invoices.py --box DIR --id 'INV-\d+'`. Each is found in a CSV
  ledger row or a file named for it, and is paid only when a line naming
  its number says so; the rest are listed overdue first with the last line
  that named them. A bank credit or remittance of the same sum that names
  no invoice is shown to check by hand, never counted as paid. On
  teodora's files: Bramble & Bean's £2,140 over three invoices, and the
  Hargreaves payment that quotes no number set beside its invoice. On
  hollis's: one overdue, the theatre's $640, out of 111. (#136)
- `quotes`, every quotation in a document checked against your files at
  once: `quotes.py --box DIR --in FILE`. Each quote of four words or more is
  as written (quote-check's verdict), almost (misquote's closest passage, with
  what the quote adds, drops or changes), or not there, with a summary line.
  Built to check the quotes an Almanac entry's notes record against copies of
  the pages they came from. (#135)
- `almanac-keep`, an Almanac entry's best permitted copy fetched into your
  folder through snapshot: `keep.py --catalog FILE --id ID --to FOLDER`. The
  publisher's own address first when the entry is live or frozen, then its
  recovery copies by authenticity; a copy marked excluded is never tried, one
  marked review only with `--review`. Wayback captures are fetched raw, and
  the copy's SHA-256 is compared with the entry's fingerprint. (#135)
- `demo/small-models`: Gemma 3 4B and 1B and Qwen2.5 3B, run locally, given
  willow's own 270 add-on cards to assemble and teodora's files to act on,
  every result kept, and `demo/small-models/build.py` putting all of it, with the session that
  ran it, into one box to ask. The session is kept by its first bytes and
  their SHA-256, never its text, and read through `transcript-redact` and
  `agent-transcript`. Picking from cards, neither model invented a name; a
  note they wrote alone missed or reversed her urgent items; with code
  ranking the facts, Gemma's note put her £2,140 owed first, the right way
  round. (#134)
- `demo/ofrenda`, a séance where the ghost can't lie: a local Gemma,
  through `openai-compatible`, speaks for a made-up New Mexico abuela from
  her old computer's files (her terminal history read by `shell-history`)
  and for Babbage and Ada Lovelace from their own books. Frozen before it
  was asked: the kernel served the right passage for every answerable
  question and nothing for the silent ones; the 4B answered most from the
  passages, cited; every guess the 1B made cited nothing and was proposed
  to no one. Nothing was sealed. (#131)
- `openai-compatible`, suggestions from a model at any OpenAI-compatible
  endpoint (llama.cpp's server, Ollama, LM Studio, vLLM, or a hosted one):
  `openai_compatible.py ask --box DIR --url URL --model NAME "question"`.
  The kernel bites first and only the passages it served go to the model;
  when it serves none, no model is asked. The reply goes to `propose`
  citing the passages its brackets name, and one citing none is proposed to
  no one. It never seals. (#131)
- `shell-history`, a reader that mirrors bash, zsh and fish history as
  plain text the kernel reads: `shell_history.py mirror --from FOLDER --to
  MIRROR`. Each command is one line with the time its shell recorded it,
  in UTC, and a day's commands are one paragraph. A file is known by its
  name (`bash_history`, `zsh_history`, `histfile`, `fish_history`), never
  by what it holds; a command with no recorded time is written bare. (#131)
- `git-history`, `persona-card` and `corpus-lens`: commit messages and
  diffs as a dated pile, the git program called not linked; a persona card
  compiled into the same system-prompt bytes every time, with the prompt's
  hash on the record; and corpus-lens process reports as passages, where
  your intent arrives and who writes the code. (#130)
- `agent-transcript`, `session-cost`, `codebase-memory`, `format-rot` and
  `nestor`: session files as numbered spoken turns; tokens those sessions
  spent, by day and repo; a code-graph SQLite file as passages; formats
  that may stop opening, flagged while you can still convert them; and
  answers a person has checked in Nestor, each citing who and when. (#130)
- `fixity`, `three-two-one` and `restore-drill`: a folder's files hashed
  again now and then, a hash that moved with no newer mtime flagged as rot;
  how many verified copies of the record exist, held to three copies, two
  kinds of storage, one away from home; and a backup zip restored into
  scratch and verified there, so you know it restores before the day you
  need it. (#130)
- Five ideas added to `adapters/planned.json` about keeping archives whole:
  `warc` (web archives read as captured pages), `restore-drill` (a backup
  restored into scratch and verified), `fixity` (file hashes on the record,
  so rot is told from an edit), `format-rot` (files in formats that may stop
  opening) and `three-two-one` (how many verified copies of the record exist,
  and where). (#128)
- Seventeen ideas added to `adapters/planned.json` about models: `model-card`
  (the model behind an assistant named on a card, its hash on the record);
  holding a model to its card and judging it by the record (`cite-honesty`,
  `model-drift`, `model-exam`, `model-recall`, `sent-log`, `weights-pin`,
  `folder-card`); finding and describing the models on this machine
  (`model-shelf`, `weights-card`); and the ways a model runs that no idea
  covered (`in-process`, `mlx`, `os-model`, `browser-model`, `llm-cli`,
  `bedrock`, `mcp-sampling`). `local-model` and `openai-compatible` now name
  the runtimes they reach. (#124)
- `almanac`: An Almanac's catalog.json (climate, health, civic and the rest):
  each public dataset's description, publisher and source as a passage, with
  the curator's status and when the link checker last reached it. Reads every
  catalog.json under a folder of almanac checkouts; never fetches one. (#123)
- `demo/stewart-crossover`, a study: a fictional Star Trek fan's files beside
  the real record of 2020 to 2023 of Patrick Stewart's life, every word about
  him a fact two publishers hold, a quote a source holds, or a planted trap,
  judged with tools from Willow, willows-grove, willow-mcp, willow-bot and
  Forge. Run 1 held 15 of 17 rules, run 2 16 of 18, and run 3, from a third
  freeze, all 18; what failed each time is written down with its cause, and
  one of them is bug #89. (#100)
- `make-it-so`: An order held for you: your question, the command you name
  (kept as given and never run), the passages that bear on it and their file
  hashes, written once to a file of yours; `check` says whether those files
  still hold what they held. (#100)
- `stack`: Seven example stacks for #87, each for a different kind of
  folder: a choir's secretary, a smallholding, a small library's maintainer,
  a teacher's class, a local reporter's story, a dog-rescue fosterer and a
  runner back from a knee injury, in `adapters/stdlib/stack/examples/`.
  (#98)
- A language form for issues (`.github/ISSUE_TEMPLATE/language.yml`): a
  language's code, common words, quirks and where its list comes from, so a
  pack can start without Python;
  `.github/ISSUE_TEMPLATE/config.yml` links the languages and the
  add-on ideas, and the pull request template asks for `Part of #`. (#92)
- `words-tlh`: Klingon common words ("'ej", "nuq") out of a question before
  the kernel's bite. Each of its 27 words is in two sources pinned by
  revision or commit and SHA-256, and its card says what the kernel's
  lowercasing and apostrophe splitting cost a Klingon question. (#88)
- `lesson-time`: Lesson plans whose timed parts do not add up to the time
  the plan says it takes, ranged parts held as ranges and optional parts
  left out. (#99)
- `pair-drift`: Figures a summary says that its full text does not, a
  draft and its packet side by side, with ranges and scale words read as
  written. (#99)
- `ripgrep`: Exact search through ripgrep, much faster on a big folder: each
  hit shown with the id of the kernel's own passage that holds it, and one
  the kernel doesn't read as written counted, never shown. Needs the rg
  program, from the ripgrep wheel or your own. (#82)
- `code-shape`: Code searched by its shape through ast-grep, a pattern with
  holes (`requests.get($$$)`) matching every use however it is written, each
  match checked against the kernel's passages. Needs ast-grep, from
  ast-grep-cli or your own. (#82)
- `static-search`: Your approved answers as a static site, a page each and a
  Pagefind search over them, from any static host or Python's http.server;
  only approvals that prove under your key. Needs Pagefind, floored at
  1.3.0, the first whose index is the same bytes every build. (#82)
- `ocr`: Text out of pictures and scanned PDF pages, read by tesseract into
  a mirror; a PDF page with text of its own left to the pdf add-on. Needs
  Pillow, pypdf and the tesseract program, run on pipes. (#82)
- `pgp`: A file signed with your own gpg key, as a detached OpenPGP
  signature anyone can check, and a signature checked back; a `--key` it
  can't use refused rather than signed with another. Needs gpg and
  python-gnupg. (#82)
- `launcher`: Ask from a launcher: the passages your folder holds for a
  question as Alfred Script Filter JSON (which Raycast reads too) or
  tab-separated lines, each with its file and line; nothing written. (#81)
- `logs`: System and app logs (syslog, journald's export, nginx and Apache
  access logs): each entry as a dated line with host, program and message; no
  year is invented for classic syslog. (#81)
- `readwise`: Readwise's highlights export: each highlight, oldest first, as
  a dated line with its book or article, author, location, your note and
  tags. (#81)
- `bank`: Bank statements, OFX or QFX and CSV: each transaction, oldest
  first, as a dated line, then the months added up as spent, received and
  net; an ambiguous date is never guessed. (#81)
- `orders`: Amazon's order history and other shops' order CSVs: each item,
  oldest first, as a dated line with its cost, currency and order number; a
  date that reads either way round is never guessed. (#81)
- `reddit`: Reddit's data request CSVs: your posts and comments, oldest
  first, as dated lines with their subreddit, and saved items by permalink;
  IP addresses not copied. (#81)
- `linkedin`: LinkedIn's data export CSVs (messages, connections, shares,
  comments): each row, oldest first, as a dated line; emails and profile
  addresses not copied. (#81)
- `goodreads`: Goodreads and StoryGraph library exports: each book, oldest
  first, as a dated line with its shelf, rating out of five, review and tags.
  (#81)
- `letterboxd`: Letterboxd's export CSVs: each film row, oldest first, as a
  dated line (watched, rated or listed) with its rating out of five, rewatch
  mark, review and tags. (#81)
- `jira`: Jira's issue export, XML or CSV: each issue, oldest first, with its
  status, type, people, labels, description and comments as a dated passage.
  (#81)
- `home-sensors`: Home Assistant's history export as a table of daily
  numbers, a column for each entity headed by its friendly name and unit, the
  form the readings add-on can trend. (#81)
- `health`: Apple Health's export.xml as a table of daily numbers (steps,
  distance, energy, exercise, heart rate, weight) the readings add-on can
  trend; read as a stream, entities refused. (#81)
- `ci-logs`: CI run logs from GitHub Actions, Forgejo Actions or GitLab CI:
  each failing step as a passage with its name, the time, its last lines and
  the error; passing runs skipped and counted. (#81)
- `code-comments`: A codebase's comments and docstrings, line for line: each
  source file becomes a file of the same number of lines holding the comment
  text of the same line, so a hit is cited by the source's own line number.
  (#79)
- `notion`: Notion's export zip, read without unpacking and one nested zip
  deep: each page and database with its path, Notion's ids taken off and a
  page's first heading not repeated. (#79)
- `discord`: Discord's data package zip, read without unpacking: your
  messages, oldest first, as dated lines by server and channel, from the
  older JSON or the newer CSV message files. (#79)
- `slack`: Slack's export zip, read without unpacking: each message, oldest
  first, as a dated line with its channel and author; users, channels and
  links written as words; joins and similar left out. (#79)
- `location-history`: Google Maps Timeline exports, Takeout's semantic
  location history or the newer Timeline file: each place visited and each
  trip as a dated line with the hours it covers. (#79)
- `meta-archive`: Facebook and Instagram's Download Your Information JSON:
  messages with their conversation and sender, posts and comments, oldest
  first as dated lines, the export's garbled accents put right. (#79)
- `gh-json`: What gh prints with --json for issues, pull requests and runs,
  saved to a file: each item, oldest first, as a dated passage with its
  state, author, labels, body and comments. (#79)
- `trello`: A Trello board's JSON export: each open list with its open cards,
  their due days, labels, descriptions, checklists with ticks and comments,
  archived lists and cards left out. (#79)
- `matrix`: Element's JSON room export: each message, oldest first, as a
  dated line with its room and sender; emotes and image or file descriptions
  kept; joins, reactions and other events left out. (#79)
- `man-pages`: The man pages installed on this machine, gzipped or not, as
  plain text: title, section headings and the words with fonts, escapes and
  the usual macros read; comments and macro definitions dropped. (#79)
- `lockfiles`: Lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml,
  Cargo.lock, poetry.lock, uv.lock, go.sum): a heading and a line for each
  locked package and version, in name order. (#79)
- `listening`: Spotify's data download, account data or extended history:
  each play, oldest first, as a dated line with its length; skips of under
  thirty seconds left out. (#79)
- `irc`: IRC logs from WeeChat, irssi or ZNC: one dated line per message and
  action with its channel; joins, parts and modes left out; a log of
  something else skipped and counted. (#79)
- `stems`: Word forms for some thirty languages through Snowball's stemmer,
  so "häuser" finds "haus" and "книги" finds "книга": a word no file holds
  is read as the form of its stem the most passages hold, offered, never
  asked. Needs snowballstemmer. (#80)
- `photos`: When and where each photo was taken, from its EXIF, as a dated
  passage in a mirror: the date and time, the GPS position, the camera.
  Needs Pillow, floored at 11.0.0, the first with a wheel for Python 3.13.
  (#80)
- `sheets`: Spreadsheets as a person sees them, beyond what the office add-on
  reads: each cell by its address and number format, each formula after its
  saved result, and the notes on cells. Needs openpyxl. (#80)
- `manifests`: Docker Compose and Kubernetes YAML, a passage for each service
  and object: its image, ports, volumes, mounts, routes and selectors, and
  environments, ConfigMaps and Secrets by name, never value. Needs PyYAML.
  (#80)
- `record-sql`: SQL straight over your record, in place: its rows, and each
  passage a bite served, as two tables in DuckDB's memory, the chain checked
  first and DuckDB's way out to files, databases and the network locked shut
  before your SQL runs. Needs DuckDB, floored at 1.1.1, the first with a
  wheel for Python 3.13. (#80)
- `dialect`: The words you use far more than the world does, from your files
  against wordfreq's counts: those the world doesn't have, and those you use
  far beyond its rate; a file's codes in capitals left out. Needs wordfreq,
  floored at 3.1.0, the first that doesn't import pkg_resources. (#80)
- `x-archive`: An X (Twitter) archive: your posts, replies and direct
  messages, oldest first, as dated lines with links expanded and entities
  read; the archive's other data files skipped and counted. (#77)
- `mastodon`: A Mastodon or Pixelfed account archive's outbox: your own
  posts, oldest first, as dated lines with content warnings, replies and
  attachment descriptions; boosts and likes left out. (#77)
- `sbom`: SBOMs in SPDX or CycloneDX JSON: a heading and a line for each
  component with its version, licence and package URL, in name order. (#77)
- `sarif`: SARIF reports from code scanners: each finding as a passage with
  the tool, rule, level and place, the rule's short description and the
  message, in file and line order. (#77)
- `wallabag`: wallabag's JSON export: each saved entry, oldest first, with
  its title, URL, tags, highlights and the article's text read as a page.
  (#77)
- `karakeep`: Karakeep's JSON export: each bookmark, oldest first, with its
  day, title, URL, tags, your note, its summary and the page description or
  text. (#77)
- `google-keep`: Google Keep notes from Takeout: each note or list as a dated
  passage with its labels and ticked items; notes in the bin and other JSON
  skipped and counted. (#77)
- `day-one`: Day One's JSON export: each journal entry, oldest first, as a
  dated passage with its place, weather and tags and its Markdown escapes
  undone. (#77)
- `joplin`: Joplin's .jex export, read as the tar archive it is without
  unpacking: each note with its title, notebook path and dates, then its
  text; the trash, tags and pictures left out. (#77)
- `musicxml`: MusicXML scores: each as its titles, credits, key, time, tempo,
  markings and lyrics in words, the notes themselves not copied; a file that
  declares entities is not read. (#77)
- `screenplay`: Fountain and Final Draft scripts: each as its scenes, with
  action, cues and dialogue, so a line can be cited by scene; notes,
  transitions and parentheticals left out. (#77)
- `mediawiki`: A MediaWiki XML dump: each page's latest revision as plain
  text with its title and the day it changed, the wiki markup taken off; a
  file that declares entities is not read. (#77)
- `family-tree`: Family trees from GEDCOM files: each person as a paragraph
  that names its own record, with births, deaths, parents, spouses and notes
  as the file writes them. (#77)
- `budget`: Spending against the monthly budget you wrote down in your own
  words: your statements' lines matched to each category by the markers you
  gave, each month held against it. (#75)
- `foia`: Freedom-of-information requests from your notes: who you asked,
  when, when an answer is due (a date you wrote, or the time the law you name
  gives), and which are answered. (#75)
- `syllabus`: A course syllabus as dates: the readings, assignments and exams
  that fall due, soonest first, each cited and measured from today. (#75)
- `livestock`: Each animal's births, treatments and sales from your farm
  records, gathered by tag or name: born, treated and last treated, sold or
  died with its price. (#75)
- `milestones`: Your child's firsts, milestones and measurements from your
  notes, each with the child's age on the day, counted from the birth date
  you give. (#75)
- `reading-log`: A child's reading log from the lines you wrote: days, pages
  and minutes for each week and for each book. (#75)
- `subscriptions`: What you pay every month or year, found by the rhythm of
  the payments in your statements and emails (a month apart three times, or a
  year apart twice), with the latest amount and when the next is about due.
  (#75)
- `pile-poetry`: Verse walked along the pairs of words your own files put
  side by side more than once, drawn by the seeded stream so a poem can be
  made again; nothing in it your files do not have. (#75)
- `oracle-text`: Readings written by a Tracery grammar, every branch picked
  by the seeded stream, so any reading can be made again from its seed:
  modifiers, named expansions, a built-in grammar or your own file. (#75)
- `hook-stop`: A Stop hook that won't let an assistant's turn end while the
  record doesn't verify or the repository has uncommitted work, and says
  which; it lets go once it has already held the turn. (#75)
- `hook-impact`: A PreToolUse hook that, before an edit, hands the assistant
  every place in the person's files that names the file by its whole name, by
  file and line; it never blocks. (#75)
- `hook-guard`: A PreToolUse hook that refuses, by two named rules and never
  by judgment, a call that would read the box's key or change a file inside
  the box other than through the kernel. (#75)
- `hook-compact`: A PreCompact hook that prints what the record still holds
  open, the suggestions waiting for a seal and the questions asked again and
  never answered, so they survive an assistant's summary. (#75)
- `demo/known-gaps`: php2shell's method pointed at the fleet's own twelve
  known security gaps, and at seven cpython CVE fixes as the outside control.
  A question written from a gap's own text, asked of the code before the fix,
  reaches the changed lines in the whole old tree far above chance, and
  cannot order the changed passages themselves; the same verdicts on cpython,
  with a far smaller effect. Four freezes, blind questions from two writers
  and a null set, every number quoted from a kernel record; phase 5's
  findings stay private. CI gains the `demo:known-gaps` gate. (#74)
- `job-hunt`: Applications sent, replies and interviews by company: where
  each stands and how long you have waited, from lines about a job search.
  (#73)
- `garden`: What you planted, where and when, and how it did, season by
  season, from garden notes that say a planting or a harvest. (#73)
- `baby-log`: Feeds, sleeps and nappies from your notes, counted by day with
  the last of each and its time. (#73)
- `attendance`: Attendance for a class, club or group from your register:
  each person's days there out of days marked, or the marks of each week.
  (#73)
- `warranties`: Receipts and warranties: for each thing a line gives a
  warranty, the day its cover ends (said, or bought plus a length) and where
  its receipt is. (#73)
- `home-upkeep`: Home upkeep from your notes and receipts: the boiler,
  filters, gutters and the rest, when each was last done and what is due by a
  date or interval you wrote. (#73)
- `pets`: Each pet's vet visits, vaccines, worming and medicines from your
  records: the last of each, its cost by currency sign, and what is due by a
  date or interval you wrote. (#73)
- `car`: Your car's services, repairs and inspections from receipts and
  notes: the last of each kind, what it cost by currency sign, and what is
  due by a date or interval you wrote. (#73)
- `mood`: The mood scores you write in a journal, gathered by month or week
  with the average, the lowest and highest day and the change from the period
  before. (#73)
- `gradebook`: A teacher's gradebook that stays on this machine: each
  student's marks from the lines you wrote, and who is falling behind, by
  plain arithmetic. (#73)
- `minutes`: Meeting minutes read for what was decided and what is still to
  do: decisions, and actions with their owner and due date, open or closed.
  (#73)
- `mileage`: Miles driven for work, totalled for each tax year from the lines
  of your notes that say a drive and how far; miles and kilometres kept
  apart, odometer readings left out. (#73)
- `hours`: Hours worked or volunteered, added up for each client or group
  your notes name, from lines that say a work word and a length of time.
  (#73)
- `badge`: an SVG badge for a page from the record: how many answers are
  approved and from how many files, green when the chain holds and every
  approval stands, amber when one doesn't, red when the chain breaks, grey
  when nothing is approved. Its description says how to check it, and
  `--link` prints the Markdown for a page. (#72)
- `llms-txt`: an llms.txt written from what is actually in a folder (a title,
  a summary, a section for each folder, a link and a one-line note for each
  text file, files over 50 KB under Optional), and a check of one against the
  llmstxt.org format, each departure at its line. Nothing is invented. (#72)
- `braille`: approved answers (or any text file) as a braille-ready file:
  uncontracted (grade 1) English braille in North American Braille ASCII,
  with capitals, number signs and punctuation, in lines of 40 cells and pages
  of 25 lines. Characters with no cell are counted and said. Nothing is sent
  to a device. (#72)
- `deep-links`: each approved answer, or each passage a question holds, as
  links that open the file at the line: a `file://` link with an RFC 5147
  `#line=` fragment and, with `--base`, a web link with a browser text
  fragment, encoded as the standards ask. Nothing is opened or written. (#72)
- `rss-out`: your approved answers as an RSS 2.0 feed file, newest first:
  each item's title the answer's first line, its description the answer with
  the reason it was given and the places it cites, its date when you approved
  it. `--since` keeps only what is new. A forged approval is never in it, a
  changed proposal is left out and said. (#72)
- `evernote`: Evernote's .enex files, each note as a paragraph with its
  title, notebook (the export file's name), dates, tags, source and
  attachment names, then its text with lists, checkboxes and tables read as
  text. (#72)
- `places`: KML, GeoJSON and GPX files, each place as a paragraph with its
  name, the folders it is in, your note on it and its coordinates (a line or
  an area as its kind and first point), so a question about a place finds
  what you wrote. (#72)
- `chordpro`: ChordPro song sheets, each song as its title, artist, key and
  capo, the chords it uses, and its lyrics with the chords taken out of the
  lines, so a question about a lyric finds the song. Tab sections are
  dropped. (#72)
- `pgn`: Chess games from PGN files, each game as who played, when, where,
  the result and the opening, then every comment in the moves with the move
  it follows (Black's with three dots). The moves themselves are not copied. (#72)
- `latex`: LaTeX sources as plain prose, line for line: the mirror has the
  source's lines, so a passage is cited by the .tex file's own line.
  Comments, the preamble (but the title and author), math, verbatim and
  picture environments and layout commands are dropped; section, emphasis,
  caption and footnote text, citations as [key], accents and dashes are kept. (#72)
- `jupyter`: Jupyter notebooks, each cell as a block headed by its number and
  kind: Markdown and code as written, and a code cell's text outputs (printed
  text, a result's plain form, an error's name and message) under "output:".
  Pictures are left out. Older nbformat 3 notebooks are read too. (#72)
- `rtf`: RTF documents as plain text: paragraphs and line breaks kept, the
  font and style tables, formatting words, pictures, headers and footers
  dropped, escaped letters and Unicode read as the characters they are, and a
  field's shown result kept. (#72)
- `bibtex`: `.bib` files, each reference as a passage that begins with its
  citation key, with its title, year, authors, where it appeared, doi,
  keywords and abstract, so you can ask which paper said it and get the key
  to cite. `@string` macros are filled in and LaTeX accents are read as the
  letters they make. (#72)
- `calendar-out`: the dates coming up in your files (found the way
  `coming-up` finds them) as an .ics file any calendar app can import or
  subscribe to: an all-day event for each, its title the line it was found on
  and its description the file and line. Ids are stable so reimporting
  doesn't double, dates already in a calendar file are not written again, and
  nothing dated writes nothing. (#71)
- `cloudevents`: the record's rows as CloudEvents 1.0 JSON events, one a
  line: the id is the row's own hash, the source names the box by its first
  row, the type is the row's kind, and the data is the row, so the chain
  still checks. `--from-row` and `--kinds` narrow it. The record holds no
  question's words, and neither do the events. (#71)
- `annotations`: approved answers as W3C Web Annotations in an annotation
  page: the answer as the body, and a target for each cited passage with its
  file, its lines as an RFC 5147 fragment and its words as a quote, so an
  annotation tool can show what your files say beside the page. A citation no
  longer in your files is left off and said. (#71)
- `ro-crate`: a box snapshot as an RO-Crate research object, a zip a
  repository such as Zenodo can read: every file with its SHA-256, size, kind
  and licence, the record and the approved answers, and the record's tip
  pinned. The key and the box's settings are not in it, the licence is never
  guessed, and the copy is checked before it is kept. (#71)
- `scrub`: a copy of a JPEG, PNG, docx, xlsx or pptx without its hidden
  details, and a list of what was taken out: Exif, XMP and IPTC (keeping the
  orientation), PNG text chunks, an Office file's author, times, revision,
  company, edit-session ids and the names on comments and tracked changes.
  Anything else is refused rather than copied unchanged. (#71)
- `profile`: where a question's time goes: how long the kernel takes to read
  the folder and to rank it, and the functions the time went to, from
  cProfile, under the kernel's version and release so two releases compare.
  Its script is named question_profile, since a script called profile shadows
  the standard library's module. Nothing is written and the question's words
  are not printed. (#71)
- `box-health`: a box's health in one line: whether the chain holds, how many
  approvals hold and suggestions wait, the files the bite can't read counted
  by kind with the add-on that reads each, whether the words list is the one
  last used, and when the record last had an `out` row. Writes nothing, not
  even an `out` row. (#71)
- `nicknames`: the names you call people, as a words list written from what
  your own files say: a family word beside a capitalised name ("Mum
  (Margaret)", "my dad Robert", "Auntie Jean") becomes `mum = margaret`, with
  the file and line it came from, so "Mum" finds Margaret. Days, months, chat
  labels and titles are no names; a nickname two names claim is said. (#71)
- `fair-merge`: each folder of a pile ranked on its own by the kernel and the
  lists dealt out in turns, so a large corpus can't push a small one out on
  volume alone; a source that found nothing says so, and one with more says
  how many. Nothing is written. (#71)
- `why-not`: why a question got "not enough to say": for each word that
  counts, how many passages hold it; the nearest passages and what they
  lacked; a close spelling with the words-list line that would teach it; and
  the kind of file that would have answered. It asks the kernel's way without
  asking, so nothing is written, not even a record row. (#71)
- `hook-start`: a SessionStart hook that tells the assistant what waits on
  the person (suggestions to approve, stale answers, dates coming up), read
  the way `digest` reads it, as the JSON a hook reads. A quiet box prints
  nothing, and opening a session writes nothing, not even an `out` row. (#71)
- `hook-shell`: a command split the way the shell splits it before a rule
  judges it: quotes, escapes, `$'...'` strings, variables, substitutions,
  `bash -c` and `eval` payloads and `sudo`/`env`/`xargs` wrappers, so `r""m`,
  a full path and `$a$b` are all `rm`. `run` is a PreToolUse hook that
  refuses a denied command, or one whose command word is only known at run
  time. (#71)
- `hook-leaks`: a PreToolUse hook that refuses a Write, Edit, notebook cell
  or Bash command holding a key, a password or a card number, by the
  `privacy` add-on's shapes. The reason names only the kind, never the value,
  and text an edit takes out is not looked at, so a secret can still be
  removed. (#71)
- `prov`: the record as W3C PROV-JSON, every row an activity and every
  seal traced to its answer, the suggestion it approved, the passages that
  suggestion cites and the person who approved it. A seal that doesn't prove
  under the key, or whose proposal file changed, is left out and said. (#70)
- `in-toto`: each approved answer as an in-toto Statement (v1), its subject
  the sha256 of the file as written, its predicate the claim, the cited
  passages, the question's fingerprint and the record row that holds the
  approval. Unsigned: signing takes the key, which no add-on reads. (#70)
- `agents-md-check`: the commands, paths, links, make targets, npm scripts
  and `@` imports an AGENTS.md or CLAUDE.md names that the repo no longer
  has, by file and line. (#70)
- `licenses`: the licence of every installed Python and npm package, read
  from its own metadata, in four classes (permissive, weak copyleft, strong
  copyleft, undeclared), with an SPDX expression read through; everything but
  the permissive ones is listed by file and line. (#70)
- `instruction-files`: for a folder, the instruction files each of eight
  coding agents would load, general first, with each file's size and hash
  and the `@` imports Claude Code would follow. (#70)
- `codeowners`: who owns a file, the CODEOWNERS rule that matches it cited
  by line, read the way GitHub (last match wins), GitLab (sections and their
  defaults) and Forgejo (every matching regex) each do. (#70)
- `words-ar` and `words-cy`, which take Arabic's and Welsh's common words out
  of a question before the kernel's bite. `words-ar` also takes the short
  vowel marks out of the question, since the kernel splits a word at each. (#70)
- `package-contents`: what a wheel, sdist, npm tarball or crate holds, every
  file with its size, and the code that would run because you installed it,
  by file and line: a `.pth` import line, a setup.py and build backend, the
  npm install hooks, a build script or procedural macro. Read in memory,
  never unpacked or run; a path that climbs out of its folder is flagged. (#70)
- `words-ru` and `words-tr`, which take Russian's and Turkish's common words
  out of a question before the kernel's bite, as the other words add-ons do.
  `words-tr` reads a capital İ as i first, so it doesn't split a word. (#70)
- `pile-build`: the pile store built after each change, behind a lock on
  its folder, again until it matches when the folder changes mid-build, and
  with `--background` detached so a hook never waits. Unlike willow-bot's,
  its orders never say where the key is. (#69)
- `pile-gold`: the passages your sealed answers cite are their questions'
  gold. Asked your questions again (from a file, since the record keeps no
  words), the kernel's rank and pile-rank are each scored by how many of
  them land in the top five. Seals are read through the kernel, which checks
  them against your key; one `gold` row records the counts and the file's
  SHA-256, never a word. (#69)
- `pile-rank`, a rank that knows the folder's phrases: BM25F over each
  passage's words and the word pairs two or more of its texts use, titles
  (path and headings) and question lines weighted over the body, no model.
  A pair never spans a comma or a full stop. (#69)
  It points at where to look, as `scan --rank bm25` does, never the
  kernel's answer. It reads a current pile-store store, else the folder.
- `pile-rungs`: a question climbs the kernel's words, then the folder's
  phrases (pile-rank), then an embedder, and the first rung that answers
  serves. Each rung reached says answered, empty or skipped, and why; the
  embedder rung is always skipped here, since the standard library has none. (#69)
- `pile-serve`: the folder's passages and pile-rank's counts held by one
  process, asked over a Unix socket (mode 600) by the kernel's rank,
  pile-rank or pile-rungs; a folder that changed is read again before the
  next answer. On Hollis's folder a question takes 17 ms on the socket,
  against 0.35 s cold. Its card says `writes: to`, not the idea's
  `nothing`: the socket is a file. (#69)
- `pile-sweep`: the passage size measured on your own sealed answers. Each
  size is read with the kernel's `MAX_CHUNK` set to it in this process only,
  and an answer is found when a top-five passage overlaps its lines; the best
  size finds the most, then reads the fewest lines. It names a size and
  changes nothing. (#69)
- `pile-store`, the store the other pile ideas stand on: a folder's passages
  read once into one SQLite file, a text held in several places stored once,
  and opened read-only only while it still matches the folder, the kernel's
  reading limits and the kernel.py that read it, else built again whole.
  `pile_store.load` gives other add-ons exactly `kernel.chunks` and
  `kernel.dates`; `--check` says stale and why, writing nothing. Unlike
  willow-bot's, it never matches or names the key. (#69)
- `ci`: `adapters/stdlib/ci/cores.py` runs `ci.py run` as its shards at once on this machine,
  `--shard K/N` each with its own record in `<DIR>/<K>`, then every gate's
  verdict from the N records in ci.py's order, each record verified. One
  after another the gates take most of an hour; eight at once took nine
  minutes. AGENTS.md's baseline names it. (#67)
- `ci-memo` pins a run cut into shards whole: `pin` takes `--box` once for
  each shard's record, and a gate two of them hold takes the later one
  named. On this repo, eight shards' records pin as one, 185 gates; after a
  change to one add-on, 123 stand and 62 run. (#68)
- `words-sv` and `words-pl`, two more of the common-words family: Swedish
  and Polish questions asked through them lose their languages' common words
  before the kernel's own `bite`, as words-de does for German. Each `list`
  prints what it leaves out (134 Swedish words, 157 Polish, the cases Polish
  declines its pronouns through among them); the record still keeps no
  words, only the question's fingerprint, and English questions are
  untouched. (#65)
- `daily-word`, an add-on that plays the day's word from the folder's own
  five-letter words: `daily_word.py --box DIR guess WORD`, and `today` for
  the board. The word is drawn by the seeded stream from the day and the
  folder's words themselves, so the same box asks everyone the same word;
  the folder is the dictionary too, and a guess it doesn't hold costs
  nothing. Guesses and marks go on the record through the kernel's append;
  the word shows only when the day is done. (#65)
- `tarot`, an add-on that deals a tarot spread on the record: `tarot.py
  --box DIR draw [N]`, then `check`. The seed is the record's tip, the cards
  come from the seeded stream without replacement, a coin turns each, and
  `check` deals every draw on the record again, naming the first that
  doesn't hold. The deck is the standard 78, named in full; what a card
  means is never said. (#65)
- `quiz`, an add-on that cuts a quiz from your own files: a passage with a
  word missing, for you to fill in from memory: `quiz.py --box DIR ask`,
  then `answer WORD`. The record's tip draws the puzzle through the seeded
  stream, the quiz row holds the answer's SHA-256 and never the word, one
  quiz is open at a time, and the score is the record's own count. Only your
  own writing is quizzed (no markup, fields or shouting), and a folder that
  changed under the quiz marks no one wrong. (#65)
- `transcript-redact`, an add-on that writes a copy of an agent transcript
  fit to share: `transcript_redact.py --from FILE --to FILE`. Keys (by the
  shapes keys wear), the account name in home paths, and emails are taken
  out, each removal listed by line with a stub, and the listing never prints
  what it removed. The copy is always written, 0 removals said when nothing
  left; JSON stays JSON; what has no shape slips through and the card says
  so. (#64)
- `pii-audit`, an add-on that lists the identifying numbers sitting in your
  files, each by file and line, shown masked, never printed whole:
  `pii_audit.py --box DIR` (or `--from FOLDER`). Every number is checked,
  not guessed: Luhn for cards, strict shapes for SSN and NI, and the
  weighted checks for NHS, Medicare and TFN, which also need their name on
  the line, since one ten-digit run in ten passes such a check by luck. A
  run passing nothing is nobody's; what has no checkable shape is said in
  the output, never mistaken for a clean bill. (#64)
- `merkle`, an add-on that cuts a Merkle tree over the record so one row is
  proven with a handful of hashes, not the whole file: `root`, `prove --row
  N --to FILE`, and `check --proof FILE [--root HEX]`, which needs no box. A
  leaf wears a zero byte and a node a one byte so neither poses as the
  other, an odd node rises unchanged, the chain is checked before any proof
  is cut, and a lone proof is self-consistency (42), an answer only beside
  your own copy of the root. On this repo's own 177-row CI record a
  verdict's proof is 8 hashes. (#64)
- `people`, an add-on that lists everyone your files name, most mentioned
  first, and, named, any one of them with every place they're mentioned:
  `people.py --box DIR [WHO]`. A name is known by what the files do with it,
  never a list of names: capitalized at least as often as lowercase, at
  least once doing a person's thing (speaking, coming, calling, being met),
  and no month or weekday. A mention is a line, cited and dated as the files
  say; the roster says what it counted, never who matters. (#63)
- `symptoms`, an add-on that gathers one symptom's diary from your files,
  ready to show a doctor: `symptoms.py --box DIR "knee"`. A line counts when
  it itself names the symptom (every content word, read the kernel's way);
  it is dated as the files say and cited, and a turn is marked only where
  the line says one (worse/better word lists on the card, a mixed line said
  so, an N/10 score shown as written). Nothing is averaged, trended or
  diagnosed; the whole matter written to a file stays `timeline`'s job. (#63)
- `habits`, an add-on that gathers the short lines your files write day
  after day into streaks: `habits.py --box DIR`. A habit is the same line
  (its words, digits dropped, one to six of them) on four or more distinct
  days, dated as the files say; runs and misses are plain counting with no
  clock consulted, "ends on" being the run the last day closes. A line that
  shouts throughout, opens with a field's mark or opens as markup is a
  machine's and never ticks. (#63)
- `debts`, an add-on that lists every line speaking of money owed, oldest
  first, each with its date, the sum it names (as the amounts add-on reads
  one) and where it is: `debts.py --box DIR`. The owing words are owe and
  its forms, IOU, repay, paid back, pay back; lent and borrowed join them
  only with a sum on the line, so a lent drill stays `lending`'s. Nothing is
  netted: a paid-back line is listed beside the debt it answers, and whether
  anything still stands is the files' story to finish. (#63)
- `renewals`, an add-on that lists every line saying an expiry and its own
  date, soonest first, what's gone by marked: `renewals.py --box DIR
  [--now TS]`. The words are expires, expiry, expiration, renew and its
  forms, valid until (till, through, thru), cover ends, ends on; the date is
  the kernel's kind, or written out with a month's name and its day. A
  renewal naming no day is unplaced, a date reading two ways is never
  guessed, and an expiry is never stitched to another line's date. (#63)
- `subtitles`, a reader that mirrors .srt and .vtt transcripts as plain
  text the kernel reads: `subtitles.py mirror --from FOLDER --to MIRROR`.
  Each cue becomes one line, its start first (HH:MM:SS, hours added where a
  cue leaves them off, fractions dropped), lines joined, styling tags off,
  and a WebVTT voice tag as its speaker's name with a colon. NOTE and STYLE
  blocks say nothing; a .vtt without WEBVTT first, or a .srt with no
  readable cue, is skipped and counted. It keeps the readers' contract. (#62)
- `jrnl`, a reader that mirrors jrnl journals as plain text the kernel
  reads: `jrnl.py mirror --from FOLDER --to MIRROR`. A journal is a .txt
  whose first line that says anything opens with jrnl's own
  `[YYYY-MM-DD HH:MM]` stamp; each entry becomes one dated paragraph, the
  brackets off so the kernel reads the date, blank lines inside an entry
  closed up. Any other .txt is someone else's and is skipped, counted,
  never guessed at. It keeps the readers' contract. (#62)
- `ids`, an add-on that names every file of your folder as the world's
  archives do: `ids.py --box DIR [PATH]`. The Software Heritage ID is the
  file's git blob SHA-1 (the tests hold it to git's own answer); the IPFS
  name is a one-chunk raw CIDv1, and past 256 KiB it is said to depend on a
  chunker's choices rather than guessed. PATH adds one file's passages,
  each by its first line, so a paragraph can be cited on its own. Computed
  at home; nothing goes online. (#62)
- `fuzzy-dates`, an add-on that reads the dates your files say with doubt
  ("about 1880", "the early 1880s", "spring 1944", "sometime in March",
  "between 1880 and 1885") and keeps the doubt, in EDTF (ISO 8601-2):
  `fuzzy_dates.py --box DIR`. The grammar is words, small and said in full;
  a year is four digits, 1000 to 2999, so a price never reads as one, and a
  bare question mark is a sentence's. Exact dates stay the kernel's job, so
  the two never read the same words. (#62)
- `abbreviations`, an add-on that reads a question's shorthand as your
  files write it, either way round (`appointment` finds the files' `appt`,
  and `appt` their `appointment`), from a small table of common shorthand:
  `abbreviations.py --box DIR "question"`. It prints the question as read,
  never asking for you, and `lines --box DIR --to FILE` writes the
  words-list lines that make it last, for you to read before you keep them.
  Shorthand the kernel splits at a slash (w/c) is out of reach, and the card
  says so. (#62)
- `said`, an add-on that gathers every line quoting someone into a dated
  timeline of who said what: `said.py --box DIR [WHO]`. A quote is read by
  shape, and three shapes are read: a chat's line (a timestamp, a name, a
  colon), a speech verb at the line's start, and a name with a colon and
  quotation marks; a bare `Name:` is a field label, not a speaker. Each is
  dated by its line, the nearest date above it in its file, or its file's
  name, saying which; WHO keeps one speaker's. (#62)
- `a11y-check`, an add-on that checks your Markdown and HTML documents for
  what trips a screen reader: `a11y_check.py --box DIR` (or `--from FOLDER`).
  Two things, nothing else guessed at: an image without a description (an
  empty Markdown bracket, or an HTML img with no alt at all — `alt=""` is
  the author saying decoration), and a heading more than a level deeper than
  the one before. Fenced code is not document, documents are read by their
  own bytes rather than a mirror's text, and a folder with no documents is
  said, never called clean. (#62)
- `duplicates`, an add-on that groups passages saying the same thing in two
  or more files: `duplicates.py --box DIR`. The same thing is the same words
  in order, case, punctuation and spacing aside, nothing else forgiven, and
  a passage under 8 words never counts. Each copy is dated by its own text,
  else its file's name; the newest is named only when its date beats every
  other, and copies tied to the day leave it unsaid. One file's repeats
  count only when the passage is also in another file. (#62)
- `ci-memo`, an add-on that memoizes CI gates on their inputs' bytes:
  `ci_memo.py pin --box DIR --to FILE` writes, after a full `ci.py run` of
  this very tree (each verdict row's `files_sha256` proves which), every
  gate's key — its reachable files' paths and SHA-256, hashed as ci.py
  hashes the tree — beside its verdict; `plan --pin FILE` then says which
  verdicts the bytes still cover and prints the `ci.py run` line for the
  rest. Reaches are drawn wide, never narrow: an undrawn gate keys on the
  whole tree, and `deps`, `ports` and `tools` are never memoized, their
  verdicts reaching past the tree. It decides nothing: a standing verdict is
  the old run's, the full run stays the merge's evidence. (#62)
- `reading-level`, an add-on that says how hard each file of your folder
  reads, easiest first: `reading_level.py --box DIR`. One row per file, its
  Flesch reading ease by the book, said in a word, with the words a sentence
  and syllables a word it is made of. Sentences are counted as written (a
  list of notes reads as its items), syllables by rule of thumb, and a file
  under 30 words is listed as too short, never scored; off English prose the
  two lengths say more than the score, and the card says so. (#62)
- `first-mention`, an add-on that says when your files first mention
  something, and shows the line that does:
  `first_mention.py --box DIR "your words"`. A mention is a line that itself
  holds every content word, each read the kernel's way (the words list, and
  a word's plain form); it is dated by its line, the nearest date above it
  in its file, or its file's name, each saying which. The earliest dated
  mention answers; undated mentions are counted beside it, which could be
  earlier, never placed. (#62)
- `amounts`, an add-on that lists every sum of money in your files, oldest
  first, each with its date and the line it's on: `amounts.py --box DIR`. A
  sum is a number written with its currency (`$20`, `£1,840.00`, `EUR 100`,
  `200 lei`); a number that reads two ways names no sum, rather than a
  guessed one, and a bare number is never money. A line that says no date
  takes the nearest date written above it in its file, else its file's name,
  saying which; a sum no date reaches is listed `undated`. It only reads,
  converts nothing and totals nothing. (#62)

- `bot-venv`, an add-on that says whether willow-bot's own venv, or any you
  name, has what CI needs, and prints the line that runs CI with its Python:
  `bot_venv.py [--bot] [--venv DIR ...] [--needs NAME[==VERSION] ...]`.
  `adapters/stdlib/ci/ci.py` calls pytest and ruff through the Python that
  runs it, so one that lacks them makes every lint, tests and mutants row
  unreachable. `--bot` finds the bot's venv by the bot's own rule
  (`$WILLOW_HOME`, else `$WILLOW_VAULT_BOX`; the venv in the bot, or its old
  home while only that exists) and refuses without a box rather than guess.
  It always asks for pytest and ruff; `--needs ruff==0.16.7` holds ruff to
  CI's pin. A folder with no Python, a Python that doesn't answer and a venv
  missing a package are three different answers. It runs nothing but each
  venv's own Python, isolated, and writes nothing. (#59)
- One idea added to `adapters/planned.json`: `bot-venv`, which says whether
  willow-bot's own venv (found by the bot's rule) or any you name has what CI
  needs (pytest, and ruff at CI's pin) and prints the line that runs CI with
  its Python. (#58)
- `tip-pin`, an add-on that pins where a box's record ends (its row count and
  last hash) to a file kept out of the box, and checks the box against it:
  `tip_pin.py pin --box DIR --to FILE`, then `tip_pin.py check --box DIR
  --pin FILE`. Rows cut off the end, or removed and then all re-hashed, pass
  `verify`; the pin finds both (exit 42). Its tests reproduce each. (#55)
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
  written, no key, no network. (#53)

- `bench`, an add-on that measures how fast the kernel answers. `run` builds a
  pile of each `--sizes` passage count (in a scratch folder), reads and ranks
  it the way a bite answers one question, and prints the median time over
  `--repeat` runs, tagged with the kernel's version — run it each release and
  watch for a size whose time jumped, a slowdown the vectors wouldn't catch.
  The pile is synthetic and the times are the machine's, so the numbers are a
  trend to compare against the same machine, not a fixed vector. It builds its
  piles with `tempfile` and reads them; writes no box or file, reads no key, no
  network. (#52)

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

- `restack` settles a conflict in any other Markdown file when both sides
  only added lines where the base had none: REF's lines, then the branch's,
  as #243 and #244 each added paragraphs to ci's card; a side that changed
  a line the base had still stops. `against` says such a conflict is settled,
  not a collision, so create_pr.py no longer stops on it
- `test-impact`'s `run --narrow` on a change that widens to every gate leaves
  them to CI and still runs the docs' checks and what the rest of the change
  reaches, under the guard: #244 changed ruff.toml beside commands.py, nothing
  ran, and a guard breach in commands.py's tests was CI's to find
- `test-impact`: a change that reaches test_strip.py by import, as any change
  to ci/ does, runs only its own reached tests in the copy without GitHub
  (WILLOW_STRIP_ONLY), in seconds, not every add-on's tests four times: 17 to
  19 of the 20 to 25 minutes of a create_pr.py run on ci/ today; GitHub's own
  files still run it whole
- `ci`: the changelog check's refusal says what does the rest: commit the
  entry with the change, and create_pr.py numbers it in the push that opens
  the pull request
- `ci` says what pytest skipped: a gate whose tests skipped some keeps its
  state, and its row says how many and why (`skipped`), printed after the
  state by `run`, `show` and cores.py, as `satisfied  [1 skipped: ...]`.
  Before, a gate whose check never ran read the same as one that held: on
  GitHub, `demo:known-gaps` skips its advisory check on every run, since
  the advisory text is private. `ci-why` reads a failing gate's reason up
  to its own parenthesis, never into the skips after it (#227)
- contradictions reads only prose: a file of code or data by its name, a
  fenced code block in Markdown and a table's row are left out and counted;
  over 14 repositories, 1,404 disagreements became 95 (#223)
- `sort` places a file by the category you sealed for it under
  `sort/<the file>.txt`, ahead of its phrases, marked "sealed by you"; a
  label still waiting, or for a file changed since, is ignored (#220)
- `github`: the drift test looks for the planted problem anywhere in `check`'s
  list, not first in it. Which gate a shard plant reports "in no job" first
  depends on the cut, and the weights move it: a pull request adding an add-on
  (sort, #206) failed the test with its own gate's weight in the cut. (#217)
- `three-two-one`: a copy that holds but has fewer rows than the box says
  how many it is behind (`holds (14 rows, 2 rows behind the box)`). A record
  cut short still verifies, so a truncated or stale copy counted as a copy
  and looked current; it still counts, and now says so. (#211)
- `in-process`: a reply that cites a passage and says nothing else, a bare
  `[1]` or a file and line in brackets, is printed and proposed to no one,
  as a reply citing nothing already was. Qwen2.5 0.5B on a folder of
  repositories cited every time and answered nothing, and three empty
  suggestions waited on a seal. (#211)
- `hook-fail-closed`: when the hook breaks, the reason is one line, how it
  exited and its last words, and its traceback stays out of stderr. With
  the traceback passed through, hook-fuzz read the wrapped hook as broken
  (a traceback under any exit) while the wrapper had blocked the tool as
  it should; now the two agree. (#211)
- `hosts`: `show claude-code` still refuses, since Claude Code takes no MCP
  server from this table, and the refusal now says where its way in is:
  the prompt hook in `adapters/stdlib/claude-code`. (#211)
- history and on-this-day print a report (the report contract), a group a
  day and a group a year; empty exits 0 in each, where it said 42. (#210)
- coming-up, box-health, agents-md-check, xref and pins print a report (the
  report contract); coming-up with nothing in its window exits 0 where it
  said 42; repo-pile reads xref's report. (#199)
- `ci`: the heavy CI jobs no longer wait on `first`, only on lint, against
  and changelog. `first` runs what a change reaches, and on a pull request
  converting seven add-ons that was 18 minutes, during which no heavy job
  could start; it runs beside them again, as the early word it is. The
  `mutants-reach` job runs its gates through `adapters/stdlib/ci/cores.py`,
  four at once: a change to the contract tests reaches every mutants gate,
  and the whole part in one job took most of an hour. (#214)
- secrets-audit, symptoms, first-mention, misquote, why-not, minutes and
  thesis print a report (the report contract); "found nothing" exits 0 where
  minutes, symptoms, first-mention and misquote said 42. A card says
  `output: report` in its header, or it isn't one. stewart-crossover's
  freeze 4: `demo/stewart-crossover/run.py` reads misquote's report. (#198)
- `ci`: the heavy CI jobs wait on the fast ones. tests, strip, ports, demo,
  deps, tools and the mutants jobs `need` lint, first, against and changelog
  in `.github/workflows/ci.yml`, so on a pull request the checks that take
  seconds take the runners first, and one that fails stops the rest from
  queueing: a red lint or a duplicate add-on costs four jobs, not fourteen.
  A push to main, where three of the four don't run, goes on past them. (#208)
- `ci`: `--shard K/N` cuts the gates by the seconds each is expected to take
  (`gate_weight`: an add-on chunk's or a mutants gate's from
  `adapters/stdlib/ci/test-times.json`, six runs of the add-on's tests for the mutants, a small
  table for the rest) instead of one apiece, so the shards end about
  together. The four mutants shards' expected time was 21, 25, 21 and 62
  minutes by count and is 32, 32, 32 and 32 now; `adapters/stdlib/ci/test-times.json` is
  refreshed from a run of every add-on's tests, 314 files timed where 106 were.
  (#208)
- `ci`'s own tests drive `tests:beats` and `tests:coverage` where they drove
  the whole `demo` part. Eight tests ran `ci.py run demo`, 14 gates and
  about 50 s a call, to prove things about the record (the same bytes twice,
  the gates in order, a shard's rows, verify, a refusal before any gate
  runs), none of which depends on which gates ran. Two gates are still more
  than one, so their order is still tested, and both are satisfied with
  only pytest installed. test_ci.py went from 147 s to 17 s. The 147 s
  showed in three places: it was `tests:adapters-1` by itself (about 40 s
  for the other chunks), the heavy end of `tests:strip-3`, and `mutants:ci`,
  which runs the file six times. (#208)
- `ci`: the tests and strip jobs are one job on each Python, running their
  four shards at once with `adapters/stdlib/ci/cores.py`, in place of eight
  and four jobs a Python. A pull request ran 36 jobs and a push to main 84,
  behind GitHub's 20-job limit; it is now 14 and 30. The tests job's wall
  time was its slowest gate (about nine minutes, the other shards ending in
  ninety seconds) and each job left three of the runner's four cores idle, so
  the four-core job ends about when that gate did. Each Python's records are
  uploaded as one artifact, and `adapters/stdlib/github/github.py check` reads
  a cores command as running every gate it selects, so a cut that drops a
  gate still fails. (#208)
- `restack` settles test_contract.py when two reader branches meet in
  `READERS`: git splits their new entries around one shared closing line, so
  neither side of the conflict holds a whole entry and the rule on lines
  stopped every time. It now reads the file at the base and on both sides and
  takes REF's, with the entries the branch added to `COMMANDS`, `READERS` or
  `PILE_EXTRA`, and its imports, whole. A branch that changed anything else
  there still stops. (#170)
- Cards in plain words: 28 one-line descriptions rewritten to name the thing
  and say what it does, for someone who has never seen willow, and six cards
  moved to the section their piece belongs in (rules, across, stack,
  oakenscroll, almanac-keep, outdated). No card's writes or network changes.
  (#155)
- Tags are worked out by similar every time the list is written, never
  stored: needs an install or not, goes online or not, two topic words a card
  shares with its nearest, and the author's own tag, the one a card's `tags:`
  now holds. Each entry names its three nearest. readme.py's `tags`, which
  wrote tags into cards, is gone, and its card writes only README.md and
  ADDONS.md. (#155)
- `bm25`, the idea, now points at what willow already has: `scan --rank bm25`
  ranks by BM25 with the kernel's own passages and tokenizer. Building the
  idea as first written would have been a second, cruder BM25 (on odile,
  "who is the doctor" served memos matched only on "the" and "who"). What
  is left to build is the one-shot over a box with no index step. (#154)
- `almanac` mirrors more of each entry: its fingerprint baselines, each
  recovery copy in the almanac's order (never one marked excluded), and the
  entry's kind and collection when it isn't a plain dataset. (#135)
- `privacy` withholds every kind willow-bot's one-script scrub does, but a
  home path: Groq, Hugging Face, Cerebras and xAI keys, a GitHub fine-grained
  token, a Discord bot token; a birth date, passport, driver's licence,
  medical record and case number after their labels; an ITIN, an EIN, an
  IPv6 address, a MAC, a wallet, a latitude and longitude, a Discord mention.
  A labelled number must hold a digit, so "claim no longer open" is prose,
  where the one script's takes the next word. (#117)
- `transcript-redact` takes out the privacy add-on's key shapes as well as its
  own, and a private key block whole: written `\n` on one line in a JSON
  transcript, or line by line from BEGIN to END, where its BEGIN line alone
  went before. (#117)
- Known bugs as tests expected to fail: #101 (`said` names "If I" a
  speaker), #102 (`agents-md-check` reads a GitHub owner/repo as a missing
  path), #111 (`snapshot` saves a page under a name the kernel doesn't read)
  and #112 (`pdf` writes ligatures as glyph names). LIMITS.md says how a date
  is read and that the same words in two files are one passage. (#110)
- CI runs a pull request's tests on Python 3.9 and 3.14 only, and a
  push to main's on all six. The six Pythons were 72 of a pull request's 84
  jobs, run 20 at a time, so its CI took 14 to 21 minutes for 6 minutes'
  longest job.
  `github` check holds the tests and strip jobs to the same exclude, as it
  holds them to the same Pythons. (#97)
- `readme` writes a Languages section in ADDONS.md: every `words-<code>`
  add-on, built and planned, by code. The contract test runs every language
  pack from its folder rather than a hand-kept list, and names one that
  isn't `words-` and its code with `words_<code>.py` beside it. (#92)
- `readme` shows each section of the README's summary with a built example or
  two, chosen by hand in `EXAMPLES`, instead of listing every add-on built and
  planned; the full list stays in ADDONS.md (#78)
- `README.md` opens with the kernel and the add-ons as its two parts, says the
  kernel is the seed and never names an add-on, and gains a "What it is not"
  section (#76)
- `mutants` no longer breaks the index in `sys.path.insert(0, ...)`: second on
  the path still finds the repo root, so no test can tell, and 18 add-ons had
  listed it by hand in `adapters/stdlib/mutants/accepted.json`. Other mutants keep their ids. The six
  chosen for `diverge`, `index-cache` and `notes` moved onto breaks their tests
  missed; each now has a test for it (#57)

- The add-ons' tests and `tests:strip` are cut so no job runs them all.
  `tests:adapters` is now `tests:adapters-1` to `-8` and `tests:strip` is
  `tests:strip-1` to `-4` (a group's name still runs all of its gates), cut by
  each test file's past time (`adapters/stdlib/ci/test-times.json`), and the
  tests and strip jobs are sharded on every Python: one pytest over the
  add-ons took eight minutes, and strip ran it again, so a tests job took
  about seventeen. `github.py check` holds that every gate still runs once (#61)

- A seal names the question it answers, and the key signs it. `seal` now
  writes the question's key (`bite_key`) on the seal row, and the proof is
  over the act, the subject and that key. Until now the question lived on the
  hash chain only (a record rewritten and re-hashed could point an approved
  answer at another question, the gap `tip-pin` catches from outside); now
  that takes the key. `verify` counts a seal whose question is changed or
  stripped as one that doesn't prove. A seal from before has no question and
  is proved the old way, so existing boxes keep working, its question taken
  from the record as before; seal it again to bind it. The three ports and the
  vectors follow: half the seal proofs name a question, and the session
  rewrites the record three ways. (#56)
- The README no longer says any edit to a past entry is detected: rows cut off
  the end, or removed and re-hashed from there on, still pass `verify`.
  LIMITS.md says so, and how to check with a copy of the last row's hash and
  the row count kept out of the box's reach. (#55)
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

- `github`'s create_pr.py tries a push or an open GitHub answers with an
  error again, after 2, 4, 8 and 16 seconds, and looks for the pull request
  before each new open: GitHub answered #236's with a 502 and opened it,
  and the run stopped, so a second run did every gate again to find it (#242)
- `forge`'s card says `role: repo` and `runs-in: repo`, so `ui/assemble.py`
  refuses it: it reads every card in the repository and runs assemble, and in
  a stack, which holds neither, 29 of its 40 tests failed (#239)
- `ci`: a deps add-on whose program this machine lacks is unreachable, not
  failing. A card names each program PyPI doesn't install on a `programs:`
  line (ocr's tesseract, kart's bwrap, pgp's gpg), and its deps gates ask
  PATH for it before installing anything; before, a machine without
  tesseract or bubblewrap showed deps:ocr and deps:kart failing, as if the
  add-ons were broken. `readme` refuses `programs:` on a stdlib card, or
  naming a program its `needs:` doesn't (#228)
- `ci` runs every demo's tests: ofrenda's, stewart-crossover's and
  small-models' were in no gate, and one of stewart-crossover's read Wren's
  folder before asking whether it had been made, so it failed on every fresh
  checkout unseen. The demo gates are one table, `DEMO_TESTS`, and
  `adapters/stdlib/ci/test_ci.py` fails on a test file under demo/ that
  none of them runs.
  `test-impact` places a demo change by that table, so a change to
  johnson's tests now plans `demo:share`, the gate that runs them (#226)
- `assemble.py add` runs a piece's own script for its contract (share.py,
  not the ed25519.py beside it), and keeps a failing piece's exit 2 when a
  later piece's is 42 (#225)
- The kernel reads a date only when its month has that day: 1984-06-31 and
  2023-02-29 are no date, 2024-02-29 is; the five ports make the same check,
  and todo's impossible-date group, which only worked around it, is gone
  (#221)
- The report contract's heading in the ci add-on's README is an h2 under the
  page's title, not an h3 that skipped a level; its anchor is unchanged
  (#218)
- `against` reads a pull request stacked on another from where the two
  left each other, not from where each left the base, so the one below is
  not failed for the names the one above took from it. The forge stack
  (#200, with #201 to #203 built on it) showed it: #200's `against` job said
  its own add-on was a duplicate, once per pull request above it. What the
  one above adds past the one below is still held to the others. (#215)
- contradictions leaves a word that's everywhere (on more than one dated
  line in 500, and more than 10) out of what two lines share: over 14
  repositories it found 371,125 "disagreements" in 133 seconds, and now
  1,404 in 18. (#212)
- people counts the values code writes capitalized (None, True, False) as no
  one, beside the months and weekdays: a repository's roster led with None,
  24,048 mentions, from one `self.left None`. (#209)
- todo lists a line whose date no calendar has (1984-06-31) under its own
  heading and exits 42, where it was ordered as the oldest thing to do; the
  oldest is said of the real dates only. known-gaps' freeze 9. (#207)
- The UI's Start it runs the sealed flow over every folder of the pick, each
  its own record with its page beside it, where it ran over the first only;
  two folders of one name get a record each (`files-2`), where the second
  was told "already set up". (#205)
- The UI's kernel baseline offers a reader for a kind of file its card
  names, not for an English word: a kind counts with its dot (`.so`), in
  capitals (PDF), or bare when three letters or more, so `.so` files are no
  longer offered agent-transcript, bibtex, chordpro and clauses. (#204)
- model-shelf looks in the Ollama service's folder
  (/usr/share/ollama/.ollama/models, where Ollama's Linux installer keeps
  its models) when no --home is given, where it said Ollama was "not on this
  machine" while it served 14 models. (#213)
- `pii-audit` reads a run holding a written date, year first, as dates, not
  a card number: two dates side by side (`2027-01-09  2027-01-09`, as
  milestones prints a row) are sixteen digits that pass Luhn one time in
  ten, and listed milestones' own card and tests. (#196)
- `jeles mirror` writes a store too big for one kernel file in parts under
  the kernel's `MAX_FILE` (store.db.1.txt and on), cut only between
  nuggets; a real store (2,277 nuggets, 2.5 MB) mirrored as one file was
  never read, 0 passages, and is now 6,476. (#195)
- The UI's page puts a ticked piece into the sealed flow only when it makes
  a page (a card usage of `--box DIR` and optional flags, and no network); a
  page server, a reader, a hook's setup, a verb or `stack` itself is put in
  the stack and listed as not run on the page. Run as a step, `browse` never
  ended and Start it timed out after 900 seconds. (#194)
- `ui/assemble.py add` adds a piece once when it is both asked for and
  leaned on by another piece asked for in the same call (`digest` and
  `hook-start`), where it crashed with `FileExistsError` and left copies
  STACK.json didn't hold; a refusal partway now removes that call's
  copies, and a folder an older crash left is named, not a traceback. (#193)
- The Java, TypeScript and C# ports exit 42 from a `propose` whose every
  line is refused, as `kernel.py` has since bug #96's fix; they exited 0,
  which looked like an approved answer. The vectors' session now proposes a
  file with every line refused, so a port that drifts here fails
  `vectors/compare.py`. (#191)
- `mail` reads a header sent as raw 8-bit UTF-8 as UTF-8: a subject such as
  "income tax — what you owe, £412.67" no longer comes out with each of
  its non-ASCII letters replaced by `���`, and a From or To name with an
  accent keeps it. The email package hands such a header back as a Header
  whose text has already swapped the bytes away; its bytes are now read
  before that. Ten of the demo lives' 224 messages, all Teodora's, read
  right now. (#169)

- An add-on's tests hold in a copy of its folder, not only in willow: scan,
  start, browse, digest, stack, starter-words, across, parallel, hosts,
  hook-start and box-health assumed an add-on beside them that each only
  looks for, or read a file of willow's; each now holds either way, nothing
  skipped. test-impact places Teodora's words test in its own gate. (#155)
- Security: `ocr` and `photos` pin Pillow 13.0.0 and `ocr` and `pdf` pin
  pypdf 6.21.4, past the advisories filed against Pillow 12.3.0 (heap
  overflows and decompression-bomb bypasses among them) and pypdf 6.21.2
  (infinite loops and runaway memory on crafted files). The floors stay
  where the floor rule puts them. `.github/secret_scanning.yml` keeps the
  redteam demo's planted, fake credentials out of secret scanning. CI's
  first job installs tesseract, as the deps job does, so a change to `ocr`
  can be tested there. (#140)

- `transcript-redact` no longer takes the `n` of a JSON `\n` as the start
  of an email: `\n@AGENTS.md` and `\n@pytest.mark` read as addresses, and
  removing them left `\[redacted:email]`, which JSON can't read, so four
  lines of a real Claude Code session came out broken and `agent-transcript`
  skipped the file. An address after a line break is still taken. (#134)
- `bank` reads a CSV statement whose header names its columns in lower case
  (`date,description,amount`, as teodora's demo files do) or in capitals:
  every one of her 58 statements was skipped. Found by a small local model
  that picked `bank` for her and got nothing back. (#132)
- `propose` now exits 42 when every suggestion is refused, so a file that
  leaves nothing waiting for a seal no longer looks like an approved answer,
  fixing bug #96. (#129)
- `box-health` says how many of the files the bite can't read are over the
  kernel's 1 MB, which a text file too big read the same as one that isn't
  UTF-8. (#127)
- `logs` cuts a mirror bigger than the kernel reads from one file (1 MB)
  into parts it can read, `<name>.txt`, `<name>.part2.txt` and on. A busy
  day's journal mirrored to one 5.9 MB file, which the kernel left out
  without a word. (#126)
- The kernel no longer reads dates that appear only inside `http://` or
  `https://` web addresses, fixing bug #95. (#125)
- `stack` no longer counts add-ons whose 42 exit means "none found" as
  flagged steps, and it can flag add-ons such as `contradictions` whose
  successful exit means something was found, fixing bug #94. (#122)
- `amounts` keeps scale words and abbreviations after sums, such as $5
  billion, $5 million and EUR 10m, so amounts that differ by scale no longer
  print as the same sum, fixing bug #93. (#121)
- `snapshot fetch` gives default names without a suffix an extension from the
  response content type, so saved HTML, text, JSON and PDF pages are names the
  kernel can read while explicit names stay as given, fixing bug #111. (#120)
- `agents-md-check` no longer reports a backticked owner/repo-shaped name as
  a missing path when the same line says it is a repo, while still reporting
  real missing file paths, fixing bug #102. (#119)
- `said` no longer treats a sentence that starts with a common word or a
  bare pronoun, such as "If I said..." or "Someone said...", as a quote by a
  speaker with that name, fixing bug #101. (#118)
- `profile`: its test read a row's location as one run of non-spaces, so it
  failed whenever a frozen module's function (`<frozen posixpath>:71 join`,
  as Python 3.11 and later name them) was among the top own times; the
  location is now any text up to its `:line`. (#83)
- `ci`: the guard meant to let a Unix socket through under `network: none`,
  as this machine only, but looked for `AF_UNIX` on `os`, which has none
  (it is `socket`'s), so every Unix socket counted as going online. It now
  looks on `socket`; a test holds that a Unix socket passes and a name
  looked up by the same code still breaches. (#69)
- `live` counted a launcher standing in for a missing program as failing:
  VS Code puts a `copilot` on PATH that only says the Copilot CLI isn't
  installed, so `tools:copilot` failed on any machine with VS Code. A
  check's own program exiting 127, a shell's "not found", is now not here
  (unreachable, still no pass); any other exit, or 127 from anything else
  the check runs, still fails. (#66)
- ADDONS.md's section headings sat two levels under its title (h1 straight
  to h3), a hole in a screen reader's outline that the new `a11y-check`
  found on this repo's own page. The generated list's headings (the readme
  add-on writes them) and the two written by hand (Newest, Add-on of the
  week) are now h2. (#62)
- A sealed answer is served only while its proposal file still hashes to the
  subject the key signed, and only for the question the record says it was
  sealed for. `bite` took both from the file, so anyone who could write the
  box could change what an approval said, or which question it answered,
  without the key; proposing the same bytes again under another question
  moved it with no file touched, and a deleted file crashed `bite`. `verify`
  now says when a sealed subject's file is missing, changed, or names another
  question (exit 42). Seal bytes are unchanged, so existing seals hold. The
  three ports follow, and the vectors' session now tampers with the file.
  (bug #54, #55)
- `stale`, `export` and `serve` read a sealed answer's proposal file through
  the kernel's `standing`, and `history` checks the file against its subject,
  as `bite` does since bug #54: a file that isn't the bytes the key signed was
  shown as approved (`export`, `stale`), served as the sealed scope (`serve`,
  which served a widened scope's extra passage), or named its path
  (`history`). Now `stale` shows it as `broken`, `export` leaves it out and
  says so on standard error (both exit 42), `serve` serves nothing, and
  `history` says "an answer". `export`'s one accepted mutant no longer
  survives and is taken out of the accepted-mutants list; `serve`'s plural of
  "pool" had no test and now does. (bug #54, #55)
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
