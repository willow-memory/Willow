"""jeles: nuggets from a Jeles seed file or corpus store as passages, never a
signature, never a gap; approvals out as a Jeles seed file, each paired with a
question only when its words hash to the key the approval was sealed under."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jeles  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "jeles.py"
NOW = ["--now", "2026-11-01T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


SEED = {
    "domain": "made-up-harbour",
    "pairs": [
        {"source_text": "When is high tide at the harbour?", "target_text": "Twice a day, about 12 hours 25 minutes apart.",
         "reason": "Tides are semidiurnal here.", "evidence_urls": ["https://tides.example.org/harbour"]},
        {"source_text": "Who keeps the harbour log?", "target_text": "The harbourmaster.",
         "verified_by": "ada", "seal_sig": "c2VjcmV0LXNpZ25hdHVyZQ=="},
        {"source_text": "", "target_text": "no question, not a pair"},
    ],
    "evidence": [{"pair_source": "When is high tide at the harbour?", "locator": "https://almanac.example.org/tides"}],
}  # fmt: skip


def store(path: Path) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE records (id TEXT PRIMARY KEY, data TEXT NOT NULL, created_at TEXT NOT NULL, "
                "updated_at TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0)")  # fmt: skip
    rows = [
        ("n1", {"question": "What is a black hole?", "answer": "A region where gravity lets nothing escape.",
                "sources": ["https://science.example.gov/black-holes"], "verified_by": "ada",
                "verified_at": "2026-10-01T09:00:00Z", "verification_kind": "human"}, 0),
        ("n2", {"question": "A deleted nugget?", "answer": "Never shown.", "verified_by": "bo"}, 1),
        ("g1", {"question": "What is dark matter?", "count": 3}, 0),  # a logged gap: no answer
    ]  # fmt: skip
    for rid, data, deleted in rows:
        con.execute(
            "INSERT INTO records VALUES (?, ?, 'x', 'x', ?)",
            (rid, json.dumps(data), deleted),
        )
    con.commit()
    con.close()


def test_a_seed_file_becomes_passages_and_a_signature_is_never_copied(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "harbour.json").write_text(json.dumps(SEED))
    got = run(str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to))
    assert got.returncode == 0, got.stderr
    text = (to / "harbour.json.txt").read_text()
    assert text.startswith("jeles seed: made-up-harbour, 2 pairs\n\n")
    assert (
        "When is high tide at the harbour?\nTwice a day, about 12 hours 25 minutes apart.\n"
        "reason: Tides are semidiurnal here.\n"
        "sources: https://almanac.example.org/tides, https://tides.example.org/harbour\n"
        "verified: asserted (a seed pair nobody has signed)\n\n"
    ) in text
    assert "verified: signed, by ada\n" in text
    assert "c2VjcmV0" not in text and "no question" not in text


def test_a_store_becomes_passages_without_deleted_rows_or_gaps(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "ask_jeles_corpus").mkdir(parents=True)
    store(folder / "ask_jeles_corpus" / "store.db")
    got = run(str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to))
    assert got.returncode == 0, got.stderr
    text = (to / "ask_jeles_corpus" / "store.db.txt").read_text()
    assert text == ("jeles store, 1 nugget\n\nWhat is a black hole?\nA region where gravity lets nothing escape.\n"
                    "sources: https://science.example.gov/black-holes\nverified: human, by ada, 2026-10-01\n\n")  # fmt: skip


def test_other_files_are_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "not-a-seed.json").write_text('{"name": "something else"}')
    (folder / "broken.json").write_text("{not json")
    (folder / "plain.db").write_bytes(b"not sqlite at all")
    got = run(str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to))
    assert (
        got.returncode == 42
        and got.stdout.strip() == f"wrote 0 files to {to}; skipped 3"
    )


def subject(row: dict) -> str:
    canon = json.dumps({k: row[k] for k in ("path", "data", "cites", "claim")},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def approved(tmp_path: Path) -> Path:
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
    row = {
        "path": "sun.md",
        "data": "Six hours.",
        "cites": [got["served"][0]["id"]],
        "claim": "the garden notes",
    }
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
    run(str(KERNEL), "seal", "--box", str(b), subject(row), *NOW)
    return b


def test_export_pairs_a_question_only_by_its_hash(tmp_path):
    b = approved(tmp_path)
    qs = tmp_path / "questions.txt"
    qs.write_text("How much SUN do tomatoes want?\nwhen does the frost come\n")
    out = tmp_path / "willow.json"
    got = run(
        str(SCRIPT), "export", "--box", str(b), "--questions", str(qs), "--to", str(out)
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == (f"wrote 1 pairs to {out}; 0 approvals had no question here; "
                                  "1 questions matched no approval")  # fmt: skip
    doc = json.loads(out.read_text())
    (pair,) = doc["pairs"]
    assert doc["domain"] == "willow-export"
    assert pair["source_text"] == "How much SUN do tomatoes want?"  # as you typed it
    assert pair["target_text"] == "Six hours." and pair["reason"] == "the garden notes"
    assert "not a Nestor seal" in pair["verified_by"] and "seal_sig" not in pair
    assert pair["willow"]["cites"] == ["garden.md:1"]
    assert doc["evidence"] == [
        {"pair_source": "How much SUN do tomatoes want?", "locator": "garden.md:1"}
    ]
    # the file it writes is one mirror reads back
    to = tmp_path / "m"
    folder = tmp_path / "exported"
    folder.mkdir()
    out.rename(folder / "willow.json")
    assert (
        run(str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to)).returncode
        == 0
    )
    assert (
        "Six hours.\nreason: the garden notes\nsources: garden.md:1\n"
        in (to / "willow.json.txt").read_text()
    )


def test_export_with_no_matching_question_writes_nothing(tmp_path):
    b = approved(tmp_path)
    qs = tmp_path / "q.txt"
    qs.write_text("how much rain do tomatoes want\n")
    out = tmp_path / "willow.json"
    got = run(
        str(SCRIPT), "export", "--box", str(b), "--questions", str(qs), "--to", str(out)
    )
    assert got.returncode == 42 and not out.exists()


def test_refusals(tmp_path):
    b = approved(tmp_path)
    qs = tmp_path / "q.txt"
    qs.write_text("how much sun do tomatoes want\n")
    (tmp_path / "taken.json").write_text("{}")
    for argv in (
        [
            "export",
            "--box",
            str(tmp_path / "nobox"),
            "--questions",
            str(qs),
            "--to",
            str(tmp_path / "o.json"),
        ],
        [
            "export",
            "--box",
            str(b),
            "--questions",
            str(qs),
            "--to",
            str(tmp_path / "taken.json"),
        ],
        [
            "export",
            "--box",
            str(b),
            "--questions",
            str(qs),
            "--to",
            str(tmp_path / "no" / "o.json"),
        ],
        [
            "export",
            "--box",
            str(b),
            "--questions",
            str(tmp_path / "missing"),
            "--to",
            str(tmp_path / "o.json"),
        ],
        ["mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")],
        ["mirror", "--from", str(tmp_path), "--to", str(tmp_path / "inside")],
        [],
    ):
        got = run(str(SCRIPT), *argv)
        assert got.returncode == 2 and got.stderr, argv
    assert "jeles.py" in run(str(SCRIPT)).stderr


def test_one_line_and_verified_wording():
    assert jeles._one_line(["a", None, " b  c "]) == "a, b c"
    assert (
        jeles._verified("human", "ada", "2026-10-01T09:00:00Z")
        == "human, by ada, 2026-10-01"
    )
    assert jeles._verified(None, None, None) == "unknown"
