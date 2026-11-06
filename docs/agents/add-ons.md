# An add-on, for agents

The steps of building an add-on that have each been missed at least once,
and what holds an add-on's tests to its card. Part of [AGENTS.md](../../AGENTS.md);
the rules are [CONTRIBUTING.md](../../CONTRIBUTING.md) and
[adapters/README.md](../../adapters/README.md).

## Step by step

Each of these is a check that fails when it's missed.
`python adapters/stdlib/ci/new.py NAME` does 1, 3, 4 and 5 from the idea's
entry, and says what's left.

1. **Its folder** in `adapters/stdlib/` or `adapters/deps/`: the code, its
   tests, and its card, `README.md`, whose header is the idea's entry from
   `adapters/planned.json` with the same `writes` and `network` promises,
   and its `role`. A reader (`role: reads`) also says what it reads,
   `reads: .ext`; the idea's entry doesn't carry that line, so add it.
2. **Its command line in `COMMANDS`**, in `adapters/stdlib/ci/test_contract.py`,
   if a person runs it, in its place A to Z. Once it's built,
   `python adapters/stdlib/ci/commands.py suggest NAME --write` finds one
   from its usage lines and writes it there; when none of them keeps the
   contract, it says what each did, and the line is yours. A reader goes in
   `READERS` instead, with a sample file: its `mirror --from --to` row is made
   from that. Missing, it fails the contract test, and every other add-on's
   mutants then report their accepted breaks as stale.
3. **Its idea out of `adapters/planned.json`**, deletions only.
4. **Its place in FILES.md's tree**, alphabetically:
   `python adapters/stdlib/ci/files.py write` puts it there.
5. **The add-on list regenerated**, never edited:
   `python adapters/stdlib/readme/readme.py write`.
6. **Its changelog entry, in a file of its own:**
   `changes/+<branch>.<kind>.md`, opening with the name in backticks
   ([changes/README.md](../../changes/README.md) says how). Never in
   CHANGELOG.md itself: every pull request editing the same lines there is
   what left each merge conflicting with all the others. create_pr.py
   names the file for the pull request.
7. **Mutants**: `python adapters/stdlib/mutants/mutants.py run NAME` must
   kill every break. CI makes the six lowest-id breaks, and an entry in
   `adapters/stdlib/mutants/accepted.json` for a break those six don't
   include fails as stale: list only what CI's own run shows surviving.
   Run this **after** step 2 and on a clean tree: a mutant is killed when the
   run's tests exit non-zero, so an add-on not yet in `COMMANDS`, or a stray
   uncommitted add-on folder, fails the contract test and marks every mutant
   killed: a false pass that CI, on the committed tree, then shows as the
   real survivors.
8. **Real data, not only fixtures.** `python adapters/stdlib/ci/realdata.py
   run NAME` runs its COMMANDS line on every demo person's folder, under the
   guard, and create_pr.py runs it for each add-on a change touches. An
   add-on can pass every test on hand-made files and still be wrong on a real
   folder; a test written from what the code does checks only that. What it
   prints is what the pull request's "Real data" says; a question only you
   can ask of a folder is still yours to ask. When no demo folder holds the
   kind of file it reads, say what real files you ran it on.
9. **If it goes online**, its tests use a server it starts on 127.0.0.1: the
   guard narrows only `none` and `loopback`, so a card naming a site lets the
   tests use this machine. Its `COMMANDS` row must still answer without the
   network, by an argument that settles the question before any fetch (an
   empty window of days, a closed local port); a row that reaches the real
   site is a test that goes online.
10. **Placeholders on its card.** `test_docs.py` reads a backticked name with
    a slash or a file extension as a path that must exist. Write a
    placeholder with angle brackets, as the pdf card writes
    `MIRROR/<same path>.txt`.

## The guard

An add-on's tests run under `adapters/stdlib/ci/guard/sitecustomize.py`,
which holds every write the add-on's own code makes to its card's `writes`,
and raises the moment it breaks one:

- **`to` means under the path in `--to` on the command line.** It reads
  `sys.argv`, so a test that calls `main()` in-process passes `--to` there
  too, or the write is judged as outside it.
- **Making a missing folder is a write.** An add-on that creates the parent
  of its `--to` file has written outside `to`; refuse a missing folder
  instead.
- **A box is written only through the kernel**, and any folder holding a
  kernel.json counts as one.
- **Scratch made with `tempfile` is the add-on's own**; a folder it names
  itself, even under /tmp, is not.
- **Never the key.** No add-on reads it, not even to copy it.

## An idea, not yet built

- **Ask the list first:**
  `python adapters/stdlib/similar/similar.py near "your idea in a sentence"`.
  It asks both ways: entries that hold half of your sentence's words, and
  entries half of whose words your sentence holds, so a long line still finds
  a short entry it contains. It shows, never refuses: you decide.
- **`adapters/planned.json` is sorted by name and written as
  `json.dumps(entries, indent=1, ensure_ascii=False)` plus a newline.**
  Rewritten any other way, every line of it changes.

## A deps add-on's floor

The deps gate installs each add-on's pins, then its floor pins
(`adapters/deps/mcp/requirements-floor.txt`, say), again on the one Python
the deps job runs (`3.13` in `.github/workflows/ci.yml`). The floor rule
names a 2020-era release, but such a pin often won't install on that Python:
raise the floor to the first version that does and say why on the card's
`floor:` line (twenty characters or more once the version is struck out, or
`deps:floors` fails). mcp's floor is raised this way.

The floor test can't ask PyPI, so it reads PyPI's dates from
`adapters/stdlib/ci/pypi-dates.json`: each floor pin's upload time and the
rule's release's. `python adapters/stdlib/ci/pypi_dates.py write` asks PyPI
for a new pin's, and only those; made.py and create_pr.py run it, so a new
deps package is never typed in by hand.
