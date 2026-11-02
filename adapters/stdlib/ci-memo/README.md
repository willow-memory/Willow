<!-- willow-addon
section: For maintainers
line: A CI gate whose inputs' bytes are unchanged keeps its recorded verdict: pin a run's per-gate keys, and run only what a change can reach.
source: new
added: 2026-10-27
writes: to
network: none
uses: ci
runs-in: repo
-->
# ci-memo

A full `ci.py run` re-checks every add-on on every change, though most gates
read none of what changed. Locally the long pole is mutants: one gate per
add-on, six breaks each. Each gate's verdict is a function of the bytes it
can reach, so this names that reach, hashes it to a key, and memoizes the
record against it — the same move [ci-cache](../ci-cache/) makes for
downloads, on verdicts.

    python adapters/stdlib/ci-memo/ci_memo.py keys [GATE ...]
    python adapters/stdlib/ci-memo/ci_memo.py pin  --box DIR [--box DIR ...] --to FILE
    python adapters/stdlib/ci-memo/ci_memo.py plan --pin FILE [--bare]

After a full run, pin it; after a change, plan:

    $ python adapters/stdlib/ci-memo/ci_memo.py plan --pin ci.pin
    stand  mutants:accents    satisfied
    stand  tests:beats        satisfied
    run    lint:check         inputs changed
    run    mutants:amounts    inputs changed
    run    deps:mcp           never memoized: it installs
    153 stand, 29 to run

    python adapters/stdlib/ci/ci.py run \
        lint:check mutants:amounts deps:mcp ... --box DIR

**A key is bytes, not a guess.** A gate's key is each reachable file's path
and SHA-256, hashed together exactly as ci.py hashes the whole tree into the
`files_sha256` on every verdict row. `pin` accepts only a record whose run
was of this very tree (that field proves it) and whose chain holds, so a
standing verdict always names the bytes that gave it.

**A run in shards is pinned whole.** A run cut with `--shard`, each shard
with its own record, is pinned by naming every record, each with its own
`--box`; a gate two of them hold takes the later one named. Eight shards'
records of one run pin as one: 185 gates, and after a change to one add-on,
123 stand and 62 run.

**The reach is drawn wide, never narrow.** A gate this tool hasn't drawn is
keyed on the whole tree, standing only when nothing at all changed: over-run,
never under-run. Drawn narrow: `lint` (every `*.py`, ruff's config, and the
workflow file that pins ruff's version); the kernel's own tests; and each
add-on's mutants gate — its folder, the kernel, the contract tests and guard
it runs under, mutants' own code, plus every stdlib script's name and
whether it holds a command line, since the contract's COMMANDS test runs
inside every one of them. The repo's own tools (`ci`, `readme`, `similar`,
`github`) read the whole tree in their tests, so their mutants take the
whole tree.

**Three parts are never memoized**, because their verdicts reach past the
tree, where no hash holds: `deps` (what pip serves), `ports` and `tools`
(what this machine has). A pinned Python that isn't the one running also
stands nothing.

**It decides nothing.** A verdict that stands is the old run's, not a new
pass: `plan` only says which rows the bytes still cover, prints the line
that runs the rest, and runs nothing itself. ci.py's record stays the
receipt, and the full run stays the merge's evidence.

`pin` writes only FILE, never inside the tree (a pin in it would change the
keys) or a box, and replaces only a file that is itself a pin. `--repo DIR`
reads another tree, for tests and studies. Exit codes, the kernel's: 0 every
pinned gate stands and nothing need run; 42 gates to run, printed; 2
refused.

**Uses:** the kernel's `read`, `h256` and exit codes; ci.py's own `gates`
and file hashing, imported from its folder.

**Never:** runs a gate; writes a verdict, the record or anything but FILE;
stands a gate on anything but byte-identical inputs.
