"""todo: marked lines across the folder, oldest first by the kernel's own
passage dates, undated last."""

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
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "todo: populated, 5 lines marked to do, the oldest from 2021-05-14",
        "  memos/2021-05-14.txt:1  2021-05-14  Sold the van. Need to call the insurer.",
        "  memos/2025-02-07.txt:1  2025-02-07  Remember to check the mites.",
        "## undated",
        "  README.md:1             TODO: fix the install step",
        "  README.md:3             - [ ] buy strings",
        "  code.py:1               x = 1  # FIXME: off by one",
    ]
    doc = json.loads(run(str(HERE / "todo.py"), "--box", str(b), "--json").stdout)
    assert doc["addon"] == "todo" and doc["state"] == "populated"
    assert [g["name"] for g in doc["groups"]] == [None, "undated"]
    assert doc["groups"][0]["rows"][0] == {
        "where": "memos/2021-05-14.txt:1",
        "what": "2021-05-14  Sold the van. Need to call the insurer.",
    }
    assert doc["groups"][1]["rows"][2] == {
        "where": "code.py:1",
        "what": "x = 1  # FIXME: off by one",
    }


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
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.returncode == 0  # empty is 0: 42 never means found nothing
    assert got.stdout == "todo: empty, nothing in your folder is marked to do\n"
    got = run(str(HERE / "todo.py"), "--box", str(b), "--json")
    assert got.returncode == 0
    assert json.loads(got.stdout) == {
        "addon": "todo",
        "state": "empty",
        "said": "nothing in your folder is marked to do",
        "groups": [],
    }


def test_all_undated_says_so(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("TODO: water\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "todo.py"), "--box", str(b))
    assert got.stdout.splitlines() == [
        "todo: populated, 1 line marked to do, none dated",
        "## undated",
        "  a.md:1  TODO: water",
    ]


def test_a_long_marked_line_is_cut_at_120(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("TODO: " + "y" * 200 + "\n")
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    line = run(str(HERE / "todo.py"), "--box", str(b)).stdout.splitlines()[-1]
    assert line.endswith("TODO: " + "y" * 114)
