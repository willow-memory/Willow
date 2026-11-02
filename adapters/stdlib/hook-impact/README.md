<!-- willow-addon
section: Assistants
line: Before an edit, a hook hands the assistant every place in your files that names what it's about to change, by file and line.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: hooks
uses: habits
-->
# hook-impact

Before an assistant edits a file, tells it every place in your files that
names that file, so a note that says "see kernel.py for the rules" is not left
saying something the edit made untrue.

```
python adapters/stdlib/hook-impact/hook_impact.py run --box DIR
python adapters/stdlib/hook-impact/hook_impact.py check --box DIR FILE
```

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input). For a Write,
Edit, MultiEdit or notebook edit of a file, it looks through the box's files
for the lines that name that file, and prints the JSON a PreToolUse hook reads,
with these sentences as its `additionalContext`:

```
Before editing kernel.py, these places in the person's files name it:
  README.md:1  kernel.py is the one file that writes a box
  docs/notes.md:2  see kernel.py for the rules
Check they still say what is true after the edit.
```

It allows the call: it hands over facts and never blocks. An edit it finds
nothing for, any other tool (a Read, a search, a command), and a call it can't
read all print nothing.

| What counts as naming a file | What doesn't |
|---|---|
| its name as a whole word with its extension, case as written: `kernel.py` in "see kernel.py", "(kernel.py)", "kernel.py," | a longer name that holds it (kernel.pyc, my-kernel.py, kernel.py-old), or the same letters in another case; the file's own lines |

Ten places are listed, each cut at a hundred characters, then a count. A
relative path is read against the call's own `cwd` when it sends one. A
name that many files share (a README, an init file) names many places:
that is what the count is for.

`check` is the same look for a person: the places that name FILE, one to a
line, and exit 42 when there are some.

It reads the box's folder only, through the kernel's `chunks` and `config`
(and [habits](../habits/)' `file_lines` to put a file's passages back
together); it never reads the key and writes nothing, not even the row
`kernel.py out` appends. Exit codes: 0 allowed (or `check` found nothing); 42
`check` found places; 2 refused (a bad command line, not a box). A hook should
fail open here: a refusal prints its reason on standard error and adds
nothing.

**Never:** blocks an edit; reads the key; writes anything.
