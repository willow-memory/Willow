"""pile-store: a folder's passages kept in one SQLite file. It builds the first
time, reports "current" while every read file's hash still matches, builds
again on an edit, an added or removed file, another folder or another
kernel.py, stores a repeated text once while naming each place, gives back
exactly the kernel's passages and dates, writes nothing with --check, and
refuses to overwrite a file that is not a store."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PS = HERE / "pile_store.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402
import pile_store  # noqa: E402

MEMO = "Order more jars before the market."


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PS), *argv], capture_output=True, text=True
    )


def a_folder(tmp: Path) -> tuple[Path, Path]:
    """A folder with one text in two places, and a store path beside it."""
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "roof.md").write_text("2026-03-01 The roof estimate was 4200.\n")
    (folder / "may.md").write_text(f"2026-05-01\n\n{MEMO}\n")
    (folder / "june.md").write_text(f"2026-06-01\n\n{MEMO}\n")
    return folder, tmp / "pile.sqlite"


def store(folder: Path, at: Path, *more: str) -> subprocess.CompletedProcess:
    return run("--from", str(folder), "--to", str(at), *more)


def test_it_builds_then_reports_current(tmp_path):
    folder, at = a_folder(tmp_path)
    first = store(folder, at)
    assert first.returncode == 0 and first.stdout.startswith("built 5 passages"), (
        first.stdout + first.stderr
    )
    assert "(4 texts, each stored once)" in first.stdout
    again = store(folder, at)
    assert again.returncode == 0 and again.stdout.startswith("current"), again.stdout


def test_a_repeat_is_stored_once_and_named_from_each_place(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    db = sqlite3.connect(at)
    texts = [t for (t,) in db.execute("SELECT text FROM texts")]
    places = db.execute(
        "SELECT p.path FROM passages p JOIN texts t ON t.id = p.id"
        " WHERE t.text = ? ORDER BY p.path",
        (MEMO,),
    ).fetchall()
    db.close()
    assert texts.count(MEMO) == 1 and len(texts) == 4
    assert places == [("june.md",), ("may.md",)]


def test_load_gives_the_kernels_passages_and_dates(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    got = pile_store.load(at, folder)
    pile = kernel.chunks(folder)
    assert got == [{**c, "date": d} for c, d in zip(pile, kernel.dates(pile))]
    assert any(c["date"] for c in got)


def test_an_edit_an_addition_and_a_removal_each_build_again(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    (folder / "roof.md").write_text("2026-03-01 The roof estimate was 5100.\n")
    assert pile_store.load(at, folder) is None
    assert pile_store.stale(at, folder) == "+0 new, ~1 changed, -0 removed"
    got = store(folder, at)
    assert got.returncode == 0 and "~1 changed" in got.stdout, got.stdout
    assert any("5100" in c["text"] for c in pile_store.load(at, folder))
    (folder / "garden.md").write_text("Tomatoes want sun.\n")
    assert "+1 new" in store(folder, at).stdout
    (folder / "garden.md").unlink()
    assert "-1 removed" in store(folder, at).stdout
    assert store(folder, at).stdout.startswith("current")


def test_a_file_the_kernel_never_reads_changes_nothing(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    (folder / ".hidden").write_text("not read\n")
    (folder / "photo.bin").write_bytes(b"\0\1\2")
    assert pile_store.stale(at, folder) is None
    assert store(folder, at).stdout.startswith("current")


def test_another_folder_or_another_kernel_builds_again(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    twin = tmp_path / "twin"
    twin.mkdir()
    for p in folder.iterdir():
        (twin / p.name).write_bytes(p.read_bytes())
    assert pile_store.stale(at, twin) == "made from another folder"
    db = sqlite3.connect(at)
    db.execute("UPDATE meta SET v = 'old' WHERE k = 'kernel'")
    db.commit()
    db.close()
    assert pile_store.stale(at, folder) == "made with another kernel.py"
    got = store(folder, at)
    assert "(made with another kernel.py)" in got.stdout, got.stdout
    assert pile_store.stale(at, folder) is None


def test_a_changed_limit_builds_again(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    db = sqlite3.connect(at)
    db.execute("UPDATE meta SET v = '9' WHERE k = 'max_chunk'")
    db.commit()
    db.close()
    assert pile_store.stale(at, folder) == "max_chunk changed"
    assert pile_store.load(at, folder) is None


def test_check_says_which_and_writes_nothing(tmp_path):
    folder, at = a_folder(tmp_path)
    got = store(folder, at, "--check")
    assert got.returncode == 42 and got.stdout == "stale: no store yet\n"
    assert not at.exists() and sorted(tmp_path.iterdir()) == [folder]
    store(folder, at)
    (folder / "roof.md").write_text("2026-03-01 Fixed.\n")
    before = at.read_bytes()
    got = store(folder, at, "--check")
    assert got.returncode == 42 and "~1 changed" in got.stdout
    assert at.read_bytes() == before
    store(folder, at)
    assert store(folder, at, "--check").returncode == 0


def test_a_folder_with_nothing_to_read_says_so(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = store(empty, tmp_path / "pile.sqlite")
    assert got.returncode == 42 and got.stdout.startswith("built 0 passages")


def test_a_file_that_is_not_a_store_is_left_as_it_is(tmp_path):
    folder, at = a_folder(tmp_path)
    at.write_text("my notes, not a store\n")
    got = store(folder, at)
    assert got.returncode == 2 and "not a pile store" in got.stderr
    assert at.read_text() == "my notes, not a store\n"
    other = sqlite3.connect(tmp_path / "other.sqlite")
    other.execute("CREATE TABLE meta (k TEXT, v TEXT)")
    other.commit()
    other.close()
    assert store(folder, tmp_path / "other.sqlite").returncode == 2
    assert store(folder, tmp_path).returncode == 2  # a folder, not a file


def test_a_bad_command_line_is_refused(tmp_path):
    folder, at = a_folder(tmp_path)
    for argv in ([], ["--from", str(folder)], ["--to", str(at)],
                 ["--from", str(folder), "--to", str(at), "--stray"],
                 ["--from", str(folder / "roof.md"), "--to", str(at)],
                 ["--from", str(folder), "--to", str(folder / "in.sqlite")],
                 ["--from", str(folder), "--to", str(tmp_path / "no" / "s")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, (argv, got.stdout, got.stderr)
    assert not (folder / "in.sqlite").exists() and not (tmp_path / "no").exists()
    assert "pile_store.py" in run().stderr


def test_a_store_is_opened_read_only(tmp_path):
    folder, at = a_folder(tmp_path)
    store(folder, at)
    db = pile_store.opened(at)
    try:
        db.execute("DELETE FROM passages")
        raise AssertionError("a read-only store took a write")
    except sqlite3.OperationalError as e:
        assert "readonly" in str(e)
    finally:
        db.close()
