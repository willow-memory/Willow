<!-- willow-addon
section: Reading more kinds of files
line: A MediaWiki XML dump: each page's latest text, with its title and when it changed.
source: new
added: 2026-10-29
writes: to
network: none
-->
# mediawiki

A wiki's export, searchable page by page.

    python adapters/stdlib/mediawiki/mediawiki.py mirror --from FOLDER --to MIRROR

A page is a block: its title and the day of its latest revision, then its text
with the wiki markup taken off.

    page: Tomatoes (changed 2024-03-03)

    Tomatoes want six hours of sun.

Where a page has several revisions, the last in the file is used. Links keep
their shown words (`[[a|b]]` is b), headings lose their equals signs, bold and
italic quotes, templates, comments, references, file and category links go,
and a table cell keeps its text. A redirect is written as "redirect to X". Only
XML that is a MediaWiki export is read (other XML is skipped and counted), and a
file that declares entities, a way to make a small file expand to a huge one,
is not read at all.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
