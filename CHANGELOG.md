# Changelog

What changed, newest first, by the pull request that changed it, under
Added, Changed, Fixed and Removed. A fix names what it fixes: a known bug
from [BUGS.md](BUGS.md) as `bug #N`, or a security report. A release turns
`Unreleased` into `vX.Y.Z · YYYY-MM-DD` ([CONTRIBUTING.md](CONTRIBUTING.md)
says how). The first was v0.1.0.

## Unreleased

### Added

- `stems`: Word forms for some thirty languages through Snowball's stemmer,
  so "häuser" finds "haus" and "книги" finds "книга": a word no file holds
  is read as the form of its stem the most passages hold, offered, never
  asked. Needs snowballstemmer.
- `photos`: When and where each photo was taken, from its EXIF, as a dated
  passage in a mirror: the date and time, the GPS position, the camera.
  Needs Pillow, floored at 11.0.0, the first with a wheel for Python 3.13.
- `sheets`: Spreadsheets as a person sees them, beyond what the office add-on
  reads: each cell by its address and number format, each formula after its
  saved result, and the notes on cells. Needs openpyxl.
- `manifests`: Docker Compose and Kubernetes YAML, a passage for each service
  and object: its image, ports, volumes, mounts, routes and selectors, and
  environments, ConfigMaps and Secrets by name, never value. Needs PyYAML.
- `record-sql`: SQL straight over your record, in place: its rows, and each
  passage a bite served, as two tables in DuckDB's memory, the chain checked
  first and DuckDB's way out to files, databases and the network locked shut
  before your SQL runs. Needs DuckDB, floored at 1.1.1, the first with a
  wheel for Python 3.13.
- `dialect`: The words you use far more than the world does, from your files
  against wordfreq's counts: those the world doesn't have, and those you use
  far beyond its rate; a file's codes in capitals left out. Needs wordfreq,
  floored at 3.1.0, the first that doesn't import pkg_resources.
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
