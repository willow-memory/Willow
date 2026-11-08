# Design note: the two made lists, for reading and for finding

**Status: notes, taken 2026-11-08, to come back to. Nothing here is built.**
FILES.md and ADDONS.md are made by scripts and held by tests; this writes
down what makes them hard to read and to search, what already leans on
their shape, and what a change could be. The idea it ends in is built:
[skim](../../adapters/stdlib/skim/).

## What they are now

Measured on main at #303:

| | FILES.md | ADDONS.md |
|---|---|---|
| Made by | [files.py](../../adapters/stdlib/ci/files.py) | [readme.py](../../adapters/stdlib/readme/readme.py) |
| Lines | 1,971 | 655 |
| Size | 131 KB | 134 KB |
| Headings | 1 | 14 |
| Longest line | 199 | 474 |
| Lines over 120 characters | 87 | 539 |

**FILES.md is one heading over one code block of 1,960 lines.**

- Inside a code block nothing is a link: a path names a file, but no one
  can click to it.
- A line holds a name, not a path: `├── ready.py` is found by a search, and
  its folder is however many `│` are in front of it, up the screen.
- `adapters/` is about 1,500 of the lines, in one run, with no way to jump
  to one add-on's folder.
- 1,127 of its 1,963 entries carry no words: files.py leaves a test and a
  folder blank by rule, and older cards went in before it wrote `its card`.
  A new Markdown file gets its title, so some read as a title where the
  rest say what the file is ("A stack, for agents").

**ADDONS.md is one line per add-on, and the line holds everything.**

- 534 entries, half of them longer than 226 characters: name, its line,
  what it uses, what it needs and where it goes online, its source, up to
  five tags, and three it is near, in one run of text.
- Its sections are long (Reading more kinds of files is 127 lines) and
  carry no heading below them: a reader of PDFs is found by scrolling or
  by search.
- An add-on has no anchor of its own, so nothing can link to its entry,
  only to its folder.
- Its tags are words in backticks, so a search for `offline` finds every
  entry that is, and a search for "pdf" finds the tag, the line and the
  near list alike.

## What leans on their shape

Change the shape and these change with it, in the same pull request:

- `test_docs.py` reads FILES.md's tree and holds it to the repo, and reads
  the README's short tree beside it.
- [files.py](../../adapters/stdlib/ci/files.py) puts each new file in its
  folder, with words of its own making (a docstring's first line, a title,
  `its card`), and moves nothing else: the words already there are a
  person's, and stay.
- [against.py](../../adapters/stdlib/against/against.py) reads the paths
  two pull requests add to FILES.md, to find a duplicate.
- [restack.py](../../adapters/stdlib/restack/restack.py) settles a conflict
  in either by making it again.
- [readme.py](../../adapters/stdlib/readme/readme.py) writes ADDONS.md
  between its `<!-- willow:... -->` markers, and the README's add-on list
  from the same cards; `test_docs.py` fails when either is behind.
- [order.py](../../adapters/stdlib/ci/order.py), ci.py, made.py, new.py,
  test-impact and restack-open name one or both.

## What a change could be

Each of these is its own pull request, and each keeps what reads the file
now working, or changes it in the same pull request.

**FILES.md**

1. A short contents at the top: each top-level folder, linked to a heading
   of its own, with its count of files.
2. The tree cut at each top-level folder, one heading and one code block
   each, so a search lands under a heading that says where it is; and
   `adapters/stdlib/` cut again, by section, as ADDONS.md is.
3. A file's whole path once per folder (the folder's heading, or its first
   line), so a name found is a path known.
4. An entry with no words says what it is by rule, not left blank: a
   `test_*.py` is "its tests", every card "its card".
5. **Done (2, by groups.py):** the tree cut at each top-level folder, and
   `adapters/stdlib/` by the add-ons' sections and groups, their folders in
   that order, with a heading wherever a block would pass a screen; files.py
   makes the cuts, test_docs.py reads every block as one tree, and restack
   settles a conflict past them. skim on FILES.md: screen 0, jump 0.
   Still open: 1, 3 and 4.

**ADDONS.md**

1. One add-on, one short block: the name and its line first, then the rest
   on a line of its own, so the line a person reads isn't the tags.
2. An anchor per add-on (`#ready`), so an entry can be linked to, and the
   README's add-on of the week can point at its entry.
3. Headings under the long sections, by role (`reads`, `page`, `ways`...),
   which every card already says.
4. Tags a search can tell from words: `tag:offline`, not `offline`.

## The idea: skim

A check, not a rewrite: a made list held to how a person reads it, so
neither list drifts back once it is easier to read. For each list it is
given: a heading at least every screen (say 60 lines), no line longer than
it can be read in (say 160 characters, a table row aside), and every
add-on or folder a name that can be jumped to. It says each place one
fails, and it starts out reporting, not refusing, until the two lists
pass. Built as [skim](../../adapters/stdlib/skim/), with a screen of 60
lines and a width of 160.
