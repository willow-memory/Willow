"""red-on-main: a pull request's failing check is said to be red on main too,
the pull request's, or not on main's record, read from records whose chain
holds; a bad command line, no record or a broken one is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
TS = "2026-11-07T00:00:00Z"


def record(folder: Path, *verdicts: tuple[str, str]) -> Path:
    """A CI record as ci.py writes it: a kernel box, a verdict row per gate."""
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    folder.mkdir(parents=True)
    box, pile = folder / "box", folder / "pile"
    pile.mkdir()
    kernel.init(box, pile, folder / "key", TS)
    for gate, state in verdicts:
        kernel.append(box, TS, "verdict", who="ci", gate=gate, state=state,
                      files_sha256="0" * 64, said_sha256="0" * 64, python="3.13")  # fmt: skip
    return folder


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "red_on_main.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def test_each_failing_check_is_held_to_mains(tmp_path):
    pr = record(tmp_path / "pr", ("lint", "satisfied"), ("tests:alone", "failing"),
                ("tests:adapters-6", "failing"), ("deps:kart", "failing"))  # fmt: skip
    main = record(tmp_path / "main", ("lint", "satisfied"), ("tests:alone", "failing"),
                  ("tests:adapters-6", "satisfied"), ("deps:kart", "unreachable"))  # fmt: skip
    got = run("--pr", str(pr), "--main", str(main), "--main-sha", "1394b08abc")
    assert got.returncode == 42, got.stderr
    assert got.stdout.splitlines() == [
        "red-on-main: populated, 3 failing; 1 the pull request's, 1 red on main too, 1 not on main's record",
        "## the pull request's",
        "  tests:adapters-6  green on main: this change broke it",
        "## red on main too",
        "  tests:alone       red on main at 1394b08 too: not this change's",
        "## not on main's record",
        "  deps:kart         main's record says unreachable: look at it yourself",
    ]
    doc = json.loads(run("--pr", str(pr), "--main", str(main), "--json").stdout)
    assert doc["addon"] == "red-on-main" and doc["state"] == "populated"
    assert [g["name"] for g in doc["groups"]] == [
        "the pull request's",
        "red on main too",
        "not on main's record",
    ]


def test_a_failure_red_on_main_too_is_not_the_pull_requests(tmp_path):
    pr = record(tmp_path / "pr", ("tests:alone", "failing"))
    main = record(tmp_path / "main", ("tests:alone", "failing"))
    got = run("--pr", str(pr), "--main", str(main))
    assert got.returncode == 0
    assert "red on main too: not this change's" in got.stdout


def test_nothing_failing_is_empty(tmp_path):
    pr = record(tmp_path / "pr", ("lint", "satisfied"))
    main = record(tmp_path / "main", ("lint", "failing"))
    got = run("--pr", str(pr), "--main", str(main))
    assert (got.returncode, got.stdout) == (0, "red-on-main: empty, nothing failing\n")


def test_a_gate_mains_record_lacks_is_left_to_a_person(tmp_path):
    pr = record(tmp_path / "pr", ("demo:corwin", "failing"))
    main = record(tmp_path / "main", ("lint", "satisfied"))
    got = run("--pr", str(pr), "--main", str(main))
    assert got.returncode == 42
    assert "main's record doesn't hold it: look at it yourself" in got.stdout


def test_records_at_any_depth_and_the_last_verdict_of_a_gate_count(tmp_path):
    record(tmp_path / "pr" / "ci-record-tests-3.9", ("tests:alone", "failing"))
    main = tmp_path / "main"
    record(main / "a", ("tests:alone", "satisfied"))
    record(main / "b", ("tests:alone", "failing"))  # later in path order: the last
    got = run("--pr", str(tmp_path / "pr"), "--main", str(main))
    assert got.returncode == 0 and "red on main too" in got.stdout


def test_no_record_or_a_broken_one_is_refused(tmp_path):
    main = record(tmp_path / "main", ("lint", "satisfied"))
    (tmp_path / "empty").mkdir()
    got = run("--pr", str(tmp_path / "empty"), "--main", str(main))
    assert got.returncode == 2 and "no record.jsonl" in got.stderr
    pr = record(tmp_path / "pr", ("lint", "failing"))
    log = pr / "box" / "record.jsonl"
    lines = log.read_text().splitlines()
    lines[-1] = lines[-1].replace("failing", "satisfied")
    log.write_text("\n".join(lines) + "\n")
    got = run("--pr", str(pr), "--main", str(main))
    assert got.returncode == 2 and "refused:" in got.stderr


@pytest.mark.parametrize("argv", [[], ["--pr", "x"], ["--pr", "x", "--main"],
                                  ["--pr", "x", "--main", "y", "--other", "z"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = run(*argv)
    assert got.returncode == 2 and "red_on_main.py" in got.stderr
