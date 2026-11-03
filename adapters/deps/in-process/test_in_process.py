"""in-process: a GGUF model loaded in this process through llama-cpp-python
answers from what the kernel served, and its reply waits on your seal.

The real model here is conftest's: llama.cpp loads it and generates, the
same way twice, but what it says is noise and cites nothing. The flow from a
reply to a proposal is held with a stand-in model passed where the loaded
one would be."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "in_process.py"
NOW = ["--now", "2026-11-02T00:00:00Z"]
Q = "what goes in biscochitos"
_spec = importlib.util.spec_from_file_location("willow_in_process", SCRIPT)
ip = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ip)


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv), *NOW],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


@pytest.fixture
def box(tmp_path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "recipes.txt").write_text(
        "Biscochitos: lard, not butter, and a spoonful of anise seed.\n\n"
        "The gate by the acequia sticks in winter.\n"
    )
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    return b


def kinds(box: Path) -> list[str]:
    return [
        json.loads(line)["kind"]
        for line in (box / "record.jsonl").read_text().splitlines()
    ]


class StandIn:
    """Says `reply`; keeps what it was asked."""

    def __init__(self, reply="Lard, not butter, and anise seed [1].", fail=None):
        self.reply, self.fail, self.asked = reply, fail, []

    def create_chat_completion(self, **kw):
        self.asked.append(kw)
        if self.fail:
            raise self.fail
        return {"choices": [{"message": {"content": self.reply}}]}


def ask_with(monkeypatch, capsys, stand_in, *argv) -> tuple[int, str]:
    loaded = []
    monkeypatch.setattr(ip, "load", lambda path: loaded.append(path) or stand_in)
    code = ip.main(["ask", *map(str, argv)])
    return code, capsys.readouterr().out


# ── the real thing: llama.cpp, in this process ─────────────────────────────


def test_llama_cpp_loads_the_model_here_and_answers_the_same_way_twice(box, model):
    first = run("ask", "--box", box, "--model", model, *NOW, Q)
    second = run("ask", "--box", box, "--model", model, *NOW, Q)
    assert first.stdout == second.stdout, "temperature 0, a fixed seed: the same reply"
    assert first.returncode == 42, first.stdout + first.stderr
    assert first.stdout.endswith(("cited no passage; proposed to no one\n",))
    assert kinds(box) == ["boot", "bite", "bite"], "bitten each time, nothing proposed"


def test_each_load_answers_the_same_chat_the_same_way(model):
    """A run loads the model once and asks once; two loads, the same reply."""
    chat = [
        {"role": "user", "content": "Passages:\n\n[1] (a:1)\nLard.\n\nQuestion: what"}
    ]
    first = ip.answer(ip.load(model), chat)
    assert isinstance(first, str) and first
    assert first == ip.answer(ip.load(model), chat)


def test_nothing_served_loads_no_model(box, tmp_path):
    not_a_model = tmp_path / "x.gguf"
    not_a_model.write_bytes(b"not a model")
    got = run("ask", "--box", box, "--model", not_a_model, *NOW, "how tall is the moon")
    assert got.returncode == 42
    assert got.stdout == "nothing in your folder holds that; no model was loaded\n"


def test_a_file_that_isnt_a_model_doesnt_answer(box, tmp_path):
    bad = tmp_path / "bad.gguf"
    bad.write_bytes(b"GGUF nonsense")
    got = run("ask", "--box", box, "--model", bad, *NOW, Q)
    assert got.returncode == 42
    assert got.stdout.startswith("the model didn't answer: bad.gguf (")


# ── the flow, with a stand-in where the loaded model would be ──────────────


def test_a_reply_citing_a_served_passage_waits_on_your_seal(
    box, model, monkeypatch, capsys
):
    stand_in = StandIn()
    code, out = ask_with(
        monkeypatch, capsys, stand_in, "--box", box, "--model", model, *NOW, Q
    )
    assert code == 0, out
    lines = out.splitlines()
    assert lines[0] == "Lard, not butter, and anise seed [1]."
    assert re.fullmatch(r"pass  proposal:[0-9a-f]{64}  waiting on your seal", lines[1])
    asked = stand_in.asked[0]
    assert (asked["temperature"], asked["seed"], asked["max_tokens"]) == (0, 0, 512)
    user = asked["messages"][1]["content"]
    assert "anise seed" in user and "acequia" not in user, "only what was served"
    subj = lines[1].split()[1]
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    assert prop["claim"] == (f"tiny.gguf (sha256 {digest}) in this process answered"
                             " from 1 of the 1 passages served")  # fmt: skip
    assert str(model.parent) not in prop["claim"], (
        "the file's name, never where it lives"
    )
    assert prop["path"] == "answers/what-goes-in-biscochitos.md"
    assert kinds(box)[-2:] == ["bite", "proposal"]
    assert k("verify", "--box", box).returncode == 0


def test_a_reply_citing_nothing_is_proposed_to_no_one(box, model, monkeypatch, capsys):
    code, out = ask_with(
        monkeypatch,
        capsys,
        StandIn("Lard, I think."),
        "--box",
        box,
        "--model",
        model,
        *NOW,
        Q,
    )
    assert code == 42
    assert out == "Lard, I think.\ncited no passage; proposed to no one\n"
    assert "proposal" not in kinds(box)


def test_a_reply_that_only_cites_is_proposed_to_no_one(box, model, monkeypatch, capsys):
    for only in ("[1]", "[1] (notes/biscochitos.md:3)\n", "[1], [1]."):
        code, out = ask_with(
            monkeypatch, capsys, StandIn(only), "--box", box, "--model", model, *NOW, Q
        )
        assert code == 42, out
        assert out.endswith(
            "cited a passage and said nothing else; proposed to no one\n"
        )
    assert "proposal" not in kinds(box)


def test_a_model_that_fails_or_says_nothing(box, model, monkeypatch, capsys):
    code, out = ask_with(monkeypatch, capsys, StandIn(fail=RuntimeError("boom")),
                         "--box", box, "--model", model, *NOW, Q)  # fmt: skip
    assert code == 42 and out == "the model didn't answer: tiny.gguf (RuntimeError)\n"
    code, out = ask_with(
        monkeypatch,
        capsys,
        StandIn(reply=None),
        "--box",
        box,
        "--model",
        model,
        *NOW,
        Q,
    )
    assert code == 42 and out == "\ncited no passage; proposed to no one\n"


def test_a_voice_comes_before_the_rule(box, model, monkeypatch, capsys, tmp_path):
    voice = tmp_path / "voice.md"
    voice.write_text("You are terse.\n")
    stand_in = StandIn()
    ask_with(
        monkeypatch,
        capsys,
        stand_in,
        "--box",
        box,
        "--model",
        model,
        "--system",
        voice,
        *NOW,
        Q,
    )
    system = stand_in.asked[0]["messages"][0]["content"]
    assert system.startswith("You are terse.\n\nAnswer only from the numbered passages")


def test_an_answer_sealed_already_is_given_and_nothing_is_loaded(
    box, model, monkeypatch, capsys
):
    code, out = ask_with(
        monkeypatch, capsys, StandIn(), "--box", box, "--model", model, *NOW, Q
    )
    subj = re.search(r"proposal:[0-9a-f]{64}", out).group(0)
    assert k("seal", "--box", box, subj).returncode == 0
    stand_in = StandIn()
    code, out = ask_with(
        monkeypatch, capsys, stand_in, "--box", box, "--model", model, *NOW, Q
    )
    assert (
        code == 0 and out == "sealed already: Lard, not butter, and anise seed [1].\n"
    )
    assert stand_in.asked == []


def test_without_llama_cpp_python_it_refuses_and_names_it(
    box, model, monkeypatch, capsys
):
    real = importlib.util.find_spec
    monkeypatch.setattr(ip.importlib.util, "find_spec",
                        lambda name, *a: None if name == "llama_cpp" else real(name, *a))  # fmt: skip
    code = ip.main(["ask", "--box", str(box), "--model", str(model), Q])
    assert code == 2
    assert "llama-cpp-python isn't installed" in capsys.readouterr().err
    assert kinds(box) == ["boot"], "refused before the kernel is asked"


def test_a_bad_command_line_is_refused(box, model, tmp_path):
    for argv in ([], ["talk"], ["ask", "--box", box, Q], ["ask", "--model", model, Q],
                 ["ask", "--box", box, "--model", model], ["ask", "--box", box, "--model", model, Q, "more"],
                 ["ask", "--box", box, "--model", model, "--box", box, Q],
                 ["ask", "--box", box, "--model", "", Q], ["ask", "--box", box, "--model", model, "--x"],
                 ["ask", "--box", box, "--model", model, " "]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "in_process.py" in got.stderr, argv
    got = run("ask", "--box", box, "--model", tmp_path / "missing.gguf", Q)
    assert got.returncode == 2 and "not a file" in got.stderr
    got = run(
        "ask", "--box", box, "--model", model, "--system", tmp_path / "missing.md", Q
    )
    assert got.returncode == 2 and "can't read" in got.stderr
    got = run("ask", "--box", tmp_path, "--model", model, Q)
    assert got.returncode == 2 and got.stdout == "" and "refused" in got.stderr
