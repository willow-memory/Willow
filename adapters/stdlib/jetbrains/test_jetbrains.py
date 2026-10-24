"""jetbrains: the lines that put willow in IntelliJ, PyCharm and the other JetBrains IDEs, printed in the form
it reads, pointing at pipe's --grep output, and nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("jetbrains_addon", HERE / "jetbrains.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text("The bus leaves at seven.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    return b


def test_the_lines_run_pipe_with_grep_over_the_box(tmp_path):
    b = box(tmp_path)
    text = mod.snippet(b, "/usr/bin/python3")
    assert "/usr/bin/python3" in text and "pipe/pipe.py" in text
    assert str(b.resolve()) in text and "--grep" in text
    import xml.etree.ElementTree as ET

    root = ET.fromstring(text)
    opts = {o.get("name"): o.get("value") for o in root.iter("option")}
    assert opts["REGEXP"] == "$FILE_PATH$:$LINE$:" and "$Prompt$" in opts["PARAMETERS"]


def test_the_pipe_it_names_exists():
    assert mod.PIPE.is_file() and mod.PIPE.parent.name == "pipe"


def test_it_prints_where_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert mod.main(["--box", str(b)]) == 0
    assert capsys.readouterr().out.startswith("Add this to ")
    assert sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    assert mod.main([]) == 2 and mod.main(["--box"]) == 2
    assert mod.main(["--box", str(tmp_path)]) == 2


def test_it_prints_with_the_python_that_ran_it(tmp_path):
    assert sys.executable in mod.render(box(tmp_path))
