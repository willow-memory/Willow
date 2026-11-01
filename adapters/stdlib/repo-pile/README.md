<!-- willow-addon
section: Ways to use it
line: Public repositories you list, cloned and made askable, keeping only those under a licence an Apache-2.0 project can use.
source: new
added: 2026-10-24
writes: record, to
network: github.com (or the --source you give), to clone the repositories you list
tags: no-install, online, records, interface, research
-->
# repo-pile

A list of public repositories turned into a box you can ask questions of,
for studying other people's code without taking on their licence trouble.

    python adapters/stdlib/repo-pile/repo_pile.py build --to <base> --repos <list.txt> --key <key>
    python adapters/stdlib/repo-pile/repo_pile.py ask --base <base> --questions <questions.txt>

The list is one `<owner>/<repo>` a line; `#` starts a comment, and a line that
isn't `<owner>/<repo>` is skipped and said. `build` writes only under `--to`:

| Step | What it does | Made under `--to` |
|---|---|---|
| clone | each repo, shallow, by the git program, from `--source` (GitHub unless you say) | repos/ |
| licence | reads each repo's own top-level licence files; keeps it only when one grants Apache, MIT, BSD, ISC, zlib, CC0, Unlicense, PSF or CC-BY and holds no copyleft text | REJECTED.txt: each one left out, and why |
| pile | each kept repo's docs: READMEs, agent notes, licences, `docs/` folders; and each `--notes` file | pile/ |
| secrets | [secrets-audit](../secrets-audit/) over the pile: where, never the value | |
| box | the kernel's own `init` over the pile, with `--key` and `--words` | box/ |
| changed | [changed](../changed/): one fingerprint row of what the pile holds | |
| index | [scan](../scan/): the pile, and the whole source unless `--no-code-index` | index-pile/, index-code/ |
| verify | the kernel's own `verify` | |

A second `build` fetches nothing already there, gates every repo again, and
rebuilds the pile, so it holds exactly what is kept now.

**Why the docs and not the code.** The kernel reads its whole pile on every
question. On 44 repositories (2.9 GB) one question through the kernel took
over ten minutes; their docs alone (3,141 files) took 27 seconds. The code
is still asked, through `scan`'s index of it: five questions of 3.36 million
passages took a minute and a half.

**After the build**, each verb is willow's own add-ons over the base:

| Verb | Add-ons | What you get |
|---|---|---|
| `ask --questions FILE` | [scan](../scan/) | each question of both indexes, as JSON lines; `--rank bm25` to point where to look, `--todo` for the lines each file marks to do, `--top N`, `--words FILE` |
| `bite "question"` | [privacy](../privacy/) | one question through the box itself, on the record |
| `quote "exact words"` | [quote-check](../quote-check/) | whether the pile holds that quote, and where |
| `report` | [digest](../digest/), [again](../again/), [stale](../stale/), [export](../export/), [history](../history/) | what the box needs from you, then `verify` |
| `check` | [xref](../xref/), [todo](../todo/), [secrets-audit](../secrets-audit/) | the pile's health as counts |
| `backup --to FOLDER` | [backup](../backup/) | the record zipped and checked; never the key |

What `ask` and `quote` print goes through privacy's scrub unless `--raw`:
other people's docs hold their email addresses, and sometimes their keys.
It hides what privacy knows to look for, no more: on willow's three demo
lives, built into a base as local repos, it first let through a UK phone
number written with spaces and a bank account number, which privacy now
withholds; a street address or a name on its own still goes through.

**The kernel's rank or BM25.** On these repositories the kernel's rank found
the right passage when a question used the files' words, and said nothing
held it when nothing did; BM25 pointed to the right file more often, and
also answered a question nothing held. Use BM25 to find where to read, and
the kernel, or the file, to say it.

**Exit codes:** the kernel's. 0 something held; 42 nothing to build, or
nothing held a question; 2 refused, or a bad command line.

**Refused:** a `--to` whose parent folder doesn't exist; a list or note
that isn't a file; a base with no box; cloning with no git program, which
it names. A list with nothing to clone and no notes builds nothing.

**Needs:** the git program for the clones (GPL, called, not linked);
everything else is Python's standard library.

**Uses:** the kernel's `init`, `verify`, `MAX_FILE` and exit codes; the
add-ons named above, each run as its own program.

**Never:** reads the key, seals an answer, or writes the record but through
the kernel and the add-ons that write it. It never keeps a repo whose
licence it can't read.
