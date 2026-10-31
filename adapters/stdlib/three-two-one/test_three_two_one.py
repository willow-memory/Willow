"""three-two-one: the box plus named copies, each counted only when its
record holds; three copies, two kinds, one away."""

from __future__ import annotations

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
        [sys.executable, str(HERE / "three_two_one.py"), *argv],
        capture_output=True,
        text=True,
    )


def box(tmp_path: Path, name: str = "box") -> Path:
    pile = tmp_path / f"{name}-pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / name
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / f"{name}.key"),
        "--now",
        "2026-10-24T09:30:00Z",
    )
    return b


def zip_of(tmp_path: Path, b: Path) -> Path:
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


def test_the_box_alone_needs_you(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b))
    assert got.returncode == 42, got.stderr
    assert got.stdout.splitlines()[0] == (
        "3-2-1 needs you: 1 copy on 1 kind of storage, none away from home"
    )
    assert "  disk  the box  holds (1 row)" in got.stdout


def test_three_copies_two_kinds_one_away_holds(tmp_path):
    b = box(tmp_path)
    z = zip_of(tmp_path, b)
    other = box(tmp_path, "offsite")
    got = run(
        "--box",
        str(b),
        "--copy",
        f"usb:{z}",
        "--copy",
        f"away:{other}",
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == (
        "3-2-1 holds: 3 copies on 3 kinds of storage, one away from home"
    )
    assert f"  usb   {z.name}  holds (1 row)" in got.stdout
    assert "  away  offsite  holds (1 row)" in got.stdout


def test_a_broken_copy_is_said_and_not_counted(tmp_path):
    b = box(tmp_path)
    z = zip_of(tmp_path, b)
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(z) as src, zipfile.ZipFile(bad, "w") as dst:
        for n in src.namelist():
            data = src.read(n)
            if n == "record.jsonl":
                data = data.replace(b'"boot"', b'"booT"', 1)
            dst.writestr(n, data)
    other = box(tmp_path, "offsite")
    got = run(
        "--box",
        str(b),
        "--copy",
        f"usb:{bad}",
        "--copy",
        f"away:{other}",
    )
    assert got.returncode == 42
    assert "1 copies failed" in got.stdout or "1 copy failed" in got.stdout
    assert "doesn't verify" in got.stdout
    assert "holds: 3 copies" not in got.stdout


def test_a_file_that_is_not_a_backup_is_nothing_there(tmp_path):
    b = box(tmp_path)
    other = tmp_path / "notes.txt"
    other.write_text("not a box\n")
    got = run("--box", str(b), "--copy", f"usb:{other}")
    assert got.returncode == 42
    assert "nothing there: not a box or a backup zip" in got.stdout


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    for argv in ([], ["--box"], ["--box", str(b), "x"], ["--copy", "usb:/x"]):
        got = run(*argv)
        assert got.returncode == 2 and "three_two_one.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    got = run("--box", str(b), "--copy", "nocolon")
    assert got.returncode == 2 and "KIND:PATH" in got.stderr
