"""corpus-lens: process reports as passages; session logs stay unread."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "corpus_lens.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]

MARKDOWN = """# corpuslens report

> This run read 21 events (dropped 0, counted not hidden), ran 6 process
> analyzers under profile 'default', and was granted nothing beyond process
> analysis.

## What this run found

- **steering_density** — 70.0% of your prompt turns arrive mid-task rather than in a session's opening prompt.
- **composition_mix** — You authored code in 0.0% of your prompts and referred to existing code in 0.0%; 10.0% deliberate before building.
"""

JSON_REPORT = {
    "schema_version": 1,
    "audit": "This run read 21 events (dropped 0, counted not hidden).",
    "results": {
        "steering_density": {
            "sentence": "70.0% of your prompt turns arrive mid-task rather than in a session's opening prompt."
        },
        "composition_mix": {"sentence": "You authored code in 0.0% of your prompts."},
    },
}


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def test_a_markdown_report_is_kept_as_passages(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "report.md").write_text(MARKDOWN, encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "report.md.txt").read_text(encoding="utf-8")
    assert text.startswith("# corpuslens report\n")
    assert "steering_density" in text
    assert "70.0% of your prompt turns arrive mid-task" in text
    assert "You authored code in 0.0% of your prompts" in text


def test_a_json_report_becomes_the_same_headlines(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "run.json").write_text(
        json.dumps(JSON_REPORT, indent=2) + "\n", encoding="utf-8"
    )
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "run.json.txt").read_text(encoding="utf-8")
    assert text.startswith("# corpuslens report\n")
    assert "steering_density:" in text
    assert "composition_mix:" in text
    assert "arrive mid-task" in text
    assert "noise:" not in text


def test_an_empty_result_is_not_a_finding(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    report = {
        "schema_version": 1,
        "audit": "This run read 21 events (dropped 0, counted not hidden).",
        "results": {
            "steering_density": {
                "sentence": "70.0% of your prompt turns arrive mid-task."
            },
            "noise": None,
            "blank": "",
        },
    }
    (folder / "run.json").write_text(json.dumps(report) + "\n", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "run.json.txt").read_text(encoding="utf-8")
    assert "steering_density:" in text
    assert "noise:" not in text and "blank:" not in text


def test_a_file_that_is_not_a_report_is_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "report.md").write_text(MARKDOWN, encoding="utf-8")
    (folder / "notes.md").write_text("just a note\n", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 1"


def test_hidden_reports_are_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / ".stash").mkdir(parents=True)
    (folder / ".stash" / "report.md").write_text(MARKDOWN, encoding="utf-8")
    folder.mkdir(exist_ok=True)
    (folder / "report.md").write_text(MARKDOWN, encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0
    made = [p.name for p in to.rglob("*.txt")]
    assert made == ["report.md.txt"]


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "report.md").write_text(MARKDOWN, encoding="utf-8")
    before = (folder / "report.md").read_bytes()
    a, b = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, a).returncode == 0
    assert mirror(folder, b).returncode == 0
    assert (
        hashlib.sha256((a / "report.md.txt").read_bytes()).digest()
        == hashlib.sha256((b / "report.md.txt").read_bytes()).digest()
    )
    assert (folder / "report.md").read_bytes() == before


def test_kernel_serves_where_intent_arrives(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "k",
    )
    folder.mkdir()
    (folder / "report.md").write_text(MARKDOWN, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "prompt turns arrive mid-task")
    assert got.returncode in (0, 42), got.stderr
    assert "steering_density" in got.stdout or "mid-task" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
