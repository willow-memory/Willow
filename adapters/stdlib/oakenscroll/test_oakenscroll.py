"""Tests for oakenscroll.py. Every ledger is built here with the office's own
schema: made-up claims, no fixture files."""

from __future__ import annotations

import calendar
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "oakenscroll.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-01T00:00:00Z"]

SCHEMA = """
CREATE TABLE predictions (
    id TEXT PRIMARY KEY, claim TEXT NOT NULL, confidence REAL NOT NULL,
    stated_at INTEGER NOT NULL, due INTEGER, tags TEXT NOT NULL DEFAULT '[]');
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id TEXT NOT NULL REFERENCES predictions(id),
    kind TEXT NOT NULL, confidence REAL, outcome INTEGER, note TEXT,
    evidence TEXT, at INTEGER NOT NULL);
"""


def t(day: str) -> int:
    y, m, d = map(int, day.split("-"))
    return calendar.timegm((y, m, d, 12, 0, 0))


def make_ledger(path: Path, schema: str = SCHEMA) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(schema)
    return con


def claim(con, pid, text, conf, stated, due=None, tags="[]"):
    con.execute(
        "INSERT INTO predictions VALUES (?,?,?,?,?,?)",
        (pid, text, conf, t(stated), t(due) if due else None, tags),
    )


def event(con, pid, kind, day, conf=None, outcome=None, note=None, evidence=None):
    con.execute(
        "INSERT INTO events (prediction_id, kind, confidence, outcome, note, "
        "evidence, at) VALUES (?,?,?,?,?,?,?)",
        (pid, kind, conf, outcome, note, evidence, t(day)),
    )


def make_office(folder: Path) -> Path:
    """Four claims: revised then resolved, open and undated, voided, reopened."""
    path = folder / "home" / "office.db"
    con = make_ledger(path)
    claim(con, "a1b2c3d4", "the PR merges\n  this week", 0.7, "2026-10-01",
          "2026-10-08", '["work", "review"]')  # fmt: skip
    event(con, "a1b2c3d4", "revised", "2026-10-03", conf=0.8)
    event(con, "a1b2c3d4", "resolved", "2026-10-09", outcome=1,
          note="merged Thursday",
          evidence=json.dumps({"kind": "almanac-data", "entry_id": "tides"}))  # fmt: skip
    claim(con, "b0000001", "it rains on the fete", 0.55, "2026-10-05")
    claim(con, "c0000002", "the demo works first try", 0.6, "2026-09-20", "2026-09-21")
    event(con, "c0000002", "voided", "2026-09-22", note="claim was ambiguous")
    claim(con, "d0000003", "the bridge reopens", 0.9, "2026-10-10", "2026-10-20")
    event(con, "d0000003", "resolved", "2026-10-21", outcome=0)
    event(con, "d0000003", "reopened", "2026-10-22", note="graded too early")
    con.commit()
    con.close()
    return path


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def snapshot(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def mirrored(tmp_path) -> str:
    folder, to = tmp_path / "f", tmp_path / "m"
    make_office(folder)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    return (to / "home" / "office.db.txt").read_text(encoding="utf-8")


EXPECTED_PR = (
    "2026-10-01: the PR merges this week (a1b2c3d4)\n"
    "said 70% on 2026-10-01; due 2026-10-08; tags: work, review\n"
    "2026-10-03: revised to 80%\n"
    "2026-10-09: graded true; note: merged Thursday; "
    "evidence: entry_id=tides, kind=almanac-data\n"
    "now: resolved true, at 80%\n"
    "\n"
)


def test_a_claim_is_one_dated_paragraph_with_every_event_in_order(tmp_path):
    text = mirrored(tmp_path)
    assert EXPECTED_PR in text
    # the statement keeps its original number beside the revision
    assert "said 70%" in text and "revised to 80%" in text


def test_claims_run_oldest_statement_first_after_a_count_line(tmp_path):
    text = mirrored(tmp_path)
    assert text.startswith("oakenscroll: 4 claims (2 open, 1 resolved, 1 voided)\n\n")
    order = [
        text.index(f"({i})") for i in ("c0000002", "a1b2c3d4", "b0000001", "d0000003")
    ]
    assert order == sorted(order)


def test_absence_is_written_down(tmp_path):
    text = mirrored(tmp_path)
    assert (
        "2026-10-05: it rains on the fete (b0000001)\n"
        "said 55% on 2026-10-05; due open-ended; tags: no tags\n"
        "now: open, at 55%\n"
    ) in text


def test_a_void_keeps_its_note_and_never_reads_as_graded(tmp_path):
    text = mirrored(tmp_path)
    assert (
        "2026-09-22: voided; note: claim was ambiguous\nnow: voided, at 60%\n" in text
    )


def test_a_reopened_claim_is_open_again_and_the_grade_stays_in_the_history(tmp_path):
    text = mirrored(tmp_path)
    assert (
        "2026-10-21: graded false\n"
        "2026-10-22: reopened; note: graded too early\n"
        "now: open, at 90%\n"
    ) in text


def test_nothing_is_scored(tmp_path):
    text = mirrored(tmp_path).lower()
    for word in ("brier", "log score", "calibrat", "overconfid"):
        assert word not in text


def test_an_empty_ledger_says_so(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_ledger(folder / "office.db").close()
    assert mirror(folder, to).returncode == 0
    assert (to / "office.db.txt").read_text(
        encoding="utf-8"
    ) == "oakenscroll: 0 claims\n\n"


def test_one_claim_is_counted_in_the_singular(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    con = make_ledger(folder / "office.db")
    claim(con, "a0000009", "the tide turns", 0.5, "2026-10-02")
    con.commit()
    con.close()
    assert mirror(folder, to).returncode == 0
    text = (to / "office.db.txt").read_text(encoding="utf-8")
    assert text.startswith("oakenscroll: 1 claim (1 open)\n\n")


def test_a_v01_ledger_without_the_evidence_column_is_read(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    old = SCHEMA.replace("evidence TEXT, ", "")
    con = make_ledger(folder / "office.db", old)
    claim(con, "e0000004", "the kettle boils", 0.99, "2026-10-02")
    con.execute(
        "INSERT INTO events (prediction_id, kind, outcome, at) VALUES (?,?,?,?)",
        ("e0000004", "resolved", 1, t("2026-10-02")),
    )
    con.commit()
    con.close()
    assert mirror(folder, to).returncode == 0
    text = (to / "office.db.txt").read_text(encoding="utf-8")
    assert "2026-10-02: graded true\nnow: resolved true, at 99%\n" in text


def test_a_bad_stamp_or_odd_evidence_does_not_crash(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    con = make_ledger(folder / "office.db")
    con.execute("INSERT INTO predictions VALUES ('f0000005','odd',0.5,?,NULL,'not json')",
                (10**17,))  # fmt: skip
    con.execute(
        "INSERT INTO events (prediction_id, kind, outcome, evidence, at) "
        "VALUES ('f0000005','resolved',1,'plain words',0)"
    )
    con.commit()
    con.close()
    assert mirror(folder, to).returncode == 0
    text = (to / "office.db.txt").read_text(encoding="utf-8")
    assert "an unknown date: odd (f0000005)" in text
    assert "tags: not json" in text
    assert "1970-01-01: graded true; evidence: plain words" in text


def test_only_office_db_is_read_and_hidden_parts_are_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_office(folder)
    make_office(folder / ".hidden")
    other = make_ledger(folder / "other" / "Office.DB")
    other.commit()
    other.close()
    make_ledger(folder / "other" / "ledger.db").close()
    assert mirror(folder, to).returncode == 0
    made = sorted(p.relative_to(to).as_posix() for p in to.rglob("*") if p.is_file())
    assert made == ["home/office.db.txt", "other/Office.DB.txt"]


def test_a_file_that_is_not_a_ledger_is_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_office(folder)
    (folder / "junk").mkdir()
    (folder / "junk" / "office.db").write_bytes(b"not sqlite at all" * 20)
    make_ledger(
        folder / "other" / "office.db", "CREATE TABLE notes (id, body);"
    ).close()
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 2"


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "office.db").write_bytes(b"\xff\xfe nope")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 1"


def test_mirror_inside_folder_is_refused(tmp_path):
    folder = tmp_path / "f"
    make_office(folder)
    before = snapshot(folder)
    got = mirror(folder, folder / "out")
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert snapshot(folder) == before


def test_folder_that_is_not_a_folder_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and got.stderr.startswith("refused:")


def test_bad_arguments_print_usage(tmp_path):
    got = run(SCRIPT, "mirror", "--from", tmp_path)
    assert got.returncode == 2 and got.stderr.startswith("usage:")


def test_two_runs_give_identical_bytes_and_the_ledger_is_untouched(tmp_path):
    folder = tmp_path / "f"
    make_office(folder)
    before = snapshot(folder)
    first, second = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0

    def digests(root: Path) -> dict[str, str]:
        return {k: hashlib.sha256(v).hexdigest() for k, v in snapshot(root).items()}

    assert digests(first) == digests(second)
    assert snapshot(folder) == before  # no journal or lock file left either


def test_a_read_only_folder_is_still_read(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    path = make_office(folder)
    path.chmod(0o444)
    path.parent.chmod(0o555)
    try:
        assert mirror(folder, to).returncode == 0
    finally:
        path.parent.chmod(0o755)
    assert (to / "home" / "office.db.txt").exists()


def test_kernel_serves_a_claim_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "key",
    )
    make_office(folder)
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "does the PR merge this week")
    assert got.returncode == 0, got.stderr
    assert "the PR merges this week (a1b2c3d4)" in got.stdout
