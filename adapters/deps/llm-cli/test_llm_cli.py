"""llm-cli: the kernel bites first, llm sees only what was served, a reply is
proposed citing what its brackets name, and nothing is asked without a passage."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("lc", HERE / "llm_cli.py")
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)
NOW = ["--now", "2026-11-05T00:00:00Z"]


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "The gate by the acequia sticks in winter.\n"
    )
    b = tmp_path / "box"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "kernel.py"),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ],
        check=True,
        capture_output=True,
    )
    return b


@pytest.fixture
def fake_llm(tmp_path, monkeypatch):
    """A stand-in `llm` on PATH: records argv, prints FAKE_REPLY."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "llm-argv.json"
    script = bin_dir / "llm"
    script.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{log}"\n'
        'printf "%s\\n" "${FAKE_REPLY:-Lard, not butter [1].}"\n'
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("FAKE_REPLY", "Lard, not butter [1].")
    return log


def run(*argv: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "llm_cli.py"), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


def test_a_cited_reply_is_proposed_and_waits_for_a_seal(box, fake_llm):
    got = run(
        "ask",
        "--box",
        str(box),
        "--model",
        "demo",
        *NOW,
        "what goes in biscochitos",
    )
    assert got.returncode == 0
    assert "Lard, not butter" in got.stdout
    assert "pass" in got.stdout and "waiting on your seal" in got.stdout
    kinds = [
        json.loads(ln)["kind"] for ln in (box / "record.jsonl").read_text().splitlines()
    ]
    assert kinds[-2:] == ["bite", "proposal"] and "seal" not in kinds
    argv = fake_llm.read_text().splitlines()
    assert "--no-stream" in argv and "-m" in argv and "demo" in argv
    assert "-s" in argv
    joined = " ".join(argv)
    assert "[1]" in joined and "Biscochitos" in joined
    assert "acequia" not in joined


def test_nothing_served_means_no_llm_is_asked(box, fake_llm):
    got = run(
        "ask",
        "--box",
        str(box),
        *NOW,
        "who won the world series",
    )
    assert got.returncode == 42
    assert got.stdout == "nothing in your folder holds that; no model was asked\n"
    assert not fake_llm.exists() or fake_llm.read_text() == ""


def test_uncited_reply_is_proposed_to_no_one(box, fake_llm, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", "Butter, obviously.")
    got = run(
        "ask",
        "--box",
        str(box),
        *NOW,
        "what goes in biscochitos",
    )
    assert got.returncode == 42
    assert "cited no passage; proposed to no one" in got.stdout
    kinds = [
        json.loads(ln)["kind"] for ln in (box / "record.jsonl").read_text().splitlines()
    ]
    assert "proposal" not in kinds


def test_missing_llm_is_unreachable(box, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent")
    got = run("ask", "--box", str(box), *NOW, "what goes in biscochitos")
    assert got.returncode == 42
    assert "unreachable: llm" in got.stdout


def test_a_bad_command_line_is_refused(capsys):
    assert lc.main([]) == 2
    assert "llm_cli.py" in capsys.readouterr().err
    assert lc.main(["ask", "--box", "/tmp", "--model"]) == 2
