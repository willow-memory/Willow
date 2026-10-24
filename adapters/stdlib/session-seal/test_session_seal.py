"""session-seal: a session's rows bundled and proposed through the kernel's own
verbs, waiting on the person's seal; each session read back as sealed,
waiting or broken; nothing ever sealed by this code."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "session_seal.py"
spec = importlib.util.spec_from_file_location("session_seal", SCRIPT)
ss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss)
NOW = ["--now", "2026-10-24T09:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def kernel(*argv: str) -> subprocess.CompletedProcess:
    return run(*argv, script=KERNEL)


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun and the beans want water.\n")
    box = tmp_path / "box"
    got = kernel("init", "--box", str(box), "--pile", str(pile),
                 "--key", str(tmp_path / "key"), *NOW)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = ss.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def waiting_subject(box: Path) -> str:
    return next(r["subject"] for r in reversed(rows(box)) if r["kind"] == "session")


def test_a_session_is_bundled_and_waits_on_the_persons_seal(tmp_path):
    box = make(tmp_path)
    assert kernel("bite", "--box", str(box), "tomatoes sun", *NOW).returncode == 0
    assert kernel("bite", "--box", str(box), "qqqq zzzz", *NOW).returncode == 42
    got = run("--box", str(box), *NOW)
    assert got.returncode == 42, got.stderr
    assert "session rows 0 to 2: 3 rows" in got.stdout
    assert "1 bite: empty, 1 bite: served, 1 boot" in got.stdout
    subj = waiting_subject(box)
    assert f"kernel.py seal --box {box} {subj}" in got.stdout
    kinds = [r["kind"] for r in rows(box)]
    assert kinds == ["boot", "bite", "bite", "bite", "proposal", "session"]
    s = rows(box)[-1]
    assert (s["from"], s["to"], s["who"]) == (0, 2, "session-seal")
    assert s["standing"] == "unattested", "only the person's seal is sealed"
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    assert prop["cites"] == [] and prop["path"] == "sessions/0-2.json"
    b = json.loads(prop["data"])
    assert b["rows"] == [[r["n"], r["kind"], r["hash"]] for r in rows(box)[:3]]
    assert b["tip"] == rows(box)[2]["hash"]
    assert not (box / "written").exists(), "nothing is written until it's sealed"


def test_the_bundle_keeps_no_words(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    run("--box", str(box), *NOW)
    prop = json.loads((box / "proposals" / f"{waiting_subject(box)[9:]}.json")
                      .read_text())  # fmt: skip
    for w in ("tomatoes", "sun", "beans", "water", "garden"):
        assert w not in prop["data"].lower()


def test_check_says_waiting_then_sealed_once_the_person_seals(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    run("--box", str(box), *NOW)
    got = run("--box", str(box), "check")
    assert got.returncode == 42 and got.stdout.startswith("waiting  rows 0 to 1")
    assert "1 waiting, 0 broken; 0 rows since, not yet bundled" in got.stdout
    sealed = kernel("seal", "--box", str(box), waiting_subject(box), *NOW)
    assert sealed.returncode == 0, sealed.stderr
    got = run("--box", str(box), "check")
    assert got.returncode == 0 and got.stdout.startswith("sealed   rows 0 to 1")
    assert "1 sessions: 1 sealed, 0 waiting, 0 broken; 1 rows since" in got.stdout
    assert (box / "written" / "sessions" / "0-1.json").exists()


def test_asking_for_the_session_again_answers_with_the_sealed_bundle(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    run("--box", str(box), *NOW)
    kernel("seal", "--box", str(box), waiting_subject(box), *NOW)
    got = kernel("bite", "--box", str(box), "Session 0 to 1", *NOW)
    doc = json.loads(got.stdout)
    assert got.returncode == 0 and doc["state"] == "sealed"
    assert json.loads(doc["answer"])["from"] == 0


def test_the_next_session_starts_after_the_last_and_none_is_empty(tmp_path):
    box = make(tmp_path)
    run("--box", str(box), *NOW)
    got = run("--box", str(box), *NOW)
    assert got.returncode == 0 and got.stdout.startswith("Nothing since")
    kernel("bite", "--box", str(box), "beans water", *NOW)
    got = run("--box", str(box), *NOW)
    assert got.returncode == 42 and "session rows 4 to 4: 1 rows" in got.stdout


def test_a_bundle_edited_in_the_box_is_broken_not_sealed(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    run("--box", str(box), *NOW)
    kernel("seal", "--box", str(box), waiting_subject(box), *NOW)
    f = box / "proposals" / f"{waiting_subject(box)[9:]}.json"
    prop = json.loads(f.read_text())
    prop["data"] = prop["data"].replace('"from":0', '"from":1')
    f.write_text(json.dumps(prop))
    got = run("--box", str(box), "check")
    assert got.returncode == 2 and got.stdout.startswith("broken   rows 0 to 1")
    assert "1 sessions: 0 sealed, 0 waiting, 1 broken" in got.stdout


def test_a_seal_this_code_could_forge_never_counts(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    run("--box", str(box), *NOW)
    subj = waiting_subject(box)
    ss.kernel.append(box, "2026-10-24T09:00:00Z", "seal", who="human",
                     subject=subj, proof="0" * 64)  # fmt: skip
    got = run("--box", str(box), "check")
    assert got.returncode == 42 and got.stdout.startswith("waiting")


def test_a_record_that_doesnt_verify_is_refused_and_nothing_is_written(tmp_path):
    box = make(tmp_path)
    kernel("bite", "--box", str(box), "tomatoes sun", *NOW)
    rec = box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"bite"', '"bitten"', 1))
    before = rec.read_bytes()
    for argv in ([], ["check"]):
        got = run("--box", str(box), *argv)
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert rec.read_bytes() == before


def test_a_bad_command_line_or_a_folder_that_isnt_a_box_is_refused(tmp_path):
    for argv in ([], ["--box"], ["--box", str(tmp_path), "seal"]):
        got = run(*argv)
        assert got.returncode == 2 and "session_seal.py" in got.stderr
    got = run("--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_came_of_says_what_each_row_came_to():
    assert ss.came_of({"kind": "bite", "served": [{"id": "x"}]}) == "bite: served"
    assert ss.came_of({"kind": "bite", "served": []}) == "bite: empty"
    assert ss.came_of({"kind": "bite", "answered_by": "p", "served": []}) == (
        "bite: sealed"
    )
    assert ss.came_of({"kind": "proposal", "verdict": "pass"}) == "proposal: pass"
    assert ss.came_of({"kind": "out", "waiting": 1}) == "out"
