"""model-drift: answers frozen, asked again, and a change flagged only when
the model's name, its card and the passages served all held still."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "model_drift.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
Q1, Q2 = "what goes in biscochitos", "when does the gate stick"


class Model:
    """A stand-in endpoint on 127.0.0.1: answers by question, keeps what it was sent."""

    def __init__(self):
        self.say, self.sent = {}, []
        model = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(n))
                model.sent.append(body)
                user = body["messages"][1]["content"]
                said = next((a for q, a in model.say.items() if user.endswith(q)), "?")
                out = json.dumps({"choices": [{"message": {"content": said}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def model():
    m = Model()
    m.say = {Q1: "Lard, not butter [1].", Q2: "It sticks in winter [1]."}
    yield m
    m.server.shutdown()


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and anise seed.\n"
    )
    (pile / "gate.txt").write_text("The gate by the acequia sticks in winter.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(b),
                    "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def frozen(box, model, tmp_path, *extra, qs=(Q1, Q2)) -> Path:
    q = tmp_path / "questions.txt"
    q.write_text("\n".join(qs) + "\n")
    got = run(
        "freeze",
        "--box",
        box,
        "--url",
        model.url,
        "--model",
        "gemma",
        "--questions",
        q,
        *extra,
    )
    assert got.returncode == 0, got.stderr
    f = tmp_path / "frozen.json"
    f.write_text(got.stdout)
    return f


def test_freeze_prints_what_was_asked_and_said_and_writes_nothing(box, model, tmp_path):
    before = (box / "record.jsonl").read_bytes()
    q = tmp_path / "questions.txt"
    q.write_text(f"{Q1}\n{Q1}\nhow tall is the moon\n")
    got = run(
        "freeze", "--box", box, "--url", model.url, "--model", "gemma", "--questions", q
    )
    assert got.returncode == 0
    doc = json.loads(got.stdout)
    assert (doc["format"], doc["model"], doc["card"]) == (
        "willow model-drift 1",
        "gemma",
        None,
    )
    assert [(a["question"], a["answer"]) for a in doc["asked"]] == [
        (Q1, "Lard, not butter [1].")
    ]
    assert len(doc["asked"][0]["served"]) == 1
    assert (
        got.stderr
        == "not asked  how tall is the moon: nothing in your folder holds that\n"
    )
    assert len(model.sent) == 1 and model.sent[0]["temperature"] == 0
    assert (box / "record.jsonl").read_bytes() == before
    again = run(
        "freeze", "--box", box, "--url", model.url, "--model", "gemma", "--questions", q
    )
    assert again.stdout == got.stdout, "the same answers, the same bytes"


def test_the_same_answers_again_are_the_same(box, model, tmp_path):
    f = frozen(box, model, tmp_path)
    model.say[Q1] = "Lard,  not butter [1].\n"  # only its spaces moved
    got = run("again", "--box", box, "--url", model.url, "--frozen", f)
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        f"same       {Q1}\nsame       {Q2}\n"
        "0 of 2 held drifted, with the name gemma the same, no card named\n"
    )
    assert model.sent[-1]["model"] == "gemma", "asked of the frozen model"


def test_a_changed_answer_with_the_same_name_and_card_drifted(box, model, tmp_path):
    card = tmp_path / "gemma.md"
    card.write_text("<!-- willow-model\nname: gemma\n-->\n")
    f = frozen(box, model, tmp_path, "--card", card)
    assert (
        json.loads(f.read_text())["card"]
        == hashlib.sha256(card.read_bytes()).hexdigest()
    )
    model.say[Q2] = "It sticks when it rains [1]."
    got = run("again", "--box", box, "--url", model.url, "--frozen", f, "--card", card)
    assert got.returncode == 42
    assert got.stdout == (
        f"same       {Q1}\n"
        f"drifted    {Q2}\n"
        "           then: It sticks in winter [1].\n"
        "           now:  It sticks when it rains [1].\n"
        "1 of 2 held drifted, with the name gemma and its card the same\n"
    )


def test_a_new_card_says_a_new_model_and_nothing_is_flagged(box, model, tmp_path):
    card = tmp_path / "gemma.md"
    card.write_text("<!-- willow-model\nname: gemma\n-->\n")
    f = frozen(box, model, tmp_path, "--card", card)
    old = hashlib.sha256(card.read_bytes()).hexdigest()
    model.say[Q2] = "It sticks when it rains [1]."
    card.write_text("<!-- willow-model\nname: gemma\nsha256: " + "a" * 64 + "\n-->\n")
    new = hashlib.sha256(card.read_bytes()).hexdigest()
    got = run("again", "--box", box, "--url", model.url, "--frozen", f, "--card", card)
    assert got.returncode == 0
    assert got.stdout.endswith(
        f"1 of 2 held changed, but nothing is flagged: frozen with card {old}, asked with card {new}\n")  # fmt: skip
    got = run("again", "--box", box, "--url", model.url, "--frozen", f)
    assert got.returncode == 0 and got.stdout.endswith(
        f"frozen with card {old}, asked with no card\n"
    )
    plain = frozen(box, model, tmp_path)
    model.say[Q2] = "Never [1]."
    got = run(
        "again", "--box", box, "--url", model.url, "--frozen", plain, "--card", card
    )
    assert got.stdout.endswith(f"frozen with no card, asked with card {new}\n")


def test_a_folder_that_moved_under_a_question_holds_nothing(box, model, tmp_path):
    f = frozen(box, model, tmp_path)
    pile = Path(json.loads((box / "kernel.json").read_text())["pile"])
    (pile / "gate.txt").write_text(
        "The gate by the acequia sticks in winter and in rain.\n"
    )
    model.say[Q2] = "Something else [1]."
    got = run("again", "--box", box, "--url", model.url, "--frozen", f)
    assert got.returncode == 0
    assert got.stdout == (
        f"same       {Q1}\n"
        f"not held   {Q2}: your folder serves other passages now\n"
        "0 of 1 held drifted, with the name gemma the same, no card named\n"
    )
    (pile / "recipes.txt").write_text("Biscochitos want lard.\n")
    got = run("again", "--box", box, "--url", model.url, "--frozen", f)
    assert got.returncode == 42
    assert got.stdout.endswith(
        "nothing held: of 2 frozen, your folder serves other passages for each\n"
    )


def test_nothing_to_freeze_and_an_endpoint_that_doesnt_answer(box, model, tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("how tall is the moon\n")
    got = run(
        "freeze", "--box", box, "--url", model.url, "--model", "m", "--questions", q
    )
    assert got.returncode == 42 and got.stdout == "" and "nothing frozen" in got.stderr
    q.write_text(Q1 + "\n")
    got = run(
        "freeze",
        "--box",
        box,
        "--url",
        "http://127.0.0.1:9/v1",
        "--model",
        "m",
        "--questions",
        q,
    )
    assert got.returncode == 42 and got.stdout.startswith(
        "unreachable: http://127.0.0.1:9/v1 ("
    )
    f = frozen(box, model, tmp_path)
    got = run("again", "--box", box, "--url", "http://127.0.0.1:9/v1", "--frozen", f)
    assert got.returncode == 42 and got.stdout.startswith("unreachable: ")


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        '{"format": "other", "model": "m", "asked": []}',
        '{"format": "willow model-drift 1", "asked": []}',
        '{"format": "willow model-drift 1", "model": "m", "asked": {}}',
        '{"format": "willow model-drift 1", "model": "m", "asked": [{"question": "q", "answer": "a"}]}',
        '{"format": "willow model-drift 1", "model": "m", "asked": [{"question": 1, "answer": "a", "served": []}]}',
        '{"format": "willow model-drift 1", "model": "m", "asked": [{"question": "q", "answer": 2, "served": []}]}',
        '{"format": "willow model-drift 1", "model": "m", "asked": ["q"]}',
    ],
)
def test_a_frozen_file_that_isnt_one_is_refused(text, box, tmp_path):
    f = tmp_path / "frozen.json"
    f.write_text(text)
    got = run("again", "--box", box, "--url", "http://127.0.0.1:9/v1", "--frozen", f)
    assert got.returncode == 2 and "not a frozen file" in got.stderr


def test_a_box_with_a_words_list_that_doesnt_read_is_refused(tmp_path, model):
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
    model.say = {"in cookies": "Lard [1]."}
    f = frozen(b, model, tmp_path, qs=("what goes in cookies",))
    wl.write_text("cookies biscochitos\n")
    got = run("again", "--box", b, "--url", model.url, "--frozen", f)
    assert got.returncode == 2 and "words list line 1" in got.stderr


def test_a_bad_command_line_is_refused(box, tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("x\n")
    good = [
        "freeze",
        "--box",
        box,
        "--url",
        "http://127.0.0.1:9/v1",
        "--model",
        "m",
        "--questions",
        q,
    ]
    for argv in ([], ["check"], good + ["stray"], good[:-2], good + ["--box", box],
                 good + ["--frozen", q], ["again", "--box", box, "--url", "u"],
                 good[:-1] + [""]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "model_drift.py" in got.stderr, argv
    got = run(*good[:2], tmp_path, *good[3:])
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = run(*good[:-1], tmp_path / "missing.txt")
    assert got.returncode == 2 and "can't read the questions" in got.stderr
    got = run(*good, "--card", tmp_path / "missing.md")
    assert got.returncode == 2 and "can't read the card" in got.stderr
    with (box / "record.jsonl").open("a") as f:
        f.write('{"n": 99}\n')
    got = run(*good)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
