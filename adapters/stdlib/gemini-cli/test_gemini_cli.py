"""gemini-cli: the settings that register mcp-lite with Google's Gemini CLI, printed,
in the format Google's Gemini CLI reads, and nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("gemini_cli", HERE / "gemini_cli.py")
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


def parsed(kind: str, text: str):
    if kind == "json":
        return json.loads(text)
    tomllib = pytest.importorskip("tomllib")
    return tomllib.loads(text)


def test_each_piece_parses_and_starts_mcp_lite_over_the_box(tmp_path):
    b = box(tmp_path)
    for where, kind, value in mod.places(b, "/usr/bin/python3"):
        text = value if kind == "toml" else json.dumps(value)
        doc = json.dumps(parsed(kind, text))
        assert "/usr/bin/python3" in doc and "mcp-lite/server.py" in doc
        assert json.dumps(str(b.resolve())) in doc and "--box" in doc


def test_the_server_it_names_exists():
    assert mod.SERVER.is_file() and mod.SERVER.parent.name == "mcp-lite"


def test_it_prints_each_place_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert mod.main(["--box", str(b)]) == 0
    out = capsys.readouterr().out
    assert out.count("Add this to ") == len(mod.places(b, "py"))
    assert sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    assert mod.main([]) == 2 and mod.main(["--box"]) == 2
    assert mod.main(["--box", str(tmp_path)]) == 2


def test_what_it_prints_parses_and_uses_the_python_that_ran_it(tmp_path):
    b = box(tmp_path)
    out = mod.render(b)
    blocks = [part.split(":\n\n", 1)[1] for part in out.split("Add this to ")[1:]]
    assert len(blocks) == len(mod.places(b, "py"))
    for (where, kind, _), text in zip(mod.places(b, "py"), blocks):
        doc = json.dumps(parsed(kind, text))
        assert json.dumps(sys.executable) in doc


def test_toml_tables_are_written_the_way_toml_reads_them():
    text = mod.toml_table("a.b", {"command": "py", "args": ["x", 'q"uote']})
    assert text == '[a.b]\ncommand = "py"\nargs = ["x", "q\\"uote"]\n'
