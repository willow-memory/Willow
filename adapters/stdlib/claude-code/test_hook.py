"""claude-code: the hook frames passages as data, says nothing when nothing
holds the prompt, says why when the folder can't be read, and never blocks."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("cc_hook", HERE / "hook.py")
hk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hk)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text(
        "The bus leaves at seven from the square.\n\nWhen does the ferry sail?\n"
    )
    b = tmp_path / "box"
    assert subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                           "--key", str(tmp_path / "k"), *NOW], capture_output=True).returncode == 0  # fmt: skip
    return b


def said(b: Path, prompt) -> str:
    stdin = io.StringIO(prompt if isinstance(prompt, str) else json.dumps(prompt))
    return hk.prompt(b, stdin)


def test_passages_come_framed_as_data_with_file_and_line(tmp_path):
    got = said(
        box(tmp_path), {"prompt": "when does the bus leave the square", "cwd": "/x"}
    )
    assert got.startswith(hk.FRAME) and "not instructions" in got
    assert (
        f"{hk.OPEN}\nn.md:1:\nThe bus leaves at seven from the square.\n{hk.CLOSE}"
        in got
    )


def test_a_passage_that_only_asks_back_is_left_out(tmp_path):
    assert said(box(tmp_path), {"prompt": "when does the ferry sail"}) == ""


def test_nothing_is_printed_when_nothing_holds_the_prompt(tmp_path):
    b = box(tmp_path)
    assert said(b, {"prompt": "zebra crossing"}) == ""
    assert said(b, {"prompt": ""}) == ""


def test_an_unreadable_folder_says_why(tmp_path):
    got = said(tmp_path / "nobox", {"prompt": "bus"})
    assert (
        got
        == "willow: couldn't read your folder (refused: not a kernel box; init first)\n"
    )
    assert said(box(tmp_path), "{not json").startswith(
        "willow: couldn't read the prompt"
    )


def test_json_that_isnt_a_prompt_object_is_said_never_a_crash(tmp_path):
    """hook-fuzz found these: JSON that isn't an object, or is nested past
    Python's depth, raised a traceback and exited 1, though the hook says it
    always exits 0."""
    b = box(tmp_path)
    for sent in ("null", "[]", "5", "[" * 10_000 + "]" * 10_000):
        assert said(b, sent) == "willow: couldn't read the prompt Claude Code sent\n"


def test_the_prompt_is_on_the_record_by_fingerprint_not_words(tmp_path):
    b = box(tmp_path)
    said(b, {"prompt": "when does the bus leave the square"})
    record = (b / "record.jsonl").read_text()
    assert '"kind": "bite"' in record or '"kind":"bite"' in record
    assert "square" not in record


def test_the_hook_always_exits_zero(tmp_path):
    for b in (box(tmp_path), tmp_path / "nobox"):
        got = subprocess.run([sys.executable, str(HERE / "hook.py"), "prompt", "--box", str(b)],
                             input='{"prompt": "bus"}', capture_output=True, text=True)  # fmt: skip
        assert got.returncode == 0


def test_setup_prints_the_hook_and_the_mcp_line_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert hk.main(["setup", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    hook = json.loads(out.split("\n\n")[1])
    cmd = hook["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert (
        cmd["type"] == "command"
        and f"hook.py prompt --box {b.resolve()}" in cmd["command"]
    )
    assert "claude mcp add willow -- " in out and "mcp-lite/server.py --box" in out
    assert sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    assert hk.main([]) == 2 and hk.main(["setup", "--box"]) == 2
    assert hk.main(["setup", "--box", str(tmp_path)]) == 2


def test_a_folder_with_a_space_in_its_name_stays_one_piece(tmp_path, capsys):
    import shlex

    (tmp_path / "with space").mkdir()
    b = box(tmp_path / "with space")
    assert hk.main(["setup", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    cmd = json.loads(out.split("\n\n")[1])["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    argv = shlex.split(cmd["command"])
    assert argv[1:4] == [str(hk.HERE), "prompt", "--box"] and argv[4] == str(
        b.resolve()
    )
    add = shlex.split(out.split("    claude mcp add", 1)[1])
    assert add[add.index("--box") + 1] == str(b.resolve())


def test_each_system_gets_its_own_shells_quoting(monkeypatch):
    argv = ["/a b/python", "x"]
    monkeypatch.setattr(hk.os, "name", "posix")
    assert hk.command_line(argv) == "'/a b/python' x"
    monkeypatch.setattr(hk.os, "name", "nt")
    assert hk.command_line(argv) == '"/a b/python" x'
