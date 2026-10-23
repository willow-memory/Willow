"""starter-words: a list the kernel accepts, copied so the kernel will read it,
and what it does on a blind character's folder, measured, not assumed."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
spec = importlib.util.spec_from_file_location("kernel", KERNEL)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def test_the_list_is_one_the_kernel_reads():
    alias, why = k.parse_words((HERE / "words.txt").read_text(encoding="utf-8"))
    assert why is None and len(alias) >= 20
    for word, theirs in alias.items():
        assert word not in k.FUNCTION and all(t not in k.FUNCTION for t in theirs)


def test_copy_writes_it_for_you_alone_and_never_overwrites(tmp_path):
    to = tmp_path / "mine.txt"
    got = run(str(HERE / "starter.py"), "copy", "--to", str(to))
    assert got.returncode == 0 and to.read_bytes() == (HERE / "words.txt").read_bytes()
    if os.name == "posix":
        assert to.stat().st_mode & 0o777 == 0o600
    to.write_text("mine now\n")
    again = run(str(HERE / "starter.py"), "copy", "--to", str(to))
    assert again.returncode == 2 and to.read_text() == "mine now\n"
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("x\n")
    (tmp_path / "list.txt").unlink(missing_ok=True)
    run(str(HERE / "starter.py"), "copy", "--to", str(tmp_path / "list.txt"))
    ok = run(str(KERNEL), "init", "--box", str(tmp_path / "b"), "--pile", str(pile),
             "--key", str(tmp_path / "k"), "--words", str(tmp_path / "list.txt"), *NOW)  # fmt: skip
    assert ok.returncode == 0  # the kernel accepts the copy as it is


def test_teodoras_debt_is_served_with_it_and_not_without(tmp_path):
    """Teodora (demo/teodora, built blind) asks "how much do I still owe dev".
    Her files say Dev would "lend" the money; none says "owe". Without a list
    nothing is served; with this one, the chat where Dev offers to lend is."""
    shutil.copytree(ROOT / "demo" / "teodora", tmp_path / "teodora")
    assert run(str(tmp_path / "teodora" / "make_life.py")).returncode == 0
    run(str(HERE / "starter.py"), "copy", "--to", str(tmp_path / "words.txt"))
    q = "how much do I still owe dev"
    served = {}
    for name, extra in (
        ("without", []),
        ("with", ["--words", str(tmp_path / "words.txt")]),
    ):
        b = tmp_path / name
        run(str(KERNEL), "init", "--box", str(b), "--pile", str(tmp_path / "teodora" / "life"),
            "--key", str(tmp_path / "k"), *NOW, *extra)  # fmt: skip
        served[name] = json.loads(
            run(str(KERNEL), "bite", "--box", str(b), *NOW, q).stdout
        )
    assert served["without"]["state"] == "empty"
    assert any(
        "lend" in s["text"] and "Dev" in s["text"] for s in served["with"]["served"]
    )
