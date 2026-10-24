"""browse: a page on 127.0.0.1 that asks with the kernel's bite and approves
with its seal, reachable only with this start's secret, from this machine's
own address, and never framed or scripted."""

from __future__ import annotations

import http.client
import importlib.util
import json
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("browse", HERE / "browse.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
NOW = ["--now", "2026-10-24T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def make_box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text(
        "The dentist is on Tuesday at 3pm. <b>Bring</b> the card.\n"
    )
    (pile / "termin.txt").write_text("Der Termin beim Zahnarzt ist am Dienstag.\n")
    b = tmp_path / "box"
    assert k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW).returncode == 0  # fmt: skip
    return b


class Open:
    """A running browse for one box, and a client that holds its cookie."""

    def __init__(self, box: Path, lang: str | None = None):
        self.willow = br.Willow(box, lang)
        self.server = br.serve(self.willow)
        self.port = self.server.server_address[1]
        self.host = f"127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.cookie = ""

    def req(self, method, path, form=None, headers=None, cookie=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        hdrs = {"Host": self.host, **(headers or {})}
        if cookie and self.cookie:
            hdrs["Cookie"] = self.cookie
        body = None
        if form is not None:
            body = urlencode(form)
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=hdrs)
        r = conn.getresponse()
        text = r.read().decode()
        conn.close()
        return r, text

    def start(self):
        r, _ = self.req("GET", f"/start?key={self.willow.token}", cookie=False)
        assert r.status == 303 and r.getheader("Location") == "/"
        self.cookie = r.getheader("Set-Cookie").split(";")[0]
        return r

    def post(self, path, **form):
        return self.req("POST", path, {"token": self.willow.token, **form})

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def site(tmp_path):
    s = Open(make_box(tmp_path))
    yield s
    s.close()


def test_the_link_hands_over_a_cookie_no_other_site_can_send(site):
    r = site.start()
    cookie = r.getheader("Set-Cookie")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie and "Path=/" in cookie
    r, text = site.req("GET", "/")
    assert (
        r.status == 200 and "Ask your folder" in text and "Nothing is waiting" in text
    )


def test_without_this_starts_secret_nothing_answers(site):
    for path in ("/", "/waiting", "/nope"):
        r, text = site.req("GET", path)
        assert r.status == 403 and "link browse.py printed" in text
    r, _ = site.req("GET", "/start?key=wrong", cookie=False)
    assert r.status == 403 and r.getheader("Set-Cookie") is None
    site.cookie = "willow=" + "x" * 43
    assert site.req("GET", "/")[0].status == 403


def test_a_page_reached_by_another_name_is_refused(site):
    site.start()
    for host in (
        "evil.example:%d" % site.port,
        "127.0.0.1",
        "localhost.evil:%d" % site.port,
    ):
        r, _ = site.req("GET", "/", headers={"Host": host})
        assert r.status == 403
    r, _ = site.req(
        "GET",
        f"/start?key={site.willow.token}",
        headers={"Host": "evil.example"},
        cookie=False,
    )
    assert r.status == 403 and r.getheader("Set-Cookie") is None
    assert (
        site.req("GET", "/", headers={"Host": f"localhost:{site.port}"})[0].status
        == 200
    )


def test_a_form_from_anywhere_else_is_refused(site):
    site.start()
    r, _ = site.req("POST", "/ask", {"q": "dentist"})  # no token in the form
    assert r.status == 403
    for origin in ("https://evil.example", "null"):  # null: a sandboxed frame's
        r, _ = site.req(
            "POST",
            "/ask",
            {"token": site.willow.token, "q": "dentist"},
            headers={"Origin": origin},
        )
        assert r.status == 403
    r, _ = site.req(
        "POST",
        "/ask",
        {"token": site.willow.token, "q": "dentist"},
        headers={"Origin": f"http://127.0.0.1:{site.port}"},
    )
    assert r.status == 200
    site.cookie = ""
    r, _ = site.req("POST", "/ask", {"token": site.willow.token, "q": "dentist"})
    assert r.status == 403  # the form's token alone isn't enough


def test_every_page_forbids_framing_scripts_and_caching(site):
    site.start()
    for r, _ in (
        site.req("GET", "/"),
        site.req("GET", "/nope"),
        site.req("GET", "/", cookie=False),
    ):
        assert "frame-ancestors 'none'" in r.getheader("Content-Security-Policy")
        assert "default-src 'none'" in r.getheader("Content-Security-Policy")
        assert r.getheader("X-Frame-Options") == "DENY"
        assert r.getheader("Cache-Control") == "no-store"
        assert r.getheader("Referrer-Policy") == "same-origin"


def test_asking_shows_each_passage_with_its_file_and_line_escaped(site):
    site.start()
    r, text = site.post("/ask", q="when is the dentist")
    assert r.status == 200 and "Your files say" in text
    assert (
        "dentist.txt:1" in text
        and "&lt;b&gt;Bring&lt;/b&gt;" in text
        and "<b>Bring" not in text
    )
    rows = (site.willow.box / "record.jsonl").read_text().splitlines()
    assert (
        json.loads(rows[-1])["kind"] == "bite"
    )  # the kernel's own bite, on the record


def test_nothing_found_is_said_with_where_to_look(site):
    site.start()
    r, text = site.post("/ask", q="passport renewal office")
    assert "Nothing in your folder holds that" in text
    r, text = site.post("/ask", q="the and of")
    assert "name the thing you mean" in text


def test_a_suggestion_waits_with_its_sources_and_a_click_approves_it(site, tmp_path):
    b = site.willow.box
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    row = {
        "path": "dentist.md",
        "data": "Tuesday at 3pm",
        "cites": [served[0]["id"]],
        "claim": "the dentist note",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW
        ).returncode
        == 42
    )
    site.start()
    assert "1 suggestion waiting" in site.req("GET", "/")[1]
    r, text = site.req("GET", "/waiting")
    assert r.status == 200 and (
        "Tuesday at 3pm" in text
        and "the dentist note" in text
        and "dentist.txt:1" in text
    )
    subject = text.split('name=subject value="')[1].split('"')[0]
    r, text = site.post("/approve", subject=subject)
    assert r.status == 200 and "Approved" in text
    seal = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (
        seal["kind"] == "seal" and seal["who"] == "human" and seal["subject"] == subject
    )
    assert k("verify", "--box", str(b)).returncode == 0
    r, text = site.post("/ask", q="when is the dentist")
    assert "You approved this answer" in text and "Tuesday at 3pm" in text
    assert "Nothing is waiting" in site.req("GET", "/waiting")[1]
    r, text = site.post("/approve", subject="proposal:" + "0" * 64)
    assert "Not approved" in text and "not a proposal in this box" in text


def test_with_a_language_its_common_words_are_left_out(tmp_path):
    s = Open(make_box(tmp_path), "de")
    try:
        s.start()
        r, text = s.post("/ask", q="Wann ist der Termin beim Zahnarzt?")
        assert "termin.txt:1" in text and "dentist.txt" not in text
    finally:
        s.close()
    with pytest.raises(ValueError):
        br.Willow(s.willow.box, "xx")


def test_the_launcher_starts_browse_over_the_box_on_each_system(tmp_path, capsys):
    (tmp_path / "with space").mkdir()
    b = make_box(tmp_path / "with space")
    files = {system: text for system, _, text in br.launchers(b, "/usr/bin/python3")}
    mac = shlex.split(files["macOS"].splitlines()[1][len("exec ") :])
    assert mac == ["/usr/bin/python3", str(br.HERE), "--box", str(b.resolve())]
    assert files["macOS"].startswith("#!/bin/sh\n")
    assert (
        files["Windows"].startswith("@echo off\r\n")
        and f'"{b.resolve()}"' in files["Windows"]
    )
    assert "Exec=" in files["Linux"] and "Terminal=true" in files["Linux"]
    before = sorted(p.name for p in b.iterdir())
    assert br.main(["launcher", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    assert out.count("save as") == 3 and sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path, capsys):
    b = make_box(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "--port", "x"],
        ["--box", str(b), "--port", "70000"],
        ["--box", str(b), "--lang", "xx"],
        ["--box", str(b), "more"],
        ["launcher"],
        ["launcher", "--box"],
    ):
        assert br.main(argv) == 2, argv
    assert br.main(["--box", str(tmp_path)]) == 2
    assert br.main(["launcher", "--box", str(tmp_path)]) == 2
    assert "not a kernel box" in capsys.readouterr().err


def test_a_port_already_taken_is_refused(tmp_path, capsys):
    s = Open(make_box(tmp_path))
    try:
        assert (
            br.main(["--box", str(s.willow.box), "--port", str(s.port), "--no-open"])
            == 2
        )
        assert "refused" in capsys.readouterr().err
    finally:
        s.close()
