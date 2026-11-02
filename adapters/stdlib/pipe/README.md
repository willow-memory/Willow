<!-- willow-addon
section: Ways to use it
line: Questions in on standard input, answers out one per line: JSON lines, or file:line: text for grep and fzf.
source: box
added: 2026-10-24
writes: record
network: none
-->
# pipe

Willow for the command line: questions in, one answer a line out, so any
script, shell or editor can use it.

    printf 'when is the dentist\nwho fixed the roof\n' \
        | python adapters/stdlib/pipe/pipe.py --box DIR
    echo "bus times" | python adapters/stdlib/pipe/pipe.py --box DIR --grep | fzf
    python adapters/stdlib/pipe/pipe.py --box DIR --grep "bus times"

Questions come one a line on standard input, or as arguments, which an
editor's task can pass when it can't type into standard input.

| Output | What each line is |
|---|---|
| JSON lines (the default) | `{"question": ..., "exit": 0, ...}`, the kernel's bite for one question, so `jq` can read it |
| `--grep` | `path:line: text`, one passage a line with its file's full path, the way grep prints a match. fzf, Vim's quickfix list, Emacs's compilation buffer and an editor's problem list all jump to it. An answer you approved is `approved: text`. |

The exit code is the worst of the questions': 2 if the kernel refused one,
42 if one found nothing, else 0, so a script can act on it without reading
the words. Blank lines are skipped.

**Source:** grep's own output format, over what the box already has: the
kernel's bite, one question at a time.

**Uses:** the kernel's `main` (its own bite, so each question is on the
record as if you'd typed it, and `verify` holds).

**Never:** approves, reads your key, changes what's served, or goes online.
A refusal comes out as the kernel's own words.
