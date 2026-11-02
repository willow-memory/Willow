<!-- willow-addon
section: Reading more kinds of files
line: Any Markdown file as the text it shows, line for line, with a table's rows named by their columns.
source: new
added: 2026-11-02
writes: to
network: none
-->
# markdown

Your Markdown notes and documents, as the text they show.

    python adapters/stdlib/markdown/markdown.py mirror --from FOLDER --to MIRROR

The kernel already reads a .md file, but it reads it raw: the pipes of a
table, the stars round a bold word, a link's whole address, a heading's hashes.
The mirror is the same file with the markup taken off and a little put back
where the markup carried meaning. It has the same number of lines as the
source, and each line is the source's line, so a passage found in the mirror is
on that same line of the .md file:

    | APMA | passed | 2024-02-09 | 71% |    unit: APMA; status: passed; date: 2024-02-09; mark: 71%
    ## Tomatoes                             Garden › Tomatoes
    - [x] pay the **gas** bill              - done: pay the gas bill
    See [the shop](https://shop.example).   See the shop (https://shop.example).

| In the file | In the mirror |
|---|---|
| front matter (YAML between `---` lines, TOML between `+++` lines) | each `key: value` kept as `key: value`, quotes and list brackets off; the fence lines blank |
| a list under a front-matter key | joined onto the key's line when it runs to the end of the block; else each item as `key: item`, so the block stays one passage |
| a heading, `#` or underlined with `===` or `---` | its text; the underline blank |
| a heading with its text straight under it | after the headings it sits under, as Garden › Tomatoes |
| a table | the separator row blank; each body row as `header: value; header: value`, empty cells left out; the header row blank once a row names its columns |
| bold, italic, struck-through text, code backticks | the words without the marks; never an underscore inside a word, as in snake_case |
| a link | its text, with the address after it in brackets when it goes outside the folder; a link to a file in the folder is only its text |
| an image | its alt text |
| a reference link, an autolink, a wikilink or an embed | the text it shows; a reference's definition line blank |
| HTML tags, entities and comments | tags and comments off, entities as their characters |
| a quote, a list, a task | the quote marks off; a list item as `- ` (a numbered one keeps its number); a task as `- to do:` or `- done:` |
| a fenced code block | kept as written; its fence lines blank |
| a footnote | its marker dropped; its definition as `note 1: text` |
| a backslash escape, a hard break | the character; the trailing backslash dropped |

A heading is written after the headings above it only when its text runs
straight on under it, so that passage says where it sits (a gift list's
`## Grace` reads gifts › Grace beside the orchid). A heading standing alone
between blank lines is only its own words: on this repository's own docs,
where most headings stand alone, writing the whole path on them made a bare
run of headings outrank the text under them.

Each file (.md or .markdown) is written to MIRROR at the same relative path
with .txt added. Point the kernel at MIRROR in place of the raw folder:
`kernel.py init --pile MIRROR`. FOLDER is only read: hidden folders and files
are skipped, and nothing is written inside it. A file that can't be read, or
that holds no text once read, is skipped and counted, never a crash:

    wrote 278 files to MIRROR; skipped 0

**What it changes in answers.** On the four demo lives' 278 .md files and on
this repository's own docs, a question about a table's row is served the row
with its columns named ("what is the floor for duckdb" gets the row that says
`Floor: duckdb 1.1.1`, where the raw file served three passages without it).
Most answers on the lives are the same passages as before, now without their
markup. An HTML comment is gone from the mirror, and with it anything said
only there: the header of a card like this one.

**Not the notes add-on.** [notes](../notes/README.md) reads an Obsidian or
Logseq vault as a vault: it collects tags, drops Logseq bullets and lists each
note's backlinks at its end. This reads any Markdown file, line for line, and
adds nothing that isn't on that line.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
