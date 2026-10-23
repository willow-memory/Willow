<!-- willow-addon
section: Reading more kinds of files
line: Obsidian and Logseq vaults, with [[links]] and #tags kept and backlinks listed.
source: new
added: 2026-10-23
-->
# notes

An Obsidian or Logseq vault, written out as plain text beside it, so the kernel can find what a note says, links to and is tagged with.

    python adapters/stdlib/notes/notes.py mirror --from FOLDER --to MIRROR

    wrote 12 files to MIRROR; skipped 1

Each .md note becomes MIRROR/<same path>.txt: daily/2024-03-03.md becomes MIRROR/daily/2024-03-03.md.txt. Folders whose name starts with a dot, such as .obsidian and .trash, are not walked.

What changes:

- **Links.** A wikilink becomes the words a reader sees: its shown text if it has one, else the note's name. A link to a heading is the note's name.

      [[Budget Sheet|the July allowance]]  becomes  the July allowance
      [[Budget Sheet]]                     becomes  Budget Sheet

- **Tags.** #tags in the text, a front-matter tags list (a YAML list or a comma list) and Logseq tags:: properties are collected into one line at the top of the note, such as tags: garden, Ideas, writing.
- **Front matter** is removed, except its tags and a date or created value that is an ISO date, which is written at the top as date: 2024-03-03.
- **Logseq** leading "- " bullets and id:: lines are dropped, and the indentation in front of a bullet goes with it.
- **Backlinks.** The end of each note has linked from: (the notes that link to it) and links to: (the notes it links to). Names are file names without .md, matched without regard to case, and a note's link to itself is not counted. A note with none says so (linked from: none): absence is recorded, not left out.
- **Everything else** is kept as written. Lines inside a code fence are not touched at all.

Running it again adds and overwrites mirror files. It does not remove a mirror file whose note has since been deleted.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused. A refusal names what is wrong: FOLDER is not a folder, or MIRROR is inside FOLDER (or FOLDER inside MIRROR).

**Uses:** the kernel's exit codes, from `kernel.py`. The mirror is plain text, so the kernel reads it like any other folder. Its tests run the kernel's `init` and `bite` on a mirror.

**Never:** writes inside your folder, changes an original, or goes online. A file that is not UTF-8 text, or holds a NUL byte, is skipped and counted, not read.
