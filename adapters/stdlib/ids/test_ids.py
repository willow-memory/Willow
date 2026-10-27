"""ids: the Software Heritage ID is git's own blob hash, the IPFS name is a
one-chunk raw CIDv1 and never a guess past that, and both are computed at
home, byte for byte."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("ids", HERE / "ids.py")
ids = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ids)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_the_swhid_is_gits_own_blob_hash(tmp_path):
    assert ids.swhid(b"") == "swh:1:cnt:e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    assert ids.swhid(b"hello\n") == (
        "swh:1:cnt:ce013625030ba8dba906f756967f9e9ca394464a"
    )
    p = tmp_path / "sample.txt"
    p.write_bytes(b"Tomatoes want sun.\n")
    git = subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True)
    if git.returncode == 0:  # git's own answer, where git is installed
        assert ids.swhid(p.read_bytes()) == f"swh:1:cnt:{git.stdout.strip()}"


def test_the_cid_is_a_one_chunk_raw_cidv1_and_decodes_to_its_own_bytes():
    got = ids.cid(b"hello\n")
    assert got == "bafkreicysg23kiwv34eg2d7qweipxwosdo2py4ldv42nbauguluen5v6am"
    body = base64.b32decode(got[1:].upper() + "=" * (-len(got[1:]) % 8))
    assert body == bytes([1, 0x55, 0x12, 0x20]) + hashlib.sha256(b"hello\n").digest()
    assert got.startswith("bafkrei"), "the prefix every raw sha2-256 CIDv1 wears"


def test_past_one_chunk_the_name_is_said_not_guessed():
    assert ids.cid(b"x" * (256 * 1024)) is not None, "one chunk exactly still names"
    assert ids.cid(b"x" * (256 * 1024 + 1)) is None
    lines = ids.named(b"x" * (256 * 1024 + 1))
    assert lines[1] == "  too big for a one-chunk CID"
    assert lines[0].startswith("  swh:1:cnt:"), "the swh name has no such ceiling"


def test_every_file_is_named_and_hidden_ones_never_read(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n", "a/b.txt": "two\n",
                       ".hidden.md": "never\n"})  # fmt: skip
    got = run(str(HERE / "ids.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and lines[-1] == "2 files named"
    assert lines[0] == "a/b.txt" and lines[3] == "garden.md"
    assert lines[1].startswith("  swh:1:cnt:") and lines[2].startswith("  bafkrei")
    assert ".hidden" not in got.stdout
    assert got.stdout == run(str(HERE / "ids.py"), "--box", str(b)).stdout


def test_a_path_adds_its_passages_each_by_its_first_line(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n\nBeans want poles.\n"})
    got = run(str(HERE / "ids.py"), "--box", str(b), "garden.md")
    assert got.returncode == 0
    assert "garden.md:1" in got.stdout and "garden.md:3" in got.stdout
    whole = ids.swhid((tmp_path / "pile" / "garden.md").read_bytes())
    first = ids.swhid(b"Tomatoes want sun.")
    assert whole in got.stdout and first in got.stdout


def test_a_path_not_of_the_folder_and_an_empty_folder_escalate(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "ids.py"), "--box", str(b), "gone.md")
    assert got.returncode == 42 and "isn't a file of your folder" in got.stdout
    got = run(str(HERE / "ids.py"), "--box", str(b), "../garden.md")
    assert got.returncode == 42, "a path may not climb out of the folder"


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "ids.py"))
    assert got.returncode == 2 and "ids.py" in got.stderr
    got = run(str(HERE / "ids.py"), "--box", str(tmp_path), "a.md", "b.md")
    assert got.returncode == 2
    got = run(str(HERE / "ids.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
