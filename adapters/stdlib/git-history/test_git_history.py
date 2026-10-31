"""git-history: each commit a dated passage with its message and diff;
git is called, never linked."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "git_history.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def git(cwd: Path, *args: str, env: dict | None = None) -> None:
    base = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "Ada",
        "GIT_AUTHOR_EMAIL": "ada@example",
        "GIT_COMMITTER_NAME": "Ada",
        "GIT_COMMITTER_EMAIL": "ada@example",
        "LC_ALL": "C",
    }
    if env:
        base.update(env)
    subprocess.run(
        ["git", "-c", "init.defaultBranch=main", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=base,
    )


def make_repo(folder: Path) -> None:
    folder.mkdir()
    git(folder, "init")
    (folder / "limit.txt").write_text("retry=3\n", encoding="utf-8")
    dated = {
        "GIT_AUTHOR_DATE": "2026-10-01T12:00:00 +0000",
        "GIT_COMMITTER_DATE": "2026-10-01T12:00:00 +0000",
    }
    git(folder, "add", "limit.txt", env=dated)
    git(folder, "commit", "-m", "set the retry limit", env=dated)
    (folder / "limit.txt").write_text("retry=5\n", encoding="utf-8")
    later = {
        "GIT_AUTHOR_DATE": "2026-10-02T12:00:00 +0000",
        "GIT_COMMITTER_DATE": "2026-10-02T12:00:00 +0000",
    }
    git(folder, "add", "limit.txt", env=later)
    git(folder, "commit", "-m", "raise the retry limit", env=later)


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def test_each_commit_is_a_dated_passage_with_its_diff(tmp_path):
    folder, to = tmp_path / "repo", tmp_path / "m"
    make_repo(folder)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    files = sorted(to.glob("*.txt"))
    assert len(files) == 2
    first, second = (p.read_text(encoding="utf-8") for p in files)
    # oldest first by hash file name is not date order; read both
    texts = first + "\n" + second
    assert "date: 2026-10-01" in texts
    assert "date: 2026-10-02" in texts
    assert "subject: set the retry limit" in texts
    assert "subject: raise the retry limit" in texts
    assert "-retry=3" in texts and "+retry=5" in texts
    assert "Ada" not in texts


def test_a_folder_with_no_git_history_is_nothing_there(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "note.txt").write_text("not a repo\n", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 0"


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "repo"
    make_repo(folder)
    a, b = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, a).returncode == 0
    assert mirror(folder, b).returncode == 0
    left = {p.name: hashlib.sha256(p.read_bytes()).digest() for p in a.glob("*.txt")}
    right = {p.name: hashlib.sha256(p.read_bytes()).digest() for p in b.glob("*.txt")}
    assert left == right


def test_kernel_serves_a_commit_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "repo",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "k",
    )
    make_repo(folder)
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "raise the retry limit")
    assert got.returncode in (0, 42), got.stderr
    assert "retry=5" in got.stdout or "raise the retry limit" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
    folder = tmp_path / "f"
    folder.mkdir()
    got = mirror(folder, folder / "out")
    assert got.returncode == 2 and "inside one another" in got.stderr
