"""pile-build: the store built behind a lock until it matches. It builds,
then finds the store current; a second build waits for the lock and then
finds nothing to do; a change made mid-build is built again; a folder that
never stops changing is reported stale after ROUNDS builds; --background
returns at once and the store appears; and a file that is not a store, or a
bad command line, is refused."""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PB = HERE / "pile_build.py"
sys.path.insert(0, str(HERE))
import pile_build  # noqa: E402

pile_store = pile_build.pile_store


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PB), *argv], capture_output=True, text=True
    )


def a_folder(tmp: Path) -> tuple[Path, Path]:
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "garden.md").write_text("Tomatoes want sun.\n")
    (folder / "roof.md").write_text("The roof estimate was 4200.\n")
    return folder, tmp / "pile.sqlite"


def test_it_builds_then_finds_the_store_current(tmp_path):
    folder, store = a_folder(tmp_path)
    got = run("--from", str(folder), "--to", str(store))
    assert got.returncode == 0 and got.stdout.startswith("built 2 passages to"), got
    assert got.stdout == f"built 2 passages to {store}\n"
    assert pile_store.stale(store, folder) is None
    again = run("--from", str(folder), "--to", str(store))
    assert again.returncode == 0 and again.stdout.startswith("current"), again


def test_a_second_build_waits_for_the_lock(tmp_path):
    folder, store = a_folder(tmp_path)
    fd = os.open(tmp_path, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        child = subprocess.Popen(
            [sys.executable, str(PB), "--from", str(folder), "--to", str(store)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )  # fmt: skip
        time.sleep(1.0)
        assert child.poll() is None and not store.exists(), "it waited"
    finally:
        os.close(fd)
    out, err = child.communicate(timeout=60)
    assert child.returncode == 0 and "waiting" in err and out.startswith("built")


def test_a_change_made_mid_build_is_built_again(tmp_path, monkeypatch):
    folder, store = a_folder(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pile_build.py", "--to", str(store)])
    real = pile_store.build
    calls = []

    def build(f, s):
        got = real(f, s)
        calls.append(1)
        if len(calls) == 1:
            (folder / "garden.md").write_text("Tomatoes want more sun.\n")
        return got

    monkeypatch.setattr(pile_store, "build", build)
    assert pile_build.settle(folder, store) == (2, 2, None)
    assert any("more sun" in c["text"] for c in pile_store.load(store, folder))


def test_a_folder_that_keeps_changing_is_stale_after_rounds(tmp_path, monkeypatch):
    folder, store = a_folder(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pile_build.py", "--to", str(store)])
    real = pile_store.build

    def build(f, s):
        got = real(f, s)
        (folder / "log.md").write_text(f"{time.time_ns()}\n")
        return got

    monkeypatch.setattr(pile_store, "build", build)
    builds, n, why = pile_build.settle(folder, store)
    assert builds == pile_build.ROUNDS == 3 and why is not None and n
    monkeypatch.setattr(pile_build, "settle", lambda f, s: (3, 2, "~1 changed"))
    assert pile_build.main(["--from", str(folder), "--to", str(store)]) == 42


def test_background_returns_at_once_and_the_store_appears(tmp_path):
    folder, store = a_folder(tmp_path)
    got = run("--from", str(folder), "--to", str(store), "--background")
    assert got.returncode == 0 and got.stdout.startswith("started"), got
    for _ in range(200):
        if pile_store.stale(store, folder) is None:
            break
        time.sleep(0.1)
    assert pile_store.stale(store, folder) is None


def test_a_folder_with_nothing_to_read_says_so(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("--from", str(empty), "--to", str(tmp_path / "pile.sqlite"))
    assert got.returncode == 42 and got.stdout.startswith("built 0 passages")


@pytest.mark.parametrize("text", ["my notes\n", ""])
def test_a_file_that_is_not_a_store_is_left_as_it_is(tmp_path, text):
    folder, store = a_folder(tmp_path)
    store.write_text(text)
    for more in ([], ["--background"]):
        got = run("--from", str(folder), "--to", str(store), *more)
        assert got.returncode == 2 and "not a pile store" in got.stderr
    assert store.read_text() == text


def test_a_bad_command_line_is_refused(tmp_path):
    folder, store = a_folder(tmp_path)
    for argv in ([], ["--from", str(folder)], ["--to", str(store)],
                 ["--from", str(folder), "--to", str(store), "--stray"],
                 ["--from", str(folder / "roof.md"), "--to", str(store)],
                 ["--from", str(folder), "--to", str(folder / "in.sqlite")],
                 ["--from", str(folder), "--to", str(tmp_path / "no" / "s")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert not (folder / "in.sqlite").exists() and not (tmp_path / "no").exists()
    assert "pile_build.py" in run().stderr
