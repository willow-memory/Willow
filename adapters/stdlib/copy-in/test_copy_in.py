"""copy-in: a new file is copied and logged with its hash; the log keeps a
file (its path and its bytes) from coming in twice, even once deleted from
DIR; the same bytes at two paths are two files; nothing is deleted
or replaced, a changed file goes beside the first; --dry-run writes
nothing; --json is the same report; a bad command line is refused."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = str(HERE / "copy_in.py")


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, *argv], capture_output=True, text=True
    )


def phone(tmp_path: Path, files: dict) -> Path:
    src = tmp_path / "Download"
    src.mkdir(exist_ok=True)
    for rel, text in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(text)
    return src


def log(dst: Path) -> list[dict]:
    return [json.loads(x) for x in (dst / "copied-in.jsonl").read_text().splitlines()]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_a_new_file_is_copied_and_logged_with_its_hash(tmp_path):
    src = phone(tmp_path, {"a.txt": "one", "docs/b.pdf": "two"})
    dst = tmp_path / "phone"
    got = run("--from", str(src), "--to", str(dst))
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("copy-in: populated, copied 2 new files, 0 already in")
    assert (dst / "a.txt").read_text() == "one"
    assert (dst / "docs/b.pdf").read_text() == "two"
    assert (src / "a.txt").read_text() == "one"  # copied, never moved
    rows = log(dst)
    assert [(r["from"], r["to"], r["sha256"], r["size"]) for r in rows] == [
        ("a.txt", "a.txt", digest("one"), 3),
        ("docs/b.pdf", "docs/b.pdf", digest("two"), 3),
    ]


def test_a_second_run_copies_nothing_and_a_deleted_copy_stays_deleted(tmp_path):
    src = phone(tmp_path, {"a.txt": "one", "b.txt": "two"})
    dst = tmp_path / "phone"
    assert run("--from", str(src), "--to", str(dst)).returncode == 0
    (dst / "a.txt").unlink()
    again = run("--from", str(src), "--to", str(dst))
    assert again.returncode == 0
    assert "copied 0 new files, 2 already in" in again.stdout
    assert not (dst / "a.txt").exists()
    assert len(log(dst)) == 2


def test_a_file_moved_on_the_other_device_comes_in_at_its_new_path(tmp_path):
    src = phone(tmp_path, {"a.txt": "one"})
    dst = tmp_path / "phone"
    run("--from", str(src), "--to", str(dst))
    (src / "a.txt").rename(src / "moved.txt")
    got = run("--from", str(src), "--to", str(dst))
    assert "copied 1 new files, 0 already in" in got.stdout
    assert (dst / "moved.txt").read_text() == "one"
    assert (dst / "a.txt").read_text() == "one"  # the old copy stays
    again = run("--from", str(src), "--to", str(dst))
    assert "copied 0 new files, 1 already in" in again.stdout


def test_a_changed_file_goes_beside_the_first_and_neither_is_replaced(tmp_path):
    src = phone(tmp_path, {"notes.md": "first", "x": "no suffix"})
    dst = tmp_path / "phone"
    run("--from", str(src), "--to", str(dst))
    (src / "notes.md").write_text("second")
    (src / "x").write_text("changed")
    got = run("--from", str(src), "--to", str(dst))
    assert got.returncode == 0
    assert "## beside an earlier copy" in got.stdout
    assert "as notes (2).md: different bytes" in got.stdout
    assert (dst / "notes.md").read_text() == "first"
    assert (dst / "notes (2).md").read_text() == "second"
    assert (dst / "x (2)").read_text() == "changed"
    (src / "notes.md").write_text("third")
    run("--from", str(src), "--to", str(dst))
    assert (dst / "notes (3).md").read_text() == "third"
    assert (dst / "notes (2).md").read_text() == "second"


def test_a_file_gone_from_the_folder_is_left_in_dir(tmp_path):
    src = phone(tmp_path, {"a.txt": "one"})
    dst = tmp_path / "phone"
    run("--from", str(src), "--to", str(dst))
    (src / "a.txt").unlink()
    got = run("--from", str(src), "--to", str(dst))
    assert got.returncode == 0
    assert (dst / "a.txt").read_text() == "one"


def test_the_same_bytes_at_two_paths_are_two_files_both_copied(tmp_path):
    src = phone(tmp_path, {"run-1/machine.json": "same", "run-2/machine.json": "same"})
    dst = tmp_path / "phone"
    got = run("--from", str(src), "--to", str(dst))
    assert "copied 2 new files" in got.stdout
    assert (dst / "run-1/machine.json").read_text() == "same"
    assert (dst / "run-2/machine.json").read_text() == "same"
    assert [r["from"] for r in log(dst)] == ["run-1/machine.json", "run-2/machine.json"]


def test_the_same_file_already_there_unlogged_is_logged_not_copied(tmp_path):
    src = phone(tmp_path, {"a.txt": "one", "b.txt": "two"})
    dst = tmp_path / "phone"
    dst.mkdir()
    (dst / "a.txt").write_text("one")
    (dst / "b.txt").write_text("other")
    got = run("--from", str(src), "--to", str(dst))
    assert "a.txt  already there, now logged" in got.stdout
    assert (dst / "b.txt").read_text() == "other"
    assert (dst / "b (2).txt").read_text() == "two"
    assert {r["to"] for r in log(dst)} == {"a.txt", "b (2).txt"}


def test_dry_run_says_the_same_and_writes_nothing(tmp_path):
    src = phone(tmp_path, {"a.txt": "one", "b.txt": "two"})
    dst = tmp_path / "phone"
    got = run("--from", str(src), "--to", str(dst), "--dry-run")
    assert got.returncode == 0
    assert got.stdout.startswith("copy-in: populated, would copy 2 new files")
    assert not dst.exists()


def test_json_is_the_same_report(tmp_path):
    src = phone(tmp_path, {"a.txt": "one"})
    dst = tmp_path / "phone"
    doc = json.loads(
        run("--from", str(src), "--to", str(dst), "--json", "--dry-run").stdout
    )
    assert doc["addon"] == "copy-in" and doc["state"] == "populated"
    assert doc["groups"] == [
        {"name": "would copy", "rows": [{"where": "a.txt", "what": "would copy"}]}
    ]


def test_a_skipped_prefix_is_counted_and_not_copied(tmp_path):
    src = phone(tmp_path, {"a.txt": "one", "phone-homecoming/r.jsonl": "deposit"})
    dst = tmp_path / "phone"
    got = run("--from", str(src), "--to", str(dst), "--skip", "phone-homecoming/")
    assert "1 skipped" in got.stdout
    assert not (dst / "phone-homecoming").exists()


def test_a_link_is_not_followed_and_said(tmp_path):
    src = phone(tmp_path, {"a.txt": "one"})
    outside = tmp_path / "secret.txt"
    outside.write_text("not the phone's")
    os.symlink(outside, src / "link.txt")
    dst = tmp_path / "phone"
    got = run("--from", str(src), "--to", str(dst))
    assert got.returncode == 42
    assert "link.txt  a link, not followed" in got.stdout
    assert not (dst / "link.txt").exists()


def test_an_empty_folder_is_empty(tmp_path):
    src = phone(tmp_path, {})
    got = run("--from", str(src), "--to", str(tmp_path / "phone"))
    assert got.returncode == 0
    assert got.stdout.startswith("copy-in: empty, copied 0 new files")


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    got = run()
    assert got.returncode == 2 and "copy_in.py" in got.stderr
    src = phone(tmp_path, {"a.txt": "one"})
    assert run("--from", str(src)).returncode == 2
    assert (
        run("--from", str(src), "--to", str(tmp_path / "d"), "--odd", "x").returncode
        == 2
    )
    assert (
        run("--from", str(tmp_path / "none"), "--to", str(tmp_path / "d")).returncode
        == 2
    )
    assert run("--from", str(src), "--to", str(src / "inside")).returncode == 2
    assert (
        run("--from", str(src), "--to", str(tmp_path / "no" / "parent")).returncode == 2
    )
    (tmp_path / "file").write_text("x")
    assert run("--from", str(src), "--to", str(tmp_path / "file")).returncode == 2


def test_a_log_it_did_not_write_is_refused(tmp_path):
    src = phone(tmp_path, {"a.txt": "one"})
    dst = tmp_path / "phone"
    dst.mkdir()
    (dst / "copied-in.jsonl").write_text("not json\n")
    got = run("--from", str(src), "--to", str(dst))
    assert got.returncode == 2 and "a line this didn't write" in got.stderr
    assert not (dst / "a.txt").exists()
