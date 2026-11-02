"""parallel: run a reader over several folders at once, across cores, into one
mirror. Each folder is mirrored whole by the reader, so a sub-mirror is exactly
the reader's own bytes (backlinks and all); it sums what the readers wrote,
is deterministic, escalates when nothing was readable, and refuses a bad
command line, an unknown reader, a non-folder, or two folders sharing a name.

It drives a stand-in reader named notes, in a scratch copy beside this
parallel.py and the kernel, that keeps the readers' contract: `mirror --from
FOLDER --to MIRROR` writes each .md file's text, upper-cased, and says `wrote
N files to MIRROR; skipped M`. So these tests hold wherever parallel.py is,
and test parallel, not the reader it runs."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PAR = None  # the scratch copy's parallel.py, set for each test
NOTES = None  # and its stand-in reader

READER = """import sys
from pathlib import Path

argv = sys.argv[1:]
if argv[:1] != ["mirror"] or "--from" not in argv or "--to" not in argv:
    print("usage: notes.py mirror --from FOLDER --to MIRROR", file=sys.stderr)
    sys.exit(2)
src, to = Path(argv[argv.index("--from") + 1]), Path(argv[argv.index("--to") + 1])
wrote = skipped = 0
for f in sorted(src.rglob("*")):
    if not f.is_file():
        continue
    if f.suffix != ".md":
        skipped += 1
        continue
    out = to / f.relative_to(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f.read_text(encoding="utf-8").upper(), encoding="utf-8")
    wrote += 1
print(f"wrote {wrote} files to {to}; skipped {skipped}")
if __name__ == "__main__":
    sys.exit(0 if wrote else 42)
"""


@pytest.fixture(autouse=True)
def scratch(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("willow")
    (root / "adapters" / "stdlib" / "parallel").mkdir(parents=True)
    (root / "adapters" / "stdlib" / "notes").mkdir(parents=True)
    shutil.copy2(HERE.parents[2] / "kernel.py", root / "kernel.py")
    shutil.copy2(
        HERE / "parallel.py", root / "adapters" / "stdlib" / "parallel" / "parallel.py"
    )
    (root / "adapters" / "stdlib" / "notes" / "notes.py").write_text(READER)
    monkeypatch.setitem(
        globals(), "PAR", root / "adapters" / "stdlib" / "parallel" / "parallel.py"
    )
    monkeypatch.setitem(
        globals(), "NOTES", root / "adapters" / "stdlib" / "notes" / "notes.py"
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PAR), *argv], capture_output=True, text=True
    )


def snapshot(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }  # fmt: skip


def two_vaults(tmp: Path) -> tuple[Path, Path]:
    """Two folders with cross-file links inside each; (A, B)."""
    a = tmp / "A"
    (a / "daily").mkdir(parents=True)
    (a / "note1.md").write_text("- [[Roof]] needs work #home\n")
    (a / "daily" / "roof.md").write_text("# Roof\nThe estimate is in. [[note1]]\n")
    b = tmp / "B"
    b.mkdir()
    (b / "garden.md").write_text("Tomatoes want [[sun]].\n")
    return a, b


def test_mirrors_each_folder_and_matches_serial(tmp_path):
    a, b = two_vaults(tmp_path)
    mirror = tmp_path / "mirror"
    got = run("--reader", "notes", "--from", str(a), "--from", str(b),
              "--to", str(mirror), "--jobs", "2")  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    assert "wrote 3 files to" in got.stdout
    # the A sub-mirror is byte-for-byte the reader's own run over A alone
    serial = tmp_path / "serialA"
    subprocess.run([sys.executable, str(NOTES), "mirror", "--from", str(a),
                    "--to", str(serial)], check=True, capture_output=True)  # fmt: skip
    assert snapshot(mirror / "A") == snapshot(serial), (
        "a whole folder, the reader's bytes"
    )


def test_the_output_is_deterministic(tmp_path):
    a, b = two_vaults(tmp_path)
    one, two = tmp_path / "m1", tmp_path / "m2"
    run("--reader", "notes", "--from", str(a), "--from", str(b), "--to", str(one))
    run("--reader", "notes", "--from", str(a), "--from", str(b), "--to", str(two),
        "--jobs", "1")  # fmt: skip
    assert snapshot(one) == snapshot(two), "same folders, same bytes, any job count"


def test_an_unknown_reader_is_refused(tmp_path):
    a, _ = two_vaults(tmp_path)
    got = run("--reader", "nope", "--from", str(a), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "no reader nope here" in got.stderr


def test_a_from_that_is_not_a_folder_is_refused(tmp_path):
    got = run("--reader", "notes", "--from", str(tmp_path / "missing"),
              "--to", str(tmp_path / "m"))  # fmt: skip
    assert got.returncode == 2 and "is not a folder" in got.stderr


def test_two_folders_with_the_same_name_are_refused(tmp_path):
    (tmp_path / "x" / "A").mkdir(parents=True)
    (tmp_path / "x" / "A" / "n.md").write_text("one\n")
    (tmp_path / "y" / "A").mkdir(parents=True)
    (tmp_path / "y" / "A" / "n.md").write_text("two\n")
    got = run("--reader", "notes", "--from", str(tmp_path / "x" / "A"),
              "--from", str(tmp_path / "y" / "A"), "--to", str(tmp_path / "m"))  # fmt: skip
    assert got.returncode == 2 and "share a name" in got.stderr


def test_all_empty_folders_escalate(tmp_path):
    (tmp_path / "e1").mkdir()
    (tmp_path / "e2").mkdir()
    got = run("--reader", "notes", "--from", str(tmp_path / "e1"),
              "--from", str(tmp_path / "e2"), "--to", str(tmp_path / "m"))  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    assert "wrote 0 files" in got.stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    a, _ = two_vaults(tmp_path)
    mirror = str(tmp_path / "m")
    for argv in (
        [],  # nothing
        ["--reader", "notes", "--from", str(a)],  # no --to
        ["--reader", "notes", "--to", mirror],  # no --from
        ["--from", str(a), "--to", mirror],  # no --reader
        ["--reader", "notes", "--from", str(a), "--to", mirror, "--jobs", "0"],  # jobs
        ["--reader", "notes", "--from", str(a), "--to", mirror, "--stray"],  # flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "parallel.py" in got.stderr, (argv, got.stderr)
