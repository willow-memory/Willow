"""mcp-sampling: draft bites, samples through the client, proposes cited
replies; empty stays unsampled; nothing is sealed."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("ms", HERE / "mcp_sampling.py")
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)
NOW = ["--now", "2026-11-05T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "The gate by the acequia sticks in winter.\n"
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


def req(mid, method, **params):
    return {"jsonrpc": "2.0", "id": mid, "method": method, "params": params}


def call(mid, name, **args):
    return req(mid, "tools/call", name=name, arguments=args)


def talk(b: Path, msgs) -> list[dict]:
    lines = "".join(
        (m if isinstance(m, str) else json.dumps(m, ensure_ascii=False)) + "\n"
        for m in msgs
    )
    out = io.StringIO()
    assert ms.main(["--box", str(b)], stdin=io.StringIO(lines), stdout=out) == 0
    return [json.loads(ln) for ln in out.getvalue().splitlines()]


def run_with_sampler(b: Path, msgs, reply="Lard, not butter [1].", model="test-model"):
    """Msgs in, answering any sampling/createMessage the server sends."""
    out = io.StringIO()
    pending = [
        (m if isinstance(m, str) else json.dumps(m, ensure_ascii=False)) + "\n"
        for m in msgs
    ]

    def lines():
        while pending:
            yield pending.pop(0)

    class Out:
        def write(self, s: str) -> int:
            out.write(s)
            for ln in s.splitlines():
                if not ln.strip():
                    continue
                msg = json.loads(ln)
                if msg.get("method") == "sampling/createMessage":
                    pending.append(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": msg["id"],
                                "result": {
                                    "role": "assistant",
                                    "content": {"type": "text", "text": reply},
                                    "model": model,
                                    "stopReason": "endTurn",
                                },
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            return len(s)

        def flush(self) -> None:
            pass

    assert ms.main(["--box", str(b)], stdin=lines(), stdout=Out()) == 0
    return [json.loads(ln) for ln in out.getvalue().splitlines()]


def test_handshake_lists_draft_and_never_approves(tmp_path):
    b = box(tmp_path)
    init, listed = talk(
        b,
        [
            req(1, "initialize", protocolVersion="2025-06-18"),
            req(2, "tools/list"),
        ],
    )
    assert init["result"]["serverInfo"]["name"] == "willow-sampling"
    assert init["result"]["serverInfo"]["version"] == kernel.VERSION[:12]
    names = [t["name"] for t in listed["result"]["tools"]]
    assert names == ["ask", "suggest", "waiting", "draft"]
    assert "seal" not in names and "approve" not in names


def test_draft_samples_proposes_and_never_seals(tmp_path):
    b = box(tmp_path)
    replies = run_with_sampler(
        b, [call(1, "draft", question="what goes in biscochitos")]
    )
    assert any(r.get("method") == "sampling/createMessage" for r in replies)
    result = next(r for r in replies if r.get("id") == 1)["result"]
    assert result["isError"] is False
    doc = result["structuredContent"]
    assert doc["state"] == "waiting" and doc["sampled"] is True
    assert doc["waiting"].startswith("proposal:")
    kinds = [
        json.loads(ln)["kind"] for ln in (b / "record.jsonl").read_text().splitlines()
    ]
    assert "bite" in kinds and "proposal" in kinds and "seal" not in kinds
    sample = next(r for r in replies if r.get("method") == "sampling/createMessage")
    user = sample["params"]["messages"][0]["content"]["text"]
    assert "[1]" in user and "Biscochitos" in user
    assert "acequia" not in user


def test_nothing_served_means_no_sample(tmp_path):
    b = box(tmp_path)
    replies = run_with_sampler(
        b, [call(1, "draft", question="who won the world series")]
    )
    assert not any(r.get("method") == "sampling/createMessage" for r in replies)
    doc = replies[0]["result"]["structuredContent"]
    assert doc["state"] == "empty" and doc["sampled"] is False


def test_uncited_reply_is_proposed_to_no_one(tmp_path):
    b = box(tmp_path)
    replies = run_with_sampler(
        b,
        [call(1, "draft", question="what goes in biscochitos")],
        reply="Butter, obviously.",
    )
    doc = next(r for r in replies if r.get("id") == 1)["result"]["structuredContent"]
    assert doc["state"] == "uncited" and "proposed to no one" in doc["reason"]
    kinds = [
        json.loads(ln)["kind"] for ln in (b / "record.jsonl").read_text().splitlines()
    ]
    assert "proposal" not in kinds


def test_ask_suggest_waiting_and_a_notification(tmp_path):
    b = box(tmp_path)
    (ask,) = talk(b, [call(1, "ask", question="what goes in biscochitos")])
    cite = ask["result"]["structuredContent"]["served"][0]["id"]
    sug, wait = talk(
        b,
        [
            call(
                2,
                "suggest",
                path="bis.md",
                answer="Lard [1].",
                cites=[cite],
                reason="the recipe",
            ),
            call(3, "waiting"),
        ],
    )
    pid = sug["result"]["structuredContent"]["waiting"]
    assert pid.startswith("proposal:")
    assert sug["result"]["structuredContent"]["for"] == "the person's approval"
    assert wait["result"]["structuredContent"]["waiting"] == [pid]
    assert talk(b, [{"jsonrpc": "2.0", "method": "notifications/initialized"}]) == []


def test_a_bad_command_line_or_box_is_refused(tmp_path, capsys):
    assert ms.main([]) == 2
    err = capsys.readouterr().err
    assert "mcp_sampling.py" in err or "--box" in err
    assert ms.main(["--box", str(tmp_path)]) == 2
    assert "not a kernel box" in capsys.readouterr().err
