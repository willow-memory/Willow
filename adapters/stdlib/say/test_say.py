"""say: a model on this machine is asked for one sentence about the boxes,
and the sentence is held to them by say-check's four checks: one that
passes stands, one that fails is struck and code's line stands, and a model
that can't be asked is unreachable. Only a loopback address is ever asked,
and nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "say.py"
sys.path.insert(0, str(HERE))
import say as sy  # noqa: E402

B5 = {"id": "b5", "text": "needs you: Ratify the work order (local-flow-and-ui §7)"}
B4 = {"id": "b4", "text": "blocked: PR 712 waiting (broker verb · 126 tests pass)"}
BOXES = [B5, B4]
GOOD = "You need to ratify the work order [b5]. PR 712's still waiting, 126 tests pass [b4]."
BAD = GOOD.replace("126", "140")


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, argv)], capture_output=True, text=True
    )


@pytest.fixture
def boxes(tmp_path):
    f = tmp_path / "b.json"
    f.write_text(json.dumps(BOXES))
    return f


class Ollama:
    """A stand-in for Ollama on this machine: it answers /api/generate with
    the words it was told to, and keeps what it was asked."""

    def __init__(self, reply: object = GOOD, status: int = 200):
        self.asked: list[dict] = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                outer.asked.append(
                    {"path": self.path, **json.loads(self.rfile.read(n))}
                )
                body = json.dumps(
                    reply if isinstance(reply, dict) else {"response": reply}
                )
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body.encode())

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.host = f"127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def ollama():
    made = []

    def make(reply: object = GOOD, status: int = 200) -> Ollama:
        made.append(Ollama(reply, status))
        return made[-1]

    yield make
    for o in made:
        o.close()


def test_a_bad_command_line_is_refused_and_names_the_script(boxes):
    got = run()
    assert got.returncode == 2 and "say.py" in got.stderr
    for argv in (
        ["--you", "hello"],  # no boxes
        ["--boxes", boxes, "--model"],
        ["--boxes", boxes, "--host"],
        ["--boxes", boxes, "--earlier"],
        ["--boxes", boxes, "--timeout", "soon"],
        ["--boxes", boxes, "--timeout", "0"],
        ["--boxes", boxes, "--timeout", "inf"],
        ["--boxes", boxes, "--nope"],
        ["--boxes", boxes, "extra"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("usage: say.py"), argv
        assert got.stdout == ""


def test_boxes_that_cant_be_read_are_refused_before_any_model_is_asked(
    tmp_path, ollama
):
    o = ollama()
    f = tmp_path / "b.json"
    for text, why in (("nope", "could not be read"), ('{"a": 1}', "not a list"),
                      ("[]", "holds no box")):  # fmt: skip
        f.write_text(text)
        got = run("--boxes", f, "--host", o.host)
        assert got.returncode == 2 and why in got.stderr, text
    f.write_text(json.dumps(BOXES))
    e = tmp_path / "e.json"
    e.write_text("nope")
    assert run("--boxes", f, "--earlier", e, "--host", o.host).returncode == 2
    assert o.asked == []


def test_a_sentence_that_keeps_to_the_boxes_stands(boxes, ollama):
    o = ollama(GOOD)
    got = run("--boxes", boxes, "--you", "where are we", "--host", o.host, "--model", "tiny:1b")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "say: populated, the sentence stands, said by tiny:1b",
        "  said                       " + GOOD,
        "  every cite was served      held",
        "  every box cited            held",
        "  nothing the boxes lack     held",
        "  your words quoted exactly  nothing quoted",
    ]
    doc = json.loads(run("--boxes", boxes, "--host", o.host, "--json").stdout)
    assert doc["addon"] == "say" and doc["state"] == "populated"
    assert doc["groups"][0]["rows"][0] == {"where": "said", "what": GOOD}


def test_a_sentence_that_adds_a_number_is_struck_and_says_which(boxes, ollama):
    o = ollama(BAD)
    got = run("--boxes", boxes, "--host", o.host)
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "say: populated, struck: 1 of 4 checks failed; code's own line stands",
        "  struck                  " + BAD,
        "  nothing the boxes lack  failed: 140 is no box's",
    ]


def test_what_the_model_is_asked_is_the_rules_your_line_and_the_tagged_boxes(
    boxes, ollama
):
    o = ollama(GOOD)
    run(
        "--boxes",
        boxes,
        "--you",
        "where  are\nwe",
        "--host",
        o.host,
        "--model",
        "tiny:1b",
    )
    (asked,) = o.asked
    assert asked["path"] == "/api/generate" and asked["model"] == "tiny:1b"
    assert asked["stream"] is False and asked["think"] is False
    assert asked["options"] == {"temperature": 0}
    lines = asked["prompt"].splitlines()
    assert lines[0] == sy.VOICE
    assert "Say ONE short sentence about the boxes below, and nothing else." in lines
    assert "Use only their facts: add no number, name or status they lack." in lines
    assert any(
        ln.startswith("Free words, and only these: morning, oh, and,") for ln in lines
    )
    assert lines[-4:] == [
        "The human asked: where are we",
        "Boxes:",
        "[b5] needs you: Ratify the work order (local-flow-and-ui §7)",
        "[b4] blocked: PR 712 waiting (broker verb · 126 tests pass)",
    ]
    assert "Earlier in this conversation" not in asked["prompt"]
    assert "/no_think" not in asked["prompt"]


def test_earlier_boxes_are_given_for_context_and_may_be_cited(tmp_path, boxes, ollama):
    e = tmp_path / "e.json"
    e.write_text(json.dumps([{"id": "b1", "text": "decided: phone only proposes"}]))
    s = "The work order [b5] is waiting [b4], and the phone only proposes [b1]."
    o = ollama(s)
    assert run("--boxes", boxes, "--host", o.host).returncode == 42
    assert run("--boxes", boxes, "--earlier", e, "--host", o.host).returncode == 0
    prompt = o.asked[-1]["prompt"].splitlines()
    at = prompt.index("[b1] decided: phone only proposes")
    assert prompt[at - 1].startswith("Earlier in this conversation, for context only")
    assert at < prompt.index("Boxes:")


def test_qwen3_is_told_not_to_think_aloud_and_its_thinking_is_dropped(boxes, ollama):
    o = ollama("<think>the boxes say 140, surely</think>\n" + GOOD)
    got = run("--boxes", boxes, "--host", o.host, "--model", "qwen3:4b")
    assert got.returncode == 0 and "140" not in got.stdout
    assert o.asked[0]["prompt"].endswith(" /no_think")


def test_a_model_that_cant_be_asked_is_unreachable_and_says_why(boxes, ollama):
    got = run("--boxes", boxes, "--host", "127.0.0.1:9")  # nothing listens there
    assert got.returncode == 42
    assert got.stdout.startswith("say: unreachable, qwen3:4b at http://127.0.0.1:9: ")
    assert len(got.stdout.splitlines()) == 1
    doc = json.loads(run("--boxes", boxes, "--host", "127.0.0.1:9", "--json").stdout)
    assert doc["state"] == "unreachable" and doc["groups"] == []
    for o, why in (
        (ollama(GOOD, 404), "that model isn't installed"),
        (ollama(GOOD, 500), "HTTP 500"),
        (ollama({"nope": 1}), "it sent no sentence"),
        (ollama("   "), "said nothing"),
        (ollama("<think>hm</think>"), "said nothing"),
    ):
        got = run("--boxes", boxes, "--host", o.host)
        assert got.returncode == 42 and "say: unreachable, " in got.stdout, why
        assert why in got.stdout, got.stdout


def test_only_this_machine_is_ever_asked(boxes):
    for host in ("example.com", "example.com:11434", "http://10.0.0.5:11434",
                 "https://127.0.0.1:11434", "127.0.0.1.example.com"):  # fmt: skip
        got = run("--boxes", boxes, "--host", host)
        assert got.returncode == 42, host
        assert "is not this machine; not asked" in got.stdout, host
    with pytest.raises(sy.SayUnreachable):
        sy.ollama_base("http://[::1")
    assert sy.ollama_base("localhost") == "http://localhost:11434"
    assert sy.ollama_base("127.0.0.1:8080") == "http://127.0.0.1:8080"
    assert sy.ollama_base("[::1]:11434") == "http://[::1]:11434"


def test_the_host_can_come_from_ollamas_own_setting(boxes, ollama, monkeypatch):
    o = ollama(GOOD)
    monkeypatch.setenv("OLLAMA_HOST", o.host)
    assert sy.ollama_base() == f"http://{o.host}"
    monkeypatch.setenv("OLLAMA_HOST", "example.com")
    with pytest.raises(sy.SayUnreachable):
        sy.ollama_base()


def test_said_takes_any_say_and_reports_what_came():
    got = sy.said(
        BOXES, "where are we", say=lambda prompt: "  " + GOOD + "\n", model="m"
    )
    assert got == {"state": "populated", "sentence": GOOD, "stands": True, "model": "m",
                   "checks": got["checks"]}  # fmt: skip
    assert [ok for _, ok, _ in got["checks"]] == [True, True, True, None]
    struck = sy.said(BOXES, say=lambda prompt: BAD)
    assert struck["stands"] is False and struck["sentence"] == BAD

    def down(prompt):
        raise sy.SayUnreachable("it is down")

    assert sy.said(BOXES, say=down, model="m") == {
        "state": "unreachable", "why": "it is down", "model": "m"}  # fmt: skip


def test_your_words_may_be_quoted_exactly_and_no_other_way(boxes, ollama):
    you = "is it bad that it is still waiting"
    ok = 'The work order [b5], PR 712 still waiting [b4]: "is it bad".'
    assert (
        run("--boxes", boxes, "--you", you, "--host", ollama(ok).host).returncode == 0
    )
    no = 'The work order [b5], PR 712 still waiting [b4]: "it is terrible".'
    got = run("--boxes", boxes, "--you", you, "--host", ollama(no).host)
    assert got.returncode == 42 and 'not your words: "it is terrible"' in got.stdout


def test_nothing_is_written(tmp_path, boxes, ollama):
    o = ollama(BAD)
    before = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    run("--boxes", boxes, "--you", "where are we", "--host", o.host)
    run("--boxes", boxes, "--host", "127.0.0.1:9")
    assert {
        p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()
    } == before


def test_a_timeout_of_a_second_or_less_is_taken(boxes):
    # nothing listens on port 9: taken, the model is tried and can't be asked; refused would be 2
    for seconds in ("0.5", "1", "0.01"):
        got = run("--boxes", boxes, "--host", "127.0.0.1:9", "--timeout", seconds)
        assert got.returncode == 42 and got.stdout.startswith("say: unreachable"), (
            seconds
        )
