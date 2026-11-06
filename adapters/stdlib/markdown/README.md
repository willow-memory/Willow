<!-- willow-addon
section: Reading more kinds of files
line: Any Markdown file as the text it shows, line for line, with no word the file doesn't hold.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
output: mirror
reads: .md, .markdown
-->
# markdown

Your Markdown notes and documents, as the text they show.

    python adapters/stdlib/markdown/markdown.py mirror --from FOLDER --to MIRROR

The kernel already reads a .md file, but it reads it raw: the pipes of a
table, the stars round a bold word, a link's whole address, a heading's hashes.
The mirror is the same file with the markup taken off. It has the same number
of lines as the source, and each line is the source's line, so a passage found
in the mirror is on that same line of the .md file:

    | APMA | passed | 2024-02-09 | 71% |    APMA; passed; 2024-02-09; 71%
    ## Tomatoes                             Tomatoes
    - [x] pay the **gas** bill              - [x] pay the gas bill
    See [the shop](https://shop.example).   See the shop (https://shop.example).

| In the file | In the mirror |
|---|---|
| front matter (YAML between `---` lines, TOML between `+++` lines) | its values, quotes and list brackets off; the keys and the fence lines blank |
| a list under a front-matter key | joined onto the key's line when it runs to the end of the block, so the block stays one passage; else each item on its own line |
| a heading, `#` or underlined with `===` or `---` | its text; the underline blank |
| a table | the header row once, moved down onto the separator's line so it heads the passage that holds the rows; each body row as its cells joined by "; ", empty cells left out |
| bold, italic, struck-through text, code backticks | the words without the marks; never an underscore inside a word, as in snake_case |
| a link | its text, with the address after it in brackets when it goes outside the folder; a link to a file in the folder is only its text |
| an image | its alt text |
| a reference link, an autolink, a wikilink or an embed | the text it shows; a reference's definition line blank |
| HTML tags, entities and comments | tags and comments off, entities as their characters |
| a quote, a list, a task | the quote marks off; a list item as `- ` (a numbered one keeps its number); a task keeps its box as written |
| a fenced code block | kept as written; its fence lines blank |
| a footnote | its marker dropped; its definition as its label and text, `1: text` |
| a backslash escape, a hard break | the character; the trailing backslash dropped |

**No word the file doesn't hold.** The kernel serves a passage holding half a
question's words, so for a two-word question one word is enough. A word
written into passage after passage ("done", "note", a heading repeated above
each section) would answer a question about something the folder doesn't
hold. So the mirror adds none, and drops front matter's keys: date and tags
head every daily note, and the raw folder serves those notes for
"volcano tags"; the mirror serves nothing. A table's header is written once,
never on each row, so "what mark did I get on APMA" lands on the passage
that starts with the header, as in the raw file. A table longer than one
passage (500 characters) loses its header in the passages after the first.

Each file (.md or .markdown) is written to MIRROR at the same relative path
with .txt added. Point the kernel at MIRROR in place of the raw folder:
`kernel.py init --pile MIRROR`. FOLDER is only read: hidden folders and files
are skipped, and nothing is written inside it. A file that can't be read, or
that holds no text once read, is skipped and counted, never a crash:

    wrote 278 files to MIRROR; skipped 0

**What it changes in answers.** On the four demo lives' 278 .md files the
answers are the same passages as from the raw files, now without their
markup. On this repository's own docs a table row reads as its cells
("what did odile ask about the van" gets `N6 the van; found, unasked; …`),
and "what is the floor for duckdb" is missed, as in the raw file: that row
sits past the first passage of its table, away from the Floor header. An HTML comment is gone from the mirror, and with it anything said
only there: the header of a card like this one, so "what does the bank add-on
read" no longer finds the bank card's first lines.

**Not the notes add-on.** [notes](../notes/README.md) reads an Obsidian or
Logseq vault as a vault: it collects tags, drops Logseq bullets and lists each
note's backlinks at its end. This reads any Markdown file, line for line, and
adds nothing that isn't on that line.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Where each passage came from** is in a hidden map beside its mirror,
`MIRROR/.places/<same path>.txt.json`, which the kernel never reads: each
passage's line, which is the source's own, as
[the mirror contract](../ci/README.md#the-mirror-contract) says. A table's first
passage, its header moved onto the separator's line, is on both lines.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
