"""annotations: each approved answer as a W3C Web Annotation in an annotation
page: the answer as the body, each cited passage as a target with an RFC 5147
line fragment and its quoted words; a forged approval, a changed proposal and
a vanished passage left out and said; the same bytes twice; written once and
private; refusals; the box unchanged."""

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
SCRIPT = HERE / "annotations.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("kernel_for_annotations", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
GARDEN = "Notes\n\nTomatoes want six hours of sun.\nWater them daily.\n\nFrost is due in November.\n"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps(
        {x: row[x] for x in ("path", "data", "cites", "claim")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(tmp_path: Path, seal: bool = True) -> tuple[Path, str]:
    pile = tmp_path / "pile"
    (pile / "notes").mkdir(parents=True)
    (pile / "notes" / "garden.md").write_text(GARDEN)
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
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want water").stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours, and water daily.",
        "cites": [s["id"] for s in served],
        "claim": "the garden notes",
    }
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"), *NOW
        ).returncode
        == 42
    )
    if seal:
        assert k("seal", "--box", str(b), subject(row), *NOW).returncode == 0
    return b, subject(row)


def export(b: Path, tmp_path: Path, *extra: str):
    to = tmp_path / "a.json"
    to.unlink(missing_ok=True)
    got = run("--box", str(b), "--to", str(to), *extra)
    return got, json.loads(to.read_text()) if to.exists() else {}


def test_an_approved_answer_is_an_annotation_with_the_answer_as_its_body(tmp_path):
    b, subj = box(tmp_path)
    got, page = export(b, tmp_path)
    assert got.returncode == 0, got.stderr
    assert (
        page["@context"] == "http://www.w3.org/ns/anno.jsonld"
        and page["type"] == "AnnotationPage"
    )
    (a,) = page["items"]
    assert (
        a["type"] == "Annotation"
        and a["id"] == f"urn:willow:annotation:{subj[9:]}"
        and a["motivation"] == "describing"
    )
    assert a["body"] == {
        "type": "TextualBody",
        "value": "Six hours, and water daily.",
        "format": "text/plain",
    }
    assert a["created"] == "2026-10-24T00:00:00Z" and a["generator"] == {
        "type": "Software",
        "name": "willow",
    }
    assert f"wrote {tmp_path / 'a.json'}: 1 annotation" in got.stdout


def test_each_cited_passage_is_a_target_with_zero_based_lines_and_its_words(tmp_path):
    b, _ = box(tmp_path)
    _, page = export(b, tmp_path)
    targets = page["items"][0]["target"]
    assert [t["source"] for t in targets] == ["notes/garden.md"] * len(targets)
    sun = next(t for t in targets if "Tomatoes" in t["selector"][1]["exact"])
    assert sun["selector"][0] == {
        "type": "FragmentSelector",
        "conformsTo": "http://tools.ietf.org/rfc/rfc5147",
        "value": "line=2,4",
    }
    assert sun["selector"][1] == {
        "type": "TextQuoteSelector",
        "exact": "Tomatoes want six hours of sun.\nWater them daily.",
    }


def test_a_base_url_prefixes_the_source_with_the_path_made_safe(tmp_path):
    b, _ = box(tmp_path)
    _, page = export(b, tmp_path, "--base", "https://example.org/files/")
    assert (
        page["items"][0]["target"][0]["source"]
        == "https://example.org/files/notes/garden.md"
    )
    (tmp_path / "pile" / "notes").rename(tmp_path / "pile" / "my notes")
    _, page = export(b, tmp_path, "--base", "https://example.org/files")
    assert (
        page["items"][0]["target"][0]["source"]
        == "https://example.org/files/my%20notes/garden.md"
    )


def test_a_passage_no_longer_in_the_files_is_left_off_and_said(tmp_path):
    b, _ = box(tmp_path)
    (tmp_path / "pile" / "notes" / "garden.md").write_text(
        GARDEN.replace("six", "eight")
    )
    got, page = export(b, tmp_path)
    assert got.returncode == 42 and "cited passage left off" in got.stderr
    assert page["items"][0]["target"] == []


def test_an_unsealed_suggestion_is_not_an_annotation(tmp_path):
    b, _ = box(tmp_path, seal=False)
    got, page = export(b, tmp_path)
    assert got.returncode == 0 and page["items"] == [] and "0 annotations" in got.stdout


def test_a_forged_approval_is_in_no_list(tmp_path):
    b, subj = box(tmp_path, seal=False)
    kernel.append(
        b, "2026-10-24T00:00:00Z", "seal", who="human", subject=subj, proof="0" * 64
    )
    got, page = export(b, tmp_path)
    assert page["items"] == [] and got.returncode == 0


def test_a_changed_proposal_file_is_left_out_and_said(tmp_path):
    b, subj = box(tmp_path)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got, page = export(b, tmp_path)
    assert (
        got.returncode == 42
        and page["items"] == []
        and "1 approval left out" in got.stderr
    )


def test_the_same_record_and_folder_give_the_same_bytes(tmp_path):
    b, _ = box(tmp_path)
    export(b, tmp_path)
    one = (tmp_path / "a.json").read_bytes()
    export(b, tmp_path)
    assert (tmp_path / "a.json").read_bytes() == one


def test_the_file_is_written_once_private_and_never_over_a_file(tmp_path):
    b, _ = box(tmp_path)
    to = tmp_path / "a.json"
    assert run("--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    again = run("--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    assert (
        run("--box", str(b), "--to", str(tmp_path / "nope" / "a.json")).returncode == 2
    )


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b, _ = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026", "2025", 1))
    got = run("--box", str(b), "--to", str(tmp_path / "a.json"))
    assert got.returncode == 2 and not (tmp_path / "a.json").exists()


def test_the_box_is_not_changed(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "a.json"))
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = box(tmp_path)
    to = str(tmp_path / "a.json")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--base"],
                 ["--box", str(b), "--to", to, "--base", "ftp://x"], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "annotations.py" in run().stderr
