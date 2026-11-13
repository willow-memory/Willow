"""ai-code-tracking: commits and conversations mirrored, code kept out, report right."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "ai_code_tracking.py"
EMPTY = {"commits": 0}

SCHEMA = """
CREATE TABLE ai_code_hashes (hash TEXT, source TEXT, fileExtension TEXT,
    fileName TEXT, requestId TEXT, conversationId TEXT, timestamp INTEGER,
    model TEXT, createdAt INTEGER);
CREATE TABLE scored_commits (commitHash TEXT, branchName TEXT, scoredAt INTEGER,
    linesAdded INTEGER, linesDeleted INTEGER, tabLinesAdded INTEGER,
    tabLinesDeleted INTEGER, composerLinesAdded INTEGER,
    composerLinesDeleted INTEGER, humanLinesAdded INTEGER,
    humanLinesDeleted INTEGER, blankLinesAdded INTEGER,
    blankLinesDeleted INTEGER, commitMessage TEXT, commitDate TEXT,
    v1AiPercentage TEXT, v2AiPercentage TEXT);
CREATE TABLE tracked_file_content (gitPath TEXT, content TEXT,
    conversationId TEXT, model TEXT, fileExtension TEXT, createdAt INTEGER);
"""
T1 = 1_779_072_120_000  # 2026-05-18 02:42 UTC
T2 = T1 + 3_600_000


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_db(path: Path, rows: bool = True) -> None:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    if rows:
        con.executemany(
            "INSERT INTO ai_code_hashes VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    "HASH-A",
                    "composer",
                    "py",
                    "SECRET-NAME.py",
                    "r1",
                    "conv-1",
                    T1,
                    "gpt-x",
                    T1,
                ),
                (
                    "HASH-B",
                    "tab",
                    "py",
                    "SECRET-NAME.py",
                    "r2",
                    "conv-1",
                    T2,
                    "gpt-x",
                    T2,
                ),
                (
                    "HASH-C",
                    "composer",
                    "md",
                    "notes.md",
                    "r3",
                    "conv-1",
                    T2,
                    "claude-y",
                    T2,
                ),
                ("HASH-D", "composer", "ts", "a.ts", "r4", "conv-2", T2, "gpt-x", T2),
            ],
        )
        con.executemany(
            "INSERT INTO scored_commits VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    "c0ffee1",
                    "main",
                    T1,
                    10,
                    2,
                    3,
                    0,
                    5,
                    1,
                    2,
                    1,
                    0,
                    0,
                    "fix the\ntomato bed",
                    "2026-05-17T23:02:29-06:00",
                    "80.0",
                    "75.5",
                ),
                (
                    "c0ffee2",
                    "dev",
                    T2,
                    20,
                    4,
                    1,
                    1,
                    4,
                    2,
                    15,
                    1,
                    0,
                    0,
                    "water the beans",
                    "2026-06-02T10:00:00+00:00",
                    "20.0",
                    "25.0",
                ),
            ],
        )
        con.execute(
            "INSERT INTO tracked_file_content VALUES "
            "('p/x.py', 'CODE-SHOULD-NOT-APPEAR', 'conv-1', 'gpt-x', 'py', 1)"
        )
    con.commit()
    con.close()


def mirror(src: Path, to: Path) -> subprocess.CompletedProcess:
    return run("mirror", "--from", src, "--to", to)


def test_commits_and_conversations_are_mirrored_and_code_stays_out(tmp_path):
    db, to = tmp_path / "ai-code-tracking.db", tmp_path / "m"
    make_db(db)
    got = mirror(db, to)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 0"
    text = (to / "ai-code-tracking.db.txt").read_text(encoding="utf-8")
    assert text.startswith("ai-code-tracking: 2 scored commits, 2 conversations\n")
    assert (
        "commit c0ffee1 on main\ndate: 2026-05-17\nmessage: fix the tomato bed" in text
    )
    assert "by tab: added 3, deleted 0" in text
    assert "by composer: added 5, deleted 1" in text
    assert "by human: added 2, deleted 1" in text
    assert "AI percentage: v1 80.0, v2 75.5" in text
    assert "commit c0ffee2 on dev" in text
    assert "conversation conv-1: the AI wrote 3 chunks" in text
    assert "models: claude-y, gpt-x" in text
    assert "first: 2026-05-18 02:42\nlast: 2026-05-18 03:42" in text
    assert "by file extension: py 2, md 1" in text
    assert "conversation conv-2: the AI wrote 1 chunks" in text
    for never in ("CODE-SHOULD-NOT-APPEAR", "HASH-A", "SECRET-NAME", "p/x.py"):
        assert never not in text


def test_a_folder_is_walked_and_a_non_matching_file_is_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "sub").mkdir(parents=True)
    make_db(folder / "sub" / "t.db")
    other = sqlite3.connect(folder / "other.db")
    other.execute("CREATE TABLE notes (a TEXT)")
    other.commit()
    other.close()
    (folder / "plain.db").write_text("not sqlite at all", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 2"
    assert (to / "sub" / "t.db.txt").is_file()
    assert not (to / "other.db.txt").exists()


def test_a_database_with_empty_tables_is_skipped(tmp_path):
    db = tmp_path / "e.db"
    make_db(db, rows=False)
    got = mirror(db, tmp_path / "m")
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {tmp_path / 'm'}; skipped 1"


def test_the_original_is_byte_identical_and_runs_agree(tmp_path):
    db = tmp_path / "t.db"
    make_db(db)
    before = hashlib.sha256(db.read_bytes()).digest()
    a, b = tmp_path / "m1", tmp_path / "m2"
    assert mirror(db, a).returncode == 0
    assert mirror(db, b).returncode == 0
    assert run("report", "--from", db).returncode == 0
    assert hashlib.sha256(db.read_bytes()).digest() == before
    assert (a / "t.db.txt").read_bytes() == (b / "t.db.txt").read_bytes()
    assert not list(tmp_path.glob("t.db-*")), "no journal or wal left beside it"


def test_a_long_mirror_goes_on_in_a_second_file(tmp_path):
    db = tmp_path / "big.db"
    make_db(db, rows=False)
    con = sqlite3.connect(db)
    con.executemany(
        "INSERT INTO scored_commits VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                f"c{i:06d}",
                "main",
                T1,
                1,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                "x" * 280,
                "2026-05-17T00:00:00+00:00",
                "1.0",
                "1.0",
            )
            for i in range(2400)
        ],
    )
    con.commit()
    con.close()
    to = tmp_path / "m"
    assert mirror(db, to).returncode == 0
    first, second = to / "big.db.txt", to / "big.db.2.txt"
    assert first.stat().st_size < 1_000_000 and second.is_file()
    assert "commit c000000" in first.read_text(encoding="utf-8")
    assert "commit c002399" in second.read_text(encoding="utf-8")


def test_report_totals_models_and_months(tmp_path):
    db = tmp_path / "t.db"
    make_db(db)
    got = run("report", "--from", db)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[0] == (
        "ai-code-tracking: populated, 2 commits scored; lines added by tab 4, "
        "composer 9, human 17"
    )
    doc = json.loads(run("report", "--from", db, "--json").stdout)
    groups = {
        g["name"]: {r["where"]: r["what"] for r in g["rows"]} for g in doc["groups"]
    }
    assert groups["totals"]["lines added"] == "30"  # tab 4 + composer 9 + human 17
    assert groups["totals"]["lines added by tab"] == "4"
    assert groups["totals"]["lines added by composer"] == "9"
    assert groups["totals"]["lines added by human"] == "17"
    assert groups["totals"]["AI-written chunks"] == "4"
    assert groups["by model"]["gpt-x"] == "3 chunks in 2 conversations"
    assert groups["by model"]["claude-y"] == "1 chunks in 1 conversations"
    assert groups["by month"]["2026-05"].startswith(
        "1 commits; added: tab 3, composer 5, human 2"
    )
    assert groups["by month"]["2026-06"].startswith(
        "1 commits; added: tab 1, composer 4, human 15"
    )


def test_report_on_empty_tables_is_empty_and_on_another_file_unreachable(tmp_path):
    db = tmp_path / "e.db"
    make_db(db, rows=False)
    got = run("report", "--from", db)
    assert got.returncode == 0
    assert got.stdout.startswith("ai-code-tracking: empty, ")
    junk = tmp_path / "junk.db"
    junk.write_text("not sqlite", encoding="utf-8")
    got = run("report", "--from", junk)
    assert got.returncode == 42
    assert got.stdout.startswith("ai-code-tracking: unreachable, ")


def test_bad_command_lines_are_refused(tmp_path):
    db = tmp_path / "t.db"
    make_db(db)
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", db],
        ["mirror", "--from", db, "--to"],
        ["report"],
        ["report", "--from", db, "--to", tmp_path / "x"],
        ["nonsense", "--from", db],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "usage:" in got.stderr, argv
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
    got = run("report", "--from", tmp_path / "missing")
    assert got.returncode == 2 and "refused:" in got.stderr
    got = mirror(tmp_path, tmp_path / "inside")
    assert got.returncode == 2 and "inside one another" in got.stderr
    assert not (tmp_path / "inside").exists()


def test_mirror_answers_json_as_a_report_since_a_stack_asks_for_it(tmp_path):
    """A stack asks every step whose card says output: report for --json;
    mirror answered that with its usage line until this held it."""
    db = tmp_path / "ai-code-tracking.db"
    make_db(db)
    got = run("mirror", "--from", str(db), "--to", str(tmp_path / "m"), "--json")
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["addon"] == "ai-code-tracking" and doc["state"] == "populated"
    assert doc["said"].startswith("wrote 1 files")
    assert (tmp_path / "m").is_dir()


def _wal(path: Path) -> None:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.close()


def test_a_wal_database_is_read_and_nothing_is_written_beside_it(tmp_path):
    """A database in WAL mode opened with mode=ro alone gets a -shm and -wal
    file beside it: a write to the person's folder. Opened immutable, none."""
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    db = folder / "ai-code-tracking.db"
    make_db(db)
    _wal(db)
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
    assert any(p.is_file() for p in to.rglob("*"))
