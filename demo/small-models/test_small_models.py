"""demo/small-models: the box is built from what is committed here, a session
is read only when it is the one SESSION.json names, and every run is a
passage the kernel can serve."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("build", HERE / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "build.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def test_flatten_gives_one_line_a_value_and_keeps_a_reply_whole():
    doc = {"plan": {"steps": [{"name": "bank", "ran": True}]}, "raw": "a\nb"}
    assert build.flatten(doc) == [
        "plan.steps[0].name: bank",
        "plan.steps[0].ran: true",
        "raw: a\nb",
        "",
    ]


def test_without_a_session_the_box_holds_every_run_the_ofrenda_and_the_code(tmp_path):
    got = run("--to", str(tmp_path / "out"))
    assert got.returncode == 0, got.stderr
    pile = tmp_path / "out" / "pile"
    runs = sorted(p.name for p in (pile / "runs").iterdir())
    want = [f"small-models-{p.stem}.txt" for p in (HERE / "runs").glob("*.json")]
    want += [
        f"ofrenda-{p.stem}.txt" for p in (ROOT / "demo/ofrenda/results").glob("*.json")
    ]
    assert runs == sorted(want)
    assert (pile / "ofrenda" / "README.md").is_file()
    assert (pile / "code" / "build.py.txt").is_file()
    assert not (pile / "session").exists()
    assert (tmp_path / "out" / "box" / "record.jsonl").is_file()
    plain = ROOT / "adapters/stdlib/plain/plain.py"
    said = subprocess.run([sys.executable, str(plain), "bite", "--box", str(tmp_path / "out" / "box"),
                           "which model told the biscochitos secret"],
                          capture_output=True, text=True)  # fmt: skip
    assert "qwen told the secret" in said.stdout.lower(), said.stdout


def test_a_session_that_isnt_the_frozen_one_is_refused_and_leaves_nothing(tmp_path):
    other = tmp_path / "other.jsonl"
    other.write_text('{"type":"user","message":{"role":"user","content":"hi"}}\n')
    got = run("--to", str(tmp_path / "out"), "--session", str(other))
    assert got.returncode == 2 and "not the session" in got.stderr
    assert not (tmp_path / "out").exists()


def test_a_later_copy_of_the_session_is_read_only_to_its_frozen_bytes(
    tmp_path, monkeypatch
):
    """A session file only grows: what was frozen is its first `bytes` bytes."""
    first = (
        b'{"type":"user","message":{"role":"user","content":"When is the dentist?"}}\n'
    )
    later = (
        first + b'{"type":"user","message":{"role":"user","content":"later words"}}\n'
    )
    monkeypatch.setattr(
        build,
        "SESSION",
        {"id": "s", "bytes": len(first), "sha256": hashlib.sha256(first).hexdigest()},
    )
    f = tmp_path / "s.jsonl"
    f.write_bytes(later)
    pile = tmp_path / "pile"
    pile.mkdir()
    (tmp_path / "t").mkdir()
    build.session(pile, f, tmp_path / "t")
    text = "".join(p.read_text() for p in (pile / "session").rglob("*.txt"))
    assert "When is the dentist?" in text and "later words" not in text


def test_the_frozen_session_is_named_by_its_bytes_and_hash_and_never_its_text():
    s = json.loads((HERE / "SESSION.json").read_text())
    assert set(s) == {"about", "id", "tool", "frozen", "bytes", "lines", "sha256"}
    assert len(s["sha256"]) == 64 and s["bytes"] > 0
    assert not list(HERE.rglob("*.jsonl")), "no session file is kept here"


def test_a_bad_command_line_or_a_folder_that_exists_is_refused(tmp_path):
    assert run().returncode == 2
    assert run("--to").returncode == 2
    assert run("--to", str(tmp_path), "--stray", "x").returncode == 2
    got = run("--to", str(tmp_path))
    assert got.returncode == 2 and got.stderr.startswith("refused")
