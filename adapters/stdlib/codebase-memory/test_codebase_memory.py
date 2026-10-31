"""codebase-memory: each function a paragraph from a copy of the graph;
the original is only read."""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "codebase_memory.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write_graph(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE symbols (
            fqn TEXT PRIMARY KEY, name TEXT, kind TEXT,
            file_path TEXT, start_line INTEGER
        );
        CREATE TABLE edges (
            source_fqn TEXT, target_fqn TEXT, edge_type TEXT
        );
        INSERT INTO symbols VALUES
            ('mod.run', 'run', 'function', 'mod.py', 10),
            ('mod.Helper', 'Helper', 'class', 'mod.py', 1),
            ('mod.Helper.work', 'work', 'method', 'mod.py', 4);
        INSERT INTO edges VALUES
            ('mod.run', 'mod.Helper.work', 'import'),
            ('mod.Helper.work', 'mod.run', 'import');
        """
    )
    con.commit()
    con.close()


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def test_each_function_is_a_paragraph_with_its_edges(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    write_graph(folder / "graph.db")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "graph.db.txt").read_text(encoding="utf-8")
    assert text.startswith("code graph: 2 functions\n")
    assert "run (function)\nfile: mod.py:10\nname: mod.run\n" in text
    assert "edges: import mod.Helper.work" in text
    assert "Helper (class)" not in text


def test_a_function_with_no_short_name_uses_its_fqn(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    con = sqlite3.connect(folder / "graph.db")
    con.executescript(
        """
        CREATE TABLE symbols (
            fqn TEXT PRIMARY KEY, name TEXT, kind TEXT,
            file_path TEXT, start_line INTEGER
        );
        CREATE TABLE edges (
            source_fqn TEXT, target_fqn TEXT, edge_type TEXT
        );
        INSERT INTO symbols VALUES
            ('mod.anon', '', 'function', 'mod.py', 3);
        """
    )
    con.commit()
    con.close()
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "graph.db.txt").read_text(encoding="utf-8")
    assert "mod.anon (function)\nfile: mod.py:3\n" in text
    assert text.splitlines()[2] == "mod.anon (function)"


def test_a_sqlite_file_that_is_not_a_graph_is_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    write_graph(folder / "graph.db")
    other = sqlite3.connect(folder / "notes.db")
    other.execute("CREATE TABLE notes (id INTEGER)")
    other.commit()
    other.close()
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 1"


def test_hidden_graphs_are_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / ".cache").mkdir(parents=True)
    write_graph(folder / ".cache" / "graph.db")
    folder.mkdir(exist_ok=True)
    write_graph(folder / "graph.db")
    got = mirror(folder, to)
    assert got.returncode == 0
    made = [p.name for p in to.rglob("*.txt")]
    assert made == ["graph.db.txt"]


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    write_graph(folder / "graph.db")
    before = (folder / "graph.db").read_bytes()
    a, b = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, a).returncode == 0
    assert mirror(folder, b).returncode == 0
    assert (
        hashlib.sha256((a / "graph.db.txt").read_bytes()).digest()
        == hashlib.sha256((b / "graph.db.txt").read_bytes()).digest()
    )
    assert (folder / "graph.db").read_bytes() == before


def test_kernel_serves_a_function_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "k",
    )
    folder.mkdir()
    write_graph(folder / "graph.db")
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "run function file mod")
    assert got.returncode == 0, got.stderr
    assert "mod.py:10" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
