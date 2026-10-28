"""pile-serve: one process holds the passages and answers on a Unix socket.
Its answers are the kernel's, pile-rank's and pile-rungs' own; an edit to
the folder is seen on the next question; the socket is this user's alone;
stop, SIGTERM and --for each end it and remove the socket; a socket left by
a dead server is replaced, while a live one, or a file that is not a socket,
is refused; a bad request or command line is refused."""

from __future__ import annotations

import json
import os
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PSV = HERE / "pile_serve.py"
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-rank"))
sys.path.insert(0, str(HERE.parent / "pile-rungs"))
import kernel  # noqa: E402
import pile_rank  # noqa: E402
import pile_rungs  # noqa: E402

pytestmark = pytest.mark.skipif(
    not hasattr(socket, "AF_UNIX"), reason="no Unix sockets here"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PSV), *argv], capture_output=True, text=True
    )


@pytest.fixture
def short():
    """A folder with a short path: a socket's path has a length limit."""
    with tempfile.TemporaryDirectory(prefix="ps") as d:
        yield Path(d)


def a_folder(tmp: Path) -> Path:
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "loaf.md").write_text("2026-03-01 Baked sourdough bread on Sunday.\n")
    (folder / "again.md").write_text("More sourdough bread for the market stall.\n")
    (folder / "garden.md").write_text("Tomatoes want sun and a warm wall.\n")
    return folder


def start(folder: Path, sock: Path, *more: str) -> subprocess.Popen:
    p = subprocess.Popen(
        [sys.executable, str(PSV), "serve", "--from", str(folder),
         "--to", str(sock), *more],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )  # fmt: skip
    for _ in range(300):  # answering, not just there: a dead socket is there
        if p.poll() is not None:
            break
        s = socket.socket(socket.AF_UNIX)
        try:
            s.connect(str(sock))
            return p
        except OSError:
            time.sleep(0.05)
        finally:
            s.close()
    raise AssertionError(p.communicate(timeout=5))


def ask(sock: Path, *argv: str) -> tuple[int, dict]:
    got = run("ask", "--at", str(sock), *argv)
    assert got.returncode in (0, 42), got.stderr
    return got.returncode, json.loads(got.stdout)


def raw(sock: Path, line: bytes) -> dict:
    s = socket.socket(socket.AF_UNIX)
    s.connect(str(sock))
    s.sendall(line)
    got = b""
    while not got.endswith(b"\n"):
        got += s.recv(65536)
    s.close()
    return json.loads(got)


def test_its_answers_are_each_ranks_own(short):
    folder, sock = a_folder(short), short / "s"
    p = start(folder, sock)
    try:
        pile = kernel.chunks(folder)
        code, row = ask(sock, "tomatoes", "sun")
        assert code == 0 and row["ranked_by"] == "kernel"
        assert [s["id"] for s in row["served"]] == [
            c["id"] for c in kernel.rank(pile, "tomatoes sun", top=5)
        ]
        assert row["read_from"] == "folder" and row["reads"] == 1
        _, row = ask(sock, "--rank", "pile-rank", "--top", "2", "sourdough", "bread")
        want = pile_rank.Ranker(pile).rank("sourdough bread", 2)
        assert [s["id"] for s in row["served"]] == [c["id"] for c, *_ in want]
        assert [s["rank"] for s in row["served"]] == [1, 2]
        assert row["served"][0]["phrases"] == ["sourdough bread"]
        assert "score" in row["served"][0]
        q = "where is the sourdough bread recipe card kept"
        _, row = ask(sock, "--rank", "rungs", *q.split())
        rung, rungs, _ = pile_rungs.climb(pile, q, 5)
        assert row["rung"] == rung == "phrases" and row["rungs"] == rungs
        code, row = ask(sock, "kayak")
        assert code == 42 and row["state"] == "empty" and row["served"] == []
    finally:
        assert run("stop", "--at", str(sock)).returncode == 0
        assert p.wait(timeout=10) == 0
    assert not sock.exists() and "stopped" in p.stdout.read()


def test_an_edit_is_seen_on_the_next_question(short):
    folder, sock = a_folder(short), short / "s"
    p = start(folder, sock)
    try:
        _, row = ask(sock, "kayak")
        assert row["served"] == [] and row["reads"] == 1
        (folder / "boat.md").write_text("The kayak hangs in the shed.\n")
        _, row = ask(sock, "kayak")
        assert [s["where"] for s in row["served"]] == ["boat.md:1"]
        assert row["reads"] == 2
        _, row = ask(sock, "kayak")
        assert row["reads"] == 2, "nothing changed, nothing read again"
    finally:
        run("stop", "--at", str(sock))
        p.wait(timeout=10)


def test_the_socket_is_this_users_alone(short):
    folder, sock = a_folder(short), short / "s"
    p = start(folder, sock)
    try:
        mode = os.stat(sock).st_mode
        assert stat.S_ISSOCK(mode) and stat.S_IMODE(mode) & 0o077 == 0
    finally:
        run("stop", "--at", str(sock))
        p.wait(timeout=10)


def test_sigterm_and_idle_each_end_it_and_remove_the_socket(short):
    folder, sock = a_folder(short), short / "s"
    p = start(folder, sock)
    p.send_signal(signal.SIGTERM)
    assert p.wait(timeout=10) == 0 and not sock.exists()
    p = start(folder, sock, "--for", "0.5")
    assert p.wait(timeout=10) == 0 and not sock.exists()


def test_a_bad_request_is_refused_and_the_server_goes_on(short):
    folder, sock = a_folder(short), short / "s"
    p = start(folder, sock)
    try:
        for line, why in (
            (b"not json\n", "one JSON line"),
            (b"[1]\n", "a JSON object"),
            (b'{"question": ""}\n', "a question is text"),
            (b'{"question": "x", "rank": "magic"}\n', "a rank is one of"),
            (b'{"question": "x", "top": 0}\n', "top is a whole number"),
            (b'{"question": "x", "top": true}\n', "top is a whole number"),
        ):
            assert why in raw(sock, line)["refused"], line
        s = socket.socket(socket.AF_UNIX)
        s.connect(str(sock))
        s.close()  # a client that says nothing and goes
        assert ask(sock, "tomatoes")[0] == 0
    finally:
        run("stop", "--at", str(sock))
        p.wait(timeout=10)


def test_a_dead_servers_socket_is_replaced_a_live_one_is_not(short):
    folder, sock = a_folder(short), short / "s"
    dead = socket.socket(socket.AF_UNIX)
    dead.bind(str(sock))
    dead.close()  # its socket file stays, and nothing answers it
    p = start(folder, sock)
    try:
        got = run("serve", "--from", str(folder), "--to", str(sock))
        assert got.returncode == 2 and "already answers" in got.stderr
        assert ask(sock, "tomatoes")[0] == 0
    finally:
        run("stop", "--at", str(sock))
        p.wait(timeout=10)


def test_losing_the_address_to_another_server_is_refused(short, monkeypatch):
    folder, sock = a_folder(short), short / "s"
    taken = socket.socket(socket.AF_UNIX)
    taken.bind(str(sock))
    sys.path.insert(0, str(HERE))
    import pile_serve

    try:  # as if another server bound it between the check and the bind
        monkeypatch.setattr(sys, "argv", ["pile_serve.py", "--to", str(sock)])
        assert pile_serve.serve(folder, str(sock), None, 0) == 2
    finally:
        taken.close()
    assert sock.exists(), "the other server's socket is left alone"


def test_a_file_that_is_not_a_socket_is_left_as_it_is(short):
    folder, notes = a_folder(short), short / "notes.txt"
    notes.write_text("mine\n")
    got = run("serve", "--from", str(folder), "--to", str(notes))
    assert got.returncode == 2 and "not a socket" in got.stderr
    assert notes.read_text() == "mine\n"


def test_nothing_serving_is_refused(short):
    for argv in (["ask", "--at", str(short / "none"), "x"],
                 ["stop", "--at", str(short / "none")]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "nothing serves" in got.stderr


def test_a_bad_command_line_is_refused(short):
    folder, sock = a_folder(short), str(short / "s")
    long = str(short / ("x" * 120))
    for argv in ([], ["serve"], ["listen", "--at", sock],
                 ["serve", "--from", str(folder)],
                 ["serve", "--from", str(folder), "--to", sock, "--stray"],
                 ["serve", "--from", str(folder), "--to", sock, "word"],
                 ["serve", "--from", str(folder), "--to", sock, "--for", "x"],
                 ["serve", "--from", str(folder), "--to", sock, "--for", "-1"],
                 ["serve", "--from", str(folder), "--to", sock, "--store", ""],
                 ["serve", "--from", str(folder), "--to", long],
                 ["serve", "--from", str(folder / "loaf.md"), "--to", sock],
                 ["serve", "--from", str(folder), "--at", sock],
                 ["ask", "--at", sock], ["ask", "--at", sock, "--rank", "x", "q"],
                 ["ask", "--at", sock, "--top", "0", "q"],
                 ["ask", "--at", sock, "--top", "x", "q"],
                 ["stop", "--at", sock, "now"], ["stop", "--to", sock]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert not os.path.lexists(sock) and not os.path.lexists(long)
    assert "pile_serve.py" in run().stderr
