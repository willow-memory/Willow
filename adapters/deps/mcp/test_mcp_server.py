"""mcp: a client can ask and suggest through the kernel's own verbs, sees a
refusal's reason, and has no way to approve."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("willow_mcp_server", HERE / "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def kernel(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


@pytest.fixture
def server(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    box = tmp_path / "box"
    kernel(
        "init",
        "--box",
        str(box),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return srv.build(box), box


def call(server, name, **args):
    got = asyncio.run(server.call_tool(name, args))
    assert not got.is_error, got
    return json.loads(got.content[0].text)


def test_exactly_ask_suggest_and_waiting_and_none_can_approve(server):
    s, _ = server
    tools = {t.name: t for t in asyncio.run(s.list_tools())}
    assert set(tools) == {"ask", "suggest", "waiting"}
    params = {p for t in tools.values() for p in t.input_schema.get("properties", {})}
    assert not params & {"key", "proof", "subject", "seal"}
    source = (HERE / "server.py").read_text()
    assert "kernel.seal" not in source and "read_key" not in source


def test_ask_then_suggest_then_it_waits_and_only_the_person_approves(server):
    s, box = server
    got = call(s, "ask", question="how much sun do tomatoes want")
    assert got["state"] == "populated" and got["served"][0]["where"] == "garden.md:1"
    cite = got["served"][0]["id"]
    waiting = call(
        s,
        "suggest",
        path="sun.md",
        answer="Six hours.",
        cites=[cite],
        reason="garden.md",
    )
    subject = waiting["waiting"]
    assert subject.startswith("proposal:")
    assert call(s, "waiting") == {"waiting": [subject]}
    assert not (box / "written").exists()  # nothing written until the person approves
    assert (
        kernel("seal", "--box", str(box), subject, *NOW).returncode == 0
    )  # the person
    assert (
        call(s, "ask", question="How much sun do tomatoes want?")["state"] == "sealed"
    )
    assert kernel("verify", "--box", str(box)).returncode == 0


def test_a_refusal_reaches_the_client_with_the_kernels_reason(server):
    s, _ = server
    call(s, "ask", question="how much sun do tomatoes want")
    with pytest.raises(Exception, match="the last bite didn't serve"):
        asyncio.run(s.call_tool("suggest", {"path": "x.md", "answer": "Eight.",
                                            "cites": ["made-up"], "reason": "guess"}))  # fmt: skip


def test_without_mcp_it_refuses_and_names_the_install(tmp_path):
    blocker = tmp_path / "block"
    (blocker / "mcp").mkdir(parents=True)
    (blocker / "mcp" / "__init__.py").write_text(
        "raise ImportError('hidden for the test')\n"
    )
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("x\n")
    box = tmp_path / "box"
    kernel(
        "init",
        "--box",
        str(box),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(HERE / 'server.py')!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(HERE / 'server.py')!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "--box", str(box)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
