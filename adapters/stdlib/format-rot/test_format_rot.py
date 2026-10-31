"""format-rot: old and proprietary formats flagged; current office and
hidden files left alone."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "format_rot.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_old_office_and_apk_are_flagged(tmp_path):
    folder = tmp_path / "f"
    (folder / "old").mkdir(parents=True)
    (folder / "old" / "letter.doc").write_bytes(b"DOC")
    (folder / "old" / "app.apk").write_bytes(b"APK")
    (folder / "old" / "app.apk2").write_bytes(b"no")  # not a known ext
    (folder / "now.docx").write_bytes(b"DOCX")
    (folder / "now.pdf").write_bytes(b"%PDF")
    got = run("--from", str(folder))
    assert got.returncode == 42, got.stdout
    assert got.stdout.splitlines() == [
        "format-rot needs you: 2 files",
        "  .apk  1  no reader in this repository",
        "  .doc  1  old office; convert while it still opens",
    ]


def test_nothing_at_risk_holds(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "note.md").write_text("ok\n")
    got = run("--from", str(folder))
    assert got.returncode == 0
    assert "format-rot holds" in got.stdout


def test_hidden_parts_are_skipped(tmp_path):
    folder = tmp_path / "f"
    (folder / ".stash").mkdir(parents=True)
    (folder / ".stash" / "old.doc").write_bytes(b"DOC")
    (folder / "note.md").write_text("ok\n")
    got = run("--from", str(folder))
    assert got.returncode == 0


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from"], ["--from", str(tmp_path), "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "format_rot.py" in got.stderr
    got = run("--from", str(tmp_path / "missing"))
    assert got.returncode == 2 and "not a folder" in got.stderr
