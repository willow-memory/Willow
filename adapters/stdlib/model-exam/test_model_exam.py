"""model-exam: a model marked against the answers you sealed: it must cite
what you cited and say what you said; nothing goes on the record."""

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
SCRIPT = HERE / "model_exam.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]


class Model:
    """A stand-in endpoint on 127.0.0.1: says `reply`, keeps what it was sent."""

    def __init__(self):
        self.reply, self.sent = "", []
        model = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers["Content-Length"])
                model.sent.append(json.loads(self.rfile.read(n)))
                body = json.dumps(
                    {"choices": [{"message": {"content": model.reply}}]}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def model():
    m = Model()
    yield m
    m.server.shutdown()


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv), *NOW],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def seal(box: Path, tmp_path: Path, question: str, answer: str, cite: int = 0) -> None:
    """What a person does: bite, take a suggestion, seal it."""
    served = json.loads(k("bite", "--box", box, question).stdout)["served"]
    f = tmp_path / "s.jsonl"
    row = {
        "path": "answers/a.md",
        "data": answer,
        "cites": [served[cite]["id"]],
        "claim": "mine",
    }
    f.write_text(json.dumps(row) + "\n")
    subj = re.search(
        r"proposal:[0-9a-f]{64}", k("propose", "--box", box, "--file", f).stdout
    )
    assert k("seal", "--box", box, subj.group(0)).returncode == 0


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "Biscochitos are cut with a star and dusted in cinnamon sugar.\n\n"
        "The gate by the acequia sticks in winter.\n"
    )
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    seal(
        b,
        tmp_path,
        "what goes in biscochitos",
        "Lard, not butter, and anise seed [1].\n",
    )
    return b


def questions(tmp_path: Path, *qs: str) -> Path:
    p = tmp_path / "exam.txt"
    p.write_text("\n".join(qs) + "\n", encoding="utf-8")
    return p


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def exam(box, model, tmp_path, *qs) -> subprocess.CompletedProcess:
    return run(
        "--box",
        box,
        "--url",
        model.url,
        "--model",
        "m",
        "--questions",
        questions(tmp_path, *qs),
    )


def test_a_reply_that_cites_and_says_what_you_sealed_passes(box, model, tmp_path):
    model.reply = "They take lard rather than butter, plus anise seed [1]."
    before = (box / "record.jsonl").read_bytes()
    got = exam(box, model, tmp_path, "what goes in biscochitos", "how tall is the moon")
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "pass      what goes in biscochitos  (cites [1] as you did; 4 of 4 words)\n"
        "unmarked  how tall is the moon: no answer you sealed\n"
        "scored 1 of 1 marked (100%); 1 unmarked\n"
    )
    assert len(model.sent) == 1, "an unmarked question is never asked"
    assert (box / "record.jsonl").read_bytes() == before


def test_a_reply_citing_another_passage_fails(box, model, tmp_path):
    model.reply = "Lard, not butter, and anise seed [2]."
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42
    assert got.stdout == (
        "fail      what goes in biscochitos  (cites [2], you cited [1]; 4 of 4 words)\n"
        "scored 0 of 1 marked (0%); 0 unmarked\n"
    )


def test_a_reply_that_cites_right_but_says_something_else_fails(box, model, tmp_path):
    model.reply = "Cinnamon sugar and a star cutter [1]."
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42
    assert (
        "fail      what goes in biscochitos  (cites [1] as you did; 0 of 4 words)\n"
        in got.stdout
    )


def test_half_the_shorter_texts_words_is_enough_and_less_is_not(box, model, tmp_path):
    model.reply = "Lard and anise [1]."  # 2 of its own 2, the shorter
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 0 and "; 2 of 2 words)" in got.stdout
    model.reply = "Lard, sugar, flour, eggs [1]."  # 1 of the answer's 4
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42 and "; 1 of 4 words)" in got.stdout
    model.reply = "Lard, sugar, anise, eggs [1]."  # 2 of 4: half holds
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 0 and "; 2 of 4 words)" in got.stdout
    model.reply = "[1]"
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42 and "; 0 of 0 words)" in got.stdout


def test_an_answer_whose_passage_is_gone_is_said(box, model, tmp_path):
    pile = Path(json.loads((box / "kernel.json").read_text())["pile"])
    (pile / "recipes.txt").write_text("The gate by the acequia sticks in winter.\n")
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42
    assert got.stdout.startswith(
        "unmarked  what goes in biscochitos: your folder serves nothing for it now\n"
    )
    assert got.stdout.endswith(
        "nothing marked: 1 of 1 questions have no sealed answer to mark against\n"
    )
    (pile / "recipes.txt").write_text("Biscochitos want lard.\n")
    model.reply = "Lard [1]."
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert "you cited [not served now]" in got.stdout


def test_a_sealed_answer_whose_file_changed_marks_nothing(box, model, tmp_path):
    for p in (box / "proposals").glob("*.json"):
        p.write_text(p.read_text().replace("anise", "fennel"))
    got = exam(box, model, tmp_path, "what goes in biscochitos")
    assert got.returncode == 42 and got.stdout.startswith(
        "unmarked  what goes in biscochitos: no answer you sealed"
    )


def test_an_endpoint_that_doesnt_answer_says_so(box, tmp_path):
    got = run("--box", box, "--url", "http://127.0.0.1:9/v1", "--model", "m",
              "--questions", questions(tmp_path, "what goes in biscochitos"))  # fmt: skip
    assert got.returncode == 42 and got.stdout.startswith(
        "unreachable: http://127.0.0.1:9/v1 ("
    )


def test_a_box_with_a_words_list_is_ranked_with_it(tmp_path, model):
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
    model.reply = "Lard [1]."
    got = exam(b, model, tmp_path, "what goes in cookies")
    assert got.returncode == 0, got.stdout + got.stderr
    wl.write_text("cookies biscochitos\n")
    got = exam(b, model, tmp_path, "what goes in cookies")
    assert got.returncode == 2 and "words list line 1" in got.stderr


def test_a_bad_command_line_is_refused(box, tmp_path):
    q = questions(tmp_path, "x")
    base = [
        "--box",
        box,
        "--url",
        "http://127.0.0.1:9/v1",
        "--model",
        "m",
        "--questions",
        q,
    ]
    for argv in (
        [],
        base + ["stray"],
        base[:-2],
        base + ["--box", box],
        base[:2] + base[4:],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "model_exam.py" in got.stderr, argv
    got = run(*base[:1], tmp_path, *base[2:])
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(*base[:-1], tmp_path / "missing.txt")
    assert got.returncode == 2 and "can't read the questions" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 99}\n')
    got = run(*base)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
