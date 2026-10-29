"""cloudevents: each row of the record as a CloudEvents 1.0 JSON event, one a
line; the id the row's hash, the source the box's first row, the type the
kind; --from-row and --kinds narrow it; nothing in range writes nothing; a
record that doesn't verify refused; the same bytes twice; written once."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "cloudevents.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

NOW = ["--now", "2026-10-24T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ).returncode
        == 0
    )
    served = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours.",
        "cites": [served[0]["id"]],
        "claim": "the notes",
    }
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"), *NOW)
    subj = (
        "proposal:"
        + hashlib.sha256(
            json.dumps(
                {x: row[x] for x in ("path", "data", "cites", "claim")},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
    )
    k("seal", "--box", str(b), subj, *NOW)
    return b


def export(b: Path, tmp_path: Path, *extra: str):
    to = tmp_path / "e.jsonl"
    to.unlink(missing_ok=True)
    got = run("--box", str(b), "--to", str(to), *extra)
    return got, [
        json.loads(x) for x in to.read_text().splitlines()
    ] if to.exists() else []


def test_each_row_is_an_event_with_the_rows_hash_as_its_id(tmp_path):
    b = box(tmp_path)
    got, events = export(b, tmp_path)
    rows, _ = kernel.read(b / "record.jsonl")
    assert got.returncode == 0, got.stderr
    assert [e["id"] for e in events] == [r["hash"] for r in rows] and len(events) == 4
    assert all(
        e["specversion"] == "1.0" and e["datacontenttype"] == "application/json"
        for e in events
    )
    assert [e["type"] for e in events] == [
        "org.willow.record.boot",
        "org.willow.record.bite",
        "org.willow.record.proposal",
        "org.willow.record.seal",
    ]
    assert [e["sequence"] for e in events] == ["0", "1", "2", "3"] and events[3][
        "time"
    ] == "2026-10-24T00:00:00Z"
    assert (
        events[3]["data"] == rows[3]
        and events[3]["standing"] == "sealed"
        and events[1]["standing"] == "unattested"
    )
    assert f"wrote {tmp_path / 'e.jsonl'}: 4 events, rows 0 to 3" in got.stdout


def test_the_source_names_the_box_by_its_first_row_and_a_subject_is_carried(tmp_path):
    b = box(tmp_path)
    _, events = export(b, tmp_path)
    rows, _ = kernel.read(b / "record.jsonl")
    assert {e["source"] for e in events} == {f"urn:willow:record:{rows[0]['hash']}"}
    assert (
        "subject" not in events[1]
        and events[2]["subject"] == events[3]["subject"] == rows[3]["subject"]
    )


def test_the_data_keeps_the_chain_checkable(tmp_path):
    b = box(tmp_path)
    _, events = export(b, tmp_path)
    for prev, e in zip(events, events[1:]):
        assert e["data"]["prev"] == prev["id"]


def test_no_question_s_words_are_in_the_events(tmp_path):
    b = box(tmp_path)
    export(b, tmp_path)
    assert "tomatoes" not in (tmp_path / "e.jsonl").read_text().lower().replace(
        "tomatoes want", ""
    )


def test_from_row_starts_there_and_kinds_keep_only_those(tmp_path):
    b = box(tmp_path)
    _, events = export(b, tmp_path, "--from-row", "2")
    assert [e["sequence"] for e in events] == ["2", "3"]
    _, events = export(b, tmp_path, "--kinds", "bite,seal")
    assert [e["sequence"] for e in events] == ["1", "3"]
    _, events = export(b, tmp_path, "--from-row", "2", "--kinds", "seal")
    assert [e["sequence"] for e in events] == ["3"]


def test_nothing_in_range_writes_nothing_and_waits_on_you(tmp_path):
    b = box(tmp_path)
    for extra in (("--from-row", "9"), ("--kinds", "quiz")):
        got, events = export(b, tmp_path, *extra)
        assert (
            got.returncode == 42
            and events == []
            and not (tmp_path / "e.jsonl").exists()
        )


def test_the_same_record_gives_the_same_bytes(tmp_path):
    b = box(tmp_path)
    export(b, tmp_path)
    one = (tmp_path / "e.jsonl").read_bytes()
    export(b, tmp_path)
    assert (tmp_path / "e.jsonl").read_bytes() == one and one.count(b"\n") == 4


def test_the_file_is_written_once_private_and_never_over_a_file(tmp_path):
    b = box(tmp_path)
    to = tmp_path / "e.jsonl"
    assert run("--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert run("--box", str(b), "--to", str(tmp_path / "nope" / "e")).returncode == 2


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("garden.md", "garden.mx", 1))
    got = run("--box", str(b), "--to", str(tmp_path / "e.jsonl"))
    assert got.returncode == 2 and not (tmp_path / "e.jsonl").exists()


def test_the_box_is_not_changed(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "e.jsonl"))
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    to = str(tmp_path / "e.jsonl")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--from-row", "x"],
                 ["--box", str(b), "--to", to, "--kinds", "Bite"], ["--box", str(b), "--to", to, "--kinds", ""], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "cloudevents.py" in run().stderr
