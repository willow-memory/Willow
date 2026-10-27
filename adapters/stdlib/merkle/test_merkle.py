"""merkle: every row's proof folds to the root at every size, a leaf can
never pose as a node, a tampered line or root is refused, and a proof alone
is self-consistency, not an answer."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("merkle", HERE / "merkle.py")
mk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mk)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, bites: int = 3) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    for _ in range(bites):
        run(str(KERNEL), "bite", "--box", str(b), *NOW, "tomatoes")
    return b


def test_every_rows_proof_folds_to_the_root_at_every_size():
    for n in range(1, 12):
        leaves = [mk.leaf_of(f"row{i}") for i in range(n)]
        root = mk.root_of(leaves)
        for i in range(n):
            path = mk.path_of(leaves, i)
            assert mk.fold(leaves[i], path) == root, (n, i)
            assert len(path) <= max(1, n - 1).bit_length(), "a handful, not the file"
        assert mk.fold(mk.leaf_of("tampered"), mk.path_of(leaves, 0)) != root


def test_the_tree_is_exactly_as_the_card_says():
    a, b, c = (mk.leaf_of(x) for x in ("a", "b", "c"))
    assert a == hashlib.sha256(b"\x00" + b"a").hexdigest(), "a leaf wears a zero byte"
    ab = hashlib.sha256(b"\x01" + bytes.fromhex(a) + bytes.fromhex(b)).hexdigest()
    assert mk.root_of([a, b]) == ab, "a node wears a one byte, left then right"
    assert mk.root_of([a, b, c]) == mk.node_of(ab, c), "the odd node rises unchanged"
    assert mk.root_of([a]) == a
    assert mk.root_of([a, b]) != mk.root_of([b, a]), "order is part of the record"


def test_root_prove_and_check_against_a_real_box(tmp_path):
    b = box(tmp_path)
    got = run(str(HERE / "merkle.py"), "root", "--box", str(b))
    assert got.returncode == 0 and got.stdout.startswith("root ")
    root = got.stdout.split()[1]
    rows = int(got.stdout.split()[3])
    assert rows >= 4, "init and the bites each wrote rows"
    proof = tmp_path / "row2.proof"
    got = run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "2",
              "--to", str(proof))  # fmt: skip
    assert got.returncode == 0 and proof.stat().st_mode & 0o777 == 0o600
    got = run(str(HERE / "merkle.py"), "check", "--proof", str(proof))
    assert got.returncode == 42, "a proof alone answers to nothing"
    assert "only your own copy can say" in got.stdout
    got = run(str(HERE / "merkle.py"), "check", "--proof", str(proof), "--root", root)
    assert got.returncode == 0 and "stands under your root" in got.stdout
    got = run(str(HERE / "merkle.py"), "check", "--proof", str(proof),
              "--root", "ab" * 32)  # fmt: skip
    assert got.returncode == 2 and "does NOT stand" in got.stderr


def test_a_tampered_proof_is_refused(tmp_path):
    b = box(tmp_path)
    proof = tmp_path / "p.json"
    run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "1",
        "--to", str(proof))  # fmt: skip
    page = json.loads(proof.read_text())
    page["line"] = page["line"].replace("bite", "seal")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(page))
    got = run(str(HERE / "merkle.py"), "check", "--proof", str(bad))
    assert got.returncode == 2 and "doesn't hold together" in got.stderr
    bad.write_text("not json")
    got = run(str(HERE / "merkle.py"), "check", "--proof", str(bad))
    assert got.returncode == 2 and "isn't a proof" in got.stderr


def test_prove_refuses_bad_rows_and_bad_places(tmp_path):
    b = box(tmp_path)
    got = run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "99",
              "--to", str(tmp_path / "p"))  # fmt: skip
    assert got.returncode == 2 and "rows 0 to" in got.stderr
    for to in (b / "p.json", tmp_path / "pile" / "p.json"):
        got = run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "1",
                  "--to", str(to))  # fmt: skip
        assert got.returncode == 2 and not to.exists()
    ok = tmp_path / "ok.json"
    ok.write_text("mine")
    got = run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "1",
              "--to", str(ok))  # fmt: skip
    assert got.returncode == 2 and ok.read_text() == "mine", "never over a file"


def test_the_same_record_gives_the_same_root_and_a_grown_one_does_not(tmp_path):
    b = box(tmp_path)
    one = run(str(HERE / "merkle.py"), "root", "--box", str(b)).stdout
    assert one == run(str(HERE / "merkle.py"), "root", "--box", str(b)).stdout
    run(str(KERNEL), "bite", "--box", str(b), *NOW, "sun")
    assert one != run(str(HERE / "merkle.py"), "root", "--box", str(b)).stdout


def test_a_two_row_record_proves_a_row_with_one_hash(tmp_path):
    b = box(tmp_path, bites=1)
    proof = tmp_path / "p.json"
    got = run(str(HERE / "merkle.py"), "prove", "--box", str(b), "--row", "0",
              "--to", str(proof))  # fmt: skip
    assert "a proof of 1 hash to" in got.stdout, "one hash, said in the singular"
    got = run(str(HERE / "merkle.py"), "root", "--box", str(b), "--to", str(proof))
    assert got.returncode == 2 and "merkle.py" in got.stderr, "root takes no FILE"


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "merkle.py"))
    assert got.returncode == 2 and "merkle.py" in got.stderr
    got = run(str(HERE / "merkle.py"), "root", "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(str(HERE / "merkle.py"), "root", "--box", str(tmp_path), "--row", "1")
    assert got.returncode == 2, "root takes no row"

    got = run(str(HERE / "merkle.py"), "check")
    assert got.returncode == 2
