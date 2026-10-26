"""bench: how fast the kernel answers on piles of set sizes. `run` builds a
pile of each size, reads and ranks it, and prints a median time per size with
the kernel's version. The tests check the shape, not the numbers (a time is
the machine's): a line per size, each a non-negative millisecond figure, the
repeat count echoed, the version printed; and a bad command line refused."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE / "bench.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BENCH), *argv], capture_output=True, text=True
    )


def sizes_timed(out: str) -> dict:
    """{size: milliseconds} from the printed lines."""
    got = {}
    for line in out.splitlines():
        m = re.match(r"\s*(\d+) passages\s+([\d.]+) ms", line)
        if m:
            got[int(m.group(1))] = float(m.group(2))
    return got


def test_times_each_size_with_the_kernel_version(tmp_path):
    got = run("run", "--sizes", "8,16", "--repeat", "2")
    assert got.returncode == 0, got.stdout + got.stderr
    assert re.search(r"kernel [0-9a-f]{12}", got.stdout), got.stdout
    timed = sizes_timed(got.stdout)
    assert set(timed) == {8, 16}
    assert all(ms >= 0 for ms in timed.values()), "a measured time is never negative"
    assert "median of 2" in got.stdout


def test_the_sizes_and_repeat_are_respected(tmp_path):
    # 1 is allowed (a positive size); it is the smallest a pile can be
    got = run("run", "--sizes", "1,4,8", "--repeat", "3")
    assert got.returncode == 0, got.stderr
    assert set(sizes_timed(got.stdout)) == {1, 4, 8}  # exactly the sizes asked
    assert "median of 3" in got.stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in (
        [],  # nothing (no run verb)
        ["--sizes", "8"],  # options without the run verb
        ["run", "--sizes", "8,abc"],  # a size that isn't a number
        ["run", "--sizes", "0,8"],  # a size must be positive
        ["run", "--repeat", "0"],  # repeat must be at least 1
        ["run", "--stray"],  # an unknown flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "bench.py" in got.stderr, (argv, got.stderr)
