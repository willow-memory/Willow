"""openai-compatible: the kernel bites first, the model sees only what was
served, a reply is proposed citing what its brackets name, and nothing is
asked, or proposed, without a passage under it."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("oc", HERE / "openai_compatible.py")
oc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oc)
NOW = ["--now", "2026-10-31T00:00:00Z"]


class Model:
    """A stand-in endpoint on 127.0.0.1: keeps what it was sent, says `reply`."""

    def __init__(self):
        self.reply, self.sent, self.headers = "", [], []
        model = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers["Content-Length"])
                model.sent.append((self.path, json.loads(self.rfile.read(n))))
                model.headers.append(dict(self.headers))
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


def run(*argv: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "openai_compatible.py"), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


def ask(box, model, question, *more):
    return run("ask", "--box", str(box), "--url", model.url, "--model", "gemma",
               *NOW, *more, question)  # fmt: skip


def rows(box) -> list[dict]:
    return [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]


def test_a_cited_reply_is_proposed_and_waits_for_a_seal(box, model):
    model.reply = "Lard, not butter, and anise seed [1]."
    got = ask(box, model, "what goes in biscochitos")
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == "Lard, not butter, and anise seed [1]."
    assert got.stdout.splitlines()[1].startswith("pass  proposal:")
    assert "waiting on your seal" in got.stdout
    kinds = [r["kind"] for r in rows(box)]
    assert kinds[-2:] == ["bite", "proposal"] and "seal" not in kinds
    served = rows(box)[-2]["served"]
    (prop,) = (box / "proposals").glob("*.json")
    kept = json.loads(prop.read_text())
    assert kept["cites"] == [served[0]["id"]]
    assert kept["data"] == "Lard, not butter, and anise seed [1].\n"
    assert kept["path"] == "answers/what-goes-in-biscochitos.md"
    assert kept["claim"] == (
        f"gemma at {model.url} (temperature 0, seed 0) answered from 1 of the 1"
        " passages served"
    )


def test_the_model_is_sent_only_the_rule_the_passages_and_the_question(box, model):
    model.reply = "[1]"
    ask(box, model, "what goes in biscochitos")
    ((path, body),) = model.sent
    assert path == "/v1/chat/completions"
    assert body["model"] == "gemma"
    assert body["temperature"] == 0 and body["seed"] == 0
    system, user = body["messages"]
    assert system == {"role": "system", "content": oc.RULE}
    assert user["role"] == "user"
    assert user["content"] == (
        "Passages:\n\n[1] (recipes.txt:1)\n"
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "Question: what goes in biscochitos"
    )
    assert "acequia" not in json.dumps(body), "a passage not served is not sent"
    assert "Authorization" not in model.headers[0]


def test_a_voice_comes_before_the_rule_never_instead_of_it(box, model, tmp_path):
    voice = tmp_path / "voice.txt"
    voice.write_text("  You are Abuela Eufemia, speaking softly.\n")
    model.reply = "[1]"
    assert ask(box, model, "biscochitos", "--system", str(voice)).returncode == 0
    system = model.sent[0][1]["messages"][0]["content"]
    assert system == "You are Abuela Eufemia, speaking softly.\n\n" + oc.RULE
    got = ask(box, model, "biscochitos", "--system", str(tmp_path / "gone"))
    assert got.returncode == 2 and got.stderr.startswith("refused")
    assert oc.messages("q", [], "  \n")[0]["content"] == oc.RULE
    (prop,) = (box / "proposals").glob("*.json")
    said = oc.read_claim(json.loads(prop.read_text())["claim"])["settings"]
    assert said["system"] == "sha256 " + oc.kernel.h256(voice.read_text())


def test_nothing_served_means_no_model_is_asked(box, model):
    got = ask(box, model, "who won the world series")
    assert got.returncode == 42
    assert got.stdout == "nothing in your folder holds that; no model was asked\n"
    assert model.sent == []
    assert rows(box)[-1]["kind"] == "bite", "the question is still on the record"


def test_a_reply_citing_nothing_is_proposed_to_no_one(box, model):
    model.reply = "Probably butter. [7]"
    got = ask(box, model, "biscochitos")
    assert got.returncode == 42
    assert got.stdout == "Probably butter. [7]\ncited no passage; proposed to no one\n"
    assert rows(box)[-1]["kind"] == "bite"
    assert not (box / "proposals").exists()


def test_an_endpoint_that_is_not_there_is_42_not_a_crash(box, tmp_path):
    got = run("ask", "--box", str(box), "--url", "http://127.0.0.1:9/v1",
              "--model", "m", *NOW, "biscochitos")  # fmt: skip
    assert got.returncode == 42
    assert got.stdout == "unreachable: http://127.0.0.1:9/v1 (URLError)\n"


def test_a_key_goes_as_a_bearer_only_when_set(box, model):
    import os

    model.reply = "[1]"
    env = {**os.environ, "OPENAI_API_KEY": "sk-local"}
    run("ask", "--box", str(box), "--url", model.url + "/", "--model", "g", *NOW,
        "biscochitos", env=env)  # fmt: skip
    assert model.headers[0]["Authorization"] == "Bearer sk-local"
    assert model.sent[0][0] == "/v1/chat/completions", "a trailing slash is one"


def test_a_sealed_answer_is_given_back_without_asking(box, model, tmp_path):
    model.reply = "Lard [1]."
    ask(box, model, "biscochitos")
    (prop,) = (box / "proposals").glob("*.json")
    k = [sys.executable, str(ROOT / "kernel.py")]
    subprocess.run([*k, "seal", "--box", str(box), "--key", str(tmp_path / "key"),
                    *NOW, f"proposal:{prop.stem}"], check=True, capture_output=True)  # fmt: skip
    got = ask(box, model, "biscochitos")
    assert got.returncode == 0 and got.stdout == "sealed already: Lard [1].\n"
    assert len(model.sent) == 1


def test_cited_reads_brackets_in_order_once_and_only_real_numbers():
    served = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert oc.cited("x [2] y [1, 3] z [2] [0] [4] [x]", served) == ["b", "a", "c"]
    assert oc.cited("[3,1]", served) == ["c", "a"]
    assert oc.cited("no brackets", served) == []


def test_the_slug_is_plain_and_short():
    assert oc.slug("What goes in Biscochitos?") == "what-goes-in-biscochitos"
    assert oc.slug("¿?") == "answer"
    assert len(oc.slug("word " * 40)) <= 60
    assert not oc.slug("a" * 59 + " b").endswith("-")


def test_a_bad_command_line_is_refused_with_usage(box, model):
    base = ["--box", str(box), "--url", model.url, "--model", "m"]
    for argv in (
        [],
        ["bite", *base, "q"],
        ["ask", *base],
        ["ask", *base, "q", "r"],
        ["ask", *base, "--box", str(box), "q"],
        ["ask", "--box", str(box), "--url", model.url, "q"],
        ["ask", *base, "--model"],
        ["ask", *base, "   "],
        ["ask", *base, "--stray"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "openai_compatible.py" in got.stderr, argv
    assert model.sent == []


def test_a_refused_bite_is_the_kernels_word(tmp_path, model):
    got = run("ask", "--box", str(tmp_path / "nobox"), "--url", model.url,
              "--model", "m", "biscochitos")  # fmt: skip
    assert got.returncode != 0 and model.sent == []


def test_it_waits_fifteen_minutes_for_a_slow_model(monkeypatch):
    """The card's promise: a model on a laptop's CPU is given 900 seconds."""
    seen = {}

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "ok"}}]}'

    def urlopen(req, timeout):
        seen["timeout"] = timeout
        return Reply()

    monkeypatch.setattr(oc.urllib.request, "urlopen", urlopen)
    assert oc.ask_model("http://127.0.0.1:9/v1", "m", []) == "ok"
    assert seen == {"timeout": 900}


def test_without_reasoning_the_request_is_the_one_it_always_was(box, model):
    model.reply = "[1]"
    assert ask(box, model, "biscochitos").returncode == 0
    body = model.sent[0][1]
    assert list(body) == ["model", "messages", "temperature", "seed"]
    assert "reasoning" not in json.dumps(body)


@pytest.mark.parametrize("effort", ["none", "low", "medium", "high"])
def test_reasoning_goes_as_the_requests_reasoning_effort(box, model, effort):
    model.reply = "[1]"
    got = ask(box, model, "biscochitos", "--reasoning", effort)
    assert got.returncode == 0, got.stderr
    body = model.sent[0][1]
    assert body["reasoning_effort"] == effort
    assert list(body) == ["model", "messages", "temperature", "seed",
                          "reasoning_effort"]  # fmt: skip
    assert body["messages"][0] == {"role": "system", "content": oc.RULE}
    (prop,) = (box / "proposals").glob("*.json")
    said = oc.read_claim(json.loads(prop.read_text())["claim"])
    assert said["settings"] == {"temperature": "0", "seed": "0", "reasoning": effort}


def test_a_reasoning_effort_not_on_the_list_is_refused(box, model):
    for more in (["--reasoning", "think"], ["--reasoning", "NONE"],
                 ["--reasoning", ""], ["--reasoning", "low", "--reasoning", "low"]):  # fmt: skip
        got = ask(box, model, "biscochitos", *more)
        assert got.returncode == 2 and "openai_compatible.py" in got.stderr, more
    got = run("ask", "--box", str(box), "--url", model.url, "--model", "m",
              "biscochitos", "--reasoning")  # fmt: skip
    assert got.returncode == 2
    assert model.sent == []
    assert [r["kind"] for r in rows(box)] == ["boot"], "refused before the bite"


def test_a_claim_says_who_where_at_what_and_what_it_did():
    made = oc.claim("gemma", "at http://127.0.0.1:1/v1", oc.settings(0, "low", "Be brief."),
                    "answered from 1 of the 2 passages served")  # fmt: skip
    assert made == (
        "gemma at http://127.0.0.1:1/v1 (temperature 0, seed 0, reasoning low,"
        f" system sha256 {oc.kernel.h256('Be brief.')}) answered from 1 of the 2"
        " passages served"
    )
    got = oc.read_claim(made)
    assert (got["who"], got["url"], got["did"]) == (
        "gemma", "http://127.0.0.1:1/v1", "answered from 1 of the 2 passages served")  # fmt: skip
    assert list(got["settings"]) == ["temperature", "seed", "reasoning", "system"]
    assert oc.settings(7) == [("temperature", "0"), ("seed", "7")]
    assert oc.settings(0, "", "  \n") == oc.settings(0)


def test_a_claim_from_before_the_settings_were_said_still_reads():
    old = oc.read_claim("llama at https://api.example.com/v1 answered from 1 of the 3 passages served")  # fmt: skip
    assert old["who"] == "llama" and old["url"] == "https://api.example.com/v1"
    assert old["settings"] == {} and old["did"].startswith("answered from 1 of the 3")
    there = oc.read_claim("m.gguf (sha256 ab) in this process answered from 1 of the 1 passages served")  # fmt: skip
    assert there["where"] == "in this process" and there["url"] is None
    assert oc.read_claim("the garden notes") is None and oc.read_claim("") is None
    assert oc.read_claim("gemma at x (temperature) did")["settings"] == {}


def test_another_add_ons_seed_goes_in_its_place(box, model):
    model.reply = "ok"
    assert oc.ask_model(model.url, "m", [], seed=7) == "ok"
    assert oc.ask_model(model.url, "m", [], "low", seed=7) == "ok"
    first, second = (body for _, body in model.sent)
    assert first["seed"] == 7 and list(first) == [
        "model",
        "messages",
        "temperature",
        "seed",
    ]
    assert second["seed"] == 7 and second["reasoning_effort"] == "low"


def test_a_claim_via_another_program_reads_only_before_its_settings():
    got = oc.read_claim("gpt-4o via MCP sampling (temperature 0, seed 0) answered from 1 of the 1 passages served")  # fmt: skip
    assert (got["who"], got["where"], got["via"], got["url"]) == (
        "gpt-4o", "via MCP sampling", "MCP sampling", None)  # fmt: skip
    assert got["settings"] == {"temperature": "0", "seed": "0"}
    assert oc.read_claim("m via llm (temperature 0, seed 0) did")["via"] == "llm"
    assert oc.read_claim("m via llm answered from 1 of the 1 passages served") is None
    assert oc.read_claim(f"m at {'http://x'} answered from 1")["via"] is None
