<!-- willow-addon
section: Ways to use it
line: An llms.txt for your folder, written from what's actually in it to the spec's version 2, and any llms.txt you saved checked against that spec.
source: new
added: 2026-10-29
writes: to
network: none
-->
# llms-txt

An llms.txt for your folder, and a check of one you have.

llms.txt is a Markdown file, put at the top of a site or a folder, that tells a
language model what is there and where to read it (the format described at
llmstxt.org): a title, a one-line summary, and lists of links with a note on
each. This writes one from what is actually in a folder and checks one against
the format.

    python adapters/stdlib/llms-txt/llms_txt.py write --from FOLDER --to FILE [--base URL] [--title TEXT] [--summary TEXT]
    python adapters/stdlib/llms-txt/llms_txt.py check FILE

`write` lists only what it finds:

    # notes

    > 14 files from notes: text and Markdown, listed by folder.

    ## garden

    - [Tomatoes](https://example.org/garden/tomatoes.md): Tomatoes want six hours of sun.

    ## Optional

    - [Archive log](https://example.org/archive/log.txt): older entries, 120 KB

| Part | From |
|---|---|
| title | the folder's name, or `--title` |
| summary | how many files there are, or `--summary` |
| a section | each folder at the top of FOLDER; files loose at the top are "Files" |
| a link's text | the file's first Markdown heading, else its file name |
| a link's note | the file's first line of prose outside a code block, cut at 100 characters |
| "Optional" | every file over 50 KB, with its size: what can be skipped when there is little room |
| the link | `--base URL` and the path, percent-encoded, or just the path |

Only text files are listed (UTF-8, no NUL byte); hidden files and folders are
left out. Nothing is invented: a file with no prose has no note.

`check` reads an llms.txt and says where it departs, by line:

    llms.txt:1  the file must begin with a "# " title
    llms.txt:7  a list item should be a link with a note after ": "

It checks one title, first; a summary after it; no heading but a section
after the title; every section a list of links, each a dash, bracketed text and a
parenthesised address, with an optional note; links with a scheme (a relative link is said, since it works only
beside the file); "Optional" last; no empty section; no tabs.

`write` reads FOLDER and writes only FILE, once, readable only by you, never
over a file that exists, the same bytes for the same folder. `check` only reads.

Exit codes, the kernel's: 0 written, or checked and clean; 42 `check` found a
departure, or `write` found nothing to list (nothing written); 2 refused.

**What it doesn't do:** know every version of the format. It follows the
llmstxt.org description (title, summary, sections, Optional); a rule added since
is not checked.

**Uses:** the kernel's `SNIFF` limit for telling text from binary.

**Never:** changes the folder, goes online, or writes anywhere but FILE.
