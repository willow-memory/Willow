<!-- willow-addon
section: For maintainers
line: The CI test jobs split by each test's past time, so every job finishes about together.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# test-shards

A test run split over several jobs finishes when its slowest job does. Cut
by count, one job gets the slow tests and the rest wait for it. This cuts by
how long each test took last time, so the jobs end about together.

    python adapters/stdlib/test-shards/shards.py --past RUN.xml --shards 3 test_kernel.py adapters/stdlib

    3 parts, 69 files, 734 tests, expected 120.405 s in all
    part 1/3  40.138 s  23 files
      adapters/stdlib/again/test_again.py  1.012 s
      adapters/stdlib/ci/test_contract.py  16.230 s
      ...
    part 2/3  40.140 s  23 files
      ...
    spread: slowest 40.140 s, fastest 40.127 s, 0.013 s apart
    every test has a past time
    0 tests in the past run are no longer in the suite, left out

`RUN.xml` is what pytest writes for an earlier run: `pytest --junitxml=RUN.xml`.
Name it more than once and each test counts as its average; name none and
every test counts the same, which is said.

To run one part, ask for it by number and give pytest what it prints:

    mapfile -t PIECES < <(python adapters/stdlib/test-shards/shards.py --past RUN.xml --shard 2/3 test_kernel.py adapters/stdlib)
    python -m pytest "${PIECES[@]}"

- **The suite is read as it is now.** It runs `pytest --collect-only -q` on
  the paths you give, which imports the test files and writes nothing. Or
  give it those ids yourself: `--tests FILE`, or `--tests -` for standard
  input. It never takes the list of tests from the old run, which may be
  stale.
- **Every test is in exactly one part.** A test that is in the suite but not
  in the old run is placed at the median of the others (or `--default
  SECONDS`) and counted in the line that says so. A test that is in the old
  run but gone from the suite is left out, and counted too. If nothing
  has a past time at all, each counts one second.
- **A file is the piece, by default.** `--by file` keeps a file's fixtures
  together and hands pytest short arguments. `--by test` cuts finer, down to
  one test, for a file bigger than a part; then only the totals are printed
  and `--shard` gives the ids, brackets and spaces and all, so quote them.
- **Longest first.** Pieces by time, slowest first, ties by name, each to
  the part with the least so far, ties to the lowest. The same input gives
  the same bytes, however the ids are ordered. Times are whole milliseconds,
  so sums are exact.
- **What a time includes.** The testcase time pytest wrote: setup and
  teardown too, so the first test to use a module's fixture carries its
  cost. Starting pytest, and importing the test files, is not counted; give
  each part a little more than its expected time.
- **Only as good as the old run.** Times from a quiet machine on one Python
  differ on a busy one; the expected time is a plan, not a measurement. Run
  the parts and compare: on this repo's own suite a plan of 40.1 s a part ran
  in 32.1, 33.9 and 36.6 s, since the old run was on a busier machine.

**Exit codes:** 0 split; 42 the suite holds no test; 2 refused (a bad
command line, an XML file that can't be read, a collection that failed).

**Uses:** the kernel's exit codes. It is a tool for this repo's maintainers:
no person's box or files are read, so it isn't in `adapters/stdlib/ci/test_contract.py`'s
list of commands that run on a pile (the list leaves out `ci`, `mutants`
and the other repo tools the same way); its own tests hold its command line.

**Never:** writes anything, goes online, or changes a CI workflow. Wiring
the parts into CI belongs in `adapters/stdlib/github/` and `.github/`.
