"""removed: a file about to be deleted or archived goes on the record as its
name, size and SHA-256, one row through the kernel, never its words; the
add-on itself removes nothing."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "removed.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("The boiler broke.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-20T09:12:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    root = tmp_path / "beside"
    (root / "drafts").mkdir(parents=True)
    (root / "drafts" / "one.md").write_text("A secret plan for the garden.\n")
    (root / "two.bin").write_bytes(b"\x00\x01\x02")
    return b, root


def rows(b: Path) -> list[dict]:
    return [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]


def test_the_hole_is_one_row_of_names_sizes_and_fingerprints(tmp_path):
    b, root = make(tmp_path)
    got = run("--box", str(b), "--root", str(root), "--what", "drafts",
              "drafts/one.md", "two.bin")  # fmt: skip
    assert got.returncode == 0, got.stderr
    row = rows(b)[-1]
    assert (row["kind"], row["how"], row["what"], row["to"]) == (
        "removed",
        "deleted",
        "drafts",
        None,
    )
    one = (root / "drafts" / "one.md").read_bytes()
    assert row["files"] == {
        "drafts/one.md": {"sha256": hashlib.sha256(one).hexdigest(), "size": len(one)},
        "two.bin": {"sha256": hashlib.sha256(b"\x00\x01\x02").hexdigest(), "size": 3},
    }
    assert "row " in got.stdout and "2 files, deleted" in got.stdout


def test_never_a_word_of_a_file_nor_a_path_of_the_machine(tmp_path):
    b, root = make(tmp_path)
    run("--box", str(b), "--root", str(root), "drafts/one.md")
    record = (b / "record.jsonl").read_text()
    assert "secret" not in record and "garden" not in record
    assert str(tmp_path) not in record.splitlines()[-1]


def test_it_removes_nothing_itself(tmp_path):
    b, root = make(tmp_path)
    before = sorted(p.name for p in root.rglob("*"))
    run("--box", str(b), "--root", str(root), "drafts/one.md", "two.bin")
    assert sorted(p.name for p in root.rglob("*")) == before
    assert (root / "drafts" / "one.md").read_text() == "A secret plan for the garden.\n"


def test_an_archive_is_named_with_its_own_fingerprint(tmp_path):
    b, root = make(tmp_path)
    tar = tmp_path / "away.tar.gz"
    tar.write_bytes(b"not really a tarball")
    got = run("--box", str(b), "--root", str(root), "--how", "archived", "--to", str(tar),
              "two.bin")  # fmt: skip
    assert got.returncode == 0, got.stderr
    row = rows(b)[-1]
    assert row["how"] == "archived"
    assert row["to"] == {"name": "away.tar.gz", "size": 20,
                         "sha256": hashlib.sha256(b"not really a tarball").hexdigest()}  # fmt: skip
    assert "to away.tar.gz" in got.stdout


def test_one_name_that_cannot_be_recorded_means_no_row(tmp_path):
    b, root = make(tmp_path)
    (root / "link.md").symlink_to(tmp_path / "pile" / "a.md")
    n = len(rows(b))
    for bad in (["gone.md"], ["../pile/a.md"], ["drafts"], ["link.md"], ["two.bin", "two.bin"],
                [str(root / "two.bin")], ["two.bin", "gone.md"]):  # fmt: skip
        got = run("--box", str(b), "--root", str(root), *bad)
        assert got.returncode == 2, bad
    assert (
        run(
            "--box", str(b), "--root", str(root), "--how", "burned", "two.bin"
        ).returncode
        == 2
    )
    assert run("--box", str(b), "--root", str(root), "--to", str(tmp_path / "no.tar"),
               "two.bin").returncode == 2  # fmt: skip
    assert (
        run(
            "--box", str(b), "--root", str(root), "--what", "x" * 81, "two.bin"
        ).returncode
        == 2
    )
    assert len(rows(b)) == n


def test_the_boxs_own_files_are_never_named(tmp_path):
    b, _ = make(tmp_path)
    assert run("--box", str(b), "--root", str(b), "record.jsonl").returncode == 2
    assert run("--box", str(b), "--root", str(b / "proposals"), "x").returncode == 2
    assert (
        run("--box", str(tmp_path / "nowhere"), "--root", str(tmp_path), "k").returncode
        == 2
    )


def test_the_record_still_verifies(tmp_path):
    b, root = make(tmp_path)
    run("--box", str(b), "--root", str(root), "two.bin")
    got = subprocess.run([sys.executable, str(KERNEL), "verify", "--box", str(b)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr


def test_an_option_it_does_not_have_is_refused_and_nothing_is_written(tmp_path):
    """A word that opens with -- is never taken for a file's name: the whole
    command line is refused, with how to run it, before any row."""
    box, root = make(tmp_path)
    rows = (box / "record.jsonl").read_text()
    got = run("--box", str(box), "--root", str(root), "two.bin", "--stray", "more")
    assert got.returncode == 2 and "removed.py" in got.stderr
    assert (box / "record.jsonl").read_text() == rows
