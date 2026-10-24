"""snapshot: fetched once, as it came, with its address, time and SHA-256;
what couldn't be fetched is written down; check says what still holds."""

from __future__ import annotations

import hashlib
import http.server
import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import snapshot  # noqa: E402

SCRIPT = HERE / "snapshot.py"
NOW = ["--now", "2026-10-24T08:00:00Z"]
PAGES = {"/policy.pdf": (200, b"%PDF-1.4 old policy\n"), "/news/": (200, b"<p>Hi.</p>"),
         "/moved": (302, b""), "/gone": (404, b"no")}  # fmt: skip


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        status, body = PAGES.get(self.path, (404, b""))
        self.send_response(status)
        if status == 302:
            self.send_header("Location", "/policy.pdf")
        self.send_header(
            "Content-Type", "application/pdf" if self.path != "/news/" else "text/html"
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def site():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def logged(folder: Path) -> list[dict]:
    return [
        json.loads(s) for s in (folder / ".snapshots.jsonl").read_text().splitlines()
    ]


def test_fetch_saves_the_bytes_as_they_came_with_where_and_when(site, tmp_path):
    pile = tmp_path / "pile"
    got = run("fetch", "--url", f"{site}/policy.pdf", "--to", str(pile), *NOW)
    assert got.returncode == 0, got.stderr
    body = PAGES["/policy.pdf"][1]
    sha = hashlib.sha256(body).hexdigest()
    assert (pile / "policy.pdf").read_bytes() == body
    assert logged(pile) == [{"bytes": len(body), "fetched": "2026-10-24T08:00:00Z",
                             "file": "policy.pdf", "sha256": sha, "status": 200,
                             "type": "application/pdf", "url": f"{site}/policy.pdf"}]  # fmt: skip
    assert f"sha256 {sha}" in got.stdout


def test_a_name_already_there_is_refused_never_overwritten(site, tmp_path):
    pile = tmp_path / "pile"
    run("fetch", "--url", f"{site}/policy.pdf", "--to", str(pile), *NOW)
    got = run(
        "fetch",
        "--url",
        f"{site}/news/",
        "--to",
        str(pile),
        "--name",
        "policy.pdf",
        *NOW,
    )
    assert got.returncode == 2 and "fetched once" in got.stderr
    assert (pile / "policy.pdf").read_bytes() == PAGES["/policy.pdf"][1]
    assert len(logged(pile)) == 1
    for bad in ("../x", ".hidden", "a/b"):
        got = run(
            "fetch", "--url", f"{site}/news/", "--to", str(pile), "--name", bad, *NOW
        )
        assert got.returncode == 2, bad


def test_a_redirect_is_followed_and_said(site, tmp_path):
    got = run("fetch", "--url", f"{site}/moved", "--to", str(tmp_path), *NOW)
    assert got.returncode == 0
    assert logged(tmp_path)[0]["final_url"] == f"{site}/policy.pdf"
    assert (tmp_path / "moved").read_bytes() == PAGES["/policy.pdf"][1]


def test_an_error_or_no_answer_writes_no_file_but_its_line(site, tmp_path):
    got = run("fetch", "--url", f"{site}/gone", "--to", str(tmp_path), *NOW)
    assert got.returncode == 42 and "answered 404" in got.stdout
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens there now
    got = run(
        "fetch", "--url", f"http://127.0.0.1:{port}/x", "--to", str(tmp_path), *NOW
    )
    assert got.returncode == 42 and "couldn't reach" in got.stdout
    rows = logged(tmp_path)
    assert [r["status"] for r in rows] == [404, None]
    assert all(r["file"] is None and r["why"] for r in rows)
    assert sorted(p.name for p in tmp_path.iterdir()) == [".snapshots.jsonl"]


def test_check_says_holds_changed_missing_and_unlisted(site, tmp_path):
    run("fetch", "--url", f"{site}/policy.pdf", "--to", str(tmp_path), *NOW)
    run("fetch", "--url", f"{site}/news/", "--to", str(tmp_path), *NOW)
    got = run("check", "--in", str(tmp_path))
    assert got.returncode == 0
    assert [s.split()[:2] for s in got.stdout.splitlines()] == [
        ["holds", "news"], ["holds", "policy.pdf"]]  # fmt: skip
    (tmp_path / "policy.pdf").write_bytes(b"edited")
    (tmp_path / "news").unlink()
    (tmp_path / "extra.txt").write_text("from nowhere")
    (tmp_path / ".hidden").write_text("not read")
    got = run("check", "--in", str(tmp_path))
    assert got.returncode == 42
    assert [s.split()[:2] for s in got.stdout.splitlines()] == [
        ["missing", "news"], ["CHANGED", "policy.pdf"], ["unlisted", "extra.txt"]]  # fmt: skip
    assert run("check", "--in", str(tmp_path / "nope")).returncode == 2


def test_names_and_bad_command_lines():
    assert snapshot.name_for("https://x.org/a/b/google_privacy_policy_en.pdf") == (
        "google_privacy_policy_en.pdf"
    )
    assert (
        snapshot.name_for("https://tech-insider.org/google-privacy/")
        == "google-privacy"
    )
    assert snapshot.name_for("https://shattered.io/") == "shattered.io"
    assert snapshot.name_for("https://x.org/a?b=c d") == "a"
    assert snapshot.name_for("https:///") == "page"
    assert run("fetch", "--url", "file:///etc/passwd", "--to", "/tmp/x").returncode == 2
    assert run("fetch", "--url", "https://x.org").returncode == 2
    assert run("check", "--in", "a", "--to", "b").returncode == 2
