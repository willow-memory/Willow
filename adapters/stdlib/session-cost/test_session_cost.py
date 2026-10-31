"""session-cost: tokens by day and repo from the session's own usage;
prices only from a table you keep."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "session_cost.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def session(tmp_path: Path) -> Path:
    folder = tmp_path / "s"
    folder.mkdir()
    lines = [
        {
            "type": "assistant",
            "timestamp": "2026-10-30T18:00:00Z",
            "cwd": "/home/ada/Willow",
            "model": "claude-opus-5-5",
            "message": {
                "role": "assistant",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        },
        {
            "type": "assistant",
            "timestamp": "2026-10-30T19:00:00Z",
            "cwd": "/home/ada/Willow",
            "model": "claude-opus-5-5",
            "message": {
                "role": "assistant",
                "usage": {"input_tokens": 20, "output_tokens": 10},
            },
        },
    ]
    (folder / "a.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8"
    )
    return folder


def test_tokens_are_summed_by_day_repo_and_model(tmp_path):
    folder = session(tmp_path)
    got = run("--from", str(folder))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "session-cost: 1 session, 1 day",
        "2026-10-30  Willow  claude-opus-5-5  in 120 out 60",
        "total  in 120 out 60",
    ]


def test_a_prices_table_adds_a_dollar_figure(tmp_path):
    folder = session(tmp_path)
    prices = tmp_path / "p.txt"
    prices.write_text("claude-opus-5-5 10000 20000\n", encoding="utf-8")
    got = run("--from", str(folder), "--prices", str(prices))
    assert got.returncode == 0
    # 120/1e6 * 10000 + 60/1e6 * 20000 = 1.20 + 1.20
    assert "  $2.40" in got.stdout


def test_nothing_there_when_no_usage(tmp_path):
    folder = tmp_path / "s"
    folder.mkdir()
    (folder / "a.jsonl").write_text(
        json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}})
        + "\n",
        encoding="utf-8",
    )
    got = run("--from", str(folder))
    assert got.returncode == 42
    assert "nothing there" in got.stdout


def test_usage_of_zero_tokens_is_not_a_session(tmp_path):
    folder = tmp_path / "s"
    folder.mkdir()
    (folder / "a.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-10-30T18:00:00Z",
                "cwd": "/home/ada/Willow",
                "model": "claude-opus-5-5",
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    got = run("--from", str(folder))
    assert got.returncode == 42
    assert "nothing there" in got.stdout


def test_two_repos_on_one_day_are_two_sessions_one_day(tmp_path):
    folder = session(tmp_path)
    (folder / "b.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-10-30T12:00:00Z",
                "cwd": "/home/ada/stdlib",
                "model": "claude-opus-5-5",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    got = run("--from", str(folder))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == "session-cost: 2 sessions, 1 day"
    assert "stdlib" in got.stdout and "Willow" in got.stdout


def test_hidden_folders_are_skipped(tmp_path):
    folder = session(tmp_path)
    hidden = folder / ".hidden"
    hidden.mkdir()
    (hidden / "b.jsonl").write_text(
        json.dumps(
            {
                "timestamp": "2026-10-31T00:00:00Z",
                "cwd": "/x/Other",
                "model": "other",
                "usage": {"input_tokens": 9, "output_tokens": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    got = run("--from", str(folder))
    assert got.returncode == 0
    assert "Other" not in got.stdout


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from"], ["--from", str(tmp_path), "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "session_cost.py" in got.stderr
    got = run("--from", str(tmp_path / "missing"))
    assert got.returncode == 2 and "not a folder" in got.stderr
