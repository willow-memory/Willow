"""ci-memo: keys hash a gate's reach exactly as ci.py hashes the tree, the
reach is drawn wide and never narrow, a pin holds only a run of this tree,
and a plan stands a gate only on unchanged bytes."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
spec = importlib.util.spec_from_file_location("ci_memo", HERE / "ci_memo.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

TS = "2026-10-23T00:00:00Z"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def memo(*argv: str) -> subprocess.CompletedProcess:
    return run(str(HERE / "ci_memo.py"), *argv)


def test_the_tree_key_is_ci_pys_files_sha256_to_the_byte():
    seen = cm.digests(cm.ROOT)
    assert cm.key_of(sorted(seen), seen) == cm.ci.files_sha256()


def test_each_reach_is_drawn_wide_never_narrow():
    files = ["kernel.py", "test_kernel.py", "README.md", "ruff.toml",
             ".github/workflows/ci.yml", "vectors/basic.json",
             "adapters/stdlib/ci/test_contract.py",
             "adapters/stdlib/mutants/accepted.json",
             "adapters/stdlib/accents/accents.py",
             "adapters/stdlib/zed/zed.py"]  # fmt: skip
    assert cm.inputs("lint:check", files) == [
        "kernel.py", "test_kernel.py", "ruff.toml", ".github/workflows/ci.yml",
        "adapters/stdlib/ci/test_contract.py", "adapters/stdlib/accents/accents.py",
        "adapters/stdlib/zed/zed.py"]  # fmt: skip
    assert cm.inputs("tests:beats", files) == ["kernel.py"]
    assert cm.inputs("tests:kernel", files) == [
        "kernel.py", "test_kernel.py", "vectors/basic.json"]  # fmt: skip
    got = cm.inputs("mutants:accents", files)
    assert "adapters/stdlib/accents/accents.py" in got and "kernel.py" in got
    assert "adapters/stdlib/ci/test_contract.py" in got and "<commands>" in got
    assert "adapters/stdlib/mutants/accepted.json" in got
    assert "adapters/stdlib/zed/zed.py" not in got and "README.md" not in got
    # the whole tree: a repo tool's mutants, a gate with no reach drawn, and
    # a rule whose folder is empty
    for gate in ("mutants:readme", "demo:odile", "tests:docs", "mutants:gone"):
        assert cm.inputs(gate, files) == files


def tree(tmp_path: Path, extra: dict | None = None) -> Path:
    root = tmp_path / "repo"
    files = {
        "kernel.py": "k\n",
        "test_kernel.py": "t\n",
        "README.md": "r\n",
        "adapters/stdlib/ci/test_contract.py": "c\n",
        "adapters/stdlib/mutants/mutants.py": "m\n",
        "adapters/stdlib/accents/accents.py": "a\n",
        "adapters/stdlib/zed/zed.py": "z\n",
        **(extra or {}),
    }
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def pinned_box(
    tmp_path: Path, root: Path, gates: dict[str, str], name: str = "box"
) -> Path:
    """A box holding one verdict per gate, of this tree, as ci.py writes
    them."""
    b = tmp_path / name
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(root),
        "--key", str(tmp_path / f"{name}.key"), "--now", TS)  # fmt: skip
    seen = cm.digests(root)
    sha = cm.key_of(sorted(seen), seen)
    for gate, state in gates.items():
        kernel.append(b, TS, "verdict", who="ci", gate=gate, state=state,
                      files_sha256=sha, said_sha256=kernel.h256(""),
                      python="{}.{}".format(*sys.version_info[:2]))  # fmt: skip
    return b


GATES = {"mutants:accents": "satisfied", "mutants:zed": "satisfied",
         "tests:beats": "satisfied", "lint:check": "satisfied",
         "deps:mcp": "satisfied"}  # fmt: skip


def test_pin_then_plan_stands_only_what_the_bytes_still_cover(tmp_path):
    root = tree(tmp_path)
    b = pinned_box(tmp_path, root, GATES)
    pin = tmp_path / "ci.pin"
    got = memo("pin", "--box", str(b), "--to", str(pin), "--repo", str(root))
    assert got.returncode == 0 and "pinned 5 gates" in got.stdout
    got = memo("plan", "--pin", str(pin), "--repo", str(root))
    assert got.returncode == 42
    for line in ("stand  mutants:accents", "stand  mutants:zed",
                 "stand  tests:beats", "stand  lint:check"):  # fmt: skip
        assert line in got.stdout
    assert "run    deps:mcp" in got.stdout and "never memoized" in got.stdout
    assert "not in the pin" in got.stdout  # every gate the box never ran

    (root / "adapters/stdlib/accents/accents.py").write_text("a2\n")
    got = memo("plan", "--pin", str(pin), "--repo", str(root)).stdout
    assert "run    mutants:accents" in got and "inputs changed" in got
    assert "stand  mutants:zed" in got, "another add-on's bytes are its own"
    assert "run    lint:check" in got, "lint reads every .py"
    assert "stand  tests:beats" in got, "the kernel didn't change"


def test_a_run_cut_into_shards_is_pinned_whole_from_each_record(tmp_path):
    root = tree(tmp_path)
    one = pinned_box(tmp_path, root, {"mutants:accents": "satisfied", "lint:check": "failing"}, "1")  # fmt: skip
    two = pinned_box(tmp_path, root, {"mutants:zed": "satisfied", "lint:check": "satisfied"}, "2")  # fmt: skip
    pin = tmp_path / "ci.pin"
    got = memo("pin", "--box", str(one), "--box", str(two), "--to", str(pin), "--repo", str(root))  # fmt: skip
    assert got.returncode == 0 and "pinned 3 gates" in got.stdout
    got = memo("plan", "--pin", str(pin), "--repo", str(root)).stdout
    assert "stand  mutants:accents" in got and "stand  mutants:zed" in got
    lint = next(
        ln.split() for ln in got.splitlines() if ln.startswith("stand  lint:check")
    )
    assert lint[2] == "satisfied", "the later record named wins"
    got = memo("pin", "--box", str(one), "--box", str(tmp_path / "nope"), "--to", str(pin), "--repo", str(root))  # fmt: skip
    assert got.returncode == 2 and "nope is not a kernel box" in got.stderr
    got = memo("pin", "--box", str(one), "--box", "", "--to", str(pin), "--repo", str(root))  # fmt: skip
    assert got.returncode == 2


def test_a_script_gaining_a_command_line_reruns_every_add_ons_mutants(tmp_path):
    root = tree(tmp_path)
    b = pinned_box(tmp_path, root, GATES)
    pin = tmp_path / "ci.pin"
    memo("pin", "--box", str(b), "--to", str(pin), "--repo", str(root))
    new = root / "adapters/stdlib/newish/newish.py"
    new.parent.mkdir(parents=True)
    new.write_text('if __name__ == "__main__":\n    pass\n')
    got = memo("plan", "--pin", str(pin), "--repo", str(root)).stdout
    assert "run    mutants:zed" in got and "run    mutants:accents" in got, (
        "the contract's COMMANDS test runs in each of them"
    )


def test_plan_bare_prints_only_the_gates_to_run(tmp_path):
    root = tree(tmp_path)
    b = pinned_box(tmp_path, root, GATES)
    pin = tmp_path / "ci.pin"
    memo("pin", "--box", str(b), "--to", str(pin), "--repo", str(root))
    got = memo("plan", "--pin", str(pin), "--repo", str(root), "--bare")
    assert got.returncode == 42 and got.stdout.count("\n") == 1
    names = got.stdout.split()
    assert "deps:mcp" in names and "mutants:accents" not in names


def test_pin_refuses_a_record_of_another_tree_and_holds_the_chain(tmp_path):
    root = tree(tmp_path)
    b = pinned_box(tmp_path, root, GATES)
    (root / "README.md").write_text("changed\n")
    got = memo("pin", "--box", str(b), "--to", str(tmp_path / "p"), "--repo", str(root))
    assert got.returncode == 2 and "no run of this tree" in got.stderr
    (root / "README.md").write_text("r\n")
    record = b / "record.jsonl"
    record.write_text(record.read_text().replace("satisfied", "SATISFIED", 1))
    got = memo("pin", "--box", str(b), "--to", str(tmp_path / "p"), "--repo", str(root))
    assert got.returncode == 2 and "chain" in got.stderr


def test_pin_never_writes_into_the_tree_a_box_or_over_a_strangers_file(tmp_path):
    root = tree(tmp_path)
    b = pinned_box(tmp_path, root, GATES)
    for to in (root / "ci.pin", b / "ci.pin"):
        got = memo("pin", "--box", str(b), "--to", str(to), "--repo", str(root))
        assert got.returncode == 2 and not to.exists()
    stranger = tmp_path / "notes.json"
    stranger.write_text("{}")
    got = memo("pin", "--box", str(b), "--to", str(stranger), "--repo", str(root))
    assert got.returncode == 2 and "no pin" in got.stderr
    pin = tmp_path / "ci.pin"
    assert (
        memo("pin", "--box", str(b), "--to", str(pin), "--repo", str(root)).returncode
        == 0
    )
    assert (
        memo("pin", "--box", str(b), "--to", str(pin), "--repo", str(root)).returncode
        == 0
    ), "its own pin is replaced"


def test_keys_are_deterministic_and_a_wrong_gate_is_refused(tmp_path):
    root = tree(tmp_path)
    one = memo("keys", "--repo", str(root), "mutants:accents", "tests:beats")
    two = memo("keys", "--repo", str(root), "mutants:accents", "tests:beats")
    assert one.returncode == 0 and one.stdout == two.stdout
    assert len(one.stdout.splitlines()) == 2
    got = memo("keys", "--repo", str(root), "mutants:acents")
    assert got.returncode == 2 and "isn't a gate" in got.stderr


def test_a_bad_command_line_is_refused_and_says_how_to_run_it(tmp_path):
    got = memo()
    assert got.returncode == 2 and "ci_memo.py" in got.stderr
    got = memo("plan")
    assert got.returncode == 2 and "ci_memo.py" in got.stderr
    got = memo("plan", "--pin", str(tmp_path / "gone"))
    assert got.returncode == 2 and "isn't a pin" in got.stderr
