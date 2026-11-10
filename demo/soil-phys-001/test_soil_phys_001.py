"""soil-phys-001: the frozen files as frozen; the answer key whole and its
sources pinned; a kept file that isn't the frozen one refused; the TEI's
text; and each pass rule counted from rows made by hand."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run  # noqa: E402


def test_frozen_files_are_as_frozen_or_the_study_says_it_is_a_draft():
    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        assert "DRAFT" in (HERE / "README.md").read_text(encoding="utf-8")
        return
    files = json.loads(frozen.read_text(encoding="utf-8"))["files"]
    for rel, sha in files.items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert {"key.json", "sources.json", "run.py"} <= set(files)


def test_the_key_is_whole_and_every_file_it_names_is_pinned():
    files = {s["file"] for s in run.SOURCES}
    lines = run.KEY["lines"]
    assert len(lines) == 35 and len({x["id"] for x in lines}) == 35
    for x in lines:
        assert x["file"] in files and x["quote"] and x["claim"] and x["question"]
        assert x["verdict"] in (*run.HOLDS, "does not hold", "not found in this text")
    assert len(run.KEY["null"]) == 10
    for s in run.SOURCES:
        assert len(s["sha256"]) == 64 and s["url"].startswith("https://")


def test_a_kept_file_missing_or_changed_is_refused(tmp_path, capsys):
    assert run.held(tmp_path)  # nothing there: every file missing
    first = run.SOURCES[0]["file"]
    (tmp_path / first).write_bytes(b"not the paper")
    bad = run.held(tmp_path)
    assert any(b.startswith(first + ": changed") for b in bad)
    args = [
        "--keep",
        str(tmp_path),
        "--work",
        str(tmp_path / "w"),
        "--out",
        str(tmp_path / "o"),
    ]
    assert run.main(args) == 2 and "aren't the frozen ones" in capsys.readouterr().err
    assert run.main(["--keep", "x"]) == 2


def test_a_tei_transcription_is_its_body_one_paragraph_a_line():
    raw = ('<TEI><teiHeader><title>Mr. Leibniz\'s Third Paper</title></teiHeader>'
           '<text><body><p>I hold <hi>Space</hi> to be\n something merely relative.</p>'
           '<p>An Order of Coexistences.</p></body></text></TEI>')  # fmt: skip
    assert run.tei_text(raw) == (
        "I hold Space to be something merely relative.\n\nAn Order of Coexistences.\n"
    )


def row(f, verdict, found=False, right=False, served=False):
    return {"file": f, "verdict": verdict, "misquote": {"found": found},
            "claim": {"all_parts": right, "right_file": right},
            "ask": {"served": int(served), "right_file": served}}  # fmt: skip


def test_each_rule_counts_only_what_it_says():
    text = sorted(s["file"] for s in run.SOURCES if s["text_layer"])
    scan = sorted(s["file"] for s in run.SOURCES if not s["text_layer"])
    rows = [row(text[0], "holds", True, True, True) for _ in range(9)]
    rows += [row(text[1], "holds with a change", True, False, False)]
    rows += [row(text[2], "does not hold", False, True, False)]
    rows += [row(scan[0], "holds", True, True, True)]  # a scan never counts
    nulls = [
        {"claim": {"all_parts": i < 1}, "ask": {"served": int(i < 2)}}
        for i in range(10)
    ]
    got = run.tally(rows, nulls)
    assert got["R1"]["number"] == "10 of 11" and got["R1"]["state"] == "satisfied"
    assert got["R2"]["number"] == "9 of 10" and got["R2"]["state"] == "satisfied"
    assert got["R3"]["number"] == "9 of 10"
    assert got["R4"]["state"] == "satisfied"
    assert got["P1"]["number"].startswith("1 of 1") and got["P2"]["number"].startswith(
        "1 of 1"
    )
    nulls[2]["ask"]["served"] = 1
    assert run.tally(rows, nulls)["R4"]["state"] == "failing"
    assert run.rule(0, 0, 0.5)["state"] == "failing"  # nothing asked passes nothing
