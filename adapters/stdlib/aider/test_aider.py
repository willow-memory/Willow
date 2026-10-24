"""aider: the lines that put willow in Aider, printed in the form
it reads, pointing at pipe's --grep output, and nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("aider_addon", HERE / "aider.py")
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
    assert text.startswith("/run ") and text.rstrip().endswith('"your question"')


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


def test_a_folder_with_a_space_in_its_name_stays_one_piece(tmp_path):
    import shlex

    (tmp_path / "with space").mkdir()
    b = box(tmp_path / "with space")
    line = mod.snippet(b, "/usr/bin/python3")[len("/run ") :]
    argv = shlex.split(line)
    assert argv[argv.index("--box") + 1] == str(b.resolve())
    assert argv[-1] == "your question"


def test_each_system_gets_its_own_shells_quoting(monkeypatch):
    argv = ["/a b/python", "x"]
    monkeypatch.setattr(mod.os, "name", "posix")
    assert mod.command_line(argv) == "'/a b/python' x"
    monkeypatch.setattr(mod.os, "name", "nt")
    assert mod.command_line(argv) == '"/a b/python" x'
