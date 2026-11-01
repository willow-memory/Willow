"""sent-log: a model is named only from a proposal file that is the bytes
proposed, never guessed; what the record cannot see is said, not hidden."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-01T00:00:00Z"]
Q = "how much sun do tomatoes want"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(b: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "sent_log.py"), "--box", str(b), *extra],
        capture_output=True, text=True,
    )  # fmt: skip


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n\nWater.\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW)
    return b


def bite(b: Path, q: str = Q) -> dict:
    return json.loads(k("bite", "--box", str(b), *NOW, q).stdout)


def propose(b: Path, tmp_path: Path, got: dict, claim: str, n: int = 0) -> str:
    row = {"path": f"a{n}.md", "data": "Six hours.", "cites": [got["served"][0]["id"]],
           "claim": claim}  # fmt: skip
    f = tmp_path / f"rows{n}.jsonl"
    f.write_text(json.dumps(row) + "\n")
    out = k("propose", "--box", str(b), "--file", str(f), *NOW).stdout
    assert out.startswith("pass")
    return out.split()[1]


def test_it_names_the_model_and_where_it_is_from_the_claim(tmp_path):
    b = box(tmp_path)
    got = bite(b)
    propose(b, tmp_path, got, "gemma-3-4b-it at http://127.0.0.1:8080/v1 answered from 1 of the 1 passages served")  # fmt: skip
    r = run(b)
    assert r.returncode == 0
    assert "gemma-3-4b-it at http://127.0.0.1:8080/v1 (this machine)" in r.stdout
    assert "went: garden.md:1 " + got["served"][0]["id"][:12] in r.stdout
    assert "1 proposal(s) on the record" in r.stdout


def test_a_remote_endpoint_is_said_to_be_online_with_its_host(tmp_path):
    b = box(tmp_path)
    propose(b, tmp_path, bite(b), "llama at https://api.example.com/v1 answered from 1 of the 1 passages served")  # fmt: skip
    r = run(b)
    assert "(online: api.example.com)" in r.stdout and r.returncode == 0
    propose(b, tmp_path, bite(b), "m at http://localhost:1/v1 answered from 1 of the 1 passages served", 1)  # fmt: skip
    assert "localhost:1/v1 (this machine)" in run(b).stdout


def test_a_claim_that_names_no_model_is_unnamed_and_escalates(tmp_path):
    b = box(tmp_path)
    propose(b, tmp_path, bite(b), "garden.md")
    r = run(b)
    assert r.returncode == 42
    assert "model not named" in r.stdout and "'garden.md'" in r.stdout
    assert "went:" not in r.stdout


def test_a_proposal_file_that_is_not_the_bytes_proposed_is_never_read(tmp_path):
    b = box(tmp_path)
    subj = propose(b, tmp_path, bite(b), "gemma at http://127.0.0.1:1/v1 answered from 1 of the 1 passages served")  # fmt: skip
    path = b / "proposals" / f"{subj[9:]}.json"
    doc = json.loads(path.read_text())
    doc["claim"] = (
        "other at http://127.0.0.1:1/v1 answered from 1 of the 1 passages served"
    )
    path.write_text(json.dumps(doc))
    r = run(b)
    assert r.returncode == 42 and "not the bytes proposed" in r.stdout
    assert "other at" not in r.stdout
    path.write_text("not json")
    assert "not the bytes proposed" in run(b).stdout
    path.unlink()
    r = run(b)
    assert r.returncode == 42 and "file is missing" in r.stdout


def test_a_count_that_disagrees_with_the_bite_is_not_called_went(tmp_path):
    b = box(tmp_path)
    propose(b, tmp_path, bite(b), "m at http://127.0.0.1:1/v1 answered from 1 of the 3 passages served")  # fmt: skip
    r = run(b)
    assert "may have gone" in r.stdout and "went:" not in r.stdout


def test_an_echo_passage_was_not_sent(tmp_path):
    b = box(tmp_path)
    (tmp_path / "pile" / "q.md").write_text(Q + "\n")
    got = bite(b)
    assert any(s["echo"] for s in got["served"]) and not got["served"][0]["echo"]
    propose(b, tmp_path, got, "m at http://127.0.0.1:1/v1 answered from 1 of the 1 passages served")  # fmt: skip
    assert "q.md" not in run(b).stdout


def test_what_the_record_cannot_see_is_counted_not_hidden(tmp_path):
    b = box(tmp_path)
    r = run(b)
    assert r.returncode == 0 and "that is a floor" in r.stdout
    bite(b)  # asked, nothing proposed: a reply that cited nothing leaves this
    f = tmp_path / "bad.jsonl"
    f.write_text(json.dumps({"path": "x.md", "data": "d", "cites": ["nope"], "claim": "c"}) + "\n")  # fmt: skip
    k("propose", "--box", str(b), "--file", str(f), *NOW)
    r = run(b)
    assert "0 proposal(s)" in r.stdout
    assert "1 bite(s) served passages and were proposed on by no one" in r.stdout
    assert "1 refused proposal(s) name nothing" in r.stdout


def test_the_claim_openai_compatible_writes_is_the_claim_this_reads(
    tmp_path, monkeypatch
):
    spec = importlib.util.spec_from_file_location(
        "oc", HERE.parent / "openai-compatible" / "openai_compatible.py"
    )
    oc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oc)
    monkeypatch.setattr(oc, "ask_model", lambda url, model, chat: "Six hours [1].")
    b = box(tmp_path)
    url = "https://models.example.org/v1"
    assert oc.main(["ask", "--box", str(b), "--url", url, "--model", "qwen", *NOW, Q]) == 0  # fmt: skip
    r = run(b)
    assert r.returncode == 0
    assert f"qwen at {url} (online: models.example.org)" in r.stdout
    assert "went: garden.md:1" in r.stdout


def test_a_broken_chain_is_refused_and_nothing_is_written(tmp_path):
    b = box(tmp_path)
    bite(b)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace('"kernel"', '"forged"', 1))
    r = run(b)
    assert r.returncode == 2 and "refused" in r.stderr
    assert run(tmp_path / "nowhere").returncode == 2
    assert run(b, "extra").returncode == 2


def test_it_reads_and_never_writes(tmp_path):
    b = box(tmp_path)
    propose(b, tmp_path, bite(b), "m at http://127.0.0.1:1/v1 answered from 1 of the 1 passages served")  # fmt: skip
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    run(b)
    after = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    assert before == after
