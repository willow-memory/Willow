"""nestor: checked pairs only; drafts and signatures stay out of the mirror."""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "nestor.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write_store(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE tm_pairs (
            source_text TEXT, target_text TEXT, verifier TEXT,
            status TEXT, created_at TEXT, seal_sig TEXT
        );
        INSERT INTO tm_pairs VALUES
            ('tomatoes want sun', 'les tomates veulent le soleil',
             'ada', 'sealed', '2026-10-01T09:00:00Z', 'SIG-SHOULD-NOT-APPEAR'),
            ('draft line', 'borrador', '', 'draft', '2026-10-02T00:00:00Z', ''),
            ('pending line', 'pendiente', 'ada', 'pending',
             '2026-10-03T00:00:00Z', '');
        """
    )
    con.commit()
    con.close()


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def test_only_checked_pairs_are_mirrored_and_signatures_stay_out(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    write_store(folder / "nestor.db")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "nestor.db.txt").read_text(encoding="utf-8")
    assert text.startswith("nestor: 1 checked pair\n")
    assert "tomatoes want sun" in text
    assert "checked by: ada" in text
    assert "when: 2026-10-01" in text
    assert "draft line" not in text and "pending line" not in text
    assert "SIG-SHOULD-NOT-APPEAR" not in text


def test_a_store_with_no_checked_pair_is_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    con = sqlite3.connect(folder / "empty.db")
    con.execute(
        "CREATE TABLE tm_pairs (source_text TEXT, verifier TEXT, "
        "status TEXT, created_at TEXT)"
    )
    con.execute("INSERT INTO tm_pairs VALUES ('x', '', 'draft', '2026-10-01')")
    con.commit()
    con.close()
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 1"


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    write_store(folder / "nestor.db")
    before = (folder / "nestor.db").read_bytes()
    a, b = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, a).returncode == 0
    assert mirror(folder, b).returncode == 0
    assert (
        hashlib.sha256((a / "nestor.db.txt").read_bytes()).digest()
        == hashlib.sha256((b / "nestor.db.txt").read_bytes()).digest()
    )
    assert (folder / "nestor.db").read_bytes() == before


def test_kernel_serves_a_checked_pair(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "k",
    )
    folder.mkdir()
    write_store(folder / "nestor.db")
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "tomatoes want sun")
    assert got.returncode in (0, 42), got.stderr
    assert "checked by: ada" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
