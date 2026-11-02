"""same-way: each question asked several times of a model on this machine,
and a flip in the words or the cites counted; nothing goes on the record."""

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
SCRIPT = HERE / "same_way.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]


class Model:
    """A stand-in endpoint on 127.0.0.1 saying `replies` in turn."""

    def __init__(self):
        self.replies, self.sent = [""], []
        model = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers["Content-Length"])
                model.sent.append(json.loads(self.rfile.read(n)))
                said = model.replies[(len(model.sent) - 1) % len(model.replies)]
                body = json.dumps(
                    {"choices": [{"message": {"content": said}}]}
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


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "The gate by the acequia sticks in winter.\n"
    )
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(b),
                    "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def questions(tmp_path: Path, *qs: str) -> Path:
    p = tmp_path / "questions.txt"
    p.write_text("\n".join(qs) + "\n", encoding="utf-8")
    return p


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def test_a_model_that_says_the_same_thing_each_time(box, model, tmp_path):
    model.replies = ["Lard, not butter [1]."]
    before = (box / "record.jsonl").read_bytes()
    q = questions(tmp_path, "what goes in biscochitos", "", "what goes in biscochitos")
    got = run("--box", box, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "same     3 of 3  what goes in biscochitos  (cites [1])\n"
        "1 asked, 1 the same every time, 0 flipped (0%)\n"
    )
    assert len(model.sent) == 3, "a question asked twice in the file is asked once"
    body = model.sent[0]
    assert (body["model"], body["temperature"], body["seed"]) == ("m", 0, 0)
    assert "anise seed" in body["messages"][1]["content"]
    assert "acequia" not in body["messages"][1]["content"], "only what was served"
    assert (box / "record.jsonl").read_bytes() == before, "nothing on the record"


def test_spaces_dont_flip_but_words_and_cites_do(box, model, tmp_path):
    q = questions(tmp_path, "what goes in biscochitos")
    model.replies = ["Lard [1].", "Lard  [1].\n"]
    got = run("--box", box, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 0 and got.stdout.startswith("same     3 of 3")
    model.replies, model.sent = ["Lard [1].", "Butter [1]."], []
    got = run(
        "--box",
        box,
        "--url",
        model.url,
        "--model",
        "m",
        "--questions",
        q,
        "--times",
        "4",
    )
    assert got.returncode == 42
    assert got.stdout == (
        "flipped  2 ways in 4  what goes in biscochitos  (cites [1])\n"
        "1 asked, 0 the same every time, 1 flipped (100%)\n"
    )
    assert len(model.sent) == 4


def test_a_flip_in_what_is_cited_is_a_flip(tmp_path, model):
    pile = tmp_path / "pile2"
    pile.mkdir()
    (pile / "a.txt").write_text(
        "The gate sticks in winter.\n\nThe gate was painted green.\n"
    )
    b = tmp_path / "box2"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(b), "--pile",
                    str(pile), "--key", str(tmp_path / "k2"), *NOW], check=True, capture_output=True)  # fmt: skip
    model.replies = ["The gate [1].", "The gate [2].", "The gate [1, 2]."]
    q = questions(tmp_path, "the gate", "how tall is the moon")
    got = run("--box", b, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 42
    assert got.stdout == (
        "flipped  3 ways in 3  the gate  (cites [1] / [2] / [1, 2])\n"
        "not asked  how tall is the moon: nothing in your folder holds that\n"
        "1 asked, 0 the same every time, 1 flipped (100%)\n"
    )


def test_questions_the_folder_doesnt_hold_ask_nothing(box, model, tmp_path):
    q = questions(tmp_path, "how tall is the moon")
    got = run("--box", box, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 42
    assert got.stdout.endswith("0 asked of 1 questions\n")
    assert model.sent == []
    q = questions(tmp_path, "The gate by the acequia sticks in winter.")
    got = run("--box", box, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 42 and model.sent == []
    assert got.stdout.startswith("not asked  The gate by the acequia sticks in winter.: "
                                 "your folder holds only the question itself\n")  # fmt: skip


def test_an_endpoint_that_doesnt_answer_says_so(box, tmp_path):
    q = questions(tmp_path, "what goes in biscochitos")
    got = run(
        "--box", box, "--url", "http://127.0.0.1:9/v1", "--model", "m", "--questions", q
    )
    assert got.returncode == 42
    assert got.stdout.startswith("unreachable: http://127.0.0.1:9/v1 (")
    assert got.stdout.endswith(", at what goes in biscochitos\n")


@pytest.mark.parametrize(
    "url", ["http://example.org/v1", "http://10.0.0.2:8080/v1", "nonsense"]
)
def test_a_url_off_this_machine_is_refused(url, box, tmp_path):
    got = run(
        "--box",
        box,
        "--url",
        url,
        "--model",
        "m",
        "--questions",
        questions(tmp_path, "x"),
    )
    assert got.returncode == 2 and "not on this machine" in got.stderr


def test_this_machine_by_any_of_its_names(box, tmp_path):
    q = questions(tmp_path, "how tall is the moon")
    for url in ("http://localhost:9/v1", "http://[::1]:9/v1", "http://127.0.0.2:9/v1"):
        got = run("--box", box, "--url", url, "--model", "m", "--questions", q)
        assert got.returncode == 42, (url, got.stderr)


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
    for argv in ([], base + ["stray"], base + ["--times", "1"], base + ["--times", "x"],
                 base[:-2], base + ["--box", box]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "same_way.py" in got.stderr, argv
    got = run(*base[:1], tmp_path, *base[2:])
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(*base[:-1], tmp_path / "missing.txt")
    assert got.returncode == 2 and "can't read the questions" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 9}\n')
    got = run(*base)
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_box_with_a_words_list_is_ranked_with_it(tmp_path, model):
    pile = tmp_path / "pile3"
    pile.mkdir()
    (pile / "recipes.txt").write_text("Biscochitos: lard, not butter.\n")
    wl = tmp_path / "words.txt"
    wl.write_text("cookies = biscochitos\n")
    wl.chmod(0o600)
    b = tmp_path / "box3"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(b), "--pile",
                    str(pile), "--key", str(tmp_path / "k3"), "--words", str(wl), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    model.replies = ["Lard [1]."]
    q = questions(tmp_path, "what goes in cookies")
    got = run("--box", b, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("same     3 of 3  what goes in cookies  (cites [1])\n")
    wl.write_text("cookies biscochitos\n")
    got = run("--box", b, "--url", model.url, "--model", "m", "--questions", q)
    assert got.returncode == 2 and "words list line 1" in got.stderr
