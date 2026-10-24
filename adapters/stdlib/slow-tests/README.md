<!-- willow-addon
section: For maintainers
line: Each test's time kept per run, with the slowest named and any that got slower flagged.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# slow-tests

Where a test run's time goes, and which tests got slower than they were.

    python adapters/stdlib/slow-tests/slow_tests.py --runs DIR [--top N] [--times X] [--seconds S]

`DIR` holds one file per run, each written by pytest with nothing to install:

    python -m pytest --junitxml=DIR/2026-10-24.xml

Keep the files: this reads them, it writes nothing, so the history is the
folder you (or your CI) keep. The runs are read in the order of their file
names, with numbers inside a name counting as numbers (`run-9` before
`run-10`), never by when a file was written. Name them so they sort: a date, or
a CI run number. The last one is "this run".

    3 runs, oldest first:
      2026-10-22  812 tests  passed 790  skipped 22  failed 0  passed time 301.20 s
      ...
    Slowest in 2026-10-24 (seconds; 790 passed):
         126.40  tests.adapters::test_big  (median of 2 earlier 41.20)
    Slowest files in 2026-10-24 (seconds, passed tests added):
         140.10  tests.adapters
    SLOWER than before in 2026-10-24 (more than 2x and 1 s over the median of earlier passes):
      tests.adapters::test_big  126.40 s now, 41.20 s median of 2 earlier  (+85.20 s, 3.1x)
    NOT RUN in 2026-10-24, though it passed before:
      tests.old::test_x  not in this run; last passed in 2026-10-23 at 8.00 s

- **The rule for "slower" is fixed and printed.** A test that passed in this
  run and in an earlier one is flagged when its time is more than **2 times**
  and more than **1 second** over the median of its earlier passes. Both must
  hold, so 0.01 s becoming 0.05 s is not flagged and neither is 5 s becoming
  5.4 s. `--times` and `--seconds` move the two numbers; nothing is learned or
  guessed. A test with no earlier pass is counted ("passed with no earlier
  pass, so not compared"), not flagged.
- **A skipped test is not a fast one.** It has no time. If it passed before
  and is skipped now, it is listed under "NOT RUN" with the run it last passed
  in, like a test that is missing from this run altogether. Both say what they
  are; neither is dropped.
- **A failed test has no time that means anything**: it may have stopped at
  the first line. It is listed as failed, and only passes count towards a
  time or a median.
- **Counted as one number.** A test that appears twice in a run has its times
  added. Times are shown to two places.
- **Each list shows `--top` lines** (10 unless you say) and then says how many
  more there are.

Order: slowest first, ties by name, so the same files give the same bytes.

**Exit codes:** 0 some runs read; 42 no run in `DIR` (no `.xml` file, or none
with a test in it); 2 refused (no such folder, a file that isn't JUnit XML, a
test with no usable time, a bad option).

**Uses:** the kernel's exit codes only.

**Never:** writes anything, runs your tests, or reads any file but the `.xml`
files in `DIR`.
