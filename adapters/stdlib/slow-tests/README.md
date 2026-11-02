<!-- willow-addon
section: For maintainers
line: Each test's time kept per run, with the slowest named and any that got slower flagged.
source: new
added: 2026-10-24
writes: nothing
network: none
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

Willow's own suite, three runs of `test_kernel.py` and `adapters/stdlib`,
with `--top 3`:

    3 runs, oldest first:
      run-01  701 tests  passed 700  skipped 1  failed 0  passed time 115.41 s
      run-02  721 tests  passed 720  skipped 1  failed 0  passed time 107.97 s
      run-03  721 tests  passed 720  skipped 1  failed 0  passed time 101.31 s

    Slowest in run-03 (seconds; 720 passed):
           3.88  adapters.stdlib.ci.test_ci::test_the_same_files_give_the_same_record_byte_for_byte  (median of 2 earlier 5.12)
           2.87  adapters.stdlib.ci.test_ci::test_a_record_inside_the_repo_where_git_would_count_it_is_refused  (median of 2 earlier 2.47)
           2.37  adapters.stdlib.ci.test_ci::test_verify_holds_the_chain_and_refuses_anything_but_ci_verdicts  (median of 2 earlier 3.02)
      ... and 717 more (--top shows more)

    Slowest files in run-03 (seconds, passed tests added):
          14.09  adapters.stdlib.ci.test_contract
          10.61  adapters.stdlib.ci.test_whose
           9.52  adapters.stdlib.ci.test_ci
      ... and 66 more (--top shows more)

    SLOWER than before in run-03 (more than 2x and 1 s over the median of earlier passes):
      none

    NOT RUN in run-03, though it passed before:
      none

No one test there is slow: the time is many short tests that each start a
program, gathered in a few files, which the files list shows and the tests
list can't. Nothing got slower between the runs, and run-to-run noise
didn't trip the rule.

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
