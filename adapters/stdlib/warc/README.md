<!-- willow-addon
section: Reading more kinds of files
line: WARC web archives (Webrecorder, Heritrix, the Internet Archive) read without unpacking: each page's text with its address and capture time.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
reads: .warc, .wacz
-->
# warc

The pages in your web archives, searchable by what they said, where they
were and when they were captured.

    python adapters/stdlib/warc/warc.py mirror --from FOLDER --to MIRROR

A WARC file is what Heritrix, wget's `--warc-file`, the Internet Archive and
Webrecorder (ArchiveWeb.page, Browsertrix, pywb) save a crawl in: every
request, response and note of a session, one record after another. For each
.warc, .warc.gz or .wacz under FOLDER this writes `MIRROR/<same path>.txt`,
each captured page a passage of its own:

    2024-03-02 08:15 https://example.org/roof
    The roof & gutters
    Our roof

    The roof was fixed on Tuesday by Kowalski.

    The gutters are next.

The first line is the time it was captured (WARC-Date, which is UTC, to
the minute) and its address (WARC-Target-URI); the second is the page's
title, when it has one; then its paragraphs, one per paragraph, heading or
list item, a blank line between them (a first heading that only repeats
the title is left out). The same address captured twice is two passages,
each under its own date.

**A paragraph doesn't carry the address again.** The kernel cuts a long
page into many passages, so only the first holds the address. The heading
is above them in the same file, which is where the kernel already looks for
a passage's date, and the kernel cites the file and line. A tag on every
paragraph would make every paragraph of a site hold the site's words, so a
question naming the site and one other word would be held by all of them.

**Nothing but what the archive holds.** No word the reader makes up goes
into a passage: no `(no title)`, no stand-in for a missing address or date,
no count of what was cut. A word written into passage after passage would
hold half of any two-word question, so a question about something the
archive never had would be answered with an unrelated page; a test asks
each such word beside one the folder lacks and is served nothing. What does
repeat is the archive's own: each page's address and capture time, which
are what you ask by. Their cost: a short question naming a site, such as
"what did example.org say about volcanoes", is held by that site's
headings even when no page mentions volcanoes.

**Read without unpacking.** A .warc.gz is read through gzip, whether each
record is its own gzip member (as crawlers write it) or the whole file is
one; a .wacz, Webrecorder's zip, through zipfile, the WARCs in its archive folder in
name order, into one mirror file. Records are read by their Content-Length,
never by looking for the blank line after one, so a page that holds a blank
line, or the words of a WARC header, is still one page.

| Read | Passed over, and counted |
|---|---|
| `response` records holding an HTTP response with a 2xx status | `warcinfo`, `request`, `metadata`, `revisit` and `conversion` records (a revisit only points at another capture) |
| `resource` records (Webrecorder's), which have no HTTP envelope | a status that isn't 2xx: redirects, not found |
| HTML, as the kernel's `html_text` reads a page, each block tag a paragraph and each tag's attributes taken off first (Wikipedia's hold `<!--` and `>` inside quotes) | images, scripts, styles and every other type that isn't HTML or plain text |
| plain text as it is | a body sent as br (Brotli), which the standard library can't read |
| a body sent chunked, gzipped or deflated | a record over 16 MB, or a body whose chunks or gzip are broken |

**Its charset** is the one Content-Type names, else the one the page's own
meta tag names in its first 4,096 bytes, else UTF-8, with any byte that
can't be read replaced.

**What was left out** of each file is said as it is read, so a file that
held no pages says why:

    crawl.warc.gz: 2 pages; left out 1 request, 1 revisit, 1 warcinfo
    wrote 1 files to MIRROR; skipped 0

**Capped for the kernel.** A long paragraph is wrapped at 200 characters,
so the kernel can cut it into passages of its own size. A page's text past
20,000 characters is left out, and the file's printed line counts it
(`1 cut short`), not the mirror.
A mirror file that would pass the kernel's 1,000,000-byte limit, which the
kernel won't read, goes on in `<same path>.2.txt`, `<same path>.3.txt` and so on, a
page never split between two.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file is skipped and counted only when no page in it
can be read (not a WARC, a broken gzip or zip, only revisits); one that
breaks part way keeps the pages before the break.

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Can't:** run a page's scripts, so text a page only draws with JavaScript
isn't there (a .wacz of a page Webrecorder rendered holds the requests the
scripts made, which are read only when they are HTML or plain text); read
the older ARC format; or keep pictures. A page's menus and footers come out
as paragraphs too.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's `html_text`, `MAX_FILE` and exit codes (`ALIVE`,
`ESCALATE`, `REFUSED`); Python's standard library (gzip, zlib, zipfile) for
the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
