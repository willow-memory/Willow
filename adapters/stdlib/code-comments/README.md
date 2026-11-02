<!-- willow-addon
section: Reading more kinds of files
line: A codebase's comments and docstrings as passages, cited by file and line.
source: new
added: 2026-10-29
writes: to
network: none
-->
# code-comments

Your code's comments and docstrings, searchable and cited by the source's own line numbers.

    python adapters/stdlib/code-comments/code_comments.py mirror --from FOLDER --to MIRROR

Each source file is written as a file of **the same number of lines**: line N holds
the comment text that was on line N of the source and is blank where there was
none. The kernel cites a passage by file and line, so a hit in the mirror is the
source's own line.

    A cache of parsed answers, kept for a minute.

    The seconds an entry lives before it is parsed again.

Python's `#` comments and docstrings are found with the language's own
tokenizer and parser, so a `#` in a string is not a comment. C, C++, Java,
JavaScript, TypeScript, Go, Rust, C#, Kotlin, Swift and PHP are read for `//`,
`///` and `/* ... */`, stepping over strings, template strings and character
literals; shell and Ruby for `#` (a `#!` line is not a comment). The comment
marks are taken off. A file with no comment, or a Python file that does not
parse, is skipped and counted.

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
