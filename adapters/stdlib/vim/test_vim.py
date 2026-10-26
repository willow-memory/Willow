"""vim: the lines that put willow in Vim and Neovim, printed in the form
it reads, pointing at pipe's --grep output, and nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("vim_addon", HERE / "vim.py")
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
    assert (
        "cgetexpr system(cmd, a:question)" in text
        and "command! -nargs=+ Willow" in text
    )
    assert mod.vim_string("it's") == "'it''s'"  # a quote in a path can't end the string


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


def test_vim_runs_the_lines_and_fills_the_quickfix_list(tmp_path):
    import shutil

    import pytest

    vim = shutil.which("vim")
    if not vim:
        pytest.skip("no vim on this machine")
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    (tmp_path / "willow.vim").write_text(mod.snippet(b, sys.executable))
    out = tmp_path / "qf.txt"
    (tmp_path / "run.vim").write_text(
        f"Willow tomatoes\nredir! > {out}\nechon json_encode(map(getqflist(), "
        "'[bufname(v:val.bufnr), v:val.lnum, v:val.valid]'))\nredir END\nqa!\n"
    )
    subprocess.run([vim, "-N", "-u", "NONE", "-i", "NONE", "-es", "-S", str(tmp_path / "willow.vim"),
                    "-S", str(tmp_path / "run.vim")], timeout=30, capture_output=True)  # fmt: skip
    assert json.loads(out.read_text().strip()) == [[str(pile / "garden.md"), 1, 1]]


def test_it_prints_with_the_python_that_ran_it(tmp_path):
    assert sys.executable in mod.render(box(tmp_path))


def test_a_hosts_of_the_same_name_earlier_on_the_path_does_not_win(tmp_path):
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    (decoy / "hosts.py").write_text("raise SystemExit('the wrong hosts')\n")
    code = (
        "import sys, importlib.util\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "s = importlib.util.spec_from_file_location('m', sys.argv[2])\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(m.hosts.__file__)\n"
    )
    got = subprocess.run([sys.executable, "-c", code, str(decoy), str(HERE / "vim.py")],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert Path(got.stdout.strip()).parent.name == "hosts"
