<!-- willow-addon
section: Finding things
line: Every quote in a document checked against your files: as written, almost (and what it adds, drops or changes), or not there.
source: new
added: 2026-11-01
writes: nothing
network: none
tags: no-install, offline, read-only, search
-->
# quotes

Every quotation in a document, checked against your files at once.

    python adapters/stdlib/quotes/quotes.py --box DIR --in FILE

    as written   policy.txt:1      "We don't show you personalized ads"
    almost       policy.txt:4      "The council met on Monday"  (8 of 9 words)
      changed    Monday -> Tuesday
    not there                      "We sell nothing to anyone"

    3 quotes: 1 as written, 1 almost, 1 not there.

[quote-check](../quote-check/) and [misquote](../misquote/) take one quote
at a time. A report, an article, or a catalog's notes hold dozens. This finds
every quotation in FILE (the words between straight or curly double
quotation marks, on one line, four words or more, each counted once) and
gives each one verdict:

- **as written**: quote-check finds it, verbatim or the same words in the
  same order;
- **almost**: misquote's closest passage holds at least half its words in
  order, and the lines under it say what the quote adds, drops or changes;
- **not there**: no passage holds even half of it.

FILE can be anywhere; only the box's folder is searched.

**What it was built for:** the Almanac's catalog entries record what each
source page said, in quotation marks, when a curator checked it. Fetch the
pages into a folder with [snapshot](../snapshot/), point a box at it, and run
this on the entry: every quote that has drifted or was never there shows up.

**Exit codes:** 0 every quotation is there as written, or FILE holds none; 42
one isn't; 2 refused (no box, or FILE isn't readable UTF-8 text).

**Uses:** quote-check's `find`, misquote's `closest` and `tokens`, and the
kernel's `chunks`, `words` and `config`.

**Never:** writes anything, or goes online.
