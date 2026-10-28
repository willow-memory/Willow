"""live: each check runs the program it names and reads back what it did;
a program that isn't here is `not here`, never a pass. The real programs
run in CI's tools job; here, small stand-ins on PATH answer as the real ones
do when, and only when, the lines they're handed are right."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("live", HERE / "live.py")
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)

#: each stand-in reads the file the real program reads and answers as the
#: real one does: only lines that start mcp-lite over the box count
FAKES = {
    "gemini": """
home = Path(os.environ["HOME"])
doc = json.loads((home / ".gemini" / "settings.json").read_text())
trusted = json.loads((home / ".gemini" / "trustedFolders.json").read_text())
ok = right(doc["mcpServers"]["willow"]["args"]) and trusted.get(os.getcwd()) == "TRUST_FOLDER"
print("willow: " + ("Connected" if ok else "Disabled"))
""",
    "codex": """
text = (Path(os.environ["CODEX_HOME"]) / "config.toml").read_text()
if "[mcp_servers.willow]" in text and "mcp-lite/server.py" in text:
    print("willow\\n  enabled: true\\n  args: " + text.split("args = ", 1)[1])
""",
    "opencode": """
doc = json.loads(Path("opencode.json").read_text())
cmd = doc["mcp"]["willow"]["command"]
print("willow " + ("connected" if doc["mcp"]["willow"]["type"] == "local" and right(cmd) else "failed"))
""",
    "copilot": """
doc = json.loads((Path(os.environ["HOME"]) / ".copilot" / "mcp-config.json").read_text())
s = doc["mcpServers"]["willow"]
print("User servers:\\n  willow (" + s["type"] + ")" if right(s["args"]) else "")
""",
    "claude": """
cfg = Path(os.environ["HOME"]) / "added.json"
if sys.argv[1:3] == ["mcp", "add"]:
    cfg.write_text(json.dumps(sys.argv[sys.argv.index("--") + 1:]))
elif sys.argv[1:3] == ["mcp", "list"]:
    print("willow: " + ("Connected" if cfg.exists() and right(json.loads(cfg.read_text())) else "Failed"))
""",
}
PRELUDE = """import json, os, sys
from pathlib import Path
def right(argv):
    return len(argv) >= 3 and argv[-3].endswith("mcp-lite/server.py") and argv[-2] == "--box" and Path(argv[-1], "kernel.json").is_file()
"""


@pytest.fixture
def fakes(tmp_path, monkeypatch):
    """A PATH holding the stand-ins and the system's own sh, nothing else."""
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    for name, body in FAKES.items():
        exe = bin_ / name
        exe.write_text(f"#!{sys.executable}\n" + PRELUDE + body)
        exe.chmod(0o755)
    sh = shutil.which("sh")
    if sh:
        (bin_ / "sh").symlink_to(sh)
    monkeypatch.setenv("PATH", str(bin_))
    return bin_


def test_a_program_that_isnt_here_is_not_here_not_a_pass(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert live.one("gemini") == (live.ABSENT, "gemini not on PATH")
    assert live.main(["run", "gemini", "zsh"]) == 42
    out = capsys.readouterr().out.splitlines()
    assert out == ["not here  gemini      gemini not on PATH",
                   "not here  zsh         zsh not on PATH"]  # fmt: skip


def test_the_exit_code_is_the_worst_state():
    W, F, A = live.WORKS, live.FAILS, live.ABSENT
    assert live.code_of([W, W]) == 0
    assert live.code_of([W, A]) == 42
    assert live.code_of([A, F, W]) == 2
    assert live.code_of([]) == 0


@pytest.mark.parametrize("name", ["gemini", "codex", "opencode", "copilot"])
def test_each_tool_works_when_its_program_reads_the_lines(fakes, name):
    assert live.one(name) == (live.WORKS, "")


def test_a_broken_line_fails_with_what_the_program_said(fakes, monkeypatch):
    monkeypatch.setattr(
        live, "config", lambda *a, **k: '{"mcpServers": {"willow": {"args": ["x"]}}}'
    )
    state, why = live.one("gemini")
    assert state == live.FAILS and "Connected" in why and "Disabled" in why


def test_gemini_is_handed_a_trusted_folder(fakes, monkeypatch):
    put = live.Place.put

    def untrusted(self, rel, text):
        return put(self, rel, "{}" if rel.endswith("trustedFolders.json") else text)

    monkeypatch.setattr(live.Place, "put", untrusted)
    assert live.one("gemini")[0] == live.FAILS


@pytest.mark.skipif(not shutil.which("sh"), reason="no sh on this machine")
def test_claude_codes_hook_serves_passages_and_its_add_line_runs(fakes):
    assert live.one("claude") == (live.WORKS, "")


def test_a_program_that_hangs_fails_by_the_clock(fakes, monkeypatch):
    (fakes / "codex").write_text(f"#!{sys.executable}\nimport time; time.sleep(5)\n")
    monkeypatch.setattr(live, "TIMEOUT", 1)
    assert live.one("codex") == (live.FAILS, "codex took more than 1s")


SHIM = "GitHub Copilot CLI was not found. Run copilot in a terminal to install it"


def test_a_launcher_standing_in_for_its_program_is_not_here(fakes):
    """VS Code puts a `copilot` on PATH that only says the CLI isn't installed,
    with the exit a shell gives for a program it can't find."""
    exe = fakes / "copilot"
    exe.write_text(f"#!{sys.executable}\nimport sys; print({SHIM!r}); sys.exit(127)\n")
    state, why = live.one("copilot")
    assert state == live.ABSENT and why == f"copilot on PATH isn't it: {SHIM}"
    exe.write_text(f"#!{sys.executable}\nimport sys; print({SHIM!r}); sys.exit(1)\n")
    assert live.one("copilot")[0] == live.FAILS, "only the not-found exit is not here"


@pytest.mark.skipif(not shutil.which("sh"), reason="no sh on this machine")
def test_another_program_exiting_not_found_still_fails(fakes):
    """The add-on's own line, run through sh, is what's checked: its exit 127
    is the add-on's failure, never the program missing."""
    exe = fakes / "claude"
    exe.write_text(exe.read_text().replace(
        'if sys.argv[1:3] == ["mcp", "add"]:\n', 'if sys.argv[1:3] == ["mcp", "add"]:\n    sys.exit(127)\n'
    ))  # fmt: skip
    assert "sys.exit(127)" in exe.read_text()
    assert live.one("claude")[0] == live.FAILS


def test_every_check_runs_in_a_folder_with_a_space_and_its_own_home():
    with tempfile.TemporaryDirectory() as tmp:  # as one() makes it
        check_place(live.Place(Path(tmp)))


def check_place(place) -> None:
    assert " " in str(place.box) and (place.box / "kernel.json").is_file()
    assert place.env["HOME"] == str(place.home) and place.env["WILLOW_BOX"] == str(
        place.box
    )
    assert place.expect("moved.txt", 2) == f"{place.notes / 'moved.txt'}:2"
    assert sorted(p.name for p in place.notes.iterdir()) == sorted(live.NOTES)


def test_a_misread_file_and_line_is_not_the_right_one():
    said = "/n/moved.txt:1: Moved from old.txt:4\n/n/dentist.txt:1\n"
    assert live.lines(said, "/n/dentist.txt:1") is None
    assert "no line '/n/moved.txt:1'" in live.lines(
        said, "/n/dentist.txt:1", "/n/moved.txt:1"
    )
    assert live.has("a b", "a") is None and "didn't say 'c'" in live.has(
        "a b", "a", "c"
    )


@pytest.mark.skipif(not shutil.which("bash"), reason="no bash on this machine")
def test_bash_runs_the_shell_add_ons_lines_for_real():
    assert live.one("bash") == (live.WORKS, "")


def test_list_names_every_check_and_what_it_needs(capsys):
    assert live.main(["list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert [ln.split()[0] for ln in out] == list(live.CHECKS)
    assert all(
        f"needs {needs}" in ln for ln, (_, needs, _) in zip(out, live.CHECKS.values())
    )


def test_an_unknown_check_or_no_verb_is_refused(capsys):
    assert live.main(["run", "gemini", "nano"]) == 2
    assert "no check 'nano'" in capsys.readouterr().err
    assert live.main([]) == 2 and live.main(["gemini"]) == 2
    assert "live.py run [CHECK ...]" in capsys.readouterr().err


def test_a_box_that_cant_be_made_fails_the_check(fakes, monkeypatch):
    monkeypatch.setattr(live, "ROOT", Path(os.devnull))
    state, why = live.one("codex")
    assert state == live.FAILS and why.startswith("RuntimeError: couldn't make the box")


def test_the_mcp_check_reads_each_answer_the_client_gives(fakes, monkeypatch):
    calls = []

    def client(place, *call):
        calls.append(call[1])
        if call[1] == "ask":
            return json.dumps({"structuredContent": {"served": [{"id": "abc"}]},
                               "state": "populated", "isError": False})  # fmt: skip
        if call[1] == "waiting":
            return '{"waiting": ["proposal:1"]}'
        if "path=../out" in call:
            return '{"isError": true}'
        return '{"waiting": "proposal:1"}'

    monkeypatch.setattr(live, "inspect", client)
    (fakes / "mcp-inspector").write_text("")
    (fakes / "mcp-inspector").chmod(0o755)
    assert live.one("mcp") == (live.WORKS, "")
    assert calls == ["ask", "suggest", "waiting", "suggest"]


def test_an_add_on_edited_within_the_same_second_runs_as_it_is_now(
    tmp_path, monkeypatch
):
    """A cached build of the old code has the new code's size and time:
    only reading the source tells them apart."""
    (tmp_path / "x").mkdir()
    src = tmp_path / "x" / "x.py"
    src.write_text('WORD = "cget"\n')
    os.utime(src, (1_700_000_000, 1_700_000_000))
    monkeypatch.setattr(live, "STDLIB", tmp_path)
    assert live.addon("x", "x").WORD == "cget"
    py_compile.compile(str(src), cfile=importlib.util.cache_from_source(str(src)))
    src.write_text('WORD = "lget"\n')
    os.utime(src, (1_700_000_000, 1_700_000_000))
    assert live.addon("x", "x").WORD == "lget"


#: node, as far as the vscode check uses it: the pattern run over each line
NODE = """import re, sys
pattern = re.compile(sys.argv[3])
for line in filter(None, sys.stdin.read().split("\\n")):
    m = pattern.match(line)
    print(m.group(1) + ":" + m.group(2) if m else "NO MATCH " + line)
print(os.environ.get("EXTRA", ""))
"""


def test_vscodes_matcher_must_read_every_line_and_read_it_right(fakes, monkeypatch):
    exe = fakes / "node"
    exe.write_text(f"#!{sys.executable}\nimport os\n" + NODE)
    exe.chmod(0o755)
    assert live.one("vscode") == (live.WORKS, "")
    monkeypatch.setenv("EXTRA", "NO MATCH /n/x.txt")
    state, why = live.one("vscode")
    assert state == live.FAILS and why.startswith("a line didn't match")


#: a stand-in Chrome on the DevTools pipe: fd 3 in, fd 4 out, NUL-ended JSON.
#: It "draws" the page as Chrome would (the script's paragraph filled in) and
#: snapshots it as Chrome does, with no charset on the part; FAKE_CHROME=bare
#: snapshots the page as fetched, without what the script drew.
CHROME = r"""
import json, os, quopri, sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
mode, url, buf = os.environ.get("FAKE_CHROME", ""), "", b""
(Path(os.environ["HOME"]) / "argv.json").write_text(json.dumps(sys.argv[1:]))
def page():
    text = Path(unquote(urlsplit(url).path)).read_text(encoding="utf-8")
    drawn = text.replace('<p id="late"></p>', '<p id="late">Drawn by script.</p>')
    return text if mode == "bare" else drawn
def reply(msg, result):
    os.write(4, json.dumps({"id": msg["id"], "result": result}).encode() + b"\0")
while True:
    chunk = os.read(3, 65536)
    if not chunk:
        sys.exit(0)
    buf += chunk
    while b"\0" in buf:
        raw, buf = buf.split(b"\0", 1)
        msg = json.loads(raw)
        m, p = msg["method"], msg.get("params", {})
        if m == "Target.createTarget":
            url = p["url"]
            reply(msg, {"targetId": "T1"})
        elif m == "Target.attachToTarget":
            reply(msg, {"sessionId": "S1"})
        elif m == "Runtime.evaluate":
            v = "complete" if p["expression"] == "document.readyState" else page()
            reply(msg, {"result": {"type": "string", "value": v}})
        elif m == "Page.captureSnapshot":
            body = quopri.encodestring(page().encode()).decode()
            reply(msg, {"data": "From: <Saved by Blink>\r\nSnapshot-Content-Location: " + url
                + '\r\nMIME-Version: 1.0\r\nContent-Type: multipart/related; type="text/html";'
                + ' boundary="B"\r\n\r\n--B\r\nContent-Type: text/html\r\n'
                + "Content-Transfer-Encoding: quoted-printable\r\n\r\n" + body + "\r\n--B--\r\n"})
        elif m == "Browser.close":
            reply(msg, {})
            sys.exit(0)
"""


@pytest.fixture
def chrome(fakes):
    exe = fakes / "google-chrome"
    exe.write_text(f"#!{sys.executable}\n" + CHROME)
    exe.chmod(0o755)
    return exe


def test_chrome_saves_a_page_web_pages_reads_both_ways(chrome):
    assert live.one("chrome") == (live.WORKS, "")


def test_chrome_fails_when_a_saved_page_lacks_what_the_script_drew(chrome, monkeypatch):
    monkeypatch.setenv("FAKE_CHROME", "bare")
    state, why = live.one("chrome")
    assert state == live.FAILS and why.startswith("no line 'Drawn by script.'")


def test_a_reply_inside_the_last_second_of_the_clock_is_still_read(chrome, monkeypatch):
    """Each message to the browser has the whole clock: with one second, a
    reply that comes within it is read, not given up on early."""
    monkeypatch.setattr(live, "TIMEOUT", 1)
    assert live.one("chrome") == (live.WORKS, "")


def test_a_browser_that_closes_its_pipe_fails_and_says_so(fakes):
    exe = fakes / "google-chrome"
    exe.write_text(f"#!{sys.executable}\nimport os\nos.close(4)\n")
    exe.chmod(0o755)
    state, why = live.one("chrome")
    assert state == live.FAILS and "closed its pipe" in why


def test_chrome_runs_without_its_sandbox_only_as_root(chrome, monkeypatch):
    """Chrome refuses to start as root with its sandbox on; as anyone else
    the sandbox stays."""
    seen = []
    real = live.check_chrome

    def keep(place):
        why = real(place)
        seen.append(json.loads((place.home / "argv.json").read_text()))
        return why

    monkeypatch.setattr(
        live, "CHECKS", {**live.CHECKS, "chrome": (*live.CHECKS["chrome"][:2], keep)}
    )
    for uid in (0, 1000):
        monkeypatch.setattr(live.os, "geteuid", lambda uid=uid: uid)
        assert live.one("chrome") == (live.WORKS, "")
    assert ["--no-sandbox" in argv for argv in seen] == [True, False]
