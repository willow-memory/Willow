"""in-toto: each approved answer as an in-toto Statement, subject hashed from
the bytes written; a forged approval never exported, a changed proposal left out and said; the same
bytes twice; written once and never over a file; refusals."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "in_toto.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
spec = importlib.util.spec_from_file_location("kernel_for_in_toto", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def subject(row: dict) -> str:
    canon = json.dumps({k: row[k] for k in ("path", "data", "cites", "claim")},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(
    tmp_path: Path, seal: bool = True, data: str = "Six hours, no less."
) -> tuple[Path, str, str]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = json.loads(
        run(
            str(KERNEL), "bite", "--box", str(b), *NOW, "how much sun do tomatoes want"
        ).stdout
    )
    pid = got["served"][0]["id"]
    row = {"path": "sun.md", "data": data, "cites": [pid], "claim": "the garden notes"}
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    run(
        str(KERNEL),
        "propose",
        "--box",
        str(b),
        "--file",
        str(tmp_path / "r.jsonl"),
        *NOW,
    )
    if seal:
        run(str(KERNEL), "seal", "--box", str(b), subject(row), *NOW)
    return b, subject(row), pid


def export(b: Path, to: Path):
    got = run(str(SCRIPT), "--box", str(b), "--to", str(to))
    lines = to.read_text().splitlines() if to.exists() else []
    return got, [json.loads(x) for x in lines]


def test_an_approved_answer_is_a_statement_hashed_from_the_file_written(tmp_path):
    b, subj, pid = box(tmp_path)
    got, found = export(b, tmp_path / "s.jsonl")
    assert got.returncode == 0, got.stderr
    assert "1 statement" in got.stdout and len(found) == 1
    s = found[0]
    assert s["_type"] == "https://in-toto.io/Statement/v1"
    written = (b / "written" / "sun.md").read_bytes()
    assert s["subject"] == [
        {"name": "sun.md", "digest": {"sha256": hashlib.sha256(written).hexdigest()}}
    ]
    p = s["predicate"]
    assert s["predicateType"] == "urn:willow:seal:v1"
    assert p["claim"] == "the garden notes" and p["suggestion"] == subj
    assert p["cites"] == [{"id": pid, "where": "garden.md:1"}]
    assert p["sealRow"] == 3 and p["sealedAt"] == "2026-10-23T00:00:00Z"
    rows, _ = kernel.read(b / "record.jsonl")
    assert p["rowHash"] == rows[3]["hash"]
    assert p["question"] == rows[1]["bite_key"]


def test_a_non_ascii_answer_is_hashed_as_utf8(tmp_path):
    b, _, _ = box(tmp_path, data="Sechs Stunden – Tomaten brauchen Sonne.")
    _, found = export(b, tmp_path / "s.jsonl")
    written = (b / "written" / "sun.md").read_bytes()
    assert (
        found[0]["subject"][0]["digest"]["sha256"]
        == hashlib.sha256(written).hexdigest()
    )


def test_nothing_approved_is_an_empty_file(tmp_path):
    b, _, _ = box(tmp_path, seal=False)
    got, found = export(b, tmp_path / "s.jsonl")
    assert got.returncode == 0 and found == [] and "0 statements" in got.stdout


def test_a_forged_approval_is_in_no_list_and_is_not_exported(tmp_path):
    b, subj, _ = box(tmp_path, seal=False)
    kernel.append(
        b, "2026-10-23T00:00:00Z", "seal", who="human", subject=subj, proof="0" * 64
    )
    got, found = export(b, tmp_path / "s.jsonl")
    assert (
        found == [] and got.returncode == 0
    )  # a forged seal is in no list: never served


def test_a_changed_proposal_file_is_left_out_and_said(tmp_path):
    b, subj, _ = box(tmp_path)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got, found = export(b, tmp_path / "s.jsonl")
    assert got.returncode == 42 and found == []
    assert "1 approval left out" in got.stderr


def test_the_same_record_gives_the_same_bytes(tmp_path):
    b, _, _ = box(tmp_path)
    export(b, tmp_path / "one.jsonl")
    export(b, tmp_path / "two.jsonl")
    assert (tmp_path / "one.jsonl").read_bytes() == (
        tmp_path / "two.jsonl"
    ).read_bytes()


def test_the_file_is_written_once_private_and_never_over_a_file(tmp_path):
    b, _, _ = box(tmp_path)
    to = tmp_path / "s.jsonl"
    assert run(str(SCRIPT), "--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run(str(SCRIPT), "--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run(
            str(SCRIPT), "--box", str(b), "--to", str(tmp_path / "nope" / "s")
        ).returncode
        == 2
    )


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b, _, _ = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("garden.md", "garden.mx", 1))
    got = run(str(SCRIPT), "--box", str(b), "--to", str(tmp_path / "s.jsonl"))
    assert got.returncode == 2 and not (tmp_path / "s.jsonl").exists()


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--box"], ["--box", str(tmp_path)], ["--to", str(tmp_path / "x")],
                 ["--box", str(tmp_path), "--to", str(tmp_path / "x"), "stray"]):  # fmt: skip
        got = run(str(SCRIPT), *argv)
        assert got.returncode == 2 and "in_toto.py" in got.stderr
    assert (
        run(str(SCRIPT), "--box", str(tmp_path), "--to", str(tmp_path / "x")).returncode
        == 2
    )
