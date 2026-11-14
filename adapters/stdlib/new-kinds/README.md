<!-- willow-addon
section: Reading more kinds of files
line: Kinds of file in your folders that no step of your stack reads yet, each with the readers that took some of them when tried on a few.
source: new
added: 2026-11-14
version: 0.1.0
writes: nothing
network: none
role: tools
output: report
-->
# new-kinds

Kinds of file in your folders that no step of your stack reads yet, each with the readers that took some of them when tried on a few.

    python adapters/stdlib/new-kinds/new_kinds.py --from FOLDER [--from FOLDER]... [--stack STACKFILE] [--leave .EXT[,.EXT]]... [--json]

    new-kinds: populated, 3 kinds no step reads, of 7 in 1 folder: .ics, .docx, .ttf
    ## a reader knows their shape
      .ics   4 files; calendar took 4 of 4
    ## the kernel can't read them
      .docx  22 files; office took 4 of 4
    ## no reader for them yet
      .ttf   140 files; no reader here says it reads them

A stack is set up for the files its folders held then. When a new kind of
file arrives (a GPX from a watch, an export from an app), nothing says so:
the kernel reads it as plain text or skips it, and the reader that would
read it well isn't in the stack. Put this in the stack as a step over the
same folders, and every run says so, until a step reads the kind or you
leave it:

    ## what arrived
    - new-kinds -- --from ~/notes --stack ~/willow-stacks/notes/stack.md --leave .ttf,.pkl

A kind isn't said when a step of STACKFILE is a reader whose card's
`reads` names it, or when `--leave` names it. `--leave` is your word that
a kind is fine as it is; it lives in the stack file, beside the step, so
nothing is remembered anywhere else.

For each other kind, the readers whose cards say they read it are tried.
Each runs its own `mirror --from --to` on copies of up to four of the
kind's files, spread over them in name order, beside a file of the kind
with nothing in it. The copies are in scratch made with `tempfile`, removed
after. A reader that took some of yours and not the nonsense knows their
shape, and is said with how many it took. One that took the nonsense too
reads any file of the kind (json-paths takes any .json): it is named only
beside the rest. The extension alone can't tell a Mastodon outbox from a
Keep note; the reader can.

| Group | A kind |
|---|---|
| a reader knows their shape | the kernel reads as text, and a reader took some as its own |
| the kernel can't read them | is binary, over 1 MB or not UTF-8, with the readers that say they read it and what they took |
| no reader for them yet | the kernel can't read, and no card here says it reads |

A kind the kernel reads as text that no reader knows the shape of is fine
as it is, and isn't a row. Hidden files and folders are skipped, as the
kernel skips them. A reader that needs an install (its card has `needs`)
and took none is said so: "(needs its install)".

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares. `--json` gives the same report as one JSON object.

The canvas ([ui/](../../../ui/)) uses its trial for the "a reader knows
their shape" list on its first page, so the page and the step say the same.

## What it doesn't do

It doesn't add a reader to your stack, or run one over your folders: what
it tries runs on copies, and what they write is thrown away. Only kinds and
counts are said, never a file's name or a line of it. The readers are the
ones beside it in this willow, and only those whose card says `network:
none`. Four files are tried a kind, so a shape held by few files of a big
kind can be missed.

**Refused:** no `--from`; a `--from` that isn't a folder; an option with no
value, or one it doesn't know; a `--leave` kind not written `.ext`; a stack
file that can't be read or names no step.

**Exit codes:** 0 `empty` (every kind is read by a step, read as text, or
left); 42 `populated` (a kind waits on you: add its reader, or leave it);
2 refused.

**Uses:** the kernel's `MAX_FILE` and `SNIFF`, to tell what it reads as
text the way it does.

**Never:** writes outside its own scratch, reads the key, or goes online.
