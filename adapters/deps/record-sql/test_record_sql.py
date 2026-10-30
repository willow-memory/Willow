"""record-sql: the record as two tables in memory, its chain checked first;
SQL over them with DuckDB's way out locked shut, so nothing is written; and a
refusal, never a quiet skip, without DuckDB."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "record_sql.py"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv],
                          capture_output=True, text=True)  # fmt: skip


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text("The dentist is on Tuesday at 3pm.\n")
    (pile / "car.txt").write_text("The car service is due in March.\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"),
      "--now", "2026-02-27T09:00:00Z")  # fmt: skip
    got = k("bite", "--box", str(b), "--now", "2026-03-02T09:13:00Z", "dentist day")
    served = json.loads(got.stdout)["served"]
    k("bite", "--box", str(b), "--now", "2026-03-05T08:00:00Z", "car service")
    k("bite", "--box", str(b), "--now", "2026-04-01T08:00:00Z", "passport")
    k("bite", "--box", str(b), "--now", "2026-04-02T08:00:00Z", "dentist day")
    rows = [{"path": "dentist.md", "data": "Tuesday 3pm", "cites": [served[0]["id"]],
             "claim": "the note"}]  # fmt: skip
    (tmp_path / "s.jsonl").write_text(json.dumps(rows[0]) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"),
      "--now", "2026-04-02T08:01:00Z")  # fmt: skip
    subj = json.loads((b / "record.jsonl").read_text().splitlines()[-1])["subject"]
    got = k("seal", "--box", str(b), subj, "--now", "2026-03-31T09:21:00Z")
    assert got.returncode == 0, got.stderr
    return b


def test_how_many_were_asked_in_march(box):
    got = run("--box", str(box), "SELECT count(*) AS asked FROM record "
              "WHERE kind = 'bite' AND ts >= '2026-03-01' AND ts < '2026-04-01'")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout == "asked\n2\n(1 row)\n"


def test_each_kind_by_month(box):
    got = run("--box", str(box), "SELECT kind, month(ts) AS m, count(*) AS c "
              "FROM record GROUP BY ALL ORDER BY kind, m")  # fmt: skip
    assert got.stdout.splitlines() == [
        "kind | m | c", "bite | 3 | 2", "bite | 4 | 2", "boot | 2 | 1",
        "proposal | 4 | 1", "seal | 3 | 1", "(5 rows)",
    ]  # fmt: skip


def test_what_was_served_is_a_table_of_its_own(box):
    got = run("--box", str(box), "SELECT \"where\", count(*) AS times FROM served "
              "GROUP BY ALL ORDER BY times DESC, \"where\"")  # fmt: skip
    assert got.stdout.splitlines() == [
        "where | times",
        "dentist.txt:1 | 2",
        "car.txt:1 | 1",
        "(2 rows)",
    ]


def test_a_field_holding_a_list_is_json(box):
    got = run("--box", str(box), "SELECT json_array_length(served) FROM record "
              "WHERE n = 1")  # fmt: skip
    assert got.stdout.splitlines()[1] == "1"
    tables = run("--box", str(box), "--tables")
    assert tables.returncode == 0
    assert "record (7 rows)" in tables.stdout and "  ts TIMESTAMP" in tables.stdout
    assert "  served JSON" in tables.stdout and "served (3 rows)" in tables.stdout


def test_no_rows_is_42_and_bad_sql_is_refused(box):
    none = run("--box", str(box), "SELECT * FROM record WHERE kind = 'decline'")
    assert none.returncode == 42 and none.stdout.endswith("(0 rows)\n")
    bad = run("--box", str(box), "SELEC nonsense")
    assert bad.returncode == 2 and bad.stderr.startswith("refused:")


def test_the_way_out_is_locked_and_nothing_is_written(box, tmp_path):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for sql in (
        f"COPY record TO '{tmp_path / 'out.csv'}'",
        f"ATTACH '{tmp_path / 'other.db'}'",
        f"SELECT * FROM read_text('{box / 'kernel.json'}')",
        "SET enable_external_access = true",
        "INSTALL httpfs",
    ):
        got = run("--box", str(box), sql)
        assert got.returncode == 2, sql
    made = run("--box", str(box), "CREATE TABLE t AS SELECT 1 AS x; SELECT x FROM t")
    assert made.returncode == 0 and made.stdout.splitlines()[1] == "1"
    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_a_record_that_doesnt_verify_is_refused(box):
    rec = box / "record.jsonl"
    rec.write_text(
        rec.read_text().replace("2026-04-01T08:00:00Z", "2026-04-01T08:00:01Z")
    )
    got = run("--box", str(box), "SELECT 1")
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_refusals(box, tmp_path):
    for argv in ([], ["--box", str(box)], ["--box", str(box), "--nope"],
                 ["--box", str(tmp_path), "SELECT 1"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv


def test_without_duckdb_it_refuses_and_names_the_install(box, tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "duckdb.py").write_text("raise ImportError('hidden')\n")
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "--box", str(box), "SELECT 1"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
