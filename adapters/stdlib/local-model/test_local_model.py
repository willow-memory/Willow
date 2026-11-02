"""local-model: openai-compatible's ask, held to this machine, finding the
server and its model when they aren't named."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "local_model.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]


class Server:
    """A stand-in local server on 127.0.0.1: lists `offered`, says `reply`."""

    def __init__(self, offered=("gemma3:4b", "qwen3:8b"), listing=None):
        self.reply, self.sent = "Lard, not butter [1].", []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def send(self, code: int, body: bytes):
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path != "/v1/models":
                    return self.send(404, b"")
                doc = (
                    listing
                    if listing is not None
                    else {"data": [{"id": m} for m in offered]}
                )
                self.send(200, json.dumps(doc).encode())

            def do_POST(self):
                n = int(self.headers["Content-Length"])
                server.sent.append(json.loads(self.rfile.read(n)))
                self.send(
                    200,
                    json.dumps(
                        {"choices": [{"message": {"content": server.reply}}]}
                    ).encode(),
                )

            def log_message(self, *a):
                pass

        self.http = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.http.server_port}/v1"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()


@pytest.fixture
def server():
    s = Server()
    yield s
    s.http.shutdown()


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and anise seed.\n"
    )
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(b),
                    "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def kinds(box: Path) -> list[str]:
    return [
        json.loads(line)["kind"]
        for line in (box / "record.jsonl").read_text().splitlines()
    ]


def test_servers_says_what_runs_and_what_it_offers(server):
    closed = "http://127.0.0.1:9/v1"
    got = run("servers", "--url", server.url, "--url", closed)
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        f"given          {server.url}  gemma3:4b, qwen3:8b\n"
        f"given          {closed}  not running\n"
    )
    got = run("servers", "--url", closed)
    assert got.returncode == 42


def test_a_server_offering_nothing_or_answering_nonsense(tmp_path):
    empty, odd, flat = (
        Server(offered=()),
        Server(listing={"models": []}),
        Server(listing=[1]),
    )
    try:
        got = run("servers", "--url", empty.url, "--url", odd.url, "--url", flat.url)
        assert got.stdout.splitlines() == [
            f"given          {empty.url}  offers no model",
            f"given          {odd.url}  not running",
            f"given          {flat.url}  not running",
        ]
    finally:
        for s in (empty, odd, flat):
            s.http.shutdown()


def test_ask_takes_the_first_model_the_server_offers(box, server):
    got = run(
        "ask", "--box", box, "--url", server.url, *NOW, "what goes in biscochitos"
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.startswith("Lard, not butter [1].\n")
    assert server.sent[0]["model"] == "gemma3:4b"
    assert kinds(box)[-2:] == ["bite", "proposal"]


def test_ask_uses_the_model_named(box, server):
    got = run("ask", "--box", box, "--url", server.url, "--model", "qwen3:8b", *NOW,
              "what goes in biscochitos")  # fmt: skip
    assert got.returncode == 0 and server.sent[0]["model"] == "qwen3:8b"


def test_a_named_model_is_asked_where_no_list_answers(box, server):
    bare = Server(listing={"nope": 1})
    try:
        got = run(
            "ask",
            "--box",
            box,
            "--url",
            bare.url,
            "--model",
            "m",
            *NOW,
            "what goes in biscochitos",
        )
        assert got.returncode == 0 and bare.sent[0]["model"] == "m"
        got = run(
            "ask", "--box", box, "--url", bare.url, *NOW, "what goes in biscochitos"
        )
        assert got.returncode == 42
        assert (
            got.stdout == f"no local model server is running (looked at {bare.url})\n"
        )
    finally:
        bare.http.shutdown()


def test_a_server_offering_no_model_is_refused_unless_one_is_named(box):
    empty = Server(offered=())
    try:
        got = run(
            "ask", "--box", box, "--url", empty.url, *NOW, "what goes in biscochitos"
        )
        assert got.returncode == 2 and "offers no model" in got.stderr
        assert kinds(box) == ["boot"], "nothing bitten before the refusal"
    finally:
        empty.http.shutdown()


def test_no_server_running_on_the_usual_ports_is_42(box):
    """None of the usual ports answer on the machine the tests run on."""
    got = run("ask", "--box", box, *NOW, "what goes in biscochitos")
    if got.stdout.startswith("no local model server is running"):
        assert got.returncode == 42
        assert "http://127.0.0.1:11434/v1, http://127.0.0.1:1234/v1" in got.stdout
        assert kinds(box) == ["boot"]
    got = run("servers")
    assert got.stdout.splitlines()[0].startswith(
        "ollama         http://127.0.0.1:11434/v1  "
    )
    assert len(got.stdout.splitlines()) == 7


@pytest.mark.parametrize(
    "url", ["http://example.org/v1", "http://10.0.0.2:8080/v1", "x"]
)
def test_a_url_off_this_machine_is_refused_before_anything_is_sent(url, box):
    got = run(
        "ask",
        "--box",
        box,
        "--url",
        url,
        "--model",
        "m",
        *NOW,
        "what goes in biscochitos",
    )
    assert got.returncode == 2 and "not on this machine" in got.stderr
    assert kinds(box) == ["boot"]
    got = run("servers", "--url", url)
    assert got.returncode == 2 and "not on this machine" in got.stderr


def test_localhost_and_ipv6_loopback_are_this_machine(box):
    for url in ("http://localhost:9/v1", "http://[::1]:9/v1"):
        got = run("ask", "--box", box, "--url", url, *NOW, "what goes in biscochitos")
        assert got.returncode == 42 and got.stdout.startswith(
            "no local model server"
        ), url


def test_a_bad_command_line_is_refused(box, server):
    for argv in ([], ["talk"], ["servers", "stray"], ["servers", "--url"],
                 ["ask", "--box", box], ["ask", "--box", box, "--url", "", "q"],
                 ["ask", "--box", box, "--model", "a", "--model", "b", "q"],
                 ["ask", "--box", box, "q", "more"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "local_model.py" in got.stderr, argv
    assert server.sent == []
