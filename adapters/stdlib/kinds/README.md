<!-- willow-addon
section: For maintainers
line: Every file of this repo sorted by what it is (code, a card, a test, made by a script, made-up, an idea) and the ones nothing declares.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: none
role: repo
output: report
runs-in: repo
-->
# kinds

Every file of this repo sorted by what it is, and the ones nothing declares.

    python adapters/stdlib/kinds/kinds.py count [--json] [--root DIR]
    python adapters/stdlib/kinds/kinds.py of PATH... [--json] [--root DIR]

    kinds: populated, 1775 files: 1597 are one of 9 kinds, 178 nothing declares
    ## what it is, and what says so
      made      6 files; a script makes it: made.py names the script
      account   112 files; what was done: towncrier.toml names the changelog
      idea      1 file; not built yet: the ideas list
      frozen    159 files; a study froze it: its demo's FROZEN.json lists it
      test      415 files; pytest runs it: named test_*.py or conftest.py
      card      361 files; an add-on's own README.md
      code      384 files; a script beside an add-on's card
      fixture   87 files; the rest of an add-on's folder
      made-up   72 files; a made-up person's files: the demo holds a make_life.py
    ## nothing declares
      demo/five-repos/  37 files, such as demo/five-repos/README.md
      docs/             19 files, such as docs/agents/add-ons.md
      (top level)       18 files, such as .editorconfig

**Why.** This repository holds several kinds of thing in one folder: what
was written to be read, what a script made from that, tests, made-up data,
ideas not built, an account of what was done. Asked a question, they answer
as equals. Pointed at itself, willow served a list made from the cards
above the cards, an idea as if it were built, and a made-up person's date
as the day something was first said
([demo/kept](../../../demo/kept/README.md)). The kernel keeps a person's
folder apart from the record of what was asked of it; nothing kept this
repo's kinds apart. This is the count, before any rule.

**It starts with what is here.** A file has a kind only when something the
repo already keeps says so, and a row names what says it:

| kind | what says so |
|---|---|
| made | ci's made.py names the script that makes it |
| account | towncrier.toml names the changelog and the folder its entries wait in |
| idea | it is the ideas list, where an add-on waits until it is built |
| frozen | a FROZEN.json in its demo lists it, under `files` or `sources` |
| test | pytest runs it: it is named `test_<name>.py`, or is pytest's conftest file |
| card | it is an add-on's README.md, the one that opens `<!-- willow-addon` |
| code | it is a script beside an add-on's card |
| fixture | it is anything else in an add-on's folder: a sample, a stand-in |
| made-up | its demo holds a make_life.py, the mark of a made-up person |

The first that fits, top to bottom, is the file's kind. So a test inside an
add-on is a test, and a made-up person's frozen file is frozen.

**What nothing declares is listed, by folder, the most first.** Today that
is the kernel, its ports, its test cases and its law, the docs, the UI, and
the studies' own reports. They are not unimportant; nothing a script can
read says what they are. A kind for them is a declaration to add where its
subject lives, not a path written here.

**One table is this add-on's own.** made.py names the scripts that make
files, not the files, so `WRITES` in the script says what each writes. A
script made.py names that the table doesn't know is a row of its own, under
"a script whose files aren't known", and the run ends 42: a new made file is
never passed over as a source.

**Asked of files by name**, it says each one's kind and what says so:

    $ python adapters/stdlib/kinds/kinds.py of kernel.py ADDONS.md
    kinds: populated, 2 asked: 1 have a kind, 1 nothing declares
      kernel.py  nothing declares it
      ADDONS.md  made; adapters/stdlib/readme/readme.py

`--root DIR` reads another checkout, a clone at an older commit say.
`--json` prints [the report](../ci/README.md#the-report-contract) as one
JSON object.

It reads the files git tracks and the new ones it isn't told to ignore, and
inside them only the cards' first line,
made.py, towncrier.toml and each FROZEN.json. It writes nothing.

**Exit codes**, the kernel's: 0 every file asked about has a kind; 42 some
have none, and they are listed, or git couldn't list the files; 2 refused
(a bad command line, a `--root` that is not a folder, a PATH that isn't one
of the repo's files).

**Needs:** the git program (GPL, called, not linked), to say which files
are the repo's.

**Uses:** the kernel's exit codes.

**Never:** writes anything, reads the key, or goes online.
