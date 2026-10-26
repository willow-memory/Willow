"""index-cache: a folder's scan index kept between runs, rebuilt only when the
folder changed. It builds the first time, reports "current" when every indexed
file's hash still matches, rebuilds on an edit, add or removal (and says which),
ignores a change to a file the index never read, and refuses a bad command
line. The cached index answers through scan."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IC = HERE / "index_cache.py"
SCAN = HERE.parent / "scan" / "scan.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(IC), *argv], capture_output=True, text=True
    )


def a_folder(tmp: Path) -> tuple[Path, Path]:
    """A two-file folder and an index path beside it; (folder, index)."""
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "roof.md").write_text("2026-03-01 The roof estimate was 4200.\n")
    (folder / "mould.md").write_text("2026-03-02 Reported the mould.\n")
    return folder, tmp / "ix"


def cache(folder: Path, index: Path) -> subprocess.CompletedProcess:
    return run("--from", str(folder), "--to", str(index))


def test_it_builds_then_reports_current(tmp_path):
    folder, index = a_folder(tmp_path)
    first = cache(folder, index)
    assert first.returncode == 0 and "rebuilt" in first.stdout, (
        first.stdout + first.stderr
    )
    assert (index / "cache.json").exists() and (index / "index.json").exists()
    again = cache(folder, index)
    assert again.returncode == 0 and "current" in again.stdout, again.stdout


def test_an_edited_file_rebuilds(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / "mould.md").write_text("2026-03-02 The mould spread to the hall.\n")
    got = cache(folder, index)
    assert got.returncode == 0 and "rebuilt" in got.stdout
    assert "~1 changed" in got.stdout


def test_an_added_then_removed_file_each_rebuild(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / "garden.md").write_text("Tomatoes want sun.\n")
    added = cache(folder, index)
    assert added.returncode == 0 and "+1 new" in added.stdout
    (folder / "garden.md").unlink()
    removed = cache(folder, index)
    assert removed.returncode == 0 and "-1 removed" in removed.stdout


def test_a_change_to_an_unread_file_does_not_rebuild(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / ".hidden.md").write_text("a dotfile the index never read\n")
    (folder / "picture.bin").write_bytes(b"\x00\x01\x02binary\x00")
    got = cache(folder, index)
    assert got.returncode == 0 and "current" in got.stdout, got.stdout


def test_the_cached_index_answers_with_scan(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    qs = tmp_path / "q.txt"
    qs.write_text("roof estimate\n")
    got = subprocess.run(
        [sys.executable, str(SCAN), "scan", "--index", str(index),
         "--questions", str(qs), "--top", "1"],
        capture_output=True, text=True,
    )  # fmt: skip
    assert got.returncode == 0 and "roof estimate was 4200" in got.stdout


def test_an_empty_folder_escalates(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    got = cache(folder, tmp_path / "ix")
    assert got.returncode == 42, got.stdout + got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    folder, index = a_folder(tmp_path)
    for argv in (
        [],  # nothing
        ["--from", str(folder)],  # no --to
        ["--to", str(index)],  # no --from
        ["--from", str(folder), "--to", str(index), "--stray"],  # unknown flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "index_cache.py" in got.stderr, (
            argv,
            got.stderr,
        )


def test_a_from_that_is_not_a_folder_is_refused(tmp_path):
    got = run("--from", str(tmp_path / "missing"), "--to", str(tmp_path / "ix"))
    assert got.returncode == 2 and "is not a folder" in got.stderr
