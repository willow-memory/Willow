<!-- willow-addon
section: Reading more kinds of files
line: OPML feed and podcast lists, a line per feed under its folder, and outliner exports as indented items with their notes.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
reads: .opml, .xml
-->
# opml

Your feed reader's and podcast app's subscriptions, and your outlines from
OmniOutliner, Workflowy, Dynalist, Logseq or Bike, as lines you can ask about.

    python adapters/stdlib/opml/opml.py mirror --from FOLDER --to MIRROR

It reads .opml files, and .xml files whose root is `<opml>`; any other .xml
(a plist, an RSS feed) is left alone and not counted. Only the file's own
words are written, never a label of this reader's: a word in passage after
passage would answer a question about something the file doesn't hold. The
cost: "which podcasts do I follow" finds a list only when the file says
"podcast" itself, in its title or a folder's name.

The head's title, dates and owner come first, as written, in a passage of
their own. A **feed list** is one line per feed, its title and its feed's and
site's addresses, and each folder is a passage that starts with its name:

    Gardening
    Hedgerow Diaries <https://hedgerow.example.org/feed.xml> <https://hedgerow.example.org/>
    The Seed Exchange <https://seeds.example.com/rss> <https://seeds.example.com>

A podcast with its episodes (an Overcast export) is a passage of its own:
the podcast's line, then each episode with its date as written and its audio's
address. One too long for a passage is cut, each piece starting again with the
podcast's line.

An **outline** is each item on its own line, indented by depth with "- ", and
its note under it; a link's address follows in angle brackets and a created
date in round ones, as written; a
completed item is ticked "✓". A top-level item with children is its own
passage, set apart by blank lines, so what you noted under "Garden plans" is
found together:

    - Garden plans
      Allotment plot 14, by the water butts.
      - Spring beds
        - Tomatoes
          Sungold and San Marzano, against the south fence.
        - ✓ Broad beans

One longer than a kernel passage (500 characters) is cut at its children, those
that fit staying together, and a long note is wrapped at words, so no line is
cut short. A cut piece doesn't repeat the items above it, so a question that
leans on a folder or a parent item's name finds only the piece that holds it.

**A DTD is never read.** A file that declares a DTD or an entity is skipped
and counted, and named on stderr, before it is parsed, so an entity bomb (a
"billion laughs") is never expanded.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read, or has nothing in its body, is
skipped and counted, never a crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and its
passage size (`MAX_CHUNK`); Python's standard library (`xml.etree`) for the
format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, expands an entity, or goes online.
