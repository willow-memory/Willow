<!-- willow-addon
section: Assistants
line: A PreToolUse hook that refuses reading by hand a file one of your boxes holds, until that box has been asked this session.
source: new
added: 2026-11-19
version: 0.1.0
writes: record
network: none
role: guards
tags: hooks
uses: hook-shell, stack
-->
# hook-ask-first

A PreToolUse hook that refuses reading by hand a file a box already holds,
until that box has been asked this session.

```
python adapters/stdlib/hook-ask-first/hook_ask_first.py run --boxes FILE
python adapters/stdlib/hook-ask-first/hook_ask_first.py check --boxes FILE PATH [PATH ...]
```

**Why it is here.** An assistant given a project with boxes and stacks
builds them, runs them, and then reads the files by hand anyway: `tail` on a
log, Read on a document, `grep` through a folder a reader already turned into
passages. The box is never asked, so nothing it was built for is tried, and
the person who built it learns nothing about whether it works. Asked in
words, an assistant agrees and goes on doing it. This is that rule held by
code.

**What a box holds** is read from the stacks beside it, never from a list
kept by hand. FILE is a list of boxes, the one [boxes-here](../boxes-here/)
keeps. For each:

- its pile, the folder the box's own settings name;
- every folder a step of a stack beside the box reads into the pile: a step
  whose `--to` is in the pile holds each of its `--from` folders, and so does
  a step that copies into one of those.

So adding a reader step to a stack is all it takes for its folder to be
held; taking the step out lets it go.

**`run`** reads what the assistant is about to do (the JSON Claude Code
sends on standard input) and finds the files it would read by hand:

| Tool | What counts as read by hand |
|---|---|
| Read, NotebookRead | the file named |
| Grep | the path searched, when one is given |
| Bash | each file named to a program that prints files (`cat`, `head`, `tail`, `grep`, `sed`, `awk`, `cut`, `wc`, `jq` and their like), the command split as the shell splits it by [hook-shell](../hook-shell/), a `cd` and a `P=...` followed |
| anything else | nothing; allowed |

For a file some box holds, that box's record is looked at:

- **the first time in a session**, a `hook-ask-first` row is written (the
  folder held and the session, never a word of a file) and the read is
  refused;
- **until the box is asked**, it stays refused;
- **once the record has an ask** (a `bite` row) after that row, the session
  reads freely what that box holds.

Each box is its own: asking one opens nothing of another.

```
blocked: ask first  /home/you/project/kit/docs/protocol.md
  the box at /home/you/project/parts/kit/box holds it: the markdown step of stack.md reads it into the pile (markdown: Any Markdown file as the text it shows, line for line, with no word the file doesn't hold.)
  ask the box, then read the place it names:  python /home/you/project/ask.py --part kit "your question"
```

The step's add-on is named with its own card's line, so the refusal says
what would have answered.

**It fails open.** A list that isn't there, a box that has moved, a record
that doesn't verify, a command that can't be split, input that isn't a call:
each is let through with a line on standard error. A PreToolUse hook that
exits 2 on its own trouble locks the assistant out of the machine, and this
one would rather miss a read than do that.

**`check`** is the same look for a person: for each PATH, the box that
holds it and why, how many asks that box's record has, and how to ask; or
that no box listed holds it.

To use it, put the `run` line where the assistant's settings name a
PreToolUse hook, matching Read, Grep and Bash.

**What it misses, said rather than hidden.** A file read by a program it
doesn't know prints files (a one-line `python -c`, an editor) goes by. So
does a search with no path, which searches the folder the assistant is in.
It can't tell a good question from an idle one: any ask opens the box for
the session. And it knows nothing of a box that is not on the list.

Exit codes, the kernel's: `run` 0 allowed, 2 a read refused; `check` 0 no
path is held, 42 one is (its box is the place to ask), 2 a bad command line
or a FILE that isn't a list of boxes.

**Uses:** the kernel's `read`, `append`, `now` and exit codes; the
[stack](../stack/) add-on's `parse_stack` and `resolve`; hook-shell's
`split`.

**Never:** reads the key; writes a word of a file onto the record; refuses
anything but a read by hand of a file a listed box holds; blocks a tool
because of its own trouble.
