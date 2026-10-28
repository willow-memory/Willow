"""cores.py's tests: every gate once across the shards, the run's verdicts
in ci.py's order, never more shards than gates, and refusals that run nothing."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cores", HERE / "cores.py")
cores = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cores)
ci, k = cores.ci, cores.kernel
NOW = "2026-10-23T00:00:00Z"


def cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "cores.py"), *argv],
        capture_output=True,
        text=True,
    )


def gates_in(box: Path) -> list[str]:
    return [r["gate"] for r in k.read(box / "record.jsonl")[0][1:]]


def test_each_shard_writes_its_own_gates_and_every_one_is_shown_once(tmp_path):
    box = tmp_path / "runs"
    got = cli("demo", "--jobs", "2", "--box", str(box), "--now", NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    for n in (1, 2):
        assert gates_in(box / str(n)) == ci.select(["demo"], [], f"{n}/2")
        assert f"══ shard {n} of 2: exit 0" in got.stdout
    every = ci.select(["demo"], [], None)
    table = got.stdout.split("══")[-1].strip().splitlines()[-len(every) - 1 :]
    assert [line.split()[0] for line in table[:-1]] == every
    assert all(line.split()[1] == ci.SATISFIED for line in table[:-1])
    assert (
        table[-1] == f"{len(every)} satisfied, 0 unreachable, 0 failing, in 2 records"
    )


def test_never_more_shards_than_gates(tmp_path):
    box = tmp_path / "runs"
    got = cli("lint:check", "--jobs", "4", "--box", str(box), "--now", NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert sorted(p.name for p in box.iterdir()) == ["1", "1.key"]
    assert gates_in(box / "1") == ["lint:check"]
    assert got.stdout.rstrip().endswith(
        "1 satisfied, 0 unreachable, 0 failing, in 1 records"
    )


def test_what_is_left_out_is_not_run(tmp_path):
    box = tmp_path / "runs"
    got = cli("lint", "--without", "lint:format", "--box", str(box), "--now", NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert gates_in(box / "1") == ["lint:check"]


@pytest.mark.parametrize("argv", [[], ["demo"], ["--jobs", "0"], ["--jobs", "x"], ["--jobs"],
                                  ["demo:nobody"], ["--without", "demo"], ["--stray"]])  # fmt: skip
def test_what_it_doesnt_know_is_refused_and_runs_nothing(tmp_path, argv):
    box = tmp_path / "runs"
    with_box = argv if argv in ([], ["demo"]) else [*argv, "--box", str(box)]
    got = cli(*with_box)
    assert got.returncode == k.REFUSED
    assert not box.exists(), "refused before any shard starts"
    assert got.stderr.startswith(
        ("refused: ", "    python adapters/stdlib/ci/cores.py")
    )
