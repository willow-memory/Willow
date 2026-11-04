<!-- willow-addon
section: Reading more kinds of files
line: Pages Safari saved as .webarchive, as their readable text with the address they came from, and their frames' text after them.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
reads: .webarchive
uses: web-pages
-->
# webarchive

Pages Safari saved as .webarchive, as the words they show, read the same way
[web-pages](../web-pages/) reads a page saved as .html.

    python adapters/stdlib/webarchive/webarchive.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

Safari's "Web Archive" save is a property list, not a page: the page's own
bytes sit inside it beside its pictures, styles and scripts, so the kernel
can't read it at all. For each .webarchive under FOLDER this writes
`MIRROR/<same path>.txt`:

    address: https://example.org/roof

    Roof repair

    The roofer comes on Thursday.

    https://maps.example/embed

    12 Harbour Lane, Leeds.

the same bytes web-pages writes for that page saved as .html: where it came
from, its title, then its blocks (paragraphs, headings, list items), one
paragraph each, so an answer lands on the paragraph that says it. After the
page, each frame it holds (an embedded map, a comment box) comes under the
frame's own address, alone on its line, in the order the archive keeps them;
a frame that isn't text gives its type instead (`<address>
(application/pdf)`). The pictures, styles and scripts are left out.

**No word of its own above each frame.** The kernel serves a passage holding
half a question's words, so a label written over every frame would answer
"volcano frame" with a frame's address. The one label it writes is web-pages'
`address:`, once a file, at the top; "volcano address" is served those lines,
and the same word lets "address of the garden page" land on the right one.

**Where it came from** is the address Safari kept for the page; if it kept
none, the page's canonical link or og:url, as web-pages finds them; else
`address: not in the file`, never a guess.

**Its charset:** the one Safari names for the page, else the one the
page's own `<meta charset>` names, else UTF-8 with what doesn't read as
UTF-8 replaced, so a page is never dropped for one bad byte.

**A page saved as plain text** (a .txt Safari opened) comes out as its
paragraphs, split at blank lines, each line kept (a list stays a list),
with nothing in it read as markup.

**Skipped and counted:** a file that isn't a property list, a property list
that isn't a web archive, and an archive whose page isn't HTML or plain text,
such as a PDF or picture Safari saved as an archive:

    wrote 2 files to MIRROR; skipped 1

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER; the mirror and the
folder can't be inside each other; the same folder gives the same bytes.

**What it was built on:** no Safari archive was at hand, and Safari doesn't
run on the machine it was built on, so its tests build archives the way
Safari writes them (a binary property list with the real keys, a frame,
pictures and styles). Built the same way around willow's own `ui/page.html`
and three HTML pages found on that machine, each came out byte for byte as
web-pages reads the page saved as .html; the demo folders hold no web pages.

**Can't:** run a page's scripts, so text a page only draws with JavaScript
isn't there; or keep its pictures. A page's menus and footers come out as
paragraphs too, as they do in web-pages.

**Exit codes:** 0 wrote at least one file; 42 nothing to read; 2 refused
(FOLDER is not a folder, or the two are inside one another).

**Uses:** web-pages' `as_text` and its charset pattern, so the page reads
exactly as web-pages reads it; the kernel's exit codes; Python's `plistlib`
for the archive.

**Never:** writes inside your folder, changes an original, or goes online.
