<!-- willow-addon
section: Privacy and safety
line: Your documents checked for screen-reader problems: images without descriptions, headings out of order.
source: new
added: 2026-10-27
writes: nothing
network: none
tags: no-install, offline, read-only, privacy
-->
# a11y-check

Your documents read as a screen reader will meet them: every Markdown and
HTML file of your folder, checked for the two things that most often trip
one, each problem with its file and line, for you to fix before you share
the page.

```
python adapters/stdlib/a11y-check/a11y_check.py --box DIR
python adapters/stdlib/a11y-check/a11y_check.py --from FOLDER

notes/trip.md:12   image without a description: ![](beach.jpg)
notes/trip.md:30   heading jumps from h1 to h3: ### Day two
2 problems in 1 of 14 documents
```

**An image without a description.** A Markdown image whose brackets are
empty, and an HTML img tag with no alt attribute at all. An HTML `alt=""`
is left alone: it is the author saying the image is decoration, which
Markdown has no way to say, so an empty bracket is read as a description
not written yet. A raw img tag inside a Markdown file counts too.

**A heading out of order.** One more than a level deeper than the heading
before it (h1 straight to h3), which a screen reader's outline renders as a
hole. A document's first heading may be any level: notes start at h2 on
purpose. Markdown headings are the `#` kind; a line underlined with equals
signs is not read, and said here so the silence isn't a pass.

**What is and isn't a document.** It reads `*.md`, `*.markdown`, `*.html`
and `*.htm` files by their own bytes, never a mirror's text, which has no tags
left to check. Lines inside fenced code blocks are code, not document.
Hidden files and folders are never read. Nothing else is guessed at: link
text, colour and contrast live in the page's styling, outside these files'
say.

On willow's demo folders, Teodora's 119 documents and Bernadette's 159 come
back clean; Odile and Hollis keep no Markdown or HTML at all, and it says
that rather than calling nothing clean.

It only reads, and the same folder gives the same bytes. Exit codes, the
kernel's, as the audits use them: 0 no problems; 42 problems found, or
nothing there to check; 2 refused.

**Uses:** the kernel's `config` and exit codes.

**Never:** changes your files; writes anything, even the record; reads a
hidden file; calls a folder with no documents clean.
