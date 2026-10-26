"""vscode: the lines that put willow in VS Code, printed in the form
it reads, pointing at pipe's --grep output, and nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("vscode_addon", HERE / "vscode.py")
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
    doc = json.loads(text)
    assert text == json.dumps(doc, indent=2) + "\n"
    import re

    where = doc["tasks"][0]["problemMatcher"]["pattern"]
    m = re.compile(where["regexp"]).match(
        "/home/a/notes/n.md:12: The bus leaves at seven."
    )
    assert m and m.group(where["file"]) == "/home/a/notes/n.md"
    assert m.group(where["line"]) == "12"
    assert m.group(where["message"]) == "The bus leaves at seven."


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


def test_a_passage_quoting_a_file_and_line_of_its_own_is_not_misread():
    import re

    pattern = re.compile(mod.REGEXP)
    m = pattern.match("/home/a/notes/moved.txt:1: Moved from old.txt:4: to here")
    assert m.group(1) == "/home/a/notes/moved.txt" and m.group(2) == "1"
    m = pattern.match(r"C:\Users\a\notes\n.md:3: The bus")
    assert m.group(1) == r"C:\Users\a\notes\n.md" and m.group(2) == "3"


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
    got = subprocess.run([sys.executable, "-c", code, str(decoy), str(HERE / "vscode.py")],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert Path(got.stdout.strip()).parent.name == "hosts"
