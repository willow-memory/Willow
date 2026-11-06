"""hooks-elsewhere: each host's envelope holds Claude Code's answer byte for
byte; empty stays empty; setup prints and writes nothing."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
CLAUDE = HERE.parent / "claude-code" / "hook.py"
spec = importlib.util.spec_from_file_location("he", HERE / "hooks_elsewhere.py")
he = importlib.util.module_from_spec(spec)
spec.loader.exec_module(he)
cc = importlib.util.spec_from_file_location("cc", CLAUDE)
hk = importlib.util.module_from_spec(cc)
cc.loader.exec_module(hk)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text(
        "The bus leaves at seven from the square.\n\nWhen does the ferry sail?\n"
    )
    b = tmp_path / "box"
    assert (
        subprocess.run(
            [
                sys.executable,
                str(KERNEL),
                "init",
                "--box",
                str(b),
                "--pile",
                str(pile),
                "--key",
                str(tmp_path / "k"),
                *NOW,
            ],
            capture_output=True,
        ).returncode
        == 0
    )
    return b


def claude_said(b: Path, ask: dict) -> str:
    return hk.prompt(b, io.StringIO(json.dumps(ask)))


def elsewhere(host: str, b: Path, ask: dict) -> str:
    return he.prompt(host, b, io.StringIO(json.dumps(ask)))


def test_each_host_holds_claude_codes_answer_byte_for_byte(tmp_path):
    b = box(tmp_path)
    ask = {"prompt": "when does the bus leave the square"}
    body = claude_said(b, ask)
    assert body.startswith(hk.FRAME) and "n.md:1:" in body
    assert elsewhere("codex-cli", b, ask) == body
    assert elsewhere("opencode", b, ask) == body
    gem = elsewhere("gemini-cli", b, ask)
    doc = json.loads(gem)
    assert doc["hookSpecificOutput"]["hookEventName"] == "BeforeAgent"
    assert doc["hookSpecificOutput"]["additionalContext"] == body


def test_empty_stays_empty_on_every_host(tmp_path):
    b = box(tmp_path)
    for host in he.HOSTS:
        assert elsewhere(host, b, {"prompt": "zebra crossing"}) == ""
        assert elsewhere(host, b, {"prompt": ""}) == ""
        assert elsewhere(host, b, {"prompt": "when does the ferry sail"}) == ""


def test_an_unreadable_folder_is_wrapped_the_same_way(tmp_path):
    ask = {"prompt": "bus"}
    body = claude_said(tmp_path / "nobox", ask)
    assert body.startswith("willow: couldn't read your folder")
    assert elsewhere("codex-cli", tmp_path / "nobox", ask) == body
    gem = elsewhere("gemini-cli", tmp_path / "nobox", ask)
    assert json.loads(gem)["hookSpecificOutput"]["additionalContext"] == body


def test_a_bad_prompt_names_the_host_not_claude(tmp_path):
    b = box(tmp_path)
    for host, title in (
        ("gemini-cli", "Gemini CLI"),
        ("codex-cli", "Codex CLI"),
        ("opencode", "OpenCode"),
    ):
        assert he.prompt(host, b, io.StringIO("null")) == (
            f"willow: couldn't read the prompt {title} sent\n"
        )


def test_the_prompt_is_on_the_record_by_fingerprint_not_words(tmp_path):
    b = box(tmp_path)
    elsewhere("gemini-cli", b, {"prompt": "when does the bus leave the square"})
    record = (b / "record.jsonl").read_text()
    assert '"kind": "bite"' in record or '"kind":"bite"' in record
    assert "square" not in record


def test_prompt_always_exits_zero(tmp_path):
    b = box(tmp_path)
    for host in he.HOSTS:
        for box_path in (b, tmp_path / "nobox"):
            got = subprocess.run(
                [
                    sys.executable,
                    str(HERE / "hooks_elsewhere.py"),
                    "prompt",
                    "--host",
                    host,
                    "--box",
                    str(box_path),
                ],
                input='{"prompt": "bus"}',
                capture_output=True,
                text=True,
            )
            assert got.returncode == 0


def test_setup_prints_the_host_hook_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert he.main(["setup", "--host", "gemini-cli", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    hook = json.loads(out.split("\n\n")[1])
    cmd = hook["hooks"]["BeforeAgent"][0]["hooks"][0]
    assert cmd["type"] == "command" and cmd["name"] == "willow-passages"
    assert f"prompt --host gemini-cli --box {b.resolve()}" in cmd["command"]
    assert sys.executable in cmd["command"]
    assert '\n  "hooks"' in out  # json.dumps indent=2, not 1 or 3
    assert "hosts.py show gemini-cli" in out
    assert sorted(p.name for p in b.iterdir()) == before
    assert he.main(["setup", "--host", "codex-cli", "--box", str(b)]) == 0
    codex = json.loads(capsys.readouterr().out.split("\n\n")[1])
    assert "UserPromptSubmit" in codex["hooks"]
    assert he.main(["setup", "--host", "opencode", "--box", str(b)]) == 0
    oc = capsys.readouterr().out
    assert "willow-passages.js" in oc and "synthetic: true" in oc
    assert f'"--box", "{b.resolve()}"' in oc or str(b.resolve()) in oc
    assert "Claude-compatible" in oc and "UserPromptSubmit" in oc


def test_list_names_each_host(capsys):
    assert he.main(["list"]) == 0
    out = capsys.readouterr().out
    for name in he.HOSTS:
        assert name in out


def test_a_bad_command_line_host_or_box_is_refused(tmp_path, capsys):
    assert he.main([]) == 2
    assert "setup" in capsys.readouterr().err
    assert he.main(["setup", "--host", "gemini-cli", "--box", str(tmp_path)]) == 2
    assert "not a kernel box" in capsys.readouterr().err
    assert he.main(["setup", "--host", "nope", "--box", str(tmp_path / "x")]) == 2
    assert "no host called nope" in capsys.readouterr().err
    assert (
        he.main(["setup", "--host", "claude-code", "--box", str(tmp_path / "x")]) == 2
    )
    assert "adapters/stdlib/claude-code" in capsys.readouterr().err


def test_a_folder_with_a_space_in_its_name_stays_one_piece(tmp_path, capsys):
    import shlex

    (tmp_path / "with space").mkdir()
    b = box(tmp_path / "with space")
    assert he.main(["setup", "--host", "codex-cli", "--box", str(b)]) == 0
    cmd = json.loads(capsys.readouterr().out.split("\n\n")[1])["hooks"][
        "UserPromptSubmit"
    ][0]["hooks"][0]
    argv = shlex.split(cmd["command"])
    assert argv[argv.index("--box") + 1] == str(b.resolve())


BESIDE = (HERE.parent / "index-cache").is_dir() and (HERE.parent / "scan").is_dir()


def test_alone_an_index_is_never_asked_and_setup_says_what_it_needs(tmp_path, capsys):
    """Without scan and index-cache, setup --index is refused; with them, the
    hook command carries --index and a wrong strip of those two args fails."""
    b = box(tmp_path)
    at = tmp_path / "index"
    if not BESIDE:
        assert (
            he.main(
                ["setup", "--host", "gemini-cli", "--box", str(b), "--index", str(at)]
            )
            == 2
        )
        assert "needs index-cache and scan" in capsys.readouterr().err
        return
    assert (
        he.main(["setup", "--host", "gemini-cli", "--box", str(b), "--index", str(at)])
        == 0
    )
    out = capsys.readouterr().out
    cmd = json.loads(out.split("\n\n")[1])["hooks"]["BeforeAgent"][0]["hooks"][0]
    assert cmd["command"].endswith(f"--index {at.resolve()}")
    assert "index_cache.py --from" in out
    assert sys.executable in out.split("index_cache.py")[0].split("\n")[-1]
    assert (
        he.main(["setup", "--host", "gemini-cli", "--box", str(b), "--index", ""]) == 2
    )
