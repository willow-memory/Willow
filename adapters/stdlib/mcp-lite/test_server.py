"""mcp-lite: the protocol's handshake and three tools over stdio, nothing to
approve with, and every call on the kernel's record."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("mcp_lite", HERE / "server.py")
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text("The bus leaves at seven from the square.\n")
    b = tmp_path / "box"
    assert subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                           "--key", str(tmp_path / "k"), *NOW], capture_output=True).returncode == 0  # fmt: skip
    return b


def talk(b: Path, *msgs) -> list[dict]:
    out = io.StringIO()
    lines = "".join((m if isinstance(m, str) else json.dumps(m)) + "\n" for m in msgs)
    assert ml.main(["--box", str(b)], stdin=io.StringIO(lines), stdout=out) == 0
    return [json.loads(ln) for ln in out.getvalue().splitlines()]


def req(mid, method, **params):
    return {"jsonrpc": "2.0", "id": mid, "method": method, "params": params}


def call(mid, name, **args):
    return req(mid, "tools/call", name=name, arguments=args)


def test_the_handshake_names_willow_and_offers_tools(tmp_path):
    (init,) = talk(box(tmp_path), req(1, "initialize", protocolVersion="2025-03-26"),
                   {"jsonrpc": "2.0", "method": "notifications/initialized"})  # fmt: skip
    r = init["result"]
    assert init["id"] == 1 and r["protocolVersion"] == "2025-03-26"
    assert r["capabilities"] == {"tools": {}} and r["serverInfo"]["name"] == "willow"


def test_a_version_it_doesnt_speak_gets_its_newest():
    (r,) = [ml.answer(Path("."), req(1, "initialize", protocolVersion="1999-01-01"))]
    assert r["result"]["protocolVersion"] == ml.VERSIONS[0]


def test_three_tools_and_none_approves(tmp_path):
    (got,) = talk(box(tmp_path), req(2, "tools/list"))
    names = [t["name"] for t in got["result"]["tools"]]
    assert names == ["ask", "suggest", "waiting"]


def test_ask_suggest_and_waiting_go_through_the_kernel(tmp_path):
    b = box(tmp_path)
    (ask,) = talk(b, call(1, "ask", question="when does the bus leave the square"))
    doc = ask["result"]["structuredContent"]
    assert ask["result"]["isError"] is False and doc["served"][0]["where"] == "n.md:1"
    cite = doc["served"][0]["id"]
    sug, wait = talk(b, call(2, "suggest", path="bus.md", answer="Seven.", cites=[cite],
                             reason="the timetable says so"), call(3, "waiting"))  # fmt: skip
    pid = sug["result"]["structuredContent"]["waiting"]
    assert wait["result"]["structuredContent"]["waiting"] == [pid]
    kinds = [
        json.loads(ln)["kind"] for ln in (b / "record.jsonl").read_text().splitlines()
    ]
    assert "bite" in kinds and "proposal" in kinds and "seal" not in kinds


def test_a_cite_the_last_ask_didnt_serve_is_a_tool_error(tmp_path):
    b = box(tmp_path)
    talk(b, call(1, "ask", question="bus"))
    (got,) = talk(
        b, call(2, "suggest", path="x.md", answer="y", cites=["f" * 64], reason="z")
    )
    assert got["result"]["isError"] is True and got["result"]["content"][0]["text"]


def test_an_unknown_tool_is_a_tool_error(tmp_path):
    (got,) = talk(box(tmp_path), call(1, "seal", id="x"))
    assert (
        got["result"]["isError"] is True
        and "no tool" in got["result"]["content"][0]["text"]
    )


def test_ping_unknown_methods_and_bad_json(tmp_path):
    ping, unknown, bad = talk(
        box(tmp_path), req(1, "ping"), req(2, "resources/list"), "{not json"
    )
    assert ping["result"] == {}
    assert unknown["error"]["code"] == -32601
    assert bad["error"]["code"] == -32700 and bad["id"] is None


def test_a_notification_gets_no_answer(tmp_path):
    assert (
        talk(box(tmp_path), {"jsonrpc": "2.0", "method": "notifications/initialized"})
        == []
    )


def test_a_bad_command_line_or_box_is_refused(tmp_path, capsys):
    assert ml.main([], stdin=io.StringIO("")) == 2
    assert ml.main(["--box", str(tmp_path)], stdin=io.StringIO("")) == 2
    assert "not a kernel box" in capsys.readouterr().err
