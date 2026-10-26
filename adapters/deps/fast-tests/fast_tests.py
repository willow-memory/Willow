"""fast_tests.py: the test suite across every core, with pytest-xdist. 3.9+.

    pip install -r adapters/deps/fast-tests/requirements.txt
    python adapters/deps/fast-tests/fast_tests.py PATH [PATH ...] [--jobs auto|N]

Runs `pytest` over the PATHs with pytest-xdist's `-n`, so the same tests run
across every core at once instead of one after another -- the same suite, in
a fraction of the time. `--jobs` is `auto` (one worker per core, the default)
or a positive number; nothing else is passed, so the run is the plain suite,
not a tuned one. It measures the wall time and prints, after pytest's own
output, how many workers ran it over how many cores and in how long.

It only runs the suite and reports: it reads no box, writes no file (pytest
keeps its own caches, turned off here with no:cacheprovider), reaches no
network -- pytest-xdist's workers talk over pipes, not sockets -- and approves
nothing. Exit codes, the kernel's: 0 every test passed; 42 a test failed or
none were collected (something is waiting for you); 2 refused (a bad command
line, or pytest could not run the suite at all).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]

# pytest's exit codes -> the kernel's: 0 all passed; 1 failures and 5 nothing
# collected both want you; 2/3/4 (interrupted, internal, usage) mean it could
# not run the suite, so refused.
BY_PYTEST = {0: kernel.ALIVE, 1: kernel.ESCALATE, 5: kernel.ESCALATE}


def parse(argv: list[str]) -> tuple[list[str], str] | None:
    """(PATHs, jobs), or None to refuse. One --jobs (auto or a positive int),
    and one or more paths."""
    paths: list[str] = []
    jobs = "auto"
    it = iter(argv)
    for a in it:
        if a == "--jobs":
            jobs = next(it, "")
            if jobs != "auto" and not (jobs.isdigit() and int(jobs) > 0):
                return None
        elif a.startswith("-") or not a:
            return None  # an unknown flag, or an empty path
        else:
            paths.append(a)
    if not paths:
        return None
    return paths, jobs


def main(argv: list[str]) -> int:
    parsed = parse(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    paths, jobs = parsed
    cmd = [sys.executable, "-m", "pytest", "-n", jobs, "-p", "no:cacheprovider", *paths]
    start = time.monotonic()
    got = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.monotonic() - start
    sys.stdout.write(got.stdout)
    if got.stderr:
        sys.stderr.write(got.stderr)
    cores = os.cpu_count() or 1
    workers = cores if jobs == "auto" else int(jobs)
    print(f"\nfast-tests: {workers} worker{'' if workers == 1 else 's'} over "
          f"{cores} core{'' if cores == 1 else 's'}, {elapsed:.2f}s")  # fmt: skip
    return BY_PYTEST.get(got.returncode, kernel.REFUSED)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
