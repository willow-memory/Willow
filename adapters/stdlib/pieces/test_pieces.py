"""pieces: the kernel's passages of a pile, the same ones in the same order,
a folder at a time; one file read alone; and a command line that says how
much a box's pile held and the most it held at once."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pieces.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("pieces", SCRIPT)
pieces = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pieces)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def pile(tmp_path: Path) -> Path:
    """Files beside folders, at every depth, in an order the names decide:
    a.txt before b/, b/ before c.txt; a long file the kernel cuts; a hidden
    file and folder, a binary, a page, and a name that sorts before its
    folder's files."""
    p = tmp_path / "pile"
    files = {
        "a.txt": "Alpha one.\n\nAlpha two.\n",
        "b/x.txt": "Bee ex.\n",
        "b/y/z.txt": "Deep zed, 2026-10-30.\n",
        "b/y.txt": "Bee why.\n",
        "b-c.txt": "Bee dash cee.\n",
        "c.txt": "\n".join(f"line {i} " + "word " * 20 for i in range(60)),
        "d/page.html": "<p>A page <b>here</b>.</p>",
        ".hidden.txt": "Never read.\n",
        ".git/config": "Never read either.\n",
        "e/.secret/f.txt": "Not this.\n",
        "e/g.txt": "Gee.\n",
    }
    for name, text in files.items():
        f = p / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    (p / "e" / "blob.bin").write_bytes(b"\0\1\2binary")
    (p / "empty").mkdir()
    return p


def test_the_passages_are_the_kernels_in_the_kernels_order(tmp_path):
    p = pile(tmp_path)
    want = kernel.chunks(p)
    assert len(want) > 10
    assert list(pieces.passages(p)) == want


def test_each_piece_is_one_folders_files_and_no_file_is_cut_across_two(tmp_path):
    p = pile(tmp_path)
    got = list(pieces.folders(p))
    assert len(got) > 3 and all(got)
    seen: set[str] = set()
    for piece in got:
        names = {c["path"] for c in piece}
        assert len({str(Path(n).parent) for n in names}) == 1
        assert not names & seen
        seen |= names


def test_nothing_hidden_binary_or_empty_is_read(tmp_path):
    paths = {c["path"] for c in pieces.passages(pile(tmp_path))}
    assert not any("hidden" in x or ".git" in x or ".secret" in x for x in paths)
    assert "e/blob.bin" not in paths and "e/g.txt" in paths


def test_one_file_is_read_alone_with_its_own_path(tmp_path):
    p = pile(tmp_path)
    want = [c for c in kernel.chunks(p) if c["path"] == "b/y/z.txt"]
    assert pieces.of_file(p, "b/y/z.txt") == want and want
    assert pieces.of_file(p, "c.txt") == [
        c for c in kernel.chunks(p) if c["path"] == "c.txt"
    ]


def test_one_file_outside_hidden_or_missing_is_nothing(tmp_path):
    p = pile(tmp_path)
    (tmp_path / "outside.txt").write_text("Outside.\n")
    for rel in ("../outside.txt", str(tmp_path / "outside.txt"), ".hidden.txt",
                "e/.secret/f.txt", "nope.txt", "b"):  # fmt: skip
        assert pieces.of_file(p, rel) == [], rel


def test_a_linked_folder_is_followed_only_as_the_kernel_follows_it(tmp_path):
    p = pile(tmp_path)
    real = tmp_path / "elsewhere"
    real.mkdir()
    (real / "far.txt").write_text("Far away.\n")
    os.symlink(real, p / "linked", target_is_directory=True)
    (p / "f.txt").write_text("Eff.\n")
    os.symlink(p / "f.txt", p / "f-link.txt")
    assert list(pieces.passages(p)) == kernel.chunks(p)
    assert bool(pieces.of_file(p, "linked/far.txt")) == pieces.FOLLOWS
    assert pieces.of_file(p, "f-link.txt") == [
        c for c in kernel.chunks(p) if c["path"] == "f-link.txt"
    ]


def test_an_empty_pile_has_no_pieces(tmp_path):
    (tmp_path / "pile").mkdir()
    assert list(pieces.folders(tmp_path / "pile")) == []


def box(tmp_path: Path, p: Path) -> Path:
    b = tmp_path / "box"
    got = subprocess.run(
        [sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(p),
         "--key", str(tmp_path / "key")], capture_output=True, text=True,
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def test_the_command_line_says_what_the_pile_held_and_the_most_at_once(tmp_path):
    p = pile(tmp_path)
    b = box(tmp_path, p)
    before = {f: f.read_bytes() for f in tmp_path.rglob("*") if f.is_file()}
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    n = len(kernel.chunks(p))
    files = len({c["path"] for c in kernel.chunks(p)})
    k = len(list(pieces.folders(p)))
    most = max(len(x) for x in pieces.folders(p))
    assert got.stdout.startswith(
        f"pieces: {n} passages from {files} files in {k} pieces; at most {most} at once ("
    )
    assert {f: f.read_bytes() for f in tmp_path.rglob("*") if f.is_file()} == before


def test_a_pile_of_one_short_file_names_its_folder_as_the_most_at_once(tmp_path):
    p = tmp_path / "pile"
    (p / "notes").mkdir(parents=True)
    (p / "notes" / "a.md").write_text("Tomatoes want six hours of sun.\n")
    assert len(kernel.chunks(p)) == 1
    got = run("--box", str(box(tmp_path, p)))
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "pieces: 1 passages from 1 files in 1 pieces; at most 1 at once (notes)\n"
    )


def test_an_empty_pile_says_so(tmp_path):
    (tmp_path / "pile").mkdir()
    got = run("--box", str(box(tmp_path, tmp_path / "pile")))
    assert got.returncode == 0 and "nothing in the pile" in got.stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in (
        [],
        ["--box"],
        ["--box", str(tmp_path), "stray"],
        ["--box", str(tmp_path)],
    ):
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "pieces.py" in run().stderr
