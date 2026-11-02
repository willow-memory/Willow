<!-- willow-addon
section: For maintainers
line: The test suite across every core with pytest-xdist, the same tests in a fraction of the time.
source: new
added: 2026-10-26
needs: pytest-xdist; MIT
floor: pytest-xdist 3.0.2; the rule names 2.2.0, but every 2.x imports py.log, long gone from pytest, so 2.x installs on today's Python yet cannot run a suite; 3.0.0 dropped the py dependency, so 3.0.2 is the oldest that runs
writes: nothing
network: none
-->
# fast-tests

The test suite across every core, with [pytest-xdist](https://pypi.org/project/pytest-xdist/).
The same tests the serial run runs, dealt out to one worker per core, so a
suite that takes minutes one test at a time finishes in a fraction of it.

    pip install -r adapters/deps/fast-tests/requirements.txt
    python adapters/deps/fast-tests/fast_tests.py PATH [PATH ...] [--jobs auto|N]

It runs `pytest` over the PATHs with xdist's `-n`. `--jobs` is `auto` (one
worker per core, the default) or a positive number. Nothing else is passed,
so it is the plain suite run in parallel, not a tuned one. After pytest's own
output it prints how many workers ran over how many cores, and the wall time.

## what it does and doesn't

It only runs the suite and reports. It reads no box, writes no file (pytest's
caches are turned off with `no:cacheprovider`), reaches no network — xdist's
workers talk over pipes, not sockets — and approves nothing. The guard holds
it to `writes: nothing` and `network: none` while its tests run.

Exit codes, the kernel's: `0` every test passed; `42` a test failed, or none
were collected — something is waiting for you; `2` refused — a bad command
line, or pytest could not run the suite at all.

## its dependency, and the floor

`pytest-xdist` (MIT) is the one requirement. The floor is **3.0.2**, above the
2020-era version the floor rule would name (`2.2.0`): every 2.x imports
`py.log`, long removed from pytest, so a 2.x pin installs on today's Python
but cannot run a suite. `3.0.0` dropped the `py` dependency, so `3.0.2` is the
oldest release that still runs — see `requirements-floor.txt`.
