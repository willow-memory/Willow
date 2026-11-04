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


def test_only_a_piece_that_makes_a_page_runs_as_a_step(site, tmp_path):
    """Ticked with no words of their own, a page server, a hook's setup, a
    reader and stack itself are put in, not run: run with only --box, browse
    never ends and the others refuse."""
    cv, call = site
    pick = {"name": "ticked", "folders": [str(a_folder(tmp_path))], "lanes": [
        {"title": "watch", "steps": [{"name": "digest"}, {"name": "browse"}]},
        {"title": "assistants", "steps": [{"name": "claude-code"}, {"name": "stack"}]},
        {"title": "read", "steps": [{"name": "office"}]},
        {"title": "scores", "steps": [{"name": "predict", "args": "score --box {box}"}]},
    ]}  # fmt: skip
    arr, why = cv.arrangement(pick)
    assert why == ""
    steps = {s["name"]: s["args"] for ln in arr["lanes"] for s in ln["steps"]}
    assert steps == {"digest": "--box {box}", "predict": "score --box {box}"}
    assert arr["kept"] == ["browse", "claude-code", "stack", "office"]
    assert {"browse", "claude-code", "stack", "office"} <= set(arr["pieces"])
    assert "## read" not in arr["stack_md"]  # a lane left empty isn't there
    assert "not run on the page: browse, claude-code, stack, office" in arr["stack_md"]
    only = {"lanes": [{"steps": [{"name": "browse"}]}]}
    assert "none of its pieces makes a page" in cv.arrangement(only)[1]


def test_no_stack_is_made_inside_this_repository(tmp_path, capsys):
    assert canvas.ready(canvas.WILLOW / "a-stack") == assemble.REFUSED
    assert (
        assemble.main(["status", "--to", str(canvas.WILLOW / "a-stack")])
        == assemble.REFUSED
    )
    assert not (canvas.WILLOW / "a-stack").exists()


def test_a_piece_both_asked_for_and_leaned_on_is_added_once(tmp_path, capsys):
    to = tmp_path / "willow-stack"
    assert assemble.main(["init", "--to", str(to)]) == assemble.ALIVE
    # hook-start leans on digest, asked for first; and todo asked for twice
    assert (
        assemble.add(["digest", "hook-start", "todo", "todo"], to, None)
        != assemble.REFUSED
    )
    assert {"digest", "hook-start", "todo"} <= set(
        assemble.manifest(to / "stack")["addons"]
    )
    # a refusal partway leaves nothing half-added
    stdlib = to / "stack" / "adapters" / "stdlib"
    before = sorted(p.name for p in stdlib.iterdir())
    assert assemble.add(["coming-up", "not-an-add-on"], to, None) == assemble.REFUSED
    assert sorted(p.name for p in stdlib.iterdir()) == before
    # a folder left by an older crash is named, not a traceback
    (stdlib / "stale").mkdir()
    assert assemble.add(["stale"], to, None) == assemble.REFUSED
    assert "not on STACK.json" in capsys.readouterr().err


def test_a_tool_for_willows_own_repository_isnt_put_in_a_stack(stack_dir, capsys):
    assert assemble.add(["ci"], stack_dir, None) == assemble.REFUSED
    assert "willow's own repository" in capsys.readouterr().err


def test_a_changed_file_in_a_stack_is_found(stack_dir, tmp_path):
    copy = tmp_path / "copy"
    shutil.copytree(stack_dir, copy)
    assert assemble.check(copy) == assemble.ALIVE
    (copy / "stack" / "kernel.py").write_text("# changed\n")
    assert assemble.check(copy) == assemble.REFUSED


def test_a_stack_takes_a_new_kernel_only_whole_and_only_if_it_holds(tmp_path, capsys):
    """`kernel` swaps the stack's kernel.py and vectors for willow's, one row
    naming both hashes; a drifted stack, a wrong pin, a kernel that can't
    verify the record or one an add-on's tests fail on is refused, and the
    old kernel is back."""
    to = tmp_path / "willow-stack"
    assert assemble.main(["init", "--to", str(to)]) == assemble.ALIVE
    assert assemble.add(["todo"], to, None) != assemble.REFUSED
    stack = to / "stack"
    # willow a commit on: its own kernel.py and vectors, the same add-ons
    later = tmp_path / "later-willow"
    (later / "vectors").mkdir(parents=True)
    shutil.copy2(
        canvas.WILLOW / "vectors" / "cases.json", later / "vectors" / "cases.json"
    )
    todo = later / "adapters" / "stdlib" / "todo"  # willow's todo, changed with it
    shutil.copytree(canvas.WILLOW / "adapters" / "stdlib" / "todo", todo)
    (todo / "README.md").write_text("# todo, a commit on\n")
    src = (canvas.WILLOW / "kernel.py").read_text(encoding="utf-8")
    m = assemble.manifest(stack)
    m["willow"] = str(later)
    assemble.save(stack, m)
    rows = lambda: sum(  # noqa: E731
        json.loads(r)["kind"] == "kernel"
        for r in (to / "box" / "record.jsonl").read_text().splitlines()
    )

    def kernel_is(text):
        (later / "kernel.py").write_text(text, encoding="utf-8")
        return assemble.sha(later / "kernel.py")

    was, before = assemble.sha(stack / "kernel.py"), rows()
    # a kernel that can't verify the record: refused, the old one back
    kernel_is("import sys\nsys.exit(3)\n")
    assert assemble.swap_kernel(to, None, None) == assemble.REFUSED
    assert "doesn't verify" in capsys.readouterr().err
    assert assemble.sha(stack / "kernel.py") == was and rows() == before
    # a kernel the record holds under but todo's tests fail on: refused too
    kernel_is(src + '\n\ndef newest(text):\n    return ""\n')
    assert assemble.swap_kernel(to, None, sys.executable) == assemble.REFUSED
    assert "willow's todo changed since; `refresh` it" in capsys.readouterr().err
    assert (
        assemble.sha(stack / "kernel.py") == was
        and assemble.check(to) == assemble.ALIVE
    )
    # a pin that names another kernel
    new = kernel_is(src + "\n# a later kernel\n")
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps({"sha256": "0" * 64}))
    assert assemble.swap_kernel(to, pin, None) == assemble.REFUSED
    # a good one: swapped, one row, every file the one put in
    assert assemble.swap_kernel(to, None, sys.executable) == assemble.ALIVE
    assert (
        assemble.sha(stack / "kernel.py") == new == assemble.manifest(stack)["kernel"]
    )
    assert rows() == before + 1 and assemble.check(to) == assemble.ALIVE
    last = json.loads((to / "box" / "record.jsonl").read_text().splitlines()[-1])
    assert (last["was"], last["sha256"]) == (was, new)
    assert assemble.swap_kernel(to, None, None) == assemble.ALIVE  # already: nothing
    assert rows() == before + 1
    # a stack whose files moved isn't given a kernel under them
    kernel_is(src + "\n# later still\n")
    (stack / "adapters" / "stdlib" / "todo" / "todo.py").write_text("# changed\n")
    assert assemble.swap_kernel(to, None, None) == assemble.REFUSED
    assert assemble.sha(stack / "kernel.py") == new


def test_a_deps_add_on_comes_in_only_with_its_packages_already_there(tmp_path, capsys):
    """A deps piece goes to adapters/deps/ when --python has every package its
    floor names, at that version or newer; one missing or too old is refused,
    nothing half-added and nothing installed; without --python it is put in,
    its packages unreachable, and the stack waits on you."""
    to = tmp_path / "willow-stack"
    assert assemble.main(["init", "--to", str(to)]) == assemble.ALIVE
    stack = to / "stack"
    later = tmp_path / "later-willow"  # willow with three deps add-ons of its own
    (later / "adapters" / "stdlib").mkdir(parents=True)

    def dep(name, floor):
        d = later / "adapters" / "deps" / name
        d.mkdir(parents=True)
        (d / "README.md").write_text(
            "<!-- willow-addon\nwrites: nothing\nnetwork: none\n-->\n# " + name + "\n"
        )
        (d / f"{name.replace('-', '_')}.py").write_text(
            "import sys\n\nif __name__ == '__main__':\n    raise SystemExit(2)\n"
        )
        (d / "requirements-floor.txt").write_text(floor + "\n")

    dep("has-it", "pytest==1.0")
    # a library sorted ahead of its script (share's ed25519.py): the script is held
    (later / "adapters" / "deps" / "has-it" / "a_lib.py").write_text("X = 1\n")
    dep("too-old", "pytest==999.0")
    dep("not-here", "no-such-willow-package==1.0")
    m = assemble.manifest(stack)
    m["willow"] = str(later)
    assemble.save(stack, m)
    py = sys.executable
    assert assemble.add(["has-it"], to, py) == assemble.ESCALATE  # no tests: said
    assert (stack / "adapters" / "deps" / "has-it").is_dir()
    entry = assemble.manifest(stack)["addons"]["has-it"]
    assert (entry["kind"], entry["packages"]["state"]) == ("deps", "met")
    assert entry["contract"] == "held"
    assert "packages met" in capsys.readouterr().out
    for name, said in (("too-old", "pytest 999.0 or newer (has "),
                       ("not-here", "no-such-willow-package 1.0 or newer (not installed)")):  # fmt: skip
        assert assemble.add([name], to, py) == assemble.REFUSED
        assert said in capsys.readouterr().err
        assert not (stack / "adapters" / "deps" / name).exists()
    assert assemble.add(["too-old"], to, None) == assemble.ESCALATE
    entry = assemble.manifest(stack)["addons"]["too-old"]
    assert entry["packages"]["state"] == "unreachable"
    assert assemble.check(to) == assemble.ALIVE  # each where it was put
    assert assemble.refresh(["has-it"], to) == assemble.ALIVE
    assert assemble.version_key("1.10.0") > assemble.version_key("1.9.2")
    assert assemble.version_key("0.10.0") > assemble.version_key("0.8.1")
    assert assemble.version_key("2.0rc1") == (2, 0)


def test_a_bad_command_line_is_refused():
    assert canvas.main(["--stray"]) == assemble.REFUSED
    assert canvas.main(["--port", "x"]) == assemble.REFUSED
    assert assemble.main([]) == assemble.REFUSED
    assert assemble.main(["init", "--willow", "/elsewhere"]) == assemble.REFUSED


def test_start_runs_the_page_over_every_folder_of_the_pick(site, tmp_path):
    """Two folders are two records, so two pages: the sealed flow runs over
    each, and each page is written beside its own record."""
    import time

    cv, call = site
    one, two = a_folder(tmp_path / "one"), a_folder(tmp_path / "two")
    pick = {"name": "two folders", "folders": [str(one), str(two)], "lanes": [
        {"title": "watch", "steps": [{"name": "coming-up", "args": "--box {box} --days 30"}]}]}  # fmt: skip
    subject = call("POST", "/tok/api/propose", pick)[1]["subject"]
    assert call("POST", "/tok/api/seal", {"subject": subject})[1]["sealed"] is True
    call("POST", "/tok/api/assemble", {"subject": subject})
    try:
        assert cv.start(subject) == {"started": True}
        for _ in range(600):
            if cv.job["state"] != "running":
                break
            time.sleep(0.5)
        flows = [s for s in cv.job["steps"] if s["step"] == "your flow, run once"]
        assert [s["said"].split(",")[0] for s in flows] == [
            f"over {one}",
            f"over {two}",
        ]
        assert all(s["state"] in ("done", "needs you") for s in flows), flows
        # both are named "files": each its own record, the second "files-2"
        for slug in ("files", "files-2"):
            assert (cv.to / "mine" / slug / "page.md").is_file()
        assert f"## over {one}" in cv.job["flow"] and f"## over {two}" in cv.job["flow"]
    finally:
        for proc in cv.browsers:
            proc.terminate()


def test_a_reader_is_offered_for_a_kind_its_card_names_not_for_an_english_word():
    """`.so` files (compiled libraries) were offered readers whose card lines
    say "so" in a sentence; a two-letter word counts with its dot or in
    capitals, never bare."""
    assert not canvas.names_kind("so", "It reads them, so you can ask.")
    assert canvas.names_kind("so", "A shared library (.so) as its symbols.")
    assert canvas.names_kind("zip", "A Notion export zip, page by page.")
    assert canvas.names_kind("pdf", "Your PDF files as passages.")
    assert not canvas.names_kind("go", "Notes you go back to.")


def test_each_piece_says_the_part_it_plays_and_why(site):
    """A role is a guess from the card, so every piece says which fact it went
    by; the page and the command line read the same one."""
    cv, call = site
    _, ps = call("GET", "/tok/api/pieces")
    keys = {k for k, _ in canvas.ROLES}
    assert all(p["role"] in keys and p["role_why"] for p in ps.values())
    want = {
        "pdf": "reads",
        "stems": "words",
        "privacy": "guards",
        "coming-up": "page",
        "local-model": "suggests",
        "model-exam": "suggests",
        "vscode": "ways",
        "claude-code": "ways",  # tagged hook, but a way in first
        "hook-guard": "guards",
        "calendar-out": "makes",
        "ci": "repo",
    }
    assert {n: ps[n]["role"] for n in want} == want
    assert ps["vscode"]["group"] == "In your editor"
    assert ps["local-model"]["group"] == "Models that suggest answers"
    assert ps["model-exam"]["group"] == "Checking a model before you trust it"


def test_a_role_goes_by_the_first_fact_that_fits():
    def r(**card):
        return canvas.role({"name": "x", "section": "", "line": "", **card})["role"]

    assert r(section="Reading more kinds of files", page=True) == "reads"
    assert r(name="hook-x", page=True) == "guards"
    assert r(line="Suggestions from a model.", page=True) == "suggests"
    assert r(page=True, writes="to") == "page"
    assert r(section="Ways to use it", writes="to") == "makes"
    assert r(section="Ways to use it", writes="nothing") == "ways"
    assert r(writes="record") == "tools"
    assert "idea" in canvas.role({"name": "x", "state": "idea"})["role_why"]
    assert r(runs_in="repo", section="Reading more kinds of files") == "repo"
    assert r(section="Your own words") == "words"
    # what the card says comes first; the guess is for a willow from before
    said = canvas.role({"name": "hook-x", "state": "built", "role": "tools", "page": True})  # fmt: skip
    assert said["role"] == "tools" and said["role_why"] == "its card says so"
    assert canvas.role({"name": "hook-x", "role": "nonsense"})["role"] == "guards"


def test_the_page_names_every_role_a_person_can_fill():
    page = (canvas.HERE / "page.html").read_text(encoding="utf-8")
    for key, title in canvas.ROLES:
        if key != "repo":
            assert f"{{key:'{key}',title:'{title}'" in page


def run(capsys, *argv):
    code = canvas.main([str(a) for a in argv])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_the_commands_list_what_the_page_lists(stack_dir, capsys):
    code, out, _ = run(capsys, "pieces", "--to", stack_dir)
    assert code == 0 and all(t in out for _, t in canvas.ROLES)
    code, out, _ = run(capsys, "pieces", "--role", "repo", "--to", stack_dir)
    assert code == 0 and "python adapters/stdlib/ci/ci.py run" in out
    assert run(capsys, "pieces", "--role", "nope", "--to", stack_dir)[0] == 2
    code, out, _ = run(capsys, "needs", "copilot", "--json", "--to", stack_dir)
    assert code == 0 and "hosts" in json.loads(out)["copilot"]["brings"]
    code, out, _ = run(capsys, "examples", "--to", stack_dir)
    assert code == 0 and "choir.md" in out


def test_a_plan_is_the_stack_file_the_page_would_send(stack_dir, tmp_path, capsys):
    """An example's steps keep their options; a way in is set up alongside,
    not run on the page; read back, the file is the same arrangement."""
    code, out, _ = run(capsys, "plan", "--example", "choir.md", "vscode", "--to", stack_dir)  # fmt: skip
    assert code == 0
    assert "## What runs on your page" in out and "- coming-up -- --box {box} --days 30" in out  # fmt: skip
    assert "not run on the page: " in out and "vscode" in out.split("not run on the page: ")[1].split("-->")[0]  # fmt: skip
    cv = canvas.Canvas(stack_dir, canvas.WILLOW, stack_dir / "box", [])
    arr, _ = cv.arrangement(canvas.read_stack(out))
    assert arr["stack_md"].rstrip() == out.rstrip()
    f = tmp_path / "mine.md"
    f.write_text(out)
    code, said, _ = run(capsys, "look", f, "--to", stack_dir)
    assert code == 0 and "1. habits" in said and "vscode" in said.split("set up alongside")[1]  # fmt: skip


def test_a_command_proposes_and_never_seals(stack_dir, tmp_path, capsys):
    code, out, _ = run(capsys, "plan", "coming-up", "--to", stack_dir)
    f = tmp_path / "mine.md"
    f.write_text(out)
    code, said, _ = run(capsys, "propose", f, "--to", stack_dir)
    assert code == 42 and "waiting for your seal" in said
    subject = said.split("subject ")[1].split(",")[0]
    k = assemble.load_kernel(stack_dir / "stack")
    rows, _ = k.read(stack_dir / "box" / "record.jsonl")
    assert any(r.get("subject") == subject for r in rows)
    assert subject not in k.sealed(stack_dir / "box", rows)
    assert "seal" not in canvas.VERBS and run(capsys, "seal", subject)[0] == 2


def test_the_commands_refuse_what_the_page_refuses(stack_dir, tmp_path, capsys):
    assert run(capsys, "plan", "ci", "--to", stack_dir)[0] == 2  # willow's own repo
    assert run(capsys, "plan", "no-such-thing", "--to", stack_dir)[0] == 2
    assert run(capsys, "plan", "--to", stack_dir)[0] == 2
    assert run(capsys, "look", tmp_path / "absent.md", "--to", stack_dir)[0] == 2
    code, _, err = run(capsys, "pieces", "--to", tmp_path / "no-stack")
    assert code == 2 and "make --to" in err


def test_the_page_knows_its_stack_to_say_the_commands_for_it(site, stack_dir):
    _, call = site
    assert call("GET", "/tok/api/state")[1]["to"] == str(stack_dir.resolve())


def test_sealed_or_changed_is_the_records_word_wherever_it_was_sealed(site, tmp_path):
    """Sealed with the kernel's own command, not the page: the page's pick is
    "sealed" while it's what was sealed, "changed" once it isn't, and asking
    writes nothing."""
    cv, call = site
    doc = {
        "name": "mine",
        "folders": [str(a_folder(tmp_path))],
        "lanes": [
            {
                "title": "t",
                "steps": [{"name": "coming-up", "args": "--box {box} --days 9"}],
            }
        ],  # fmt: skip
    }
    subject = call("POST", "/tok/api/propose", doc)[1]["subject"]
    k = cv.kernel
    assert canvas.quiet(k.seal, cv.box, subject, k.now())[0] == k.ALIVE
    before = (cv.box / "record.jsonl").read_bytes()
    assert call("POST", "/tok/api/sealed", doc)[1] == {"state": "sealed", "subject": subject}  # fmt: skip
    moved = json.loads(json.dumps(doc))
    moved["lanes"][0]["steps"][0]["args"] = "--box {box} --days 10"
    assert call("POST", "/tok/api/sealed", moved)[1]["state"] == "changed"
    assert call("POST", "/tok/api/sealed", {"lanes": []})[1]["state"] == "changed"
    assert (cv.box / "record.jsonl").read_bytes() == before


def test_a_start_is_what_the_examples_run_not_a_list_by_hand(site):
    cv, call = site
    _, ps = call("GET", "/tok/api/pieces")
    ran = {s["name"] for e in cv.examples()["found"] for s in e["steps"]}
    assert ran and all(ps[n]["in_examples"] >= 1 for n in ran if n in ps)
    assert all(p["in_examples"] == 0 for n, p in ps.items() if n not in ran)
    page = (canvas.HERE / "page.html").read_text(encoding="utf-8")
    assert "SUGGEST" not in page
