"""night-batch: waiting questions asked of a local model one after another,
skipping what is settled, and stopping once you're back or past --until."""

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
SCRIPT = HERE / "night_batch.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
Q1, Q2, Q3 = (
    "what goes in biscochitos",
    "when does the gate stick",
    "where is the anise kept",
)


class Server:
    """A stand-in local server on 127.0.0.1. `during` runs on each chat
    request before it answers: the person, busy while the model works."""

    def __init__(self):
        self.sent, self.during = [], None
        server = self

        class Handler(BaseHTTPRequestHandler):
            def send(self, body: bytes):
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self.send(b'{"data": [{"id": "gemma3:4b"}]}')

            def do_POST(self):
                n = int(self.headers["Content-Length"])
                server.sent.append(json.loads(self.rfile.read(n)))
                if server.during:
                    server.during()
                self.send(
                    json.dumps(
                        {"choices": [{"message": {"content": "From the folder [1]."}}]}
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


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text("Biscochitos: lard, not butter, and anise seed.\n\n"
                                      "The anise is kept in the blue tin.\n")  # fmt: skip
    (pile / "gate.txt").write_text("The gate by the acequia sticks in winter.\n")
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    return b


def questions(tmp_path: Path, *qs: str) -> Path:
    p = tmp_path / "questions.txt"
    p.write_text("\n".join(qs) + "\n")
    return p


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def kinds(box: Path) -> list[str]:
    return [
        json.loads(line)["kind"]
        for line in (box / "record.jsonl").read_text().splitlines()
    ]


def test_each_waiting_question_is_asked_and_proposed(box, server, tmp_path):
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1, Q2, Q1),
    )
    assert got.returncode == 0, got.stdout + got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == f"asked    {Q1}"
    assert lines[1] == "         From the folder [1]."
    assert re.fullmatch(
        r"         pass  proposal:[0-9a-f]{64}  waiting on your seal", lines[2]
    )
    assert lines[3] == f"asked    {Q2}"
    assert lines[-1] == "2 asked, 0 skipped, 0 not reached"
    assert len(server.sent) == 2
    assert kinds(box) == ["boot", "bite", "proposal", "bite", "proposal"]


def test_settled_questions_are_skipped(box, server, tmp_path):
    run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1)
    )
    subj = re.search(r"proposal:[0-9a-f]{64}", run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q2)).stdout).group(0)  # fmt: skip
    assert k("seal", "--box", box, subj).returncode == 0
    server.sent.clear()
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1, Q2, Q3),
    )
    assert got.returncode == 0, got.stdout
    assert got.stdout.splitlines()[:3] == [
        f"skipped  {Q1}: waiting on your seal already",
        f"skipped  {Q2}: answered by your seal already",
        f"asked    {Q3}",
    ]
    assert got.stdout.endswith("1 asked, 2 skipped, 0 not reached\n")
    assert len(server.sent) == 1


def test_a_declined_suggestion_is_asked_again(box, server, tmp_path):
    out = run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1)
    ).stdout
    assert (
        k(
            "decline", "--box", box, re.search(r"proposal:[0-9a-f]{64}", out).group(0)
        ).returncode
        == 0
    )
    got = run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1)
    )
    assert got.stdout.startswith(f"asked    {Q1}\n")


def test_it_stops_the_moment_you_are_back(box, server, tmp_path):
    def person():
        if len(server.sent) == 1:
            k("bite", "--box", box, "the gate")

    server.during = person
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q1, Q2, Q3),
    )
    assert got.returncode == 42
    assert got.stdout.splitlines()[-2:] == [
        "stopped  you're back: row 2 (bite) isn't this run's",
        "1 asked, 0 skipped, 2 not reached",
    ]
    assert len(server.sent) == 1


def test_your_bite_of_a_settled_question_is_yours_and_the_kernel_refuses_the_run(
    box, server, tmp_path
):
    """You bite while the model works: the run's suggestion now answers your
    bite, so the kernel refuses it, and the run stops at your row."""
    run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1)
    )

    def person():
        k("bite", "--box", box, Q1)  # a question the run skips, bitten by you

    server.during = person
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, Q2, Q1, Q3),
    )
    assert got.returncode == 42
    assert (
        "         refused  line 0: a cite that the last bite didn't serve\n"
        in got.stdout
    )
    assert got.stdout.endswith("stopped  you're back: row 4 (bite) isn't this run's\n"
                               "1 asked, 0 skipped, 2 not reached\n")  # fmt: skip


def test_it_stops_past_until(box, server, tmp_path):
    q = questions(tmp_path, Q1, Q2)
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        q,
        "--until",
        "2000-01-01T00:00:00Z",
    )
    assert got.returncode == 42
    assert got.stdout == ("stopped  it is past 2000-01-01T00:00:00Z\n"
                          "0 asked, 0 skipped, 2 not reached\n")  # fmt: skip
    assert server.sent == []
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        q,
        "--until",
        "2999-01-01T00:00:00Z",
    )
    assert got.returncode == 0 and got.stdout.endswith(
        "2 asked, 0 skipped, 0 not reached\n"
    )


def test_a_question_without_a_suggestion_and_no_server(box, server, tmp_path):
    got = run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--questions",
        questions(tmp_path, "how tall is the moon"),
    )
    assert got.returncode == 42
    assert (
        "         nothing in your folder holds that; no model was asked" in got.stdout
    )
    closed = "http://127.0.0.1:9/v1"
    got = run(
        "run", "--box", box, "--url", closed, "--questions", questions(tmp_path, Q1, Q2)
    )
    assert got.returncode == 42
    assert got.stdout == (f"no local model server is running (looked at {closed})\n"
                          "0 asked, 0 skipped, 2 not reached\n")  # fmt: skip


def test_the_model_named_is_asked(box, server, tmp_path):
    run(
        "run",
        "--box",
        box,
        "--url",
        server.url,
        "--model",
        "qwen3:8b",
        "--questions",
        questions(tmp_path, Q1),
    )
    assert server.sent[0]["model"] == "qwen3:8b"


def test_a_bad_command_line_is_refused(box, tmp_path):
    q = questions(tmp_path, Q1)
    base = ["run", "--box", box, "--questions", q]
    for argv in ([], base[1:], base + ["stray"], base[:3], base + ["--url", ""],
                 base + ["--model", "a", "--model", "b"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "night_batch.py" in got.stderr, argv
    got = run(*base, "--until", "7am")
    assert got.returncode == 2 and "--until is a time" in got.stderr
    got = run(*base, "--url", "http://example.org/v1")
    assert got.returncode == 2 and "not on this machine" in got.stderr
    got = run("run", "--box", tmp_path, "--questions", q)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run("run", "--box", box, "--questions", tmp_path / "missing.txt")
    assert got.returncode == 2 and "can't read the questions" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 99}\n')
    got = run(*base)
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_refused_suggestion_on_the_record_leaves_its_question_waiting(
    box, server, tmp_path
):
    served = json.loads(k("bite", "--box", box, Q1).stdout)["served"]
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps({"path": "a.md", "data": "x", "cites": ["nope"], "claim": "c"})
        + "\n"
    )
    assert "refused" in k("propose", "--box", box, "--file", bad).stdout and served
    got = run(
        "run", "--box", box, "--url", server.url, "--questions", questions(tmp_path, Q1)
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.startswith(f"asked    {Q1}\n")
