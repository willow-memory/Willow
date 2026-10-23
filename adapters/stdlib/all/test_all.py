"""all: every passage the kernel's rank holds, in its order; its first three
are the kernel's three, and nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for i in range(8):
        (pile / f"bees-{i}.md").write_text(
            f"2026-0{i + 1}-01 the bees in hive {i} are calm.\n"
        )
    (pile / "other.md").write_text("The shed is blue.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return b


def test_its_first_three_are_the_kernels_and_it_shows_the_rest(tmp_path):
    b = box(tmp_path)
    got = run(str(HERE / "all.py"), "--box", str(b), "how are the bees")
    mine = json.loads(got.stdout)
    theirs = json.loads(
        run(str(KERNEL), "bite", "--box", str(b), *NOW, "how are the bees").stdout
    )
    assert got.returncode == 0 and mine["count"] == 8
    assert [s["id"] for s in mine["served"][:3]] == [s["id"] for s in theirs["served"]]
    assert [s["rank"] for s in mine["served"]] == list(range(1, 9))


def test_top_n_and_nothing_found(tmp_path):
    b = box(tmp_path)
    got = json.loads(
        run(str(HERE / "all.py"), "--box", str(b), "--top", "5", "bees").stdout
    )
    assert got["count"] == 5
    none = run(str(HERE / "all.py"), "--box", str(b), "when does the frost come")
    assert none.returncode == 42 and json.loads(none.stdout)["state"] == "empty"


def test_it_writes_nothing_and_leaves_the_kernels_limit_as_it_was(tmp_path):
    b = box(tmp_path)
    before = (b / "record.jsonl").read_bytes()
    run(str(HERE / "all.py"), "--box", str(b), "how are the bees")
    assert (b / "record.jsonl").read_bytes() == before
    import importlib.util

    spec = importlib.util.spec_from_file_location("all_", HERE / "all.py")
    al = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(al)
    assert len(al.ranked(b, "how are the bees")) == 8
    assert al.kernel.TOP == 3
