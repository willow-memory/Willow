"""hosts: one table of the assistants that take an MCP server, printing
the lines for each, and nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = load("hosts", HERE / "hosts.py")


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text("The bus leaves at seven.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    return b


def test_each_host_has_the_shape_its_assistant_reads(tmp_path):
    b = box(tmp_path)
    py, args = "/usr/bin/python3", [str(mod.SERVER), "--box", str(b.resolve())]
    plain = {"command": py, "args": args}
    want = {
        "cursor": [{"mcpServers": {"willow": plain}}],
        "gemini-cli": [{"mcpServers": {"willow": plain}}],
        "windsurf": [{"mcpServers": {"willow": plain}}],
        "zed": [{"context_servers": {"willow": {**plain, "env": {}}}}],
        "opencode": [
            {
                "$schema": "https://opencode.ai/config.json",
                "mcp": {
                    "willow": {"type": "local", "command": [py, *args], "enabled": True}
                },
            }
        ],
        "copilot": [
            {"servers": {"willow": {"type": "stdio", **plain}}},
            {"mcpServers": {"willow": {"type": "local", **plain, "tools": ["*"]}}},
        ],
    }
    assert sorted(mod.HOSTS) == sorted([*want, "codex-cli"])
    for name, docs in want.items():
        found = mod.places(name, b, py)
        assert [kind for _, kind, _ in found] == ["json"] * len(docs)
        assert [value for _, _, value in found] == docs
    ((_, kind, text),) = mod.places("codex-cli", b, py)
    assert kind == "toml"
    assert text == mod.toml_table("mcp_servers.willow", plain)


def test_toml_tables_are_written_the_way_toml_reads_them():
    text = mod.toml_table("a.b", {"command": "py", "args": ["x", 'q"uote']})
    assert text == '[a.b]\ncommand = "py"\nargs = ["x", "q\\"uote"]\n'


def test_every_one_assistant_addon_is_this_table_and_prints_the_same(tmp_path):
    """Each assistant's own add-on beside this one prints what this table
    does: all of them in willow (ci's test_contract holds that every row has
    one), the ones a copy holds in a copy."""
    b = box(tmp_path)
    beside = [n for n in mod.HOSTS if (STDLIB / n).is_dir()]
    for name in beside:
        own = load(name, STDLIB / name / f"{name.replace('-', '_')}.py")
        assert own.render(b, "py") == mod.render(name, b, "py")


def test_cli_prints_for_a_box_and_refuses_the_rest(tmp_path, capsys):
    b = box(tmp_path)
    doc = "x.py: y.\n\n    python x.py --box DIR\n\nmore"
    assert mod.cli(doc, lambda box: "hello\n", ["--box", str(b)]) == 0
    assert capsys.readouterr().out == "hello\n"
    for bad in ([], ["--box"], ["--to", str(b)], ["--box", str(tmp_path)]):
        assert mod.cli(doc, lambda box: "hello\n", bad) == 2
    err = capsys.readouterr().err
    assert err.count("python x.py --box DIR") == 3 and "not a kernel box" in err


@pytest.mark.parametrize("name", sorted(mod.HOSTS))
def test_each_host_starts_mcp_lite_over_the_box(name, tmp_path):
    b = box(tmp_path)
    text = mod.render(name, b, "/usr/bin/python3").split(":\n\n", 1)[1]
    doc = (
        text
        if name == "codex-cli"
        else json.dumps(json.loads(text.split("\n\nAdd this to")[0]))
    )
    assert "/usr/bin/python3" in doc and "mcp-lite/server.py" in doc
    assert json.dumps(str(b.resolve())) in doc and "--box" in doc


def test_the_server_it_names_exists_and_the_table_is_sorted():
    assert mod.SERVER.is_file() and mod.SERVER.parent.name == "mcp-lite"
    assert list(mod.HOSTS) == sorted(mod.HOSTS)


def test_list_names_every_host_with_its_place(capsys):
    assert mod.main(["list"]) == 0
    rows = [line.split("\t") for line in capsys.readouterr().out.splitlines()]
    assert [r[0] for r in rows] == list(mod.HOSTS)
    assert all(r[1] and r[2] for r in rows)


def test_show_prints_the_host_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert mod.main(["show", "zed", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    assert (
        out.startswith("Add this to ~/.config/zed/settings.json")
        and "context_servers" in out
    )
    assert sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_host_or_box_is_refused(tmp_path, capsys):
    b = box(tmp_path)
    assert (
        mod.main([]) == 2 and mod.main(["show"]) == 2 and mod.main(["list", "x"]) == 2
    )
    assert mod.main(["show", "emacs-nope", "--box", str(b)]) == 2
    assert "no host called emacs-nope" in capsys.readouterr().err
    assert mod.main(["show", "zed", "--box", str(tmp_path)]) == 2
