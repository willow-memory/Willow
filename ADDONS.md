# Add-ons

Everything below is an add-on: a folder beside the kernel that uses it and
never changes it. Some are built and tested; the rest are planned, and each
one's line says what it will do. This section is generated from the add-ons'
own cards by [adapters/stdlib/readme](adapters/stdlib/readme/), so an idea
becomes a built add-on only when it exists, and CI fails if this page falls
behind.
The list is open: anyone can add an idea, and anyone can build one from it.
[CONTRIBUTING.md](CONTRIBUTING.md) says how.

**How to read it:** a linked name is built; *(idea)* is not yet. What an
add-on needs installed, with its licence, and where it goes online are said in
words: the kernel itself never goes online. *bot* is rebuilt from
[willow-bot's one script](https://github.com/willow-memory/willow-bot), *box* is built from what the kernel already has, *new* is new.
Each carries up to five tags, worked out from the cards every time this page
is written: `no-install` or `needs-install`; `offline`, `this-machine` or
`online`; two topic words it shares with the add-ons nearest it; and the one
tag its author chose, if any. *near* names the three add-ons closest to it.

<!-- willow:pools -->
`████████████░░░░░░░░` **292 of 505 built** · 451 need no install · 54 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 73 | 35 | 100 | 8 |
| Finding things | 32 | 14 | 36 | 10 |
| Your own words | 19 | 7 | 23 | 3 |
| Keeping track | 40 | 16 | 56 | 0 |
| Trust and proof | 31 | 23 | 45 | 9 |
| Privacy and safety | 13 | 3 | 16 | 0 |
| Assistants | 28 | 43 | 60 | 11 |
| Ways to use it | 25 | 18 | 39 | 4 |
| Play | 12 | 29 | 37 | 4 |
| For maintainers | 19 | 25 | 39 | 5 |
<!-- /willow:pools -->

## Languages

A language pack takes one language's common words out of a question before
the kernel's `bite`, as the kernel already does for English. A pack is mostly
its list: someone who speaks the language can add one without much Python.
[CONTRIBUTING.md](CONTRIBUTING.md#pick-one-up) says how.

<!-- willow:languages -->
**13 built, 3 planned**, beside English, which the kernel has built in.

| Code | Pack | What it does |
|---|---|---|
| `ar` | [words-ar](adapters/stdlib/words-ar/) | Arabic common words ("في", "من", "على"). |
| `cy` | [words-cy](adapters/stdlib/words-cy/) | Welsh common words ("a", "y", "yn"). |
| `de` | [words-de](adapters/stdlib/words-de/) | German common words, so questions aren't matched on "der" and "und". |
| `es` | [words-es](adapters/stdlib/words-es/) | Spanish common words ("el", "y"). |
| `fr` | [words-fr](adapters/stdlib/words-fr/) | French common words ("le", "et"). |
| `hi` | words-hi *(idea)* | Hindi common words ('और', 'है'). |
| `it` | [words-it](adapters/stdlib/words-it/) | Italian common words ("il", "e"). |
| `ja` | words-ja *(idea)* | Japanese, which has no spaces: a small segmenter of its own and a common-words list. |
| `nl` | [words-nl](adapters/stdlib/words-nl/) | Dutch common words ("de", "en"). |
| `pl` | [words-pl](adapters/stdlib/words-pl/) | Polish common words ('i', 'w'). |
| `pt` | [words-pt](adapters/stdlib/words-pt/) | Portuguese common words ("o", "e"). |
| `ru` | [words-ru](adapters/stdlib/words-ru/) | Russian common words ("и", "в", "на"). |
| `sv` | [words-sv](adapters/stdlib/words-sv/) | Swedish common words ('och', 'att'). |
| `tlh` | [words-tlh](adapters/stdlib/words-tlh/) | Klingon common words ("'ej", "nuq"). |
| `tr` | [words-tr](adapters/stdlib/words-tr/) | Turkish common words ("ve", "bir"). |
| `zh` | words-zh *(idea)* | Chinese, which has no spaces: words found by a small segmenter of its own, and a common-words list. |
<!-- /willow:languages -->

## Newest

<!-- willow:newest -->
- 2026-11-01 · [**weakest-link**](adapters/stdlib/weakest-link/) — Each answer's inputs marked measured, fitted or assumed, and the result worth its weakest input, never an average.
- 2026-11-01 · [**thesis**](adapters/stdlib/thesis/) — A thesis's claims, each tied to the source that backs it, and a list of the ones with none.
- 2026-11-01 · [**sent-log**](adapters/stdlib/sent-log/) — Which of your passages went to which online model, read from the record by model card: what left this machine and where to.
- 2026-11-01 · [**rules**](adapters/stdlib/rules/) — A game's or a house's rules, approved one section at a time, so asking what a rule says gives back that exact section, word for word.
- 2026-11-01 · [**quotes**](adapters/stdlib/quotes/) — Every quote in a document checked against your files: as written, almost (and what it adds, drops or changes), or not there.
<!-- /willow:newest -->

## Add-on of the week

<!-- willow:pick week=2026-W44 -->
**[habits](adapters/stdlib/habits/)** — Streaks from the lines you write each day: how many days in a row, and which you missed.

*Drawn for 2026-W44: SHA-256 of "willow add-on of the week 2026-W44", modulo the 292 built add-ons in name order.*
<!-- /willow:pick -->

<!-- willow:list -->
**Contents:** [Reading more kinds of files](#reading-more-kinds-of-files) · [Finding things](#finding-things) · [Your own words](#your-own-words) · [Keeping track](#keeping-track) · [Trust and proof](#trust-and-proof) · [Privacy and safety](#privacy-and-safety) · [Assistants](#assistants) · [Ways to use it](#ways-to-use-it) · [Play](#play) · [For maintainers](#for-maintainers)

## Reading more kinds of files

Each writes plain text into a mirror folder the kernel searches, so your originals are never touched.

- [**agent-transcript**](adapters/stdlib/agent-transcript/) — Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told. *new* `no-install` `offline` `gemini` `claude` · near: instruction-files, hooks-elsewhere, session-cost
- [**almanac**](adapters/stdlib/almanac/) — An Almanac's catalog.json (climate, health, civic and the rest): each public dataset's description and source as passages, with when its link was last checked. *new* `no-install` `offline` `almanac` `links` · near: oakenscroll, almanac-keep, books
- [**almanac-keep**](adapters/stdlib/almanac-keep/) — An Almanac entry's best permitted copy, from the publisher or its ranked recovery list, fetched into your folder with its SHA-256. Goes online: the copy's address, fetched once. *new* `no-install` `online` `sha` `copy` · near: almanac, snapshot, index-cache
- **apple-notes** (idea) — Apple Notes, read from a copy of its database: each note as plain text with its folder and dates. *new* `no-install` `offline` `database` `copy` · near: joplin, evernote, writefreely
- **archivebox** (idea) — ArchiveBox snapshots: each saved page's text, with its URL and the date it was captured. *new* `no-install` `offline` `snapshot` `saved` · near: warc, wayback, snapshot
- [**bank**](adapters/stdlib/bank/) — Bank CSV and OFX statements as dated lines, with spending by month. *new* `no-install` `offline` · near: mastodon, discord, linkedin
- [**bibtex**](adapters/stdlib/bibtex/) — .bib files: each reference as a passage, so you can ask which paper said it and get its key. *new* `no-install` `offline` · near: pgn, code-comments, latex
- **bluesky** (idea) — A Bluesky repo.car export: your posts as dated lines, read by a small CAR and CBOR reader of its own. *new* `no-install` `offline` `posts` `repo` · near: mastodon, linkedin, reddit
- **bookmarks** (idea) — Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file. *new* `no-install` `offline` `sqlite` `html` · near: codebase-memory, nestor, writefreely
- [**books**](adapters/stdlib/books/) — Kindle "My Clippings.txt" highlights and .epub text. *new* `no-install` `offline` `highlights` `book` · near: oakenscroll, almanac, wallabag
- [**calendar**](adapters/stdlib/calendar/) — .ics events and .vcf contacts as dated lines. *new* `no-install` `offline` · near: texts, chats, office
- **canvas** (idea) — Canvas course exports: pages, assignments and discussions as passages. *new* `no-install` `offline` `assignments` `course` · near: moodle, syllabus, google-classroom
- [**chats**](adapters/stdlib/chats/) — WhatsApp and Telegram exports, one dated line per message. *new* `no-install` `offline` `message` `chats` · near: texts, matrix, slack
- [**chordpro**](adapters/stdlib/chordpro/) — ChordPro song sheets: titles, lyrics and chords, so you can ask which song had that line. *new* `no-install` `offline` `title` `lyrics` · near: musicxml, letterboxd, mediawiki
- [**ci-logs**](adapters/stdlib/ci-logs/) — CI run logs you downloaded (GitHub Actions, GitLab CI, Forgejo Actions): each failing step as a passage. *new* `no-install` `offline` `log` `failed` · near: ci-why, logs, ci-cache
- [**clauses**](adapters/stdlib/clauses/) — A policy, contract or set of terms as one sentence a passage, so an answer lands on the clause, and what changed between two versions, sentence by sentence. *new* `no-install` `offline` `policies` · near: web-pages, photos, pdf
- [**code-comments**](adapters/stdlib/code-comments/) — A codebase's comments and docstrings as passages, cited by file and line. *new* `no-install` `offline` `comments` `codebase` · near: codebase-memory, latex, sarif
- [**codebase-memory**](adapters/stdlib/codebase-memory/) — codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line. *new* `no-install` `offline` `codebase` `sqlite` · near: nestor, code-comments, bookmarks
- **confluence** (idea) — A Confluence space's HTML export as plain text, page by page. *new* `no-install` `offline` `html` · near: wallabag, recipes, mediawiki
- [**corpus-lens**](adapters/stdlib/corpus-lens/) — corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code. *new* `no-install` `offline` `agent` `session` · near: agent-transcript, session-cost, sarif
- [**day-one**](adapters/stdlib/day-one/) — Day One's JSON export: each journal entry as a dated passage, with its place and weather. *new* `no-install` `offline` `json` `entries` · near: gh-json, chats, karakeep
- [**discord**](adapters/stdlib/discord/) — Discord's data package: your messages, one dated line each, by server and channel. *new* `no-install` `offline` `message` `channel` · near: slack, irc, matrix
- **dotfiles** (idea) — Your dotfiles as passages: which file sets what, for 'where did I set my editor?' *new* `no-install` `offline` `sets` `editor` · near: start, clauses, mcp
- [**evernote**](adapters/stdlib/evernote/) — Evernote's .enex files: each note as plain text with its notebook, tags and dates. *new* `no-install` `offline` `tags` · near: joplin, karakeep, wallabag
- [**family-tree**](adapters/stdlib/family-tree/) — Family trees from GEDCOM files: who was born where and when, and which record says so. *new* `no-install` `offline` · near: places, bibtex, code-comments
- **forgejo-dump** (idea) — A Forgejo or Gitea dump, Codeberg's included: issues, pull requests and wiki pages as dated passages. *new* `no-install` `offline` `requests` `issues` · near: github-archive, forgejo, gh-json
- [**gh-json**](adapters/stdlib/gh-json/) — What gh prints with --json (issues, pull requests, runs), saved to a file and read as dated passages. *new* `no-install` `offline` `issues` `pull` · near: goodreads, day-one, jira
- [**git-history**](adapters/stdlib/git-history/) — Commit messages and diffs as a dated pile: "when did we change the retry limit?" *new* `no-install` `offline` `message` `history` · near: clauses, location-history, discord
- **github-archive** (idea) — Your GitHub account's data export: the issues, pull requests, reviews and comments you wrote, as dated passages with their links. *new* `no-install` `offline` `requests` `pull` · near: quote-review, contribute, forgejo-dump
- **gitlab-export** (idea) — A GitLab project export, read without unpacking it: its issues, merge requests and comments as dated passages. *new* `no-install` `offline` `issues` `comments` · near: github-archive, joplin, warc
- [**goodreads**](adapters/stdlib/goodreads/) — Goodreads and StoryGraph exports: the books you've read, when, and what you thought of them. *new* `no-install` `offline` `title` `book` · near: letterboxd, slack, musicxml
- **google-classroom** (idea) — Google Classroom from Takeout: assignments, announcements and comments as dated passages. *new* `no-install` `offline` `comments` `takeout` · near: gitlab-export, google-keep, takeout
- [**google-keep**](adapters/stdlib/google-keep/) — Google Keep from Takeout: notes, lists and labels as dated passages. *new* `no-install` `offline` `google` · near: location-history, day-one, mastodon
- [**health**](adapters/stdlib/health/) — Apple Health and Google Fit exports as daily numbers the readings add-on can trend. *new* `no-install` `offline` `google` `trend` · near: home-sensors, sheets, location-history
- [**home-sensors**](adapters/stdlib/home-sensors/) — Home Assistant's history export: sensor readings as dated numbers the readings add-on can trend. *new* `no-install` `offline` `history` `trend` · near: health, location-history, sheets
- **homestead** (idea) — Homestead's exports from its law, ledger and health modules: records, deadlines and evidence as dated passages. *new* `no-install` `offline` `health` `ledger` · near: gitlab-export, oakenscroll, github-archive
- **instapaper** (idea) — Instapaper's CSV and HTML export: saved articles and highlights as dated lines. *new* `no-install` `offline` `html` `saved` · near: pocket, wallabag, readwise
- [**irc**](adapters/stdlib/irc/) — IRC logs from WeeChat, irssi or ZNC, one dated line per message, by network and channel. *new* `no-install` `offline` `message` `channel` · near: slack, matrix, discord
- [**jira**](adapters/stdlib/jira/) — Jira's issue export, CSV or XML: each issue, comment and status change as dated passages. *new* `no-install` `offline` `comments` `xml` · near: mediawiki, linkedin, day-one
- [**joplin**](adapters/stdlib/joplin/) — Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates. *new* `no-install` `offline` `unpacking` `title` · near: evernote, apple-notes, karakeep
- **journiv** (idea) — Journiv journal entries, with their moods, as dated lines, once its export format is settled. *new* `no-install` `offline` `journal` `entries` · near: day-one, mood, jrnl
- [**jrnl**](adapters/stdlib/jrnl/) — jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage. *new* `no-install` `offline` `journal` `entries` · near: shell-history, day-one, outdated
- [**jupyter**](adapters/stdlib/jupyter/) — Jupyter notebooks: Markdown cells, code and text outputs as passages, cited by cell. *new* `no-install` `offline` `notebook` `markdown` · near: code-comments, evernote, joplin
- [**karakeep**](adapters/stdlib/karakeep/) — Karakeep's JSON export: bookmarks, notes and tags as plain text. *new* `no-install` `offline` `tags` `json` · near: wallabag, evernote, joplin
- [**latex**](adapters/stdlib/latex/) — LaTeX sources as plain prose, commands stripped, cited by the .tex file's own lines. *new* `no-install` `offline` · near: code-comments, bibtex, notes
- **lessons** (idea) — Lesson plans from the Emerging Rule community library, by grade and subject, as passages a teacher can ask. *new* `no-install` `offline` `plan` `lesson` · near: my-lessons, lesson-time, support-plan
- [**letterboxd**](adapters/stdlib/letterboxd/) — Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines. *new* `no-install` `offline` · near: goodreads, matrix, musicxml
- [**linkedin**](adapters/stdlib/linkedin/) — LinkedIn's data export: messages, posts and connections as dated lines. *new* `no-install` `offline` `posts` `message` · near: reddit, meta-archive, discord
- [**listening**](adapters/stdlib/listening/) — Spotify's data download: what you listened to, by day, so you can ask what was on that summer. *new* `no-install` `offline` `data` `download` · near: discord, linkedin, reddit
- [**location-history**](adapters/stdlib/location-history/) — Google Maps Timeline and other location exports: where you were, by day. *new* `no-install` `offline` `google` `history` · near: google-keep, orders, day-one
- [**lockfiles**](adapters/stdlib/lockfiles/) — Lockfiles as passages (package-lock.json, pnpm-lock.yaml, poetry.lock, uv.lock, Cargo.lock, go.sum): each package and its locked version. *new* `no-install` `offline` `json` `version` · near: sbom, pins, discord
- [**logs**](adapters/stdlib/logs/) — System and app logs (syslog, journald's export, nginx): each line dated, so you can ask when it started. *new* `no-install` `offline` `message` `log` · near: discord, irc, linkedin
- [**mail**](adapters/stdlib/mail/) — .eml and .mbox files, with sender, date and subject kept. *new* `no-install` `offline` · near: office, calendar, books
- [**man-pages**](adapters/stdlib/man-pages/) — The man pages installed on this machine as plain text, so you can ask your own system's docs. *new* `no-install` `offline` · near: rtf, books, notion
- [**manifests**](adapters/deps/manifests/) — Docker Compose and Kubernetes YAML: each service, image, port and volume as a passage. Needs PyYAML; MIT. *new* `needs-install` `offline` · near: photos, pdf, ocr
- [**mastodon**](adapters/stdlib/mastodon/) — A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines. *new* `no-install` `offline` `posts` `archive` · near: x-archive, meta-archive, linkedin
- [**matrix**](adapters/stdlib/matrix/) — Element's room export, JSON or HTML: one dated line per message in each Matrix room. *new* `no-install` `offline` `message` · near: slack, chats, irc
- [**mediawiki**](adapters/stdlib/mediawiki/) — A MediaWiki XML dump: each page's latest text, with its title and when it changed. *new* `no-install` `offline` `title` `xml` · near: notion, jira, joplin
- **medical-records** (idea) — Your health records as FHIR JSON or C-CDA XML: visits, results and prescriptions as dated lines. *new* `no-install` `offline` `json` `health` · near: box-health, takeout, schema-check
- [**meta-archive**](adapters/stdlib/meta-archive/) — Facebook and Instagram's Download Your Information files: posts, comments and messages as dated lines. *new* `no-install` `offline` `posts` `message` · near: x-archive, linkedin, mastodon
- **moodle** (idea) — Moodle course backups: pages, assignments, quizzes and forum posts as passages. *new* `no-install` `offline` `assignments` `course` · near: canvas, syllabus, front-page
- **music-library** (idea) — Your music files' tags (MP3, FLAC, M4A): artist, album, year and track, as lines. *new* `no-install` `offline` `year` `library` · near: listening, tax-year, livestock
- [**musicxml**](adapters/stdlib/musicxml/) — MusicXML scores: titles, lyrics, tempo and performance markings as passages. *new* `no-install` `offline` `title` `lyrics` · near: chordpro, goodreads, letterboxd
- [**notes**](adapters/stdlib/notes/) — Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. *new* `no-install` `offline` `tags` · near: calendar, karakeep, evernote
- [**notion**](adapters/stdlib/notion/) — Notion's export zip, Markdown and CSV, as plain text with each page's title and path. *new* `no-install` `offline` `title` `zip` · near: mediawiki, slack, joplin
- [**oakenscroll**](adapters/stdlib/oakenscroll/) — Oakenscroll's Office prediction ledger as dated passages you can ask: what you believed, how sure you were, and how it turned out. *new* `no-install` `offline` `office` · near: almanac, jeles, books
- [**ocr**](adapters/deps/ocr/) — Text out of photos of letters and scanned PDFs. Needs Pillow and pypdf, and the tesseract program, run not linked; MIT-CMU, BSD-3-Clause, Apache-2.0. *new* `needs-install` `offline` `photos` `pdf` · near: pdf, photos, sheets
- [**office**](adapters/stdlib/office/) — .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. *new* `no-install` `offline` `office` · near: calendar, mail, oakenscroll
- [**orders**](adapters/stdlib/orders/) — Amazon's order history and other shops' CSV exports: what you bought, when, and for how much. *new* `no-install` `offline` `csv` `history` · near: location-history, reddit, bank
- **package-docs** (idea) — The READMEs and docs inside packages you've already installed (site-packages, node_modules, Cargo's registry cache), so you can ask your dependencies offline. *new* `no-install` `offline` `install` `package` · near: install-scripts, pins, package-contents
- [**parallel**](adapters/stdlib/parallel/) — A reader run over several folders at once, across every CPU core, so a big mirror of many sources builds in a fraction of the time. *new* `no-install` `offline` `core` `fraction` · near: fast-tests, index-cache, test-shards
- **past-papers** (idea) — Past exam papers and their mark schemes as passages: which year asked this, and what earned the marks. *new* `no-install` `offline` `exam` `paper` · near: model-exam, bibtex, paper-key
- [**pdf**](adapters/deps/pdf/) — Text out of PDFs. Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `pdf` · near: ocr, photos, sheets
- [**pgn**](adapters/stdlib/pgn/) — Chess games from PGN files: players, dates, openings and your annotations. *new* `no-install` `offline` · near: bibtex, letterboxd, matrix
- [**photos**](adapters/deps/photos/) — When and where each photo was taken, as dated lines. Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `photos` · near: pdf, ocr, sheets
- [**places**](adapters/stdlib/places/) — KML and GeoJSON files: each place's name, note and coordinates as a passage. *new* `no-install` `offline` · near: sarif, readwise, evernote
- **pocket** (idea) — Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone. *new* `no-install` `offline` `html` `article` · near: instapaper, teams, slack
- **quiet-corner** (idea) — A Quiet Corner backup file: a teacher's classroom observations as dated passages, for that teacher's questions alone. *new* `no-install` `offline` `classroom` · near: google-classroom, repo-index, homestead
- [**readwise**](adapters/stdlib/readwise/) — Readwise's highlights export: every highlight with its book or article, and your note on it. *new* `no-install` `offline` `book` `highlights` · near: wallabag, books, goodreads
- **recipes** (idea) — Recipes from saved web pages and recipe-app exports, as plain text: what can I cook with leeks? *new* `no-install` `offline` `web` `saved` · near: web-pages, confluence, wallabag
- [**reddit**](adapters/stdlib/reddit/) — Reddit's data export: your posts, comments and saved items as dated lines. *new* `no-install` `offline` `posts` `data` · near: linkedin, meta-archive, mastodon
- [**rtf**](adapters/stdlib/rtf/) — RTF documents as plain text. *new* `no-install` `offline` · near: evernote, books, karakeep
- [**sarif**](adapters/stdlib/sarif/) — SARIF reports from code scanners such as CodeQL and Semgrep: each finding as a passage with its rule and place. *new* `no-install` `offline` `reports` · near: code-comments, places, codebase-memory
- [**sbom**](adapters/stdlib/sbom/) — SBOMs in SPDX or CycloneDX JSON: each component, its version and licence, as passages. *new* `no-install` `offline` `json` `version` · near: lockfiles, gh-json, day-one
- [**screenplay**](adapters/stdlib/screenplay/) — Fountain and Final Draft scripts: scenes, characters and lines, cited by scene. *new* `no-install` `offline` · near: code-comments, bibtex, jupyter
- **scripture** (idea) — A scripture or other canonical text with your study notes beside it, cited by book, chapter and verse. *new* `no-install` `offline` `book` `beside` · near: readwise, books, gutenberg
- **scrivener** (idea) — Scrivener projects: each document in the binder as plain text, by its place in the manuscript. *new* `no-install` `offline` `documents` · near: rtf, apple-notes, sigmap
- [**sheets**](adapters/deps/sheets/) — Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. Needs openpyxl; MIT. *new* `needs-install` `offline` · near: pdf, photos, ocr
- [**shell-history**](adapters/stdlib/shell-history/) — Your bash, zsh and fish history: what you ran, and when the shell recorded it. *new* `no-install` `offline` `bash` `fish` · near: jrnl, subtitles, shell
- **sigmap** (idea) — SigMap's signature map of a codebase as plain text: each function's signature with its file and line, for questions about the code. *new* `no-install` `offline` `codebase` `function` · near: codebase-memory, code-comments, by-function
- **signal** (idea) — A Signal backup, decrypted with its passphrase, as one dated line per message. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `message` `backup` · near: texts, teams, chats
- [**slack**](adapters/stdlib/slack/) — Slack's export zip: one dated line per message, with channel and author. *new* `no-install` `offline` `message` `channel` · near: irc, matrix, chats
- [**snapshot**](adapters/stdlib/snapshot/) — A web page or data file fetched once into a folder, as it came, with its address, the time and its SHA-256, so later answers cite the copy. Goes online: the address you give, fetched once. *bot* `no-install` `online` `snapshot` `copy` `sources` · near: web-pages, wayback, policy-watch
- [**star-system**](adapters/deps/star-system/) — A friend's star-system simulation (science_bitch) run deterministically and written as cited passages: each body's Kepler period and how well the run conserves energy, angular momentum and linear momentum. Needs numpy; BSD-3-Clause. *bot* `needs-install` `offline` · near: static-search, manifests, ripgrep
- **steam** (idea) — Your Steam library from its local files: games, playtime and when you last played. *new* `no-install` `offline` `game` `library` · near: life, game-master, music-library
- **strava** (idea) — Strava's export and GPX files: each run, ride and walk as a dated line with its distance and time. *new* `no-install` `offline` · near: habits, instapaper, weights-pin
- [**subtitles**](adapters/stdlib/subtitles/) — Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed. *new* `no-install` `offline` `transcript` · near: shell-history, calendar, mail
- **takeout** (idea) — Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines. *new* `no-install` `offline` `html` `takeout` · near: matrix, google-classroom, google-keep
- **teams** (idea) — Microsoft Teams chats from your Microsoft account's export, one dated line per message. *new* `no-install` `offline` `message` `chats` · near: chats, signal, texts
- [**texts**](adapters/stdlib/texts/) — Phone text messages, from an Android SMS backup or an iPhone backup's copy, one dated line per message. *new* `no-install` `offline` `message` `backup` · near: chats, slack, irc
- [**trello**](adapters/stdlib/trello/) — A Trello board's JSON export: cards, checklists and comments, by list. *new* `no-install` `offline` `comments` `json` · near: karakeep, day-one, reddit
- **voice** (idea) — Dictation, calls and lectures transcribed into dated text. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `transcribed` `voice` · near: writefreely, texts, calendar
- [**wallabag**](adapters/stdlib/wallabag/) — wallabag's JSON or HTML export: saved entries as plain text, with their tags. *new* `no-install` `offline` `highlights` `tags` · near: karakeep, readwise, evernote
- **warc** (idea) — WARC web archives, from Webrecorder, Heritrix or the Internet Archive, read without unpacking: each captured page's text with its address and the time it was captured. *new* `no-install` `offline` `address` `unpacking` · near: gitlab-export, joplin, archivebox
- [**web-pages**](adapters/stdlib/web-pages/) — Saved web pages, .html and .mhtml, as their readable text, with the address they came from. *new* `no-install` `offline` `address` `web` · near: snapshot, pdf, photos
- **writefreely** (idea) — WriteFreely posts, from its export or a copy of its SQLite database, as dated text. *new* `no-install` `offline` `copy` `sqlite` · near: bookmarks, apple-notes, nestor
- [**x-archive**](adapters/stdlib/x-archive/) — An X (Twitter) archive: your posts, replies and DMs as dated lines. *new* `no-install` `offline` `posts` `message` · near: meta-archive, mastodon, linkedin
- **zotero** (idea) — Your Zotero library, from a copy of zotero.sqlite: items, notes and PDF annotations, each with its citation. *new* `no-install` `offline` `copy` `sqlite` · near: annotations, apple-notes, writefreely

## Finding things

- [**all**](adapters/stdlib/all/) — Every matching passage, ranked, not just the top three. *box* `no-install` `offline` `ranked` `matched` · near: latent, claim-check, thesis
- [**amounts**](adapters/stdlib/amounts/) — Every sum of money in your files, with its date and the line it's on. *new* `no-install` `offline` `amount` · near: debts, said, todo
- **bm25** (idea) — BM25 over a box in one go, with no index to build first: the rank scan --rank bm25 gives, for a folder you ask once. *new* `no-install` `offline` `index` `scan` · near: scan, index-cache, latent
- **by-function** (idea) — Code read by function and class instead of by line, so a hit names the function it's in. Needs tree-sitter and its language pack; MIT. *new* `needs-install` `offline` `function` `instead` · near: codebase-memory, risky-code, claude-code
- **code-first** (idea) — Questions code can answer exactly (counts, dates, ids) answered by code before any model, with a wrong answer counted as a defect. *bot* `no-install` `offline` · near: model-exam, llm-cli, sigmap
- [**code-shape**](adapters/deps/code-shape/) — Search code by its shape, not its words: every call of a kind, whatever it's named. Needs the ast-grep program, from ast-grep-cli on PyPI or your own ast-grep; MIT. *new* `needs-install` `offline` `search` · near: dialect, stems, ocr
- [**codeowners**](adapters/stdlib/codeowners/) — Who owns this file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo alike. *new* `no-install` `offline` `gitlab` `github` · near: claude-code, gitlab, across
- **crosswalk** (idea) — The outside IDs a passage points to (Wikidata, DOI, ORCID, GeoNames) kept beside it, so your notes join the world's. *new* `no-install` `offline` `beside` `joins` · near: ids, translate, joins
- [**duplicates**](adapters/stdlib/duplicates/) — Passages that say the same thing in two files, and which one is newer. *new* `no-install` `offline` · near: contradictions, xref, three-two-one
- [**fair-merge**](adapters/stdlib/fair-merge/) — Each folder or repo ranked on its own and the lists merged in turns, so a large corpus can't push a small one out on volume alone, and a source that found nothing says so. *bot* `no-install` `offline` `sources` `pile` · near: scan, parallel, ripgrep
- [**first-mention**](adapters/stdlib/first-mention/) — When your files first mention something, and the line that does. *new* `no-install` `offline` `mention` · near: people, timeline, pipe
- [**fuzzy-dates**](adapters/stdlib/fuzzy-dates/) — Dates that admit doubt ('about 1880', 'sometime in March') read and kept with their doubt, in EDTF. *new* `no-install` `offline` · near: family-tree, syllabus, minutes
- [**index-cache**](adapters/stdlib/index-cache/) — Keeps scan's index between runs and rebuilds it only when a file in your folder actually changed. *new* `no-install` `offline` `between` `scan` `index` · near: scan, parallel, policy-watch
- **kiwix** (idea) — An offline Wikipedia (or Stack Exchange, or Gutenberg) as a source after your own files, cited by article. Needs libzim, and a ZIM file you download; GPL-3.0. *new* `needs-install` `offline` `stack` `wikipedia` · near: pageviews, codeowners, stack
- [**latent**](adapters/deps/latent/) — Finds code by meaning, not just matching words, using scan's index: a question reaches code that says the same thing another way. Needs numpy; BSD-3-Clause. *new* `needs-install` `offline` `matched` `ranked` · near: scan, all, pile-rank
- **meaning** (idea) — Search by meaning: "who owes me money" finds "invoice outstanding". Needs sentence-transformers; Apache-2.0. Goes online: the model, downloaded once from Hugging Face. *new* `needs-install` `online` `invoice` `owes` · near: amounts, starter-words, debts
- [**misquote**](adapters/stdlib/misquote/) — A quote that is almost in your files: the closest passage, and the words it adds, drops or changes, so a misquote shows as one. *new* `no-install` `offline` `quote` `drops` · near: quotes, quote-check, nightstand
- [**month-first**](adapters/stdlib/month-first/) — For a folder you know writes dates month first: each one's ISO form written beside it, so it can be placed. *new* `no-install` `offline` `month` `form` · near: abbreviations, chats, coming-up
- **my-lessons** (idea) — Your own lesson plans by grade, subject and standard: what did I teach on fractions last year? *new* `no-install` `offline` `lesson` `plan` · near: lessons, lesson-time, standards
- [**on-this-day**](adapters/stdlib/on-this-day/) — What you wrote on this date in earlier years. *box* `no-install` `offline` · near: coming-up, surprise, serve
- [**people**](adapters/stdlib/people/) — Everyone your files name, and every place each is mentioned. *new* `no-install` `offline` `mention` · near: first-mention, life, catgrid
- [**pile-build**](adapters/stdlib/pile-build/) — Rebuilds pile-store's saved passages after each change, one build at a time, so your next question doesn't wait for it. *bot* `no-install` `offline` `store` `pile` · near: pile-store, pile-serve, predict
- [**pile-gold**](adapters/stdlib/pile-gold/) — Your approved answers used as a test: each question asked again, scored by how often the search puts the passage that held it in its top five. *box* `no-install` `offline` `search` `pile` · near: again, pile-store, pile-sweep
- [**pile-rank**](adapters/stdlib/pile-rank/) — Finds passages that use your folder's own phrases ("sourdough bread"), not just the separate words, ranked without any AI model. *bot* `no-install` `offline` `phrases` `ranked` `pile` · near: pile-rungs, pile-serve, all
- [**pile-rungs**](adapters/stdlib/pile-rungs/) — Tries the strict word match first, then your folder's phrases, and says which one found the answer and why the others didn't. *bot* `no-install` `offline` `matched` `phrases` `pile` · near: pile-rank, pile-serve, pile-store
- [**pile-serve**](adapters/stdlib/pile-serve/) — Keeps your folder's search ready in one background process on this machine, so a hook's lookup answers in milliseconds instead of seconds. *bot* `no-install` `offline` `second` `store` `pile` · near: pile-rank, pile-rungs, pile-store
- [**pile-store**](adapters/stdlib/pile-store/) — Your folder's passages kept in one file between questions, used only while the folder hasn't changed, so other add-ons don't re-read it every time. *bot* `no-install` `offline` `store` `pile` · near: pile-serve, pile-build, pile-sweep
- [**pile-sweep**](adapters/stdlib/pile-sweep/) — Finds the passage length that suits your folder, by asking your own answered questions at several lengths and naming the one that finds the most. *bot* `no-install` `offline` `pile` · near: pile-store, pile-gold, pile-rank
- **promises** (idea) — What a candidate or a council said, by date and source, from the documents you saved. *new* `no-install` `offline` `saved` `council` · near: said, thesis, timeline
- [**quote-check**](adapters/stdlib/quote-check/) — Is this exact quote in my files, and where? For writers, journalists and students. *box* `no-install` `offline` `quote` · near: quotes, claim-check, xref
- [**quotes**](adapters/stdlib/quotes/) — Every quote in a document checked against your files: as written, almost (and what it adds, drops or changes), or not there. *new* `no-install` `offline` `quote` `drops` · near: misquote, quote-check, claim-check
- [**reading-level**](adapters/stdlib/reading-level/) — How hard a passage reads (sentence length, word length, Flesch), so a teacher can find texts for a class. *new* `no-install` `offline` `length` `sentence` · near: plain, pile-sweep, browse
- [**record-sql**](adapters/deps/record-sql/) — SQL straight over your record, in place: 'how many answers did I approve in March?' Needs DuckDB; MIT. *box* `needs-install` `offline` · near: mcp, static-search, dialect
- **rerank** (idea) — A small model on the CPU that reorders the top passages by reading the question and each passage together. Needs FlashRank; Apache-2.0. Goes online: the model, downloaded once. *new* `needs-install` `online` `top` · near: claude-code, pile-gold, all
- [**ripgrep**](adapters/deps/ripgrep/) — Exact search through ripgrep, much faster on a big folder, its hits checked against the kernel's hashes. Needs the ripgrep program, from the ripgrep wheel on PyPI or your own rg; MIT or Unlicense. *new* `needs-install` `offline` `search` · near: pdf, manifests, ocr
- [**rules**](adapters/stdlib/rules/) — A game's or a house's rules, approved one section at a time, so asking what a rule says gives back that exact section, word for word. *bot* `no-install` `offline` `game` · near: session-seal, game-master, browse
- [**said**](adapters/stdlib/said/) — Your own quotes, gathered: every 'so-and-so, on this date: "..."' in your files, as a dated timeline of what was decided. *new* `no-install` `offline` `quote` `timeline` · near: amounts, timeline, todo
- [**scan**](adapters/stdlib/scan/) — Index a big folder once, then ask it a list of questions in seconds, with the kernel's own answers: of everything, or only what changed since another index. *box* `no-install` `offline` `scan` `ranked` `index` · near: latent, index-cache, bm25
- **standards** (idea) — Curriculum standards beside your lessons: which standard each lesson meets, each cited. *new* `no-install` `offline` `lesson` `standard` · near: my-lessons, lesson-time, grant-report
- [**surprise**](adapters/stdlib/surprise/) — One passage from your folder at random, seeded so it can be replayed. *bot* `no-install` `offline` `seeded` `replayed` · near: on-this-day, serve, tarot
- **symbols** (idea) — Exact definitions and references for Python code: where a name is defined, and every place it's used. Needs scip-python; MIT. *new* `needs-install` `offline` `reference` · near: hook-impact, people, code-shape
- [**typos**](adapters/stdlib/typos/) — Forgives misspellings in questions. *new* `no-install` `offline` · near: accents, abbreviations, again
- **upgrade-notes** (idea) — Before an upgrade: the changelog lines between the version you lock and the one you'd move to, from the package's own files. Goes online: the registry (PyPI, npm or crates.io), to fetch the newer version's changelog. *new* `no-install` `online` `package` `version` · near: lockfiles, package-contents, install-scripts
- **vectors** (idea) — The meaning add-on's vectors kept in the store's own SQLite file, so they're computed once per passage, not at every question. Needs sqlite-vec and model2vec; MIT or Apache-2.0. *bot* `needs-install` `offline` `sqlite` `store` `pile` · near: pile-store, codebase-memory, welcome
- **watch** (idea) — A file re-read the moment it changes (inotify, FSEvents, or polling), so the index is always current. *new* `no-install` `offline` `index` `moment` · near: index-cache, scan, policy-watch
- [**why-not**](adapters/stdlib/why-not/) — When the answer is 'not enough to say', which words found nothing, and what kind of file would have answered. *new* `no-install` `offline` · near: nicknames, scan, daily-word

## Your own words

The blind tests' biggest gap: on day one, a person's words aren't their files' words.

- [**abbreviations**](adapters/stdlib/abbreviations/) — Your own shorthand, written down once (appt, Rx, w/c), so a question finds either form. *new* `no-install` `offline` `form` `down` · near: accents, stems, month-first
- [**accents**](adapters/stdlib/accents/) — A word typed without its accent read as your files write it, and the words-list lines that make it last. *new* `no-install` `offline` · near: abbreviations, stems, typos
- [**dialect**](adapters/deps/dialect/) — The words you use far more than the world does: your own dialect, from your files against wordfreq's counts. Needs wordfreq; Apache-2.0, its data CC BY-SA 4.0. *new* `needs-install` `offline` · near: code-shape, stems, record-sql
- **memoir** (idea) — A question a week about your life, answered in your own words and kept, so your story is in your files. *new* `no-install` `offline` `life` · near: quiz, browse, why-not
- [**nicknames**](adapters/stdlib/nicknames/) — The names you call people, mapped to who they are, so 'Mum' finds Margaret. *new* `no-install` `offline` `starter` · near: starter-words, abbreviations, notes
- [**starter-words**](adapters/stdlib/starter-words/) — A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic). *new* `no-install` `offline` `copy` `starter` · near: start, snapshot, pdf
- [**stems**](adapters/deps/stems/) — Word forms for 20+ languages, so "häuser" finds "haus" and "книги" finds "книга". Needs snowballstemmer; BSD-3-Clause. *new* `needs-install` `offline` `form` · near: accents, abbreviations, ocr
- **synonyms** (idea) — Suggests words-list lines for a word no file has. Needs nltk and WordNet; Apache-2.0. Goes online: the WordNet data, downloaded once. *new* `needs-install` `online` · near: accents, starter-words, abbreviations
- **tatoeba** (idea) — A question in one language finds the same idea in another, through Tatoeba's sentence pairs, downloaded once. *new* `no-install` `offline` `pairs` `language` · near: why-not, stems, latent
- **vocab** (idea) — The words you're learning, from your notes and the texts you read, with where you met each one. *new* `no-install` `offline` · near: apple-notes, oracle-text, starter-words
- [**words-ar**](adapters/stdlib/words-ar/) — Arabic common words ("في", "من", "على"). *new* `no-install` `offline` `common` `arabic` · near: words-it, words-pl, words-pt
- [**words-cy**](adapters/stdlib/words-cy/) — Welsh common words ("a", "y", "yn"). *new* `no-install` `offline` `common` `welsh` · near: words-it, words-es, words-pl
- [**words-de**](adapters/stdlib/words-de/) — German common words, so questions aren't matched on "der" and "und". *new* `no-install` `offline` `common` `german` · near: words-nl, words-pl, words-it
- [**words-es**](adapters/stdlib/words-es/) — Spanish common words ("el", "y"). *new* `no-install` `offline` `common` `spanish` · near: words-it, words-pt, words-cy
- [**words-fr**](adapters/stdlib/words-fr/) — French common words ("le", "et"). *new* `no-install` `offline` `common` `french` · near: words-it, words-pl, words-pt
- **words-hi** (idea) — Hindi common words ('और', 'है'). *new* `no-install` `offline` `common` · near: words-ja, words-zh, words-it
- [**words-it**](adapters/stdlib/words-it/) — Italian common words ("il", "e"). *new* `no-install` `offline` `common` `italian` · near: words-pt, words-tlh, words-es
- **words-ja** (idea) — Japanese, which has no spaces: a small segmenter of its own and a common-words list. *new* `no-install` `offline` `common` `segmenter` · near: words-zh, words-hi, synonyms
- [**words-nl**](adapters/stdlib/words-nl/) — Dutch common words ("de", "en"). *new* `no-install` `offline` `common` `dutch` · near: words-de, words-it, words-pl
- [**words-pl**](adapters/stdlib/words-pl/) — Polish common words ('i', 'w'). *new* `no-install` `offline` `common` `polish` · near: words-it, words-de, words-pt
- [**words-pt**](adapters/stdlib/words-pt/) — Portuguese common words ("o", "e"). *new* `no-install` `offline` `common` `portuguese` · near: words-it, words-tlh, words-es
- [**words-ru**](adapters/stdlib/words-ru/) — Russian common words ("и", "в", "на"). *new* `no-install` `offline` `common` `russian` · near: words-it, words-pl, words-pt
- [**words-sv**](adapters/stdlib/words-sv/) — Swedish common words ('och', 'att'). *new* `no-install` `offline` `common` `swedish` · near: words-it, words-pl, words-pt
- [**words-tlh**](adapters/stdlib/words-tlh/) — Klingon common words ("'ej", "nuq"). *new* `no-install` `offline` `common` `klingon` · near: words-it, words-pt, words-pl
- [**words-tr**](adapters/stdlib/words-tr/) — Turkish common words ("ve", "bir"). *new* `no-install` `offline` `common` `turkish` · near: words-it, words-pl, words-pt
- **words-zh** (idea) — Chinese, which has no spaces: words found by a small segmenter of its own, and a common-words list. *new* `no-install` `offline` `common` `segmenter` · near: words-ja, words-hi, synonyms

## Keeping track

- [**again**](adapters/stdlib/again/) — Questions you keep asking: "asked 4 times; approve an answer?" *bot* `no-install` `offline` `counts` · near: export, pile-gold, history
- **ask-later** (idea) — A question with no answer yet kept on a list, and asked again whenever a new file arrives. *new* `no-install` `offline` · near: pile-gold, model-drift, flashcards
- [**attendance**](adapters/stdlib/attendance/) — Attendance for a class, club or group, from your register, by week. *new* `no-install` `offline` `week` · near: gradebook, symptoms, syllabus
- [**baby-log**](adapters/stdlib/baby-log/) — Feeds, sleeps and nappies from your notes, by day: when was the last one? *new* `no-install` `offline` `log` · near: milestones, mood, syllabus
- [**budget**](adapters/stdlib/budget/) — Spending against the budget you wrote down, month by month, from your statements. *new* `no-install` `offline` `month` `statements` · near: mood, baby-log, reading-log
- [**car**](adapters/stdlib/car/) — Your car's services, repairs and inspection dates, from receipts and notes: what's due, and what it cost. *new* `no-install` `offline` `due` `receipts` · near: home-upkeep, pets, subscriptions
- **care** (idea) — For caregivers: medications, vitals and appointments from a care log, what's due and what moved. *box* `no-install` `offline` `car` `due` · near: car, coming-up, bluesky
- [**coming-up**](adapters/stdlib/coming-up/) — Dates written in your files in the next N days: appointments, renewals, deadlines. *box* `no-install` `offline` `coming` `days` · near: calendar-out, digest, on-this-day
- **contracts** (idea) — The dates that matter in your contracts: renewals, notice periods and break clauses, each cited. *new* `no-install` `offline` `break` `contracts` · near: clauses, support-plan, mutants
- **crowd** (idea) — You against the crowd: a prediction market's question copied into your ledger, your probability beside theirs, both scored. Goes online: the market's public API, to read the question and its resolution. *new* `no-install` `online` `prediction` `score` · near: predictions, oakenscroll, market-calls
- **cycle** (idea) — A menstrual cycle log that never leaves this machine: dates, what's next, and what changed. *new* `no-install` `offline` `log` · near: coming-up, silence-log, sent-log
- [**debts**](adapters/stdlib/debts/) — Who owes whom, from the IOUs in your notes and messages, each cited. *new* `no-install` `offline` · near: amounts, symptoms, renewals
- [**digest**](adapters/stdlib/digest/) — One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that keep finding nothing. *bot* `no-install` `offline` `coming` `stale` `everyday` · near: coming-up, hook-start, browse
- [**flashcards**](adapters/stdlib/flashcards/) — Approved question-and-answer pairs become cards, scheduled by spaced repetition. *box* `no-install` `offline` · near: jeles, ask-later, hook-compact
- [**foia**](adapters/stdlib/foia/) — Freedom-of-information requests: what you asked, when, and when the answer is due by law. *new* `no-install` `offline` `due` · near: home-upkeep, subscriptions, mood
- **food-log** (idea) — What you ate, from your notes, by day. *new* `no-install` `offline` `log` · near: gaps, baby-log, reading-log
- [**forecasts**](adapters/stdlib/forecasts/) — Write a prediction before the outcome, settle it later with your seal, see your Brier score. *bot* `no-install` `offline` `brier` `forecast` · near: market-calls, predict, weather-bet
- [**gaps**](adapters/stdlib/gaps/) — Where a log you keep stops: the days a daily note, reading or diary skipped, said as gaps, not left out. *new* `no-install` `offline` `gaps` `daily` `journal` · near: on-this-day, folder-card, serve
- [**garden**](adapters/stdlib/garden/) — What you planted, where and when, and how it did, season by season. *new* `no-install` `offline` · near: home-upkeep, pets, mileage
- **gifts** (idea) — Gifts given and received, and who likes what, so nobody gets the same scarf twice. *new* `no-install` `offline` `twice` · near: hook-replay, repro, opentimestamps
- [**gradebook**](adapters/stdlib/gradebook/) — A teacher's gradebook, kept on this machine: each student's marks by assignment, and who is falling behind. *new* `no-install` `offline` `assignments` · near: syllabus, attendance, reading-log
- **grant-report** (idea) — For charities and groups: what you promised a funder and what you did, side by side, each cited. *new* `no-install` `offline` · near: second-opinion, contradictions, standards
- [**habits**](adapters/stdlib/habits/) — Streaks from the lines you write each day: how many days in a row, and which you missed. *new* `no-install` `offline` · near: pets, renewals, car
- [**home-upkeep**](adapters/stdlib/home-upkeep/) — Home upkeep: the boiler service, the filters, the gutters, what's due and when it was last done. *new* `no-install` `offline` `due` `service` · near: car, pets, garden
- [**hours**](adapters/stdlib/hours/) — Hours worked or volunteered, per client or group, from your notes. *new* `no-install` `offline` `group` · near: symptoms, mood, baby-log
- **inventory** (idea) — What you own, where it is, and where its papers are, for insurance or a will. *new* `no-install` `offline` `paper` `insurance` · near: paper-key, past-papers, renewals
- [**invoices**](adapters/stdlib/invoices/) — For freelancers: invoices and payments matched by the id pattern you give, never guessed. *new* `no-install` `offline` `pattern` `matched` · near: serve, privacy, on-this-day
- [**job-hunt**](adapters/stdlib/job-hunt/) — Applications sent, replies and interviews, by date: who you're still waiting on. *new* `no-install` `offline` · near: mood, warranties, foia
- **lab-notebook** (idea) — A lab notebook's dated entries, by sample and experiment: what was done to what, and when. *new* `no-install` `offline` `entries` `sampling` · near: joplin, mcp-sampling, journiv
- [**lending**](adapters/stdlib/lending/) — Things you lent, to whom and when, and which are still out. *new* `no-install` `offline` · near: on-this-day, xref, licenses
- [**lesson-time**](adapters/stdlib/lesson-time/) — Lesson plans whose timed parts don't add up to the time the plan says it takes, each part's minutes shown beside the total. *new* `no-install` `offline` `lesson` `plan` `teaching` · near: make-it-so, test-impact, my-lessons
- [**livestock**](adapters/stdlib/livestock/) — Each animal's births, treatments and sales, from your farm records. *new* `no-install` `offline` · near: calendar-out, hook-impact, habits
- [**market-calls**](adapters/stdlib/market-calls/) — Market calls kept as wagers on the record ('SPY closes up on Friday'), settled later by your seal, with the losers kept. *bot* `no-install` `offline` `settled` `calls` · near: forecasts, predict, car
- [**mileage**](adapters/stdlib/mileage/) — Miles driven for work, from your trips and notes, totalled for a tax year. *new* `no-install` `offline` `tax` `work` · near: garden, home-upkeep, hours
- [**milestones**](adapters/stdlib/milestones/) — Your child's firsts, words and heights, from your notes, by age. *new* `no-install` `offline` `child` · near: baby-log, syllabus, minutes
- [**minutes**](adapters/stdlib/minutes/) — Meeting minutes: who decided what and when, and which actions are still open. *new* `no-install` `offline` `minutes` `due` · near: syllabus, foia, reading-log
- [**mood**](adapters/stdlib/mood/) — Mood scores you write in a journal, over weeks and months. *new* `no-install` `offline` `week` · near: job-hunt, foia, baby-log
- [**nightstand**](adapters/stdlib/nightstand/) — Set heavy things down at night and pick up just one small next step in the morning: at most one thing in hand, and nothing ever deleted. *new* `no-install` `offline` `step` · near: start, all, game-master
- [**pets**](adapters/stdlib/pets/) — Each pet's vet visits, vaccines and medicines, from your records: what's due next. *new* `no-install` `offline` `due` · near: home-upkeep, car, garden
- [**policy-watch**](adapters/stdlib/policy-watch/) — A terms or policy page fetched each time you run it, by snapshot, and what changed since last time, sentence by sentence, by clauses. Goes online: the page you name, fetched each time you run it. *new* `no-install` `online` `snapshot` `clauses` `policies` · near: snapshot, clauses, wayback
- [**predict**](adapters/stdlib/predict/) — Write down what a question will come to before you ask it, and grade it after; the record counts how often it was right. *bot* `no-install` `offline` `down` `score` · near: forecasts, pile-gold, again
- [**reading-log**](adapters/stdlib/reading-log/) — A child's reading log: books, pages and minutes, week by week. *new* `no-install` `offline` `week` `minutes` · near: foia, baby-log, attendance
- [**readings**](adapters/stdlib/readings/) — Two hints beside an answer: a number in your files that moved a lot lately, and a date in a log that passed with nothing written since. *box* `no-install` `offline` `numbers` · near: plain, privacy, coming-up
- [**renewals**](adapters/stdlib/renewals/) — Passports, licences, insurance and memberships: when each expires, from your documents. *new* `no-install` `offline` · near: warranties, symptoms, attendance
- **rubric** (idea) — Marking against a rubric you wrote: each mark cites the criterion and the line of work it's for. *new* `no-install` `offline` `mark` `work` · near: gradebook, symptoms, weakest-link
- **school** (idea) — School letters and emails for parents: trips, forms due, term dates, and what to bring. *new* `no-install` `offline` `trips` `parent` · near: trips, month-first, support-plan
- [**session-cost**](adapters/stdlib/session-cost/) — Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep. *new* `no-install` `offline` `agent` `session` · near: agent-transcript, corpus-lens, line-origin
- [**subscriptions**](adapters/stdlib/subscriptions/) — What you pay for every month, found in bank statements and emails, and when each renews. *new* `no-install` `offline` `month` `statements` · near: foia, pets, home-upkeep
- **support-plan** (idea) — An IEP or support plan's goals, accommodations and review dates, each cited, for a parent or teacher. *new* `no-install` `offline` `parent` `plan` · near: contracts, lessons, standards
- [**syllabus**](adapters/stdlib/syllabus/) — A course syllabus as dates: readings, assignments and exams due, each cited. *new* `no-install` `offline` `assignments` `due` · near: gradebook, minutes, symptoms
- [**symptoms**](adapters/stdlib/symptoms/) — A symptom diary over time, ready to show a doctor: what, when, how bad, each line cited. *new* `no-install` `offline` · near: syllabus, hours, attendance
- **tax-year** (idea) — One tax year's receipts and statements gathered in one place, each with the file it came from. *new* `no-install` `offline` `tax` `statements` · near: mileage, todays-place, upstream-desk
- [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first. *box* `no-install` `offline` · near: amounts, said, nightstand
- **trips** (idea) — Your trips from booking emails and tickets: where you went, when, and where you stayed. *new* `no-install` `offline` `trips` `emails` · near: school, mileage, books
- **upstream-desk** (idea) — Your work in other people's projects, in one place: notifications sorted into what needs you, and your open pull requests there. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `pull` `requests` · near: contribute, pr-context, welcome
- [**warranties**](adapters/stdlib/warranties/) — Receipts and warranties: when the dishwasher's cover ends, and where its receipt is. *new* `no-install` `offline` `receipts` · near: job-hunt, renewals, baby-log

## Trust and proof

- [**backup**](adapters/stdlib/backup/) — Your record in one zip, every byte and the chain checked before it's kept; never beside your key, and it never reads the key. *new* `no-install` `offline` `chain` `backup` `everyday` · near: diverge, three-two-one, restore-drill
- [**box-health**](adapters/stdlib/box-health/) — Is your willow all right? One line: files it can't read, readers out of date, and when its record was last checked. *new* `no-install` `offline` · near: changed, tip-pin, pipe
- [**changed**](adapters/stdlib/changed/) — What's new, edited or deleted in your folder since the last check, as fingerprint rows. *bot* `no-install` `offline` `edit` `rows` `everyday` · near: box-health, policy-watch, stale
- [**claim-check**](adapters/stdlib/claim-check/) — A claim checked against your sources: the passages that hold all of its parts, the ones that hold only some, and the parts no file names. *new* `no-install` `offline` `claim` `top` · near: thesis, all, typosquat
- [**contradictions**](adapters/stdlib/contradictions/) — Two passages that disagree about the same date or amount, side by side. *new* `no-install` `offline` `amount` · near: duplicates, joins, amounts
- [**decisions**](adapters/stdlib/decisions/) — A recorded no with its reason and the condition that would reopen it, so a rejection is kept, not forgotten. *new* `no-install` `offline` · near: again, pile-sweep, predict
- [**diverge**](adapters/stdlib/diverge/) — Where two copies part, your record and its backup zip or two copies of a folder, down to the first row, file and line that differ. *bot* `no-install` `offline` `backup` `zip` `everyday` · near: backup, three-two-one, restore-drill
- **encrypt** (idea) — Keeps the record folder encrypted at rest. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `rest` · near: make-it-so, almanac-keep, google-keep
- [**export**](adapters/stdlib/export/) — Approved answers, and the question log (counts only, never words), as Markdown or CSV. *box* `no-install` `offline` `counts` · near: again, history, pgp
- **family-box** (idea) — One box for a household: each person's own seal, and every answer showing whose it is. *new* `no-install` `offline` `person` `family` · near: second-opinion, dialect, handoff
- [**fixity**](adapters/stdlib/fixity/) — Your folder's files hashed again now and then, the hashes kept on the record, and a file that changed with no edit of yours flagged as rot. *new* `no-install` `offline` `rot` `flagged` · near: hook-replay, hook-pin, changed
- [**format-rot**](adapters/stdlib/format-rot/) — Files in formats that may stop opening (old office files, proprietary ones, those no reader handles) flagged while you can still convert them. *new* `no-install` `offline` `office` `rot` · near: office, fixity, sheets
- **git-notes** (idea) — Approved answers kept as git notes on the commits they cite, so they travel with the repo to any forge. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `commit` `forge` · near: mirror, stale, git-history
- **handoff** (idea) — A box handed to the person you name (an executor, a carer): read only, your seals kept, theirs their own. *new* `no-install` `offline` `person` · near: family-box, datasette, serve
- [**history**](adapters/stdlib/history/) — Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words. *new* `no-install` `offline` `counts` `sentence` `everyday` · near: export, again, plain
- [**ids**](adapters/stdlib/ids/) — Every file and passage given its Software Heritage ID and IPFS CID, names the rest of the world already uses. *new* `no-install` `offline` `world` `ids` · near: dialect, a11y-check, ripgrep
- **in-case** (idea) — A letter for the people you trust, if something happens to you: where things are and who to call, from your files, sealed by you. *new* `no-install` `offline` `people` `trust` · near: witness, model-exam, people
- [**in-toto**](adapters/stdlib/in-toto/) — A sealed answer exported as an in-toto Statement, the envelope SLSA uses, so others can check it. *new* `no-install` `offline` `envelope` `tool` · near: annotations, ro-crate, prov
- [**jeles**](adapters/stdlib/jeles/) — Your approved answers as Jeles nuggets, with question, answer, sources and who sealed it, and Jeles' own verified nuggets read back as passages. *new* `no-install` `offline` `sources` · near: oakenscroll, almanac, pile-gold
- [**licenses**](adapters/stdlib/licenses/) — The licence of every installed dependency, read from its own metadata on this machine: which are copyleft, and which file says so. *new* `no-install` `offline` `dependency` · near: claude-code, lending, on-this-day
- **line-origin** (idea) — Which agent session wrote this line of code: git blame to the commit, then the transcript turn that made it. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `agent` `transcript` · near: agent-transcript, session-cost, transcript-redact
- **losc** (idea) — Does a project pass the Local Only Servers Club's test: no accounts, no cloud, and your data your own? *bot* `no-install` `offline` `account` `server` · near: local-model, github-archive, discord
- [**merkle**](adapters/stdlib/merkle/) — A Merkle tree over the record, so one row can be proven with a handful of hashes, not the whole file. *new* `no-install` `offline` `hash` `rows` · near: ci, hook-replay, hosts
- **mirror** (idea) — Checks each mirror of a repo on another forge holds the same commits as the original, so losing a host loses nothing. Needs the git program; GPL, called not linked. Goes online: each mirror's git URL, to read its refs. *new* `needs-install` `online` `commit` `repo` · near: repro, git-notes, provenance
- **model-recall** (idea) — Every sealed answer a model suggested, listed for a second look once you mark its card as flawed; nothing is unsealed for you. *new* `no-install` `offline` `second` `suggested` · near: openai-compatible, share, scan
- [**nestor**](adapters/stdlib/nestor/) — Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when. *new* `no-install` `offline` `sqlite` `copy` · near: codebase-memory, bookmarks, bibtex
- **notary** (idea) — The record's newest hash timestamped by an outside time server, so anyone can see it existed by then. Goes online: an RFC 3161 time server you choose, sent only the hash. *new* `no-install` `online` `hash` `existed` · near: opentimestamps, persona-card, three-two-one
- **opentimestamps** (idea) — The record's newest hash anchored by OpenTimestamps, proof that it existed by a given block. Goes online: the OpenTimestamps calendars, sent only the hash. *new* `no-install` `online` `hash` `existed` · near: notary, merkle, fight5e
- [**pair-drift**](adapters/stdlib/pair-drift/) — Figures a summary says that its full text doesn't: a draft and its packet side by side, ranges and billions read as written. *new* `no-install` `offline` `ranges` `pairs` `writing` · near: contradictions, pins, nightstand
- **paper-key** (idea) — Your key printed as words on paper, to keep somewhere safe, and typed back in to restore it. *new* `no-install` `offline` `prints` `key` · near: print, start, ci-cache
- [**pgp**](adapters/deps/pgp/) — Signs exports and reports with your PGP key, verifiable anywhere. Needs the gpg program, run not linked, and python-gnupg; GPL, BSD-3-Clause. *new* `needs-install` `offline` · near: pdf, mcp, photos
- [**prov**](adapters/stdlib/prov/) — The record exported as W3C PROV: what came from what, by which step, sealed by whom. *new* `no-install` `offline` `prov` `tool` · near: cloudevents, annotations, in-toto
- **provenance** (idea) — Checks a package's Sigstore provenance or PyPI attestation names the repo and commit it claims, before you trust it. Needs sigstore; Apache-2.0. Goes online: the registry and Sigstore's log, to fetch the attestation. *new* `needs-install` `online` `trust` `package` · near: pypi, in-toto, sync
- **quote-review** (idea) — A review comment that quotes the repo, checked: does the quoted line still say that at the pull request's head? Goes online: the forge, through the workflow's token, to read the review comments. *new* `no-install` `online` `pull` `requests` · near: github-archive, xref, pr-context
- **redential** (idea) — The bundle redential-cli's scan makes, written to the record before you submit it, so what left your machine can be checked later. Needs the redential program, run through npx; Apache-2.0. *new* `needs-install` `offline` `bundle` `left` · near: report, sent-log, predict
- **report** (idea) — A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. *box* `no-install` `offline` `bundle` `verified` · near: datasette, redential, jeles
- [**restore-drill**](adapters/stdlib/restore-drill/) — A backup zip restored into scratch and verified there, chain and every file, so you know it restores before the day you need it. *new* `no-install` `offline` `zip` `backup` · near: backup, diverge, three-two-one
- **retire** (idea) — Proposes setting aside approved answers that no longer hold, each one gone only when you seal it. *bot* `no-install` `offline` `aside` · near: assistant-scores, stale, plain-language
- [**ro-crate**](adapters/stdlib/ro-crate/) — Your willow (the files it reads, its record and your approved answers) as an RO-Crate research object that Zenodo and similar archives can read. *new* `no-install` `offline` `tool` · near: in-toto, annotations, cloudevents
- **sap-gate** (idea) — The mcp add-on's tool calls checked against SAP/1.0 grants before they run, through openclaw-sap-gate. Needs openclaw-sap-gate; MIT. *new* `needs-install` `offline` `mcp` `tool` · near: mcp-lite, cursor, opencode
- [**session-seal**](adapters/stdlib/session-seal/) — One seal at the end of a session, over everything asked and approved in it: yes, these were my actions. *bot* `no-install` `offline` `end` · near: rules, abbreviations, tip-pin
- **signed-commits** (idea) — Which commits are signed, and by whose key, checked on this machine against the keys you trust. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `trust` `commit` · near: provenance, pgp, model-exam
- [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. *box* `no-install` `offline` `stale` · near: again, export, changed
- **sync** (idea) — Your record kept on two devices through any synced folder, with the chain checked on each before it's trusted. *new* `no-install` `offline` `trust` `chain` · near: backup, model-exam, provenance
- [**thesis**](adapters/stdlib/thesis/) — A thesis's claims, each tied to the source that backs it, and a list of the ones with none. *new* `no-install` `offline` `claim` `top` · near: claim-check, all, surprise
- [**three-two-one**](adapters/stdlib/three-two-one/) — How many verified copies of your record exist and where, held to three copies, on two kinds of storage, one away from home. *new* `no-install` `offline` `zip` `copy` · near: diverge, backup, duplicates
- **time-capsule** (idea) — A note sealed now and opened on a date you choose, with the record proving it wasn't changed. *new* `no-install` `offline` `prov` `open` · near: prov, hook-compact, fixity
- [**timeline**](adapters/stdlib/timeline/) — A dated timeline of one matter (a dispute, an illness, a tenancy), every line cited, to hand to a lawyer, doctor or council. *new* `no-install` `offline` `timeline` · near: said, across, first-mention
- [**tip-pin**](adapters/stdlib/tip-pin/) — Where your record ends, written down somewhere willow can't reach, so rows cut off the end or rewritten from some point on are caught where verify can't. *new* `no-install` `offline` `rows` `pin` · near: ci-memo, ci, persona-card
- [**wayback**](adapters/stdlib/wayback/) — The Wayback Machine's copy of a page from a window of days, saved beside your own snapshot and compared with it byte for byte. Goes online: archive.org, to find the archived copy and fetch it. *new* `no-install` `online` `snapshot` `byte` `sources` · near: snapshot, policy-watch, archivebox
- [**weakest-link**](adapters/stdlib/weakest-link/) — Each answer's inputs marked measured, fitted or assumed, and the result worth its weakest input, never an average. *new* `no-install` `offline` `links` · near: stale, export, jetbrains
- **weights-pin** (idea) — A local model's weights file hashed before each run and refused when it differs from the hash on its model card. *new* `no-install` `offline` `local` `weights` · near: model-card, weights-card, model-fit
- **witness** (idea) — A second person's seal beside yours, for answers that need two people to agree. *new* `no-install` `offline` `beside` `second` · near: second-opinion, model-recall, gutenberg
- [**xref**](adapters/stdlib/xref/) — Every reference in your files checked: each link to another file, and each quoted line, still there and still saying it. *bot* `no-install` `offline` `quote` `everyday` · near: quote-review, quotes, secrets-audit

## Privacy and safety

- [**a11y-check**](adapters/stdlib/a11y-check/) — Your documents checked for screen-reader problems: images without descriptions, headings out of order. *new* `no-install` `offline` `problems` `share` · near: scrub, transcript-redact, mileage
- [**advisories**](adapters/stdlib/advisories/) — Security advisories from a downloaded OSV or GitHub advisory database, matched to your lockfiles: which dependency each names, and since when. *new* `no-install` `offline` `lockfiles` `dependency` · near: outdated, typosquat, pins
- **forget** (idea) — Stops a file being searched, recorded on the chain, so what was taken out is known and nothing else is touched. *new* `no-install` `offline` `taken` `known` · near: ro-crate, merkle, transcript-redact
- [**install-scripts**](adapters/stdlib/install-scripts/) — The install scripts the packages in node_modules would run (preinstall, install, postinstall), each cited by file and line. *new* `no-install` `offline` `install` `package` · near: package-contents, package-docs, code-comments
- **kids** (idea) — A box for a child: answers only from the folder you choose for them, and nothing they can approve. *new* `no-install` `offline` · near: student-records, export, browse
- [**outdated**](adapters/stdlib/outdated/) — How old each locked dependency is, and which are yanked, deprecated or two years without a release, from a registry index you downloaded. *new* `no-install` `offline` `dependency` · near: advisories, typosquat, pins
- [**package-contents**](adapters/stdlib/package-contents/) — What's inside a wheel, sdist, npm tarball or .crate before you install it: every file, and any code it runs on install. *new* `no-install` `offline` `install` `package` · near: install-scripts, ci-cache, launcher
- [**pii-audit**](adapters/stdlib/pii-audit/) — Personal data sitting in your files (ID numbers, health details, card numbers), listed by file and line. *new* `no-install` `offline` `numbers` `audit` · near: secrets-audit, privacy, debts
- [**privacy**](adapters/stdlib/privacy/) — Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. *bot* `no-install` `offline` `numbers` · near: plain, readings, pii-audit
- [**risky-code**](adapters/stdlib/risky-code/) — Lines of code matching a known-dangerous pattern (command injection, eval, sql concatenation, broken tls and more), by file and line, as leads to read. *new* `no-install` `offline` `matched` `command` `security` · near: secrets-audit, advisories, xref
- [**scrub**](adapters/stdlib/scrub/) — Strips the hidden details (EXIF, author, edit history) from a file before you share it. *new* `no-install` `offline` `share` `taken` · near: photos, transcript-redact, a11y-check
- [**secrets-audit**](adapters/stdlib/secrets-audit/) — Finds passwords, keys and card numbers sitting in plain files, by file and line, never showing the value. *bot* `no-install` `offline` `numbers` `key` `everyday` · near: pii-audit, hook-leaks, risky-code
- [**sent-log**](adapters/stdlib/sent-log/) — Which of your passages went to which online model, read from the record by model card: what left this machine and where to. *new* `no-install` `offline` `left` `log` · near: cite-honesty, gaps, model-card
- **student-records** (idea) — A box of student records that answers only the teacher who owns it, and logs every look. *new* `no-install` `offline` `student` `log` · near: kids, ci-why, export
- [**transcript-redact**](adapters/stdlib/transcript-redact/) — An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line. *new* `no-install` `offline` `agent` `paths` · near: scrub, agent-transcript, agents-md-check
- [**typosquat**](adapters/stdlib/typosquat/) — Dependency names a letter off from a popular one (reqeusts, lodahs), checked against a list of top packages you downloaded. *new* `no-install` `offline` `dependency` `package` · near: advisories, outdated, claim-check

## Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal.

- [**aider**](adapters/stdlib/aider/) — Aider reads answers from your folder with its /run command, file and line included. *new* `no-install` `offline` · near: launcher, emacs, browse
- **assistant-scores** (idea) — How often each assistant's suggestions were sealed or set aside, from the record. *new* `no-install` `offline` `score` `assistant` · near: retire, second-opinion, cite-honesty
- **basic-memory** (idea) — Basic Memory's Markdown notes where an AI wrote them: each observation and relation handed in through propose, waiting for your seal. *new* `no-install` `offline` `handed` `propose` · near: memory-import, hermes, hook-feedback
- **bedrock** (idea) — Suggestions from a model on Amazon Bedrock, under your own AWS account and region, citing your passages. Needs boto3; Apache-2.0. Goes online: Amazon Bedrock's endpoint in your region, to ask for suggestions. *new* `needs-install` `online` `citing` · near: cite-honesty, claude, os-model
- **browser-model** (idea) — Suggestions from a model running in your browser, Chrome's built-in model or one run on WebGPU, through a page served on this machine. Reaches this machine only. *new* `no-install` `this-machine` `browser` · near: mlx, os-model, local-model
- **cassettes** (idea) — Each exchange with a model kept as a row (what was asked, what came back, the model and its seed), replayed later as a test, and drift between models found by plain diff. *bot* `no-install` `offline` `rows` `drift` · near: hook-replay, hook-errors, lending
- **cite-honesty** (idea) — How often each model's suggestions were refused at propose for citing a passage the last bite never returned, read from the record by model card. *new* `no-install` `offline` `refuses` `citing` · near: sent-log, model-card, hook-cite
- **claude** (idea) — Suggestions from Claude through the Anthropic API, citing your passages. Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `citing` `claude` · near: claude-code, bedrock, cite-honesty
- [**claude-code**](adapters/stdlib/claude-code/) — Claude Code sees cited passages from your folder with each prompt, through its prompt hook. *bot* `no-install` `offline` `claude` `hook` · near: hooks-elsewhere, hook-impact, vscode
- [**codex-cli**](adapters/stdlib/codex-cli/) — OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` `cli` · near: gemini-cli, cursor, opencode
- [**copilot**](adapters/stdlib/copilot/) — GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on. *new* `no-install` `offline` `mcp` `cli` · near: codex-cli, gemini-cli, cursor
- [**cursor**](adapters/stdlib/cursor/) — Cursor asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` · near: opencode, windsurf, zed
- [**folder-card**](adapters/stdlib/folder-card/) — A card for your folder itself (what the files are, their dates, the gaps you know of), made from your files and your notes and handed to a model as context. *new* `no-install` `offline` `gaps` · near: serve, persona-card, gaps
- [**gemini-cli**](adapters/stdlib/gemini-cli/) — Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` `cli` · near: codex-cli, cursor, opencode
- **hermes** (idea) — Hermes Agent asking your folder as a plugin, and its memories, and what its dreaming plugin consolidates, handed in through propose. *new* `no-install` `offline` `handed` `propose` · near: basic-memory, memory-import, hook-feedback
- **hook-checks** (idea) — A PostToolUse hook that runs the repo's own fast checks on the file just edited and hands back only what failed, the same output for the same file. *new* `no-install` `offline` `failed` `output` `hooks` · near: hook-pin, hook-fail-closed, hook-impact
- **hook-cite** (idea) — A hook that refuses an assistant's claim citing a passage the box never served it, checked against the record by id. *new* `no-install` `offline` `refuses` `assistant` `hooks` · near: claim-check, cite-honesty, hook-read-first
- [**hook-compact**](adapters/stdlib/hook-compact/) — A PreCompact hook that prints what the record still holds open, seals waiting and questions unanswered, so it survives the assistant's summary. *box* `no-install` `offline` `assistant` `open` `hooks` · near: hook-start, browse, flashcards
- **hook-errors** (idea) — Each failed command an assistant runs kept as a row of its hash and exit code, so the same failure the third time is named, not retried blind. *new* `no-install` `offline` `failed` `hash` `hooks` · near: hook-replay, hook-fail-closed, hook-fuzz
- [**hook-fail-closed**](adapters/stdlib/hook-fail-closed/) — Wraps any hook so a crash, a timeout or output it can't read blocks the tool, since Claude Code, Gemini CLI, Codex and Cursor all let the tool run by default. *new* `no-install` `offline` `claude` `gemini` `hooks` · near: hook-fuzz, hooks-elsewhere, agent-transcript
- **hook-feedback** (idea) — Your corrections to an assistant (no, wrong, I said) caught by fixed patterns at each prompt and handed in through propose, for you to keep or drop. *new* `no-install` `offline` `handed` `propose` `hooks` · near: memory-import, basic-memory, hermes
- [**hook-fuzz**](adapters/stdlib/hook-fuzz/) — Throws empty, malformed, oversized and non-UTF-8 input at a hook and fails it if any of them crash it, since a crashed hook lets the tool run. *new* `no-install` `offline` `crash` `failed` `hooks` · near: hook-fail-closed, fuzz, hook-replay
- [**hook-guard**](adapters/stdlib/hook-guard/) — A PreToolUse hook that blocks, by fixed rule and never by judgment, a tool call that would read your key or write willow's record behind its back, naming the rule. *box* `no-install` `offline` `assistant` `pretooluse` `hooks` · near: hook-impact, hook-leaks, hook-read-first
- **hook-handoff** (idea) — A Stop hook that writes where the session ended, and the next session's first prompt gets it back, so nothing rides on the assistant's memory. *new* `no-install` `offline` `assistant` `session` `hooks` · near: hook-stop, memory-import, hook-read-first
- [**hook-impact**](adapters/stdlib/hook-impact/) — Before an edit, a hook hands the assistant every place in your files that names what it's about to change, by file and line. *box* `no-install` `offline` `assistant` `pretooluse` `hooks` · near: hook-read-first, hook-start, hook-stop
- [**hook-leaks**](adapters/stdlib/hook-leaks/) — A PreToolUse hook that refuses a write or a command holding a key, password or card number, by the privacy add-on's shapes, naming only the kind. *box* `no-install` `offline` `key` `pretooluse` `hooks` · near: hook-read-first, hook-impact, hook-guard
- [**hook-pin**](adapters/stdlib/hook-pin/) — Each hook's SHA-256 kept on the record when you approve it, so a hook that changed since is named before it runs, never silently trusted or skipped. *new* `no-install` `offline` `byte` `pin` `hooks` · near: hook-replay, ci-memo, backup
- **hook-read-first** (idea) — A PreToolUse hook that refuses an edit to a file the assistant hasn't read this session, or whose bytes changed since it did, each read kept as a hash. *new* `no-install` `offline` `assistant` `refuses` `hooks` · near: hook-impact, hook-leaks, hook-start
- [**hook-replay**](adapters/stdlib/hook-replay/) — Every hook's answer kept as a row with the hashes of what it was given and what it said, and check runs it again to prove the same input still gets the same answer. *new* `no-install` `offline` `hash` `rows` `hooks` · near: hook-errors, hook-pin, ci
- **hook-sequence** (idea) — Rules over what an assistant did before, not just this call: no push until the tests ran on this commit, at most so many deletions a session, read from the record. *new* `no-install` `offline` `assistant` `rule` `hooks` · near: hook-stop, hook-guard, hook-start
- [**hook-shell**](adapters/stdlib/hook-shell/) — A command split the way the shell will split it, quotes, variables and chained commands included, before any rule judges it, so a rule can't be dodged by spelling. *new* `no-install` `offline` `command` `shell` `hooks` · near: shell, hook-impact, hook-leaks
- [**hook-start**](adapters/stdlib/hook-start/) — A SessionStart hook that hands the assistant what needs you, read the way digest reads it, so opening a session writes nothing. *bot* `no-install` `offline` `assistant` `coming` `hooks` · near: digest, hook-impact, browse
- [**hook-stop**](adapters/stdlib/hook-stop/) — A Stop hook that won't let an assistant's turn end while the record doesn't verify or its changes aren't committed, and says which. *box* `no-install` `offline` `assistant` `end` `hooks` · near: hook-impact, hook-handoff, hook-replay
- **hook-tiers** (idea) — Edits sorted into tiers by the paths they touch, and the top tier held as a proposal until you seal it, by a rule you can read. *new* `no-install` `offline` `rule` `held` `hooks` · near: plain-language, translate, hook-sequence
- **hooks-elsewhere** (idea) — The prompt hook for Gemini CLI, Codex and opencode, wherever they take hooks, held to Claude Code's answer byte for byte. *box* `no-install` `offline` `gemini` `claude` `hooks` · near: claude-code, hook-fail-closed, agent-transcript
- [**hosts**](adapters/stdlib/hosts/) — One table of the assistants that take an MCP server, printing the lines that register willow with any of them. *new* `no-install` `offline` `mcp` `assistant` · near: mcp-lite, zed, mcp
- **in-process** (idea) — Suggestions from a GGUF model loaded inside the add-on itself through llama-cpp-python: no server, no port, nothing listening. Needs llama-cpp-python; MIT; licence of the model varies. *new* `needs-install` `offline` `cpp` `llama` · near: local-model, openai-compatible, browser-model
- [**instruction-files**](adapters/stdlib/instruction-files/) — For a folder, which instruction files each coding agent would load (AGENTS.md, CLAUDE.md, GEMINI.md, rules folders), in what order, with each file's size and hash. *box* `no-install` `offline` `claude` `gemini` · near: agent-transcript, claude-code, agents-md-check
- **issue-answer** (idea) — A workflow that drafts an answer to a new issue from the repo's own docs, each line cited, posted only once a maintainer seals it. Goes online: the forge, through the workflow's token, to post an answer once it is sealed. *new* `no-install` `online` `repo` `docs` · near: hook-checks, repo-index, pr-context
- **ladder** (idea) — Your files first, then sources you trust such as Jeles and Nestor, then a model, stopping at the first that answers, each answer kept for next time. *bot* `no-install` `offline` `jeles` `nestor` · near: jeles, first-mention, nestor
- **llm-cli** (idea) — Suggestions through the llm command, so any model its plugins reach (local or hosted) can hand one in, with llm's own log naming the model. Needs llm and the plugin for your model; Apache-2.0. Goes online: the model its plugin reaches, to ask for suggestions. *new* `needs-install` `online` `cli` `plugin` · near: codex-cli, gemini-cli, model-exam
- **local-model** (idea) — Suggestions from a model on this machine only, such as Ollama, llama.cpp's server, llamafile, KoboldCpp or Jan. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `cpp` `jan` · near: openai-compatible, in-process, os-model
- [**mcp**](adapters/deps/mcp/) — Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. Needs mcp; MIT. *new* `needs-install` `offline` `mcp` `assistant` · near: mcp-lite, zed, cursor
- **mcp-by-hash** (idea) — Your passages served as MCP resources named by their SHA-256, so an assistant cites exactly the bytes it read and a changed passage gets a new name. *bot* `no-install` `offline` `sha` `citing` · near: snapshot, hook-read-first, hook-pin
- [**mcp-lite**](adapters/stdlib/mcp-lite/) — The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only. *box* `no-install` `offline` `mcp` · near: mcp, cursor, opencode
- **mcp-sampling** (idea) — Suggestions from whatever model your MCP client already runs, asked through MCP sampling, so willow needs no model or key of its own. *new* `no-install` `offline` `mcp` `client` · near: mcp, cursor, opencode
- **memory-import** (idea) — An AI assistant's memory store, SQLite or Markdown, handed in through propose: one suggestion per memory, none trusted until you seal it. *new* `no-install` `offline` `handed` `propose` · near: basic-memory, hermes, hook-feedback
- **mex** (idea) — mex's project memory for coding agents: its scaffold read as cited passages, and what an agent writes back held for your seal. *new* `no-install` `offline` `agent` `memory` · near: instruction-files, claude-code, codebase-memory
- **mlx** (idea) — Suggestions from a model run on Apple silicon through MLX, on this Mac alone. Needs mlx-lm, on Apple silicon only; MIT; licence of the model varies. *new* `needs-install` `offline` `apple` `silicon` · near: browser-model, model-fit, os-model
- **model-card** (idea) — A card naming the model behind an assistant (version or weights hash, where it runs, licence, known limits), with the card's hash on the record so each suggestion can say which model made it. *new* `no-install` `offline` `weights` `hash` · near: weights-pin, weights-card, cite-honesty
- **model-drift** (idea) — Your frozen questions asked again of a model now and then, flagging when its answers change while its name and card stay the same. Goes online: the endpoint you configure, to ask your questions again. *new* `no-install` `online` `drift` `flagged` · near: pile-gold, ask-later, fixity
- **model-exam** (idea) — Any model scored against the answers you sealed, your own questions as its exam, before you trust its suggestions. Goes online: the endpoint you configure, to ask your sealed questions. *new* `no-install` `online` `trust` `score` · near: code-first, ci-bets, llm-cli
- **model-fit** (idea) — Whether this machine's GPU, NPU or Apple silicon can run a local model, and about how fast, before you download one. *new* `no-install` `offline` `local` `apple` · near: mlx, local-model, model-shelf
- **model-shelf** (idea) — Every model already on this machine, read from Ollama's, LM Studio's, Jan's and GPT4All's folders and the Hugging Face cache: its runtime, size, quantization and hash, before you download another. *new* `no-install` `offline` `cache` `download` · near: openai-compatible, model-fit, local-model
- **night-batch** (idea) — Questions waiting for suggestions batched into one local-model run overnight, stopped the moment you're back. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `local` · near: local-model, browser-model, quantized
- [**openai-compatible**](adapters/stdlib/openai-compatible/) — Suggestions from any OpenAI-compatible endpoint you choose (LM Studio, vLLM, LocalAI, SGLang, Docker Model Runner, OpenRouter, Groq, Mistral), citing your passages. Goes online: the endpoint you configure, to ask for suggestions. *new* `no-install` `online` `cpp` `llama` · near: local-model, model-shelf, in-process
- [**opencode**](adapters/stdlib/opencode/) — OpenCode asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` · near: cursor, windsurf, zed
- **os-model** (idea) — Suggestions from the model built into the operating system, such as Apple's Foundation Models on a Mac: nothing to download, nothing leaving the device. Needs macOS 26 with Apple Intelligence on, and a small Swift helper; Apple's terms. *new* `needs-install` `offline` `apple` `mac` · near: mlx, local-model, browser-model
- [**persona-card**](adapters/stdlib/persona-card/) — A persona written as a card and compiled into the same system-prompt bytes every time, with the prompt's hash on the record. *box* `no-install` `offline` · near: folder-card, tip-pin, serve
- **plain-language** (idea) — An approved answer rewritten in plain language by a model, the rewrite held until you seal it. *new* `no-install` `offline` `held` · near: translate, hook-tiers, memory-import
- **quantized** (idea) — Finds the smallest quantized local model that still gets your box's own questions right, so suggestions come faster. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `local` · near: local-model, model-exam, night-batch
- **same-way** (idea) — A local model asked each of your box's questions three times, and how often its answer flips, since a model that answers the same way every time is one you can build on. Goes online: this-machine. *new* `no-install` `online` `local` `build` · near: pile-build, night-batch, quantized
- **schema-check** (idea) — A model's answer held to a JSON schema before anything reads it, and a reply that doesn't fit recorded as a result, not lost as an error. *box* `no-install` `offline` `result` `fit` · near: model-fit, connect-four, medical-records
- **second-opinion** (idea) — Two assistants' suggestions for the same question side by side, each waiting for its own seal. *new* `no-install` `offline` `assistant` `waiting` · near: assistant-scores, contradictions, pile-poetry
- [**serve**](adapters/stdlib/serve/) — The one file an AI model may read: only the passages you approved, under ids it can't guess, and nothing else. *bot* `no-install` `offline` · near: stack, decisions, export
- **serve-piles** (idea) — serve's piles grouped on all four W's -- who, when, what and where -- not where alone, so a model meets a question from every box that touched it. *new* `no-install` `offline` `serve` · near: pile-serve, pile-rungs, serve
- **silence-log** (idea) — A model that ran and said nothing kept as its own row, so silence is told apart from a model that never ran. *bot* `no-install` `offline` `log` `rows` · near: said, cassettes, llm-cli
- **translate** (idea) — An answer translated by a local model, the original kept beside it, the translation held until you seal it. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `local` `held` · near: plain-language, hook-tiers, local-model
- **weights-card** (idea) — A model card filled in from the weights file's own header, GGUF or safetensors (architecture, quantization, context length, licence), so the card says what the file says. *new* `no-install` `offline` `weights` `licence` · near: weights-pin, model-card, folder-card
- [**windsurf**](adapters/stdlib/windsurf/) — Windsurf asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` · near: cursor, opencode, zed
- [**zed**](adapters/stdlib/zed/) — Zed's assistant asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `mcp` · near: cursor, opencode, windsurf

## Ways to use it

- [**across**](adapters/stdlib/across/) — One page made from several willow records at once (each one's digest, export, timeline or readings), every line still cited by where it came from. *new* `no-install` `offline` `timeline` `digest` `everyday` · near: stack, timeline, digest
- **anki** (idea) — Approved answers as an Anki deck, built without Anki installed. *new* `no-install` `offline` · near: static-search, stale, export
- [**annotations**](adapters/stdlib/annotations/) — Approved answers as W3C Web Annotations, so any annotation tool can show what your files say about a page. *new* `no-install` `offline` `web` · near: rss-out, in-toto, prov
- [**badge**](adapters/stdlib/badge/) — A badge for a page: these answers came from these files and were approved, linked to the check anyone can run. *new* `no-install` `offline` `links` · near: in-toto, annotations, deep-links
- [**braille**](adapters/stdlib/braille/) — Answers as braille-ready files (BRF) for a braille display or embosser. *new* `no-install` `offline` · near: annotations, rss-out, calendar
- [**browse**](adapters/stdlib/browse/) — Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only. Reaches this machine only. *new* `no-install` `this-machine` `web` `everyday` · near: digest, launcher, hook-start
- [**calendar-out**](adapters/stdlib/calendar-out/) — Dates coming up as an .ics file your calendar app can subscribe to. *new* `no-install` `offline` `coming` `calendar` · near: coming-up, digest, calendar
- [**capture**](adapters/stdlib/capture/) — A note written into your folder in one line, with its type and tags, so the next question can find it. *new* `no-install` `offline` `tags` · near: coming-up, notes, plain
- [**cloudevents**](adapters/stdlib/cloudevents/) — Record rows in the CloudEvents envelope, for any tool that already reads them. *new* `no-install` `offline` `envelope` `tool` · near: prov, ro-crate, in-toto
- **datasette** (idea) — Your record and approved answers browsable in Datasette, read only: tables, facets and SQL on this machine. Needs Datasette; Apache-2.0. Reaches this machine only. *new* `needs-install` `this-machine` `sql` · near: record-sql, report, ro-crate
- [**deep-links**](adapters/stdlib/deep-links/) — Each answer as a link that opens the file at the line (RFC 5147 lines, browser text fragments). *new* `no-install` `offline` `links` `browser` · near: jetbrains, browse, vscode
- **desktop** (idea) — A small window to ask and approve, with nothing to install: Python's own tkinter. *new* `no-install` `offline` · near: copilot, cursor, opencode
- **dictate** (idea) — Ask out loud: your question spoken and turned to text on this machine. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `turned` · near: oakenscroll, agent-transcript, man-pages
- [**emacs**](adapters/stdlib/emacs/) — Answers in an Emacs compilation buffer, each a jump to its file and line. *new* `no-install` `offline` `jump` `command` · near: vim, vscode, pipe
- **email-ask** (idea) — Ask by emailing yourself; the answer comes back as a reply with its sources. Goes online: your own mail server, over IMAP and SMTP, to read questions and reply. *new* `no-install` `online` `sources` `replies` · near: jeles, bot-venv, thesis
- **emergency-card** (idea) — One page of your medicines, allergies and contacts, from your files, to print or keep on your phone. *new* `no-install` `offline` `prints` `contacts` · near: digest, privacy, calendar
- **home-assistant** (idea) — Ask through Home Assistant's voice assistant, answered from your files. Goes online: your Home Assistant, on your own network, to answer its voice assistant. *new* `no-install` `online` `assistant` `voice` · near: home-sensors, mcp-sampling, launcher
- [**jetbrains**](adapters/stdlib/jetbrains/) — An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line. *new* `no-install` `offline` `links` · near: vscode, privacy, aider
- **kiosk** (idea) — A shared machine in a library or classroom: one box, ask only, nobody's key on it. Reaches this machine only. *new* `no-install` `this-machine` `share` `key` · near: family-box, transcript-redact, share
- [**launcher**](adapters/stdlib/launcher/) — Ask from Alfred, Raycast, KRunner or PowerToys Run, answers with file and line. *new* `no-install` `offline` · near: aider, browse, pile-store
- [**llms-txt**](adapters/stdlib/llms-txt/) — An llms.txt for your folder, written from what's actually in it to the spec's version 2, and any llms.txt you saved checked against that spec. *new* `no-install` `offline` `llm` · near: typosquat, serve, capture
- [**make-it-so**](adapters/stdlib/make-it-so/) — Write down what you want done and the passages it rests on; it checks they still hold, and never does it for you. *new* `no-install` `offline` `down` · near: decisions, predict, tip-pin
- **obsidian** (idea) — Ask from inside Obsidian, answers as links to the note and line. Reaches this machine only. *new* `no-install` `this-machine` `links` `obsidian` · near: jetbrains, notes, deep-links
- [**pipe**](adapters/stdlib/pipe/) — Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf. *box* `no-install` `offline` · near: vim, shell, emacs
- [**plain**](adapters/stdlib/plain/) — Answers as sentences instead of JSON, each with its file and line. *new* `no-install` `offline` `sentence` · near: readings, privacy, aider
- **pr-context** (idea) — On a pull request, the passages in the repo's docs that name the files it changes, posted as one comment. Goes online: the forge, through the workflow's token, to post the comment. *new* `no-install` `online` `pull` `requests` · near: quote-review, github-archive, forgejo-dump
- [**print**](adapters/stdlib/print/) — An answer as a printable page with its sources, to take to an appointment; --large for big, high-contrast type. *new* `no-install` `offline` `prints` `everyday` · near: web-pages, pipe, across
- **qr** (idea) — An answer as a QR code on screen, to carry it to your phone without the network. *new* `no-install` `offline` `screen` · near: scrub, a11y-check, code-first
- [**repo-pile**](adapters/stdlib/repo-pile/) — Public repositories you list, cloned and made askable, keeping only those under a licence an Apache-2.0 project can use. Goes online: github.com (or the --source you give), to clone the repositories you list. *new* `no-install` `online` `project` `research` · near: upstream-desk, pile-build, pile-serve
- [**rss-out**](adapters/stdlib/rss-out/) — New approved answers as an RSS feed file, for any feed reader. *new* `no-install` `offline` · near: annotations, in-toto, static-search
- **safe-app** (idea) — willow as a SAFE app: installed from the SAFE App Store, authorized per session, and deleted clean. *new* `no-install` `offline` `store` `session` · near: vectors, memory-import, session-cost
- **share** (idea) — One sealed answer to send someone, checkable by them, without giving them the folder. *new* `no-install` `offline` `share` · near: session-seal, model-recall, in-toto
- [**shell**](adapters/stdlib/shell/) — A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows. *new* `no-install` `offline` `shell` `bash` · near: pipe, shell-history, hook-shell
- **socratic** (idea) — Asks you questions about your own notes instead of answering, each citing the passage it asked from. *new* `no-install` `offline` `citing` · near: oakenscroll, stale, claude-code
- **speak** (idea) — Reads answers aloud. Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` · near: aider, debts, openai-compatible
- [**stack**](adapters/stdlib/stack/) — One page made from several add-ons run in the order you list them, their results grouped so the biggest come first. *new* `no-install` `offline` `several` `prints` · near: across, serve, readme
- [**start**](adapters/stdlib/start/) — First run in one step: asks where your files are, sets up willow's record and your key, copies in a starter words list, and prints a double-click launcher. *new* `no-install` `offline` `launcher` `starter` `everyday` · near: starter-words, launcher, nicknames
- [**static-search**](adapters/deps/static-search/) — An exported page of approved answers with its own search built in, no server of its own, served from any static host. Needs Pagefind, its Python package pagefind and its program pagefind-bin; MIT. *box* `needs-install` `offline` `search` · near: mcp, record-sql, pgp
- **telegram-bot** (idea) — Ask from your phone through a Telegram bot only you can talk to. Goes online: api.telegram.org, to receive your questions and send answers. *new* `no-install` `online` `telegram` `bot` · near: bot-venv, chats, cursor
- **tui** (idea) — A full-screen terminal view to ask, read passages and approve, in curses. *new* `no-install` `offline` `screen` `full` · near: browse, jeles, serve
- [**vim**](adapters/stdlib/vim/) — Answers in Vim and Neovim's quickfix list, each a jump to its file and line. *new* `no-install` `offline` `jump` · near: emacs, pipe, vscode
- [**vscode**](adapters/stdlib/vscode/) — A VS Code task whose answers land in the Problems panel, each a jump to its file and line. *new* `no-install` `offline` `jump` · near: emacs, vim, jetbrains
- **warm** (idea) — The kernel kept running between questions on this machine, so each question skips the start-up. Reaches this machine only. *new* `no-install` `this-machine` `start` `between` · near: start, pile-store, cassettes

## Play

- **art-of-the-day** (idea) — An artwork from the Met's public-domain collection, drawn for the day or for each sealed session. Goes online: collectionapi.metmuseum.org, to read the artwork. *new* `no-install` `online` `domain` `drawn` · near: todays-place, gutenberg, session-seal
- **beacon** (idea) — Draws seeded by a public randomness beacon (drand), so nobody could have picked the result in advance. Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `seeded` `draws` · near: tarot, oracle-text, dice
- [**catgrid**](adapters/stdlib/catgrid/) — A seeded logic grid with one cat in every row, column and colour region and a unique answer, replayed from its moves. *new* `no-install` `offline` `rows` `seeded` · near: life, game-master, hook-replay
- **chess-puzzle** (idea) — A Lichess puzzle a day, drawn by a seed: predict whether you'll solve it, then solve it. Goes online: lichess.org, to read the puzzle. *new* `no-install` `online` `drawn` `chess` · near: predict, art-of-the-day, daily-word
- **connect-four** (idea) — Connect Four as rows on the record, held to the solved result: the first player wins. *new* `no-install` `offline` `result` `held` · near: schema-check, cloudevents, crates
- [**daily-word**](adapters/stdlib/daily-word/) — A five-letter word game drawn from your own files' words: a new word each day, the same for anyone asking the same folder. *new* `no-install` `offline` `daily` · near: quiz, surprise, on-this-day
- [**dice**](adapters/stdlib/dice/) — Seeded dice rolls as rows: every roll replayable and checkable. *bot* `no-install` `offline` `seeded` `dice` · near: dice5e, game-master, tarot
- [**dice5e**](adapters/stdlib/dice5e/) — Full tabletop dice notation (4d6kh3, advantage), rolled on the record and checkable like dice. *bot* `no-install` `offline` `rolls` `rows` · near: dice, game-master, fight5e
- **fight5e** (idea) — Tabletop combat run from stat blocks on dice5e's rolls, every attack on the record and replayable. *new* `no-install` `offline` `rolls` `replayable` · near: dice5e, dice, roll-for-merge
- **front-page** (idea) — Which new posts will make the Hacker News front page? Wager, and let its search settle it. Goes online: hn.algolia.com, to read the front page. *new* `no-install` `online` `settled` `front` · near: spurious, quake-bets, readme
- [**game-master**](adapters/stdlib/game-master/) — A tabletop game's rolls and rulings as rows on the record, with the game master's calls sealed. *bot* `no-install` `offline` `rows` `dice` · near: life, dice5e, dice
- **gutenberg** (idea) — A paragraph from a public-domain book beside one of yours, for serendipity. Goes online: gutenberg.org, each book fetched once. *new* `no-install` `online` `book` `domain` · near: todays-place, art-of-the-day, witness
- **hanoi** (idea) — Towers of Hanoi as rows: each move, n discs in 2^n - 1. *new* `no-install` `offline` `rows` `move` · near: reversi, session-seal, tic-tac-toe
- [**horoscope**](adapters/stdlib/horoscope/) — A daily horoscope keyed on your name and the date: same name, same day, same reading, always. *bot* `no-install` `offline` `daily` · near: daily-word, goodreads, gaps
- **horoscope-grades** (idea) — Every horoscope logged as a forecast and settled against the day, so the stars get a Brier score. *new* `no-install` `offline` `forecast` `score` · near: forecasts, weather-bet, predictions
- **ink-story** (idea) — A branching ink story where every choice made for you comes from a seed on the record. Needs inkjs; MIT. *new* `needs-install` `offline` `branch` `seed` · near: oracle-text, restack, timeline
- **joins** (idea) — Two passages from two different folders, drawn by chance, for you to say what joins them. *bot* `no-install` `offline` `joins` `drawn` · near: contradictions, pageviews, crosswalk
- [**life**](adapters/stdlib/life/) — Conway's Game of Life as rows: a fully deterministic world on the record. *bot* `no-install` `offline` `rows` `game` · near: catgrid, game-master, tarot
- **lore** (idea) — For a world you're writing: each fact about it sealed one at a time, so a story can be checked against its canon. *bot* `no-install` `offline` `world` · near: mutants, llms-txt, claim-check
- **lunatic** (idea) — The moon's real phase sets how far typos are forgiven: everything at full moon, nothing at new. Needs Skyfield; MIT. *new* `needs-install` `offline` `real` `far` · near: typos, real-sky, dotfiles
- **mastermind** (idea) — Mastermind with the secret's hash at the open: each guess and score on the record. *new* `no-install` `offline` `open` `score` · near: assistant-scores, secrets-audit, weather-bet
- **movie** (idea) — Your record as a Gource film: every question, approval and miss growing like a tree. Needs the gource program; GPL-3.0, called not linked. *new* `needs-install` `offline` `tree` `film` · near: bench, family-tree, vectors
- **nim** (idea) — Nim as rows: the heaps and each take, a position lost exactly when the heaps' XOR is 0. *new* `no-install` `offline` `rows` `lost` · near: tic-tac-toe, cloudevents, hosts
- **ninety-percent** (idea) — The calibration drill: give a range you're 90% sure of for a real number, and see how many hold. Goes online: Our World in Data, its numbers downloaded once. *new* `no-install` `online` `ranges` `drill` · near: oakenscroll, restore-drill, pins
- [**odds**](adapters/stdlib/odds/) — Exact odds, as fractions, for a game's dice and tables: what each outcome's chance really is. *bot* `no-install` `offline` `game` `dice` · near: game-master, dice, dice5e
- [**oracle-text**](adapters/stdlib/oracle-text/) — Readings written by a Tracery grammar, every branch picked by the seeded stream, so each one can be replayed. *new* `no-install` `offline` `branch` `replayed` · near: hook-replay, restack, ink-story
- **pageviews** (idea) — Two Wikipedia articles drawn at random: which gets more views tomorrow? Goes online: the Wikimedia pageviews API, to settle it. *new* `no-install` `online` `article` `drawn` · near: surprise, kiwix, joins
- [**pile-poetry**](adapters/stdlib/pile-poetry/) — Verse from the word pairs your own files use most, in your own dialect. *new* `no-install` `offline` `dialect` `pairs` · near: dialect, second-opinion, pair-drift
- **predictions** (idea) — Twelve yes-or-no questions about random data, forecast now and answered by a beacon round later, with your Brier score. Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `score` `brier` · near: forecasts, tides, horoscope-grades
- **quake-bets** (idea) — Will there be a magnitude 6 this week? Bet, then let the USGS feed settle it against the base rate. Goes online: earthquake.usgs.gov, to read the week's earthquakes. *new* `no-install` `online` `bet` `settled` · near: horoscope-grades, ci-bets, weather-bet
- [**quiz**](adapters/stdlib/quiz/) — A quiz from your own files: a passage with a word missing, and you fill it in. *new* `no-install` `offline` · near: daily-word, serve, plain
- **real-sky** (idea) — A horoscope from where the planets really are, computed offline from a JPL ephemeris. Needs Skyfield; MIT. Goes online: the ephemeris file, downloaded once. *new* `needs-install` `online` `horoscope` `computed` · near: horoscope, horoscope-grades, odds
- **reversi** (idea) — Reversi as rows: every move, each flip following from the board. *new* `no-install` `offline` `move` `rows` · near: tic-tac-toe, catgrid, hanoi
- **roll-for-merge** (idea) — A d20 for every pull request, green runs added and red streaks taken away, against a DC the bot calls. *new* `no-install` `offline` `pull` `requests` · near: ci-bets, ci-baseline, github
- **sokoban** (idea) — Sokoban levels and moves on the record, a solution checked by replaying it. *new* `no-install` `offline` `replayed` `level` · near: hook-replay, catgrid, reading-level
- **spurious** (idea) — Everything joined on time and place (CI reds, earthquakes, rain, front pages) to hunt correlations that mean nothing. *new* `no-install` `offline` `front` `red` · near: front-page, ci-why, readme
- [**tarot**](adapters/stdlib/tarot/) — A seeded tarot draw on the record, replayable by anyone with the seed. *new* `no-install` `offline` `seeded` `replayable` · near: catgrid, dice, life
- **tic-tac-toe** (idea) — Tic-tac-toe as rows: every move, and the solver's value of each position; perfect play draws. *new* `no-install` `offline` `rows` `move` · near: reversi, catgrid, nim
- **tides** (idea) — Tide predictions as a control: if your Brier score on tides isn't near zero, the forecasting plumbing is broken. Goes online: NOAA's tides API, to read predictions and what happened. *new* `no-install` `online` `score` `forecast` · near: predictions, forecasts, horoscope-grades
- **todays-place** (idea) — One place a day drawn from Natural Earth's public-domain list, for the day's questions and bets. *new* `no-install` `offline` `public` `domain` · near: art-of-the-day, gutenberg, tax-year
- **weather-bet** (idea) — Wager on rain tomorrow before you look, against Open-Meteo's own forecast, and see whose Brier score wins. Goes online: api.open-meteo.com, to read the forecast and the outcome. *new* `no-install` `online` `score` `forecast` · near: forecasts, horoscope-grades, ci-bets

## For maintainers

- [**agents-md-check**](adapters/stdlib/agents-md-check/) — Commands and paths named in AGENTS.md or CLAUDE.md that no longer exist in the repo. *new* `no-install` `offline` `claude` `agent` · near: instruction-files, hook-impact, install-scripts
- [**bench**](adapters/stdlib/bench/) — How fast the kernel answers on boxes of set sizes, per release, so a slowdown is seen. *new* `no-install` `offline` `release` `build` · near: profile, pile-store, pile-build
- [**bot-venv**](adapters/stdlib/bot-venv/) — Which venv has what CI needs, willow-bot's own by its rule or any you name, and the line that runs CI with its Python. *bot* `no-install` `offline` `test` `repo` · near: ci, hosts, fast-tests
- [**ci**](adapters/stdlib/ci/) — This repo's checks as verdict rows on a kernel record, the same every run. Goes online: PyPI, to read each dependency floor's release date. *box* `no-install` `online` `rows` `verdict` · near: ci-memo, bot-venv, ci-why
- **ci-baseline** (idea) — Is your CI normal? How often pull requests everywhere go green first time, from GH Archive. Goes online: data.gharchive.org, its hours downloaded once. *new* `no-install` `online` `pull` `requests` · near: ci-bets, welcome, github-archive
- **ci-bets** (idea) — Bet on your own CI: forecasts on each pull request going green, scored against the model's. *new* `no-install` `offline` `pull` `requests` · near: ci-baseline, roll-for-merge, weather-bet
- [**ci-cache**](adapters/stdlib/ci-cache/) — CI caches pip, npm, .NET and Maven downloads keyed on their lockfiles, so a run skips the installs. *new* `no-install` `offline` `npm` `cache` · near: ci-memo, ci-logs, ci
- [**ci-memo**](adapters/stdlib/ci-memo/) — A CI gate whose inputs' bytes are unchanged keeps its recorded verdict: pin a run's per-gate keys, and run only what a change can reach. *new* `no-install` `offline` `pin` `reach` · near: ci-cache, test-impact, ci
- [**ci-why**](adapters/stdlib/ci-why/) — Why CI went red: the failing block pulled out of the job's log, plain, put where people look. *bot* `no-install` `offline` `job` `failed` · near: ci, ci-logs, gh-json
- **code-stats** (idea) — Lines, code and complexity per language, per release, as rows the list can answer from. Needs the scc program; MIT. *new* `needs-install` `offline` `release` `language` · near: profile, bench, plain-language
- **compiled** (idea) — kernel.py compiled with mypyc for speed, held to the same vectors byte for byte. Needs mypyc; MIT. *new* `needs-install` `offline` `held` `vectors` · near: go, swift, crates
- **contribute** (idea) — For anyone on GitHub, what they can do next in the projects they work on: open pull requests, reviews asked of them, issues assigned. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `requests` `pull` · near: upstream-desk, github-archive, quote-review
- **contributions** (idea) — A ledger of who contributes to the repo: first-timers and outside contributors called out, bots known by type, never by name. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `bot` `calls` · near: bot-venv, hook-guard, welcome
- **crates** (idea) — A Rust port of kernel.py on crates.io, held to the same vectors as the other four. Goes online: crates.io, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `port` · near: go, swift, compiled
- **docs-i18n** (idea) — The README in other languages, each checked for drift against the English one. *new* `no-install` `offline` `readme` `drift` · near: readme, llms-txt, package-docs
- [**fast-tests**](adapters/deps/fast-tests/) — The test suite across every core with pytest-xdist, the same tests in a fraction of the time. Needs pytest-xdist; MIT. *new* `needs-install` `offline` `core` `fraction` · near: parallel, pdf, mcp
- **forgejo** (idea) — What willow's repo needs from Forgejo, Gitea or Codeberg: its host.json and an Actions file, so the repo can move there. Goes online: the Forgejo instance's API, to read the author of a pull request a security report points to. *new* `no-install` `online` `repo` `actions` · near: gitlab, sourcehut, github
- **fuzz** (idea) — Random and broken inputs thrown at the kernel's commands, every crash kept as a test. *new* `no-install` `offline` `test` `fuzz` · near: hook-fuzz, property-tests, hook-replay
- [**github**](adapters/stdlib/github/) — What willow's repo needs from GitHub, kept in one folder so it can be taken away. Goes online: GitHub, through gh, to read the author of a pull request a security report points to. *box* `no-install` `online` `repo` `away` · near: gitlab, ci, live
- **gitlab** (idea) — What willow's repo needs from GitLab, as github does for GitHub: its host.json and CI file, so the repo can move there. Goes online: GitLab, through glab, to read the author of a merge request a security report points to. *new* `no-install` `online` `github` `repo` · near: forgejo, github, sourcehut
- **go** (idea) — A Go port of kernel.py, held to the same vectors as the others. *new* `no-install` `offline` `vectors` `port` · near: crates, swift, compiled
- [**live**](adapters/stdlib/live/) — Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here. Goes online: only what the programs it starts reach on their own; it reaches nothing itself. *new* `no-install` `online` `tests` · near: mutants, github, ci
- **maven** (idea) — The Java port on Maven Central, built from this repo and checked against the vectors. Goes online: Maven Central, to publish a release a maintainer tags. *new* `no-install` `online` `repo` `vectors` · near: nuget, npm, pypi
- [**mutants**](adapters/stdlib/mutants/) — Breaks each add-on's code on purpose and checks its tests notice. *new* `no-install` `offline` `test` · near: live, slow-tests, ci
- **novelty** (idea) — Before a new add-on merges, whether its combination of pieces has been assembled before, scanned the way a study checks its own novelty. *new* `no-install` `offline` `merge` `scan` · near: similar, redential, restack
- **npm** (idea) — The TypeScript port on npm, built from this repo, checked against the vectors, and published with provenance; npx runs it. Goes online: registry.npmjs.org, to publish a release a maintainer tags. *new* `no-install` `online` `repo` `vectors` · near: nuget, maven, pypi
- **nuget** (idea) — The C# port on NuGet, built from this repo and checked against the vectors. Goes online: nuget.org, to publish a release a maintainer tags. *new* `no-install` `online` `repo` `vectors` · near: maven, npm, pypi
- [**pins**](adapters/stdlib/pins/) — Version ranges in package.json, pyproject.toml or Cargo.toml that no lockfile holds. *new* `no-install` `offline` `dependency` `package` · near: lockfiles, advisories, typosquat
- [**profile**](adapters/stdlib/profile/) — Where a question's time goes, function by function, from cProfile, per release. *new* `no-install` `offline` `release` · near: bench, test-shards, calendar
- **property-tests** (idea) — Thousands of odd inputs (combining marks, empty strings, huge seeds) thrown at the byte rules by Hypothesis. Needs Hypothesis; MPL-2.0. *new* `needs-install` `offline` `inputs` `rule` · near: fuzz, hook-fuzz, weakest-link
- **pypi** (idea) — kernel.py on PyPI as a package with no dependencies, built from this repo, checked against the vectors, and attested on upload; uvx and pipx run it. Goes online: upload.pypi.org, to publish a release a maintainer tags. *new* `no-install` `online` `repo` `vectors` · near: npm, nuget, maven
- **pypy** (idea) — The kernel and its tests run under PyPy too, and timed against CPython. *new* `no-install` `offline` `test` · near: slow-tests, test-shards, mutants
- [**readme**](adapters/stdlib/readme/) — Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. *new* `no-install` `offline` · near: similar, live, front-page
- **reconciler** (idea) — willow-reconciler run on this repo's idea list and git history: how much of what was proposed has landed. Needs willow-reconciler; Apache-2.0. *new* `needs-install` `offline` `repo` `git` · near: git-history, hook-checks, git-notes
- **repo-index** (idea) — This repository as its own deterministic box: its cards, docs and code as dated passages, rebuilt the same bytes each time, so willow can answer questions about itself. *new* `no-install` `offline` `repositories` `index` · near: persona-card, latent, same-way
- **repro** (idea) — A release built twice from the same commit, byte for byte the same. *new* `no-install` `offline` `byte` `twice` · near: compiled, mirror, hooks-elsewhere
- [**restack**](adapters/stdlib/restack/) — Main merged into your branches, with the conflicts in the files the repo makes or only adds to settled by its own tools, and every other one left to you. *new* `no-install` `offline` `branch` `repo` `git` · near: github, similar, oracle-text
- [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search. *box* `no-install` `offline` `search` · near: readme, restack, repo-pile
- [**slow-tests**](adapters/stdlib/slow-tests/) — Each test's time kept per run, with the slowest named and any that got slower flagged. *new* `no-install` `offline` `test` · near: test-shards, mutants, profile
- **sourcehut** (idea) — What willow's repo needs from SourceHut: its host.json for patches by email and a builds.sr.ht manifest. Goes online: sr.ht, through hut, to read the author of a patch a security report points to. *new* `no-install` `online` `host` `repo` · near: forgejo, gitlab, github
- **swift** (idea) — A Swift port of kernel.py for iPhone and Mac apps, held to the same vectors. *new* `no-install` `offline` `vectors` `port` · near: go, crates, compiled
- [**test-impact**](adapters/stdlib/test-impact/) — Only the tests a change can reach run first, from the import graph; the full suite still runs after. *new* `no-install` `offline` `test` `suite` · near: ci-memo, lesson-time, stale
- [**test-shards**](adapters/stdlib/test-shards/) — The CI test jobs split by each test's past time, so every job finishes about together. *new* `no-install` `offline` `test` `job` · near: slow-tests, ci, profile
- **welcome** (idea) — One plain thank-you on a first-time contributor's first pull request, once per person, and only where it's turned on. Goes online: the forge, through the workflow's token, to post the thank-you. *bot* `no-install` `online` `pull` `requests` · near: ci-baseline, pr-context, upstream-desk
<!-- /willow:list -->

Back to the [README](README.md).
