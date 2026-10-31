"""restore-drill: a backup zip unzipped into scratch; the chain holds;
nothing written beside the zip; a zip that isn't a backup is nothing there."""

from __future__ import annotations

import io
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
BACKUP = HERE.parent / "backup" / "backup.py"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "restore_drill.py"), *argv],
        capture_output=True,
        text=True,
    )


def life(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "key"),
        "--now",
        "2026-10-24T09:30:00Z",
    )
    dest = tmp_path / "usb"
    got = subprocess.run(
        [
            sys.executable,
            str(BACKUP),
            "--box",
            str(b),
            "--to",
            str(dest),
            "--now",
            "2026-10-24T09:30:00Z",
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return next(dest.glob("*.zip"))


def test_a_backup_zip_restores_and_the_chain_holds(tmp_path):
    z = life(tmp_path)
    before = z.read_bytes()
    got = run("--from", str(z))
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == (
        f"restored: {z.name}, 2 files, 1 row; the chain holds"
    )
    assert z.read_bytes() == before
    assert list((tmp_path / "usb").iterdir()) == [z]


def test_a_broken_record_fails_the_drill(tmp_path):
    z = life(tmp_path)
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(z) as src, zipfile.ZipFile(bad, "w") as dst:
        for n in src.namelist():
            data = src.read(n)
            if n == "record.jsonl":
                data = data.replace(b'"boot"', b'"booT"', 1)
            dst.writestr(n, data)
    got = run("--from", str(bad))
    assert got.returncode == 42
    assert "doesn't verify" in got.stdout


def test_a_member_that_leaves_the_zip_fails(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("kernel.json", "{}")
        z.writestr("record.jsonl", "{}\n")
        z.writestr("../escape.txt", "no\n")
    evil = tmp_path / "evil.zip"
    evil.write_bytes(buf.getvalue())
    got = run("--from", str(evil))
    assert got.returncode == 42
    assert "leaves the zip" in got.stdout
    assert not (tmp_path / "escape.txt").exists()


def test_not_a_zip_and_not_a_backup_are_nothing_there(tmp_path):
    note = tmp_path / "notes.txt"
    note.write_text("not a zip\n")
    got = run("--from", str(note))
    assert got.returncode == 42 and "nothing there: not a zip" in got.stdout
    empty = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty, "w") as z:
        z.writestr("readme.txt", "hi\n")
    got = run("--from", str(empty))
    assert got.returncode == 42 and "not a willow backup" in got.stdout


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    z = life(tmp_path)
    for argv in ([], ["--from"], ["--from", str(z), "x"]):
        got = run(*argv)
        assert got.returncode == 2 and "restore_drill.py" in got.stderr
    got = run("--from", str(tmp_path / "missing.zip"))
    assert got.returncode == 2 and "not a file" in got.stderr
