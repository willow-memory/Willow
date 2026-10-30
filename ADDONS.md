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
Each carries up to five tags: four filled in from its card (`no-install` or
`needs-install`; `offline`, `this-machine` or `online`; `read-only`, `records`
or `writes-output`; its section), and any the card's author adds or changes.

<!-- willow:pools -->
`██████████░░░░░░░░░░` **225 of 470 built** · 419 need no install · 51 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 42 | 63 | 96 | 9 |
| Finding things | 27 | 16 | 33 | 10 |
| Your own words | 18 | 7 | 22 | 3 |
| Keeping track | 35 | 23 | 58 | 0 |
| Trust and proof | 20 | 25 | 36 | 9 |
| Privacy and safety | 11 | 3 | 14 | 0 |
| Assistants | 25 | 32 | 51 | 6 |
| Ways to use it | 19 | 20 | 35 | 4 |
| Play | 9 | 31 | 35 | 5 |
| For maintainers | 19 | 25 | 39 | 5 |
<!-- /willow:pools -->

## Newest

<!-- willow:newest -->
- 2026-10-29 · [**x-archive**](adapters/stdlib/x-archive/) — An X (Twitter) archive: your posts, replies and DMs as dated lines.
- 2026-10-29 · [**words-tr**](adapters/stdlib/words-tr/) — Turkish common words ("ve", "bir").
- 2026-10-29 · [**words-ru**](adapters/stdlib/words-ru/) — Russian common words ("и", "в", "на").
- 2026-10-29 · [**words-cy**](adapters/stdlib/words-cy/) — Welsh common words ("a", "y", "yn").
- 2026-10-29 · [**words-ar**](adapters/stdlib/words-ar/) — Arabic common words ("في", "من", "على").
<!-- /willow:newest -->

## Add-on of the week

<!-- willow:pick week=2026-W44 -->
**[restack](adapters/stdlib/restack/)** — Main merged into your branches, with the conflicts in the files the repo makes or only adds to settled by its own tools, and every other one left to you.

*Drawn for 2026-W44: SHA-256 of "willow add-on of the week 2026-W44", modulo the 225 built add-ons in name order.*
<!-- /willow:pick -->

<!-- willow:list -->
**Contents:** [Reading more kinds of files](#reading-more-kinds-of-files) · [Finding things](#finding-things) · [Your own words](#your-own-words) · [Keeping track](#keeping-track) · [Trust and proof](#trust-and-proof) · [Privacy and safety](#privacy-and-safety) · [Assistants](#assistants) · [Ways to use it](#ways-to-use-it) · [Play](#play) · [For maintainers](#for-maintainers)

## Reading more kinds of files

Each writes plain text into a mirror folder the kernel searches, so your originals are never touched.

- **agent-transcript** (idea) — Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told. *new* `no-install` `offline` `writes-output` `file-reader`
- **almanac** (idea) — An Almanac's catalog.json (climate, health, civic and the rest): each public dataset's description and source as passages, with when its link was last checked. *new* `no-install` `offline` `writes-output` `file-reader`
- **apple-notes** (idea) — Apple Notes, read from a copy of its database: each note as plain text with its folder and dates. *new* `no-install` `offline` `writes-output` `file-reader`
- **archivebox** (idea) — ArchiveBox snapshots: each saved page's text, with its URL and the date it was captured. *new* `no-install` `offline` `writes-output` `file-reader`
- **bank** (idea) — Bank CSV and OFX statements as dated lines, with spending by month. *new* `no-install` `offline` `writes-output` `file-reader`
- [**bibtex**](adapters/stdlib/bibtex/) — .bib files: each reference as a passage, so you can ask which paper said it and get its key. *new* `no-install` `offline` `writes-output` `file-reader`
- **bluesky** (idea) — A Bluesky repo.car export: your posts as dated lines, read by a small CAR and CBOR reader of its own. *new* `no-install` `offline` `writes-output` `file-reader`
- **bookmarks** (idea) — Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file. *new* `no-install` `offline` `writes-output` `file-reader`
- [**books**](adapters/stdlib/books/) — Kindle "My Clippings.txt" highlights and .epub text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**calendar**](adapters/stdlib/calendar/) — .ics events and .vcf contacts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **canvas** (idea) — Canvas course exports: pages, assignments and discussions as passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**chats**](adapters/stdlib/chats/) — WhatsApp and Telegram exports, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- [**chordpro**](adapters/stdlib/chordpro/) — ChordPro song sheets: titles, lyrics and chords, so you can ask which song had that line. *new* `no-install` `offline` `writes-output` `file-reader`
- [**ci-logs**](adapters/stdlib/ci-logs/) — CI run logs you downloaded (GitHub Actions, GitLab CI, Forgejo Actions): each failing step as a passage. *new* `no-install` `offline` `writes-output` `file-reader`
- [**clauses**](adapters/stdlib/clauses/) — A policy, contract or set of terms as one sentence a passage, so an answer lands on the clause, and what changed between two versions, sentence by sentence. *new* `no-install` `offline` `writes-output` `file-reader` `policies`
- **code-comments** (idea) — A codebase's comments and docstrings as passages, cited by file and line. *new* `no-install` `offline` `writes-output` `file-reader`
- **codebase-memory** (idea) — codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line. *new* `no-install` `offline` `writes-output` `file-reader`
- **confluence** (idea) — A Confluence space's HTML export as plain text, page by page. *new* `no-install` `offline` `writes-output` `file-reader`
- **corpus-lens** (idea) — corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code. *new* `no-install` `offline` `writes-output` `file-reader`
- [**day-one**](adapters/stdlib/day-one/) — Day One's JSON export: each journal entry as a dated passage, with its place and weather. *new* `no-install` `offline` `writes-output` `file-reader`
- **discord** (idea) — Discord's data package: your messages, one dated line each, by server and channel. *new* `no-install` `offline` `writes-output` `file-reader`
- **dotfiles** (idea) — Your dotfiles as passages: which file sets what, for 'where did I set my editor?' *new* `no-install` `offline` `writes-output` `file-reader`
- [**evernote**](adapters/stdlib/evernote/) — Evernote's .enex files: each note as plain text with its notebook, tags and dates. *new* `no-install` `offline` `writes-output` `file-reader`
- [**family-tree**](adapters/stdlib/family-tree/) — Family trees from GEDCOM files: who was born where and when, and which record says so. *new* `no-install` `offline` `writes-output` `file-reader`
- **forgejo-dump** (idea) — A Forgejo or Gitea dump, Codeberg's included: issues, pull requests and wiki pages as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **gh-json** (idea) — What gh prints with --json (issues, pull requests, runs), saved to a file and read as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **git-history** (idea) — Commit messages and diffs as a dated pile: "when did we change the retry limit?" Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `file-reader`
- **github-archive** (idea) — Your GitHub account's data export: the issues, pull requests, reviews and comments you wrote, as dated passages with their links. *new* `no-install` `offline` `writes-output` `file-reader`
- **gitlab-export** (idea) — A GitLab project export, read without unpacking it: its issues, merge requests and comments as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **goodreads** (idea) — Goodreads and StoryGraph exports: the books you've read, when, and what you thought of them. *new* `no-install` `offline` `writes-output` `file-reader`
- **google-classroom** (idea) — Google Classroom from Takeout: assignments, announcements and comments as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**google-keep**](adapters/stdlib/google-keep/) — Google Keep from Takeout: notes, lists and labels as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**health**](adapters/stdlib/health/) — Apple Health and Google Fit exports as daily numbers the readings add-on can trend. *new* `no-install` `offline` `writes-output` `file-reader`
- [**home-sensors**](adapters/stdlib/home-sensors/) — Home Assistant's history export: sensor readings as dated numbers the readings add-on can trend. *new* `no-install` `offline` `writes-output` `file-reader`
- **homestead** (idea) — Homestead's exports from its law, ledger and health modules: records, deadlines and evidence as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **instapaper** (idea) — Instapaper's CSV and HTML export: saved articles and highlights as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **irc** (idea) — IRC logs from WeeChat, irssi or ZNC, one dated line per message, by network and channel. *new* `no-install` `offline` `writes-output` `file-reader`
- [**jira**](adapters/stdlib/jira/) — Jira's issue export, CSV or XML: each issue, comment and status change as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**joplin**](adapters/stdlib/joplin/) — Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates. *new* `no-install` `offline` `writes-output` `file-reader`
- **journiv** (idea) — Journiv journal entries, with their moods, as dated lines, once its export format is settled. *new* `no-install` `offline` `writes-output` `file-reader`
- [**jrnl**](adapters/stdlib/jrnl/) — jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage. *new* `no-install` `offline` `writes-output` `file-reader`
- [**jupyter**](adapters/stdlib/jupyter/) — Jupyter notebooks: Markdown cells, code and text outputs as passages, cited by cell. *new* `no-install` `offline` `writes-output` `file-reader`
- [**karakeep**](adapters/stdlib/karakeep/) — Karakeep's JSON export: bookmarks, notes and tags as plain text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**latex**](adapters/stdlib/latex/) — LaTeX sources as plain prose, commands stripped, cited by the .tex file's own lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **lessons** (idea) — Lesson plans from the Emerging Rule community library, by grade and subject, as passages a teacher can ask. *new* `no-install` `offline` `writes-output` `file-reader`
- **letterboxd** (idea) — Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **linkedin** (idea) — LinkedIn's data export: messages, posts and connections as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **listening** (idea) — Spotify's data download: what you listened to, by day, so you can ask what was on that summer. *new* `no-install` `offline` `writes-output` `file-reader`
- **location-history** (idea) — Google Maps Timeline and other location exports: where you were, by day. *new* `no-install` `offline` `writes-output` `file-reader`
- **lockfiles** (idea) — Lockfiles as passages (package-lock.json, pnpm-lock.yaml, poetry.lock, uv.lock, Cargo.lock, go.sum): which version of each dependency, and which lockfile says so. *new* `no-install` `offline` `writes-output` `file-reader`
- **logs** (idea) — System and app logs (syslog, journald's export, nginx): each line dated, so you can ask when it started. *new* `no-install` `offline` `writes-output` `file-reader`
- [**mail**](adapters/stdlib/mail/) — .eml and .mbox files, with sender, date and subject kept. *new* `no-install` `offline` `writes-output` `file-reader`
- **man-pages** (idea) — The man pages installed on this machine as plain text, so you can ask your own system's docs. *new* `no-install` `offline` `writes-output` `file-reader`
- [**manifests**](adapters/deps/manifests/) — Docker Compose and Kubernetes YAML: each service, image, port and volume as a passage. Needs PyYAML; MIT. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**mastodon**](adapters/stdlib/mastodon/) — A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **matrix** (idea) — Element's room export, JSON or HTML: one dated line per message in each Matrix room. *new* `no-install` `offline` `writes-output` `file-reader`
- [**mediawiki**](adapters/stdlib/mediawiki/) — A MediaWiki XML dump: each page's latest text, with its title and when it changed. *new* `no-install` `offline` `writes-output` `file-reader`
- **medical-records** (idea) — Your health records as FHIR JSON or C-CDA XML: visits, results and prescriptions as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **meta-archive** (idea) — Facebook and Instagram's Download Your Information files: posts, comments and messages as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **moodle** (idea) — Moodle course backups: pages, assignments, quizzes and forum posts as passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **music-library** (idea) — Your music files' tags (MP3, FLAC, M4A): artist, album, year and track, as lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**musicxml**](adapters/stdlib/musicxml/) — MusicXML scores: titles, lyrics, tempo and performance markings as passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**notes**](adapters/stdlib/notes/) — Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. *new* `no-install` `offline` `writes-output` `file-reader`
- **notion** (idea) — Notion's export zip, Markdown and CSV, as plain text with each page's title and path. *new* `no-install` `offline` `writes-output` `file-reader`
- **ocr** (idea) — Text out of photos of letters and scanned PDFs. Needs pytesseract and the tesseract program; Apache-2.0. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**office**](adapters/stdlib/office/) — .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. *new* `no-install` `offline` `writes-output` `file-reader`
- **orders** (idea) — Amazon's order history and other shops' CSV exports: what you bought, when, and for how much. *new* `no-install` `offline` `writes-output` `file-reader`
- **package-docs** (idea) — The READMEs and docs inside packages you've already installed (site-packages, node_modules, Cargo's registry cache), so you can ask your dependencies offline. *new* `no-install` `offline` `writes-output` `file-reader`
- [**parallel**](adapters/stdlib/parallel/) — A reader run over several folders at once, across every CPU core, so a big mirror of many sources builds in a fraction of the time. *new* `no-install` `offline` `writes-output` `file-reader`
- **past-papers** (idea) — Past exam papers and their mark schemes as passages: which year asked this, and what earned the marks. *new* `no-install` `offline` `writes-output` `file-reader`
- [**pdf**](adapters/deps/pdf/) — Text out of PDFs. Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**pgn**](adapters/stdlib/pgn/) — Chess games from PGN files: players, dates, openings and your annotations. *new* `no-install` `offline` `writes-output` `file-reader`
- [**photos**](adapters/deps/photos/) — When and where each photo was taken, as dated lines. Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**places**](adapters/stdlib/places/) — KML and GeoJSON files: each place's name, note and coordinates as a passage. *new* `no-install` `offline` `writes-output` `file-reader`
- **pocket** (idea) — Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone. *new* `no-install` `offline` `writes-output` `file-reader`
- **quiet-corner** (idea) — A Quiet Corner backup file: a teacher's classroom observations as dated passages, for that teacher's questions alone. *new* `no-install` `offline` `writes-output` `file-reader`
- **readwise** (idea) — Readwise's highlights export: every highlight with its book or article, and your note on it. *new* `no-install` `offline` `writes-output` `file-reader`
- **recipes** (idea) — Recipes from saved web pages and recipe-app exports, as plain text: what can I cook with leeks? *new* `no-install` `offline` `writes-output` `file-reader`
- **reddit** (idea) — Reddit's data export: your posts, comments and saved items as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**rtf**](adapters/stdlib/rtf/) — RTF documents as plain text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**sarif**](adapters/stdlib/sarif/) — SARIF reports from code scanners such as CodeQL and Semgrep: each finding as a passage with its rule and place. *new* `no-install` `offline` `writes-output` `file-reader`
- [**sbom**](adapters/stdlib/sbom/) — SBOMs in SPDX or CycloneDX JSON: each component, its version and licence, as passages. *new* `no-install` `offline` `writes-output` `file-reader`
- [**screenplay**](adapters/stdlib/screenplay/) — Fountain and Final Draft scripts: scenes, characters and lines, cited by scene. *new* `no-install` `offline` `writes-output` `file-reader`
- **scripture** (idea) — A scripture or other canonical text with your study notes beside it, cited by book, chapter and verse. *new* `no-install` `offline` `writes-output` `file-reader`
- **scrivener** (idea) — Scrivener projects: each document in the binder as plain text, by its place in the manuscript. *new* `no-install` `offline` `writes-output` `file-reader`
- [**sheets**](adapters/deps/sheets/) — Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. Needs openpyxl; MIT. *new* `needs-install` `offline` `writes-output` `file-reader`
- **shell-history** (idea) — Your bash, zsh and fish history: what you ran, and when the shell recorded it. *new* `no-install` `offline` `writes-output` `file-reader`
- **sigmap** (idea) — SigMap's signature map of a codebase as plain text: each function's signature with its file and line, for questions about the code. *new* `no-install` `offline` `writes-output` `file-reader`
- **signal** (idea) — A Signal backup, decrypted with its passphrase, as one dated line per message. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `writes-output` `file-reader`
- **slack** (idea) — Slack's export zip: one dated line per message, with channel and author. *new* `no-install` `offline` `writes-output` `file-reader`
- [**snapshot**](adapters/stdlib/snapshot/) — A web page or data file fetched once into a folder, as it came, with its address, the time and its SHA-256, so later answers cite the copy. Goes online: the address you give, fetched once. *bot* `no-install` `online` `writes-output` `file-reader` `sources`
- [**star-system**](adapters/deps/star-system/) — A friend's star-system simulation (science_bitch) run deterministically and written as cited passages: each body's Kepler period and how well the run conserves energy, angular momentum and linear momentum. Needs numpy; BSD-3-Clause. *bot* `needs-install` `offline` `writes-output`
- **steam** (idea) — Your Steam library from its local files: games, playtime and when you last played. *new* `no-install` `offline` `writes-output` `file-reader`
- **strava** (idea) — Strava's export and GPX files: each run, ride and walk as a dated line with its distance and time. *new* `no-install` `offline` `writes-output` `file-reader`
- [**subtitles**](adapters/stdlib/subtitles/) — Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed. *new* `no-install` `offline` `writes-output` `file-reader`
- **takeout** (idea) — Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **teams** (idea) — Microsoft Teams chats from your Microsoft account's export, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- **texts** (idea) — Phone text messages, from an Android SMS backup or an iPhone backup's copy, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- **trello** (idea) — A Trello board's JSON export: cards, checklists and comments, by list. *new* `no-install` `offline` `writes-output` `file-reader`
- **voice** (idea) — Dictation, calls and lectures transcribed into dated text. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `writes-output` `file-reader`
- [**wallabag**](adapters/stdlib/wallabag/) — wallabag's JSON or HTML export: saved entries as plain text, with their tags. *new* `no-install` `offline` `writes-output` `file-reader`
- [**web-pages**](adapters/stdlib/web-pages/) — Saved web pages, .html and .mhtml, as their readable text, with the address they came from. *new* `no-install` `offline` `writes-output` `file-reader`
- **writefreely** (idea) — WriteFreely posts, from its export or a copy of its SQLite database, as dated text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**x-archive**](adapters/stdlib/x-archive/) — An X (Twitter) archive: your posts, replies and DMs as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **zotero** (idea) — Your Zotero library, from a copy of zotero.sqlite: items, notes and PDF annotations, each with its citation. *new* `no-install` `offline` `writes-output` `file-reader`

## Finding things

- [**all**](adapters/stdlib/all/) — Every matching passage, ranked, not just the top three. *box* `no-install` `offline` `read-only` `search`
- [**amounts**](adapters/stdlib/amounts/) — Every sum of money in your files, with its date and the line it's on. *new* `no-install` `offline` `read-only` `search`
- **bm25** (idea) — A BM25 rank from SQLite's own full-text index, beside the kernel's words rank: rare words weigh more. *new* `no-install` `offline` `read-only` `search`
- **by-function** (idea) — Code read by function and class instead of by line, so a hit names the function it's in. Needs tree-sitter and its language pack; MIT. *new* `needs-install` `offline` `writes-output` `search`
- **code-first** (idea) — Questions code can answer exactly (counts, dates, ids) answered by code before any model, with a wrong answer counted as a defect. *bot* `no-install` `offline` `read-only` `search`
- **code-shape** (idea) — Search code by its shape, not its words: every call of a kind, whatever it's named. Needs the ast-grep program; MIT. *new* `needs-install` `offline` `read-only` `search`
- [**codeowners**](adapters/stdlib/codeowners/) — Who owns this file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo alike. *new* `no-install` `offline` `read-only` `search`
- **crosswalk** (idea) — The outside IDs a passage points to (Wikidata, DOI, ORCID, GeoNames) kept beside it, so your notes join the world's. *new* `no-install` `offline` `writes-output` `search`
- [**duplicates**](adapters/stdlib/duplicates/) — Passages that say the same thing in two files, and which one is newer. *new* `no-install` `offline` `read-only` `search`
- [**fair-merge**](adapters/stdlib/fair-merge/) — Each folder or repo ranked on its own and the lists merged in turns, so a large corpus can't push a small one out on volume alone, and a source that found nothing says so. *bot* `no-install` `offline` `read-only` `search` `pile`
- [**first-mention**](adapters/stdlib/first-mention/) — When your files first mention something, and the line that does. *new* `no-install` `offline` `read-only` `search`
- [**fuzzy-dates**](adapters/stdlib/fuzzy-dates/) — Dates that admit doubt ('about 1880', 'sometime in March') read and kept with their doubt, in EDTF. *new* `no-install` `offline` `read-only` `search`
- [**index-cache**](adapters/stdlib/index-cache/) — The box's index kept between runs and checked against each file's hash, so a question doesn't re-read the folder unless the folder changed. *new* `no-install` `offline` `writes-output` `search` `index`
- **kiwix** (idea) — An offline Wikipedia (or Stack Exchange, or Gutenberg) as a source after your own files, cited by article. Needs libzim, and a ZIM file you download; GPL-3.0. *new* `needs-install` `offline` `read-only` `search`
- [**latent**](adapters/deps/latent/) — Rank a scan index by meaning, not just words: a question reaches code that shares its sense without sharing its words. Needs numpy; BSD-3-Clause. *new* `needs-install` `offline` `read-only` `search`
- **meaning** (idea) — Search by meaning: "who owes me money" finds "invoice outstanding". Needs sentence-transformers; Apache-2.0. Goes online: the model, downloaded once from Hugging Face. *new* `needs-install` `online` `writes-output` `search`
- [**misquote**](adapters/stdlib/misquote/) — A quote that is almost in your files: the closest passage, and the words it adds, drops or changes, so a misquote shows as one. *new* `no-install` `offline` `read-only` `search`
- **my-lessons** (idea) — Your own lesson plans by grade, subject and standard: what did I teach on fractions last year? *new* `no-install` `offline` `read-only` `search`
- [**on-this-day**](adapters/stdlib/on-this-day/) — What you wrote on this date in earlier years. *box* `no-install` `offline` `read-only` `search`
- [**people**](adapters/stdlib/people/) — Everyone your files name, and every place each is mentioned. *new* `no-install` `offline` `read-only` `search`
- [**pile-build**](adapters/stdlib/pile-build/) — The store built after each change, behind a lock, until it matches the folder, so your next question finds it warm. *bot* `no-install` `offline` `writes-output` `search` `pile`
- [**pile-gold**](adapters/stdlib/pile-gold/) — Each answer you approve marks the passage that held it, so your own questions become a test of how well the search finds things, scored as recall at five. *box* `no-install` `offline` `records` `search` `pile`
- [**pile-rank**](adapters/stdlib/pile-rank/) — Phrases as well as words: BM25F over each passage's words and the word pairs your files use together, title and question lines weighted, no model. *bot* `no-install` `offline` `read-only` `search` `pile`
- [**pile-rungs**](adapters/stdlib/pile-rungs/) — Each lookup says which rung answered, words, phrases or an embedder, and why a higher one was skipped, as data beside the passages. *bot* `no-install` `offline` `read-only` `search` `pile`
- [**pile-serve**](adapters/stdlib/pile-serve/) — The store held open by one process on this machine, over a Unix socket the way willow-bot's deterministic runner serves, so a hook's lookup takes milliseconds instead of a cold start. *bot* `no-install` `offline` `writes-output` `search` `pile`
- [**pile-store**](adapters/stdlib/pile-store/) — Your folder's passages read once into one SQLite file, each repeat stored once, and opened read-only only while it still matches the folder, the limits and the kernel that read it, else built again. *bot* `no-install` `offline` `writes-output` `search` `pile`
- [**pile-sweep**](adapters/stdlib/pile-sweep/) — The passage size measured, not guessed: your box's own questions asked at several sizes, and the size that finds the most of their answers named. *bot* `no-install` `offline` `read-only` `search` `pile`
- **promises** (idea) — What a candidate or a council said, by date and source, from the documents you saved. *new* `no-install` `offline` `read-only` `search`
- [**quote-check**](adapters/stdlib/quote-check/) — Is this exact quote in my files, and where? For writers, journalists and students. *box* `no-install` `offline` `read-only` `search`
- [**reading-level**](adapters/stdlib/reading-level/) — How hard a passage reads (sentence length, word length, Flesch), so a teacher can find texts for a class. *new* `no-install` `offline` `read-only` `search`
- [**record-sql**](adapters/deps/record-sql/) — SQL straight over your record, in place: 'how many answers did I approve in March?' Needs DuckDB; MIT. *box* `needs-install` `offline` `read-only` `search`
- **rerank** (idea) — A small model on the CPU that reorders the top passages by reading the question and each passage together. Needs FlashRank; Apache-2.0. Goes online: the model, downloaded once. *new* `needs-install` `online` `read-only` `search`
- **ripgrep** (idea) — Exact search through ripgrep, much faster on a big folder, its hits checked against the kernel's hashes. Needs the ripgrep program; MIT or Unlicense. *new* `needs-install` `offline` `read-only` `search`
- [**said**](adapters/stdlib/said/) — Your own quotes, gathered: every 'so-and-so, on this date: "..."' in your files, as a dated timeline of what was decided. *new* `no-install` `offline` `read-only` `search`
- [**scan**](adapters/stdlib/scan/) — Index a big folder once, then ask it a list of questions in seconds, with the kernel's own answers: of everything, or only what changed since another index. *box* `no-install` `offline` `writes-output` `search` `index`
- **standards** (idea) — Curriculum standards beside your lessons: which standard each lesson meets, each cited. *new* `no-install` `offline` `read-only` `search`
- [**surprise**](adapters/stdlib/surprise/) — One passage from your folder at random, seeded so it can be replayed. *bot* `no-install` `offline` `records` `search`
- **symbols** (idea) — Exact definitions and references for Python code: where a name is defined, and every place it's used. Needs scip-python; MIT. *new* `needs-install` `offline` `read-only` `search`
- [**typos**](adapters/stdlib/typos/) — Forgives misspellings in questions. *new* `no-install` `offline` `read-only` `search`
- **upgrade-notes** (idea) — Before an upgrade: the changelog lines between the version you lock and the one you'd move to, from the package's own files. Goes online: the registry (PyPI, npm or crates.io), to fetch the newer version's changelog. *new* `no-install` `online` `read-only` `search`
- **vectors** (idea) — The meaning add-on's vectors kept in the store's own SQLite file, so they're computed once per passage, not at every question. Needs sqlite-vec and model2vec; MIT or Apache-2.0. *bot* `needs-install` `offline` `writes-output` `search` `pile`
- **watch** (idea) — A file re-read the moment it changes (inotify, FSEvents, or polling), so the index is always current. *new* `no-install` `offline` `writes-output` `search`
- [**why-not**](adapters/stdlib/why-not/) — When the answer is 'not enough to say', which words found nothing, and what kind of file would have answered. *new* `no-install` `offline` `read-only` `search`

## Your own words

The blind tests' biggest gap: on day one, a person's words aren't their files' words.

- [**abbreviations**](adapters/stdlib/abbreviations/) — Your own shorthand, written down once (appt, Rx, w/c), so a question finds either form. *new* `no-install` `offline` `writes-output` `words`
- [**accents**](adapters/stdlib/accents/) — A word typed without its accent read as your files write it, and the words-list lines that make it last. *new* `no-install` `offline` `read-only` `words`
- [**dialect**](adapters/deps/dialect/) — The words you use far more than the world does: your own dialect, from your files against wordfreq's counts. Needs wordfreq; Apache-2.0, its data CC BY-SA 4.0. *new* `needs-install` `offline` `read-only` `words`
- **memoir** (idea) — A question a week about your life, answered in your own words and kept, so your story is in your files. *new* `no-install` `offline` `writes-output` `words`
- [**nicknames**](adapters/stdlib/nicknames/) — The names you call people, mapped to who they are, so 'Mum' finds Margaret. *new* `no-install` `offline` `writes-output` `words`
- [**starter-words**](adapters/stdlib/starter-words/) — A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic). *new* `no-install` `offline` `writes-output` `words`
- [**stems**](adapters/deps/stems/) — Word forms for 20+ languages, so "häuser" finds "haus" and "книги" finds "книга". Needs snowballstemmer; BSD-3-Clause. *new* `needs-install` `offline` `read-only` `words`
- **synonyms** (idea) — Suggests words-list lines for a word no file has. Needs nltk and WordNet; Apache-2.0. Goes online: the WordNet data, downloaded once. *new* `needs-install` `online` `writes-output` `words`
- **tatoeba** (idea) — A question in one language finds the same idea in another, through Tatoeba's sentence pairs, downloaded once. *new* `no-install` `offline` `writes-output` `words`
- **vocab** (idea) — The words you're learning, from your notes and the texts you read, with where you met each one. *new* `no-install` `offline` `writes-output` `words`
- [**words-ar**](adapters/stdlib/words-ar/) — Arabic common words ("في", "من", "على"). *new* `no-install` `offline` `records` `words` `arabic`
- [**words-cy**](adapters/stdlib/words-cy/) — Welsh common words ("a", "y", "yn"). *new* `no-install` `offline` `records` `words` `welsh`
- [**words-de**](adapters/stdlib/words-de/) — German common words, so questions aren't matched on "der" and "und". *new* `no-install` `offline` `records` `words` `german`
- [**words-es**](adapters/stdlib/words-es/) — Spanish common words ("el", "y"). *new* `no-install` `offline` `records` `words` `spanish`
- [**words-fr**](adapters/stdlib/words-fr/) — French common words ("le", "et"). *new* `no-install` `offline` `records` `words` `french`
- **words-hi** (idea) — Hindi common words ('और', 'है'). *new* `no-install` `offline` `writes-output` `words`
- [**words-it**](adapters/stdlib/words-it/) — Italian common words ("il", "e"). *new* `no-install` `offline` `records` `words` `italian`
- **words-ja** (idea) — Japanese, which has no spaces: a small segmenter of its own and a common-words list. *new* `no-install` `offline` `writes-output` `words`
- [**words-nl**](adapters/stdlib/words-nl/) — Dutch common words ("de", "en"). *new* `no-install` `offline` `records` `words` `dutch`
- [**words-pl**](adapters/stdlib/words-pl/) — Polish common words ('i', 'w'). *new* `no-install` `offline` `records` `words` `polish`
- [**words-pt**](adapters/stdlib/words-pt/) — Portuguese common words ("o", "e"). *new* `no-install` `offline` `records` `words` `portuguese`
- [**words-ru**](adapters/stdlib/words-ru/) — Russian common words ("и", "в", "на"). *new* `no-install` `offline` `records` `words` `russian`
- [**words-sv**](adapters/stdlib/words-sv/) — Swedish common words ('och', 'att'). *new* `no-install` `offline` `records` `words` `swedish`
- [**words-tr**](adapters/stdlib/words-tr/) — Turkish common words ("ve", "bir"). *new* `no-install` `offline` `records` `words` `turkish`
- **words-zh** (idea) — Chinese, which has no spaces: words found by a small segmenter of its own, and a common-words list. *new* `no-install` `offline` `writes-output` `words`

## Keeping track

- [**across**](adapters/stdlib/across/) — One document across several boxes, not just one: each box's digest, export, timeline or readings, composed into one page, every line still cited by its box, file and line. *new* `no-install` `offline` `read-only` `tracking` `everyday`
- [**again**](adapters/stdlib/again/) — Questions you keep asking: "asked 4 times; approve an answer?" *bot* `no-install` `offline` `read-only` `tracking`
- **ask-later** (idea) — A question with no answer yet kept on a list, and asked again whenever a new file arrives. *new* `no-install` `offline` `records` `tracking`
- [**attendance**](adapters/stdlib/attendance/) — Attendance for a class, club or group, from your register, by week. *new* `no-install` `offline` `read-only` `tracking`
- [**baby-log**](adapters/stdlib/baby-log/) — Feeds, sleeps and nappies from your notes, by day: when was the last one? *new* `no-install` `offline` `read-only` `tracking`
- [**budget**](adapters/stdlib/budget/) — Spending against the budget you wrote down, month by month, from your statements. *new* `no-install` `offline` `read-only` `tracking`
- [**car**](adapters/stdlib/car/) — Your car's services, repairs and inspection dates, from receipts and notes: what's due, and what it cost. *new* `no-install` `offline` `read-only` `tracking`
- **care** (idea) — For caregivers: medications, vitals and appointments from a care log, what's due and what moved. *box* `no-install` `offline` `read-only` `tracking`
- [**coming-up**](adapters/stdlib/coming-up/) — Dates written in your files in the next N days: appointments, renewals, deadlines. *box* `no-install` `offline` `read-only` `tracking`
- **contracts** (idea) — The dates that matter in your contracts: renewals, notice periods and break clauses, each cited. *new* `no-install` `offline` `read-only` `tracking`
- **crowd** (idea) — You against the crowd: a prediction market's question copied into your ledger, your probability beside theirs, both scored. Goes online: the market's public API, to read the question and its resolution. *new* `no-install` `online` `records` `tracking`
- **cycle** (idea) — A menstrual cycle log that never leaves this machine: dates, what's next, and what changed. *new* `no-install` `offline` `read-only` `tracking`
- [**debts**](adapters/stdlib/debts/) — Who owes whom, from the IOUs in your notes and messages, each cited. *new* `no-install` `offline` `read-only` `tracking`
- [**digest**](adapters/stdlib/digest/) — One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that keep finding nothing. *bot* `no-install` `offline` `read-only` `tracking` `everyday`
- **flashcards** (idea) — Approved question-and-answer pairs become cards, scheduled by spaced repetition. *box* `no-install` `offline` `records` `tracking`
- [**foia**](adapters/stdlib/foia/) — Freedom-of-information requests: what you asked, when, and when the answer is due by law. *new* `no-install` `offline` `read-only` `tracking`
- **food-log** (idea) — What you ate, from your notes, by day. *new* `no-install` `offline` `read-only` `tracking`
- **forecasts** (idea) — Write a prediction before the outcome, settle it later, see your Brier score. *bot* `no-install` `offline` `records` `tracking`
- [**gaps**](adapters/stdlib/gaps/) — Where a log you keep stops: the days a daily note, reading or diary skipped, said as gaps, not left out. *new* `no-install` `offline` `read-only` `tracking` `journal`
- [**garden**](adapters/stdlib/garden/) — What you planted, where and when, and how it did, season by season. *new* `no-install` `offline` `read-only` `tracking`
- **gifts** (idea) — Gifts given and received, and who likes what, so nobody gets the same scarf twice. *new* `no-install` `offline` `read-only` `tracking`
- [**gradebook**](adapters/stdlib/gradebook/) — A teacher's gradebook, kept on this machine: each student's marks by assignment, and who is falling behind. *new* `no-install` `offline` `read-only` `tracking`
- **grant-report** (idea) — For charities and groups: what you promised a funder and what you did, side by side, each cited. *new* `no-install` `offline` `read-only` `tracking`
- [**habits**](adapters/stdlib/habits/) — Streaks from the lines you write each day: how many days in a row, and which you missed. *new* `no-install` `offline` `read-only` `tracking`
- [**home-upkeep**](adapters/stdlib/home-upkeep/) — Home upkeep: the boiler service, the filters, the gutters, what's due and when it was last done. *new* `no-install` `offline` `read-only` `tracking`
- [**hours**](adapters/stdlib/hours/) — Hours worked or volunteered, per client or group, from your notes. *new* `no-install` `offline` `read-only` `tracking`
- **inventory** (idea) — What you own, where it is, and where its papers are, for insurance or a will. *new* `no-install` `offline` `read-only` `tracking`
- **invoices** (idea) — For freelancers: invoices and payments matched by the id pattern you give, never guessed. *new* `no-install` `offline` `read-only` `tracking`
- [**job-hunt**](adapters/stdlib/job-hunt/) — Applications sent, replies and interviews, by date: who you're still waiting on. *new* `no-install` `offline` `read-only` `tracking`
- **lab-notebook** (idea) — A lab notebook's dated entries, by sample and experiment: what was done to what, and when. *new* `no-install` `offline` `read-only` `tracking`
- [**lending**](adapters/stdlib/lending/) — Things you lent, to whom and when, and which are still out. *new* `no-install` `offline` `read-only` `tracking`
- [**livestock**](adapters/stdlib/livestock/) — Each animal's births, treatments and sales, from your farm records. *new* `no-install` `offline` `read-only` `tracking`
- **market-calls** (idea) — Market calls kept as wagers on the record ('SPY closes up on Friday'), settled later, with the losers kept. *bot* `no-install` `offline` `records` `tracking`
- [**mileage**](adapters/stdlib/mileage/) — Miles driven for work, from your trips and notes, totalled for a tax year. *new* `no-install` `offline` `read-only` `tracking`
- [**milestones**](adapters/stdlib/milestones/) — Your child's firsts, words and heights, from your notes, by age. *new* `no-install` `offline` `read-only` `tracking`
- [**minutes**](adapters/stdlib/minutes/) — Meeting minutes: who decided what and when, and which actions are still open. *new* `no-install` `offline` `read-only` `tracking`
- [**mood**](adapters/stdlib/mood/) — Mood scores you write in a journal, over weeks and months. *new* `no-install` `offline` `read-only` `tracking`
- **oakenscroll** (idea) — Oakenscroll's Office calibration ledger: what you believed, how hard, and how it resolved, as dated passages. *new* `no-install` `offline` `writes-output` `tracking`
- [**outdated**](adapters/stdlib/outdated/) — How old each locked dependency is, and which are yanked, deprecated or two years without a release, from a registry index you downloaded. *new* `no-install` `offline` `read-only` `tracking`
- [**pets**](adapters/stdlib/pets/) — Each pet's vet visits, vaccines and medicines, from your records: what's due next. *new* `no-install` `offline` `read-only` `tracking`
- [**policy-watch**](adapters/stdlib/policy-watch/) — A terms or policy page fetched each time you run it, by snapshot, and what changed since last time, sentence by sentence, by clauses. Goes online: the page you name, fetched each time you run it. *new* `no-install` `online` `writes-output` `tracking` `policies`
- **predict** (idea) — Write down what you'll do next before you do it, and grade it after; the record counts how often you were right. *bot* `no-install` `offline` `records` `tracking`
- [**reading-log**](adapters/stdlib/reading-log/) — A child's reading log: books, pages and minutes, week by week. *new* `no-install` `offline` `read-only` `tracking`
- [**readings**](adapters/stdlib/readings/) — Numbers over time and a date gone by, beside an answer. *box* `no-install` `offline` `records` `tracking`
- [**renewals**](adapters/stdlib/renewals/) — Passports, licences, insurance and memberships: when each expires, from your documents. *new* `no-install` `offline` `read-only` `tracking`
- **rubric** (idea) — Marking against a rubric you wrote: each mark cites the criterion and the line of work it's for. *new* `no-install` `offline` `read-only` `tracking`
- **school** (idea) — School letters and emails for parents: trips, forms due, term dates, and what to bring. *new* `no-install` `offline` `read-only` `tracking`
- **session-cost** (idea) — Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep. *new* `no-install` `offline` `read-only` `tracking`
- [**stack**](adapters/stdlib/stack/) — One document from a stack of add-on steps over a box: each step's output grouped into pools and ordered tallest-first, so the peaks are what a reader meets first. *new* `no-install` `offline` `read-only` `tracking`
- [**subscriptions**](adapters/stdlib/subscriptions/) — What you pay for every month, found in bank statements and emails, and when each renews. *new* `no-install` `offline` `read-only` `tracking`
- **support-plan** (idea) — An IEP or support plan's goals, accommodations and review dates, each cited, for a parent or teacher. *new* `no-install` `offline` `read-only` `tracking`
- [**syllabus**](adapters/stdlib/syllabus/) — A course syllabus as dates: readings, assignments and exams due, each cited. *new* `no-install` `offline` `read-only` `tracking`
- [**symptoms**](adapters/stdlib/symptoms/) — A symptom diary over time, ready to show a doctor: what, when, how bad, each line cited. *new* `no-install` `offline` `read-only` `tracking`
- **tax-year** (idea) — One tax year's receipts and statements gathered in one place, each with the file it came from. *new* `no-install` `offline` `read-only` `tracking`
- [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first. *box* `no-install` `offline` `read-only` `tracking`
- **trips** (idea) — Your trips from booking emails and tickets: where you went, when, and where you stayed. *new* `no-install` `offline` `read-only` `tracking`
- **upstream-desk** (idea) — Your work in other people's projects, in one place: notifications sorted into what needs you, and your open pull requests there. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `read-only` `tracking`
- [**warranties**](adapters/stdlib/warranties/) — Receipts and warranties: when the dishwasher's cover ends, and where its receipt is. *new* `no-install` `offline` `read-only` `tracking`

## Trust and proof

- [**backup**](adapters/stdlib/backup/) — Your record in one zip, every byte and the chain checked before it's kept; never beside your key, and it never reads the key. *new* `no-install` `offline` `writes-output` `trust` `everyday`
- [**box-health**](adapters/stdlib/box-health/) — A box's health in one line: files it can't read, readers out of date, and when the chain was last checked. *new* `no-install` `offline` `read-only` `trust`
- [**changed**](adapters/stdlib/changed/) — What's new, edited or deleted in your folder since the last check, as fingerprint rows. *bot* `no-install` `offline` `records` `trust` `everyday`
- [**claim-check**](adapters/stdlib/claim-check/) — A claim checked against your sources: the passages that hold all of its parts, the ones that hold only some, and the parts no file names. *new* `no-install` `offline` `read-only` `trust`
- [**contradictions**](adapters/stdlib/contradictions/) — Two passages that disagree about the same date or amount, side by side. *new* `no-install` `offline` `read-only` `trust`
- [**diverge**](adapters/stdlib/diverge/) — Where two copies of a folder or a box part, a backup zip included, narrowed to the first row, file and line that differ. *bot* `no-install` `offline` `read-only` `trust` `everyday`
- **encrypt** (idea) — Keeps the record folder encrypted at rest. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `records` `trust`
- [**export**](adapters/stdlib/export/) — Approved answers, and the question log (counts only, never words), as Markdown or CSV. *box* `no-install` `offline` `read-only` `trust`
- **family-box** (idea) — One box for a household: each person's own seal, and every answer showing whose it is. *new* `no-install` `offline` `records` `trust`
- **git-notes** (idea) — Approved answers kept as git notes on the commits they cite, so they travel with the repo to any forge. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `trust`
- **handoff** (idea) — A box handed to the person you name (an executor, a carer): read only, your seals kept, theirs their own. *new* `no-install` `offline` `records` `trust`
- [**history**](adapters/stdlib/history/) — Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words. *new* `no-install` `offline` `read-only` `trust` `everyday`
- [**ids**](adapters/stdlib/ids/) — Every file and passage given its Software Heritage ID and IPFS CID, names the rest of the world already uses. *new* `no-install` `offline` `read-only` `trust`
- **in-case** (idea) — A letter for the people you trust, if something happens to you: where things are and who to call, from your files, sealed by you. *new* `no-install` `offline` `writes-output` `trust`
- [**in-toto**](adapters/stdlib/in-toto/) — A sealed answer exported as an in-toto Statement, the envelope SLSA uses, so others can check it. *new* `no-install` `offline` `writes-output` `trust`
- **jeles** (idea) — Your approved answers as Jeles nuggets, with question, answer, sources and who sealed it, and Jeles' own verified nuggets read back as passages. *new* `no-install` `offline` `writes-output` `trust`
- [**licenses**](adapters/stdlib/licenses/) — The licence of every installed dependency, read from its own metadata on this machine: which are copyleft, and which file says so. *new* `no-install` `offline` `read-only` `trust`
- **line-origin** (idea) — Which agent session wrote this line of code: git blame to the commit, then the transcript turn that made it. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `read-only` `trust`
- **losc** (idea) — Does a project pass the Local Only Servers Club's test: no accounts, no cloud, and your data your own? *bot* `no-install` `offline` `read-only` `trust`
- [**merkle**](adapters/stdlib/merkle/) — A Merkle tree over the record, so one row can be proven with a handful of hashes, not the whole file. *new* `no-install` `offline` `writes-output` `trust`
- **mirror** (idea) — Checks each mirror of a repo on another forge holds the same commits as the original, so losing a host loses nothing. Needs the git program; GPL, called not linked. Goes online: each mirror's git URL, to read its refs. *new* `needs-install` `online` `read-only` `trust`
- **nestor** (idea) — Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when. *new* `no-install` `offline` `writes-output` `trust`
- **notary** (idea) — The record's newest hash timestamped by an outside time server, so anyone can see it existed by then. Goes online: an RFC 3161 time server you choose, sent only the hash. *new* `no-install` `online` `records` `trust`
- **opentimestamps** (idea) — The record's newest hash anchored by OpenTimestamps, proof that it existed by a given block. Goes online: the OpenTimestamps calendars, sent only the hash. *new* `no-install` `online` `records` `trust`
- **paper-key** (idea) — Your key printed as words on paper, to keep somewhere safe, and typed back in to restore it. *new* `no-install` `offline` `writes-output` `trust`
- **pgp** (idea) — Signs exports and reports with your PGP key, verifiable anywhere. Needs the gpg program and python-gnupg; BSD. *new* `needs-install` `offline` `writes-output` `trust`
- [**prov**](adapters/stdlib/prov/) — The record exported as W3C PROV: what came from what, by which step, sealed by whom. *new* `no-install` `offline` `writes-output` `trust`
- **provenance** (idea) — Checks a package's Sigstore provenance or PyPI attestation names the repo and commit it claims, before you trust it. Needs sigstore; Apache-2.0. Goes online: the registry and Sigstore's log, to fetch the attestation. *new* `needs-install` `online` `read-only` `trust`
- **quote-review** (idea) — A review comment that quotes the repo, checked: does the quoted line still say that at the pull request's head? Goes online: the forge, through the workflow's token, to read the review comments. *new* `no-install` `online` `read-only` `trust`
- **redential** (idea) — The bundle redential-cli's scan makes, written to the record before you submit it, so what left your machine can be checked later. Needs the redential program, run through npx; Apache-2.0. *new* `needs-install` `offline` `records` `trust`
- **report** (idea) — A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. *box* `no-install` `offline` `writes-output` `trust`
- **retire** (idea) — Proposes setting aside approved answers that no longer hold, each one gone only when you seal it. *bot* `no-install` `offline` `records` `trust`
- [**ro-crate**](adapters/stdlib/ro-crate/) — A box snapshot as an RO-Crate research object Zenodo can read: each file with its hash and licence. *new* `no-install` `offline` `writes-output` `trust`
- **sap-gate** (idea) — The mcp add-on's tool calls checked against SAP/1.0 grants before they run, through openclaw-sap-gate. Needs openclaw-sap-gate; MIT. *new* `needs-install` `offline` `read-only` `trust`
- [**session-seal**](adapters/stdlib/session-seal/) — One seal at the end of a session, over everything asked and approved in it: yes, these were my actions. *bot* `no-install` `offline` `records` `trust`
- **signed-commits** (idea) — Which commits are signed, and by whose key, checked on this machine against the keys you trust. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `read-only` `trust`
- [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. *box* `no-install` `offline` `read-only` `trust`
- **sync** (idea) — Your record kept on two devices through any synced folder, with the chain checked on each before it's trusted. *new* `no-install` `offline` `records` `trust`
- **thesis** (idea) — A thesis's claims, each tied to the source that backs it, and a list of the ones with none. *new* `no-install` `offline` `read-only` `trust`
- **time-capsule** (idea) — A note sealed now and opened on a date you choose, with the record proving it wasn't changed. *new* `no-install` `offline` `records` `trust`
- [**timeline**](adapters/stdlib/timeline/) — A dated timeline of one matter (a dispute, an illness, a tenancy), every line cited, to hand to a lawyer, doctor or council. *new* `no-install` `offline` `writes-output` `trust`
- [**tip-pin**](adapters/stdlib/tip-pin/) — Where a box's record ends, kept outside the box, so rows cut off or a whole chain re-hashed are found where verify can't. *new* `no-install` `offline` `writes-output` `trust`
- [**wayback**](adapters/stdlib/wayback/) — The Wayback Machine's copy of a page from a window of days, saved beside your own snapshot and compared with it byte for byte. Goes online: archive.org, to find the archived copy and fetch it. *new* `no-install` `online` `writes-output` `trust` `sources`
- **witness** (idea) — A second person's seal beside yours, for answers that need two people to agree. *new* `no-install` `offline` `records` `trust`
- [**xref**](adapters/stdlib/xref/) — Every reference in your files checked: each link to another file, and each quoted line, still there and still saying it. *bot* `no-install` `offline` `read-only` `trust` `everyday`

## Privacy and safety

- [**a11y-check**](adapters/stdlib/a11y-check/) — Your documents checked for screen-reader problems: images without descriptions, headings out of order. *new* `no-install` `offline` `read-only` `privacy`
- [**advisories**](adapters/stdlib/advisories/) — Security advisories from a downloaded OSV or GitHub advisory database, matched to your lockfiles: which dependency each names, and since when. *new* `no-install` `offline` `read-only` `privacy`
- **forget** (idea) — Stops a file being searched, recorded on the chain, so what was taken out is known and nothing else is touched. *new* `no-install` `offline` `records` `privacy`
- [**install-scripts**](adapters/stdlib/install-scripts/) — The install scripts the packages in node_modules would run (preinstall, install, postinstall), each cited by file and line. *new* `no-install` `offline` `read-only` `privacy`
- **kids** (idea) — A box for a child: answers only from the folder you choose for them, and nothing they can approve. *new* `no-install` `offline` `read-only` `privacy`
- [**package-contents**](adapters/stdlib/package-contents/) — What's inside a wheel, sdist, npm tarball or .crate before you install it: every file, and any code it runs on install. *new* `no-install` `offline` `read-only` `privacy`
- [**pii-audit**](adapters/stdlib/pii-audit/) — Personal data sitting in your files (ID numbers, health details, card numbers), listed by file and line. *new* `no-install` `offline` `read-only` `privacy`
- [**privacy**](adapters/stdlib/privacy/) — Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. *bot* `no-install` `offline` `records` `privacy`
- [**risky-code**](adapters/stdlib/risky-code/) — Lines of code matching a known-dangerous pattern (command injection, eval, sql concatenation, broken tls and more), by file and line, as leads to read. *new* `no-install` `offline` `read-only` `security`
- [**scrub**](adapters/stdlib/scrub/) — Strips the hidden details (EXIF, author, edit history) from a file before you share it. *new* `no-install` `offline` `writes-output` `privacy`
- [**secrets-audit**](adapters/stdlib/secrets-audit/) — Finds passwords, keys and card numbers sitting in plain files, by file and line, never showing the value. *bot* `no-install` `offline` `read-only` `privacy` `everyday`
- **student-records** (idea) — A box of student records that answers only the teacher who owns it, and logs every look. *new* `no-install` `offline` `records` `privacy`
- [**transcript-redact**](adapters/stdlib/transcript-redact/) — An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line. *new* `no-install` `offline` `writes-output` `privacy`
- [**typosquat**](adapters/stdlib/typosquat/) — Dependency names a letter off from a popular one (reqeusts, lodahs), checked against a list of top packages you downloaded. *new* `no-install` `offline` `read-only` `privacy`

## Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal.

- [**aider**](adapters/stdlib/aider/) — Aider reads answers from your folder with its /run command, file and line included. *new* `no-install` `offline` `read-only` `assistant`
- **assistant-scores** (idea) — How often each assistant's suggestions were sealed or set aside, from the record. *new* `no-install` `offline` `read-only` `assistant`
- **basic-memory** (idea) — Basic Memory's Markdown notes where an AI wrote them: each observation and relation handed in through propose, waiting for your seal. *new* `no-install` `offline` `records` `assistant`
- **cassettes** (idea) — Each exchange with a model kept as a row (what was asked, what came back, the model and its seed), replayed later as a test, and drift between models found by plain diff. *bot* `no-install` `offline` `records` `assistant`
- **claude** (idea) — Suggestions from Claude through the Anthropic API, citing your passages. Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `records` `assistant`
- [**claude-code**](adapters/stdlib/claude-code/) — Claude Code sees cited passages from your folder with each prompt, through its prompt hook. *bot* `no-install` `offline` `records` `assistant`
- [**codex-cli**](adapters/stdlib/codex-cli/) — OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**copilot**](adapters/stdlib/copilot/) — GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**cursor**](adapters/stdlib/cursor/) — Cursor asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**gemini-cli**](adapters/stdlib/gemini-cli/) — Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- **hermes** (idea) — Hermes Agent asking your folder as a plugin, and its memories, and what its dreaming plugin consolidates, handed in through propose. *new* `no-install` `offline` `records` `assistant`
- **hook-checks** (idea) — A PostToolUse hook that runs the repo's own fast checks on the file just edited and hands back only what failed, the same output for the same file. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- **hook-cite** (idea) — A hook that refuses an assistant's claim citing a passage the box never served it, checked against the record by id. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-compact**](adapters/stdlib/hook-compact/) — A PreCompact hook that prints what the record still holds open, seals waiting and questions unanswered, so it survives the assistant's summary. *box* `no-install` `offline` `read-only` `assistant` `hooks`
- **hook-errors** (idea) — Each failed command an assistant runs kept as a row of its hash and exit code, so the same failure the third time is named, not retried blind. *new* `no-install` `offline` `records` `assistant` `hooks`
- [**hook-fail-closed**](adapters/stdlib/hook-fail-closed/) — Wraps any hook so a crash, a timeout or output it can't read blocks the tool, since Claude Code, Gemini CLI, Codex and Cursor all let the tool run by default. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- **hook-feedback** (idea) — Your corrections to an assistant (no, wrong, I said) caught by fixed patterns at each prompt and handed in through propose, for you to keep or drop. *new* `no-install` `offline` `records` `assistant` `hooks`
- [**hook-fuzz**](adapters/stdlib/hook-fuzz/) — Throws empty, malformed, oversized and non-UTF-8 input at a hook and fails it if any of them crash it, since a crashed hook lets the tool run. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-guard**](adapters/stdlib/hook-guard/) — A PreToolUse hook that refuses, by rule and never by judgment, a tool call that would read the key or write a box outside the kernel, naming the rule it hit. *box* `no-install` `offline` `read-only` `assistant` `hooks`
- **hook-handoff** (idea) — A Stop hook that writes where the session ended, and the next session's first prompt gets it back, so nothing rides on the assistant's memory. *new* `no-install` `offline` `records` `assistant` `hooks`
- [**hook-impact**](adapters/stdlib/hook-impact/) — Before an edit, a hook hands the assistant every place in your files that names what it's about to change, by file and line. *box* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-leaks**](adapters/stdlib/hook-leaks/) — A PreToolUse hook that refuses a write or a command holding a key, password or card number, by the privacy add-on's shapes, naming only the kind. *box* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-pin**](adapters/stdlib/hook-pin/) — Each hook's SHA-256 kept on the record when you approve it, so a hook that changed since is named before it runs, never silently trusted or skipped. *new* `no-install` `offline` `records` `assistant` `hooks`
- **hook-read-first** (idea) — A PreToolUse hook that refuses an edit to a file the assistant hasn't read this session, or whose bytes changed since it did, each read kept as a hash. *new* `no-install` `offline` `records` `assistant` `hooks`
- [**hook-replay**](adapters/stdlib/hook-replay/) — Every hook's answer kept as a row with the hashes of what it was given and what it said, and check runs it again to prove the same input still gets the same answer. *new* `no-install` `offline` `records` `assistant` `hooks`
- **hook-sequence** (idea) — Rules over what an assistant did before, not just this call: no push until the tests ran on this commit, at most so many deletions a session, read from the record. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-shell**](adapters/stdlib/hook-shell/) — A command split the way the shell will split it, quotes, variables and chained commands included, before any rule judges it, so a rule can't be dodged by spelling. *new* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-start**](adapters/stdlib/hook-start/) — A SessionStart hook that hands the assistant what needs you, read the way digest reads it, so opening a session writes nothing. *bot* `no-install` `offline` `read-only` `assistant` `hooks`
- [**hook-stop**](adapters/stdlib/hook-stop/) — A Stop hook that won't let an assistant's turn end while the record doesn't verify or its changes aren't committed, and says which. *box* `no-install` `offline` `read-only` `assistant` `hooks`
- **hook-tiers** (idea) — Edits sorted into tiers by the paths they touch, and the top tier held as a proposal until you seal it, by a rule you can read. *new* `no-install` `offline` `records` `assistant` `hooks`
- **hooks-elsewhere** (idea) — The prompt hook for Gemini CLI, Codex and opencode, wherever they take hooks, held to Claude Code's answer byte for byte. *box* `no-install` `offline` `records` `assistant` `hooks`
- [**hosts**](adapters/stdlib/hosts/) — One table of the assistants that take an MCP server, printing the lines that register willow with any of them. *new* `no-install` `offline` `read-only` `assistant`
- [**instruction-files**](adapters/stdlib/instruction-files/) — For a folder, which instruction files each coding agent would load (AGENTS.md, CLAUDE.md, GEMINI.md, rules folders), in what order, with each file's size and hash. *box* `no-install` `offline` `read-only` `assistant`
- **issue-answer** (idea) — A workflow that drafts an answer to a new issue from the repo's own docs, each line cited, posted only once a maintainer seals it. Goes online: the forge, through the workflow's token, to post an answer once it is sealed. *new* `no-install` `online` `records` `assistant`
- **ladder** (idea) — Your files first, then sources you trust such as Jeles and Nestor, then a model, stopping at the first that answers, each answer kept for next time. *bot* `no-install` `offline` `records` `assistant`
- **local-model** (idea) — Suggestions from a model on this machine only, such as Ollama or llama.cpp. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- [**mcp**](adapters/deps/mcp/) — Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. Needs mcp; MIT. *new* `needs-install` `offline` `records` `assistant`
- **mcp-by-hash** (idea) — Your passages served as MCP resources named by their SHA-256, so an assistant cites exactly the bytes it read and a changed passage gets a new name. *bot* `no-install` `offline` `read-only` `assistant`
- [**mcp-lite**](adapters/stdlib/mcp-lite/) — The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only. *box* `no-install` `offline` `records` `assistant`
- **memory-import** (idea) — An AI assistant's memory store, SQLite or Markdown, handed in through propose: one suggestion per memory, none trusted until you seal it. *new* `no-install` `offline` `records` `assistant`
- **mex** (idea) — mex's project memory for coding agents: its scaffold read as cited passages, and what an agent writes back held for your seal. *new* `no-install` `offline` `records` `assistant`
- **model-fit** (idea) — Whether this machine's GPU, NPU or Apple silicon can run a local model, and about how fast, before you download one. *new* `no-install` `offline` `read-only` `assistant`
- **night-batch** (idea) — Questions waiting for suggestions batched into one local-model run overnight, stopped the moment you're back. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- **openai-compatible** (idea) — Suggestions from any OpenAI-compatible endpoint you choose (LM Studio, vLLM, OpenRouter), citing your passages. Goes online: the endpoint you configure, to ask for suggestions. *new* `no-install` `online` `records` `assistant`
- [**opencode**](adapters/stdlib/opencode/) — OpenCode asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- **persona-card** (idea) — A persona written as a card and compiled into the same system-prompt bytes every time, with the prompt's hash on the record. *box* `no-install` `offline` `records` `assistant`
- **plain-language** (idea) — An approved answer rewritten in plain language by a model, the rewrite held until you seal it. *new* `no-install` `offline` `records` `assistant`
- **quantized** (idea) — Finds the smallest quantized local model that still gets your box's own questions right, so suggestions come faster. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `read-only` `assistant`
- **same-way** (idea) — A local model asked each of your box's questions three times, and how often its answer flips, since a model that answers the same way every time is one you can build on. Goes online: this-machine. *new* `no-install` `this-machine` `read-only` `assistant`
- **schema-check** (idea) — A model's answer held to a JSON schema before anything reads it, and a reply that doesn't fit recorded as a result, not lost as an error. *box* `no-install` `offline` `records` `assistant`
- **second-opinion** (idea) — Two assistants' suggestions for the same question side by side, each waiting for its own seal. *new* `no-install` `offline` `records` `assistant`
- [**serve**](adapters/stdlib/serve/) — The one markdown file a model reads: only the passages a human sealed, grouped into pools with the peaks first, by ids it can't guess, and nothing else. *bot* `no-install` `offline` `writes-output` `trust` `assistant`
- **serve-piles** (idea) — serve's piles grouped on all four W's -- who, when, what and where -- not where alone, so a model meets a question from every box that touched it. *new* `no-install` `offline` `writes-output` `trust` `assistant`
- **silence-log** (idea) — A model that ran and said nothing kept as its own row, so silence is told apart from a model that never ran. *bot* `no-install` `offline` `records` `assistant`
- **translate** (idea) — An answer translated by a local model, the original kept beside it, the translation held until you seal it. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- [**windsurf**](adapters/stdlib/windsurf/) — Windsurf asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**zed**](adapters/stdlib/zed/) — Zed's assistant asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`

## Ways to use it

- **anki** (idea) — Approved answers as an Anki deck, built without Anki installed. *new* `no-install` `offline` `writes-output` `interface`
- [**annotations**](adapters/stdlib/annotations/) — Approved answers as W3C Web Annotations, so any annotation tool can show what your files say about a page. *new* `no-install` `offline` `writes-output` `interface`
- [**badge**](adapters/stdlib/badge/) — A badge for a page: these answers came from these files and were approved, linked to the check anyone can run. *new* `no-install` `offline` `writes-output` `interface`
- [**braille**](adapters/stdlib/braille/) — Answers as braille-ready files (BRF) for a braille display or embosser. *new* `no-install` `offline` `writes-output` `interface`
- [**browse**](adapters/stdlib/browse/) — Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only. Reaches this machine only. *new* `no-install` `this-machine` `records` `interface` `everyday`
- [**calendar-out**](adapters/stdlib/calendar-out/) — Dates coming up as an .ics file your calendar app can subscribe to. *new* `no-install` `offline` `writes-output` `interface`
- [**cloudevents**](adapters/stdlib/cloudevents/) — Record rows in the CloudEvents envelope, for any tool that already reads them. *new* `no-install` `offline` `writes-output` `interface`
- **datasette** (idea) — Your record and approved answers browsable in Datasette, read only: tables, facets and SQL on this machine. Needs Datasette; Apache-2.0. Reaches this machine only. *new* `needs-install` `this-machine` `read-only` `interface`
- [**deep-links**](adapters/stdlib/deep-links/) — Each answer as a link that opens the file at the line (RFC 5147 lines, browser text fragments). *new* `no-install` `offline` `read-only` `interface`
- **desktop** (idea) — A small window to ask and approve, with nothing to install: Python's own tkinter. *new* `no-install` `offline` `records` `interface`
- **dictate** (idea) — Ask out loud: your question spoken and turned to text on this machine. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `read-only` `interface`
- [**emacs**](adapters/stdlib/emacs/) — Answers in an Emacs compilation buffer, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- **email-ask** (idea) — Ask by emailing yourself; the answer comes back as a reply with its sources. Goes online: your own mail server, over IMAP and SMTP, to read questions and reply. *new* `no-install` `online` `read-only` `interface`
- **emergency-card** (idea) — One page of your medicines, allergies and contacts, from your files, to print or keep on your phone. *new* `no-install` `offline` `writes-output` `interface`
- **home-assistant** (idea) — Ask through Home Assistant's voice assistant, answered from your files. Goes online: your Home Assistant, on your own network, to answer its voice assistant. *new* `no-install` `online` `read-only` `interface`
- [**jetbrains**](adapters/stdlib/jetbrains/) — An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line. *new* `no-install` `offline` `read-only` `interface`
- **kiosk** (idea) — A shared machine in a library or classroom: one box, ask only, nobody's key on it. Reaches this machine only. *new* `no-install` `this-machine` `read-only` `interface`
- **launcher** (idea) — Ask from Alfred, Raycast, KRunner or PowerToys Run, answers with file and line. *new* `no-install` `offline` `read-only` `interface`
- [**llms-txt**](adapters/stdlib/llms-txt/) — An llms.txt for your folder, written from what's actually in it to the spec's version 2, and any llms.txt you saved checked against that spec. *new* `no-install` `offline` `writes-output`
- **obsidian** (idea) — Ask from inside Obsidian, answers as links to the note and line. Reaches this machine only. *new* `no-install` `this-machine` `read-only` `interface`
- [**pipe**](adapters/stdlib/pipe/) — Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf. *box* `no-install` `offline` `records` `interface`
- [**plain**](adapters/stdlib/plain/) — Answers as sentences instead of JSON, each with its file and line. *new* `no-install` `offline` `records` `interface`
- **pr-context** (idea) — On a pull request, the passages in the repo's docs that name the files it changes, posted as one comment. Goes online: the forge, through the workflow's token, to post the comment. *new* `no-install` `online` `read-only` `interface`
- [**print**](adapters/stdlib/print/) — An answer as a printable page with its sources, to take to an appointment; --large for big, high-contrast type. *new* `no-install` `offline` `records` `interface` `everyday`
- **qr** (idea) — An answer as a QR code on screen, to carry it to your phone without the network. *new* `no-install` `offline` `read-only` `interface`
- [**repo-pile**](adapters/stdlib/repo-pile/) — Public repositories made into a box you can ask: cloned, kept only under a licence an Apache-2.0 project can use, their docs the pile, indexed for fast questions. Goes online: github.com (or the --source you give), to clone the repositories you list. *new* `no-install` `online` `records` `interface` `research`
- [**rss-out**](adapters/stdlib/rss-out/) — New approved answers as an RSS feed file, for any feed reader. *new* `no-install` `offline` `writes-output` `interface`
- **safe-app** (idea) — willow as a SAFE app: installed from the SAFE App Store, authorized per session, and deleted clean. *new* `no-install` `offline` `read-only` `interface`
- **share** (idea) — One sealed answer to send someone, checkable by them, without giving them the folder. *new* `no-install` `offline` `writes-output` `interface`
- [**shell**](adapters/stdlib/shell/) — A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows. *new* `no-install` `offline` `records` `interface`
- **socratic** (idea) — Asks you questions about your own notes instead of answering, each citing the passage it asked from. *new* `no-install` `offline` `records` `interface`
- **speak** (idea) — Reads answers aloud. Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` `read-only` `interface`
- [**start**](adapters/stdlib/start/) — First run in one step: asks where your files are, makes the box and key where they belong, copies in the starter words, and prints the double-click launcher. *new* `no-install` `offline` `records` `interface` `everyday`
- **static-search** (idea) — An exported page of approved answers with its own search built in, no server, opened in any browser. Needs Pagefind; MIT. *new* `needs-install` `offline` `writes-output` `interface`
- **telegram-bot** (idea) — Ask from your phone through a Telegram bot only you can talk to. Goes online: api.telegram.org, to receive your questions and send answers. *new* `no-install` `online` `read-only` `interface`
- **tui** (idea) — A full-screen terminal view to ask, read passages and approve, in curses. *new* `no-install` `offline` `records` `interface`
- [**vim**](adapters/stdlib/vim/) — Answers in Vim and Neovim's quickfix list, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- [**vscode**](adapters/stdlib/vscode/) — A VS Code task whose answers land in the Problems panel, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- **warm** (idea) — The kernel kept running between questions on this machine, so each question skips the start-up. Reaches this machine only. *new* `no-install` `this-machine` `read-only` `interface`

## Play

- **art-of-the-day** (idea) — An artwork from the Met's public-domain collection, drawn for the day or for each sealed session. Goes online: collectionapi.metmuseum.org, to read the artwork. *new* `no-install` `online` `records` `play`
- **beacon** (idea) — Draws seeded by a public randomness beacon (drand), so nobody could have picked the result in advance. Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `records` `play`
- **chess-puzzle** (idea) — A Lichess puzzle a day, drawn by a seed: predict whether you'll solve it, then solve it. Goes online: lichess.org, to read the puzzle. *new* `no-install` `online` `records` `play`
- **connect-four** (idea) — Connect Four as rows on the record, held to the solved result: the first player wins. *new* `no-install` `offline` `records` `play`
- [**daily-word**](adapters/stdlib/daily-word/) — A word game drawn from your own files' words, the same puzzle for everyone with the same box. *new* `no-install` `offline` `records` `play`
- [**dice**](adapters/stdlib/dice/) — Seeded dice rolls as rows: every roll replayable and checkable. *bot* `no-install` `offline` `records` `play`
- **dice5e** (idea) — Full tabletop dice notation (4d6kh3, advantage). Needs dice; MIT. *bot* `needs-install` `offline` `records` `play`
- **front-page** (idea) — Which new posts will make the Hacker News front page? Wager, and let its search settle it. Goes online: hn.algolia.com, to read the front page. *new* `no-install` `online` `records` `play`
- **game-master** (idea) — A tabletop game's rolls and rulings as rows on the record, with the game master's calls sealed. *bot* `no-install` `offline` `records` `play`
- **gutenberg** (idea) — A paragraph from a public-domain book beside one of yours, for serendipity. Goes online: gutenberg.org, each book fetched once. *new* `no-install` `online` `records` `play`
- **hanoi** (idea) — Towers of Hanoi as rows: each move, n discs in 2^n - 1. *new* `no-install` `offline` `records` `play`
- [**horoscope**](adapters/stdlib/horoscope/) — A daily horoscope keyed on your name and the date: same name, same day, same reading, always. *bot* `no-install` `offline` `read-only` `play`
- **horoscope-grades** (idea) — Every horoscope logged as a forecast and settled against the day, so the stars get a Brier score. *new* `no-install` `offline` `records` `play`
- **ink-story** (idea) — A branching ink story where every choice made for you comes from a seed on the record. Needs inkjs; MIT. *new* `needs-install` `offline` `records` `play`
- **joins** (idea) — Two passages from two different folders, drawn by chance, for you to say what joins them. *bot* `no-install` `offline` `records` `play`
- [**life**](adapters/stdlib/life/) — Conway's Game of Life as rows: a fully deterministic world on the record. *bot* `no-install` `offline` `records` `play`
- **lore** (idea) — For a world you're writing: each fact about it sealed one at a time, so a story can be checked against its canon. *bot* `no-install` `offline` `records` `play`
- **lunatic** (idea) — The moon's real phase sets how far typos are forgiven: everything at full moon, nothing at new. Needs Skyfield; MIT. *new* `needs-install` `offline` `read-only` `play`
- **mastermind** (idea) — Mastermind with the secret's hash at the open: each guess and score on the record. *new* `no-install` `offline` `records` `play`
- **movie** (idea) — Your record as a Gource film: every question, approval and miss growing like a tree. Needs the gource program; GPL-3.0, called not linked. *new* `needs-install` `offline` `writes-output` `play`
- **nim** (idea) — Nim as rows: the heaps and each take, a position lost exactly when the heaps' XOR is 0. *new* `no-install` `offline` `records` `play`
- **ninety-percent** (idea) — The calibration drill: give a range you're 90% sure of for a real number, and see how many hold. Goes online: Our World in Data, its numbers downloaded once. *new* `no-install` `online` `records` `play`
- [**odds**](adapters/stdlib/odds/) — Exact odds, as fractions, for a game's dice and tables: what each outcome's chance really is. *bot* `no-install` `offline` `read-only` `play`
- [**oracle-text**](adapters/stdlib/oracle-text/) — Readings written by a Tracery grammar, every branch picked by the seeded stream, so each one can be replayed. *new* `no-install` `offline` `read-only` `play`
- **pageviews** (idea) — Two Wikipedia articles drawn at random: which gets more views tomorrow? Goes online: the Wikimedia pageviews API, to settle it. *new* `no-install` `online` `records` `play`
- [**pile-poetry**](adapters/stdlib/pile-poetry/) — Verse from the word pairs your own files use most, in your own dialect. *new* `no-install` `offline` `read-only` `play`
- **predictions** (idea) — Twelve yes-or-no questions about random data, forecast now and answered by a beacon round later, with your Brier score. Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `records` `play`
- **quake-bets** (idea) — Will there be a magnitude 6 this week? Bet, then let the USGS feed settle it against the base rate. Goes online: earthquake.usgs.gov, to read the week's earthquakes. *new* `no-install` `online` `records` `play`
- [**quiz**](adapters/stdlib/quiz/) — A quiz from your own files: a passage with a word missing, and you fill it in. *new* `no-install` `offline` `records` `play`
- **real-sky** (idea) — A horoscope from where the planets really are, computed offline from a JPL ephemeris. Needs Skyfield; MIT. Goes online: the ephemeris file, downloaded once. *new* `needs-install` `online` `read-only` `play`
- **reversi** (idea) — Reversi as rows: every move, each flip following from the board. *new* `no-install` `offline` `records` `play`
- **roll-for-merge** (idea) — A d20 for every pull request, green runs added and red streaks taken away, against a DC the bot calls. *new* `no-install` `offline` `records` `play`
- **rules** (idea) — A game's or a house's rules, sealed section by section, so 'what does the rule say?' answers with the exact section. *bot* `no-install` `offline` `records` `play`
- **sokoban** (idea) — Sokoban levels and moves on the record, a solution checked by replaying it. *new* `no-install` `offline` `records` `play`
- **spurious** (idea) — Everything joined on time and place (CI reds, earthquakes, rain, front pages) to hunt correlations that mean nothing. *new* `no-install` `offline` `read-only` `play`
- [**tarot**](adapters/stdlib/tarot/) — A seeded tarot draw on the record, replayable by anyone with the seed. *new* `no-install` `offline` `records` `play`
- **tic-tac-toe** (idea) — Tic-tac-toe as rows: every move, and the solver's value of each position; perfect play draws. *new* `no-install` `offline` `records` `play`
- **tides** (idea) — Tide predictions as a control: if your Brier score on tides isn't near zero, the forecasting plumbing is broken. Goes online: NOAA's tides API, to read predictions and what happened. *new* `no-install` `online` `records` `play`
- **todays-place** (idea) — One place a day drawn from Natural Earth's public-domain list, for the day's questions and bets. *new* `no-install` `offline` `records` `play`
- **weather-bet** (idea) — Wager on rain tomorrow before you look, against Open-Meteo's own forecast, and see whose Brier score wins. Goes online: api.open-meteo.com, to read the forecast and the outcome. *new* `no-install` `online` `records` `play`

## For maintainers

- [**agents-md-check**](adapters/stdlib/agents-md-check/) — Commands and paths named in AGENTS.md or CLAUDE.md that no longer exist in the repo. *new* `no-install` `offline` `read-only` `maintainers`
- [**bench**](adapters/stdlib/bench/) — How fast the kernel answers on boxes of set sizes, per release, so a slowdown is seen. *new* `no-install` `offline` `read-only` `maintainers`
- [**bot-venv**](adapters/stdlib/bot-venv/) — Which venv has what CI needs, willow-bot's own by its rule or any you name, and the line that runs CI with its Python. *bot* `no-install` `offline` `read-only` `maintainers`
- [**ci**](adapters/stdlib/ci/) — This repo's checks as verdict rows on a kernel record, the same every run. Goes online: PyPI, to read each dependency floor's release date. *box* `no-install` `online` `records` `maintainers`
- **ci-baseline** (idea) — Is your CI normal? How often pull requests everywhere go green first time, from GH Archive. Goes online: data.gharchive.org, its hours downloaded once. *new* `no-install` `online` `read-only` `maintainers`
- **ci-bets** (idea) — Bet on your own CI: forecasts on each pull request going green, scored against the model's. *new* `no-install` `offline` `records` `maintainers`
- [**ci-cache**](adapters/stdlib/ci-cache/) — CI caches pip, npm, .NET and Maven downloads keyed on their lockfiles, so a run skips the installs. *new* `no-install` `offline` `read-only` `maintainers`
- [**ci-memo**](adapters/stdlib/ci-memo/) — A CI gate whose inputs' bytes are unchanged keeps its recorded verdict: pin a run's per-gate keys, and run only what a change can reach. *new* `no-install` `offline` `writes-output` `maintainers`
- [**ci-why**](adapters/stdlib/ci-why/) — Why CI went red: the failing block pulled out of the job's log, plain, put where people look. *bot* `no-install` `offline` `read-only` `maintainers`
- **code-stats** (idea) — Lines, code and complexity per language, per release, as rows the list can answer from. Needs the scc program; MIT. *new* `needs-install` `offline` `read-only` `maintainers`
- **compiled** (idea) — kernel.py compiled with mypyc for speed, held to the same vectors byte for byte. Needs mypyc; MIT. *new* `needs-install` `offline` `read-only` `maintainers`
- **contribute** (idea) — For anyone on GitHub, what they can do next in the projects they work on: open pull requests, reviews asked of them, issues assigned. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `read-only` `maintainers`
- **contributions** (idea) — A ledger of who contributes to the repo: first-timers and outside contributors called out, bots known by type, never by name. Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `read-only` `maintainers`
- **crates** (idea) — A Rust port of kernel.py on crates.io, held to the same vectors as the other four. Goes online: crates.io, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **docs-i18n** (idea) — The README in other languages, each checked for drift against the English one. *new* `no-install` `offline` `read-only` `maintainers`
- [**fast-tests**](adapters/deps/fast-tests/) — The test suite across every core with pytest-xdist, the same tests in a fraction of the time. Needs pytest-xdist; MIT. *new* `needs-install` `offline` `read-only` `maintainers`
- **forgejo** (idea) — What willow's repo needs from Forgejo, Gitea or Codeberg: its host.json and an Actions file, so the repo can move there. Goes online: the Forgejo instance's API, to read the author of a pull request a security report points to. *new* `no-install` `online` `read-only` `maintainers`
- **fuzz** (idea) — Random and broken inputs thrown at the kernel's commands, every crash kept as a test. *new* `no-install` `offline` `read-only` `maintainers`
- [**github**](adapters/stdlib/github/) — What willow's repo needs from GitHub, kept in one folder so it can be taken away. Goes online: GitHub, through gh, to read the author of a pull request a security report points to. *box* `no-install` `online` `read-only` `maintainers`
- **gitlab** (idea) — What willow's repo needs from GitLab, as github does for GitHub: its host.json and CI file, so the repo can move there. Goes online: GitLab, through glab, to read the author of a merge request a security report points to. *new* `no-install` `online` `read-only` `maintainers`
- **go** (idea) — A Go port of kernel.py, held to the same vectors as the others. *new* `no-install` `offline` `read-only` `maintainers`
- [**live**](adapters/stdlib/live/) — Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here. Goes online: only what the programs it starts reach on their own; it reaches nothing itself. *new* `no-install` `maintainers` `tests` `interface` `assistant`
- **maven** (idea) — The Java port on Maven Central, built from this repo and checked against the vectors. Goes online: Maven Central, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- [**mutants**](adapters/stdlib/mutants/) — Breaks each add-on's code on purpose and checks its tests notice. *new* `no-install` `offline` `read-only` `maintainers`
- **novelty** (idea) — Before a new add-on merges, whether its combination of pieces has been assembled before, scanned the way a study checks its own novelty. *new* `no-install` `offline` `read-only` `maintainers`
- **npm** (idea) — The TypeScript port on npm, built from this repo, checked against the vectors, and published with provenance; npx runs it. Goes online: registry.npmjs.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **nuget** (idea) — The C# port on NuGet, built from this repo and checked against the vectors. Goes online: nuget.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- [**pins**](adapters/stdlib/pins/) — Version ranges in package.json, pyproject.toml or Cargo.toml that no lockfile holds. *new* `no-install` `offline` `read-only` `maintainers`
- [**profile**](adapters/stdlib/profile/) — Where a question's time goes, function by function, from cProfile, per release. *new* `no-install` `offline` `read-only` `maintainers`
- **property-tests** (idea) — Thousands of odd inputs (combining marks, empty strings, huge seeds) thrown at the byte rules by Hypothesis. Needs Hypothesis; MPL-2.0. *new* `needs-install` `offline` `read-only` `maintainers`
- **pypi** (idea) — kernel.py on PyPI as a package with no dependencies, built from this repo, checked against the vectors, and attested on upload; uvx and pipx run it. Goes online: upload.pypi.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **pypy** (idea) — The kernel and its tests run under PyPy too, and timed against CPython. *new* `no-install` `offline` `read-only` `maintainers`
- [**readme**](adapters/stdlib/readme/) — Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. *new* `no-install` `offline` `writes-output` `maintainers`
- **reconciler** (idea) — willow-reconciler run on this repo's idea list and git history: how much of what was proposed has landed. Needs willow-reconciler; Apache-2.0. *new* `needs-install` `offline` `read-only` `maintainers`
- **repo-index** (idea) — This repository as its own deterministic box: its cards, docs and code as dated passages, rebuilt the same bytes each time, so willow can answer questions about itself. *new* `no-install` `offline` `writes-output` `maintainers`
- **repro** (idea) — A release built twice from the same commit, byte for byte the same. *new* `no-install` `offline` `read-only` `maintainers`
- [**restack**](adapters/stdlib/restack/) — Main merged into your branches, with the conflicts in the files the repo makes or only adds to settled by its own tools, and every other one left to you. *new* `no-install` `offline` `read-only` `maintainers` `git`
- [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search. *box* `no-install` `offline` `read-only` `maintainers`
- [**slow-tests**](adapters/stdlib/slow-tests/) — Each test's time kept per run, with the slowest named and any that got slower flagged. *new* `no-install` `offline` `read-only` `maintainers`
- **sourcehut** (idea) — What willow's repo needs from SourceHut: its host.json for patches by email and a builds.sr.ht manifest. Goes online: sr.ht, through hut, to read the author of a patch a security report points to. *new* `no-install` `online` `read-only` `maintainers`
- **swift** (idea) — A Swift port of kernel.py for iPhone and Mac apps, held to the same vectors. *new* `no-install` `offline` `read-only` `maintainers`
- [**test-impact**](adapters/stdlib/test-impact/) — Only the tests a change can reach run first, from the import graph; the full suite still runs after. *new* `no-install` `offline` `read-only` `maintainers`
- [**test-shards**](adapters/stdlib/test-shards/) — The CI test jobs split by each test's past time, so every job finishes about together. *new* `no-install` `offline` `read-only` `maintainers`
- **welcome** (idea) — One plain thank-you on a first-time contributor's first pull request, once per person, and only where it's turned on. Goes online: the forge, through the workflow's token, to post the thank-you. *bot* `no-install` `online` `read-only` `maintainers`
<!-- /willow:list -->

Back to the [README](README.md).
