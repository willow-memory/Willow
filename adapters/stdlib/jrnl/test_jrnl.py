"""jrnl: a journal is known by its first said line's stamp, each entry
mirrors as one dated paragraph, and a .txt that is someone else's is
skipped, counted, never guessed at."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("jrnl", HERE / "jrnl.py")
jr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jr)

JOURNAL = (
    "[2024-03-03 10:15] Fixed the gate.\n"
    "The hinge wanted oil, not force.\n"
    "\n"
    "Second thought, kept with the first.\n"
    "\n"
    "[2024-03-04 09:00:30] Rain all day.\n"
    "\n"
    "[2024-03-05 08:00]\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "jrnl.py"), *argv], capture_output=True, text=True
    )


def test_each_entry_is_one_dated_paragraph_in_file_order():
    got = jr.journal_text(JOURNAL.encode())
    assert got == (
        "2024-03-03 10:15  Fixed the gate.\n"
        "The hinge wanted oil, not force.\n"
        "Second thought, kept with the first.\n"
        "\n"
        "2024-03-04 09:00:30  Rain all day.\n"
        "\n"
        "2024-03-05 08:00\n"
        "\n"
    ), "brackets off, blank lines inside an entry closed up, seconds kept"


def test_a_txt_that_is_someone_elses_is_none():
    assert jr.journal_text(b"Tomatoes want sun.\n") is None
    assert jr.journal_text(b"notes\n[2024-03-03 10:15] too late\n") is None
    assert jr.journal_text(b"[2024-3-3 10:15] not the stamp\n") is None
    assert jr.journal_text(b"") is None
    assert jr.journal_text(b"\n\n[2024-03-03 10:15] blanks first are fine\n")


def test_mirror_writes_journals_skips_the_rest_and_never_touches_from(tmp_path):
    src = tmp_path / "from"
    (src / "diary").mkdir(parents=True)
    (src / "diary" / "journal.txt").write_text(JOURNAL)
    (src / "notes.txt").write_text("not a journal\n")
    (src / "readme.md").write_text("[2024-03-03 10:15] not a .txt\n")
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    dst = tmp_path / "mirror"
    got = run("mirror", "--from", str(src), "--to", str(dst))
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {dst}; skipped 1"
    assert (dst / "diary" / "journal.txt.txt").exists()
    assert sorted(p for p in dst.rglob("*") if p.is_file()) == [
        dst / "diary" / "journal.txt.txt"
    ]
    assert before == {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    again = tmp_path / "again"
    run("mirror", "--from", str(src), "--to", str(again))
    assert (again / "diary" / "journal.txt.txt").read_bytes() == (
        dst / "diary" / "journal.txt.txt"
    ).read_bytes(), "the same folder gives the same bytes"


def test_the_kernel_dates_a_mirrored_entry(tmp_path):
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    assert kernel.newest(jr.journal_text(JOURNAL.encode())) == "20240305"


def test_nothing_readable_is_42_and_bad_places_are_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("mirror", "--from", str(empty), "--to", str(tmp_path / "m"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    got = run()
    assert got.returncode == 2 and "jrnl.py" in got.stderr
    got = run("mirror", "--from", str(tmp_path / "gone"), "--to", str(tmp_path / "m2"))
    assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run("mirror", "--from", str(empty), "--to", str(empty / "inside"))
    assert got.returncode == 2 and "inside one another" in got.stderr
