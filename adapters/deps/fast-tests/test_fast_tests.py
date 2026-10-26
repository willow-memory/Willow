"""fast-tests: the suite across every core with pytest-xdist. It runs the
PATHs in parallel and reports workers, cores and wall time; passes clean,
escalates on a failure or an empty suite, and refuses a bad command line. The
suite installs pytest-xdist, so these run under the deps gate's venv."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE / "fast_tests.py"

PASS = "def test_one():\n    assert 1 + 1 == 2\n\n\ndef test_two():\n    assert 'a' < 'b'\n"
FAIL = "def test_bad():\n    assert 1 == 2\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(FAST), *argv], capture_output=True, text=True
    )


def a_suite(tmp: Path, body: str) -> Path:
    """A folder with one trivial test file in it."""
    d = tmp / "suite"
    d.mkdir()
    (d / "test_sample.py").write_text(body, encoding="utf-8")
    return d


def test_a_passing_suite_runs_in_parallel_and_passes(tmp_path):
    suite = a_suite(tmp_path, PASS)
    got = run(str(suite), "--jobs", "2")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "passed" in got.stdout  # pytest's own summary came through
    assert "fast-tests: 2 workers over" in got.stdout  # its own footer


def test_jobs_auto_is_the_default_and_reports_cores(tmp_path):
    suite = a_suite(tmp_path, PASS)
    got = run(str(suite))  # no --jobs: auto
    assert got.returncode == 0, got.stdout + got.stderr
    assert "fast-tests:" in got.stdout and "core" in got.stdout


def test_a_failing_test_escalates(tmp_path):
    suite = a_suite(tmp_path, FAIL)
    got = run(str(suite), "--jobs", "2")
    assert got.returncode == 42, got.stdout + got.stderr
    assert "failed" in got.stdout


def test_an_empty_suite_escalates(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run(str(empty), "--jobs", "2")
    assert got.returncode == 42, got.stdout + got.stderr  # nothing collected


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    suite = a_suite(tmp_path, PASS)
    for argv in (
        [],  # no path
        ["--jobs", "2"],  # a job count but no path
        [str(suite), "--jobs", "0"],  # jobs must be positive
        [str(suite), "--jobs", "nope"],  # jobs must be auto or a number
        [str(suite), "--unknown"],  # an unknown flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "fast_tests.py" in got.stderr, (argv, got.stderr)
