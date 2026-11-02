<!-- willow-addon
section: Reading more kinds of files
line: Saved web pages, .html and .mhtml, as their readable text, with the address they came from.
source: new
added: 2026-10-24
writes: to
network: none
uses: clauses
-->
# web-pages

Saved web pages as their readable text, with the address they came from.

    python adapters/stdlib/web-pages/web_pages.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

The kernel reads a web page as the words it shows, but a page saved from a
browser is often one long line of markup, so its paragraphs run together,
and an .mhtml is a whole message of parts the kernel doesn't open. For each
.html, .htm, .mhtml or .mht under FOLDER this writes
`MIRROR/<same path>.txt`:

    address: https://example.org/terms

    Terms

    We keep data.

a first line saying where the page came from, then the page's blocks
(paragraphs, headings, list items), one paragraph each, so an answer lands
on the paragraph that says it.

**Where it came from** is the first of: the `saved from url=` note a
browser writes into an .html it saves (Internet Explorer's Mark of the Web),
except `about:internet`, which marks a zone, not an address; an .mhtml's
`Snapshot-Content-Location`, or its page's `Content-Location`; the page's
canonical link; its `og:url`. A page that says none of these gets
`address: not in the file`, never a guess.

**Its charset:** UTF-8, or the one the page's own `<meta charset>` names
in its first 4,096 bytes. An .mhtml's page is read in the charset its part
names, else the same way: Chrome names none on the part, only in the page.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER; the mirror and the
folder can't be inside each other; the same folder gives the same bytes; a
page it can't read is skipped and counted.

**What it was built for:** the three news reports of
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/),
saved as fetched: each came out as its own paragraphs (220, 336 and 349 of
them), under the address its canonical link gives.

**Which browser saved it:** Chrome and Edge save .mhtml; Firefox saves
only .html, without a saved-from note, so a page Firefox saved gets its
address from the page's canonical link or og:url, if it has one. A "complete"
save puts the page's files in a folder beside it; an .html there (a frame)
is read as a page of its own.

**Can't:** run a page's scripts, so text a page only draws with JavaScript
isn't there; or keep a page's pictures. A page's menus and footers come out
as paragraphs too.

**Exit codes:** 0 wrote at least one file; 42 nothing to read; 2 refused.

**Uses:** the clauses add-on's `blocks_of_html` and `inside`, which read a
page's blocks the kernel's way; the kernel's exit codes; Python's `email`
package for .mhtml.

**Never:** writes inside your folder, changes an original, or goes online.
