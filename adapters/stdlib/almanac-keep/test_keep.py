"""almanac-keep: the first permitted copy that answers, publisher first for a
live entry, recovery copies by authenticity, never an excluded one; kept
through snapshot and compared with the almanac's fingerprint."""

from __future__ import annotations

import hashlib
import http.server
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import keep  # noqa: E402

SCRIPT = HERE / "keep.py"
NOW = ["--now", "2026-11-01T09:00:00Z"]
BODY = b"<p>Harbour levels, as archived.</p>"
PAGES = {"/live": (200, b"<p>The publisher's page.</p>"), "/gone": (404, b""),
         "/copy": (200, BODY), "/asserted": (200, b"<p>A rebuilt copy.</p>"),
         "/excluded": (200, b"<p>Never this.</p>")}  # fmt: skip


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        status, body = PAGES.get(self.path, (404, b""))
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
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


def catalog(tmp_path: Path, entry: dict) -> Path:
    p = tmp_path / "catalog.json"
    p.write_text(json.dumps({"name": "Made-Up Almanac", "entries": [entry]}))
    return p


def run(cat: Path, eid: str, to: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(cat), "--id", eid,
                           "--to", str(to), *more, *NOW], capture_output=True, text=True)  # fmt: skip


def dark(site: str, **over) -> dict:
    e = {"id": "harbour", "status": "dark", "source": {"canonical_url": f"{site}/gone"},
         "recovery": [
             {"via": "community", "url": f"{site}/asserted", "authenticity": "asserted",
              "permission": "ok"},
             {"via": "mirror", "url": f"{site}/excluded", "authenticity": "hash-verified",
              "permission": "excluded"},
             {"via": "wayback", "url": f"{site}/gone", "authenticity": "timestamped",
              "permission": "ok", "captured": "2025-02-01"},
             {"via": "wayback", "url": f"{site}/copy", "authenticity": "timestamped",
              "permission": "ok", "captured": "2025-02-04"},
         ]}  # fmt: skip
    e.update(over)
    return e


def test_a_dark_entry_keeps_the_best_copy_that_answers_never_an_excluded_one(
    site, tmp_path
):
    got = run(catalog(tmp_path, dark(site)), "harbour", tmp_path / "kept")
    assert got.returncode == 0, got.stderr
    assert (
        tmp_path / "kept" / "harbour.html"
    ).read_bytes() == BODY  # /gone failed, /copy next
    assert "from: wayback, timestamped, captured 2025-02-04" in got.stdout
    rows = [
        json.loads(x)
        for x in (tmp_path / "kept" / ".snapshots.jsonl").read_text().splitlines()
    ]
    assert (
        rows[0]["status"] == 404 and rows[0]["file"] is None
    )  # the failed try is written down
    assert rows[1]["almanac_id"] == "harbour" and rows[1]["copy"].startswith("wayback")
    assert all("excluded" not in r["url"] for r in rows)


def test_a_live_entry_starts_with_the_publisher(site, tmp_path):
    e = dark(site, status="live", source={"canonical_url": f"{site}/live"})
    got = run(catalog(tmp_path, e), "harbour", tmp_path / "kept")
    assert got.returncode == 0
    assert "from: the publisher's own address" in got.stdout


def test_the_fingerprint_is_compared(site, tmp_path):
    e = dark(site, fingerprint={"sha256": hashlib.sha256(BODY).hexdigest()})
    got = run(catalog(tmp_path, e), "harbour", tmp_path / "a")
    assert "matches the almanac's fingerprint" in got.stdout
    e = dark(site, fingerprint={"sha256": "0" * 64})
    got = run(catalog(tmp_path, e), "harbour", tmp_path / "b")
    assert "differs from the almanac's fingerprint" in got.stdout


def test_review_copies_only_when_asked(site, tmp_path):
    e = dark(site, recovery=[{"via": "community", "url": f"{site}/copy",
                              "authenticity": "asserted", "permission": "review"}])  # fmt: skip
    assert run(catalog(tmp_path, e), "harbour", tmp_path / "a").returncode == 42
    assert (
        run(catalog(tmp_path, e), "harbour", tmp_path / "b", "--review").returncode == 0
    )


def test_nothing_to_try_and_nothing_answering_are_42(site, tmp_path):
    got = run(catalog(tmp_path, dark(site, recovery=[])), "harbour", tmp_path / "a")
    assert got.returncode == 42 and got.stdout.startswith("nothing to fetch")
    e = dark(
        site, recovery=[{"via": "wayback", "url": f"{site}/gone", "permission": "ok"}]
    )
    got = run(catalog(tmp_path, e), "harbour", tmp_path / "b")
    assert got.returncode == 42 and "none of the 1 copies" in got.stdout


def test_wayback_captures_are_fetched_raw():
    assert keep.raw(
        "https://web.archive.org/web/20250204145447/https://www.epa.gov/x"
    ) == ("https://web.archive.org/web/20250204145447id_/https://www.epa.gov/x")
    assert keep.raw(
        "https://web.archive.org/web/20250204145447im_/https://e/x"
    ).endswith("20250204145447id_/https://e/x")
    assert keep.raw("https://mirror.example/x") == "https://mirror.example/x"


def test_refusals(site, tmp_path):
    cat = catalog(tmp_path, dark(site))
    assert run(cat, "no-such-id", tmp_path / "a").returncode == 2
    assert run(tmp_path / "missing.json", "harbour", tmp_path / "a").returncode == 2
    assert run(cat, "harbour", tmp_path / "a").returncode == 0
    got = run(cat, "harbour", tmp_path / "a")  # fetched once: the name is taken
    assert got.returncode == 2
    got = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert got.returncode == 2 and "keep.py" in got.stderr
