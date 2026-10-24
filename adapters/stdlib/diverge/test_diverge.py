"""diverge: where two copies part, records by row, then files, then the
first differing line; a folder or a zip on either side; a key never read."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("diverge", HERE / "diverge.py")
dv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dv)
NOW = ["--now", "2026-10-24T09:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "diverge.py"), *argv],
        capture_output=True,
        text=True,
    )


def willow(tmp_path: Path, name: str) -> Path:
    """A start-like folder: a box and its key side by side."""
    home = tmp_path / name
    pile = tmp_path / "pile"
    pile.mkdir(exist_ok=True)
    (pile / "n.txt").write_text("The dentist is on Tuesday.\n")
    k(
        "init",
        "--box",
        str(home / "box"),
        "--pile",
        str(pile),
        "--key",
        str(home / "key"),
        *NOW,
    )
    k("bite", "--box", str(home / "box"), *NOW, "when is the dentist")
    return home


def zipped(box: Path, to: Path) -> Path:
    with zipfile.ZipFile(to, "w") as z:
        for p in sorted(box.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(box).as_posix())
    return to


def test_a_box_and_its_backup_are_the_same_until_the_box_moves_on(tmp_path):
    box = willow(tmp_path, "w") / "box"
    z = zipped(box, tmp_path / "backup.zip")
    got = run(str(box), str(z))
    assert got.returncode == 0 and "The same: every file, byte for byte." in got.stdout
    k("bite", "--box", str(box), *NOW, "when is the dentist")
    got = run(str(z), str(box))
    assert got.returncode == 42
    assert (
        got.stdout.splitlines()[0]
        == "records: the same for 2 rows, then B runs on 1 more"
    )


def test_records_that_part_say_at_which_row(tmp_path):
    a, b = willow(tmp_path, "a") / "box", willow(tmp_path, "b") / "box"
    said = dv.compare(dv.load(a), dv.load(b))
    # the same files at the same time make the same record: only the key's place differs
    assert said[0] == "differ:     kernel.json (first at line 1)"
    rows = (a / "record.jsonl").read_text().splitlines()
    (tmp_path / "c").mkdir()
    shutil.copy(a / "kernel.json", tmp_path / "c" / "kernel.json")
    (tmp_path / "c" / "record.jsonl").write_text(
        rows[0] + "\n" + rows[1].replace('"bite"', '"bitE"') + "\n"
    )
    assert (
        dv.compare(dv.load(a), dv.load(tmp_path / "c"))[0]
        == "records: the same for 1 rows, then part at row 1"
    )


def test_files_then_the_first_line_that_differs(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        (d / "notes").mkdir(parents=True)
        (d / "same.txt").write_text("x\n")
        (d / ".git").mkdir()
    (a / ".git" / "x").write_text("1")
    (b / ".git" / "x").write_text("2")  # hidden: not compared
    (a / "notes" / "todo.txt").write_text("Milk\nEggs\nCall the bank\n")
    (b / "notes" / "todo.txt").write_text("Milk\nEggs\nCall the bank on Monday\n")
    (a / "notes" / "z.txt").write_text("a\n")
    (b / "notes" / "z.txt").write_text("b\n")
    (a / "old.txt").write_text("gone\n")
    (b / "photo.jpg").write_bytes(b"\xff\xd8")
    assert dv.compare(dv.load(a), dv.load(b)) == [
        "only in A:  old.txt",
        "only in B:  photo.jpg",
        "differ:     notes/todo.txt (first at line 3)",
        "  A: Call the bank",
        "  B: Call the bank on Monday",
        "differ:     notes/z.txt",
    ]


def test_a_file_that_ends_early_or_isnt_text(tmp_path):
    assert dv.first_line(b"a\nb\n", b"a\n") == (2, "b", "(the file ends)")
    assert dv.first_line(b"\xff\xfe", b"x") is None
    assert dv.first_line(b"a", b"a\n") is None


@pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0, reason="needs a file root can't read"
)
def test_a_key_beside_the_box_is_never_read(tmp_path):
    a, b = willow(tmp_path, "a"), willow(tmp_path, "b")
    (a / "key").chmod(0)  # reading it would raise
    said = dv.compare(dv.load(a), dv.load(b))
    assert not any("key" == line.split()[-1] for line in said)


def test_a_key_beside_the_box_is_left_out(tmp_path):
    a = willow(tmp_path, "a")
    assert "key" not in dv.load(a) and "box/kernel.json" in dv.load(a)


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in (
        [],
        [str(tmp_path)],
        [str(tmp_path), str(tmp_path), "x"],
        ["--a", str(tmp_path)],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "diverge.py" in got.stderr
    (tmp_path / "f.txt").write_text("x")
    got = run(str(tmp_path), str(tmp_path / "f.txt"))
    assert got.returncode == 2 and "neither a folder nor a zip" in got.stderr


def test_records_parting_at_their_first_row():
    assert (
        dv.chains(b"x\ny\n", b"z\ny\n")
        == "records: the same for 0 rows, then part at row 0"
    )
    assert dv.chains(b"x\n", b"x\n") == "records: the same, 1 rows"
