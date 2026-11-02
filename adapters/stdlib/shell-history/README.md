<!-- willow-addon
section: Reading more kinds of files
line: Your bash, zsh and fish history: what you ran, and when the shell recorded it.
source: new
added: 2026-10-31
writes: to
network: none
-->
# shell-history

Your shell history as plain text the kernel reads: each command one line
with the time its shell recorded it, so "when did I last rsync the photos"
finds the day you ran it.

```
python adapters/stdlib/shell-history/shell_history.py mirror --from FOLDER --to MIRROR

2024-03-03 10:15:00 UTC  git push
2024-03-03 10:16:40 UTC  rsync -a photos/ /mnt/backup/
```

**Copy your history in without its dot.** Hidden files are never read, so
`cp ~/.bash_history FOLDER/bash_history`, and the same for `zsh_history`
and fish's `~/.local/share/fish/fish_history`. A file is known by its name,
never by guessing at what it holds: a name starting `bash_history`,
`zsh_history`, `histfile` (zsh) or `fish_history`. Anything else is left
alone.

**Each shell its own way.** bash dates a command by the `#1709460900` line
over it, when `HISTTIMEFORMAT` was set; zsh's extended history by
`: 1709460900:0;`, a line ending in a backslash going on to the next; fish
by the `when:` under each `- cmd:`. zsh's own escaping of bytes past ASCII
is undone, and fish's `\n` and `\\` are.

**A time is the shell's, in UTC.** Times are written in UTC so the same
file gives the same bytes on any machine. A command the shell kept no time
for (plain bash or zsh history, or one before the first stamp) is written
bare, never given a time it doesn't have. Commands keep the order the shell
wrote them; a day's commands are one paragraph, and a multi-line command
keeps its lines.

Each history is written to MIRROR at the same relative path with .txt
added: `<folder>/bash_history` becomes `MIRROR/<folder>/bash_history.txt`.
FOLDER is only read: originals are never modified and nothing is written
inside it. A file that cannot be read, or holds no command, is skipped and
counted, never a crash.

It keeps [the readers' contract](../ci/test_contract.py): the same folder
gives the same bytes, and `wrote N files to MIRROR; skipped M` says what
happened. Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2
refused (FOLDER is not a folder, or MIRROR and FOLDER are inside one
another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of what you ran. A history holds whatever you typed, passwords
pasted on a command line included: read the mirror before you hand it to a
model.

**Uses:** the kernel's exit codes; the mirror is for `chunks` to read.

**Never:** changes your files; writes outside MIRROR; reads a hidden file;
guesses a file's shell from what it holds; gives a command a time its shell
didn't record.
