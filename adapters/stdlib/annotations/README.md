<!-- willow-addon
section: Ways to use it
line: Approved answers as W3C Web Annotations, so any annotation tool can show what your files say about a page.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# annotations

What you approved, as notes an annotation tool can pin to the page.

The W3C Web Annotation Data Model is how annotation tools say "this note is
about that part of that page". This writes each answer you approved as one,
in an annotation page, so a tool that reads it can show what your files say
about a document beside the document.

    python adapters/stdlib/annotations/annotations.py --box DIR --to FILE [--base URL]
    wrote FILE: 2 annotations

| In an annotation | Is |
|---|---|
| body | the answer, as a text body |
| one target for each cited passage | the file as the source, and two selectors: the lines as an RFC 5147 fragment (counted from zero, as that standard counts, so a passage on line 3 is line=2,3), and the passage's own words as a quote, for a tool that can't use the lines |
| created | when you approved it |
| motivation | describing |
| id | a urn made from the suggestion's subject, so the same answer is the same annotation |

With `--base URL` the source is URL followed by the file's path, for files you
publish there; without it, the path as it is in your folder. The path is made
safe as a link, a space as %20.

An approval is exported only while its proof holds under your key (the
kernel's `sealed`, so the key is read there and nowhere here) and its proposal
file still holds the bytes you approved. A cited passage that is no longer in
your files is left off its annotation, since a target that quotes text no
longer there would lie. Both are said on standard error.

FILE is written once, readable only by you, never over a file that exists, and
the same record and folder give the same bytes.

**What it doesn't do:** anchor to a web page's address. It names your files;
a tool that wants a page needs `--base` to say where they are published.

Exit codes, the kernel's: 0 written; 42 written, but an approval or a citation
was left out and waits on you; 2 refused (a record that doesn't verify, a bad
command line).

**Uses:** the kernel's `read`, `sealed`, `standing` and `chunks`.

**Never:** reads the key, changes the box, or writes anywhere but FILE.
