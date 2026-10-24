"""policy-watch: each run a dated copy, and against the last copy of the
same address: first, unchanged, same words, or what changed, sentence by
sentence; a PDF by its bytes, a failed fetch written down."""

from __future__ import annotations

import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "policy_watch.py"
PAGE = {"/terms": ("text/html", b"<p>We keep data. We delete it on request.</p>")}


class Site(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        kind, body = PAGE.get(self.path, ("text/plain", b""))
        self.send_response(200 if self.path in PAGE else 404)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def site():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Site)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def run(url: str, folder: Path, day: int) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--url", url, "--to", str(folder),
                           "--now", f"2026-10-{day:02d}T09:00:00Z"],
                          capture_output=True, text=True)  # fmt: skip


def test_first_unchanged_same_words_then_changed(site, tmp_path):
    url = f"{site}/terms"
    PAGE["/terms"] = ("text/html", b"<p>We keep data. We delete it on request.</p>")
    got = run(url, tmp_path, 16)
    assert (
        got.returncode == 0
        and "first copy      20261016T090000Z-terms saved" in got.stdout
    )
    got = run(url, tmp_path, 17)
    assert (
        got.returncode == 0
        and "unchanged       the same bytes as 20261016T090000Z-terms" in got.stdout
    )
    PAGE["/terms"] = (
        "text/html",
        b"<div><p>We keep data.  We delete it on request.</p></div>",
    )
    got = run(url, tmp_path, 18)
    assert got.returncode == 0 and got.stdout.splitlines()[-1].startswith("same words")
    PAGE["/terms"] = (
        "text/html",
        b"<p>We keep data, unless asked. We sell nothing.</p>",
    )
    got = run(url, tmp_path, 19)
    lines = got.stdout.splitlines()
    assert got.returncode == 42
    assert lines[1] == "changed         since 20261018T090000Z-terms:"
    assert lines[2].startswith("reworded  1 -> 1")
    assert lines[3:5] == ["  - We keep data.", "  + We keep data, unless asked."]
    assert lines[5] == "added     1   We sell nothing."
    assert lines[6] == "removed   1   We delete it on request."
    PAGE["/terms"] = ("text/html", b"<p>We keep data, unless asked.</p>")
    got = run(url, tmp_path, 20)  # only a sentence gone is a change too
    assert got.returncode == 42
    assert got.stdout.splitlines()[2:] == ["removed   1   We sell nothing."]
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == [".snapshots.jsonl"] + [
        f"202610{d}T090000Z-terms" for d in (16, 17, 18, 19, 20)
    ]


def test_a_pdf_is_compared_by_its_bytes(site, tmp_path):
    PAGE["/p.pdf"] = ("application/pdf", b"%PDF-1.4 \xff\xfe one")
    run(f"{site}/p.pdf", tmp_path, 16)
    PAGE["/p.pdf"] = ("application/pdf", b"%PDF-1.4 \xff\xfe two")
    got = run(f"{site}/p.pdf", tmp_path, 17)
    assert got.returncode == 42 and "it isn't text" in got.stdout


def test_a_failed_fetch_is_written_down_and_compared_with_nothing(site, tmp_path):
    got = run(f"{site}/gone", tmp_path, 16)
    assert got.returncode == 42 and "answered 404" in got.stdout
    row = json.loads((tmp_path / ".snapshots.jsonl").read_text())
    assert row["file"] is None and row["status"] == 404
    PAGE["/gone"] = ("text/plain", b"Back.")
    got = run(f"{site}/gone", tmp_path, 17)
    assert got.returncode == 0 and "first copy" in got.stdout  # a failure isn't a copy


def test_bad_command_lines_are_refused(tmp_path):
    for argv in ([], ["--url", "ftp://x", "--to", str(tmp_path)], ["--url", "https://x.org"],
                 ["--url", "https://x.org", "--to", str(tmp_path), "--name", "n"]):  # fmt: skip
        got = subprocess.run(
            [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
        )
        assert got.returncode == 2, argv
    assert not any(tmp_path.iterdir())
