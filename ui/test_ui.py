"""The UI: willow put together on a page, on this machine only. Its server is
run here, in this process, over a stack made in a scratch folder from this
willow: another site can't drive it; what the kernel makes of a folder is
said as counts, never a file's words or name; a batch is saved, replaced only
when asked and deleted for good; what an add-on uses comes with it; a seal is
the kernel's own, and only a sealed pick is put together; no stack is ever
made inside this repository."""

from __future__ import annotations

import http.client
import importlib.util
import json
import shutil
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("ui_canvas", HERE / "canvas.py")
canvas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canvas)
assemble = canvas.assemble


@pytest.fixture(scope="module")
def stack_dir(tmp_path_factory):
    """A stack made from this willow, as the first run makes it."""
    to = Path(tempfile.mkdtemp(dir=tmp_path_factory.mktemp("ui"))) / "willow-stack"
    assert canvas.ready(to) == assemble.ALIVE
    return to


@pytest.fixture
def site(stack_dir, tmp_path):
    """The UI's server over the stack, on a free port of this machine."""
    cv = canvas.Canvas(stack_dir, canvas.WILLOW, stack_dir / "box", [])
    srv = ThreadingHTTPServer(("127.0.0.1", 0), None)
    host = f"127.0.0.1:{srv.server_address[1]}"
    srv.RequestHandlerClass = canvas.handler(cv, "tok", host)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def call(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=60)
        h = {
            "Host": host,
            "Content-Type": "application/json",
            "Origin": f"http://{host}",
        }
        h.update(headers or {})
        c.request(method, path, json.dumps(body) if body is not None else None, h)
        r = c.getresponse()
        data = r.read().decode()
        try:
            return r.status, json.loads(data)
        except ValueError:
            return r.status, data

    yield cv, call
    srv.shutdown()
    (stack_dir / "batches.json").unlink(missing_ok=True)


def a_folder(tmp_path: Path) -> Path:
    """Files named and filled so a leak would show."""
    f = tmp_path / "files"
    (f / "sub").mkdir(parents=True)
    (f / ".secret").mkdir()
    (f / "notes-DIVORCE.txt").write_text(
        "The roof estimate came in at 4200.\n\nMould again.\n"
    )
    (f / "sub" / "garden-ZEBRA.md").write_text("# Garden\n\nTomatoes want sun.\n")
    (f / "lawyer-LETTER.pdf").write_bytes(b"%PDF-1.4\0\0x")
    (f / "will-DRAFT.docx").write_bytes(b"PK\3\4\0\0")
    (f / "utf16-NOTE.txt").write_bytes(b"\xff\xfeh\0i\0")
    (f / ".secret" / "key-HIDDEN.txt").write_text("hidden\n")
    return f


def test_another_site_cant_drive_it(site):
    _, call = site
    assert call("GET", "/")[0] == 404  # no token
    assert call("GET", "/tok/api/pieces", headers={"Host": "evil.example"})[0] == 404
    assert (
        call("POST", "/tok/api/batches/save", {}, {"Origin": "http://evil.example"})[0]
        == 403
    )
    assert (
        call("POST", "/tok/api/batches/save", {}, {"Content-Type": "text/plain"})[0]
        == 415
    )
    status, page = call("GET", "/tok/")
    assert status == 200 and "Put your willow together" in page


def test_the_kernels_baseline_is_counts_and_kinds_and_nothing_of_the_files(
    site, tmp_path
):
    _, call = site
    folder = a_folder(tmp_path)
    status, b = call("GET", f"/tok/api/baseline?path={folder}")
    assert status == 200 and b["ok"]
    assert (b["read"], b["passages"], b["hidden"]) == (2, 4, 1)
    kinds = {c["kind"]: c for c in b["cant"]}
    assert kinds[".pdf"]["files"] == 1 and "pdf" in kinds[".pdf"]["readers"]
    assert kinds[".docx"]["readers"][0] == "office"
    assert (
        kinds[".txt"]["readers"] == [] and kinds[".txt"]["text"]
    )  # no reader fixes an encoding
    said = json.dumps(b)
    for leak in (
        "DIVORCE",
        "ZEBRA",
        "LETTER",
        "DRAFT",
        "NOTE",
        "HIDDEN",
        "roof",
        "Tomatoes",
    ):
        assert leak not in said, leak
    assert call("GET", f"/tok/api/baseline?path={tmp_path / 'nope'}")[1]["ok"] is False


def test_what_an_add_on_uses_comes_with_it_and_the_cards_say_it(site):
    cv, call = site
    pieces = call("GET", "/tok/api/pieces")[1]
    assert pieces["debts"]["hard"] == ["amounts"]  # its card's uses
    assert set(pieces["digest"]["soft"]) == {"coming-up", "stale"}  # looks-for
    assert pieces["ci"]["runs_in"] == "repo"
    assert pieces["vim"]["tags"][:2] == [
        "no-install",
        "offline",
    ]  # similar's, worked out
    assert cv.closure(["debts"]) == ["amounts"]


def test_a_batch_is_saved_replaced_only_when_asked_and_deleted_for_good(site):
    _, call = site
    post = lambda path, body: call("POST", f"/tok/api/batches/{path}", body)[1]  # noqa: E731
    picked = {
        "watch": ["habits", "attendance"],
        "hide": ["privacy"],
        "x": ["not-an-add-on"],
    }
    assert post("save", {"name": "farm", "stages": picked}) == {"saved": "farm"}
    got = call("GET", "/tok/api/batches")[1]
    assert got["farm"]["pieces"] == 3 and got["farm"]["stages"]["hide"] == ["privacy"]
    assert post("save", {"name": "farm", "stages": {"watch": ["todo"]}}) == {
        "exists": "farm"
    }
    assert (
        call("GET", "/tok/api/batches")[1]["farm"]["pieces"] == 3
    )  # untouched until asked
    assert post(
        "save", {"name": "farm", "stages": {"watch": ["todo"]}, "replace": True}
    )
    assert call("GET", "/tok/api/batches")[1]["farm"]["pieces"] == 1
    assert "refused" in post("save", {"name": " ", "stages": picked})
    assert "refused" in post("save", {"name": "empty", "stages": {}})
    assert post("delete", {"name": "farm"}) == {"deleted": "farm"}
    assert call("GET", "/tok/api/batches")[1] == {}
    assert "refused" in post("delete", {"name": "farm"})


def test_the_examples_are_the_stack_add_ons_own_with_their_options(site):
    _, call = site
    ex = call("GET", "/tok/api/examples")[1]
    assert ex["state"] == "populated" and len(ex["found"]) >= 8
    small = next(e for e in ex["found"] if e["title"] == "a smallholding")
    args = {s["name"]: s["args"] for s in small["steps"]}
    assert args["coming-up"] == "--box {box} --days 30"


def test_search_finds_a_card_in_a_persons_own_words(site):
    _, call = site
    got = call("GET", "/tok/api/search?q=remind%20me%20when%20things%20are%20due")[1]
    assert got["found"][0]["name"] == "coming-up"
    assert "remind" in got["found"][0]["why"]
    vim = call("GET", "/tok/api/search?q=use%20it%20from%20vim")[1]["found"][0]
    assert vim == {"name": "vim", "why": "you named it"}


def test_only_a_sealed_pick_is_put_together_and_the_seal_is_the_kernels(site, tmp_path):
    cv, call = site
    folder = a_folder(tmp_path)
    pick = {"name": "my willow", "folders": [str(folder)], "lanes": [
        {"title": "watch", "steps": [{"name": "coming-up", "args": "--box {box} --days 30"}]}]}  # fmt: skip
    got = call("POST", "/tok/api/propose", pick)[1]
    subject = got["subject"]
    assert "- coming-up -- --box {box} --days 30" in got["arrangement"]["stack_md"]
    assert got["claim"] == "this is my stack: 1 folder, 1 piece, reaches no network"
    assert "refused" in call("POST", "/tok/api/assemble", {"subject": subject})[1]
    assert (
        "refused"
        in call("POST", "/tok/api/seal", {"subject": "proposal:" + "0" * 64})[1]
    )
    assert call("POST", "/tok/api/seal", {"subject": subject})[1]["sealed"] is True
    put = call("POST", "/tok/api/assemble", {"subject": subject})[1]
    assert put["added"] == ["coming-up"]
    assert "coming-up" in assemble.manifest(cv.stack)["addons"]
    assert assemble.check(cv.to) == assemble.ALIVE
    k = cv.kernel
    rows, breaks = k.read(cv.box / "record.jsonl")
    assert not breaks and subject in k.sealed(cv.box, rows)


def test_no_stack_is_made_inside_this_repository(tmp_path, capsys):
    assert canvas.ready(canvas.WILLOW / "a-stack") == assemble.REFUSED
    assert (
        assemble.main(["status", "--to", str(canvas.WILLOW / "a-stack")])
        == assemble.REFUSED
    )
    assert not (canvas.WILLOW / "a-stack").exists()


def test_a_tool_for_willows_own_repository_isnt_put_in_a_stack(stack_dir, capsys):
    assert assemble.add(["ci"], stack_dir, None) == assemble.REFUSED
    assert "willow's own repository" in capsys.readouterr().err


def test_a_changed_file_in_a_stack_is_found(stack_dir, tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(stack_dir, copy)
    assert assemble.check(copy) == assemble.ALIVE
    (copy / "stack" / "kernel.py").write_text("# changed\n")
    assert assemble.check(copy) == assemble.REFUSED


def test_a_bad_command_line_is_refused():
    assert canvas.main(["--stray"]) == assemble.REFUSED
    assert canvas.main(["--port", "x"]) == assemble.REFUSED
    assert assemble.main([]) == assemble.REFUSED
    assert assemble.main(["init", "--willow", "/elsewhere"]) == assemble.REFUSED
