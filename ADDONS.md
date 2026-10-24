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
words: the kernel itself never goes online. *bot* is rebuilt from willow-bot's
one script, *box* is built from what the kernel already has, *new* is new.
Each carries up to five tags: four filled in from its card (`no-install` or
`needs-install`; `offline`, `this-machine` or `online`; `read-only`, `records`
or `writes-output`; its section), and any the card's author adds or changes.

<!-- willow:pools -->
`█████░░░░░░░░░░░░░░░` **26 of 98 built** · 76 need no install · 22 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 7 | 32 | 32 | 7 |
| Finding things | 4 | 2 | 4 | 2 |
| Your own words | 1 | 6 | 5 | 2 |
| Keeping track | 4 | 7 | 11 | 0 |
| Trust and proof | 2 | 9 | 6 | 5 |
| Privacy and safety | 1 | 2 | 3 | 0 |
| Assistants | 1 | 6 | 4 | 3 |
| Ways to use it | 1 | 3 | 3 | 1 |
| Play | 0 | 3 | 2 | 1 |
| For maintainers | 5 | 2 | 6 | 1 |
<!-- /willow:pools -->

### Newest

<!-- willow:newest -->
- 2026-10-23 · [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first.
- 2026-10-23 · [**surprise**](adapters/stdlib/surprise/) — One passage from your folder at random, seeded so it can be replayed.
- 2026-10-23 · [**starter-words**](adapters/stdlib/starter-words/) — A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic).
- 2026-10-23 · [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact.
- 2026-10-23 · [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search.
<!-- /willow:newest -->

### Add-on of the week

<!-- willow:pick week=2026-W43 -->
**[todo](adapters/stdlib/todo/)** — TODO, FIXME and "need to" lines across the folder, oldest first.

*Drawn for 2026-W43: SHA-256 of "willow add-on of the week 2026-W43", modulo the 26 built add-ons in name order.*
<!-- /willow:pick -->

<!-- willow:list -->
**Contents:** [Reading more kinds of files](#reading-more-kinds-of-files) · [Finding things](#finding-things) · [Your own words](#your-own-words) · [Keeping track](#keeping-track) · [Trust and proof](#trust-and-proof) · [Privacy and safety](#privacy-and-safety) · [Assistants](#assistants) · [Ways to use it](#ways-to-use-it) · [Play](#play) · [For maintainers](#for-maintainers)

### Reading more kinds of files

Each writes plain text into a mirror folder the kernel searches, so your originals are never touched.

- **agent-transcript** (idea) — Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told. *new* `no-install` `offline` `writes-output` `file-reader`
- **almanac** (idea) — An Almanac's catalog.json (climate, health, civic and the rest): each public dataset's description and source as passages, with when its link was last checked. *new* `no-install` `offline` `writes-output` `file-reader`
- **archivebox** (idea) — ArchiveBox snapshots: each saved page's text, with its URL and the date it was captured. *new* `no-install` `offline` `writes-output` `file-reader`
- **bank** (idea) — Bank CSV and OFX statements as dated lines, with spending by month. *new* `no-install` `offline` `writes-output` `file-reader`
- **bluesky** (idea) — A Bluesky repo.car export: your posts as dated lines, read by a small CAR and CBOR reader of its own. *new* `no-install` `offline` `writes-output` `file-reader`
- **bookmarks** (idea) — Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file. *new* `no-install` `offline` `writes-output` `file-reader`
- [**books**](adapters/stdlib/books/) — Kindle "My Clippings.txt" highlights and .epub text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**calendar**](adapters/stdlib/calendar/) — .ics events and .vcf contacts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**chats**](adapters/stdlib/chats/) — WhatsApp and Telegram exports, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- **codebase-memory** (idea) — codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line. *new* `no-install` `offline` `writes-output` `file-reader`
- **corpus-lens** (idea) — corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code. *new* `no-install` `offline` `writes-output` `file-reader`
- **discord** (idea) — Discord's data package: your messages, one dated line each, by server and channel. *new* `no-install` `offline` `writes-output` `file-reader`
- **git-history** (idea) — Commit messages and diffs as a dated pile: "when did we change the retry limit?" Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `file-reader`
- **health** (idea) — Apple Health and Google Fit exports as daily numbers the readings add-on can trend. *new* `no-install` `offline` `writes-output` `file-reader`
- **homestead** (idea) — Homestead's exports from its law, ledger and health modules: records, deadlines and evidence as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **instapaper** (idea) — Instapaper's CSV and HTML export: saved articles and highlights as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **joplin** (idea) — Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates. *new* `no-install` `offline` `writes-output` `file-reader`
- **journiv** (idea) — Journiv journal entries, with their moods, as dated lines, once its export format is settled. *new* `no-install` `offline` `writes-output` `file-reader`
- **jrnl** (idea) — jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage. *new* `no-install` `offline` `writes-output` `file-reader`
- **karakeep** (idea) — Karakeep's JSON export: bookmarks, notes and tags as plain text. *new* `no-install` `offline` `writes-output` `file-reader`
- **lessons** (idea) — Lesson plans from the Emerging Rule community library, by grade and subject, as passages a teacher can ask. *new* `no-install` `offline` `writes-output` `file-reader`
- [**mail**](adapters/stdlib/mail/) — .eml and .mbox files, with sender, date and subject kept. *new* `no-install` `offline` `writes-output` `file-reader`
- **mastodon** (idea) — A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**notes**](adapters/stdlib/notes/) — Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. *new* `no-install` `offline` `writes-output` `file-reader`
- **ocr** (idea) — Text out of photos of letters and scanned PDFs. Needs pytesseract and the tesseract program; Apache-2.0. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**office**](adapters/stdlib/office/) — .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. *new* `no-install` `offline` `writes-output` `file-reader`
- [**pdf**](adapters/deps/pdf/) — Text out of PDFs. Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `writes-output` `file-reader`
- **photos** (idea) — When and where each photo was taken, as dated lines. Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `writes-output` `file-reader`
- **pocket** (idea) — Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone. *new* `no-install` `offline` `writes-output` `file-reader`
- **quiet-corner** (idea) — A Quiet Corner backup file: a teacher's classroom observations as dated passages, for that teacher's questions alone. *new* `no-install` `offline` `writes-output` `file-reader`
- **sheets** (idea) — Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. Needs openpyxl; MIT. *new* `needs-install` `offline` `writes-output` `file-reader`
- **sigmap** (idea) — SigMap's signature map of a codebase as plain text: each function's signature with its file and line, for questions about the code. *new* `no-install` `offline` `writes-output` `file-reader`
- **signal** (idea) — A Signal backup, decrypted with its passphrase, as one dated line per message. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `writes-output` `file-reader`
- **slack** (idea) — Slack's export zip: one dated line per message, with channel and author. *new* `no-install` `offline` `writes-output` `file-reader`
- **subtitles** (idea) — Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed. *new* `no-install` `offline` `writes-output` `file-reader`
- **takeout** (idea) — Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **voice** (idea) — Dictation, calls and lectures transcribed into dated text. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `writes-output` `file-reader`
- **wallabag** (idea) — wallabag's JSON or HTML export: saved entries as plain text, with their tags. *new* `no-install` `offline` `writes-output` `file-reader`
- **writefreely** (idea) — WriteFreely posts, from its export or a copy of its SQLite database, as dated text. *new* `no-install` `offline` `writes-output` `file-reader`

### Finding things

- [**all**](adapters/stdlib/all/) — Every matching passage, ranked, not just the top three. *box* `no-install` `offline` `read-only` `search`
- **meaning** (idea) — Search by meaning: "who owes me money" finds "invoice outstanding". Needs sentence-transformers; Apache-2.0. Goes online: the model, downloaded once from Hugging Face. *new* `needs-install` `online` `writes-output` `search`
- [**on-this-day**](adapters/stdlib/on-this-day/) — What you wrote on this date in earlier years. *box* `no-install` `offline` `read-only` `search`
- [**quote-check**](adapters/stdlib/quote-check/) — Is this exact quote in my files, and where? For writers, journalists and students. *box* `no-install` `offline` `read-only` `search`
- [**surprise**](adapters/stdlib/surprise/) — One passage from your folder at random, seeded so it can be replayed. *bot* `no-install` `offline` `records` `search`
- **typos** (idea) — Forgives misspellings in questions. Needs rapidfuzz; MIT. *new* `needs-install` `offline` `read-only` `search`

### Your own words

The blind tests' biggest gap: on day one, a person's words aren't their files' words.

- [**starter-words**](adapters/stdlib/starter-words/) — A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic). *new* `no-install` `offline` `writes-output` `words`
- **stems** (idea) — Word forms for 20+ languages, so "maisons" finds "maison". Needs snowballstemmer; BSD-3. *new* `needs-install` `offline` `read-only` `words`
- **synonyms** (idea) — Suggests words-list lines for a word no file has. Needs nltk and WordNet; Apache-2.0. Goes online: the WordNet data, downloaded once. *new* `needs-install` `online` `writes-output` `words`
- **words-de** (idea) — German common words, so questions aren't matched on "der" and "und". *new* `no-install` `offline` `writes-output` `words`
- **words-es** (idea) — Spanish common words ("el", "y"). *new* `no-install` `offline` `writes-output` `words`
- **words-fr** (idea) — French common words ("le", "et"). *new* `no-install` `offline` `writes-output` `words`
- **words-pt** (idea) — Portuguese common words ("o", "e"). *new* `no-install` `offline` `writes-output` `words`

### Keeping track

- [**again**](adapters/stdlib/again/) — Questions you keep asking: "asked 4 times; approve an answer?" *bot* `no-install` `offline` `read-only` `tracking`
- **care** (idea) — For caregivers: medications, vitals and appointments from a care log, what's due and what moved. *box* `no-install` `offline` `read-only` `tracking`
- [**coming-up**](adapters/stdlib/coming-up/) — Dates written in your files in the next N days: appointments, renewals, deadlines. *box* `no-install` `offline` `read-only` `tracking`
- **digest** (idea) — One page: suggestions waiting, approvals gone stale, dates coming up, questions repeated. *bot* `no-install` `offline` `read-only` `tracking`
- **flashcards** (idea) — Approved question-and-answer pairs become cards, scheduled by spaced repetition. *box* `no-install` `offline` `records` `tracking`
- **forecasts** (idea) — Write a prediction before the outcome, settle it later, see your Brier score. *bot* `no-install` `offline` `records` `tracking`
- **invoices** (idea) — For freelancers: invoices and payments matched by the id pattern you give, never guessed. *new* `no-install` `offline` `read-only` `tracking`
- **oakenscroll** (idea) — Oakenscroll's Office calibration ledger: what you believed, how hard, and how it resolved, as dated passages. *new* `no-install` `offline` `writes-output` `tracking`
- [**readings**](adapters/stdlib/readings/) — Numbers over time and a date gone by, beside an answer. *box* `no-install` `offline` `records` `tracking`
- **session-cost** (idea) — Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep. *new* `no-install` `offline` `read-only` `tracking`
- [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first. *box* `no-install` `offline` `read-only` `tracking`

### Trust and proof

- **changed** (idea) — What's new, edited or deleted in your folder since the last check, as fingerprint rows. *bot* `no-install` `offline` `records` `trust`
- **encrypt** (idea) — Keeps the record folder encrypted at rest. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `records` `trust`
- [**export**](adapters/stdlib/export/) — Approved answers, and the question log (counts only, never words), as Markdown or CSV. *box* `no-install` `offline` `read-only` `trust`
- **jeles** (idea) — Your approved answers as Jeles nuggets, with question, answer, sources and who sealed it, and Jeles' own verified nuggets read back as passages. *new* `no-install` `offline` `writes-output` `trust`
- **line-origin** (idea) — Which agent session wrote this line of code: git blame to the commit, then the transcript turn that made it. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `read-only` `trust`
- **nestor** (idea) — Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when. *new* `no-install` `offline` `writes-output` `trust`
- **pgp** (idea) — Signs exports and reports with your PGP key, verifiable anywhere. Needs the gpg program and python-gnupg; BSD. *new* `needs-install` `offline` `writes-output` `trust`
- **redential** (idea) — The bundle redential-cli's scan makes, written to the record before you submit it, so what left your machine can be checked later. Needs the redential program, run through npx; Apache-2.0. *new* `needs-install` `offline` `records` `trust`
- **report** (idea) — A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. *box* `no-install` `offline` `writes-output` `trust`
- **sap-gate** (idea) — The mcp add-on's tool calls checked against SAP/1.0 grants before they run, through openclaw-sap-gate. Needs openclaw-sap-gate; MIT. *new* `needs-install` `offline` `read-only` `trust`
- [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. *box* `no-install` `offline` `read-only` `trust`

### Privacy and safety

- [**privacy**](adapters/stdlib/privacy/) — Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. *bot* `no-install` `offline` `records` `privacy`
- **secrets-audit** (idea) — Finds keys and passwords sitting in plain files. *bot* `no-install` `offline` `read-only` `privacy`
- **transcript-redact** (idea) — An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line. *new* `no-install` `offline` `writes-output` `privacy`

### Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal.

- **basic-memory** (idea) — Basic Memory's Markdown notes where an AI wrote them: each observation and relation handed in through propose, waiting for your seal. *new* `no-install` `offline` `records` `assistant`
- **claude** (idea) — Suggestions from Claude through the Anthropic API, citing your passages. Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `records` `assistant`
- **hermes** (idea) — Hermes Agent asking your folder as a plugin, and its memories, and what its dreaming plugin consolidates, handed in through propose. *new* `no-install` `offline` `records` `assistant`
- **local-model** (idea) — Suggestions from a model on this machine only, such as Ollama or llama.cpp. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- [**mcp**](adapters/deps/mcp/) — Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. Needs mcp; MIT. *new* `needs-install` `offline` `records` `assistant`
- **memory-import** (idea) — An AI assistant's memory store, SQLite or Markdown, handed in through propose: one suggestion per memory, none trusted until you seal it. *new* `no-install` `offline` `records` `assistant`
- **mex** (idea) — mex's project memory for coding agents: its scaffold read as cited passages, and what an agent writes back held for your seal. *new* `no-install` `offline` `records` `assistant`

### Ways to use it

- **browse** (idea) — A local web page to ask questions and approve answers, reachable from this machine only. Reaches this machine only. *new* `no-install` `this-machine` `records` `interface`
- [**plain**](adapters/stdlib/plain/) — Answers as sentences instead of JSON, each with its file and line. *new* `no-install` `offline` `records` `interface`
- **safe-app** (idea) — willow as a SAFE app: installed from the SAFE App Store, authorized per session, and deleted clean. *new* `no-install` `offline` `read-only` `interface`
- **speak** (idea) — Reads answers aloud. Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` `read-only` `interface`

### Play

- **dice** (idea) — Seeded dice rolls as rows: every roll replayable and checkable. *bot* `no-install` `offline` `records` `play`
- **dice5e** (idea) — Full tabletop dice notation (4d6kh3, advantage). Needs dice; MIT. *bot* `needs-install` `offline` `records` `play`
- **life** (idea) — Conway's Game of Life as rows: a fully deterministic world on the record. *bot* `no-install` `offline` `records` `play`

### For maintainers

- **agents-md-check** (idea) — Commands and paths named in AGENTS.md or CLAUDE.md that no longer exist in the repo. *new* `no-install` `offline` `read-only` `maintainers`
- [**ci**](adapters/stdlib/ci/) — This repo's checks as verdict rows on a kernel record, the same every run. Goes online: PyPI, to read each dependency floor's release date. *box* `no-install` `online` `records` `maintainers`
- [**github**](adapters/stdlib/github/) — What willow's repo needs from GitHub, kept in one folder so it can be taken away. Goes online: GitHub, through gh, to read the author of a pull request a security report points to. *box* `no-install` `online` `read-only` `maintainers`
- [**mutants**](adapters/stdlib/mutants/) — Breaks each add-on's code on purpose and checks its tests notice. *new* `no-install` `offline` `read-only` `maintainers`
- [**readme**](adapters/stdlib/readme/) — Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. *new* `no-install` `offline` `writes-output` `maintainers`
- **reconciler** (idea) — willow-reconciler run on this repo's idea list and git history: how much of what was proposed has landed. Needs willow-reconciler; Apache-2.0. *new* `needs-install` `offline` `read-only` `maintainers`
- [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search. *box* `no-install` `offline` `read-only` `maintainers`
<!-- /willow:list -->

Back to the [README](README.md).
