<!-- willow-addon
section: For maintainers
line: This repo's checks as verdict rows on a kernel record, the same every run.
source: box
added: 2026-10-23
writes: record, BUGS.md, FILES.md, README.md, ADDONS.md, adapters/planned.json, adapters/*/*, adapters/*/*/*, demo/*/*, demo/*/*/*
network: PyPI, to read each dependency floor's release date
role: repo
uses: live, readme, stack, test-shards
runs-in: repo
-->
# ci

This repo's checks as a kernel record. Each check runs one fixed command and
is written as one `verdict` row through the kernel's own `append`, so the CI
record is hash-chained like any other and the kernel's `verify` checks it.

    python adapters/stdlib/ci/ci.py run    [lint|tests|ports|demo|deps|mutants|tools ...] [--box DIR]
    python adapters/stdlib/ci/ci.py run    tests --without tests:strip
    python adapters/stdlib/ci/ci.py run    mutants --shard 2/4
    python adapters/stdlib/ci/ci.py verify [--box DIR]
    python adapters/stdlib/ci/ci.py show   [--box DIR]
    python adapters/stdlib/ci/ci.py needs  [PART|GATE ...]

`needs` runs nothing: it reads what each gate needs (a module, a program on
PATH) and names the gates this machine would find unreachable, in a second;
the deps gates install from PyPI, so only a run can tell for them, and it
says so. `run` with no part runs all seven. A gate's own name (`tests:strip-2`) runs
just that gate, and the name of a numbered group (`tests:strip`, `tests:adapters`) all of its gates, `--without GATE` leaves one out of what was named, and
`--shard K/N` runs the Kth of N parts of it, cut by
[test-shards](../test-shards/)' own split with each gate weighing the seconds
it is expected to take (`gate_weight`: a chunk's or an add-on's test times
from `test-times.json`, six times that for a mutants gate, a small table for
the rest), so the parts end about together: the N parts hold every gate once
between them, in the table's order. The cut comes from committed data alone,
the same on every machine. A name it doesn't know, or `--without`
given a part, is refused before anything runs. The record goes in `.ci-record/` by default
(git ignores it), and the key `init` makes goes beside it in
`.ci-record.key`. A record or key inside the repo where git would count it is
refused: it would be hashed into the very files it records. CI keeps its
record in the runner's temp folder.

| Part | Gates, in this order |
|---|---|
| lint | `lint:check`, `lint:format` (ruff), `lint:py39` (what 3.10 and later added, [py39.py](py39.py)) |
| tests | `tests:beats` (`kernel.py test`), `tests:kernel`, `tests:docs` (`test_docs.py`, and `test_docs_fires.py`, which shows each docs check fails on a planted violation), `tests:adapters-1` to `-8` (the add-ons in `adapters/stdlib/`, under the guard, each a share of their test files, cut by the times in [test-times.json](test-times.json)), `tests:alone` ([alone.py](alone.py): each add-on's tests again, in a copy holding only the kernel, the add-on and what its card `uses`), `tests:ui` ([ui/](../../../ui/): willow's own UI, its server run over a stack made in a scratch folder), `tests:vectors` (pytest), `tests:strip-1` to `-4` (`test_strip.py`: the repo without GitHub, then without any add-on; the first the kernel-alone work and the kernel's tests, the others a share of the add-ons' test files in the stripped copy), `tests:constitution` (the eternity clause, attacked), `tests:coverage` (`constitution/coverage.py`: which clauses are cited where; failing only on a clause declared failing) |
| ports | `ports:java`, `ports:ts`, `ports:csharp`: `vectors/compare.py`, one port at a time |
| demo | `demo:hollis`, `demo:odile`, `demo:teodora`: each person's files made in a temporary folder and held to their `demo/*/PLANTED.md` |
| deps | `deps:mcp`, `deps:mcp@floor`, `deps:pdf`, `deps:pdf@floor`, two per add-on in `adapters/deps/`: its tests, under the guard, in a fresh virtual environment with only its own pinned requirements (then its floor's) and pytest; an install that can't be done is unreachable. Then `deps:floors`: each floor against the floor rule, by PyPI's upload dates; PyPI out of reach is unreachable |
| mutants | `mutants:again`, `mutants:all`, … one per stdlib add-on: [mutants.py](../mutants/) breaks its code a few ways and runs its tests against each break; a break they miss fails, unless [accepted.json](../mutants/accepted.json) gives the reason it's harmless |
| tools | `tools:bash`, `tools:zsh`, … one per check in [live.py](../live/): the real program a way-in add-on is for (a shell, an editor, an AI tool), run on the lines that add-on prints; a program that isn't installed is unreachable |

Each verdict row holds the gate, its state, a hash of every file in the repo
it ran on, a hash of what the command printed, the Python version, and a
reason when it didn't pass. When pytest skipped tests, the row also says
how many and why (`skipped`), and `run`, `show` and cores.py print it after
the state: `satisfied  [1 skipped: ...]`. A skip changes no state, and is no
pass of that test: the row keeps it in sight. Only what pytest is asked to
report is said, so `tests:alone` and the mutants, which run pytest inside
another program, never say a skip.

**States, never collapsed:** `satisfied`; `failing` (the command failed, or
its output didn't show what it must, such as a port that `vectors/compare.py`
skipped); `unreachable` (a tool isn't installed). Neither of the last two is a
pass.

**Exit codes, the kernel's:** 0 every gate satisfied; 42 a gate unreachable
and none failing; 2 a gate failing, or a record that doesn't verify.

**Deterministic:** every row's time is the commit's, and what changes between
runs (durations, temporary folders, where the repo sits) is taken out before
the output is hashed. The same files give the same record, byte for byte.

**The changelog:** [changelog.py](changelog.py) runs as its own CI job on
every pull request, outside the record (it needs the pull request's number
and its base branch). When anything but Markdown changed, the pull request
owes an entry: a changelog fragment named for it,
`changes/<number>.<kind>.md` ([changes/README.md](../../../changes/README.md)
says how), or, from before the fragments, an entry in CHANGELOG.md's
`## Unreleased` ending `(#N)`. A bug [BUGS.md](../../../BUGS.md) stopped
listing must be named in a `fixed` one, `bug #12`. Exit 0 every entry owed
is there, or nothing is owed; 42 git couldn't compare with the base; 2 an
entry is missing.

**Known bugs:** [bugs.py](bugs.py) makes BUGS.md from the tests marked as
expected to fail, `strict=True` with a reason `bug #N: …`, and refuses any
other such mark. `test_docs.py` fails when BUGS.md and the tests disagree.

**Every file:** [files.py](files.py) keeps FILES.md's tree to git's list of
files. `check` says what the tree lacks and what it lists that's gone;
`write` puts each new file in its folder's order (tests after the code,
README.md last; at the end of a folder kept in an order of its own, which
it says), with what the file says of itself (a docstring's first line, a
Markdown title, `its card`), and takes out what's gone with its notes. A
file it can't describe goes in with nothing, and it says which.
[create_pr.py](../github/create_pr.py) runs `write` before a pull request
opens.

**Made again:** [made.py](made.py) runs every script that makes a file
from the repo's others, in order: readme's add-on lists, BUGS.md, FILES.md,
the lists kept A to Z, the PyPI dates, and craft-assembly's report. `write` makes each
again; `check` names what's stale. A new generator goes in its MADE table,
and create_pr.py, which runs `write`, then makes it in every pull request.

**PyPI's dates:** [pypi_dates.py](pypi_dates.py) keeps
[pypi-dates.json](pypi-dates.json), the upload dates of each deps floor pin
and of the release the floor rule names, which the `deps:floors` test reads
in place of PyPI. `write` asks PyPI only for a pin the file lacks, so in
most pull requests it goes nowhere; `check` names what it lacks.

**Its line in COMMANDS:** [commands.py](commands.py) `suggest NAME`
reads the add-on's usage lines, fills each in as the contract test would
(`--box DIR` is `{box}`, a question is "tomatoes", a file it reads is the
pile's garden.md, an option left out first), and runs it as the test does.
The first that keeps the contract is its line; `--write` puts it in
COMMANDS, A to Z. Run on the 208 add-ons whose lines were written by hand,
it found one that keeps the contract for 174; the other 34 need what only a
person knows (a git ref, dice notation, a model's name, a catalog), and it
says what each of their lines did.

**A demo's tests:** a demo folder with tests that no `DEMO_TESTS` row
runs gets a gate anyway, `demo:FOLDER` (`demo:FOLDER-tests` beside a
person's own gate), from `demo_tests()`, so a new demo's tests run in CI
with no row written. A row is for another name, or a program its tests
need.

**Newer than 3.9:** [py39.py](py39.py) `check` names each use of what
Python 3.10 and later added that ruff can't see, by file and line: a
keyword 3.9 doesn't take (`write_text(newline=)`), a newer name
(`itertools.pairwise`, `datetime.UTC`), `isinstance(x, A | B)`. The deps
add-ons, run on 3.13 alone, are left out; a newer module tried with
ImportError caught, or given by a conftest.py, passes. It is the lint:py39
gate, so create_pr.py runs it on every pull request.

**Real data:** [realdata.py](realdata.py) `run NAME` (or `--base REF`,
each stdlib add-on the branch changed) makes every demo person's files and a
box over them, and runs the add-on's COMMANDS line on each, a reader its
`mirror`, under the guard and held to a minute. A traceback, a breach, a
hang or an odd exit fails it; a refusal is said. create_pr.py runs it.

**Test times:** [times.py](times.py) keeps [test-times.json](test-times.json)
to CI's own run: on a push to main the tests job writes each
tests:adapters gate's JUnit XML (`WILLOW_JUNIT_DIR`) as the `test-times`
artifact, and `write --run latest` reads the last green run's, by gh;
`write --from DIR` reads files already here. `check` says what the json
lacks, and never fails: only the balance of the chunks depends on it.

**A to Z:** [order.py](order.py) keeps the lists people add to in order:
the tables in test_contract.py (COMMANDS, READERS, PILE_EXTRA,
REPORT_COMMANDS) and ci.py's DEMO_TESTS, each entry with the comments
above it; planned.json by name; FILES.md's folders kept A to Z, a slip by
hand put back; and demo/, always. The demo rows run A to Z too, a person's
folder among the rest. A new
line then goes in its own place, not at the end where every pull request
adds one and two collide. `check` names a list out of order, and its test
holds the repo's lists to it; `write` sorts them, moving nothing else, and
refuses a table it can't take apart line by line. create_pr.py runs `write`.

**A new add-on:** [new.py](new.py) `NAME` starts an idea from
adapters/planned.json: its folder, its card (the idea's entry as its
header, `added` today), a script that refuses every command line until it's
built, a test holding that, the idea off the list, FILES.md and the add-on
list written. It exits 42 with what's left for a person: the add-on itself,
its tests, its line in COMMANDS, a changelog fragment, its mutants, and for a
deps idea its requirements and `floor:` line.

**Whose lines:** [whose.py](whose.py) takes `PATH:FIRST-LAST` places and
prints the commit that wrote each, with git alone. Given a host add-on's
folder (`--host adapters/stdlib/github`), it prints the pull request
instead, by the merge that brought the commit in and that host's
host.json. It refuses any place that isn't a line range in a file git
tracks, since the places may come from a report anyone can write.

**At once, on one machine:** [cores.py](cores.py) runs `ci.py run`
as N shards at the same time, `--shard K/N` each with its own record in
`<DIR>/<K>`, then shows every gate's verdict from the N records in the table's
order, verifies each record, and exits as `run` would for all of them.

    python adapters/stdlib/ci/cores.py --box /tmp/ci-main [--jobs N] [PART|GATE ...]

N is the machine's CPUs unless `--jobs` says, never more than there are
gates. Run one after another, every gate takes most of an hour; eight at once
took nine minutes. It runs no gate of its own and writes nothing but ci.py's
records.

**The contract:** [test_contract.py](test_contract.py) holds every add-on to
what they all promise alike. Run with nothing, or with one argument too many
against a real box, an add-on refuses (exit 2) and names itself; every reader
keeps the readers' contract (the summary line, the same bytes twice,
originals untouched, hidden files unread, 42 for nothing to read, refusals
that write nothing). A new add-on with a command line has to be listed there.

## The mirror contract

A reader writes each file it reads as `MIRROR/<same path>.txt`, and the
kernel cites a passage by that mirror file's line. A reader that keeps the
mirror contract also says where in the original each passage came from, so
an answer can point at the file you wrote, not at its mirror. Its card says
`output: mirror`.

Beside each mirror file it writes a hidden map, where the kernel never
reads, so the passages still hold only the file's words:

    MIRROR/notes/garden.md.txt
    MIRROR/.places/notes/garden.md.txt.json
      {"source": "notes/garden.md", "places": {"1": "line 1", "9": "lines 8-9"}}

- **Each key** is the mirror line a passage starts on: a line with words
  after a blank one, or the first, as the kernel cuts paragraphs.
- **Each value** is the place in the source: `line N`, `lines N-M`, or
  another named place, a word and what it names (`page 2`, `cell 4`,
  `row 17`), for a source whose places aren't lines.
- **A chunk the kernel cuts** from a longer passage is at the last place at
  or before its line. A map may place lines inside a passage too, as
  subtitles places each cue of a transcript's one passage.
- **A passage may open with its own citation line**, the source's path then
  `line N` (equations' `paper/main.tex line 120, label eq:oz`): the line it
  cites must be inside its place, and the next line is held to the word rule.

[mirrors.py](mirrors.py)'s `check` holds a mirror to it: every mirror file
has its map, naming its source; every passage is placed, and nothing else
is; a line place is inside the source, with a content word of the passage's
first line on it, so an off-by-one shows; and no mirror line is longer than
one of the kernel's chunks, which it would cut unread.
[test_contract.py](test_contract.py) runs it on each such reader's sample,
and [realdata.py](realdata.py) on the demo people's folders.

    python adapters/stdlib/ci/mirrors.py check --from FOLDER --mirror MIRROR

Each reader keeps its own copy of the dozen lines that write the map, as a
report add-on keeps its copy of the report's: an add-on holds alone and
shares only the kernel. A reader that writes its source line for line places
each passage on its own line (markdown, latex, org, rst, asciidoc,
code-comments, dotfiles); one that moves a line says both (a table's header
moved onto its rule is `lines 8-9`); one that gathers a passage from several
says them all (equations, from the paragraph before to the one after;
subtitles, a cue from its timing line to its text). One whose lines aren't
the file's names its places: jupyter's `cell 4`, mail's `message 3`, a
Telegram export's `message 4417`, and the `whole file` for a note about it.

## The report contract

An add-on that tells you what it found in your files (a check, an audit, a
list of what's waiting) prints a report, and every report has the same
shape, so one add-on's output reads like the next and a stack can line
them up. Its card says `output: report`.

    pii-audit: populated, 3 personal numbers in 3 of 254 files
    ## a card number
      money/orders.csv:17  ···· 4242
    ## a National Insurance number, by shape
      work/p60.txt:9       ···· 45C

- **The first line** is the add-on's name, its state and one thing said:
  `NAME: STATE, SAID`. The state is the kernel's own word: `populated`
  (rows found), `empty` (none), or `unreachable` (it couldn't look, and
  SAID says why). A refusal is no report: it is exit 2, on stderr.
- **Rows** are where, then what, one line each, indented two spaces, the
  where column as wide as its longest (up to 60). Where is a place, a
  `path:line` or another name for where the thing is; what is the thing.
- **Groups** are `## name` above their rows, in the add-on's own order;
  rows that belong to no group come first, with no heading. A group with
  no rows isn't printed.
- **`--json`** prints the same report as one JSON object: `addon`,
  `state`, `said`, and `groups`, each `{"name": ..., "rows": [{"where":
  ..., "what": ...}]}`, the group of no group named `null`.
- **Exit codes:** `empty` is 0 and `unreachable` 42; `populated` is 0, or
  42 when what was found waits on you, as the card says. So 42 never means
  "found nothing".

Each report add-on keeps its own copy of the twenty lines that print it
(`report`, `report_text`, `say`: an add-on holds alone and shares only the
kernel). [stack](../stack/) runs a report add-on with `--json` and prints the
report itself, and [test_contract.py](test_contract.py) holds each one to
it: its text is exactly what stack prints from its JSON, its first line
and rows have the shape, its state agrees with its rows and its exit code,
and the same box gives the same report twice.

[reports.py](reports.py) brings add-ons onto it in batches: `survey` runs
every add-on on one box and sorts what each prints by shape, the ones
printing rows with places being the next to convert; `scaffold NAME...`
does what is the same every time (the add-on's name, its copy of the three
functions, `--json` taken off before it reads its arguments), writing the
add-on's script in place, the one write to the add-ons' folders this card's
`writes` names; `check NAME...` runs the contract on each and says which
aren't done.

    python adapters/stdlib/ci/reports.py survey
    python adapters/stdlib/ci/reports.py scaffold NAME...
    python adapters/stdlib/ci/reports.py check NAME...

**The guard:** the add-ons' tests, and each deps add-on's, run with
[guard/sitecustomize.py](guard/sitecustomize.py) on `PYTHONPATH`, so it is
loaded into every Python process they start. It holds each add-on to its
card's `writes` and `network` and to the rules no card loosens (no original
changed, no box written but through the kernel, no key read), and writes
each breach to a log. A gate whose log isn't empty is `failing`, even when
every test passed: a breach the add-on caught and hid is still a breach.
[test_guard.py](test_guard.py) breaks each promise on purpose and checks the
guard catches it.

**Uses:** the kernel's `init`, `append`, `read`, `verify`, `h256` and its exit
codes.

**Never:** writes a `seal` row, or a field a seal reader looks at (`proof`,
`subject`). Its verdicts are draft. What makes a tree count is a person
merging it.

In CI (`.github/workflows/ci.yml`) each part is its own job with its own
record, every heavy job waiting on the fast ones (lint, and a pull request's
against and changelog) so a quick failure stops the rest from queueing, verified and uploaded as that run's artifact, but three: `tests:strip`
has jobs of its own on each Python (it runs the add-ons' tests again, in a
stripped copy, so beside the rest it doubled the job), the tests and strip
jobs are one job on each Python that runs four `--shard`s at once with
[cores.py](cores.py) (records `<DIR>/1` to `<DIR>/4`, all uploaded under one
artifact), and mutants is four jobs cut with `--shard` on a push to main
only: a pull request's `mutants-reach` job runs just the gates
[ci-memo](../ci-memo/) says its change reaches, standing the rest on
main's last green run. Cut into one job
each, a pull request is 14 jobs and a push to main 30, not 36 and 84: a job
had used one of the runner's four cores, and the tests job ended with its
slowest gate (about nine minutes) however it was cut. All the add-ons' tests
in one gate took eight minutes, and strip ran them again: the chunk gates are
what lets a job run a few of them.
`test-times.json` is each test file's seconds in one run
(`pytest adapters/stdlib --junitxml=RUN.xml`, summed by file); it only sets
the balance, so a stale one runs every test all the same. `adapters/stdlib/github/github.py check` holds the cut: every gate run by exactly
one job on a push, and a job skipped on pull requests backed by one that plans
its gates with ci-memo and falls back to running them all. A job that fails writes [ci-why](../ci-why/)'s reading of its log
to the run's summary.
