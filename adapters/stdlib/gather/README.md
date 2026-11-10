<!-- willow-addon
section: Reading more kinds of files
line: Folders and files you name, copied into your pile under a name, only the kinds you keep, never a key or a file too big to read.
source: new
added: 2026-11-10
version: 0.1.0
writes: to
network: none
role: makes
output: report
-->
# gather

Folders and files you name, copied into your pile under a name, only the kinds you keep, never a key or a file too big to read.

    python adapters/stdlib/gather/gather.py --from PATH [--from PATH ...] --to FOLDER
        [--keep .py,.md] [--skip tests,data] [--json]

    gather: populated, 148 files copied from 3 places, 212 left out
      panes                61 files
      widgets              74 files
      app.py               1 file
    ## left out
      not a kind you keep  170 files
      a name you skip      41 files
      looks like a key     1 file

A pile is the folder the kernel reads. Often the files you want in it live
in several places: two folders of a project, a file beside them, notes kept
somewhere else. This makes one pile from the places you name. Each folder
goes in under its own name, each single file goes straight in. Your places
are only read; nothing in them is changed.

## What goes in

- `--from` is a place to copy: a folder or one file. Give it once for each
  place.
- `--to` is the folder they are copied into. It is made if it isn't there.
- `--keep` is the file endings that go in, with or without the dot, in
  capitals or not. Give none and every kind goes in. A file you name by hand
  goes in whatever its ending: you asked for that one.
- `--skip` is names left out, a folder's or a file's, with `*` standing for
  anything: a skip of `test_*` leaves out every file whose name starts that
  way. A folder you skip is not looked into, so its files are not counted.

## What never goes in

Whatever you ask for, these stay out:

- **A file that looks like a key.** One whose name ends in .key, .pem or
  .p12, starts with .env, id_rsa or id_ed25519, or holds the word "secret".
  A pile gets indexed, searched and sometimes shared, and a password or a
  private key should never be carried along by accident. It goes by the name
  alone: the file is not opened.
- **A file over 1 MB.** The kernel wouldn't read it, so it would only take
  up room.
- **Hidden folders** (a name starting with a dot, such as .git) **and the
  folders no one reads**: node_modules, venv, __pycache__, dist and build.
  They hold tools and leftovers, not your work.
- **Links.** A shortcut to a file or folder somewhere else is not followed,
  so nothing outside the places you named comes in.

## What it prints

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares. The first line counts what was copied, and what was
left out, removed or not found. Then a row for each place, with how many
files came from it. Under "left out", a row for each reason with how many
files; under "not there", a row for each place you named that it couldn't
find. `--json` gives the same report as one JSON object.

## Run it again to refresh

Run the same line again when your files have changed. A changed file is
copied again, a new one is added, and a file that has gone from a folder you
named goes from its copy too, with any folder that leaves empty:

    gather: populated, 147 files copied from 3 places, 212 left out, 1 removed as gone

It removes only inside the folder copies it made. Anything else you keep in
the `--to` folder is left alone, and so is the copy of a single file whose
source has gone: that is said as a place not there, for you to decide.

## What is refused

Each of these stops before anything is written, with the reason:

- A command line it can't read: no `--from`, no `--to`, or a word it
  doesn't know.
- A `--to` inside a place you named, or a place you named inside `--to`.
  A copy inside its own source would copy itself.
- Two places with the same name. Both would go to one spot and one would
  overwrite the other. Give each its own `--to`.

## In a stack

In a stack file, write one line for each place, at the top. The list of what
a project is made of is then the first thing anyone reads in its stack:

    ## what this project is made of
    - gather -- --from ~/code/app/panes --to ~/piles/app --keep .py,.md
    - gather -- --from ~/code/app/widgets --to ~/piles/app --keep .py,.md --skip tests
    - gather -- --from ~/code/app/app.py --to ~/piles/app

Lines that share a `--to` build one pile between them. The
[stack](../stack/) add-on runs them, and each prints its own report.

**Exit codes:** 0 copied; 42 a place you named isn't there (the rest is
still copied), or nothing was copied, and it waits on you; 2 refused.

**Uses:** nothing of the kernel's but its exit codes. It reads no box and no
record.

**Never:** writes outside `--to`, changes a place you named, or copies a
file that looks like a key.
