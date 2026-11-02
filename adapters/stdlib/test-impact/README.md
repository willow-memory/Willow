<!-- willow-addon
section: For maintainers
line: Only the tests a change can reach run first, from the import graph; the full suite still runs after.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# test-impact

You changed one add-on and a line in the docs. The full check takes five to
fifteen minutes. Nearly every real failure would have shown in seconds from the
add-on's own tests, its share of the checks every add-on keeps, and the docs
test. This says which ones a change can reach, and can run just those first.

    python adapters/stdlib/test-impact/impact.py plan --base origin/main
    python adapters/stdlib/test-impact/impact.py run  --base origin/main
    python adapters/stdlib/test-impact/impact.py plan adapters/stdlib/stale/stale.py CHANGELOG.md

    1 path(s) changed (1 by hand):
      adapters/stdlib/stale/stale.py

    Plan, in ci.py's gate names, cheapest and closest first:
      1. lint:check: ruff on 1 changed .py file(s)
      2. lint:format: ruff on 1 changed .py file(s)
      3. tests:adapters: test_contract.py narrowed to stale
           WILLOW_ONLY=stale pytest adapters/stdlib/ci/test_contract.py
      4. tests:adapters: 1 test file(s) of the add-ons reached
           pytest adapters/stdlib/stale/test_stale.py
      5. tests:docs: FILES.md, README counts, generated lists, citations
           pytest test_docs.py
      6. mutants:stale: break its code a few ways; its tests must notice
           mutants.py run stale

    This does not replace the full run: it still runs after, in CI, and here:
      python adapters/stdlib/ci/ci.py run --box /tmp/ci-record

**The change** is the paths git says differ from `--base REF` (from where your
branch left REF, so REF's later commits don't count), to `--head REF` if you
give one, else to your files as they are now, edits and new files included. Paths
you name are added. With neither, it refuses. `--head` must be the commit you
have checked out: the plan is read from the files on disk, so another branch's
head is refused rather than planned from the wrong files. To plan a branch,
check it out (a `git worktree` will do) and plan there.

**How a path is placed.** Every Python file in the repo is read with Python's
`ast` and joined to what it imports, and to any Python file it names in a string
(the way the tests load an add-on's script). A test that comes to a changed
file through those joins runs. Then a few written rules cover what imports
can't show:

| Change | Also runs |
|---|---|
| an add-on's folder | its tests; `../ci/test_contract.py` narrowed to it (`WILLOW_ONLY`); its mutants when its code changed; ruff on its changed Python files |
| `../ci/test_contract.py` | the whole of it |
| anything at all | `test_docs.py` (FILES.md, README counts, generated lists, the law's citations); `test_docs_fires.py` too when a docs test changed |
| `constitution/` | its tests and the coverage report |
| `vectors/` | its tests and every port |
| a folder under `ports/` or `demo/` | that port, that demo |
| a folder under `adapters/deps/` | its two gates, `deps:NAME` and `deps:NAME@floor` |
| GitHub's files | the strip test |
| `kernel.py`, `ruff.toml` | everything |

**A change it can't place widens.** A workflow, `.gitignore`, a test that
belongs to no gate: it says `couldn't place PATH: running everything`, and
everything is every gate of ci.py, run in memory with no record. It never
shrinks silently.

**`run`** says the plan, then runs it in order and stops at the first gate that
fails, naming the gates it did not reach. The gates are ci.py's own: the
add-on tests run under the same guard that holds them to their cards.

**What it leaves to the full run, always:** the strip test (minutes), the other
add-ons' mutants, and any test that only a change somewhere else could break
without importing it. Run the full thing before you say it's done.

Exit codes, the kernel's: 0 a plan printed, or every gate it ran satisfied; 42
nothing changed, or a gate it needed is unreachable here (a tool isn't
installed) and none failed; 2 refused (nothing to go on, a ref git doesn't know,
a path outside the repo), or a gate failed.

**Uses:** `../ci/ci.py`'s gates and guard, and `git`, to list what changed.

**Never:** writes a file or a record, goes online, or changes your files.
(The tests it runs write their own temporary folders, as they do under ci.py.)
