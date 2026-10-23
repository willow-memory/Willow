"""todo: marked lines across the folder, oldest first by the kernel's own
passage dates, undated last."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def test_oldest_first_undated_last_and_every_marker(tmp_path):
    pile = tmp_path / "pile"
    (pile / "memos").mkdir(parents=True)
    (pile / "memos" / "2021-05-14.txt").write_text(
        "Sold the van. Need to call the insurer.\n"
    )
    (pile / "memos" / "2025-02-07.txt").write_text("Remember to check the mites.\n")
    (pile / "README.md").write_text(
        "TODO: fix the install step\n\n- [ ] buy strings\n\nAll done here.\n"
    )
    (pile / "code.py").write_text("x = 1  # FIXME: off by one\n")
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
    got = run(str(HERE / "todo.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0 and len(lines) == 5
    assert lines[0].startswith("2021-05-14") and "insurer" in lines[0]
    assert lines[1].startswith("2025-02-07")
    assert all(ln.startswith("undated") for ln in lines[2:])
    assert "All done" not in got.stdout


def test_nothing_marked(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Nothing to see.\n")
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
    assert run(str(HERE / "todo.py"), "--box", str(b)).returncode == 42
