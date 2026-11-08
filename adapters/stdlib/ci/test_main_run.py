"""main_run.py: main's records found in its push run, or in the merge queue's
run of the same commit when the push stood on it; asked of a fake gh."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "main_run.py"

#: gh, answering from gh.json: `run list` by event (and --commit), and `api`
#: for a run's artifacts; every call kept
GH = """import json, os, sys
from pathlib import Path
state = Path(os.environ["FAKE_GH"])
s = json.loads(state.read_text())
s["calls"].append(sys.argv[1:])
state.write_text(json.dumps(s))
a = sys.argv[1:]
if os.environ.get("FAKE_GH_FAIL"):
    print("HTTP 401: Bad credentials", file=sys.stderr)
    sys.exit(1)
if a[:2] == ["run", "list"]:
    event = a[a.index("--event") + 1]
    limit = int(a[a.index("--limit") + 1])
    rows = [r for r in s["runs"] if r["event"] == event]
    if "--commit" in a:
        rows = [r for r in rows if r["headSha"] == a[a.index("--commit") + 1]]
    if "--branch" in a:
        rows = [r for r in rows if r.get("branch") == a[a.index("--branch") + 1]]
    print(json.dumps([{"databaseId": r["id"], "headSha": r["headSha"]} for r in rows[:limit]]))
elif a[0] == "api":
    run = a[1].split("/")[-2]
    for name, expired in s["artifacts"].get(run, []):
        if not expired:
            print(name)
"""


@pytest.fixture
def fake(tmp_path):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "gh").write_text(f"#!{sys.executable}\n" + GH, encoding="utf-8")
    (bin_ / "gh").chmod(0o755)
    state = tmp_path / "gh.json"

    def run(runs, artifacts, *argv, fail=False, gh=True):
        state.write_text(
            json.dumps({"runs": runs, "artifacts": artifacts, "calls": []})
        )
        path = str(bin_) + os.pathsep + os.environ["PATH"] if gh else str(tmp_path / "none")  # fmt: skip
        env = {**os.environ, "PATH": path, "FAKE_GH": str(state),
               **({"FAKE_GH_FAIL": "1"} if fail else {})}  # fmt: skip
        got = subprocess.run([sys.executable, str(SCRIPT), "--repo", "o/r", *argv],
                             env=env, capture_output=True, text=True)  # fmt: skip
        return got, json.loads(state.read_text())["calls"]

    return run


def push(id_, sha):
    return {"id": id_, "headSha": sha, "event": "push", "branch": "main"}


def queued(id_, sha):
    return {"id": id_, "headSha": sha, "event": "merge_group", "branch": f"gh-readonly-queue/main/pr-1-{sha}"}  # fmt: skip


def test_a_push_run_that_kept_its_records_is_the_one(fake):
    got, _ = fake([push(9, "c9"), queued(8, "c9")],
                  {"9": [["ci-record-mutants-1", False]], "8": [["ci-record-mutants-1", False]]},
                  "--artifact", "ci-record-mutants-*")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == "9 c9"


def test_a_push_that_stood_on_the_queue_reads_the_queues_run_of_its_commit(fake):
    got, calls = fake([push(9, "c9"), queued(8, "c9"), queued(7, "other")],
                      {"9": [], "8": [["test-times", False]], "7": [["test-times", False]]},
                      "--artifact", "test-times")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == "8 c9", "the queue's run of the push's own commit"
    listed = [c for c in calls if c[:2] == ["run", "list"]]
    assert ["--event", "merge_group", "--commit", "c9"] == listed[1][listed[1].index("--event"):listed[1].index("--event") + 4]  # fmt: skip
    assert all("--status" in c and "success" in c for c in listed), "green runs only"


def test_it_goes_back_past_a_commit_neither_run_of_holds(fake):
    got, _ = fake([push(9, "c9"), push(6, "c6"), queued(8, "c9")],
                  {"9": [], "8": [["ci-record-deps", True]], "6": [["ci-record-deps", False]]},
                  "--artifact", "ci-record-deps")  # fmt: skip
    assert got.returncode == 0 and got.stdout.strip() == "6 c6", (
        "an expired artifact holds nothing"
    )


def test_none_held_is_42_and_says_so(fake):
    got, _ = fake([push(9, "c9")], {"9": [["ci-record-lint", False]]}, "--artifact", "ci-record-mutants-*")  # fmt: skip
    assert got.returncode == 42 and got.stdout == ""
    assert "none of main's last 10 green runs holds ci-record-mutants-*" in got.stderr
    got, calls = fake([push(9, "c9"), push(6, "c6")], {}, "--artifact", "x", "--limit", "1")  # fmt: skip
    assert got.returncode == 42 and "last 1 green runs" in got.stderr
    assert not any("c6" in c for c in calls), "it stops at the limit"


def test_only_mains_own_push_runs_are_read(fake):
    """A fork's pull request can upload an artifact of any name: its runs
    are never main's push runs, so they're never read."""
    got, calls = fake([{"id": 5, "headSha": "f5", "event": "pull_request", "branch": "main"}],
                      {"5": [["ci-record-deps", False]]}, "--artifact", "ci-record-deps")  # fmt: skip
    assert got.returncode == 42
    first = calls[0]
    assert first[first.index("--branch") + 1] == "main" and first[first.index("--event") + 1] == "push"  # fmt: skip


def test_gh_missing_or_failing_is_unreachable_not_none(fake):
    got, _ = fake([push(9, "c9")], {}, "--artifact", "x", gh=False)
    assert got.returncode == 42 and "unreachable: gh isn't installed" in got.stderr
    got, _ = fake([push(9, "c9")], {}, "--artifact", "x", fail=True)
    assert got.returncode == 42 and "unreachable: gh run list" in got.stderr
    assert "Bad credentials" in got.stderr


@pytest.mark.parametrize("argv", [[], ["--artifact"], ["--artifact", "--repo"], ["--limit", "3"],
                                  ["--artifact", "x", "--limit", "0"], ["--artifact", "x", "--limit", "many"],
                                  ["--artifact", "x", "--stray", "y"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "main_run.py" in got.stderr
