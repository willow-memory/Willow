"""wayback: the latest capture in a window, saved as it was archived with its
own snapshot line, and compared; no capture and no answer are said as such."""

from __future__ import annotations

import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "wayback.py"
NOW = ["--now", "2026-10-24T09:00:00Z"]
PAGE = "https://policies.example/privacy.pdf"
#: the archive's index: header, then (timestamp, status) rows
INDEX = [["timestamp", "statuscode"], ["20260930090000", "200"], ["20261005120000", "200"],
         ["20261012080000", "200"], ["20261013000000", "404"], ["20261017100000", "200"]]  # fmt: skip
BODIES = {"20261012080000": b"%PDF old policy", "20260930090000": b"%PDF older",
          "20261005120000": b"%PDF old policy, earlier"}  # fmt: skip
SEEN: list[str] = []


class Archive(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        SEEN.append(self.path)
        parts = urllib.parse.urlsplit(self.path)
        if parts.path == "/cdx/search/cdx":
            q = urllib.parse.parse_qs(parts.query)
            body = json.dumps(INDEX if q["url"] == [PAGE] else []).encode()
            if q["url"] == ["https://broken.example/"]:
                body = b"<html>busy</html>"
        else:
            ts = parts.path.split("/")[2].removesuffix("id_")
            body = BODIES.get(ts, b"")
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def archive():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Archive)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    SEEN.clear()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def run(base: str, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True,
                          text=True, env={**os.environ, "WILLOW_WAYBACK": base})  # fmt: skip


def test_the_latest_capture_in_the_window_is_saved_and_compared(archive, tmp_path):
    mine = tmp_path / "old.pdf"
    mine.write_bytes(b"%PDF old policy")
    got = run(archive, "find", "--url", PAGE, "--to", str(tmp_path / "w"), "--after", "20261001",
              "--before", "20261016", "--against", str(mine), "--name", "old.wayback.pdf", *NOW)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0].startswith("saved     old.wayback.pdf   15 bytes")
    assert got.stdout.splitlines()[1] == (
        f"capture   20261012080000 of {PAGE}   saved as old.wayback.pdf"
    )
    assert got.stdout.splitlines()[-1].startswith("same bytes as old.pdf   sha256 ")
    assert SEEN[-1] == f"/web/20261012080000id_/{PAGE}"  # as archived, no banner
    row = json.loads((tmp_path / "w" / ".snapshots.jsonl").read_text())
    assert row["wayback"] == "20261012080000" and row["of"] == PAGE
    assert row["url"] == f"{archive}/web/20261012080000id_/{PAGE}"


def test_different_bytes_are_said_with_both_hashes(archive, tmp_path):
    mine = tmp_path / "old.pdf"
    mine.write_bytes(b"%PDF something else")
    got = run(archive, "find", "--url", PAGE, "--to", str(tmp_path / "w"), "--before", "20261006",
              "--against", str(mine), *NOW)  # fmt: skip
    assert got.returncode == 42 and "DIFFERS from old.pdf" in got.stdout
    assert "20261005120000" in got.stdout  # the latest before the 6th
    assert (tmp_path / "w" / "wayback-privacy.pdf").read_bytes() == BODIES[
        "20261005120000"
    ]


def test_no_capture_and_no_answer_are_not_differences(archive, tmp_path):
    got = run(
        archive,
        "find",
        "--url",
        PAGE,
        "--to",
        str(tmp_path),
        "--after",
        "20261018",
        *NOW,
    )
    assert got.returncode == 42 and got.stdout.startswith("no capture of")
    got = run(
        archive, "find", "--url", "https://broken.example/", "--to", str(tmp_path), *NOW
    )
    assert got.returncode == 42 and "not JSON" in got.stdout
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    dead = f"http://127.0.0.1:{s.getsockname()[1]}"
    s.close()
    got = run(dead, "find", "--url", PAGE, "--to", str(tmp_path), *NOW)
    assert got.returncode == 42 and got.stdout.startswith("couldn't reach the archive")
    assert not any(tmp_path.iterdir())


def test_bad_command_lines_are_refused(archive, tmp_path):
    for argv in (["find", "--url", PAGE], ["find", "--url", "ftp://x", "--to", str(tmp_path)],
                 ["find", "--url", PAGE, "--to", str(tmp_path), "--after", "2026-10-01"],
                 ["find", "--url", PAGE, "--to", str(tmp_path), "--against", str(tmp_path / "no")],
                 ["find", "--url", PAGE, "--to", str(tmp_path), "--near", "x"]):  # fmt: skip
        assert run(archive, *argv).returncode == 2, argv
    assert SEEN == []
