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
`█████████████░░░░░░░` **351 of 537 built** · 482 need no install · 55 need one

| Section | Built | Ideas | No install | Needs one |
|---|---|---|---|---|
| Reading more kinds of files | 94 | 30 | 115 | 9 |
| Finding things | 34 | 14 | 38 | 10 |
| Your own words | 21 | 7 | 25 | 3 |
| Keeping track | 43 | 15 | 57 | 1 |
| Trust and proof | 32 | 23 | 46 | 9 |
| Privacy and safety | 13 | 3 | 16 | 0 |
| Assistants | 49 | 23 | 64 | 8 |
| Ways to use it | 29 | 18 | 41 | 6 |
| Play | 12 | 29 | 37 | 4 |
| For maintainers | 24 | 24 | 43 | 5 |
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
- 2026-11-09 · [**synonyms**](adapters/stdlib/synonyms/) \
  Words-list lines for a word no file holds: the dictionary's other words that your files do hold.
- 2026-11-08 · [**wake-gate**](adapters/deps/wake-gate/) \
  Ask out loud after a wake word you chose: audio before it is never transcribed, kept or sent.
- 2026-11-08 · [**skim**](adapters/stdlib/skim/) \
  The lists this repo makes held to how a person reads them: a heading each screen, no line too long, each add-on and folder a name to find.
- 2026-11-08 · [**ready**](adapters/stdlib/ready/) \
  A branch made ready for its pull request, on no host: the repo's own steps run in order, what they make committed, and the body written.
- 2026-11-07 · [**restack-open**](adapters/stdlib/restack-open/) \
  Every open pull request that conflicts with its base, merged up to it by restack's rules and pushed, or named for a person.
<!-- /willow:newest -->

## Add-on of the week

<!-- willow:pick week=2026-W46 -->
**[fixity](adapters/stdlib/fixity/)** \
Your folder's files hashed again now and then, the hashes kept on the record, and a file that changed with no edit of yours flagged as rot.

*Drawn for 2026-W46: SHA-256 of "willow add-on of the week 2026-W46", modulo the 351 built add-ons in name order.*
<!-- /willow:pick -->

<!-- willow:list -->
**Contents:** [Reading more kinds of files](#reading-more-kinds-of-files) · [Finding things](#finding-things) · [Your own words](#your-own-words) ·
[Keeping track](#keeping-track) · [Trust and proof](#trust-and-proof) · [Privacy and safety](#privacy-and-safety) · [Assistants](#assistants) ·
[Ways to use it](#ways-to-use-it) · [Play](#play) · [For maintainers](#for-maintainers)

## Reading more kinds of files

Each writes plain text into a mirror folder the kernel searches, so your originals are never touched.

### Documents and office files, a to n

- <a id="asciidoc"></a>[**asciidoc**](adapters/stdlib/asciidoc/) \
  AsciiDoc documents as the text they show, line for line, markup taken off, cited by the file's own lines. \
  *new* `no-install` `offline` `markup` `documents` · near: org, markdown, latex
- <a id="bibtex"></a>[**bibtex**](adapters/stdlib/bibtex/) \
  .bib files: each reference as a passage, so you can ask which paper said it and get its key. \
  *new* `no-install` `offline` `reference` · near: ris, equations, pgn
- <a id="books"></a>[**books**](adapters/stdlib/books/) \
  Kindle "My Clippings.txt" highlights and .epub text. \
  *new* `no-install` `offline` `highlights` `book` · near: almanac, oakenscroll, text
- <a id="clauses"></a>[**clauses**](adapters/stdlib/clauses/) \
  A policy, contract or terms as one sentence a passage, so an answer lands on its clause; and what changed between two versions, by sentence. \
  *new* `no-install` `offline` `policies` · near: web-pages, photos, pdf
- <a id="equations"></a>[**equations**](adapters/stdlib/equations/) \
  Each displayed equation in LaTeX sources as a passage of its own, with the sentences around it and its label, cited by the .tex file's line. \
  *new* `no-install` `offline` `latex` `equation` · near: latex, notation, code-comments
- <a id="latex"></a>[**latex**](adapters/stdlib/latex/) \
  LaTeX sources as plain prose, commands stripped, cited by the .tex file's own lines. \
  *new* `no-install` `offline` `latex` `prose` · near: equations, org, asciidoc
- <a id="man-pages"></a>[**man-pages**](adapters/stdlib/man-pages/) \
  The man pages installed on this machine as plain text, so you can ask your own system's docs. \
  *new* `no-install` `offline` · near: rtf, notion, books
- <a id="markdown"></a>[**markdown**](adapters/stdlib/markdown/) \
  Any Markdown file as the text it shows, line for line, with no word the file doesn't hold. \
  *new* `no-install` `offline` `markdown` `documents` · near: asciidoc, rtf, rst
- <a id="mediawiki"></a>[**mediawiki**](adapters/stdlib/mediawiki/) \
  A MediaWiki XML dump: each page's latest text, with its title and when it changed. \
  *new* `no-install` `offline` `title` `xml` · near: notion, warc, jira
- <a id="notation"></a>[**notation**](adapters/stdlib/notation/) \
  Each displayed LaTeX equation with the words its paper gives its symbols ("where η is the packing fraction"), so words find the equation. \
  Uses equations. *new* `no-install` `offline` `latex` `equation` · near: equations, latex, bibtex

#### Documents and office files, o to z

- <a id="ocr"></a>[**ocr**](adapters/deps/ocr/) \
  Text out of photos of letters and scanned PDFs. \
  Needs Pillow and pypdf, and the tesseract program, run not linked; MIT-CMU, BSD-3-Clause, Apache-2.0. *new* `needs-install` `offline` `photos` `pdf` · near:
  pdf, photos, sheets
- <a id="office"></a>[**office**](adapters/stdlib/office/) \
  .docx, .odt, .pptx, .xlsx and .ods, which are all zipped XML. \
  *new* `no-install` `offline` `office` · near: calendar, mail, text
- <a id="pdf"></a>[**pdf**](adapters/deps/pdf/) \
  Text out of PDFs. \
  Needs pypdf; BSD-3-Clause. *new* `needs-install` `offline` `pdf` · near: ocr, photos, sheets
- <a id="ris"></a>[**ris**](adapters/stdlib/ris/) \
  RIS citation exports from EndNote, Zotero, Mendeley and the journal databases: each reference as a passage that opens with its citation. \
  *new* `no-install` `offline` `zotero` `citation` · near: zotero, bibtex, day-one
- <a id="rst"></a>[**rst**](adapters/stdlib/rst/) \
  reStructuredText files as plain prose, line for line, with directives, roles, links and tables read. \
  *new* `no-install` `offline` `prose` `links` · near: markdown, asciidoc, latex
- <a id="rtf"></a>[**rtf**](adapters/stdlib/rtf/) \
  RTF documents as plain text. \
  *new* `no-install` `offline` `documents` · near: markdown, asciidoc, rst
- <a id="screenplay"></a>[**screenplay**](adapters/stdlib/screenplay/) \
  Fountain and Final Draft scripts: scenes, characters and lines, cited by scene. \
  *new* `no-install` `offline` `characters` · near: code-comments, bibtex, jupyter
- <a id="sheets"></a>[**sheets**](adapters/deps/sheets/) \
  Spreadsheets with formulas and formatting kept, beyond what the office add-on reads. \
  Needs openpyxl; MIT. *new* `needs-install` `offline` `address` · near: pdf, photos, ocr
- <a id="text"></a>[**text**](adapters/stdlib/text/) \
  Plain-text files the kernel leaves out (UTF-16, an old code page, over 1 MB, lines past 500 characters) as UTF-8 it reads, line for line. \
  *new* `no-install` `offline` · near: mail, calendar, texts
- <a id="zotero"></a>[**zotero**](adapters/stdlib/zotero/) \
  Your Zotero library, from a copy of zotero.sqlite: items, notes and PDF annotations, each with its citation. \
  *new* `no-install` `offline` `zotero` `annotations` · near: ris, readwise, evernote

### Mail and chat

- <a id="apple-mail"></a>[**apple-mail**](adapters/stdlib/apple-mail/) \
  Apple Mail's .emlx messages, read as the mail add-on reads an .eml. \
  Uses mail. *new* `no-install` `offline` `eml` `mail` · near: mail, text, calendar
- <a id="chats"></a>[**chats**](adapters/stdlib/chats/) \
  WhatsApp and Telegram exports, one dated line per message. \
  *new* `no-install` `offline` `message` `chats` · near: texts, matrix, slack
- <a id="discord"></a>[**discord**](adapters/stdlib/discord/) \
  Discord's data package: your messages, one dated line each, by server and channel. \
  *new* `no-install` `offline` `message` `channel` · near: slack, irc, matrix
- <a id="irc"></a>[**irc**](adapters/stdlib/irc/) \
  IRC logs from WeeChat, irssi or ZNC, one dated line per message, by network and channel. \
  *new* `no-install` `offline` `message` `channel` · near: slack, matrix, discord
- <a id="linkedin"></a>[**linkedin**](adapters/stdlib/linkedin/) \
  LinkedIn's data export: messages, posts and connections as dated lines. \
  *new* `no-install` `offline` `posts` `message` · near: reddit, meta-archive, discord
- <a id="mail"></a>[**mail**](adapters/stdlib/mail/) \
  .eml and .mbox files, with sender, date and subject kept. \
  *new* `no-install` `offline` `eml` `mail` · near: apple-mail, text, office
- <a id="mastodon"></a>[**mastodon**](adapters/stdlib/mastodon/) \
  A Mastodon or Pixelfed account archive's outbox.json: your posts as dated lines. \
  *new* `no-install` `offline` `posts` `archive` · near: x-archive, meta-archive, linkedin
- <a id="matrix"></a>[**matrix**](adapters/stdlib/matrix/) \
  Element's room export, JSON or HTML: one dated line per message in each Matrix room. \
  *new* `no-install` `offline` `message` `html` · near: slack, chats, irc
- <a id="meta-archive"></a>[**meta-archive**](adapters/stdlib/meta-archive/) \
  Facebook and Instagram's Download Your Information files: posts, comments and messages as dated lines. \
  *new* `no-install` `offline` `posts` `message` · near: x-archive, linkedin, mastodon
- <a id="reddit"></a>[**reddit**](adapters/stdlib/reddit/) \
  Reddit's data export: your posts, comments and saved items as dated lines. \
  *new* `no-install` `offline` `posts` `data` · near: linkedin, meta-archive, mastodon
- <a id="slack"></a>[**slack**](adapters/stdlib/slack/) \
  Slack's export zip: one dated line per message, with channel and author. \
  *new* `no-install` `offline` `message` `channel` · near: irc, matrix, chats
- <a id="texts"></a>[**texts**](adapters/stdlib/texts/) \
  Phone text messages, from an Android SMS backup or an iPhone backup's copy, one dated line per message. \
  *new* `no-install` `offline` `message` `backup` · near: chats, slack, irc
- <a id="x-archive"></a>[**x-archive**](adapters/stdlib/x-archive/) \
  An X (Twitter) archive: your posts, replies and DMs as dated lines. \
  *new* `no-install` `offline` `posts` `message` · near: meta-archive, mastodon, linkedin

### Notes, journals and saved pages, b to o

- <a id="bookmarks"></a>[**bookmarks**](adapters/stdlib/bookmarks/) \
  Browser bookmarks (HTML export, Firefox JSON) and history, read from a copy of its SQLite file. \
  *new* `no-install` `offline` `json` `sqlite` · near: codebase-memory, nestor, wallabag
- <a id="day-one"></a>[**day-one**](adapters/stdlib/day-one/) \
  Day One's JSON export: each journal entry as a dated passage, with its place and weather. \
  *new* `no-install` `offline` `json` · near: gh-json, chats, karakeep
- <a id="evernote"></a>[**evernote**](adapters/stdlib/evernote/) \
  Evernote's .enex files: each note as plain text with its notebook, tags and dates. \
  *new* `no-install` `offline` `tags` · near: joplin, karakeep, wallabag
- <a id="google-keep"></a>[**google-keep**](adapters/stdlib/google-keep/) \
  Google Keep from Takeout: notes, lists and labels as dated passages. \
  *new* `no-install` `offline` `google` `takeout` · near: takeout, location-history, day-one
- <a id="joplin"></a>[**joplin**](adapters/stdlib/joplin/) \
  Joplin's .jex export, read without unpacking it: each note as plain text with its title and dates. \
  *new* `no-install` `offline` `unpacking` `title` · near: evernote, warc, apple-notes
- <a id="jrnl"></a>[**jrnl**](adapters/stdlib/jrnl/) \
  jrnl journals: each [YYYY-MM-DD HH:MM] entry as a dated passage. \
  *new* `no-install` `offline` `journal` `entry` · near: shell-history, outdated, day-one
- <a id="karakeep"></a>[**karakeep**](adapters/stdlib/karakeep/) \
  Karakeep's JSON export: bookmarks, notes and tags as plain text. \
  *new* `no-install` `offline` `tags` `json` · near: wallabag, evernote, notes
- <a id="notes"></a>[**notes**](adapters/stdlib/notes/) \
  Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed. \
  *new* `no-install` `offline` `tags` · near: calendar, karakeep, evernote
- <a id="notion"></a>[**notion**](adapters/stdlib/notion/) \
  Notion's export zip, Markdown and CSV, as plain text with each page's title and path. \
  *new* `no-install` `offline` `title` `zip` · near: mediawiki, slack, joplin
- <a id="opml"></a>[**opml**](adapters/stdlib/opml/) \
  OPML feed and podcast lists, a line per feed under its folder, and outliner exports as indented items with their notes. \
  *new* `no-install` `offline` `feed` `listed` · near: rss-out, notes, slack

#### Notes, journals and saved pages, o to w

- <a id="org"></a>[**org**](adapters/stdlib/org/) \
  Org-mode files as plain lines, Org's markup taken off and each outline entry its own passage, cited by the .org file's own lines. \
  *new* `no-install` `offline` `markup` `entry` · near: asciidoc, latex, json-paths
- <a id="pocket"></a>[**pocket**](adapters/stdlib/pocket/) \
  Pocket's export, the HTML and CSV in its zip, as one dated line per saved article, now that Pocket is gone. \
  *new* `no-install` `offline` `html` `article` · near: slack, matrix, instapaper
- <a id="readwise"></a>[**readwise**](adapters/stdlib/readwise/) \
  Readwise's highlights export: every highlight with its book or article, and your note on it. \
  *new* `no-install` `offline` `book` `highlights` · near: wallabag, books, goodreads
- <a id="shortcuts"></a>[**shortcuts**](adapters/stdlib/shortcuts/) \
  Link files dragged to a desktop or folder (.url, .webloc, .desktop) as their title and the address they hold. \
  *new* `no-install` `offline` `title` `address` · near: bookmarks, notes, musicxml
- <a id="snapshot"></a>[**snapshot**](adapters/stdlib/snapshot/) \
  A web page or data file fetched once into a folder, as it came, with its address, the time and its SHA-256, so later answers cite the copy. \
  Goes online: the address you give, fetched once. *bot* `no-install` `online` `snapshot` `address` `sources` · near: web-pages, webarchive, wayback
- <a id="trello"></a>[**trello**](adapters/stdlib/trello/) \
  A Trello board's JSON export: cards, checklists and comments, by list. \
  *new* `no-install` `offline` `comments` `json` · near: karakeep, day-one, reddit
- <a id="wallabag"></a>[**wallabag**](adapters/stdlib/wallabag/) \
  wallabag's JSON or HTML export: saved entries as plain text, with their tags. \
  *new* `no-install` `offline` `html` `article` · near: karakeep, readwise, evernote
- <a id="warc"></a>[**warc**](adapters/stdlib/warc/) \
  WARC web archives (Webrecorder, Heritrix, the Internet Archive) read without unpacking: each page's text with its address and capture time. \
  *new* `no-install` `offline` `address` `unpacking` · near: joplin, web-pages, webarchive
- <a id="web-pages"></a>[**web-pages**](adapters/stdlib/web-pages/) \
  Saved web pages, .html and .mhtml, as their readable text, with the address they came from. \
  Uses clauses. *new* `no-install` `offline` `address` `readable` · near: webarchive, snapshot, pdf
- <a id="webarchive"></a>[**webarchive**](adapters/stdlib/webarchive/) \
  Pages Safari saved as .webarchive, as their readable text with the address they came from, and their frames' text after them. \
  Uses web-pages. *new* `no-install` `offline` `address` `readable` · near: web-pages, snapshot, photos

### Exports from apps and services

- <a id="almanac"></a>[**almanac**](adapters/stdlib/almanac/) \
  An Almanac's catalog.json: each public dataset's description and source as passages, with when its link was last checked. \
  *new* `no-install` `offline` `almanac` `links` · near: oakenscroll, almanac-keep, books
- <a id="almanac-keep"></a>[**almanac-keep**](adapters/stdlib/almanac-keep/) \
  An Almanac entry's best permitted copy, from the publisher or its ranked recovery list, fetched into your folder with its SHA-256. \
  Uses snapshot. Goes online: the copy's address, fetched once. *new* `no-install` `online` `sha` `copy` · near: almanac, snapshot, index-cache
- <a id="bank"></a>[**bank**](adapters/stdlib/bank/) \
  Bank CSV and OFX statements as dated lines, with spending by month. \
  *new* `no-install` `offline` · near: mastodon, discord, linkedin
- <a id="calendar"></a>[**calendar**](adapters/stdlib/calendar/) \
  .ics events and .vcf contacts as dated lines. \
  *new* `no-install` `offline` · near: texts, chats, office
- <a id="family-tree"></a>[**family-tree**](adapters/stdlib/family-tree/) \
  Family trees from GEDCOM files: who was born where and when, and which record says so. \
  *new* `no-install` `offline` · near: places, bibtex, code-comments
- <a id="goodreads"></a>[**goodreads**](adapters/stdlib/goodreads/) \
  Goodreads and StoryGraph exports: the books you've read, when, and what you thought of them. \
  *new* `no-install` `offline` `title` `book` · near: letterboxd, slack, musicxml
- <a id="health"></a>[**health**](adapters/stdlib/health/) \
  Apple Health and Google Fit exports as daily numbers the readings add-on can trend. \
  *new* `no-install` `offline` `google` `trend` · near: home-sensors, apple-mail, sheets
- <a id="home-sensors"></a>[**home-sensors**](adapters/stdlib/home-sensors/) \
  Home Assistant's history export: sensor readings as dated numbers the readings add-on can trend. \
  *new* `no-install` `offline` `history` `trend` · near: health, location-history, sheets
- <a id="letterboxd"></a>[**letterboxd**](adapters/stdlib/letterboxd/) \
  Letterboxd's export: the films you've watched, your ratings and reviews, as dated lines. \
  *new* `no-install` `offline` · near: goodreads, takeout, matrix
- <a id="listening"></a>[**listening**](adapters/stdlib/listening/) \
  Spotify's data download: what you listened to, by day, so you can ask what was on that summer. \
  *new* `no-install` `offline` `data` `download` · near: discord, linkedin, reddit
- <a id="location-history"></a>[**location-history**](adapters/stdlib/location-history/) \
  Google Maps Timeline and other location exports: where you were, by day. \
  *new* `no-install` `offline` `google` `history` · near: google-keep, orders, day-one
- <a id="oakenscroll"></a>[**oakenscroll**](adapters/stdlib/oakenscroll/) \
  Oakenscroll's Office prediction ledger as dated passages you can ask: what you believed, how sure you were, and how it turned out. \
  *new* `no-install` `offline` `office` · near: almanac, jeles, books
- <a id="orders"></a>[**orders**](adapters/stdlib/orders/) \
  Amazon's order history and other shops' CSV exports: what you bought, when, and for how much. \
  *new* `no-install` `offline` `csv` `history` · near: location-history, reddit, bank
- <a id="pgn"></a>[**pgn**](adapters/stdlib/pgn/) \
  Chess games from PGN files: players, dates, openings and your annotations. \
  *new* `no-install` `offline` `annotations` · near: bibtex, letterboxd, matrix
- <a id="places"></a>[**places**](adapters/stdlib/places/) \
  KML and GeoJSON files: each place's name, note and coordinates as a passage. \
  *new* `no-install` `offline` · near: sarif, readwise, day-one
- <a id="strava"></a>[**strava**](adapters/stdlib/strava/) \
  Strava's export and GPX files: each run, ride and walk as a dated line with its distance and time. \
  *new* `no-install` `offline` · near: takeout, chats, slack
- <a id="takeout"></a>[**takeout**](adapters/stdlib/takeout/) \
  Google Takeout's My Activity and YouTube history, JSON or HTML, as dated lines. \
  *new* `no-install` `offline` `html` `json` · near: matrix, chats, pocket

### Code and data, a to j

- <a id="agent-transcript"></a>[**agent-transcript**](adapters/stdlib/agent-transcript/) \
  Claude Code, Codex, Gemini CLI, Cursor and Copilot session files as plain text, each turn numbered, so you can ask what an agent was told. \
  *new* `no-install` `offline` `gemini` `claude` · near: instruction-files, session-cost, hooks-elsewhere
- <a id="ci-logs"></a>[**ci-logs**](adapters/stdlib/ci-logs/) \
  CI run logs you downloaded (GitHub Actions, GitLab CI, Forgejo Actions): each failing step as a passage. \
  *new* `no-install` `offline` `log` `fails` · near: ci-why, logs, ci-cache
- <a id="code-comments"></a>[**code-comments**](adapters/stdlib/code-comments/) \
  A codebase's comments and docstrings as passages, cited by file and line. \
  *new* `no-install` `offline` `codebase` `sources` · near: codebase-memory, asciidoc, latex
- <a id="codebase-memory"></a>[**codebase-memory**](adapters/stdlib/codebase-memory/) \
  codebase-memory-mcp's code graph, read from a copy of its SQLite file: each function, what calls it, and its file and line. \
  *new* `no-install` `offline` `sqlite` `copy` · near: bookmarks, nestor, code-comments
- <a id="corpus-lens"></a>[**corpus-lens**](adapters/stdlib/corpus-lens/) \
  corpus-lens's process reports on your own sessions with agents, as passages: where your intent arrives, who writes the code. \
  *new* `no-install` `offline` `agent` `session` · near: agent-transcript, session-cost, sarif
- <a id="csv-rows"></a>[**csv-rows**](adapters/stdlib/csv-rows/) \
  CSV and TSV tables as one passage per row, the header row kept once as the first. \
  *new* `no-install` `offline` `csv` `log` · near: json-paths, google-keep, irc
- <a id="dotfiles"></a>[**dotfiles**](adapters/stdlib/dotfiles/) \
  Your dotfiles as passages: which file sets what, for 'where did I set my editor?' \
  *new* `no-install` `offline` · near: org, json-paths, latex
- <a id="gh-json"></a>[**gh-json**](adapters/stdlib/gh-json/) \
  What gh prints with --json (issues, pull requests, runs), saved to a file and read as dated passages. \
  *new* `no-install` `offline` `issues` `pull` · near: goodreads, day-one, jira
- <a id="git-history"></a>[**git-history**](adapters/stdlib/git-history/) \
  Commit messages and diffs as a dated pile: "when did we change the retry limit?" \
  *new* `no-install` `offline` `history` `message` · near: clauses, discord, linkedin
- <a id="jira"></a>[**jira**](adapters/stdlib/jira/) \
  Jira's issue export, CSV or XML: each issue, comment and status change as dated passages. \
  *new* `no-install` `offline` `comments` `xml` · near: mediawiki, linkedin, day-one

#### Code and data, j to s

- <a id="json-paths"></a>[**json-paths**](adapters/stdlib/json-paths/) \
  Any JSON or JSON Lines file as plain lines, one passage per record, each value beside its key. \
  *new* `no-install` `offline` `value` `key` · near: org, csv-rows, rst
- <a id="jupyter"></a>[**jupyter**](adapters/stdlib/jupyter/) \
  Jupyter notebooks: Markdown cells, code and text outputs as passages, cited by cell. \
  *new* `no-install` `offline` `markdown` `notebook` · near: code-comments, markdown, evernote
- <a id="lockfiles"></a>[**lockfiles**](adapters/stdlib/lockfiles/) \
  Lockfiles as passages (package-lock.json, pnpm-lock.yaml, poetry.lock, uv.lock, Cargo.lock, go.sum): each package and its locked version. \
  *new* `no-install` `offline` `json` `version` · near: pins, sbom, discord
- <a id="logs"></a>[**logs**](adapters/stdlib/logs/) \
  System and app logs (syslog, journald's export, nginx): each line dated, so you can ask when it started. \
  *new* `no-install` `offline` `message` `log` · near: discord, irc, linkedin
- <a id="manifests"></a>[**manifests**](adapters/deps/manifests/) \
  Docker Compose and Kubernetes YAML: each service, image, port and volume as a passage. \
  Needs PyYAML; MIT. *new* `needs-install` `offline` · near: photos, pdf, ocr
- <a id="parallel"></a>[**parallel**](adapters/stdlib/parallel/) \
  A reader run over several folders at once, across every CPU core, so a big mirror of many sources builds in a fraction of the time. \
  *new* `no-install` `offline` `core` `mail` · near: fast-tests, index-cache, test-shards
- <a id="sarif"></a>[**sarif**](adapters/stdlib/sarif/) \
  SARIF reports from code scanners such as CodeQL and Semgrep: each finding as a passage with its rule and place. \
  *new* `no-install` `offline` `reports` · near: code-comments, places, codebase-memory
- <a id="sbom"></a>[**sbom**](adapters/stdlib/sbom/) \
  SBOMs in SPDX or CycloneDX JSON: each component, its version and licence, as passages. \
  *new* `no-install` `offline` `json` `version` · near: lockfiles, gh-json, day-one
- <a id="shell-history"></a>[**shell-history**](adapters/stdlib/shell-history/) \
  Your bash, zsh and fish history: what you ran, and when the shell recorded it. \
  *new* `no-install` `offline` `bash` `fish` · near: jrnl, subtitles, shell
- <a id="star-system"></a>[**star-system**](adapters/deps/star-system/) \
  A friend's star-system simulation (science_bitch) run deterministically: each body's Kepler period, and how well the run conserves momentum. \
  Needs numpy; BSD-3-Clause. *bot* `needs-install` `offline` · near: kart, static-search, dialect

### Media

- <a id="chordpro"></a>[**chordpro**](adapters/stdlib/chordpro/) \
  ChordPro song sheets: titles, lyrics and chords, so you can ask which song had that line. \
  *new* `no-install` `offline` `title` `lyrics` · near: musicxml, letterboxd, mediawiki
- <a id="musicxml"></a>[**musicxml**](adapters/stdlib/musicxml/) \
  MusicXML scores: titles, lyrics, tempo and performance markings as passages. \
  *new* `no-install` `offline` `title` `lyrics` · near: chordpro, goodreads, letterboxd
- <a id="photos"></a>[**photos**](adapters/deps/photos/) \
  When and where each photo was taken, as dated lines. \
  Needs Pillow; MIT-CMU. *new* `needs-install` `offline` `photos` · near: pdf, ocr, sheets
- <a id="subtitles"></a>[**subtitles**](adapters/stdlib/subtitles/) \
  Subtitle and transcript files (.vtt, .srt) as lines cited by timestamp, for podcasts and videos already transcribed. \
  *new* `no-install` `offline` `transcript` · near: shell-history, calendar, text

### Other readers


#### Other readers: ideas, not built yet, a to m

- <a id="apple-notes"></a>**apple-notes** (idea) \
  Apple Notes, read from a copy of its database: each note as plain text with its folder and dates. \
  *new* `no-install` `offline` `database` `apple` · near: joplin, evernote, apple-mail
- <a id="archivebox"></a>**archivebox** (idea) \
  ArchiveBox snapshots: each saved page's text, with its URL and the date it was captured. \
  *new* `no-install` `offline` `snapshot` `saved` · near: warc, wayback, snapshot
- <a id="bluesky"></a>**bluesky** (idea) \
  A Bluesky repo.car export: your posts as dated lines, read by a small CAR and CBOR reader of its own. \
  *new* `no-install` `offline` `posts` · near: mastodon, linkedin, reddit
- <a id="canvas"></a>**canvas** (idea) \
  Canvas course exports: pages, assignments and discussions as passages. \
  *new* `no-install` `offline` `assignments` `course` · near: moodle, syllabus, google-classroom
- <a id="chat-dataset"></a>**chat-dataset** (idea) \
  Chat fine-tuning and evaluation sets in JSONL ({"messages": [...]}) as numbered turns, one example after another. \
  *new* `no-install` `offline` `messages` `chat` · near: agent-transcript, chats, teams
- <a id="confluence"></a>**confluence** (idea) \
  A Confluence space's HTML export as plain text, page by page. \
  *new* `no-install` `offline` `html` · near: wallabag, recipes, mediawiki
- <a id="forgejo-dump"></a>**forgejo-dump** (idea) \
  A Forgejo or Gitea dump, Codeberg's included: issues, pull requests and wiki pages as dated passages. \
  *new* `no-install` `offline` `issues` `request` · near: github-archive, forgejo, gh-json
- <a id="github-archive"></a>**github-archive** (idea) \
  Your GitHub account's data export: the issues, pull requests, reviews and comments you wrote, as dated passages with their links. \
  *new* `no-install` `offline` `issues` `request` · near: quote-review, contribute, gitlab-export
- <a id="gitlab-export"></a>**gitlab-export** (idea) \
  A GitLab project export, read without unpacking it: its issues, merge requests and comments as dated passages. \
  *new* `no-install` `offline` `issues` `comments` · near: github-archive, joplin, google-classroom
- <a id="google-classroom"></a>**google-classroom** (idea) \
  Google Classroom from Takeout: assignments, announcements and comments as dated passages. \
  *new* `no-install` `offline` `comments` `takeout` · near: gitlab-export, google-keep, takeout
- <a id="homestead"></a>**homestead** (idea) \
  Homestead's exports from its law, ledger and health modules: records, deadlines and evidence as dated passages. \
  *new* `no-install` `offline` `health` `ledger` · near: gitlab-export, oakenscroll, github-archive
- <a id="instapaper"></a>**instapaper** (idea) \
  Instapaper's CSV and HTML export: saved articles and highlights as dated lines. \
  *new* `no-install` `offline` `html` `article` · near: pocket, wallabag, readwise
- <a id="journiv"></a>**journiv** (idea) \
  Journiv journal entries, with their moods, as dated lines, once its export format is settled. \
  *new* `no-install` `offline` `journal` `entry` · near: day-one, mood, jrnl
- <a id="lessons"></a>**lessons** (idea) \
  Lesson plans from the Emerging Rule community library, by grade and subject, as passages a teacher can ask. \
  *new* `no-install` `offline` `plan` `lesson` · near: my-lessons, lesson-time, support-plan
- <a id="medical-records"></a>**medical-records** (idea) \
  Your health records as FHIR JSON or C-CDA XML: visits, results and prescriptions as dated lines. \
  *new* `no-install` `offline` `json` `health` · near: box-health, takeout, schema-check

#### Other readers: ideas, not built yet, m to w

- <a id="moodle"></a>**moodle** (idea) \
  Moodle course backups: pages, assignments, quizzes and forum posts as passages. \
  *new* `no-install` `offline` `assignments` `course` · near: canvas, syllabus, front-page
- <a id="music-library"></a>**music-library** (idea) \
  Your music files' tags (MP3, FLAC, M4A): artist, album, year and track, as lines. \
  *new* `no-install` `offline` `year` `library` · near: listening, livestock, tax-year
- <a id="package-docs"></a>**package-docs** (idea) \
  The READMEs and docs in packages you've installed (site-packages, node_modules, Cargo's cache), so you can ask your dependencies offline. \
  *new* `no-install` `offline` `install` `package` · near: install-scripts, pins, ci-cache
- <a id="past-papers"></a>**past-papers** (idea) \
  Past exam papers and their mark schemes as passages: which year asked this, and what earned the marks. \
  *new* `no-install` `offline` `exam` `paper` · near: model-exam, bibtex, equations
- <a id="quiet-corner"></a>**quiet-corner** (idea) \
  A Quiet Corner backup file: a teacher's classroom observations as dated passages, for that teacher's questions alone. \
  *new* `no-install` `offline` `classroom` · near: google-classroom, homestead, forgejo-dump
- <a id="recipes"></a>**recipes** (idea) \
  Recipes from saved web pages and recipe-app exports, as plain text: what can I cook with leeks? \
  *new* `no-install` `offline` `saved` `web` · near: web-pages, webarchive, confluence
- <a id="scripture"></a>**scripture** (idea) \
  A scripture or other canonical text with your study notes beside it, cited by book, chapter and verse. \
  *new* `no-install` `offline` `book` `beside` · near: readwise, books, gutenberg
- <a id="scrivener"></a>**scrivener** (idea) \
  Scrivener projects: each document in the binder as plain text, by its place in the manuscript. \
  *new* `no-install` `offline` `documents` · near: rtf, apple-notes, sigmap
- <a id="sigmap"></a>**sigmap** (idea) \
  SigMap's signature map of a codebase as plain text: each function's signature with its file and line, for questions about the code. \
  *new* `no-install` `offline` `codebase` `function` · near: codebase-memory, code-comments, text
- <a id="signal"></a>**signal** (idea) \
  A Signal backup, decrypted with its passphrase, as one dated line per message. \
  Needs cryptography; Apache-2.0 or BSD. *new* `needs-install` `offline` `message` `backup` · near: texts, teams, chats
- <a id="sqlite"></a>**sqlite** (idea) \
  Any SQLite database, read from a copy: each table as a section, each row a line with its column names. \
  *new* `no-install` `offline` `copy` `sqlite` · near: writefreely, apple-notes, codebase-memory
- <a id="steam"></a>**steam** (idea) \
  Your Steam library from its local files: games, playtime and when you last played. \
  *new* `no-install` `offline` `game` `library` · near: life, game-master, music-library
- <a id="teams"></a>**teams** (idea) \
  Microsoft Teams chats from your Microsoft account's export, one dated line per message. \
  *new* `no-install` `offline` `message` `chats` · near: chats, signal, texts
- <a id="voice"></a>**voice** (idea) \
  Dictation, calls and lectures transcribed into dated text. \
  Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `voice` `transcribed` · near: wis, writefreely, texts
- <a id="wis"></a>**wis** (idea) \
  Audio files transcribed by a Willow Inference Server you run on your own network, kept as dated text. \
  Needs a Willow Inference Server you run; Apache-2.0, called over HTTP, not linked. Goes online: your own Willow Inference Server, to transcribe the audio
  you point it at. From: dep of [toverainc/willow-inference-server](https://github.com/toverainc/willow-inference-server), Apache-2.0. *new* `needs-install`
  `online` `transcribed` `audio` · near: voice, wake-gate, writefreely
- <a id="writefreely"></a>**writefreely** (idea) \
  WriteFreely posts, from its export or a copy of its SQLite database, as dated text. \
  *new* `no-install` `offline` `copy` `sqlite` · near: apple-notes, bookmarks, nestor

### What it makes for elsewhere

- <a id="gather"></a>[**gather**](adapters/stdlib/gather/) \
  Folders and files you name, copied into your pile under a name, only the kinds you keep, never a key or a file too big to read. \
  *new* `no-install` `offline` `key` `copy` · near: json-paths, snapshot, repo-pile

### Tools you run yourself


#### Tools you run yourself: ideas, not built yet

- <a id="file-kind"></a>**file-kind** (idea) \
  Each file the kernel leaves out, named by what its first bytes say it is (a PDF, a PNG, a zip), whatever its name or extension says. \
  From: shape of [wagtail/Willow](https://github.com/wagtail/Willow), BSD-3-Clause. *new* `no-install` `offline` `pdf` `whatever` · near: text, pdf, why-not

## Finding things

### What runs on your page

- <a id="amounts"></a>[**amounts**](adapters/stdlib/amounts/) \
  Every sum of money in your files, with its date and the line it's on. \
  *new* `no-install` `offline` `amount` · near: debts, said, chats
- <a id="duplicates"></a>[**duplicates**](adapters/stdlib/duplicates/) \
  Passages that say the same thing in two files, and which one is newer. \
  *new* `no-install` `offline` · near: contradictions, xref, three-two-one
- <a id="fuzzy-dates"></a>[**fuzzy-dates**](adapters/stdlib/fuzzy-dates/) \
  Dates that admit doubt ('about 1880', 'sometime in March') read and kept with their doubt, in EDTF. \
  *new* `no-install` `offline` · near: family-tree, syllabus, sort
- <a id="on-this-day"></a>[**on-this-day**](adapters/stdlib/on-this-day/) \
  What you wrote on this date in earlier years. \
  *box* `no-install` `offline` · near: coming-up, surprise, plain
- <a id="people"></a>[**people**](adapters/stdlib/people/) \
  Everyone your files name, and every place each is mentioned. \
  *new* `no-install` `offline` `mention` · near: first-mention, life, catgrid
- <a id="reading-level"></a>[**reading-level**](adapters/stdlib/reading-level/) \
  How hard a passage reads (sentence length, word length, Flesch), so a teacher can find texts for a class. \
  *new* `no-install` `offline` `length` `sentence` · near: plain, pile-sweep, browse
- <a id="said"></a>[**said**](adapters/stdlib/said/) \
  Your own quotes, gathered: every 'so-and-so, on this date: "..."' in your files, as a dated timeline of what was decided. \
  *new* `no-install` `offline` `timeline` `quote` · near: amounts, timeline, debts
- <a id="surprise"></a>[**surprise**](adapters/stdlib/surprise/) \
  One passage from your folder at random, seeded so it can be replayed. \
  *bot* `no-install` `offline` `seeded` `replayed` · near: on-this-day, serve, daily-word

### Models that suggest answers

- <a id="sort-ask"></a>[**sort-ask**](adapters/stdlib/sort-ask/) \
  A model on this machine suggests a category for each file your phrases didn't place, citing a passage, for your seal. \
  Uses openai-compatible, sort. Reaches this machine only. *new* `no-install` `this-machine` `categories` `phrases` · near: sort, local-model, in-process

### What it makes for elsewhere

- <a id="index-cache"></a>[**index-cache**](adapters/stdlib/index-cache/) \
  Keeps scan's index between runs and rebuilds it only when a file in your folder actually changed. \
  Uses scan. *new* `no-install` `offline` `scan` `index` · near: scan, parallel, policy-watch
- <a id="month-first"></a>[**month-first**](adapters/stdlib/month-first/) \
  For a folder you know writes dates month first: each one's ISO form written beside it, so it can be placed. \
  *new* `no-install` `offline` `month` `form` · near: abbreviations, coming-up, chats
- <a id="pile-build"></a>[**pile-build**](adapters/stdlib/pile-build/) \
  Rebuilds pile-store's saved passages after each change, one build at a time, so your next question doesn't wait for it. \
  Uses pile-store. *bot* `no-install` `offline` `store` `pile` · near: pile-store, pile-serve, pile-rank
- <a id="pile-serve"></a>[**pile-serve**](adapters/stdlib/pile-serve/) \
  Keeps your folder's search ready in one background process on this machine, so a hook's lookup answers in milliseconds instead of seconds. \
  Uses pile-rank, pile-rungs. *bot* `no-install` `offline` `second` `store` `pile` · near: pile-rank, pile-rungs, pile-store
- <a id="pile-store"></a>[**pile-store**](adapters/stdlib/pile-store/) \
  Your folder's passages kept in one file between questions, used only while the folder is unchanged, so add-ons don't re-read it each time. \
  Uses index-cache. *bot* `no-install` `offline` `store` `pile` · near: pile-serve, pile-build, pile-sweep
- <a id="scan"></a>[**scan**](adapters/stdlib/scan/) \
  Index a big folder once, then ask it a list of questions in seconds with the kernel's own answers, of everything or only what's changed. \
  Uses todo. *box* `no-install` `offline` `scan` `ranked` `index` · near: latent, index-cache, bm25

#### What it makes for elsewhere: ideas, not built yet

- <a id="by-function"></a>**by-function** (idea) \
  Code read by function and class instead of by line, so a hit names the function it's in. \
  Needs tree-sitter and its language pack; MIT. *new* `needs-install` `offline` `function` `instead` · near: codebase-memory, sigmap, risky-code
- <a id="crosswalk"></a>**crosswalk** (idea) \
  The outside IDs a passage points to (Wikidata, DOI, ORCID, GeoNames) kept beside it, so your notes join the world's. \
  *new* `no-install` `offline` `beside` `joins` · near: ids, translate, joins
- <a id="meaning"></a>**meaning** (idea) \
  Search by meaning: "who owes me money" finds "invoice outstanding". \
  Needs sentence-transformers; Apache-2.0. Goes online: the model, downloaded once from Hugging Face. *new* `needs-install` `online` `invoice` `owes` · near:
  starter-words, sort, amounts
- <a id="vectors"></a>**vectors** (idea) \
  The meaning add-on's vectors kept in the store's own SQLite file, so they're computed once per passage, not at every question. \
  Needs sqlite-vec and model2vec; MIT or Apache-2.0. *bot* `needs-install` `offline` `store` `sqlite` `pile` · near: pile-store, codebase-memory, welcome
- <a id="watch"></a>**watch** (idea) \
  A file re-read the moment it changes (inotify, FSEvents, or polling), so the index is always current. \
  *new* `no-install` `offline` `index` `moment` · near: index-cache, scan, policy-watch

### Tools you run yourself, a to p

- <a id="all"></a>[**all**](adapters/stdlib/all/) \
  Every matching passage, ranked, not just the top three. \
  *box* `no-install` `offline` `ranked` `matched` · near: claim-check, latent, thesis
- <a id="code-shape"></a>[**code-shape**](adapters/deps/code-shape/) \
  Search code by its shape, not its words: every call of a kind, whatever it's named. \
  Needs the ast-grep program, from ast-grep-cli on PyPI or your own ast-grep; MIT. *new* `needs-install` `offline` `search` · near: risky-code, dialect, stems
- <a id="codeowners"></a>[**codeowners**](adapters/stdlib/codeowners/) \
  Who owns this file: the CODEOWNERS rule that matches it, cited by line, on GitHub, GitLab and Forgejo alike. \
  *new* `no-install` `offline` `gitlab` `github` · near: gitlab, across, rules
- <a id="fair-merge"></a>[**fair-merge**](adapters/stdlib/fair-merge/) \
  Each folder ranked on its own and the lists merged in turns, so a big corpus can't crowd out a small one; one that found nothing says so. \
  Uses scan. *bot* `no-install` `offline` `found` `pile` · near: scan, parallel, bench
- <a id="first-mention"></a>[**first-mention**](adapters/stdlib/first-mention/) \
  When your files first mention something, and the line that does. \
  *new* `no-install` `offline` `mention` · near: dialect-dates, people, timeline
- <a id="glance"></a>[**glance**](adapters/stdlib/glance/) \
  What a scan found, a line a question: where its best passage is, how it opens, and which of the question's words it lacks. \
  Uses scan. *new* `no-install` `offline` `scan` · near: scan, synonyms, latent
- <a id="latent"></a>[**latent**](adapters/deps/latent/) \
  Finds code by meaning, not just matching words, using scan's index: a question reaches code that says the same thing another way. \
  Needs numpy; BSD-3-Clause. Uses scan. *new* `needs-install` `offline` `index` `scan` · near: scan, all, duplicates
- <a id="look"></a>[**look**](adapters/stdlib/look/) \
  One question sent to the step whose job it is, and answered by the lines that step's kept run holds; your own notes by the kernel. \
  Uses route. *new* `no-install` `offline` `owes` · near: pipe, debts, why-not
- <a id="misquote"></a>[**misquote**](adapters/stdlib/misquote/) \
  A quote that is almost in your files: the closest passage, and the words it adds, drops or changes, so a misquote shows as one. \
  *new* `no-install` `offline` `quote` `drops` · near: quotes, stale, quote-check
- <a id="pile-gold"></a>[**pile-gold**](adapters/stdlib/pile-gold/) \
  Your approved answers used as a test: each question asked again, scored by how often search puts its passage in the top five. \
  Uses pile-rank, scan. *box* `no-install` `offline` `search` `pile` · near: again, pile-store, pile-sweep
- <a id="pile-rank"></a>[**pile-rank**](adapters/stdlib/pile-rank/) \
  Finds passages that use your folder's own phrases ("sourdough bread"), not just the separate words, ranked without any AI model. \
  Uses pile-store. *bot* `no-install` `offline` `phrases` `ranked` `pile` · near: pile-rungs, pile-serve, all

#### Tools you run yourself, p to w

- <a id="pile-rungs"></a>[**pile-rungs**](adapters/stdlib/pile-rungs/) \
  Tries the strict word match first, then your folder's phrases, and says which one found the answer and why the others didn't. \
  Uses pile-rank. *bot* `no-install` `offline` `matched` `phrases` `pile` · near: pile-rank, pile-serve, pile-store
- <a id="pile-sweep"></a>[**pile-sweep**](adapters/stdlib/pile-sweep/) \
  Finds the passage length that suits your folder, by asking your answered questions at several lengths and naming the one finding the most. \
  Uses pile-gold, pile-rank, scan. *bot* `no-install` `offline` `pile` · near: pile-store, pile-gold, pile-rank
- <a id="quote-check"></a>[**quote-check**](adapters/stdlib/quote-check/) \
  Is this exact quote in my files, and where? For writers, journalists and students. \
  *box* `no-install` `offline` `quote` · near: quotes, claim-check, xref
- <a id="quotes"></a>[**quotes**](adapters/stdlib/quotes/) \
  Every quote in a document checked against your files: as written, almost (and what it adds, drops or changes), or not there. \
  Uses misquote, quote-check. *new* `no-install` `offline` `quote` `drops` · near: misquote, quote-check, claim-check
- <a id="record-sql"></a>[**record-sql**](adapters/deps/record-sql/) \
  SQL straight over your record, in place: 'how many answers did I approve in March?' \
  Needs DuckDB; MIT. *box* `needs-install` `offline` · near: mcp, static-search, dialect
- <a id="ripgrep"></a>[**ripgrep**](adapters/deps/ripgrep/) \
  Exact search through ripgrep, much faster on a big folder, its hits checked against the kernel's hashes. \
  Needs the ripgrep program, from the ripgrep wheel on PyPI or your own rg; MIT or Unlicense. *new* `needs-install` `offline` `search` · near: manifests, pdf,
  ocr
- <a id="route"></a>[**route**](adapters/stdlib/route/) \
  A question sent to the step whose job it is: money owed to debts and invoices, a date to what's coming up, the rest to the ask. \
  *new* `no-install` `offline` `coming` `money` · near: debts, coming-up, meaning
- <a id="rules"></a>[**rules**](adapters/stdlib/rules/) \
  A game's or a house's rules, approved one section at a time, so asking what a rule says gives back that exact section, word for word. \
  *bot* `no-install` `offline` `game` · near: session-seal, game-master, night-batch
- <a id="sort"></a>[**sort**](adapters/stdlib/sort/) \
  Your files sorted into your own categories, by the phrases you gave each: what's where, and what nothing of yours reached. \
  *new* `no-install` `offline` `phrases` `sorted` `categories` · near: sort-ask, pile-rungs, debts
- <a id="typos"></a>[**typos**](adapters/stdlib/typos/) \
  Forgives misspellings in questions. \
  *new* `no-install` `offline` · near: accents, abbreviations, again
- <a id="why-not"></a>[**why-not**](adapters/stdlib/why-not/) \
  When the answer is 'not enough to say', which words found nothing, and what kind of file would have answered. \
  *new* `no-install` `offline` · near: latent, nicknames, daily-word

#### Tools you run yourself: ideas, not built yet

- <a id="bm25"></a>**bm25** (idea) \
  BM25 over a box in one go, with no index to build first: the rank scan --rank bm25 gives, for a folder you ask once. \
  *new* `no-install` `offline` `index` `scan` · near: scan, index-cache, latent
- <a id="by-index"></a>**by-index** (idea) \
  claim-check, all and first-mention asked of scan's index, so a folder too big to hold in memory is still checked passage by passage. \
  Uses scan. *new* `no-install` `offline` `index` `scan` · near: claim-check, scan, index-cache
- <a id="code-first"></a>**code-first** (idea) \
  Questions code can answer exactly (counts, dates, ids) answered by code before any model, with a wrong answer counted as a defect. \
  *bot* `no-install` `offline` · near: model-exam, sigmap, install-scripts
- <a id="hit-kinds"></a>**hit-kinds** (idea) \
  Every place some text appears, sorted by what it sits inside: on its own, a number, a date, a hash, a path, a name, each with its count. \
  *new* `no-install` `offline` `hit` `sorted` · near: sort, ripgrep, symbols
- <a id="kiwix"></a>**kiwix** (idea) \
  An offline Wikipedia (or Stack Exchange, or Gutenberg) as a source after your own files, cited by article. \
  Needs libzim, and a ZIM file you download; GPL-3.0. *new* `needs-install` `offline` `stack` `wikipedia` · near: pageviews, codeowners, stack-share
- <a id="my-lessons"></a>**my-lessons** (idea) \
  Your own lesson plans by grade, subject and standard: what did I teach on fractions last year? \
  *new* `no-install` `offline` `lesson` `plan` · near: lessons, lesson-time, standards
- <a id="narrow"></a>**narrow** (idea) \
  The question to ask you next: the one fact about what you're after that would cut what's left the most, with the count each answer leaves. \
  *new* `no-install` `offline` `fact` `counts` · near: predict, pile-sweep, lore
- <a id="promises"></a>**promises** (idea) \
  What a candidate or a council said, by date and source, from the documents you saved. \
  *new* `no-install` `offline` `saved` `council` · near: said, thesis, timeline
- <a id="rerank"></a>**rerank** (idea) \
  A small model on the CPU that reorders the top passages by reading the question and each passage together. \
  Needs FlashRank; Apache-2.0. Goes online: the model, downloaded once. *new* `needs-install` `online` `top` · near: model-fit, pile-store, pile-gold
- <a id="standards"></a>**standards** (idea) \
  Curriculum standards beside your lessons: which standard each lesson meets, each cited. \
  *new* `no-install` `offline` `lesson` `standard` · near: my-lessons, lesson-time, grant-report
- <a id="symbols"></a>**symbols** (idea) \
  Exact definitions and references for Python code: where a name is defined, and every place it's used. \
  Needs scip-python; MIT. *new* `needs-install` `offline` `reference` · near: hook-impact, people, code-shape
- <a id="upgrade-notes"></a>**upgrade-notes** (idea) \
  Before an upgrade: the changelog lines between the version you lock and the one you'd move to, from the package's own files. \
  Goes online: the registry (PyPI, npm or crates.io), to fetch the newer version's changelog. *new* `no-install` `online` `package` `version` · near:
  lockfiles, package-contents, install-scripts

## Your own words

The blind tests' biggest gap: on day one, a person's words aren't their files' words.

### What words it knows, a to w

- <a id="abbreviations"></a>[**abbreviations**](adapters/stdlib/abbreviations/) \
  Your own shorthand, written down once (appt, Rx, w/c), so a question finds either form. \
  *new* `no-install` `offline` `form` `down` · near: accents, stems, month-first
- <a id="accents"></a>[**accents**](adapters/stdlib/accents/) \
  A word typed without its accent read as your files write it, and the words-list lines that make it last. \
  *new* `no-install` `offline` · near: abbreviations, stems, typos
- <a id="nicknames"></a>[**nicknames**](adapters/stdlib/nicknames/) \
  The names you call people, mapped to who they are, so 'Mum' finds Margaret. \
  *new* `no-install` `offline` `starter` · near: starter-words, abbreviations, notes
- <a id="starter-words"></a>[**starter-words**](adapters/stdlib/starter-words/) \
  A first-day words list to copy and edit (owes = invoice, outstanding; doctor = dr, physician, clinic). \
  *new* `no-install` `offline` `copy` `starter` · near: start, snapshot, pdf
- <a id="stems"></a>[**stems**](adapters/deps/stems/) \
  Word forms for 20+ languages, so "häuser" finds "haus" and "книги" finds "книга". \
  Needs snowballstemmer; BSD-3-Clause. *new* `needs-install` `offline` `form` · near: accents, abbreviations, ocr
- <a id="synonyms"></a>[**synonyms**](adapters/stdlib/synonyms/) \
  Words-list lines for a word no file holds: the dictionary's other words that your files do hold. \
  Reaches this machine only. *new* `no-install` `this-machine` · near: accents, abbreviations, starter-words
- <a id="words-ar"></a>[**words-ar**](adapters/stdlib/words-ar/) \
  Arabic common words ("في", "من", "على"). \
  *new* `no-install` `offline` `common` `arabic` · near: words-it, words-pl, words-pt
- <a id="words-cy"></a>[**words-cy**](adapters/stdlib/words-cy/) \
  Welsh common words ("a", "y", "yn"). \
  *new* `no-install` `offline` `common` `welsh` · near: words-it, words-es, words-pl
- <a id="words-de"></a>[**words-de**](adapters/stdlib/words-de/) \
  German common words, so questions aren't matched on "der" and "und". \
  *new* `no-install` `offline` `common` `german` · near: words-nl, words-pl, words-it

#### What words it knows, w to w

- <a id="words-es"></a>[**words-es**](adapters/stdlib/words-es/) \
  Spanish common words ("el", "y"). \
  *new* `no-install` `offline` `common` `spanish` · near: words-it, words-pt, words-cy
- <a id="words-fr"></a>[**words-fr**](adapters/stdlib/words-fr/) \
  French common words ("le", "et"). \
  *new* `no-install` `offline` `common` `french` · near: words-it, words-pl, words-pt
- <a id="words-it"></a>[**words-it**](adapters/stdlib/words-it/) \
  Italian common words ("il", "e"). \
  *new* `no-install` `offline` `common` `italian` · near: words-pt, words-tlh, words-es
- <a id="words-nl"></a>[**words-nl**](adapters/stdlib/words-nl/) \
  Dutch common words ("de", "en"). \
  *new* `no-install` `offline` `common` `dutch` · near: words-de, words-it, words-pl
- <a id="words-pl"></a>[**words-pl**](adapters/stdlib/words-pl/) \
  Polish common words ('i', 'w'). \
  *new* `no-install` `offline` `common` `polish` · near: words-it, words-de, words-pt
- <a id="words-pt"></a>[**words-pt**](adapters/stdlib/words-pt/) \
  Portuguese common words ("o", "e"). \
  *new* `no-install` `offline` `common` `portuguese` · near: words-it, words-tlh, words-es
- <a id="words-ru"></a>[**words-ru**](adapters/stdlib/words-ru/) \
  Russian common words ("и", "в", "на"). \
  *new* `no-install` `offline` `common` `russian` · near: words-it, words-pl, words-pt
- <a id="words-sv"></a>[**words-sv**](adapters/stdlib/words-sv/) \
  Swedish common words ('och', 'att'). \
  *new* `no-install` `offline` `common` `swedish` · near: words-it, words-pl, words-pt
- <a id="words-tlh"></a>[**words-tlh**](adapters/stdlib/words-tlh/) \
  Klingon common words ("'ej", "nuq"). \
  *new* `no-install` `offline` `common` `klingon` · near: words-it, words-pt, words-pl
- <a id="words-tr"></a>[**words-tr**](adapters/stdlib/words-tr/) \
  Turkish common words ("ve", "bir"). \
  *new* `no-install` `offline` `common` `turkish` · near: words-it, words-pl, words-pt

#### What words it knows: ideas, not built yet

- <a id="memoir"></a>**memoir** (idea) \
  A question a week about your life, answered in your own words and kept, so your story is in your files. \
  *new* `no-install` `offline` `life` · near: quiz, why-not, browse
- <a id="tatoeba"></a>**tatoeba** (idea) \
  A question in one language finds the same idea in another, through Tatoeba's sentence pairs, downloaded once. \
  *new* `no-install` `offline` `pairs` `language` · near: why-not, stems, latent
- <a id="vocab"></a>**vocab** (idea) \
  The words you're learning, from your notes and the texts you read, with where you met each one. \
  *new* `no-install` `offline` · near: equations, apple-notes, oracle-text
- <a id="words-hi"></a>**words-hi** (idea) \
  Hindi common words ('और', 'है'). \
  *new* `no-install` `offline` `common` · near: words-ja, words-zh, words-it
- <a id="words-ja"></a>**words-ja** (idea) \
  Japanese, which has no spaces: a small segmenter of its own and a common-words list. \
  *new* `no-install` `offline` `common` `segmenter` · near: words-zh, words-hi, synonyms
- <a id="words-later"></a>**words-later** (idea) \
  A box made again with a words list it lacked, its record kept as it was, since a box takes its words only when it is made. \
  *new* `no-install` `offline` · near: ask-later, starter-words, sync
- <a id="words-zh"></a>**words-zh** (idea) \
  Chinese, which has no spaces: words found by a small segmenter of its own, and a common-words list. \
  *new* `no-install` `offline` `common` `found` · near: words-ja, words-hi, synonyms

### What runs on your page

- <a id="dialect"></a>[**dialect**](adapters/deps/dialect/) \
  The words you use far more than the world does: your own dialect, from your files against wordfreq's counts. \
  Needs wordfreq; Apache-2.0, its data CC BY-SA 4.0. *new* `needs-install` `offline` `dialect` `far` · near: dialect-dates, code-shape, stems
- <a id="dialect-dates"></a>[**dialect-dates**](adapters/deps/dialect-dates/) \
  The words your folder uses far more than the world does, each dated by its first and last appearance, with the passage that first says it. \
  Needs wordfreq; Apache-2.0, its data CC BY-SA 4.0. Uses dialect, first-mention. *new* `needs-install` `offline` `dialect` `far` · near: dialect, code-shape,
  pdf

### Tools you run yourself


#### Tools you run yourself: ideas, not built yet

- <a id="misheard"></a>**misheard** (idea) \
  A spoken question's misheard words corrected against your own folder's words before it is asked, each change shown. \
  From: shape of [toverainc/willow-autocorrect](https://github.com/toverainc/willow-autocorrect), Apache-2.0. *new* `no-install` `offline` `spoken` · near:
  pile-build, predict, scan

## Keeping track

### Exports from apps and services

- <a id="robinhood"></a>[**robinhood**](adapters/deps/robinhood/) \
  Your Robinhood account as dated files (positions, orders, portfolio, watchlists), read through Robinhood's own MCP server, never traded on. \
  Needs mcp (Python SDK); MIT. Goes online: agent.robinhood.com and Robinhood's sign-in, to read your account; this machine, for the sign-in's return. *new*
  `needs-install` `online` `mcp` · near: photos, mcp, pdf

### What runs on your page, a to h

- <a id="again"></a>[**again**](adapters/stdlib/again/) \
  Questions you keep asking: "asked 4 times; approve an answer?" \
  *bot* `no-install` `offline` `counts` · near: export, pile-gold, history
- <a id="attendance"></a>[**attendance**](adapters/stdlib/attendance/) \
  Attendance for a class, club or group, from your register, by week. \
  Uses habits. *new* `no-install` `offline` `week` · near: gradebook, symptoms, syllabus
- <a id="baby-log"></a>[**baby-log**](adapters/stdlib/baby-log/) \
  Feeds, sleeps and nappies from your notes, by day: when was the last one? \
  Uses habits. *new* `no-install` `offline` `log` · near: milestones, mood, reading-log
- <a id="budget"></a>[**budget**](adapters/stdlib/budget/) \
  Spending against the budget you wrote down, month by month, from your statements. \
  Uses habits. *new* `no-install` `offline` `month` `statements` · near: mood, reading-log, baby-log
- <a id="car"></a>[**car**](adapters/stdlib/car/) \
  Your car's services, repairs and inspection dates, from receipts and notes: what's due, and what it cost. \
  Uses habits. *new* `no-install` `offline` `due` `receipts` · near: home-upkeep, pets, subscriptions
- <a id="coming-up"></a>[**coming-up**](adapters/stdlib/coming-up/) \
  Dates written in your files in the next N days: appointments, renewals, deadlines. \
  *box* `no-install` `offline` `coming` `days` · near: calendar-out, on-this-day, gaps
- <a id="debts"></a>[**debts**](adapters/stdlib/debts/) \
  Who owes whom, from the IOUs in your notes and messages, each cited. \
  Uses amounts. *new* `no-install` `offline` · near: amounts, todo, symptoms
- <a id="digest"></a>[**digest**](adapters/stdlib/digest/) \
  One page of what your folder needs from you: suggestions waiting, approvals gone stale, dates coming up, questions that find nothing. \
  *bot* `no-install` `offline` `waiting` `coming` `everyday` · near: hook-start, renewals, hook-compact
- <a id="foia"></a>[**foia**](adapters/stdlib/foia/) \
  Freedom-of-information requests: what you asked, when, and when the answer is due by law. \
  Uses habits. *new* `no-install` `offline` `due` · near: home-upkeep, subscriptions, mood
- <a id="food-log"></a>[**food-log**](adapters/stdlib/food-log/) \
  What you ate, from your notes, by day. \
  Uses habits, log-kit. *new* `no-install` `offline` `log` · near: log-kit, gaps, sent-log
- <a id="gaps"></a>[**gaps**](adapters/stdlib/gaps/) \
  Where a log you keep stops: the days a daily note, reading or diary skipped, said as gaps, not left out. \
  *new* `no-install` `offline` `gaps` `daily` `journal` · near: folder-card, on-this-day, serve
- <a id="garden"></a>[**garden**](adapters/stdlib/garden/) \
  What you planted, where and when, and how it did, season by season. \
  Uses habits. *new* `no-install` `offline` · near: home-upkeep, pets, mileage
- <a id="gradebook"></a>[**gradebook**](adapters/stdlib/gradebook/) \
  A teacher's gradebook, kept on this machine: each student's marks by assignment, and who is falling behind. \
  Uses habits. *new* `no-install` `offline` `assignments` · near: syllabus, attendance, reading-log
- <a id="habits"></a>[**habits**](adapters/stdlib/habits/) \
  Streaks from the lines you write each day: how many days in a row, and which you missed. \
  *new* `no-install` `offline` · near: pets, renewals, car
- <a id="home-upkeep"></a>[**home-upkeep**](adapters/stdlib/home-upkeep/) \
  Home upkeep: the boiler service, the filters, the gutters, what's due and when it was last done. \
  Uses car. *new* `no-install` `offline` `due` `service` · near: car, pets, garden

#### What runs on your page, h to w

- <a id="hours"></a>[**hours**](adapters/stdlib/hours/) \
  Hours worked or volunteered, per client or group, from your notes. \
  Uses habits. *new* `no-install` `offline` `group` · near: symptoms, mood, home-upkeep
- <a id="job-hunt"></a>[**job-hunt**](adapters/stdlib/job-hunt/) \
  Applications sent, replies and interviews, by date: who you're still waiting on. \
  Uses habits. *new* `no-install` `offline` · near: mood, warranties, foia
- <a id="lending"></a>[**lending**](adapters/stdlib/lending/) \
  Things you lent, to whom and when, and which are still out. \
  *new* `no-install` `offline` · near: on-this-day, xref, licenses
- <a id="lesson-time"></a>[**lesson-time**](adapters/stdlib/lesson-time/) \
  Lesson plans whose timed parts don't add up to the time the plan says it takes, each part's minutes shown beside the total. \
  *new* `no-install` `offline` `lesson` `plan` `teaching` · near: test-impact, make-it-so, my-lessons
- <a id="livestock"></a>[**livestock**](adapters/stdlib/livestock/) \
  Each animal's births, treatments and sales, from your farm records. \
  Uses habits. *new* `no-install` `offline` `paths` · near: calendar-out, hook-impact, habits
- <a id="mileage"></a>[**mileage**](adapters/stdlib/mileage/) \
  Miles driven for work, from your trips and notes, totalled for a tax year. \
  Uses habits. *new* `no-install` `offline` `tax` `work` · near: garden, home-upkeep, subscriptions
- <a id="minutes"></a>[**minutes**](adapters/stdlib/minutes/) \
  Meeting minutes: who decided what and when, and which actions are still open. \
  Uses habits. *new* `no-install` `offline` `minutes` `due` · near: syllabus, foia, symptoms
- <a id="mood"></a>[**mood**](adapters/stdlib/mood/) \
  Mood scores you write in a journal, over weeks and months. \
  Uses habits, log-kit. *new* `no-install` `offline` `week` · near: job-hunt, symptoms, foia
- <a id="pets"></a>[**pets**](adapters/stdlib/pets/) \
  Each pet's vet visits, vaccines and medicines, from your records: what's due next. \
  Uses car. *new* `no-install` `offline` `due` · near: home-upkeep, car, garden
- <a id="reading-log"></a>[**reading-log**](adapters/stdlib/reading-log/) \
  A child's reading log: books, pages and minutes, week by week. \
  Uses habits. *new* `no-install` `offline` `week` `minutes` · near: foia, baby-log, attendance
- <a id="renewals"></a>[**renewals**](adapters/stdlib/renewals/) \
  Passports, licences, insurance and memberships: when each expires, from your documents. \
  *new* `no-install` `offline` · near: warranties, symptoms, attendance
- <a id="subscriptions"></a>[**subscriptions**](adapters/stdlib/subscriptions/) \
  What you pay for every month, found in bank statements and emails, and when each renews. \
  Uses habits. *new* `no-install` `offline` `month` `statements` · near: foia, pets, home-upkeep
- <a id="syllabus"></a>[**syllabus**](adapters/stdlib/syllabus/) \
  A course syllabus as dates: readings, assignments and exams due, each cited. \
  Uses habits. *new* `no-install` `offline` `assignments` `due` · near: gradebook, minutes, symptoms
- <a id="todo"></a>[**todo**](adapters/stdlib/todo/) \
  TODO, FIXME and "need to" lines across the folder, oldest first. \
  *box* `no-install` `offline` · near: debts, budget, sort
- <a id="warranties"></a>[**warranties**](adapters/stdlib/warranties/) \
  Receipts and warranties: when the dishwasher's cover ends, and where its receipt is. \
  Uses car. *new* `no-install` `offline` `receipts` · near: job-hunt, renewals, baby-log

#### What runs on your page: ideas, not built yet

- <a id="ask-later"></a>**ask-later** (idea) \
  A question with no answer yet kept on a list, and asked again whenever a new file arrives. \
  *new* `no-install` `offline` · near: pile-gold, flashcards, digest
- <a id="care"></a>**care** (idea) \
  For caregivers: medications, vitals and appointments from a care log, what's due and what moved. \
  *box* `no-install` `offline` `due` `car` · near: car, coming-up, bluesky
- <a id="contracts"></a>**contracts** (idea) \
  The dates that matter in your contracts: renewals, notice periods and break clauses, each cited. \
  *new* `no-install` `offline` `break` `contracts` · near: clauses, mutants, support-plan
- <a id="cycle"></a>**cycle** (idea) \
  A menstrual cycle log that never leaves this machine: dates, what's next, and what changed. \
  *new* `no-install` `offline` `log` · near: coming-up, silence-log, sent-log
- <a id="gifts"></a>**gifts** (idea) \
  Gifts given and received, and who likes what, so nobody gets the same scarf twice. \
  *new* `no-install` `offline` `twice` · near: repro, hook-replay, opentimestamps
- <a id="grant-report"></a>**grant-report** (idea) \
  For charities and groups: what you promised a funder and what you did, side by side, each cited. \
  *new* `no-install` `offline` · near: second-opinion, contradictions, standards
- <a id="inventory"></a>**inventory** (idea) \
  What you own, where it is, and where its papers are, for insurance or a will. \
  *new* `no-install` `offline` `paper` `insurance` · near: renewals, paper-key, past-papers
- <a id="lab-notebook"></a>**lab-notebook** (idea) \
  A lab notebook's dated entries, by sample and experiment: what was done to what, and when. \
  *new* `no-install` `offline` `entry` `sampling` · near: joplin, mcp-sampling, journiv
- <a id="rubric"></a>**rubric** (idea) \
  Marking against a rubric you wrote: each mark cites the criterion and the line of work it's for. \
  *new* `no-install` `offline` `mark` `citing` · near: model-exam, gradebook, symptoms
- <a id="school"></a>**school** (idea) \
  School letters and emails for parents: trips, forms due, term dates, and what to bring. \
  *new* `no-install` `offline` `trips` `parent` · near: trips, month-first, support-plan
- <a id="support-plan"></a>**support-plan** (idea) \
  An IEP or support plan's goals, accommodations and review dates, each cited, for a parent or teacher. \
  *new* `no-install` `offline` `parent` `plan` · near: contracts, lessons, standards
- <a id="tax-year"></a>**tax-year** (idea) \
  One tax year's receipts and statements gathered in one place, each with the file it came from. \
  *new* `no-install` `offline` `tax` `year` · near: mileage, todays-place, upstream-desk
- <a id="trips"></a>**trips** (idea) \
  Your trips from booking emails and tickets: where you went, when, and where you stayed. \
  *new* `no-install` `offline` `trips` `emails` · near: school, mileage, books

### What it makes for elsewhere

- <a id="policy-watch"></a>[**policy-watch**](adapters/stdlib/policy-watch/) \
  A terms or policy page fetched each time you run it, by snapshot, and what changed since last time, sentence by sentence, by clauses. \
  Uses clauses, snapshot. Goes online: the page you name, fetched each time you run it. *new* `no-install` `online` `snapshot` `clauses` `policies` · near:
  snapshot, clauses, wayback

### Tools you run yourself

- <a id="flashcards"></a>[**flashcards**](adapters/stdlib/flashcards/) \
  Approved question-and-answer pairs become cards, scheduled by spaced repetition. \
  *box* `no-install` `offline` · near: jeles, ask-later, hook-compact
- <a id="forecasts"></a>[**forecasts**](adapters/stdlib/forecasts/) \
  Write a prediction before the outcome, settle it later with your seal, see your Brier score. \
  *bot* `no-install` `offline` `brier` `forecast` · near: market-calls, predict, weather-bet
- <a id="handover"></a>[**handover**](adapters/stdlib/handover/) \
  Where one project stands, to hand on: what waits on you, what each stack's last run said step by step, and where each line can be checked. \
  Uses projects, stack. *new* `no-install` `offline` `stack` `step` · near: stack-share, stack, red-on-main
- <a id="invoices"></a>[**invoices**](adapters/stdlib/invoices/) \
  For freelancers: invoices and payments matched by the id pattern you give, never guessed. \
  Uses amounts, bank. *new* `no-install` `offline` `numbers` · near: serve, share, privacy
- <a id="log-kit"></a>[**log-kit**](adapters/stdlib/log-kit/) \
  The engine the logs share: your notes' dated lines read by a short spec of words, numbers and a period, so a new log is a spec, not code. \
  Uses habits. *new* `no-install` `offline` `log` `share` · near: food-log, logs, on-this-day
- <a id="market-calls"></a>[**market-calls**](adapters/stdlib/market-calls/) \
  Market calls kept as wagers on the record ('SPY closes up on Friday'), settled later by your seal, with the losers kept. \
  Uses forecasts. *bot* `no-install` `offline` `settle` `calls` · near: forecasts, predict, car
- <a id="milestones"></a>[**milestones**](adapters/stdlib/milestones/) \
  Your child's firsts, words and heights, from your notes, by age. \
  Uses habits. *new* `no-install` `offline` `child` · near: baby-log, syllabus, reading-log
- <a id="nightstand"></a>[**nightstand**](adapters/stdlib/nightstand/) \
  Set heavy things down at night and pick up just one small next step in the morning: at most one thing in hand, and nothing ever deleted. \
  *new* `no-install` `offline` `step` · near: start, all, game-master
- <a id="predict"></a>[**predict**](adapters/stdlib/predict/) \
  Write down what a question will come to before you ask it, and grade it after; the record counts how often it was right. \
  *bot* `no-install` `offline` `score` `down` · near: forecasts, pile-gold, assistant-scores
- <a id="projects"></a>[**projects**](adapters/stdlib/projects/) \
  Every project under one folder: its records, its stacks, and each stack's runs, so you can see what there is to go back to. \
  Uses stack. *new* `no-install` `offline` `stack` · near: stack-share, stack, browse
- <a id="readings"></a>[**readings**](adapters/stdlib/readings/) \
  Two hints beside an answer: a number in your files that moved a lot lately, and a date in a log that passed with nothing written since. \
  *box* `no-install` `offline` `numbers` · near: plain, privacy, coming-up
- <a id="session-cost"></a>[**session-cost**](adapters/stdlib/session-cost/) \
  Tokens each agent session spent, by day and by repo, summed from its own session files and priced from a table you keep. \
  *new* `no-install` `offline` `agent` `session` · near: agent-transcript, corpus-lens, csv-rows
- <a id="symptoms"></a>[**symptoms**](adapters/stdlib/symptoms/) \
  A symptom diary over time, ready to show a doctor: what, when, how bad, each line cited. \
  *new* `no-install` `offline` · near: syllabus, hours, minutes

#### Tools you run yourself: ideas, not built yet

- <a id="crowd"></a>**crowd** (idea) \
  You against the crowd: a prediction market's question copied into your ledger, your probability beside theirs, both scored. \
  Goes online: the market's public API, to read the question and its resolution. *new* `no-install` `online` `prediction` `score` · near: predictions,
  oakenscroll, market-calls
- <a id="mirror-sweep"></a>**mirror-sweep** (idea) \
  When a file is deleted, the copies of it that readers made are found and removed, so your folder stops answering from what is gone. \
  *new* `no-install` `offline` `reader` `sweep` · near: pile-sweep, format-rot, changed
- <a id="upstream-desk"></a>**upstream-desk** (idea) \
  Your work in other people's projects, in one place: notifications sorted into what needs you, and your open pull requests there. \
  Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `pull` `request` · near: contribute, against, restack-open

## Trust and proof

### What runs on your page

- <a id="box-health"></a>[**box-health**](adapters/stdlib/box-health/) \
  Is your willow all right? One line: files it can't read, readers out of date, and when its record was last checked. \
  *new* `no-install` `offline` `rows` · near: tip-pin, changed, pipe
- <a id="changed"></a>[**changed**](adapters/stdlib/changed/) \
  What's new, edited or deleted in your folder since the last check, as fingerprint rows. \
  *bot* `no-install` `offline` `edit` `rows` `everyday` · near: box-health, policy-watch, stale
- <a id="contradictions"></a>[**contradictions**](adapters/stdlib/contradictions/) \
  Two passages that disagree about the same date or amount, side by side. \
  *new* `no-install` `offline` `amount` · near: duplicates, joins, amounts
- <a id="export"></a>[**export**](adapters/stdlib/export/) \
  Approved answers, and the question log (counts only, never words), as Markdown or CSV. \
  *box* `no-install` `offline` `counts` · near: again, history, pgp
- <a id="fixity"></a>[**fixity**](adapters/stdlib/fixity/) \
  Your folder's files hashed again now and then, the hashes kept on the record, and a file that changed with no edit of yours flagged as rot. \
  *new* `no-install` `offline` `rot` `flagged` · near: hook-replay, hook-pin, changed
- <a id="history"></a>[**history**](adapters/stdlib/history/) \
  Your record in plain sentences: what was asked when, what found nothing, what you approved; places and counts, never the words. \
  *new* `no-install` `offline` `counts` `sentence` `everyday` · near: again, export, plain
- <a id="ids"></a>[**ids**](adapters/stdlib/ids/) \
  Every file and passage given its Software Heritage ID and IPFS CID, names the rest of the world already uses. \
  *new* `no-install` `offline` `world` `ids` · near: dialect, a11y-check, sort-ask
- <a id="licenses"></a>[**licenses**](adapters/stdlib/licenses/) \
  The licence of every installed dependency, read from its own metadata on this machine: which are copyleft, and which file says so. \
  *new* `no-install` `offline` `dependency` · near: lending, on-this-day, pins
- <a id="pair-drift"></a>[**pair-drift**](adapters/stdlib/pair-drift/) \
  Figures a summary says that its full text doesn't: a draft and its packet side by side, ranges and billions read as written. \
  *new* `no-install` `offline` `ranges` `pairs` `writing` · near: contradictions, pins, pile-poetry
- <a id="stale"></a>[**stale**](adapters/stdlib/stale/) \
  Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact. \
  *box* `no-install` `offline` · near: again, export, weakest-link
- <a id="weakest-link"></a>[**weakest-link**](adapters/stdlib/weakest-link/) \
  Each answer's inputs marked measured, fitted or assumed, and the result worth its weakest input, never an average. \
  *new* `no-install` `offline` `links` · near: stale, export, jetbrains
- <a id="xref"></a>[**xref**](adapters/stdlib/xref/) \
  Every reference in your files checked: each link to another file, and each quoted line, still there and still saying it. \
  *bot* `no-install` `offline` `quote` `everyday` · near: quote-review, secrets-audit, quotes

### Checking a model before you trust it

- <a id="say-check"></a>[**say-check**](adapters/stdlib/say-check/) \
  A sentence said about your boxes, checked by code: each cite served, each box cited, no word or number the boxes lack, your words exact. \
  From: code of [willow-memory/willows-grove](https://github.com/willow-memory/willows-grove), Apache-2.0. *new* `no-install` `offline` `sentence` · near:
  plain, on-this-day, code-comments

#### Checking a model before you trust it: ideas, not built yet

- <a id="join-check"></a>**join-check** (idea) \
  A connection a model made between two passages, held to your files: each thing it says looked for, and the passage that backs it shown. \
  Uses claim-check, connect. *new* `no-install` `offline` `join` `between` · near: joins, clauses, contradictions

### What guards it


#### What guards it: ideas, not built yet

- <a id="sap-gate"></a>**sap-gate** (idea) \
  The mcp add-on's tool calls checked against SAP/1.0 grants before they run, through openclaw-sap-gate. \
  Needs openclaw-sap-gate; MIT. *new* `needs-install` `offline` `mcp` `tool` · near: mcp-lite, cursor, opencode

### What it makes for elsewhere

- <a id="backup"></a>[**backup**](adapters/stdlib/backup/) \
  Your record in one zip, every byte and the chain checked before it's kept; never beside your key, and it never reads the key. \
  *new* `no-install` `offline` `chain` `backup` `everyday` · near: diverge, three-two-one, restore-drill
- <a id="in-toto"></a>[**in-toto**](adapters/stdlib/in-toto/) \
  A sealed answer exported as an in-toto Statement, the envelope SLSA uses, so others can check it. \
  *new* `no-install` `offline` `envelope` `tool` · near: ro-crate, annotations, prov
- <a id="jeles"></a>[**jeles**](adapters/stdlib/jeles/) \
  Your approved answers as Jeles nuggets (question, answer, sources, who sealed it), and Jeles' own verified nuggets read back as passages. \
  *new* `no-install` `offline` `sources` · near: oakenscroll, pile-gold, almanac
- <a id="merkle"></a>[**merkle**](adapters/stdlib/merkle/) \
  A Merkle tree over the record, so one row can be proven with a handful of hashes, not the whole file. \
  *new* `no-install` `offline` `hash` `rows` · near: hook-replay, ci, claim-check
- <a id="nestor"></a>[**nestor**](adapters/stdlib/nestor/) \
  Answers Nestor records a person has checked, read from a copy of its SQLite store, each citing who checked it and when. \
  *new* `no-install` `offline` `sqlite` `copy` · near: bookmarks, codebase-memory, zotero
- <a id="pgp"></a>[**pgp**](adapters/deps/pgp/) \
  Signs exports and reports with your PGP key, verifiable anywhere. \
  Needs the gpg program, run not linked, and python-gnupg; GPL, BSD-3-Clause. *new* `needs-install` `offline` · near: pdf, mcp, static-search
- <a id="prov"></a>[**prov**](adapters/stdlib/prov/) \
  The record exported as W3C PROV: what came from what, by which step, sealed by whom. \
  *new* `no-install` `offline` `prov` `tool` · near: cloudevents, annotations, in-toto
- <a id="ro-crate"></a>[**ro-crate**](adapters/stdlib/ro-crate/) \
  Your willow (the files it reads, its record, your approved answers) as an RO-Crate research object that Zenodo and other archives can read. \
  *new* `no-install` `offline` `tool` · near: in-toto, annotations, cloudevents
- <a id="timeline"></a>[**timeline**](adapters/stdlib/timeline/) \
  A dated timeline of one matter (a dispute, an illness, a tenancy), every line cited, to hand to a lawyer, doctor or council. \
  *new* `no-install` `offline` `timeline` · near: said, across, first-mention
- <a id="tip-pin"></a>[**tip-pin**](adapters/stdlib/tip-pin/) \
  Where your record ends, written somewhere willow can't reach, so rows cut off the end or rewritten are caught where verify can't. \
  *new* `no-install` `offline` `pin` `rows` · near: ci-memo, box-health, ci
- <a id="wayback"></a>[**wayback**](adapters/stdlib/wayback/) \
  The Wayback Machine's copy of a page from a window of days, saved beside your own snapshot and compared with it byte for byte. \
  Uses snapshot. Goes online: archive.org, to find the archived copy and fetch it. *new* `no-install` `online` `snapshot` `saved` `sources` · near: snapshot,
  policy-watch, archivebox

#### What it makes for elsewhere: ideas, not built yet

- <a id="git-notes"></a>**git-notes** (idea) \
  Approved answers kept as git notes on the commits they cite, so they travel with the repo to any forge. \
  Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `commit` `forge` · near: mirror, stale, annotations
- <a id="in-case"></a>**in-case** (idea) \
  A letter for the people you trust, if something happens to you: where things are and who to call, from your files, sealed by you. \
  *new* `no-install` `offline` `people` `trust` · near: witness, people, nicknames
- <a id="paper-key"></a>**paper-key** (idea) \
  Your key printed as words on paper, to keep somewhere safe, and typed back in to restore it. \
  *new* `no-install` `offline` `prints` `key` · near: notation, print, start
- <a id="report"></a>**report** (idea) \
  A self-checking bundle: the record, the approved answers, and a script that re-verifies them on any machine. \
  *box* `no-install` `offline` `bundle` `verified` · near: datasette, redential, jeles

### Tools you run yourself

- <a id="claim-check"></a>[**claim-check**](adapters/stdlib/claim-check/) \
  A claim checked against your sources: the passages that hold all of its parts, the ones that hold only some, and the parts no file names. \
  *new* `no-install` `offline` `claim` `top` · near: thesis, all, typosquat
- <a id="decisions"></a>[**decisions**](adapters/stdlib/decisions/) \
  A recorded no with its reason and the condition that would reopen it, so a rejection is kept, not forgotten. \
  *new* `no-install` `offline` · near: pile-sweep, predict, again
- <a id="diverge"></a>[**diverge**](adapters/stdlib/diverge/) \
  Where two copies part, your record and its backup zip or two copies of a folder, down to the first row, file and line that differ. \
  *bot* `no-install` `offline` `backup` `zip` `everyday` · near: backup, three-two-one, restore-drill
- <a id="format-rot"></a>[**format-rot**](adapters/stdlib/format-rot/) \
  Files in formats that may stop opening (old office files, proprietary ones, ones no reader handles), flagged while you can convert them. \
  *new* `no-install` `offline` `office` `rot` · near: office, fixity, sheets
- <a id="restore-drill"></a>[**restore-drill**](adapters/stdlib/restore-drill/) \
  A backup zip restored into scratch and verified there, chain and every file, so you know it restores before the day you need it. \
  Uses backup. *new* `no-install` `offline` `backup` `zip` · near: backup, diverge, ci
- <a id="session-seal"></a>[**session-seal**](adapters/stdlib/session-seal/) \
  One seal at the end of a session, over everything asked and approved in it: yes, these were my actions. \
  *bot* `no-install` `offline` `end` · near: rules, abbreviations, tip-pin
- <a id="stack-row"></a>[**stack-row**](adapters/stdlib/stack-row/) \
  A stack's kept run put on your record as one row: which steps ran, how each ended, and the hash of what each printed, never the words. \
  Uses stack. *new* `no-install` `offline` `stack` `step` · near: stack, stack-share, backup
- <a id="thesis"></a>[**thesis**](adapters/stdlib/thesis/) \
  A thesis's claims, each tied to the source that backs it, and a list of the ones with none. \
  Uses claim-check. *new* `no-install` `offline` `claim` `top` · near: claim-check, all, surprise
- <a id="three-two-one"></a>[**three-two-one**](adapters/stdlib/three-two-one/) \
  How many verified copies of your record exist and where, held to three copies, on two kinds of storage, one away from home. \
  Uses backup. *new* `no-install` `offline` `zip` `copy` · near: diverge, backup, duplicates
- <a id="weights-pin"></a>[**weights-pin**](adapters/stdlib/weights-pin/) \
  A local model's weights file hashed before each run and refused when it differs from the hash on its model card. \
  Uses weights-card. *new* `no-install` `offline` `local` `weights` · near: weights-card, model-card, model-fit

#### Tools you run yourself: ideas, not built yet, b to m

- <a id="before-copy"></a>**before-copy** (idea) \
  A file beside its dated before-copy (plan.py.pre-2026-09-30, notes.md.bak) side by side: what changed since the copy was made. \
  *new* `no-install` `offline` · near: garden, policy-watch, contradictions
- <a id="chain-check"></a>**chain-check** (idea) \
  A hash-chained JSONL log that isn't willow's own record, checked link by link: where its chain holds, and the first row where it breaks. \
  *new* `no-install` `offline` `rows` `chain` · near: merkle, sync, diverge
- <a id="encrypt"></a>**encrypt** (idea) \
  Keeps the record folder encrypted at rest. \
  Needs cryptography; Apache-2.0 or BSD. From: shape of [willow-memory/willow-data-vault](https://github.com/willow-memory/willow-data-vault), Apache-2.0.
  *new* `needs-install` `offline` `rest` · near: make-it-so, ci-memo, almanac-keep
- <a id="family-box"></a>**family-box** (idea) \
  One box for a household: each person's own seal, and every answer showing whose it is. \
  *new* `no-install` `offline` `person` `family` · near: second-opinion, dialect, family-tree
- <a id="grant"></a>**grant** (idea) \
  Someone else allowed to ask part of your folder: a grant to their key for a path and a time, passed on only narrower, never your seal key. \
  Uses share. From: shape of [willowprotocol.org/specs/meadowcap](https://willowprotocol.org/specs/meadowcap/), none; shape of
  [Deln0r/willow-go](https://github.com/Deln0r/willow-go), MIT. *new* `no-install` `offline` `key` `paths` · near: hook-compact, lesson-time, rules
- <a id="handoff"></a>**handoff** (idea) \
  A box handed to the person you name (an executor, a carer): read only, your seals kept, theirs their own. \
  *new* `no-install` `offline` `person` · near: family-box, serve, datasette
- <a id="line-origin"></a>**line-origin** (idea) \
  Which agent session wrote this line of code: git blame to the commit, then the transcript turn that made it. \
  Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `agent` `git` · near: agent-transcript, session-cost, transcript-redact
- <a id="losc"></a>**losc** (idea) \
  Does a project pass the Local Only Servers Club's test: no accounts, no cloud, and your data your own? \
  *bot* `no-install` `offline` `local` `server` · near: quantized, robinhood, github-archive
- <a id="mirror"></a>**mirror** (idea) \
  Checks each mirror of a repo on another forge holds the same commits as the original, so losing a host loses nothing. \
  Needs the git program; GPL, called not linked. Goes online: each mirror's git URL, to read its refs. *new* `needs-install` `online` `commit` `forge` · near:
  repro, git-notes, provenance
- <a id="model-recall"></a>**model-recall** (idea) \
  Every sealed answer a model suggested, listed for a second look once you mark its card as flawed; nothing is unsealed for you. \
  *new* `no-install` `offline` `suggests` `second` · near: openai-compatible, model-exam, sort-ask

#### Tools you run yourself: ideas, not built yet, n to w

- <a id="notary"></a>**notary** (idea) \
  The record's newest hash timestamped by an outside time server, so anyone can see it existed by then. \
  Goes online: an RFC 3161 time server you choose, sent only the hash. *new* `no-install` `online` `hash` `existed` · near: opentimestamps, persona-card,
  three-two-one
- <a id="opentimestamps"></a>**opentimestamps** (idea) \
  The record's newest hash anchored by OpenTimestamps, proof that it existed by a given block. \
  Goes online: the OpenTimestamps calendars, sent only the hash. *new* `no-install` `online` `hash` `existed` · near: notary, merkle, three-two-one
- <a id="provenance"></a>**provenance** (idea) \
  Checks a package's Sigstore provenance or PyPI attestation names the repo and commit it claims, before you trust it. \
  Needs sigstore; Apache-2.0. Goes online: the registry and Sigstore's log, to fetch the attestation. *new* `needs-install` `online` `trust` `package` · near:
  pypi, in-toto, sync
- <a id="quote-review"></a>**quote-review** (idea) \
  A review comment that quotes the repo, checked: does the quoted line still say that at the pull request's head? \
  Goes online: the forge, through the workflow's token, to read the review comments. *new* `no-install` `online` `pull` `request` · near: github-archive,
  xref, against
- <a id="redential"></a>**redential** (idea) \
  The bundle redential-cli's scan makes, written to the record before you submit it, so what left your machine can be checked later. \
  Needs the redential program, run through npx; Apache-2.0. *new* `needs-install` `offline` `bundle` `left` · near: report, sent-log, tip-pin
- <a id="retire"></a>**retire** (idea) \
  Proposes setting aside approved answers that no longer hold, each one gone only when you seal it. \
  *bot* `no-install` `offline` `aside` · near: assistant-scores, stale, datasette
- <a id="signed-commits"></a>**signed-commits** (idea) \
  Which commits are signed, and by whose key, checked on this machine against the keys you trust. \
  Needs the git program; GPL, called not linked. *new* `needs-install` `offline` `trust` `commit` · near: provenance, pgp, sync
- <a id="sync"></a>**sync** (idea) \
  Your record kept on two devices through any synced folder, with the chain checked on each before it's trusted. \
  *new* `no-install` `offline` `trust` `chain` · near: backup, provenance, model-exam
- <a id="time-capsule"></a>**time-capsule** (idea) \
  A note sealed now and opened on a date you choose, with the record proving it wasn't changed. \
  *new* `no-install` `offline` `prov` `open` · near: prov, hook-compact, fixity
- <a id="witness"></a>**witness** (idea) \
  A second person's seal beside yours, for answers that need two people to agree. \
  *new* `no-install` `offline` `beside` `second` · near: second-opinion, translate, model-recall

## Privacy and safety

### What runs on your page

- <a id="a11y-check"></a>[**a11y-check**](adapters/stdlib/a11y-check/) \
  Your documents checked for screen-reader problems: images without descriptions, headings out of order. \
  *new* `no-install` `offline` `problems` `screen` · near: skim, digest, scrub
- <a id="advisories"></a>[**advisories**](adapters/stdlib/advisories/) \
  Security advisories from a downloaded OSV or GitHub database, matched to your lockfiles: which dependency each names, and since when. \
  *new* `no-install` `offline` `dependency` `lock` · near: typosquat, outdated, risky-code
- <a id="install-scripts"></a>[**install-scripts**](adapters/stdlib/install-scripts/) \
  The install scripts the packages in node_modules would run (preinstall, install, postinstall), each cited by file and line. \
  *new* `no-install` `offline` `package` `install` · near: package-contents, package-docs, aider
- <a id="outdated"></a>[**outdated**](adapters/stdlib/outdated/) \
  How old each locked dependency is, and which are yanked, deprecated or two years without a release, from a registry index you downloaded. \
  Uses advisories. *new* `no-install` `offline` `dependency` · near: typosquat, pins, jrnl
- <a id="package-contents"></a>[**package-contents**](adapters/stdlib/package-contents/) \
  What's inside a wheel, sdist, npm tarball or .crate before you install it: every file, and any code it runs on install. \
  *new* `no-install` `offline` `install` `npm` · near: install-scripts, ci-cache, instruction-files
- <a id="pii-audit"></a>[**pii-audit**](adapters/stdlib/pii-audit/) \
  Personal data sitting in your files (ID numbers, health details, card numbers), listed by file and line. \
  *new* `no-install` `offline` `numbers` `audit` · near: secrets-audit, privacy, sort
- <a id="risky-code"></a>[**risky-code**](adapters/stdlib/risky-code/) \
  Code lines matching a known-dangerous pattern (command injection, eval, SQL concatenation, broken TLS and more), by file and line, as leads. \
  *new* `no-install` `offline` `matched` `command` `security` · near: code-shape, install-scripts, sort
- <a id="secrets-audit"></a>[**secrets-audit**](adapters/stdlib/secrets-audit/) \
  Finds passwords, keys and card numbers sitting in plain files, by file and line, never showing the value. \
  Uses privacy. *bot* `no-install` `offline` `numbers` `key` `everyday` · near: pii-audit, hook-leaks, xref
- <a id="sent-log"></a>[**sent-log**](adapters/stdlib/sent-log/) \
  Which of your passages went to which online model, read from the record by model card: what left this machine and where to. \
  Uses openai-compatible. *new* `no-install` `offline` `left` `log` · near: gaps, model-card, redential
- <a id="typosquat"></a>[**typosquat**](adapters/stdlib/typosquat/) \
  Dependency names a letter off from a popular one (reqeusts, lodahs), checked against a list of top packages you downloaded. \
  Uses advisories. *new* `no-install` `offline` `dependency` `package` · near: outdated, advisories, claim-check

### What guards it

- <a id="privacy"></a>[**privacy**](adapters/stdlib/privacy/) \
  Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid. \
  *bot* `no-install` `offline` `numbers` · near: plain, readings, pii-audit

### What it makes for elsewhere

- <a id="scrub"></a>[**scrub**](adapters/stdlib/scrub/) \
  Strips the hidden details (EXIF, author, edit history) from a file before you share it. \
  *new* `no-install` `offline` `history` `share` · near: photos, transcript-redact, bookmarks
- <a id="transcript-redact"></a>[**transcript-redact**](adapters/stdlib/transcript-redact/) \
  An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line. \
  Uses privacy. *new* `no-install` `offline` `agent` `transcript` · near: scrub, agent-transcript, agents-md-check

### Tools you run yourself

- <a id="dp"></a>[**dp**](adapters/deps/dp/) \
  A count of yours, noised by OpenDP before you seal and send it, so your one number doesn't say what your folder holds. \
  Needs opendp; MIT. Uses kart, share. *new* `needs-install` `offline` · near: kart, pdf, fast-tests
- <a id="secure-sum"></a>[**secure-sum**](adapters/deps/secure-sum/) \
  A total of everyone's counts, by Shamir's secret sharing: the one who asked learns the sum, and no one's own count is in any package. \
  Needs shamirs; MIT. Uses kart, share. *new* `needs-install` `offline` `share` · near: share, kart, pdf

#### Tools you run yourself: ideas, not built yet

- <a id="forget"></a>**forget** (idea) \
  Stops a file being searched, recorded on the chain, so what was taken out is known and nothing else is touched. \
  *new* `no-install` `offline` `known` `stop` · near: ro-crate, merkle, transcript-redact
- <a id="kids"></a>**kids** (idea) \
  A box for a child: answers only from the folder you choose for them, and nothing they can approve. \
  *new* `no-install` `offline` · near: student-records, export, browse
- <a id="student-records"></a>**student-records** (idea) \
  A box of student records that answers only the teacher who owns it, and logs every look. \
  *new* `no-install` `offline` `student` `log` · near: kids, ci-why, export

## Assistants

Each hands in suggestions through propose. None can approve: every suggestion waits for your seal. Two ways in: MCP tools the host calls when it asks
([hosts](adapters/stdlib/hosts/), [mcp-lite](adapters/stdlib/mcp-lite/)), and a prompt hook that cites your passages at each prompt where the host allows it
([claude-code](adapters/stdlib/claude-code/); [hooks-elsewhere](adapters/stdlib/hooks-elsewhere/) for the rest).

### What runs on your page

- <a id="instruction-files"></a>[**instruction-files**](adapters/stdlib/instruction-files/) \
  For a folder, which instruction files each coding agent loads (AGENTS.md, CLAUDE.md, GEMINI.md, rules), in what order, with size and hash. \
  *box* `no-install` `offline` `gemini` `claude` · near: agent-transcript, agents-md-check, hook-read-first

### Models that suggest answers

- <a id="in-process"></a>[**in-process**](adapters/deps/in-process/) \
  Suggestions from a GGUF model loaded inside the add-on itself through llama-cpp-python: no server, no port, nothing listening. \
  Needs llama-cpp-python; MIT; licence of the model varies. Uses openai-compatible. *new* `needs-install` `offline` `cpp` `llama` · near: openai-compatible,
  llm-cli, night-batch
- <a id="llm-cli"></a>[**llm-cli**](adapters/deps/llm-cli/) \
  Suggestions through the llm command, so any model its plugins reach (local or hosted) can hand one in, with llm's own log naming the model. \
  Needs llm and the plugin for your model; Apache-2.0. Uses openai-compatible. Goes online: the model its plugin reaches, to ask for suggestions. Hands on
  your question and the passages served, to the llm command and the model it runs. *new* `needs-install` `online` `local` `openai` · near: in-process,
  openai-compatible, night-batch
- <a id="local-model"></a>[**local-model**](adapters/stdlib/local-model/) \
  Suggestions from a model on this machine only, such as Ollama, llama.cpp's server, llamafile, KoboldCpp or Jan. \
  Uses openai-compatible. Reaches this machine only. *new* `no-install` `this-machine` `cpp` `jan` · near: openai-compatible, in-process, model-shelf
- <a id="mcp-sampling"></a>[**mcp-sampling**](adapters/stdlib/mcp-sampling/) \
  Suggestions from whatever model your MCP client already runs, asked through MCP sampling, so willow needs no model or key of its own. \
  Uses openai-compatible. Hands on your question and the passages served, to the model your MCP client runs. *new* `no-install` `to-a-model` `mcp` `client` ·
  near: cursor, opencode, windsurf
- <a id="night-batch"></a>[**night-batch**](adapters/stdlib/night-batch/) \
  Questions waiting for suggestions batched into one local-model run overnight, stopped the moment you're back. \
  Uses local-model. Reaches this machine only. *new* `no-install` `this-machine` `local` · near: llm-cli, in-process, openai-compatible
- <a id="openai-compatible"></a>[**openai-compatible**](adapters/stdlib/openai-compatible/) \
  Suggestions from any OpenAI-compatible endpoint you choose (LM Studio, vLLM, LocalAI, OpenRouter, Groq, Mistral...), citing your passages. \
  Goes online: the endpoint you configure, to ask for suggestions. *new* `no-install` `online` `cpp` `llama` · near: in-process, llm-cli, local-model
- <a id="translate"></a>[**translate**](adapters/stdlib/translate/) \
  An answer translated by a local model, the original kept beside it, the translation held until you seal it. \
  Uses local-model, openai-compatible. Reaches this machine only. *new* `no-install` `this-machine` `local` `held` · near: night-batch, in-process, llm-cli

#### Models that suggest answers: ideas, not built yet

- <a id="basic-memory"></a>**basic-memory** (idea) \
  Basic Memory's Markdown notes where an AI wrote them: each observation and relation handed in through propose, waiting for your seal. \
  *new* `no-install` `offline` `handed` `propose` · near: memory-import, hermes, hook-feedback
- <a id="bedrock"></a>**bedrock** (idea) \
  Suggestions from a model on Amazon Bedrock, under your own AWS account and region, citing your passages. \
  Needs boto3; Apache-2.0. Goes online: Amazon Bedrock's endpoint in your region, to ask for suggestions. *new* `needs-install` `online` `citing` · near:
  cite-honesty, claude, sort-ask
- <a id="browser-model"></a>**browser-model** (idea) \
  Suggestions from a model running in your browser, Chrome's built-in model or one run on WebGPU, through a page served on this machine. \
  Reaches this machine only. *new* `no-install` `this-machine` `browser` · near: mlx, night-batch, os-model
- <a id="claude"></a>**claude** (idea) \
  Suggestions from Claude through the Anthropic API, citing your passages. \
  Needs anthropic; MIT. Goes online: api.anthropic.com, to ask for suggestions. *new* `needs-install` `online` `citing` `claude` · near: claude-code,
  cite-honesty, bedrock
- <a id="hermes"></a>**hermes** (idea) \
  Hermes Agent asking your folder as a plugin, and its memories, and what its dreaming plugin consolidates, handed in through propose. \
  *new* `no-install` `offline` `handed` `propose` · near: basic-memory, memory-import, hook-feedback
- <a id="memory-import"></a>**memory-import** (idea) \
  An AI assistant's memory store, SQLite or Markdown, handed in through propose: one suggestion per memory, none trusted until you seal it. \
  *new* `no-install` `offline` `handed` `propose` · near: basic-memory, hermes, hook-feedback
- <a id="mlx"></a>**mlx** (idea) \
  Suggestions from a model run on Apple silicon through MLX, on this Mac alone. \
  Needs mlx-lm, on Apple silicon only; MIT; licence of the model varies. *new* `needs-install` `offline` `apple` `silicon` · near: browser-model, os-model,
  model-fit
- <a id="os-model"></a>**os-model** (idea) \
  Suggestions from the model built into the operating system, such as Apple's Foundation Models: nothing to download, nothing leaving it. \
  Needs macOS 26 with Apple Intelligence on, and a small Swift helper; Apple's terms. *new* `needs-install` `offline` `apple` `download` · near: mlx,
  browser-model, local-model
- <a id="plain-language"></a>**plain-language** (idea) \
  An approved answer rewritten in plain language by a model, the rewrite held until you seal it. \
  *new* `no-install` `offline` `held` · near: translate, hook-tiers, memory-import
- <a id="second-opinion"></a>**second-opinion** (idea) \
  Two assistants' suggestions for the same question side by side, each waiting for its own seal. \
  *new* `no-install` `offline` `assistant` `waiting` · near: assistant-scores, contradictions, pile-poetry

### Checking a model before you trust it

- <a id="assistant-scores"></a>[**assistant-scores**](adapters/stdlib/assistant-scores/) \
  How often each assistant's suggestions were sealed or set aside, from the record. \
  Uses openai-compatible. *new* `no-install` `offline` `aside` `score` · near: retire, predict, forecasts
- <a id="connect"></a>[**connect**](adapters/stdlib/connect/) \
  What a model on this machine says connects two passages of yours, in a few sentences, each number and name it gives checked against them. \
  Uses say. Reaches this machine only. *new* `no-install` `this-machine` `sentence` · near: contradictions, duplicates, claim-check
- <a id="model-card"></a>[**model-card**](adapters/stdlib/model-card/) \
  A card naming the model behind an assistant (version or weights hash, where it runs, licence, limits), on the record for each suggestion. \
  Uses weights-card. *new* `no-install` `offline` `hash` `weights` · near: weights-card, local-model, weights-pin
- <a id="model-drift"></a>[**model-drift**](adapters/stdlib/model-drift/) \
  Your frozen questions asked again of a model now and then, flagging when its answers change while its name and card stay the same. \
  Uses openai-compatible. Goes online: the endpoint you configure, to ask your questions again. *new* `no-install` `online` · near: same-way, model-card,
  model-exam
- <a id="model-exam"></a>[**model-exam**](adapters/stdlib/model-exam/) \
  Any model scored against the answers you sealed, your own questions as its exam, before you trust its suggestions. \
  Uses openai-compatible. Goes online: the endpoint you configure, to ask your sealed questions. *new* `no-install` `online` `score` · near: same-way,
  model-drift, night-batch
- <a id="model-fit"></a>[**model-fit**](adapters/stdlib/model-fit/) \
  Whether this machine's GPU, NPU or Apple silicon can run a local model, and about how fast, before you download one. \
  *new* `no-install` `offline` `local` `weights` · near: model-shelf, weights-card, quantized
- <a id="model-shelf"></a>[**model-shelf**](adapters/stdlib/model-shelf/) \
  Every model already on this machine (Ollama, LM Studio, Jan, GPT4All, the Hugging Face cache): its runtime, size, quantization and hash. \
  Uses weights-card. *new* `no-install` `offline` `jan` `ollama` · near: quantized, weights-card, model-fit
- <a id="quantized"></a>[**quantized**](adapters/stdlib/quantized/) \
  Finds the smallest quantized local model that still gets your box's own questions right, so suggestions come faster. \
  Uses local-model, model-exam. Reaches this machine only. *new* `no-install` `this-machine` `local` · near: model-shelf, model-fit, model-exam
- <a id="same-way"></a>[**same-way**](adapters/stdlib/same-way/) \
  A local model asked each of your box's questions three times, and how often its answer flips: one that answers the same way can be built on. \
  Uses openai-compatible. Reaches this machine only. *new* `no-install` `this-machine` `local` · near: model-exam, model-drift, night-batch
- <a id="say"></a>[**say**](adapters/stdlib/say/) \
  One sentence a model on this machine says about your boxes, struck and left to code when it adds a word or number they lack. \
  Uses say-check. Reaches this machine only. From: code of [willow-memory/willows-grove](https://github.com/willow-memory/willows-grove), Apache-2.0. *new*
  `no-install` `this-machine` `sentence` `left` · near: on-this-day, hooks-elsewhere, clauses
- <a id="weights-card"></a>[**weights-card**](adapters/stdlib/weights-card/) \
  A model card filled in from the weights file's own GGUF or safetensors header: architecture, quantization, context length, licence. \
  *new* `no-install` `offline` `weights` `quantization` · near: model-shelf, weights-pin, model-card

#### Checking a model before you trust it: ideas, not built yet

- <a id="cassettes"></a>**cassettes** (idea) \
  Each exchange with a model kept as a row (what was asked and came back, the model, its seed), replayed later as a test, drift found by diff. \
  *bot* `no-install` `offline` `rows` `drift` · near: hook-replay, lending, model-drift
- <a id="cite-honesty"></a>**cite-honesty** (idea) \
  How often each model's suggestions were refused at propose for citing a passage the last bite never returned, read from the record. \
  *new* `no-install` `offline` `citing` `refuses` · near: hook-cite, assistant-scores, sent-log
- <a id="ladder"></a>**ladder** (idea) \
  Your files first, then sources you trust such as Jeles and Nestor, then a model, stopping at the first that answers, kept for next time. \
  *bot* `no-install` `offline` `jeles` `nestor` · near: jeles, first-mention, hook-handoff
- <a id="pool-fit"></a>**pool-fit** (idea) \
  How many passages a model on this machine can be handed at once, measured on your own questions, before its answers add what they lack. \
  Reaches this machine only. *new* `no-install` `this-machine` `fit` · near: model-exam, model-fit, in-process
- <a id="schema-check"></a>**schema-check** (idea) \
  A model's answer held to a JSON schema before anything reads it, and a reply that doesn't fit recorded as a result, not lost as an error. \
  *box* `no-install` `offline` `result` `fit` · near: weights-pin, model-fit, connect-four
- <a id="silence-log"></a>**silence-log** (idea) \
  A model that ran and said nothing kept as its own row, so silence is told apart from a model that never ran. \
  *bot* `no-install` `offline` `log` `rows` · near: said, cassettes, csv-rows

### In your editor

- <a id="copilot"></a>[**copilot**](adapters/stdlib/copilot/) \
  GitHub Copilot, in VS Code and in its own CLI, asks your folder through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` `cli` · near: codex-cli, cursor, opencode
- <a id="cursor"></a>[**cursor**](adapters/stdlib/cursor/) \
  Cursor asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` · near: opencode, windsurf, zed
- <a id="windsurf"></a>[**windsurf**](adapters/stdlib/windsurf/) \
  Windsurf asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` · near: cursor, opencode, zed
- <a id="zed"></a>[**zed**](adapters/stdlib/zed/) \
  Zed's assistant asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` · near: cursor, opencode, windsurf

### With an AI assistant

- <a id="aider"></a>[**aider**](adapters/stdlib/aider/) \
  Aider reads answers from your folder with its /run command, file and line included. \
  Uses hosts. *new* `no-install` `offline` · near: launcher, emacs, browse
- <a id="claude-code"></a>[**claude-code**](adapters/stdlib/claude-code/) \
  Claude Code sees cited passages from your folder with each prompt, through its prompt hook. \
  Uses mcp-lite. Hands on the passages served for each prompt, to Claude Code's model. *bot* `no-install` `to-a-model` `hook` `prompt` · near:
  hooks-elsewhere, gemini-cli, hook-impact
- <a id="codex-cli"></a>[**codex-cli**](adapters/stdlib/codex-cli/) \
  OpenAI's Codex CLI asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` `cli` · near: cursor, opencode, windsurf
- <a id="gemini-cli"></a>[**gemini-cli**](adapters/stdlib/gemini-cli/) \
  Google's Gemini CLI asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` `cli` · near: codex-cli, cursor, opencode
- <a id="hosts"></a>[**hosts**](adapters/stdlib/hosts/) \
  One table of the assistants that take an MCP server, printing the lines that register willow with any of them. \
  Uses mcp-lite, pipe. *new* `no-install` `offline` `mcp` `assistant` · near: hooks-elsewhere, gemini-cli, claude-code
- <a id="mcp"></a>[**mcp**](adapters/deps/mcp/) \
  Lets any MCP client, such as an AI assistant or editor, ask your folder and hand in suggestions. \
  Needs mcp; MIT. Hands on the passages served for each ask, and what waits on you, to the MCP client's model. *new* `needs-install` `to-a-model` `mcp`
  `assistant` · near: mcp-lite, zed, cursor
- <a id="mcp-lite"></a>[**mcp-lite**](adapters/stdlib/mcp-lite/) \
  The mcp add-on's three tools with nothing to install: the protocol by hand, standard library only. \
  Hands on the passages served for each ask, and what waits on you, to the MCP client's model. *box* `no-install` `to-a-model` `mcp` · near: mcp, cursor,
  opencode
- <a id="opencode"></a>[**opencode**](adapters/stdlib/opencode/) \
  OpenCode asks your folder and hands in suggestions, through the mcp add-on. \
  Uses hosts. *new* `no-install` `offline` `mcp` · near: cursor, windsurf, zed

### What guards it, h to h

- <a id="hook-compact"></a>[**hook-compact**](adapters/stdlib/hook-compact/) \
  A PreCompact hook that prints what the record holds open (seals waiting, questions unanswered), so it survives the assistant's summary. \
  Uses digest. Hands on the waiting suggestions' text and reasons, to the assistant's model before it summarises. *box* `no-install` `to-a-model` `waiting`
  `open` `hooks` · near: digest, sort-ask, hook-start
- <a id="hook-errors"></a>[**hook-errors**](adapters/stdlib/hook-errors/) \
  Each failed command an assistant runs kept as a row of its hash and exit code, so the third time it fails it's named, not retried blind. \
  *new* `no-install` `offline` `assistant` `fails` `hooks` · near: hook-read-first, hook-feedback, hook-handoff
- <a id="hook-fail-closed"></a>[**hook-fail-closed**](adapters/stdlib/hook-fail-closed/) \
  Wraps any hook so a crash, a timeout or output it can't read blocks the tool, where Claude Code, Gemini CLI, Codex and Cursor let it run. \
  *new* `no-install` `offline` `codex` `gemini` `hooks` · near: hook-fuzz, hook-errors, hooks-elsewhere
- <a id="hook-feedback"></a>[**hook-feedback**](adapters/stdlib/hook-feedback/) \
  Your corrections to an assistant (no, wrong, I said) caught by fixed patterns at each prompt and handed in through propose, to keep or drop. \
  *new* `no-install` `offline` `prompt` `assistant` `hooks` · near: hook-handoff, hook-read-first, hook-errors
- <a id="hook-fuzz"></a>[**hook-fuzz**](adapters/stdlib/hook-fuzz/) \
  Throws empty, malformed, oversized and non-UTF-8 input at a hook and fails it if any crash it, since a crashed hook lets the tool run. \
  *new* `no-install` `offline` `crash` `fails` `hooks` · near: hook-fail-closed, fuzz, hook-replay
- <a id="hook-guard"></a>[**hook-guard**](adapters/stdlib/hook-guard/) \
  A PreToolUse hook that blocks, by fixed rule and never by judgment, a call that would read your key or write the record behind its back. \
  *box* `no-install` `offline` `assistant` `pretooluse` `hooks` · near: hook-impact, hook-leaks, hook-read-first
- <a id="hook-handoff"></a>[**hook-handoff**](adapters/stdlib/hook-handoff/) \
  A Stop hook that writes where the session ended, and the next session's first prompt gets it back, so nothing rides on memory. \
  Hands on the session's id and the folder it ended in, never your files' words, to the next session's model. *new* `no-install` `to-a-model` `assistant`
  `prompt` `hooks` · near: hook-read-first, hook-feedback, hook-errors
- <a id="hook-impact"></a>[**hook-impact**](adapters/stdlib/hook-impact/) \
  Before an edit, a hook hands the assistant every place in your files that names what it's about to change, by file and line. \
  Uses habits. Hands on the lines of your files that name a file before it is edited, to the assistant's model. *box* `no-install` `to-a-model` `assistant`
  `edit` `hooks` · near: hook-read-first, hook-feedback, hook-handoff

#### What guards it, h to s

- <a id="hook-leaks"></a>[**hook-leaks**](adapters/stdlib/hook-leaks/) \
  A PreToolUse hook that refuses a write or command holding a key, password or card number, by the privacy add-on's shapes, naming the kind. \
  Uses privacy. *box* `no-install` `offline` `numbers` `key` `hooks` · near: hook-read-first, hook-impact, hook-guard
- <a id="hook-pin"></a>[**hook-pin**](adapters/stdlib/hook-pin/) \
  Each hook's SHA-256 kept on the record when you approve it, so a hook that changed since is named before it runs, never trusted silently. \
  *new* `no-install` `offline` `byte` `pin` `hooks` · near: hook-replay, ci-memo, backup
- <a id="hook-read-first"></a>[**hook-read-first**](adapters/stdlib/hook-read-first/) \
  A PreToolUse hook that refuses an edit to a file the assistant hasn't read this session, or that changed since, each read kept as a hash. \
  *new* `no-install` `offline` `assistant` `edit` `hooks` · near: hook-impact, hook-handoff, hook-errors
- <a id="hook-replay"></a>[**hook-replay**](adapters/stdlib/hook-replay/) \
  Every hook's answer kept as a row of the hashes of what it got and said; check runs it again to prove the same input gets the same answer. \
  *new* `no-install` `offline` `hash` `rows` `hooks` · near: hook-errors, hook-pin, ci
- <a id="hook-shell"></a>[**hook-shell**](adapters/stdlib/hook-shell/) \
  A command split as the shell will split it (quotes, variables, chained commands) before any rule judges it, so spelling can't dodge a rule. \
  *new* `no-install` `offline` `command` `shell` `hooks` · near: hook-errors, shell, hook-impact
- <a id="hook-start"></a>[**hook-start**](adapters/stdlib/hook-start/) \
  A SessionStart hook that hands the assistant what needs you, read the way digest reads it, so opening a session writes nothing. \
  Uses digest. Hands on what needs you, its dated lines and waiting suggestions included, to the assistant's model at the session's start. *bot* `no-install`
  `to-a-model` `assistant` `coming` `hooks` · near: digest, hook-impact, browse
- <a id="hook-stop"></a>[**hook-stop**](adapters/stdlib/hook-stop/) \
  A Stop hook that won't let an assistant's turn end while the record doesn't verify or its changes aren't committed, and says which. \
  *box* `no-install` `offline` `assistant` `end` `hooks` · near: hook-handoff, hook-read-first, hook-feedback
- <a id="hooks-elsewhere"></a>[**hooks-elsewhere**](adapters/stdlib/hooks-elsewhere/) \
  The prompt hook for Gemini CLI, Codex and opencode, wherever they take hooks, held to Claude Code's answer byte for byte. \
  Uses claude-code. Hands on the passages served for each prompt, to the model of the assistant it hooks (Gemini CLI, Codex, opencode). *box* `no-install`
  `to-a-model` `prompt` `gemini` `hooks` · near: claude-code, gemini-cli, hook-feedback
- <a id="serve"></a>[**serve**](adapters/stdlib/serve/) \
  The one file an AI model may read: only the passages you approved, under ids it can't guess, and nothing else. \
  *bot* `no-install` `offline` · near: stack, decisions, folder-card

#### What guards it: ideas, not built yet

- <a id="hook-checks"></a>**hook-checks** (idea) \
  A PostToolUse hook that runs the repo's fast checks on the file just edited and hands back only what failed, the same for the same file. \
  *new* `no-install` `offline` `fails` `edit` `hooks` · near: hook-errors, hook-pin, hook-impact
- <a id="hook-cite"></a>**hook-cite** (idea) \
  A hook that refuses an assistant's claim citing a passage the box never served it, checked against the record by id. \
  *new* `no-install` `offline` `refuses` `assistant` `hooks` · near: claim-check, cite-honesty, hook-read-first
- <a id="hook-sequence"></a>**hook-sequence** (idea) \
  Rules over what an assistant did before, not just this call: no push until the tests ran on this commit, so many deletions a session. \
  *new* `no-install` `offline` `session` `assistant` `hooks` · near: hook-read-first, hook-stop, hook-guard
- <a id="hook-tiers"></a>**hook-tiers** (idea) \
  Edits sorted into tiers by the paths they touch, and the top tier held as a proposal until you seal it, by a rule you can read. \
  *new* `no-install` `offline` `edit` `held` `hooks` · near: translate, plain-language, hook-read-first
- <a id="serve-piles"></a>**serve-piles** (idea) \
  serve's piles grouped on all four W's (who, when, what, where), not where alone, so a model meets a question from every box that touched it. \
  *new* `no-install` `offline` `serve` `alone` · near: pile-serve, pile-rungs, words-pl

### What it makes for elsewhere

- <a id="folder-card"></a>[**folder-card**](adapters/stdlib/folder-card/) \
  A card for your folder itself (what the files are, their dates, the gaps you know of), made from your files and notes, as a model's context. \
  Uses gaps. *new* `no-install` `offline` `gaps` · near: serve, persona-card, gaps

### Tools you run yourself

- <a id="persona-card"></a>[**persona-card**](adapters/stdlib/persona-card/) \
  A persona written as a card and compiled into the same system-prompt bytes every time, with the prompt's hash on the record. \
  *box* `no-install` `offline` · near: folder-card, tip-pin, serve

#### Tools you run yourself: ideas, not built yet

- <a id="issue-answer"></a>**issue-answer** (idea) \
  A workflow that drafts an answer to a new issue from the repo's own docs, each line cited, posted only once a maintainer seals it. \
  Goes online: the forge, through the workflow's token, to post an answer once it is sealed. *new* `no-install` `online` `docs` `posts` · near: repo-index,
  pr-context, bluesky
- <a id="mcp-by-hash"></a>**mcp-by-hash** (idea) \
  Your passages served as MCP resources named by their SHA-256, so an assistant cites the bytes it read; a changed one gets a new name. \
  *bot* `no-install` `offline` `assistant` `sha` · near: model-card, snapshot, hook-pin
- <a id="mex"></a>**mex** (idea) \
  mex's project memory for coding agents: its scaffold read as cited passages, and what an agent writes back held for your seal. \
  *new* `no-install` `offline` `memory` `agent` · near: instruction-files, hook-handoff, codebase-memory

### Works on willow itself

- <a id="forge"></a>[**forge**](adapters/deps/forge/) \
  A sentence in, the add-ons it means out: a plan with its forks, for the Forge's checkpoint to settle and the person to seal before it runs. \
  Needs forge-play; Apache-2.0. Uses stack. *new* `needs-install` `offline` `sentence` `forge` · near: stack-share, kart, plain

## Ways to use it

### What runs on your page

- <a id="deep-links"></a>[**deep-links**](adapters/stdlib/deep-links/) \
  Each answer as a link that opens the file at the line (RFC 5147 lines, browser text fragments). \
  *new* `no-install` `offline` `links` `browser` · near: browse, jetbrains, vscode

### In your terminal

- <a id="pipe"></a>[**pipe**](adapters/stdlib/pipe/) \
  Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf. \
  *box* `no-install` `offline` `json` · near: vim, shell, emacs
- <a id="plain"></a>[**plain**](adapters/stdlib/plain/) \
  Answers as sentences instead of JSON, each with its file and line. \
  *new* `no-install` `offline` `sentence` · near: readings, privacy, on-this-day
- <a id="shell"></a>[**shell**](adapters/stdlib/shell/) \
  A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows. \
  *new* `no-install` `offline` `shell` `bash` · near: pipe, shell-history, hook-shell
- <a id="start"></a>[**start**](adapters/stdlib/start/) \
  First run in one step: asks where your files are, sets up willow's record and your key, copies in a starter words list, prints a launcher. \
  *new* `no-install` `offline` `launcher` `starter` `everyday` · near: starter-words, launcher, nicknames

#### In your terminal: ideas, not built yet

- <a id="tui"></a>**tui** (idea) \
  A full-screen terminal view to ask, read passages and approve, in curses. \
  *new* `no-install` `offline` `screen` `full` · near: browse, jeles, serve
- <a id="warm"></a>**warm** (idea) \
  The kernel kept running between questions on this machine, so each question skips the start-up. \
  Reaches this machine only. *new* `no-install` `this-machine` `start` `between` · near: pile-store, start, night-batch

### In your editor

- <a id="emacs"></a>[**emacs**](adapters/stdlib/emacs/) \
  Answers in an Emacs compilation buffer, each a jump to its file and line. \
  Uses hosts. *new* `no-install` `offline` `jump` `command` · near: vim, vscode, pipe
- <a id="jetbrains"></a>[**jetbrains**](adapters/stdlib/jetbrains/) \
  An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line. \
  Uses hosts. *new* `no-install` `offline` `links` · near: vscode, privacy, aider
- <a id="vim"></a>[**vim**](adapters/stdlib/vim/) \
  Answers in Vim and Neovim's quickfix list, each a jump to its file and line. \
  Uses hosts. *new* `no-install` `offline` `jump` · near: emacs, pipe, vscode
- <a id="vscode"></a>[**vscode**](adapters/stdlib/vscode/) \
  A VS Code task whose answers land in the Problems panel, each a jump to its file and line. \
  Uses hosts. *new* `no-install` `offline` `jump` · near: emacs, vim, jetbrains

#### In your editor: ideas, not built yet

- <a id="obsidian"></a>**obsidian** (idea) \
  Ask from inside Obsidian, answers as links to the note and line. \
  Reaches this machine only. *new* `no-install` `this-machine` `links` `obsidian` · near: jetbrains, notes, deep-links

### In your browser or on your desktop

- <a id="browse"></a>[**browse**](adapters/stdlib/browse/) \
  Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only. \
  Reaches this machine only. *new* `no-install` `this-machine` `web` `everyday` · near: launcher, digest, hook-start
- <a id="launcher"></a>[**launcher**](adapters/stdlib/launcher/) \
  Ask from Alfred, Raycast, KRunner or PowerToys Run, answers with file and line. \
  *new* `no-install` `offline` · near: aider, browse, same-way
- <a id="static-search"></a>[**static-search**](adapters/deps/static-search/) \
  An exported page of approved answers with its own search built in, no server of its own, served from any static host. \
  Needs Pagefind, its Python package pagefind and its program pagefind-bin; MIT. *box* `needs-install` `offline` `search` · near: mcp, record-sql, pgp

#### In your browser or on your desktop: ideas, not built yet

- <a id="datasette"></a>**datasette** (idea) \
  Your record and approved answers browsable in Datasette, read only: tables, facets and SQL on this machine. \
  Needs Datasette; Apache-2.0. Reaches this machine only. *new* `needs-install` `this-machine` `sql` · near: record-sql, report, export
- <a id="desktop"></a>**desktop** (idea) \
  A small window to ask and approve, with nothing to install: Python's own tkinter. \
  *new* `no-install` `offline` · near: copilot, cursor, opencode
- <a id="kiosk"></a>**kiosk** (idea) \
  A shared machine in a library or classroom: one box, ask only, nobody's key on it. \
  Reaches this machine only. *new* `no-install` `this-machine` `share` `key` · near: share, family-box, transcript-redact

### From your phone, by voice or by email

- <a id="wake-gate"></a>[**wake-gate**](adapters/deps/wake-gate/) \
  Ask out loud after a wake word you chose: audio before it is never transcribed, kept or sent. \
  Needs onnxruntime, numpy and faster-whisper; MIT, BSD-3-Clause, MIT. A wake word model you give it, trained the openWakeWord way; openWakeWord's own are CC
  BY-NC-SA 4.0. From: code of [willow-memory/willow-mcp](https://github.com/willow-memory/willow-mcp), Apache-2.0; code of
  [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord), Apache-2.0. *new* `needs-install` `offline` `loud` · near: dictate, pdf, ocr

#### From your phone, by voice or by email: ideas, not built yet

- <a id="dictate"></a>**dictate** (idea) \
  Ask out loud: your question spoken and turned to text on this machine. \
  Needs faster-whisper; MIT. Goes online: the model, downloaded once. *new* `needs-install` `online` `loud` `spoken` · near: wake-gate, oakenscroll, misheard
- <a id="email-ask"></a>**email-ask** (idea) \
  Ask by emailing yourself; the answer comes back as a reply with its sources. \
  Goes online: your own mail server, over IMAP and SMTP, to read questions and reply. *new* `no-install` `online` `sources` `replies` · near: jeles,
  willow-box, bot-venv
- <a id="home-assistant"></a>**home-assistant** (idea) \
  Ask through Home Assistant's voice assistant, answered from your files. \
  Goes online: your Home Assistant, on your own network, to answer its voice assistant. *new* `no-install` `online` `assistant` `voice` · near: home-sensors,
  mcp-sampling, willow-box
- <a id="qr"></a>**qr** (idea) \
  An answer as a QR code on screen, to carry it to your phone without the network. \
  *new* `no-install` `offline` `screen` `phone` · near: scrub, a11y-check, code-first
- <a id="speak"></a>**speak** (idea) \
  Reads answers aloud. \
  Needs pyttsx3; MPL-2.0. *new* `needs-install` `offline` · near: willow-box, aider, debts
- <a id="telegram-bot"></a>**telegram-bot** (idea) \
  Ask from your phone through a Telegram bot only you can talk to. \
  Goes online: api.telegram.org, to receive your questions and send answers. *new* `no-install` `online` `telegram` `bot` · near: bot-venv, chats, cursor

### Several add-ons at once

- <a id="across"></a>[**across**](adapters/stdlib/across/) \
  One page from several willow records at once (each one's digest, export, timeline or readings), every line still cited where it came from. \
  *new* `no-install` `offline` `timeline` `several` `everyday` · near: stack, timeline, readme
- <a id="stack"></a>[**stack**](adapters/stdlib/stack/) \
  One page made from several add-ons run in the order you list them, their results grouped so the biggest come first. \
  *new* `no-install` `offline` `stack` `several` · near: across, serve, stack-share
- <a id="stack-share"></a>[**stack-share**](adapters/stdlib/stack-share/) \
  A stack you sealed with the Forge, written out to share: your sentence, each choice and why, each step's promises, and the stack to run. \
  Uses forge, stack. *new* `no-install` `offline` `stack` `forge` · near: forge, stack, kart

### Other ways in


#### Other ways in: ideas, not built yet

- <a id="pr-context"></a>**pr-context** (idea) \
  On a pull request, the passages in the repo's docs that name the files it changes, posted as one comment. \
  Goes online: the forge, through the workflow's token, to post the comment. *new* `no-install` `online` `pull` `request` · near: against, quote-review,
  github-archive
- <a id="safe-app"></a>**safe-app** (idea) \
  willow as a SAFE app: installed from the SAFE App Store, authorized per session, and deleted clean. \
  *new* `no-install` `offline` `store` `session` · near: vectors, memory-import, session-cost
- <a id="socratic"></a>**socratic** (idea) \
  Asks you questions about your own notes instead of answering, each citing the passage it asked from. \
  *new* `no-install` `offline` `citing` · near: equations, oakenscroll, sort-ask
- <a id="willow-box"></a>**willow-box** (idea) \
  Ask from a Willow voice box on your counter: its application server sends your words here and reads the answer back. \
  Goes online: your Willow Application Server, on your own network, to answer what the box heard. From: shape of
  [HeyWillow/willow-application-server](https://github.com/HeyWillow/willow-application-server), Apache-2.0. *new* `no-install` `online` `voice` · near:
  aider, speak, shell

### What it makes for elsewhere

- <a id="annotations"></a>[**annotations**](adapters/stdlib/annotations/) \
  Approved answers as W3C Web Annotations, so any annotation tool can show what your files say about a page. \
  *new* `no-install` `offline` `web` · near: rss-out, in-toto, prov
- <a id="badge"></a>[**badge**](adapters/stdlib/badge/) \
  A badge for a page: these answers came from these files and were approved, linked to the check anyone can run. \
  *new* `no-install` `offline` `links` · near: in-toto, annotations, deep-links
- <a id="braille"></a>[**braille**](adapters/stdlib/braille/) \
  Answers as braille-ready files (BRF) for a braille display or embosser. \
  *new* `no-install` `offline` · near: text, annotations, rss-out
- <a id="calendar-out"></a>[**calendar-out**](adapters/stdlib/calendar-out/) \
  Dates coming up as an .ics file your calendar app can subscribe to. \
  Uses coming-up. *new* `no-install` `offline` `coming` `calendar` · near: coming-up, digest, calendar
- <a id="capture"></a>[**capture**](adapters/stdlib/capture/) \
  A note written into your folder in one line, with its type and tags, so the next question can find it. \
  *new* `no-install` `offline` `tags` · near: coming-up, serve, plain
- <a id="cloudevents"></a>[**cloudevents**](adapters/stdlib/cloudevents/) \
  Record rows in the CloudEvents envelope, for any tool that already reads them. \
  *new* `no-install` `offline` `envelope` `tool` · near: prov, ro-crate, in-toto
- <a id="llms-txt"></a>[**llms-txt**](adapters/stdlib/llms-txt/) \
  An llms.txt for your folder, written to the spec's version 2 from what's in it, and any llms.txt you saved checked against that spec. \
  *new* `no-install` `offline` `llm` · near: typosquat, markdown, serve
- <a id="make-it-so"></a>[**make-it-so**](adapters/stdlib/make-it-so/) \
  Write down what you want done and the passages it rests on; it checks they still hold, and never does it for you. \
  *new* `no-install` `offline` `down` · near: decisions, predict, xref
- <a id="print"></a>[**print**](adapters/stdlib/print/) \
  An answer as a printable page with its sources, to take to an appointment; --large for big, high-contrast type. \
  *new* `no-install` `offline` `prints` `everyday` · near: web-pages, pipe, across
- <a id="repo-pile"></a>[**repo-pile**](adapters/stdlib/repo-pile/) \
  Public repositories you list, cloned and made askable, keeping only those under a licence an Apache-2.0 project can use. \
  Uses again, backup, changed, digest, export, history, privacy, quote-check, scan, secrets-audit, stale, todo, xref. Goes online: github.com (or the --source
  you give), to clone the repositories you list. *new* `no-install` `online` `repositories` `build` `research` · near: upstream-desk, pile-serve, pile-build
- <a id="rss-out"></a>[**rss-out**](adapters/stdlib/rss-out/) \
  New approved answers as an RSS feed file, for any feed reader. \
  *new* `no-install` `offline` `feed` · near: annotations, in-toto, opml
- <a id="share"></a>[**share**](adapters/stdlib/share/) \
  Sealed answers sent to someone, checkable by them and by whoever they pass them on to, without giving anyone the folder. \
  From: shape of [willow-memory/willow-gate](https://github.com/willow-memory/willow-gate), Apache-2.0. *new* `no-install` `offline` `sent` · near: kart,
  invoices, pgp

#### What it makes for elsewhere: ideas, not built yet

- <a id="anki"></a>**anki** (idea) \
  Approved answers as an Anki deck, built without Anki installed. \
  *new* `no-install` `offline` · near: static-search, stale, export
- <a id="emergency-card"></a>**emergency-card** (idea) \
  One page of your medicines, allergies and contacts, from your files, to print or keep on your phone. \
  *new* `no-install` `offline` `prints` `contacts` · near: privacy, calendar, stack
- <a id="received"></a>**received** (idea) \
  A package you were sent, kept by your own choice as a page: whose word it is, when, not sealed by you, so your folder can answer from it. \
  Uses share. *new* `no-install` `offline` `sent` `choice` · near: kart, share, silence-log

### Tools you run yourself

- <a id="kart"></a>[**kart**](adapters/deps/kart/) \
  A job someone sent you, run in a sandbox over your own folder only once you seal it, its result yours to seal before it goes back. \
  Needs kartikeya, and the bwrap program (bubblewrap), run not linked; Apache-2.0, LGPL-2.0-or-later. Uses share. *new* `needs-install` `offline` · near: ocr,
  pdf, dialect
- <a id="stack-bridges"></a>[**stack-bridges**](adapters/stdlib/stack-bridges/) \
  Which steps of a stack take what an earlier step made, the order that leaves them in, and a step that takes what none before it made. \
  Uses stack. *new* `no-install` `offline` `stack` `order` · near: stack, stack-share, ready
- <a id="wasi-python"></a>[**wasi-python**](adapters/deps/wasi-python/) \
  A job someone sent you as a Python script, run on CPython for WebAssembly over your folder read-only: one runtime, the same answer anywhere. \
  Needs wasi-python; Apache-2.0. Uses kart, share. *new* `needs-install` `offline` `job` `sent` · near: kart, fast-tests, dialect
- <a id="wasm"></a>[**wasm**](adapters/deps/wasm/) \
  A job someone sent you as WebAssembly, run by Wasmtime over your folder read-only: the same bytes, so the same answer, on every machine. \
  Needs wasmtime; Apache-2.0 WITH LLVM-exception. Uses kart, share. *new* `needs-install` `offline` `job` `sent` · near: kart, fast-tests, dialect

#### Tools you run yourself: ideas, not built yet

- <a id="one-step"></a>**one-step** (idea) \
  One step of a kept run run again alone, its new output kept in its place, and the steps after it marked as resting on the old one. \
  Uses stack. *new* `no-install` `offline` `step` · near: hook-replay, start, warm
- <a id="stack-check"></a>**stack-check** (idea) \
  A stack file read through before anything runs: each add-on is here, each option is one it takes, each file it names is there. \
  Uses stack. *new* `no-install` `offline` `stack` · near: stack, mutants, sap-gate

## Play

### What runs on your page

- <a id="pile-poetry"></a>[**pile-poetry**](adapters/stdlib/pile-poetry/) \
  Verse from the word pairs your own files use most, in your own dialect. \
  Uses tarot. *new* `no-install` `offline` `dialect` `pairs` · near: dialect, pair-drift, second-opinion

### What it makes for elsewhere


#### What it makes for elsewhere: ideas, not built yet

- <a id="movie"></a>**movie** (idea) \
  Your record as a Gource film: every question, approval and miss growing like a tree. \
  Needs the gource program; GPL-3.0, called not linked. *new* `needs-install` `offline` `tree` `miss` · near: bench, family-tree, vectors

### Tools you run yourself

- <a id="catgrid"></a>[**catgrid**](adapters/stdlib/catgrid/) \
  A seeded logic grid with one cat in every row, column and colour region and a unique answer, replayed from its moves. \
  *new* `no-install` `offline` `rows` `seeded` · near: life, game-master, hook-replay
- <a id="daily-word"></a>[**daily-word**](adapters/stdlib/daily-word/) \
  A five-letter word game drawn from your own files' words: a new word each day, the same for anyone asking the same folder. \
  *new* `no-install` `offline` · near: quiz, surprise, serve
- <a id="dice"></a>[**dice**](adapters/stdlib/dice/) \
  Seeded dice rolls as rows: every roll replayable and checkable. \
  *bot* `no-install` `offline` `rows` `dice` · near: dice5e, game-master, tarot
- <a id="dice5e"></a>[**dice5e**](adapters/stdlib/dice5e/) \
  Full tabletop dice notation (4d6kh3, advantage), rolled on the record and checkable like dice. \
  Uses dice. *bot* `no-install` `offline` `rolls` `tabletop` · near: dice, game-master, fight5e
- <a id="game-master"></a>[**game-master**](adapters/stdlib/game-master/) \
  A tabletop game's rolls and rulings as rows on the record, with the game master's calls sealed. \
  Uses dice, odds. *bot* `no-install` `offline` `rows` `dice` · near: life, dice5e, dice
- <a id="horoscope"></a>[**horoscope**](adapters/stdlib/horoscope/) \
  A daily horoscope keyed on your name and the date: same name, same day, same reading, always. \
  *bot* `no-install` `offline` `daily` · near: daily-word, goodreads, gaps
- <a id="life"></a>[**life**](adapters/stdlib/life/) \
  Conway's Game of Life as rows: a fully deterministic world on the record. \
  *bot* `no-install` `offline` `rows` `game` · near: catgrid, game-master, tarot
- <a id="odds"></a>[**odds**](adapters/stdlib/odds/) \
  Exact odds, as fractions, for a game's dice and tables: what each outcome's chance really is. \
  *bot* `no-install` `offline` `game` `dice` · near: game-master, dice, dice5e
- <a id="oracle-text"></a>[**oracle-text**](adapters/stdlib/oracle-text/) \
  Readings written by a Tracery grammar, every branch picked by the seeded stream, so each one can be replayed. \
  Uses tarot. *new* `no-install` `offline` `seeded` `branch` · near: hook-replay, ink-story, restack
- <a id="quiz"></a>[**quiz**](adapters/stdlib/quiz/) \
  A quiz from your own files: a passage with a word missing, and you fill it in. \
  *new* `no-install` `offline` · near: daily-word, serve, pile-gold
- <a id="tarot"></a>[**tarot**](adapters/stdlib/tarot/) \
  A seeded tarot draw on the record, replayable by anyone with the seed. \
  *new* `no-install` `offline` `seeded` `replayable` · near: life, catgrid, dice

#### Tools you run yourself: ideas, not built yet, a to m

- <a id="art-of-the-day"></a>**art-of-the-day** (idea) \
  An artwork from the Met's public-domain collection, drawn for the day or for each sealed session. \
  Goes online: collectionapi.metmuseum.org, to read the artwork. *new* `no-install` `online` `domain` `drawn` · near: todays-place, gutenberg, session-seal
- <a id="beacon"></a>**beacon** (idea) \
  Draws seeded by a public randomness beacon (drand), so nobody could have picked the result in advance. \
  Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `seeded` `draws` · near: tarot, oracle-text, dice
- <a id="chess-puzzle"></a>**chess-puzzle** (idea) \
  A Lichess puzzle a day, drawn by a seed: predict whether you'll solve it, then solve it. \
  Goes online: lichess.org, to read the puzzle. *new* `no-install` `online` `drawn` `chess` · near: predict, daily-word, art-of-the-day
- <a id="connect-four"></a>**connect-four** (idea) \
  Connect Four as rows on the record, held to the solved result: the first player wins. \
  *new* `no-install` `offline` `result` `held` · near: schema-check, cloudevents, crates
- <a id="fight5e"></a>**fight5e** (idea) \
  Tabletop combat run from stat blocks on dice5e's rolls, every attack on the record and replayable. \
  *new* `no-install` `offline` `rolls` `replayable` · near: dice5e, dice, roll-for-merge
- <a id="front-page"></a>**front-page** (idea) \
  Which new posts will make the Hacker News front page? Wager, and let its search settle it. \
  Goes online: hn.algolia.com, to read the front page. *new* `no-install` `online` `settle` `front` · near: spurious, readme, quake-bets
- <a id="gutenberg"></a>**gutenberg** (idea) \
  A paragraph from a public-domain book beside one of yours, for serendipity. \
  Goes online: gutenberg.org, each book fetched once. *new* `no-install` `online` `book` `domain` · near: todays-place, art-of-the-day, scripture
- <a id="hanoi"></a>**hanoi** (idea) \
  Towers of Hanoi as rows: each move, n discs in 2^n - 1. \
  *new* `no-install` `offline` `rows` `move` · near: reversi, tic-tac-toe, session-seal
- <a id="horoscope-grades"></a>**horoscope-grades** (idea) \
  Every horoscope logged as a forecast and settled against the day, so the stars get a Brier score. \
  *new* `no-install` `offline` `forecast` `score` · near: forecasts, weather-bet, predictions
- <a id="ink-story"></a>**ink-story** (idea) \
  A branching ink story where every choice made for you comes from a seed on the record. \
  Needs inkjs; MIT. *new* `needs-install` `offline` `seeded` `branch` · near: oracle-text, tarot, timeline
- <a id="joins"></a>**joins** (idea) \
  Two passages from two different folders, drawn by chance, for you to say what joins them. \
  *bot* `no-install` `offline` `joins` `drawn` · near: contradictions, pageviews, crosswalk
- <a id="lore"></a>**lore** (idea) \
  For a world you're writing: each fact about it sealed one at a time, so a story can be checked against its canon. \
  *bot* `no-install` `offline` `world` · near: mutants, llms-txt, claim-check
- <a id="lunatic"></a>**lunatic** (idea) \
  The moon's real phase sets how far typos are forgiven: everything at full moon, nothing at new. \
  Needs Skyfield; MIT. *new* `needs-install` `offline` `far` `typos` · near: typos, real-sky, dialect
- <a id="mastermind"></a>**mastermind** (idea) \
  Mastermind with the secret's hash at the open: each guess and score on the record. \
  *new* `no-install` `offline` `score` `hash` · near: assistant-scores, secrets-audit, quiz

#### Tools you run yourself: ideas, not built yet, n to w

- <a id="nim"></a>**nim** (idea) \
  Nim as rows: the heaps and each take, a position lost exactly when the heaps' XOR is 0. \
  *new* `no-install` `offline` `rows` `lost` · near: tic-tac-toe, cloudevents, model-card
- <a id="ninety-percent"></a>**ninety-percent** (idea) \
  The calibration drill: give a range you're 90% sure of for a real number, and see how many hold. \
  Goes online: Our World in Data, its numbers downloaded once. *new* `no-install` `online` `ranges` `drill` · near: oakenscroll, restore-drill, pins
- <a id="pageviews"></a>**pageviews** (idea) \
  Two Wikipedia articles drawn at random: which gets more views tomorrow? \
  Goes online: the Wikimedia pageviews API, to settle it. *new* `no-install` `online` `article` `drawn` · near: surprise, kiwix, joins
- <a id="predictions"></a>**predictions** (idea) \
  Twelve yes-or-no questions about random data, forecast now and answered by a beacon round later, with your Brier score. \
  Goes online: api.drand.sh, to read a beacon round's randomness. *bot* `no-install` `online` `score` `brier` · near: forecasts, tides, horoscope-grades
- <a id="quake-bets"></a>**quake-bets** (idea) \
  Will there be a magnitude 6 this week? Bet, then let the USGS feed settle it against the base rate. \
  Goes online: earthquake.usgs.gov, to read the week's earthquakes. *new* `no-install` `online` `bet` `settle` · near: horoscope-grades, ci-bets, weather-bet
- <a id="real-sky"></a>**real-sky** (idea) \
  A horoscope from where the planets really are, computed offline from a JPL ephemeris. \
  Needs Skyfield; MIT. Goes online: the ephemeris file, downloaded once. *new* `needs-install` `online` `horoscope` `computed` · near: horoscope,
  horoscope-grades, odds
- <a id="reversi"></a>**reversi** (idea) \
  Reversi as rows: every move, each flip following from the board. \
  *new* `no-install` `offline` `move` `rows` · near: tic-tac-toe, catgrid, same-way
- <a id="roll-for-merge"></a>**roll-for-merge** (idea) \
  A d20 for every pull request, green runs added and red streaks taken away, against a DC the bot calls. \
  *new* `no-install` `offline` `pull` `request` · near: red-on-main, ci-bets, against
- <a id="sokoban"></a>**sokoban** (idea) \
  Sokoban levels and moves on the record, a solution checked by replaying it. \
  *new* `no-install` `offline` `replayed` `level` · near: hook-replay, catgrid, reading-level
- <a id="spurious"></a>**spurious** (idea) \
  Everything joined on time and place (CI reds, earthquakes, rain, front pages) to hunt correlations that mean nothing. \
  *new* `no-install` `offline` `front` `joins` · near: front-page, ci-why, readme
- <a id="tic-tac-toe"></a>**tic-tac-toe** (idea) \
  Tic-tac-toe as rows: every move, and the solver's value of each position; perfect play draws. \
  *new* `no-install` `offline` `rows` `move` · near: reversi, catgrid, nim
- <a id="tides"></a>**tides** (idea) \
  Tide predictions as a control: if your Brier score on tides isn't near zero, the forecasting plumbing is broken. \
  Goes online: NOAA's tides API, to read predictions and what happened. *new* `no-install` `online` `score` `forecast` · near: predictions, forecasts,
  horoscope-grades
- <a id="todays-place"></a>**todays-place** (idea) \
  One place a day drawn from Natural Earth's public-domain list, for the day's questions and bets. \
  *new* `no-install` `offline` `public` `domain` · near: art-of-the-day, gutenberg, tax-year
- <a id="weather-bet"></a>**weather-bet** (idea) \
  Wager on rain tomorrow before you look, against Open-Meteo's own forecast, and see whose Brier score wins. \
  Goes online: api.open-meteo.com, to read the forecast and the outcome. *new* `no-install` `online` `forecast` `score` · near: forecasts, horoscope-grades,
  ci-bets

## For maintainers

### What runs on your page

- <a id="agents-md-check"></a>[**agents-md-check**](adapters/stdlib/agents-md-check/) \
  Commands and paths named in AGENTS.md, CLAUDE.md, GEMINI.md or copilot-instructions.md that no longer exist in the repo. \
  *new* `no-install` `offline` `agent` `gemini` · near: instruction-files, skim, hook-impact
- <a id="pins"></a>[**pins**](adapters/stdlib/pins/) \
  Version ranges in package.json, pyproject.toml or Cargo.toml that no lockfile holds. \
  Uses advisories. *new* `no-install` `offline` `package` `cargo` · near: lockfiles, typosquat, outdated

### What it makes for elsewhere


#### What it makes for elsewhere: ideas, not built yet

- <a id="crates"></a>**crates** (idea) \
  A Rust port of kernel.py on crates.io, held to the same vectors as the other four. \
  Goes online: crates.io, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `port` · near: swift, compiled, connect-four
- <a id="maven"></a>**maven** (idea) \
  The Java port on Maven Central, built from this repo and checked against the vectors. \
  Goes online: Maven Central, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `port` · near: nuget, npm, pypi
- <a id="npm"></a>**npm** (idea) \
  The TypeScript port on npm, built from this repo, checked against the vectors, and published with provenance; npx runs it. \
  Goes online: registry.npmjs.org, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `port` · near: nuget, maven, pypi
- <a id="nuget"></a>**nuget** (idea) \
  The C# port on NuGet, built from this repo and checked against the vectors. \
  Goes online: nuget.org, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `port` · near: maven, npm, pypi
- <a id="pypi"></a>**pypi** (idea) \
  kernel.py on PyPI as a package with no dependencies, built from this repo, checked against the vectors and attested; uvx and pipx run it. \
  Goes online: upload.pypi.org, to publish a release a maintainer tags. *new* `no-install` `online` `vectors` `package` · near: npm, nuget, maven
- <a id="repo-index"></a>**repo-index** (idea) \
  This repository as its own deterministic box: its cards, docs and code as dated passages, the same each build, so willow can answer of it. \
  *new* `no-install` `offline` `repositories` `build` · near: repo-pile, issue-answer, latent

### Tools you run yourself

- <a id="bench"></a>[**bench**](adapters/stdlib/bench/) \
  How fast the kernel answers on boxes of set sizes, per release, so a slowdown is seen. \
  *new* `no-install` `offline` `release` · near: profile, pile-store, pile-build
- <a id="bot-venv"></a>[**bot-venv**](adapters/stdlib/bot-venv/) \
  Where your venvs are, in willow-bot or out, their locks and the services running them; and which one has what CI needs, and how to run it. \
  *bot* `no-install` `offline` `test` · near: ci, fast-tests, ci-why
- <a id="ci-cache"></a>[**ci-cache**](adapters/stdlib/ci-cache/) \
  CI caches pip, npm, .NET and Maven downloads keyed on their lockfiles, so a run skips the installs. \
  *new* `no-install` `offline` `npm` `cache` · near: ci-memo, ci, ci-logs
- <a id="ci-why"></a>[**ci-why**](adapters/stdlib/ci-why/) \
  Why CI went red: the failing block pulled out of the job's log, plain, put where people look. \
  *bot* `no-install` `offline` `fails` `pull` · near: ci, ci-logs, red-on-main
- <a id="fast-tests"></a>[**fast-tests**](adapters/deps/fast-tests/) \
  The test suite across every core with pytest-xdist, the same tests in a fraction of the time. \
  Needs pytest-xdist; MIT. *new* `needs-install` `offline` `core` `fraction` · near: parallel, pdf, kart
- <a id="mutants"></a>[**mutants**](adapters/stdlib/mutants/) \
  Breaks each add-on's code on purpose and checks its tests notice. \
  *new* `no-install` `offline` `test` · near: live, slow-tests, ci
- <a id="profile"></a>[**profile**](adapters/stdlib/profile/) \
  Where a question's time goes, function by function, from cProfile, per release. \
  *new* `no-install` `offline` `release` · near: bench, test-shards, calendar
- <a id="slow-tests"></a>[**slow-tests**](adapters/stdlib/slow-tests/) \
  Each test's time kept per run, with the slowest named and any that got slower flagged. \
  *new* `no-install` `offline` `test` · near: test-shards, mutants, profile
- <a id="test-shards"></a>[**test-shards**](adapters/stdlib/test-shards/) \
  The CI test jobs split by each test's past time, so every job finishes about together. \
  *new* `no-install` `offline` `test` · near: slow-tests, ci, profile

#### Tools you run yourself: ideas, not built yet, c to f

- <a id="ci-baseline"></a>**ci-baseline** (idea) \
  Is your CI normal? How often pull requests everywhere go green first time, from GH Archive. \
  Goes online: data.gharchive.org, its hours downloaded once. *new* `no-install` `online` `pull` `request` · near: ci-bets, welcome, red-on-main
- <a id="ci-bets"></a>**ci-bets** (idea) \
  Bet on your own CI: forecasts on each pull request going green, scored against the model's. \
  *new* `no-install` `offline` `pull` `request` · near: ci-baseline, red-on-main, weather-bet
- <a id="code-stats"></a>**code-stats** (idea) \
  Lines, code and complexity per language, per release, as rows the list can answer from. \
  Needs the scc program; MIT. *new* `needs-install` `offline` `release` `language` · near: profile, bench, csv-rows
- <a id="compiled"></a>**compiled** (idea) \
  kernel.py compiled with mypyc for speed, held to the same vectors byte for byte. \
  Needs mypyc; MIT. *new* `needs-install` `offline` `byte` `held` · near: swift, crates, repro
- <a id="contribute"></a>**contribute** (idea) \
  For anyone on GitHub, what they can do next in the projects they work on: open pull requests, reviews asked of them, issues assigned. \
  Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `pull` `request` · near: upstream-desk, github-archive, quote-review
- <a id="contributions"></a>**contributions** (idea) \
  A ledger of who contributes to the repo: first-timers and outside contributors called out, bots known by type, never by name. \
  Goes online: GitHub, through gh, with your own login. *bot* `no-install` `online` `bot` `calls` · near: bot-venv, hook-guard, welcome
- <a id="docs-i18n"></a>**docs-i18n** (idea) \
  The README in other languages, each checked for drift against the English one. \
  *new* `no-install` `offline` `readme` `drift` · near: readme, llms-txt, against
- <a id="forgejo"></a>**forgejo** (idea) \
  What willow's repo needs from Forgejo, Gitea or Codeberg: its host.json and an Actions file, so the repo can move there. \
  Goes online: the Forgejo instance's API, to read the author of a pull request a security report points to. *new* `no-install` `online` `host` `forgejo` ·
  near: gitlab, sourcehut, forgejo-dump
- <a id="fuzz"></a>**fuzz** (idea) \
  Random and broken inputs thrown at the kernel's commands, every crash kept as a test. \
  *new* `no-install` `offline` `command` `test` · near: hook-fuzz, property-tests, hook-replay

#### Tools you run yourself: ideas, not built yet, g to w

- <a id="gitlab"></a>**gitlab** (idea) \
  What willow's repo needs from GitLab, as github does for GitHub: its host.json and CI file, so the repo can move there. \
  Goes online: GitLab, through glab, to read the author of a merge request a security report points to. *new* `no-install` `online` `host` `github` · near:
  forgejo, github, sourcehut
- <a id="novelty"></a>**novelty** (idea) \
  Before a new add-on merges, whether its combination of pieces has been assembled before, scanned the way a study checks its own novelty. \
  *new* `no-install` `offline` `merge` `scan` · near: similar, redential, restack
- <a id="property-tests"></a>**property-tests** (idea) \
  Thousands of odd inputs (combining marks, empty strings, huge seeds) thrown at the byte rules by Hypothesis. \
  Needs Hypothesis; MPL-2.0. *new* `needs-install` `offline` `inputs` `empty` · near: fuzz, hook-fuzz, model-shelf
- <a id="pypy"></a>**pypy** (idea) \
  The kernel and its tests run under PyPy too, and timed against CPython. \
  *new* `no-install` `offline` `test` · near: slow-tests, test-shards, mutants
- <a id="reconciler"></a>**reconciler** (idea) \
  willow-reconciler run on this repo's idea list and git history: how much of what was proposed has landed. \
  Needs willow-reconciler; Apache-2.0. From: dep of [willow-memory/willow-reconciler](https://github.com/willow-memory/willow-reconciler), Apache-2.0. *new*
  `needs-install` `offline` `git` `history` · near: git-history, hook-checks, git-notes
- <a id="repro"></a>**repro** (idea) \
  A release built twice from the same commit, byte for byte the same. \
  *new* `no-install` `offline` `byte` `twice` · near: compiled, mirror, gifts
- <a id="sourcehut"></a>**sourcehut** (idea) \
  What willow's repo needs from SourceHut: its host.json for patches by email and a builds.sr.ht manifest. \
  Goes online: sr.ht, through hut, to read the author of a patch a security report points to. *new* `no-install` `online` `host` `json` · near: forgejo,
  gitlab, github
- <a id="swift"></a>**swift** (idea) \
  A Swift port of kernel.py for iPhone and Mac apps, held to the same vectors. \
  *new* `no-install` `offline` `vectors` `port` · near: crates, compiled, nuget
- <a id="welcome"></a>**welcome** (idea) \
  One plain thank-you on a first-time contributor's first pull request, once per person, and only where it's turned on. \
  Goes online: the forge, through the workflow's token, to post the thank-you. *bot* `no-install` `online` `pull` `request` · near: ci-baseline, against,
  restack-open

### Works on willow itself

- <a id="against"></a>[**against**](adapters/stdlib/against/) \
  A pull request held to the other open ones: a name both add fails, a file both change is said. \
  Uses similar. *new* `no-install` `offline` `pull` `request` · near: test-impact, red-on-main, ready
- <a id="ci"></a>[**ci**](adapters/stdlib/ci/) \
  This repo's checks as verdict rows on a kernel record, the same every run. \
  Uses live, readme, skim, stack, test-shards. Goes online: PyPI, to read each dependency floor's release date; GitHub, through gh, to find main's last
  records (main_run.py, times.py). *box* `no-install` `online` `rows` `verdict` · near: ci-memo, bot-venv, ci-why
- <a id="ci-memo"></a>[**ci-memo**](adapters/stdlib/ci-memo/) \
  A CI gate whose inputs' bytes are unchanged keeps its recorded verdict: pin a run's per-gate keys, and run only what a change can reach. \
  Uses ci. *new* `no-install` `offline` `pin` `reach` · near: ci-cache, ci, test-impact
- <a id="github"></a>[**github**](adapters/stdlib/github/) \
  What willow's repo needs from GitHub, kept in one folder so it can be taken away. \
  Uses ci, readme, ready, stack. Goes online: GitHub, through gh, to read the author of a pull request a security report points to, and for create_pr.py to
  list the open pull requests and open yours. *box* `no-install` `online` `branch` `github` · near: ready, gitlab, ci
- <a id="kinds"></a>[**kinds**](adapters/stdlib/kinds/) \
  Every file of this repo sorted by what it is (code, a card, a test, made by a script, made-up, an idea) and the ones nothing declares. \
  *new* `no-install` `offline` `scripts` `test` · near: fast-tests, github, json-paths
- <a id="live"></a>[**live**](adapters/stdlib/live/) \
  Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here. \
  Uses mcp-lite, pipe. Goes online: only what the programs it starts reach on their own; it reaches nothing itself. *new* `no-install` `online` `tests` ·
  near: mutants, github, ci
- <a id="readme"></a>[**readme**](adapters/stdlib/readme/) \
  Builds ADDONS.md, and the README's one feature, from the add-ons' own cards. \
  Uses similar, skim. *new* `no-install` `offline` · near: similar, skim, front-page
- <a id="ready"></a>[**ready**](adapters/stdlib/ready/) \
  A branch made ready for its pull request, on no host: the repo's own steps run in order, what they make committed, and the body written. \
  Uses ci, stack, restack, test-impact, against. *new* `no-install` `offline` `pull` `request` · near: github, against, restack-open
- <a id="red-on-main"></a>[**red-on-main**](adapters/stdlib/red-on-main/) \
  A pull request's failing checks held to main's last run: red there too is not the pull request's, green there is. \
  *new* `no-install` `offline` `pull` `request` · near: against, ci-bets, ci-baseline
- <a id="repo-digest"></a>[**repo-digest**](adapters/stdlib/repo-digest/) \
  One page of what this repo needs from you: files nothing declares, a ring in what add-ons use, ideas waiting, and the order they build in. \
  Uses kinds. *new* `no-install` `offline` `digest` `build` · near: readme, across, stack
- <a id="restack"></a>[**restack**](adapters/stdlib/restack/) \
  Main merged into your branches, conflicts in the files the repo makes or only adds to settled by its own tools, and any other left to you. \
  *new* `no-install` `offline` `branch` `conflicts` `git` · near: restack-open, similar, oracle-text
- <a id="restack-open"></a>[**restack-open**](adapters/stdlib/restack-open/) \
  Every open pull request that conflicts with its base, merged up to it by restack's rules and pushed, or named for a person. \
  Uses restack. Goes online: github.com, to fetch and push the open pull requests' branches. *new* `no-install` `online` `pull` `request` · near: restack,
  red-on-main, ready
- <a id="similar"></a>[**similar**](adapters/stdlib/similar/) \
  What's already on the add-on list near a new idea, by the kernel's own search. \
  Uses pile-rank, readme. *box* `no-install` `offline` · near: ready, readme, restack
- <a id="skim"></a>[**skim**](adapters/stdlib/skim/) \
  The lists this repo makes held to how a person reads them: a heading each screen, no line too long, each add-on and folder a name to find. \
  *new* `no-install` `offline` `screen` `held` · near: against, agents-md-check, mutants
- <a id="test-impact"></a>[**test-impact**](adapters/stdlib/test-impact/) \
  Only the tests a change can reach run first, from the import graph; the full suite still runs after. \
  Uses ci. *new* `no-install` `offline` `suite` `reach` · near: against, ci-memo, lesson-time
<!-- /willow:list -->

Back to the [README](README.md).
