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
`█████████████░░░░░░░` **49 of 76 built** · 59 need no install · 17 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 7 | 8 | 9 | 6 |
| Finding things | 4 | 2 | 4 | 2 |
| Your own words | 5 | 2 | 5 | 2 |
| Keeping track | 5 | 4 | 9 | 0 |
| Trust and proof | 2 | 4 | 4 | 2 |
| Privacy and safety | 1 | 1 | 2 | 0 |
| Assistants | 11 | 2 | 10 | 3 |
| Ways to use it | 8 | 1 | 8 | 1 |
| Play | 0 | 3 | 2 | 1 |
| For maintainers | 6 | 0 | 6 | 0 |
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

- **bank** (idea) — Bank CSV and OFX statements as dated lines, with spending by month. *new* `no-install` `offline` `writes-output` `file-reader`
- **bookmarks** (idea) — Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file. *new* `no-install` `offline` `writes-output` `file-reader`
- [**books**](adapters/stdlib/books/) — Kindle "My Clippings.txt" highlights and .epub text. *new* `no-install` `offline` `writes-output` `file-reader`
- [**calendar**](adapters/stdlib/calendar/) — .ics events and .vcf contacts as dated lines. *new* `no-install` `offline` `writes-output` `file-reader`
- [**chats**](adapters/stdlib/chats/) — WhatsApp and Telegram exports, one dated line per message. *new* `no-install` `offline` `writes-output` `file-reader`
- **git-history** (idea) — Commit messages and diffs as a dated pile: "when did we change the retry limit?" Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `writes-output` `file-reader`
- **health** (idea) — Apple Health and Google Fit exports as daily numbers the readings add-on can trend. *new* `no-install` `offline` `writes-output` `file-reader`
- [**mail**](adapters/stdlib/mail/) — .eml and .mbox files, with sender, date and subject kept. *new* `no-install` `offline` `writes-output` `file-reader`
- [**notes**](adapters/stdlib/notes/) — Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. *new* `no-install` `offline` `writes-output` `file-reader`
- **ocr** (idea) — Text out of photos of letters and scanned PDFs. Needs pytesseract and the tesseract program; Apache-2.0. *new* `needs-install` `offline` `writes-output` `file-reader`
- [**office**](adapters/stdlib/office/) — .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. *new* `no-install` `offline` `writes-output` `file-reader`
- [**pdf**](adapters/deps/pdf/) — Text out of PDFs. Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `writes-output` `file-reader`
- **photos** (idea) — When and where each photo was taken, as dated lines. Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `writes-output` `file-reader`
- **sheets** (idea) — Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. Needs openpyxl; MIT. *new* `needs-install` `offline` `writes-output` `file-reader`
- **voice** (idea) — Dictation, calls and lectures transcribed into dated text. Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `writes-output` `file-reader`

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
- [**words-de**](adapters/stdlib/words-de/) — German common words, so questions aren't matched on "der" and "und". *new* `no-install` `offline` `records` `words` `german`
- [**words-es**](adapters/stdlib/words-es/) — Spanish common words ("el", "y"). *new* `no-install` `offline` `records` `words` `spanish`
- [**words-fr**](adapters/stdlib/words-fr/) — French common words ("le", "et"). *new* `no-install` `offline` `records` `words` `french`
- [**words-pt**](adapters/stdlib/words-pt/) — Portuguese common words ("o", "e"). *new* `no-install` `offline` `records` `words` `portuguese`

### Keeping track

- [**again**](adapters/stdlib/again/) — Questions you keep asking: "asked 4 times; approve an answer?" *bot* `no-install` `offline` `read-only` `tracking`
- **care** (idea) — For caregivers: medications, vitals and appointments from a care log, what's due and what moved. *box* `no-install` `offline` `read-only` `tracking`
- [**coming-up**](adapters/stdlib/coming-up/) — Dates written in your files in the next N days: appointments, renewals, deadlines. *box* `no-install` `offline` `read-only` `tracking`
- [**digest**](adapters/stdlib/digest/) — One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that keep finding nothing. *bot* `no-install` `offline` `read-only` `tracking` `everyday`
- **flashcards** (idea) — Approved question-and-answer pairs become cards, scheduled by spaced repetition. *box* `no-install` `offline` `records` `tracking`
- **forecasts** (idea) — Write a prediction before the outcome, settle it later, see your Brier score. *bot* `no-install` `offline` `records` `tracking`
- **invoices** (idea) — For freelancers: invoices and payments matched by the id pattern you give, never guessed. *new* `no-install` `offline` `read-only` `tracking`
- [**readings**](adapters/stdlib/readings/) — Numbers over time and a date gone by, beside an answer. *box* `no-install` `offline` `records` `tracking`
- [**todo**](adapters/stdlib/todo/) — TODO, FIXME and "need to" lines across the folder, oldest first. *box* `no-install` `offline` `read-only` `tracking`

### Trust and proof

- **changed** (idea) — What's new, edited or deleted in your folder since the last check, as fingerprint rows. *bot* `no-install` `offline` `records` `trust`
- **encrypt** (idea) — Keeps the record folder encrypted at rest. Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `records` `trust`
- [**export**](adapters/stdlib/export/) — Approved answers, and the question log (counts only, never words), as Markdown or CSV. *box* `no-install` `offline` `read-only` `trust`
- **pgp** (idea) — Signs exports and reports with your PGP key, verifiable anywhere. Needs the gpg program and python-gnupg; BSD. *new* `needs-install` `offline` `writes-output` `trust`
- **report** (idea) — A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. *box* `no-install` `offline` `writes-output` `trust`
- [**stale**](adapters/stdlib/stale/) — Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. *box* `no-install` `offline` `read-only` `trust`

### Privacy and safety

- [**privacy**](adapters/stdlib/privacy/) — Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. *bot* `no-install` `offline` `records` `privacy`
- **secrets-audit** (idea) — Finds keys and passwords sitting in plain files. *bot* `no-install` `offline` `read-only` `privacy`

### Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal.

- [**aider**](adapters/stdlib/aider/) — Aider reads answers from your folder with its /run command, file and line included. *new* `no-install` `offline` `read-only` `assistant`
- **claude** (idea) — Suggestions from Claude through the Anthropic API, citing your passages. Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `records` `assistant`
- [**claude-code**](adapters/stdlib/claude-code/) — Claude Code sees cited passages from your folder with each prompt, through its prompt hook. *bot* `no-install` `offline` `records` `assistant`
- [**codex-cli**](adapters/stdlib/codex-cli/) — OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**copilot**](adapters/stdlib/copilot/) — GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**cursor**](adapters/stdlib/cursor/) — Cursor asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**gemini-cli**](adapters/stdlib/gemini-cli/) — Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- **local-model** (idea) — Suggestions from a model on this machine only, such as Ollama or llama.cpp. Needs a local model server; licence varies by model. Reaches this machine only. *new* `needs-install` `this-machine` `records` `assistant`
- [**mcp**](adapters/deps/mcp/) — Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. Needs mcp; MIT. *new* `needs-install` `offline` `records` `assistant`
- [**mcp-lite**](adapters/stdlib/mcp-lite/) — The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only. *box* `no-install` `offline` `records` `assistant`
- [**opencode**](adapters/stdlib/opencode/) — OpenCode asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**windsurf**](adapters/stdlib/windsurf/) — Windsurf asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`
- [**zed**](adapters/stdlib/zed/) — Zed's assistant asks your folder and hands in suggestions, through the mcp add-on. *new* `no-install` `offline` `read-only` `assistant`

### Ways to use it

- [**browse**](adapters/stdlib/browse/) — Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only. Reaches this machine only. *new* `no-install` `this-machine` `records` `interface` `everyday`
- [**emacs**](adapters/stdlib/emacs/) — Answers in an Emacs compilation buffer, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- [**jetbrains**](adapters/stdlib/jetbrains/) — An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line. *new* `no-install` `offline` `read-only` `interface`
- [**pipe**](adapters/stdlib/pipe/) — Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf. *box* `no-install` `offline` `records` `interface`
- [**plain**](adapters/stdlib/plain/) — Answers as sentences instead of JSON, each with its file and line. *new* `no-install` `offline` `records` `interface`
- [**shell**](adapters/stdlib/shell/) — A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows. *new* `no-install` `offline` `records` `interface`
- **speak** (idea) — Reads answers aloud. Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` `read-only` `interface`
- [**vim**](adapters/stdlib/vim/) — Answers in Vim and Neovim's quickfix list, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`
- [**vscode**](adapters/stdlib/vscode/) — A VS Code task whose answers land in the Problems panel, each a jump to its file and line. *new* `no-install` `offline` `read-only` `interface`

### Play

- **dice** (idea) — Seeded dice rolls as rows: every roll replayable and checkable. *bot* `no-install` `offline` `records` `play`
- **dice5e** (idea) — Full tabletop dice notation (4d6kh3, advantage). Needs dice; MIT. *bot* `needs-install` `offline` `records` `play`
- **life** (idea) — Conway's Game of Life as rows: a fully deterministic world on the record. *bot* `no-install` `offline` `records` `play`

### For maintainers

- [**ci**](adapters/stdlib/ci/) — This repo's checks as verdict rows on a kernel record, the same every run. Goes online: PyPI, to read each dependency floor's release date. *box* `no-install` `online` `records` `maintainers`
- [**github**](adapters/stdlib/github/) — What willow's repo needs from GitHub, kept in one folder so it can be taken away. Goes online: GitHub, through gh, to read the author of a pull request a security report points to. *box* `no-install` `online` `read-only` `maintainers`
- [**live**](adapters/stdlib/live/) — Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here. Goes online: only what the programs it starts reach on their own; it reaches nothing itself. *new* `no-install` `maintainers` `tests` `interface` `assistant`
- [**mutants**](adapters/stdlib/mutants/) — Breaks each add-on's code on purpose and checks its tests notice. *new* `no-install` `offline` `read-only` `maintainers`
- [**readme**](adapters/stdlib/readme/) — Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. *new* `no-install` `offline` `writes-output` `maintainers`
- [**similar**](adapters/stdlib/similar/) — What's already on the add-on list near a new idea, by the kernel's own search. *box* `no-install` `offline` `read-only` `maintainers`
<!-- /willow:list -->

Back to the [README](README.md).
