"""translate: an answer you sealed, translated on this machine, proposed as
the answer to its own question with the original beside it."""

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
SCRIPT = HERE / "translate.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
Q = "what goes in biscochitos"
ANSWER = "Lard, not butter, and anise seed [1].\n"


class Server:
    """A stand-in local server on 127.0.0.1: lists `offered`, says `reply`."""

    def __init__(self, offered=("gemma3:4b",)):
        self.reply, self.sent = "Manteca, no mantequilla, y anís [1].", []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def send(self, body: bytes):
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self.send(json.dumps({"data": [{"id": m} for m in offered]}).encode())

            def do_POST(self):
                n = int(self.headers["Content-Length"])
                server.sent.append(json.loads(self.rfile.read(n)))
                self.send(
                    json.dumps(
                        {"choices": [{"message": {"content": server.reply}}]}
                    ).encode()
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


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv), *NOW],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def seal_one(
    box: Path, tmp_path: Path, question: str, answer: str, cite: bool = True
) -> str:
    """What a person does: bite, take a suggestion, seal it."""
    served = json.loads(k("bite", "--box", box, question).stdout)["served"]
    f = tmp_path / "s.jsonl"
    row = {"path": "answers/a.md", "data": answer, "cites": [served[0]["id"]] if cite else [],
           "claim": "mine"}  # fmt: skip
    f.write_text(json.dumps(row) + "\n")
    subj = re.search(
        r"proposal:[0-9a-f]{64}", k("propose", "--box", box, "--file", f).stdout
    ).group(0)
    assert k("seal", "--box", box, subj).returncode == 0
    return subj


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and anise seed. In Spanish they are bizcochitos.\n"
    )
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    return b


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def rows(box: Path) -> list[dict]:
    return [
        json.loads(line) for line in (box / "record.jsonl").read_text().splitlines()
    ]


def test_a_sealed_answer_is_translated_and_held_for_your_seal(box, server, tmp_path):
    subj = seal_one(box, tmp_path, Q, ANSWER)
    got = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
    assert got.returncode == 0, got.stdout + got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == "Manteca, no mantequilla, y anís [1]."
    assert re.fullmatch(r"pass  proposal:[0-9a-f]{64}  waiting on your seal", lines[1])
    body = server.sent[0]
    assert body["model"] == "gemma3:4b" and body["temperature"] == 0
    assert body["messages"][0]["content"].startswith(
        "Translate the user's text into Spanish."
    )
    assert body["messages"][1]["content"] == ANSWER
    new = lines[1].split()[1]
    prop = json.loads((box / "proposals" / f"{new[9:]}.json").read_text())
    assert prop["path"] == "answers/what-goes-in-biscochitos.spanish.md"
    assert (
        prop["data"] == f"Manteca, no mantequilla, y anís [1].\n\nOriginal:\n\n{ANSWER}"
    )
    assert prop["claim"] == (
        f"gemma3:4b at {server.url} (temperature 0, seed 0) translated {subj} into"
        " Spanish"
    )
    original = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    assert prop["cites"] == original["cites"], "the original's passage, served again"
    assert rows(box)[-2]["kind"] == "bite" and rows(box)[-1]["verdict"] == "pass"
    assert k("verify", "--box", box).returncode == 0


def test_once_sealed_the_translation_answers_its_own_question_not_the_original(
    box, server, tmp_path
):
    seal_one(box, tmp_path, Q, ANSWER)
    got = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
    new = re.search(r"proposal:[0-9a-f]{64}", got.stdout).group(0)
    assert k("seal", "--box", box, new).returncode == 0
    assert json.loads(k("bite", "--box", box, Q).stdout)["answer"] == ANSWER
    spanish = json.loads(k("bite", "--box", box, f"{Q} in Spanish").stdout)
    assert spanish["state"] == "sealed" and spanish["answer"].startswith("Manteca")
    again = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
    assert again.returncode == 0
    assert again.stdout == "sealed already: Manteca, no mantequilla, y anís [1].\n"
    assert len(server.sent) == 1, "a translation sealed already is not asked for again"


def test_a_translation_whose_citations_differ_is_proposed_to_no_one(
    box, server, tmp_path
):
    seal_one(box, tmp_path, Q, ANSWER)
    before = len(rows(box))
    for reply in ("Manteca y anís.", "Manteca [1] y anís [2]."):
        server.reply = reply
        got = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
        assert got.returncode == 42
        assert got.stdout.splitlines()[-1].endswith(
            "aren't the original's [1]; proposed to no one"
        )
    assert len(rows(box)) == before, "nothing bitten, nothing proposed"


def test_an_answer_citing_nothing_served_now_is_proposed_citing_nothing(
    box, server, tmp_path
):
    seal_one(box, tmp_path, Q, "Lard.\n", cite=False)
    server.reply = "Manteca."
    got = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
    assert got.returncode == 0, got.stdout
    new = re.search(r"proposal:[0-9a-f]{64}", got.stdout).group(0)
    assert (
        json.loads((box / "proposals" / f"{new[9:]}.json").read_text())["cites"] == []
    )


def test_no_sealed_answer_and_no_server_say_so(box, server, tmp_path):
    got = run("--box", box, "--into", "Spanish", "--url", server.url, *NOW, Q)
    assert (
        got.returncode == 42
        and got.stdout == "no answer you sealed for that; nothing to translate\n"
    )
    assert server.sent == []
    seal_one(box, tmp_path, Q, ANSWER)
    closed = "http://127.0.0.1:9/v1"
    got = run("--box", box, "--into", "Spanish", "--url", closed, *NOW, Q)
    assert (
        got.returncode == 42
        and got.stdout == f"no local model server is running (looked at {closed})\n"
    )
    got = run(
        "--box",
        box,
        "--into",
        "Spanish",
        "--url",
        closed,
        "--url",
        server.url,
        "--model",
        "m",
        *NOW,
        Q,
    )
    assert got.returncode == 0 and server.sent[-1]["model"] == "m"


def test_a_server_offering_no_model_and_one_that_breaks(box, tmp_path):
    seal_one(box, tmp_path, Q, ANSWER)
    empty = Server(offered=())
    try:
        got = run("--box", box, "--into", "Spanish", "--url", empty.url, *NOW, Q)
        assert got.returncode == 2 and "offers no model" in got.stderr
    finally:
        empty.http.shutdown()

    class Broken(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b'{"data": [{"id": "m"}]}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.send_response(500)
            self.end_headers()

        def log_message(self, *a):
            pass

    http = HTTPServer(("127.0.0.1", 0), Broken)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{http.server_port}/v1"
        got = run("--box", box, "--into", "Spanish", "--url", url, *NOW, Q)
        assert got.returncode == 42 and got.stdout.startswith(f"unreachable: {url} (")
    finally:
        http.shutdown()


@pytest.mark.parametrize("url", ["http://example.org/v1", "http://10.0.0.2:8080/v1"])
def test_a_url_off_this_machine_is_refused(url, box):
    got = run("--box", box, "--into", "Spanish", "--url", url, *NOW, Q)
    assert got.returncode == 2 and "not on this machine" in got.stderr


def test_a_bad_command_line_is_refused(box, tmp_path):
    for argv in ([], ["--box", box, Q], ["--box", box, "--into", "Spanish"],
                 ["--box", box, "--into", "Spanish", Q, "more"], ["--box", box, "--into", "", Q],
                 ["--box", box, "--into", "Spanish", "--url", "", Q],
                 ["--box", box, "--into", "Spanish", "--stray"], ["--box", box, "--into", "Spanish", "?"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "translate.py" in got.stderr, argv
    got = run("--box", tmp_path, "--into", "Spanish", Q)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 99}\n')
    got = run("--box", box, "--into", "Spanish", Q)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
