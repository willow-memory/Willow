"""fixity: every file hashed on the first check, then rot (bytes moved,
mtime did not) told from an edit; hashes on the record, never the words."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("fixity", HERE / "fixity.py")
fx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fx)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "fixity.py"), *argv],
        capture_output=True,
        text=True,
    )


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    (pile / "care").mkdir(parents=True)
    (pile / "care" / "log.txt").write_text("Pills at 8.\n")
    (pile / "notes.txt").write_text("Tuesday.\n")
    (pile / ".hidden").mkdir()
    (pile / ".hidden" / "x.txt").write_text("not counted\n")
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            "--now",
            "2026-10-20T09:12:00Z",
        ],
        check=True,
        capture_output=True,
    )
    return pile, b


def rows(b: Path) -> list[dict]:
    return [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]


def test_the_first_check_hashes_every_file_and_skips_hidden(tmp_path):
    pile, b = make(tmp_path)
    got = run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    assert got.returncode == 0 and "First fixity check: 2 files" in got.stdout
    row = rows(b)[-1]
    assert row["kind"] == "fixity" and row["who"] == "fixity"
    assert sorted(row["files"]) == ["care/log.txt", "notes.txt"]
    assert "hash" in row["files"]["notes.txt"]
    assert ".hidden/x.txt" not in row["files"]


def test_a_hash_change_with_no_newer_mtime_is_rot(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    log = pile / "care" / "log.txt"
    was = log.stat().st_mtime_ns
    log.write_text("Pills at 9.\n")
    os.utime(log, ns=(was, was))
    got = run("--box", str(b), "--now", "2026-10-21T10:00:00Z")
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "Fixity needs you:",
        "  rot      care/log.txt",
    ]


def test_a_hash_change_with_a_newer_mtime_is_an_edit(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    log = pile / "care" / "log.txt"
    later = log.stat().st_mtime_ns + 1_000_000_000
    log.write_text("Pills at 9.\n")
    os.utime(log, ns=(later, later))
    got = run("--box", str(b), "--now", "2026-10-21T10:00:00Z")
    assert got.returncode == 42
    assert "  edited   care/log.txt" in got.stdout
    assert "rot" not in got.stdout


def test_gone_and_new_are_said_and_a_match_holds(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    (pile / "notes.txt").unlink()
    (pile / "bank.txt").write_text("Statement.\n")
    got = run("--box", str(b), "--now", "2026-10-21T00:00:00Z")
    assert got.returncode == 42
    assert "  gone     notes.txt" in got.stdout
    assert "  new      bank.txt" in got.stdout
    again = run("--box", str(b), "--now", "2026-10-22T00:00:00Z")
    assert again.returncode == 0
    assert (
        "Fixity holds: 2 files match the last check (2026-10-21 00:00)." in again.stdout
    )


def test_no_words_of_a_file_reach_the_record_and_the_chain_holds(tmp_path):
    pile, b = make(tmp_path)
    run("--box", str(b), "--now", "2026-10-20T09:12:00Z")
    text = (b / "record.jsonl").read_text()
    assert "Pills" not in text and "Tuesday" not in text
    assert (
        subprocess.run(
            [sys.executable, str(KERNEL), "verify", "--box", str(b)],
            capture_output=True,
        ).returncode
        == 0
    )


def test_a_broken_record_is_refused(tmp_path):
    pile, b = make(tmp_path)
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"boot"', b'"booT"', 1))
    got = run("--box", str(b))
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--box"], ["--box", str(tmp_path), "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "fixity.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
