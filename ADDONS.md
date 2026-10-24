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
`██████░░░░░░░░░░░░░░` **49 of 176 built** · 150 need no install · 26 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 7 | 48 | 48 | 7 |
| Finding things | 4 | 4 | 6 | 2 |
| Your own words | 5 | 5 | 8 | 2 |
| Keeping track | 5 | 17 | 22 | 0 |
| Trust and proof | 2 | 19 | 12 | 9 |
| Privacy and safety | 1 | 6 | 7 | 0 |
| Assistants | 11 | 7 | 15 | 3 |
| Ways to use it | 8 | 7 | 14 | 1 |
| Play | 0 | 3 | 2 | 1 |
| For maintainers | 6 | 11 | 16 | 1 |
<!-- /willow:pools -->

### Newest

<!-- willow:newest -->
- 2026-10-24 · [**zed**](adapters/stdlib/zed/) — Zed's assistant asks your folder and hands in suggestions, through the mcp add-on.
- 2026-10-24 · [**words-pt**](adapters/stdlib/words-pt/) — Portuguese common words ("o", "e").
- 2026-10-24 · [**words-fr**](adapters/stdlib/words-fr/) — French common words ("le", "et").
- 2026-10-24 · [**words-es**](adapters/stdlib/words-es/) — Spanish common words ("el", "y").
- 2026-10-24 · [**words-de**](adapters/stdlib/words-de/) — German common words, so questions aren't matched on "der" and "und".
<!-- /willow:newest -->

### Add-on of the week

<!-- willow:pick week=2026-W43 -->
**[aider](adapters/stdlib/aider/)** — Aider reads answers from your folder with its /run command, file and line included.

*Drawn for 2026-W43: SHA-256 of "willow add-on of the week 2026-W43", modulo the 49 built add-ons in name order.*
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
- **ci-logs** (idea) — CI run logs you downloaded (GitHub Actions, GitLab CI, Forgejo Actions): each failing step as a passage, so you can ask when a test last failed. *new* `no-install` `offline` `writes-output` `file-reader`
- **codebase-memory** (idea) — codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line. *new* `no-install` `offline` `writes-output` `file-reader`
- **corpus-lens** (idea) — corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code. *new* `no-install` `offline` `writes-output` `file-reader`
- **discord** (idea) — Discord's data package: your messages, one dated line each, by server and channel. *new* `no-install` `offline` `writes-output` `file-reader`
- **family-tree** (idea) — Family trees from GEDCOM files: who was born where and when, and which record says so. *new* `no-install` `offline` `writes-output` `file-reader`
- **forgejo-dump** (idea) — A Forgejo or Gitea dump, Codeberg's included: issues, pull requests and wiki pages as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **gh-json** (idea) — What gh prints with --json (issues, pull requests, runs), saved to a file and read as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **git-history** (idea) — Commit messages and diffs as a dated pile: "when did we change the retry limit?" Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `file-reader`
- **github-archive** (idea) — Your GitHub account's data export: the issues, pull requests, reviews and comments you wrote, as dated passages with their links. *new* `no-install` `offline` `writes-output` `file-reader`
- **gitlab-export** (idea) — A GitLab project export, read without unpacking it: its issues, merge requests and comments as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **goodreads** (idea) — Goodreads and StoryGraph exports: the books you've read, when, and what you thought of them. *new* `no-install` `offline` `writes-output` `file-reader`
- **health** (idea) — Apple Health and Google Fit exports as daily numbers the readings add-on can trend. *new* `no-install` `offline` `writes-output` `file-reader`
- **homestead** (idea) — Homestead's exports from its law, ledger and health modules: records, deadlines and evidence as dated passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **instapaper** (idea) — Instapaper's CSV and HTML export: saved articles and highlights as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **joplin** (idea) — Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates. *new* `no-install` `offline` `writes-output` `file-reader`
- **journiv** (idea) — Journiv journal entries, with their moods, as dated lines, once its export format is settled. *new* `no-install` `offline` `writes-output` `file-reader`
- **jrnl** (idea) — jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage. *new* `no-install` `offline` `writes-output` `file-reader`
- **karakeep** (idea) — Karakeep's JSON export: bookmarks, notes and tags as plain text. *new* `no-install` `offline` `writes-output` `file-reader`
- **lessons** (idea) — Lesson plans from the Emerging Rule community library, by grade and subject, as passages a teacher can ask. *new* `no-install` `offline` `writes-output` `file-reader`
- **letterboxd** (idea) — Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **listening** (idea) — Spotify's data download: what you listened to, by day, so you can ask what was on that summer. *new* `no-install` `offline` `writes-output` `file-reader`
- **lockfiles** (idea) — Lockfiles as passages (package-lock.json, pnpm-lock.yaml, poetry.lock, uv.lock, Cargo.lock, go.sum): which version of each dependency, and which lockfile says so. *new* `no-install` `offline` `writes-output` `file-reader`
- [**mail**](adapters/stdlib/mail/) — .eml and .mbox files, with sender, date and subject kept. *new* `no-install` `offline` `writes-output` `file-reader`
- **mastodon** (idea) — A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**notes**](adapters/stdlib/notes/) — Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. *new* `no-install` `offline` `writes-output` `file-reader`
- **ocr** (idea) — Text out of photos of letters and scanned PDFs. Needs pytesseract and the tesseract program; Apache-2.0. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**office**](adapters/stdlib/office/) — .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. *new* `no-install` `offline` `writes-output` `file-reader`
- **package-docs** (idea) — The READMEs and docs inside packages you've already installed (site-packages, node_modules, Cargo's registry cache), so you can ask your dependencies offline. *new* `no-install` `offline` `writes-output` `file-reader`
- [**pdf**](adapters/deps/pdf/) — Text out of PDFs. Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `writes-output` `file-reader`
- **photos** (idea) — When and where each photo was taken, as dated lines. Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `writes-output` `file-reader`
- **pocket** (idea) — Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone. *new* `no-install` `offline` `writes-output` `file-reader`
- **quiet-corner** (idea) — A Quiet Corner backup file: a teacher's classroom observations as dated passages, for that teacher's questions alone. *new* `no-install` `offline` `writes-output` `file-reader`
- **recipes** (idea) — Recipes from saved web pages and recipe-app exports, as plain text: what can I cook with leeks? *new* `no-install` `offline` `writes-output` `file-reader`
- **sarif** (idea) — SARIF reports from code scanners such as CodeQL and Semgrep: each finding as a passage with its rule, file and line. *new* `no-install` `offline` `writes-output` `file-reader`
- **sbom** (idea) — SBOMs in SPDX or CycloneDX JSON: each component, its version and licence, as passages. *new* `no-install` `offline` `writes-output` `file-reader`
- **sheets** (idea) — Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. Needs openpyxl; MIT. *new* `needs-install` `offline` `writes-output` `file-reader`
- **sigmap** (idea) — SigMap's signature map of a codebase as plain text: each function's signature with its file and line, for questions about the code. *new* `no-install` `offline` `writes-output` `file-reader`
- **signal** (idea) — A Signal backup, decrypted with its passphrase, as one dated line per message. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `writes-output` `file-reader`
- **slack** (idea) — Slack's export zip: one dated line per message, with channel and author. *new* `no-install` `offline` `writes-output` `file-reader`
- **strava** (idea) — Strava's export and GPX files: each run, ride and walk as a dated line with its distance and time. *new* `no-install` `offline` `writes-output` `file-reader`
- **subtitles** (idea) — Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed. *new* `no-install` `offline` `writes-output` `file-reader`
- **takeout** (idea) — Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- **texts** (idea) — Phone text messages, from an Android SMS backup or an iPhone backup's copy, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- **voice** (idea) — Dictation, calls and lectures transcribed into dated text. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `writes-output` `file-reader`
- **wallabag** (idea) — wallabag's JSON or HTML export: saved entries as plain text, with their tags. *new* `no-install` `offline` `writes-output` `file-reader`
- **writefreely** (idea) — WriteFreely posts, from its export or a copy of its SQLite database, as dated text. *new* `no-install` `offline` `writes-output` `file-reader`

### Finding things

- [**all**](adapters/stdlib/all/) — Every matching passage, ranked, not just the top three. *box* `no-install` `offline` `read-only` `search`
- **codeowners** (idea) — Who owns this file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo alike. *new* `no-install` `offline` `read-only` `search`
- **meaning** (idea) — Search by meaning: "who owes me money" finds "invoice outstanding". Needs sentence-transformers; Apache-2.0. Goes online: the model, downloaded once from Hugging Face. *new* `needs-install` `online` `writes-output` `search`
- [**on-this-day**](adapters/stdlib/on-this-day/) — What you wrote on this date in earlier years. *box* `no-install` `offline` `read-only` `search`
- [**quote-check**](adapters/stdlib/quote-check/) — Is this exact quote in my files, and where? For writers, journalists and students. *box* `no-install` `offline` `read-only` `search`
- [**surprise**](adapters/stdlib/surprise/) — One passage from your folder at random, seeded so it can be replayed. *bot* `no-install` `offline` `records` `search`
- **typos** (idea) — Forgives misspellings in questions. Needs rapidfuzz; MIT. *new* `needs-install` `offline` `read-only` `search`
- **upgrade-notes** (idea) — Before an upgrade: the changelog lines between the version you lock and the one you'd move to, from the package's own files. Goes online: the registry (PyPI, npm or crates.io), to fetch the newer version's changelog. *new* `no-install` `online` `read-only` `search`

### Your own words

The blind tests' biggest gap: on day one, a person's words aren't their files' words.

- **memoir** (idea) — A question a week about your life, answered in your own words and kept, so your story is in your files. *new* `no-install` `offline` `writes-output` `words`
- [**starter-words**](adapters/stdlib/starter-words/) — A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic). *new* `no-install` `offline` `writes-output` `words`
- **stems** (idea) — Word forms for 20+ languages, so "maisons" finds "maison". Needs snowballstemmer; BSD-3. *new* `needs-install` `offline` `read-only` `words`
- **synonyms** (idea) — Suggests words-list lines for a word no file has. Needs nltk and WordNet; Apache-2.0. Goes online: the WordNet data, downloaded once. *new* `needs-install` `online` `writes-output` `words`
- [**words-de**](adapters/stdlib/words-de/) — German common words, so questions aren't matched on "der" and "und". *new* `no-install` `offline` `records` `words` `german`
- [**words-es**](adapters/stdlib/words-es/) — Spanish common words ("el", "y"). *new* `no-install` `offline` `records` `words` `spanish`
- [**words-fr**](adapters/stdlib/words-fr/) — French common words ("le", "et"). *new* `no-install` `offline` `records` `words` `french`
- **words-it** (idea) — Italian common words ("il", "e"). *new* `no-install` `offline` `records` `words` `italian`
- **words-nl** (idea) — Dutch common words ("de", "en"). *new* `no-install` `offline` `records` `words` `dutch`
- [**words-pt**](adapters/stdlib/words-pt/) — Portuguese common words ("o", "e"). *new* `no-install` `offline` `records` `words` `portuguese`

### Keeping track

- [**again**](adapters/stdlib/again/) — Questions you keep asking: "asked 4 times; approve an answer?" *bot* `no-install` `offline` `read-only` `tracking`
- **car** (idea) — Your car's services, repairs and inspection dates, from receipts and notes: what's due, and what it cost. *new* `no-install` `offline` `read-only` `tracking`
- **care** (idea) — For caregivers: medications, vitals and appointments from a care log, what's due and what moved. *box* `no-install` `offline` `read-only` `tracking`
- [**coming-up**](adapters/stdlib/coming-up/) — Dates written in your files in the next N days: appointments, renewals, deadlines. *box* `no-install` `offline` `read-only` `tracking`
- [**digest**](adapters/stdlib/digest/) — One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that keep finding nothing. *bot* `no-install` `offline` `read-only` `tracking` `everyday`
- **flashcards** (idea) — Approved question-and-answer pairs become cards, scheduled by spaced repetition. *box* `no-install` `offline` `records` `tracking`
- **forecasts** (idea) — Write a prediction before the outcome, settle it later, see your Brier score. *bot* `no-install` `offline` `records` `tracking`
- **garden** (idea) — What you planted, where and when, and how it did, season by season. *new* `no-install` `offline` `read-only` `tracking`
- **gifts** (idea) — Gifts given and received, and who likes what, so nobody gets the same scarf twice. *new* `no-install` `offline` `read-only` `tracking`
- **invoices** (idea) — For freelancers: invoices and payments matched by the id pattern you give, never guessed. *new* `no-install` `offline` `read-only` `tracking`
- **milestones** (idea) — Your child's firsts, words and heights, from your notes, by age. *new* `no-install` `offline` `read-only` `tracking`
- **oakenscroll** (idea) — Oakenscroll's Office calibration ledger: what you believed, how hard, and how it resolved, as dated passages. *new* `no-install` `offline` `writes-output` `tracking`
- **outdated** (idea) — How old each locked dependency is, and which are yanked, deprecated or two years without a release, from a registry index you downloaded. *new* `no-install` `offline` `read-only` `tracking`
- **pets** (idea) — Each pet's vet visits, vaccines and medicines, from your records: what's due next. *new* `no-install` `offline` `read-only` `tracking`
- [**readings**](adapters/stdlib/readings/) — Numbers over time and a date gone by, beside an answer. *box* `no-install` `offline` `records` `tracking`
- **school** (idea) — School letters and emails for parents: trips, forms due, term dates, and what to bring. *new* `no-install` `offline` `read-only` `tracking`
- **session-cost** (idea) — Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep. *new* `no-install` `offline` `read-only` `tracking`
- **subscriptions** (idea) — What you pay for every month, found in bank statements and emails, and when each renews. *new* `no-install` `offline` `read-only` `tracking`
- **tax-year** (idea) — One tax year's receipts and statements gathered in one place, each with the file it came from. *new* `no-install` `offline` `read-only` `tracking`
- [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first. *box* `no-install` `offline` `read-only` `tracking`
- **trips** (idea) — Your trips from booking emails and tickets: where you went, when, and where you stayed. *new* `no-install` `offline` `read-only` `tracking`
- **warranties** (idea) — Receipts and warranties: when the dishwasher's cover ends, and where its receipt is. *new* `no-install` `offline` `read-only` `tracking`

### Trust and proof

- **backup** (idea) — Copies your record and your key to a place you choose, checks the copy's chain verifies, and won't put the key beside the box. *new* `no-install` `offline` `writes-output` `trust` `everyday`
- **changed** (idea) — What's new, edited or deleted in your folder since the last check, as fingerprint rows. *bot* `no-install` `offline` `records` `trust`
- **encrypt** (idea) — Keeps the record folder encrypted at rest. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `records` `trust`
- [**export**](adapters/stdlib/export/) — Approved answers, and the question log (counts only, never words), as Markdown or CSV. *box* `no-install` `offline` `read-only` `trust`
- **git-notes** (idea) — Approved answers kept as git notes on the commits they cite, so they travel with the repo to any forge. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `trust`
- **history** (idea) — Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words. *new* `no-install` `offline` `read-only` `trust` `everyday`
- **in-case** (idea) — A letter for the people you trust, if something happens to you: where things are and who to call, from your files, sealed by you. *new* `no-install` `offline` `writes-output` `trust`
- **jeles** (idea) — Your approved answers as Jeles nuggets, with question, answer, sources and who sealed it, and Jeles' own verified nuggets read back as passages. *new* `no-install` `offline` `writes-output` `trust`
- **licenses** (idea) — The licence of every installed dependency, read from its own metadata on this machine: which are copyleft, and which file says so. *new* `no-install` `offline` `read-only` `trust`
- **line-origin** (idea) — Which agent session wrote this line of code: git blame to the commit, then the transcript turn that made it. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `read-only` `trust`
- **mirror** (idea) — Checks each mirror of a repo on another forge holds the same commits as the original, so losing a host loses nothing. Needs the git program; GPL, called not linked. Goes online: each mirror's git URL, to read its refs. *new* `needs-install` `online` `read-only` `trust`
- **nestor** (idea) — Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when. *new* `no-install` `offline` `writes-output` `trust`
- **pgp** (idea) — Signs exports and reports with your PGP key, verifiable anywhere. Needs the gpg program and python-gnupg; BSD. *new* `needs-install` `offline` `writes-output` `trust`
- **provenance** (idea) — Checks a package's Sigstore provenance or PyPI attestation names the repo and commit it claims, before you trust it. Needs sigstore; Apache-2.0. Goes online: the registry and Sigstore's log, to fetch the attestation. *new* `needs-install` `online` `read-only` `trust`
- **quote-review** (idea) — A review comment that quotes the repo, checked: does the quoted line still say that at the pull request's head? Goes online: the forge, through the workflow's token, to read the review comments. *new* `no-install` `online` `read-only` `trust`
- **redential** (idea) — The bundle redential-cli's scan makes, written to the record before you submit it, so what left your machine can be checked later. Needs the redential program, run through npx; Apache-2.0. *new* `needs-install` `offline` `records` `trust`
- **report** (idea) — A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. *box* `no-install` `offline` `writes-output` `trust`
- **sap-gate** (idea) — The mcp add-on's tool calls checked against SAP/1.0 grants before they run, through openclaw-sap-gate. Needs openclaw-sap-gate; MIT. *new* `needs-install` `offline` `read-only` `trust`
- **signed-commits** (idea) — Which commits are signed, and by whose key, checked on this machine against the keys you trust. Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `read-only` `trust`
- [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. *box* `no-install` `offline` `read-only` `trust`
- **timeline** (idea) — A dated timeline of one matter (a dispute, an illness, a tenancy), every line cited, to hand to a lawyer, doctor or council. *new* `no-install` `offline` `writes-output` `trust`

### Privacy and safety

- **advisories** (idea) — Security advisories from a downloaded OSV or GitHub advisory database, matched to your lockfiles: which dependency each names, and since when. *new* `no-install` `offline` `read-only` `privacy`
- **install-scripts** (idea) — The install scripts the packages in node_modules would run (preinstall, install, postinstall), each cited by file and line. *new* `no-install` `offline` `read-only` `privacy`
- **package-contents** (idea) — What's inside a wheel, sdist, npm tarball or .crate before you install it: every file, and any code it runs on install. *new* `no-install` `offline` `read-only` `privacy`
- [**privacy**](adapters/stdlib/privacy/) — Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. *bot* `no-install` `offline` `records` `privacy`
- **secrets-audit** (idea) — Finds keys and passwords sitting in plain files. *bot* `no-install` `offline` `read-only` `privacy`
- **transcript-redact** (idea) — An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line. *new* `no-install` `offline` `writes-output` `privacy`
- **typosquat** (idea) — Dependency names a letter off from a popular one (reqeusts, lodahs), checked against a list of top packages you downloaded. *new* `no-install` `offline` `read-only` `privacy`

### Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal.

- [**aider**](adapters/stdlib/aider/) — Aider reads answers from your folder with its /run command, file and line included. *new* `no-install` `offline` `read-only` `assistant`
- **basic-memory** (idea) — Basic Memory's Markdown notes where an AI wrote them: each observation and relation handed in through propose, waiting for your seal. *new* `no-install` `offline` `records` `assistant`
- **claude** (idea) — Suggestions from Claude through the Anthropic API, citing your passages. Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `records` `assistant`
- [**claude-code**](adapters/stdlib/claude-code/) — Claude Code sees cited passages from your folder with each prompt, through its prompt hook. *bot* `no-install` `offline` `records` `assistant`
- [**codex-cli**](adapters/stdlib/codex-cli/) — OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**copilot**](adapters/stdlib/copilot/) — GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**cursor**](adapters/stdlib/cursor/) — Cursor asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**gemini-cli**](adapters/stdlib/gemini-cli/) — Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- **hermes** (idea) — Hermes Agent asking your folder as a plugin, and its memories, and what its dreaming plugin consolidates, handed in through propose. *new* `no-install` `offline` `records` `assistant`
- **issue-answer** (idea) — A workflow that drafts an answer to a new issue from the repo's own docs, each line cited, posted only once a maintainer seals it. Goes online: the forge, through the workflow's token, to post an answer once it is sealed. *new* `no-install` `online` `records` `assistant`
- **local-model** (idea) — Suggestions from a model on this machine only, such as Ollama or llama.cpp. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- [**mcp**](adapters/deps/mcp/) — Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. Needs mcp; MIT. *new* `needs-install` `offline` `records` `assistant`
- [**mcp-lite**](adapters/stdlib/mcp-lite/) — The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only. *box* `no-install` `offline` `records` `assistant`
- **memory-import** (idea) — An AI assistant's memory store, SQLite or Markdown, handed in through propose: one suggestion per memory, none trusted until you seal it. *new* `no-install` `offline` `records` `assistant`
- **mex** (idea) — mex's project memory for coding agents: its scaffold read as cited passages, and what an agent writes back held for your seal. *new* `no-install` `offline` `records` `assistant`
- [**opencode**](adapters/stdlib/opencode/) — OpenCode asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**windsurf**](adapters/stdlib/windsurf/) — Windsurf asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**zed**](adapters/stdlib/zed/) — Zed's assistant asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`

### Ways to use it

- [**browse**](adapters/stdlib/browse/) — Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only. Reaches this machine only. *new* `no-install` `this-machine` `records` `interface` `everyday`
- [**emacs**](adapters/stdlib/emacs/) — Answers in an Emacs compilation buffer, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- [**jetbrains**](adapters/stdlib/jetbrains/) — An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line. *new* `no-install` `offline` `read-only` `interface`
- **large-print** (idea) — Answers in large, high-contrast type, read on a screen or printed. *new* `no-install` `offline` `read-only` `interface`
- [**pipe**](adapters/stdlib/pipe/) — Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf. *box* `no-install` `offline` `records` `interface`
- [**plain**](adapters/stdlib/plain/) — Answers as sentences instead of JSON, each with its file and line. *new* `no-install` `offline` `records` `interface`
- **pr-context** (idea) — On a pull request, the passages in the repo's docs that name the files it changes, posted as one comment. Goes online: the forge, through the workflow's token, to post the comment. *new* `no-install` `online` `read-only` `interface`
- **print** (idea) — An answer as a printable page with its sources, to take to an appointment. *new* `no-install` `offline` `writes-output` `interface`
- **safe-app** (idea) — willow as a SAFE app: installed from the SAFE App Store, authorized per session, and deleted clean. *new* `no-install` `offline` `read-only` `interface`
- **share** (idea) — One sealed answer to send someone, checkable by them, without giving them the folder. *new* `no-install` `offline` `writes-output` `interface`
- [**shell**](adapters/stdlib/shell/) — A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows. *new* `no-install` `offline` `records` `interface`
- **speak** (idea) — Reads answers aloud. Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` `read-only` `interface`
- **start** (idea) — First run in one step: asks where your files are, makes the box and key where they belong, copies in the starter words, and prints the double-click launcher. *new* `no-install` `offline` `writes-output` `interface` `everyday`
- [**vim**](adapters/stdlib/vim/) — Answers in Vim and Neovim's quickfix list, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- [**vscode**](adapters/stdlib/vscode/) — A VS Code task whose answers land in the Problems panel, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`

### Play

- **dice** (idea) — Seeded dice rolls as rows: every roll replayable and checkable. *bot* `no-install` `offline` `records` `play`
- **dice5e** (idea) — Full tabletop dice notation (4d6kh3, advantage). Needs dice; MIT. *bot* `needs-install` `offline` `records` `play`
- **life** (idea) — Conway's Game of Life as rows: a fully deterministic world on the record. *bot* `no-install` `offline` `records` `play`

### For maintainers

- **agents-md-check** (idea) — Commands and paths named in AGENTS.md or CLAUDE.md that no longer exist in the repo. *new* `no-install` `offline` `read-only` `maintainers`
- [**ci**](adapters/stdlib/ci/) — This repo's checks as verdict rows on a kernel record, the same every run. Goes online: PyPI, to read each dependency floor's release date. *box* `no-install` `online` `records` `maintainers`
- **crates** (idea) — A Rust port of kernel.py on crates.io, held to the same vectors as the other four. Goes online: crates.io, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **forgejo** (idea) — What willow's repo needs from Forgejo, Gitea or Codeberg: its host.json and an Actions file, so the repo can move there. Goes online: the Forgejo instance's API, to read the author of a pull request a security report points to. *new* `no-install` `online` `read-only` `maintainers`
- [**github**](adapters/stdlib/github/) — What willow's repo needs from GitHub, kept in one folder so it can be taken away. Goes online: GitHub, through gh, to read the author of a pull request a security report points to. *box* `no-install` `online` `read-only` `maintainers`
- **gitlab** (idea) — What willow's repo needs from GitLab, as github does for GitHub: its host.json and CI file, so the repo can move there. Goes online: GitLab, through glab, to read the author of a merge request a security report points to. *new* `no-install` `online` `read-only` `maintainers`
- [**live**](adapters/stdlib/live/) — Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here. Goes online: only what the programs it starts reach on their own; it reaches nothing itself. *new* `no-install` `maintainers` `tests` `interface` `assistant`
- **maven** (idea) — The Java port on Maven Central, built from this repo and checked against the vectors. Goes online: Maven Central, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- [**mutants**](adapters/stdlib/mutants/) — Breaks each add-on's code on purpose and checks its tests notice. *new* `no-install` `offline` `read-only` `maintainers`
- **npm** (idea) — The TypeScript port on npm, built from this repo, checked against the vectors, and published with provenance; npx runs it. Goes online: registry.npmjs.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **nuget** (idea) — The C# port on NuGet, built from this repo and checked against the vectors. Goes online: nuget.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- **pins** (idea) — Version ranges in package.json, pyproject.toml or Cargo.toml that no lockfile holds. *new* `no-install` `offline` `read-only` `maintainers`
- **pypi** (idea) — kernel.py on PyPI as a package with no dependencies, built from this repo, checked against the vectors, and attested on upload; uvx and pipx run it. Goes online: upload.pypi.org, to publish a release a maintainer tags. *new* `no-install` `online` `writes-output` `maintainers`
- [**readme**](adapters/stdlib/readme/) — Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. *new* `no-install` `offline` `writes-output` `maintainers`
- **reconciler** (idea) — willow-reconciler run on this repo's idea list and git history: how much of what was proposed has landed. Needs willow-reconciler; Apache-2.0. *new* `needs-install` `offline` `read-only` `maintainers`
- [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search. *box* `no-install` `offline` `read-only` `maintainers`
- **sourcehut** (idea) — What willow's repo needs from SourceHut: its host.json for patches by email and a builds.sr.ht manifest. Goes online: sr.ht, through hut, to read the author of a patch a security report points to. *new* `no-install` `online` `read-only` `maintainers`
<!-- /willow:list -->

Back to the [README](README.md).
