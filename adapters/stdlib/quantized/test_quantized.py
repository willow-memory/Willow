"""quantized: each local model sits model-exam's exam, smallest first, and
the smallest that passes every marked question is named."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SCRIPT = HERE / "quantized.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
Q1, Q2 = "what goes in biscochitos", "when does the gate stick"
RIGHT = {Q1: "Lard, not butter, and anise seed [1].", Q2: "It sticks in winter [1]."}


class Server:
    """A stand-in Ollama on 127.0.0.1: `say[model]` maps a question to a reply."""

    def __init__(self, tags=None):
        self.say, self.sent = {}, []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def send(self, body: bytes, code: int = 200):
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/v1/models":
                    return self.send(
                        json.dumps({"data": [{"id": m} for m in server.say]}).encode()
                    )
                if self.path == "/api/tags" and tags is not None:
                    return self.send(json.dumps(tags).encode())
                self.send(b"", 404)

            def do_POST(self):
                n = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(n))
                server.sent.append(body["model"])
                user = body["messages"][1]["content"]
                said = next(
                    (
                        a
                        for q, a in server.say[body["model"]].items()
                        if user.endswith(q)
                    ),
                    "?",
                )
                self.send(
                    json.dumps({"choices": [{"message": {"content": said}}]}).encode()
                )

            def log_message(self, *a):
                pass

        self.http = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.http.server_port}/v1"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()


TAGS = {"models": [
    {"name": "gemma3:4b", "size": 3338801804, "details": {"quantization_level": "Q4_K_M"}},
    {"name": "gemma3:1b", "size": 815319791, "details": {"quantization_level": "Q4_K_M"}},
    {"name": "gemma3:12b", "size": 8149190253, "details": {"quantization_level": "Q2_K"}},
    {"name": "big", "size": 9000000000, "details": {}},
    {"name": "odd", "size": "big"}, "stray",
]}  # fmt: skip


@pytest.fixture
def server():
    s = Server(TAGS)
    s.say = {
        "gemma3:12b": RIGHT,
        "big": {},
        "gemma3:4b": RIGHT,
        "gemma3:1b": {Q1: RIGHT[Q1], Q2: "The hinge wants oil [1]."},
    }
    yield s
    s.http.shutdown()


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv), *NOW],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def seal(box: Path, tmp_path: Path, question: str, answer: str) -> None:
    served = json.loads(k("bite", "--box", box, question).stdout)["served"]
    f = tmp_path / "s.jsonl"
    f.write_text(
        json.dumps(
            {
                "path": "a.md",
                "data": answer,
                "cites": [served[0]["id"]],
                "claim": "mine",
            }
        )
        + "\n"
    )
    subj = re.search(
        r"proposal:[0-9a-f]{64}", k("propose", "--box", box, "--file", f).stdout
    ).group(0)
    assert k("seal", "--box", box, subj).returncode == 0


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and anise seed.\n"
    )
    (pile / "gate.txt").write_text("The gate by the acequia sticks in winter.\n")
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    seal(b, tmp_path, Q1, RIGHT[Q1] + "\n")
    seal(b, tmp_path, Q2, RIGHT[Q2] + "\n")
    return b


def questions(tmp_path: Path, *qs: str) -> Path:
    p = tmp_path / "exam.txt"
    p.write_text("\n".join(qs) + "\n")
    return p


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def test_the_smallest_model_that_passes_everything_is_named(box, server, tmp_path):
    before = (box / "record.jsonl").read_bytes()
    got = run(
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1, Q2, "how tall is the moon"),
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout == (
        "gemma3:1b   815319791 bytes  Q4_K_M  passed 1 of 2\n"
        "gemma3:4b   3338801804 bytes  Q4_K_M  passed 2 of 2\n"
        "gemma3:12b  8149190253 bytes  Q2_K  passed 2 of 2\n"
        "big         9000000000 bytes  quantization not said  passed 0 of 2\n"
        "smallest passing all 2: gemma3:4b, 3338801804 bytes\n"
    )
    assert sorted(server.sent) == sorted(
        ["gemma3:12b", "gemma3:4b", "gemma3:1b", "big"] * 2
    )
    assert (box / "record.jsonl").read_bytes() == before


def test_named_models_only_and_one_the_server_gives_no_size_for(box, server, tmp_path):
    server.say["mystery"] = RIGHT
    got = run("--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1, Q2),
              "--model", "mystery", "--model", "gemma3:1b", "--model", "mystery")  # fmt: skip
    assert got.returncode == 0
    assert got.stdout == (
        "gemma3:1b  815319791 bytes  Q4_K_M  passed 1 of 2\n"
        "mystery    size not said by the server  passed 2 of 2\n"
        "smallest passing all 2: mystery, its size not said\n"
    )


def test_a_server_without_ollamas_list_gives_no_sizes(box, tmp_path):
    plain = Server(tags=None)
    plain.say = {"b": RIGHT, "a": RIGHT}
    try:
        got = run(
            "--box", box, "--url", plain.url, "--questions", questions(tmp_path, Q1, Q2)
        )
        assert got.returncode == 0
        assert got.stdout.splitlines() == [
            "a  size not said by the server  passed 2 of 2",
            "b  size not said by the server  passed 2 of 2",
            "smallest passing all 2: a, its size not said",
        ]
    finally:
        plain.http.shutdown()
    flat = Server(tags=["not", "a", "dict"])
    flat.say = {"a": RIGHT}
    try:
        got = run(
            "--box", box, "--url", flat.url, "--questions", questions(tmp_path, Q1)
        )
        assert "a  size not said by the server  passed 1 of 1\n" in got.stdout
    finally:
        flat.http.shutdown()


def test_none_passing_everything_is_42(box, server, tmp_path):
    got = run(
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1, Q2),
        "--model",
        "gemma3:1b",
    )
    assert got.returncode == 42 and got.stdout.endswith("none passed all 2\n")


def test_nothing_to_mark_asks_nothing(box, server, tmp_path):
    got = run(
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, "how tall is the moon"),
    )
    assert got.returncode == 42 and got.stdout.startswith("nothing to mark")
    assert server.sent == []
    pile = Path(json.loads((box / "kernel.json").read_text())["pile"])
    (pile / "gate.txt").unlink()
    got = run("--box", box, "--url", server.url, "--questions", questions(tmp_path, Q2))
    assert got.returncode == 42 and got.stdout.startswith("nothing to mark")


def test_no_server_a_server_with_no_model_and_one_that_breaks(box, tmp_path):
    closed = "http://127.0.0.1:9/v1"
    got = run("--box", box, "--url", closed, "--questions", questions(tmp_path, Q1))
    assert (
        got.returncode == 42
        and got.stdout == f"no local model server is running (looked at {closed})\n"
    )
    empty = Server(tags=None)
    try:
        got = run(
            "--box", box, "--url", empty.url, "--questions", questions(tmp_path, Q1)
        )
        assert got.returncode == 2 and "offers no model" in got.stderr
        got = run(
            "--box",
            box,
            "--url",
            empty.url,
            "--questions",
            questions(tmp_path, Q1),
            "--model",
            "ghost",
        )
        assert got.returncode == 42 and got.stdout.startswith(
            f"unreachable: {empty.url} ("
        )
        assert got.stdout.endswith(", asking ghost\n")
    finally:
        empty.http.shutdown()


def test_a_box_with_a_words_list_that_doesnt_read_is_refused(tmp_path, server):
    pile = tmp_path / "pile3"
    pile.mkdir()
    (pile / "recipes.txt").write_text("Biscochitos: lard, not butter.\n")
    wl = tmp_path / "words.txt"
    wl.write_text("cookies = biscochitos\n")
    wl.chmod(0o600)
    b = tmp_path / "box3"
    assert (
        k(
            "init", "--box", b, "--pile", pile, "--key", tmp_path / "k3", "--words", wl
        ).returncode
        == 0
    )
    seal(b, tmp_path, "what goes in cookies", "Lard [1].\n")
    wl.write_text("cookies biscochitos\n")
    got = run(
        "--box",
        b,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, "what goes in cookies"),
    )
    assert got.returncode == 2 and "words list line 1" in got.stderr


def test_a_bad_command_line_is_refused(box, tmp_path):
    q = questions(tmp_path, Q1)
    base = ["--box", box, "--questions", q]
    for argv in ([], base[:2], base + ["stray"], base + ["--url", ""], base + ["--model", ""],
                 base + ["--box", box]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "quantized.py" in got.stderr, argv
    got = run(*base, "--url", "http://example.org/v1")
    assert got.returncode == 2 and "not on this machine" in got.stderr
    got = run("--box", tmp_path, "--questions", q)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run("--box", box, "--questions", tmp_path / "missing.txt")
    assert got.returncode == 2 and "can't read the questions" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 99}\n')
    got = run(*base)
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_reply_of_one_word_can_pass(box, server, tmp_path):
    server.say["terse"] = {Q1: "Lard [1]."}
    got = run(
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1),
        "--model",
        "terse",
    )
    assert (
        got.returncode == 0
        and "terse  size not said by the server  passed 1 of 1\n" in got.stdout
    )
