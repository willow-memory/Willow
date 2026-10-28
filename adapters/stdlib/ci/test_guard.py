"""The guard catches each broken promise, and passes a kept one.

Each test builds a small repo in a temporary folder with one add-on whose
card makes a promise and whose code keeps or breaks it, then runs that code
the way its tests would, under the guard."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent / "guard"
KERNEL = Path(__file__).resolve().parents[3] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "adapters" / "stdlib").mkdir(parents=True)
    (root / "kernel.py").write_bytes(KERNEL.read_bytes())
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want sun.\n")
    box = tmp_path / "box"
    subprocess.run(
        [sys.executable, str(root / "kernel.py"), "init", "--box", str(box),
         "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW],
        check=True, capture_output=True,
    )  # fmt: skip
    return root, box, pile


def addon(root: Path, writes: str, network: str, code: str) -> Path:
    here = root / "adapters" / "stdlib" / "probe"
    here.mkdir(exist_ok=True)
    (here / "README.md").write_text(
        "<!-- willow-addon\nsection: Play\nline: A probe.\nsource: new\n"
        f"added: 2026-10-23\nwrites: {writes}\nnetwork: {network}\n-->\n# probe\n"
    )
    script = here / "probe.py"
    script.write_text(
        "import sys, os, socket\n"
        f"sys.path.insert(0, {str(root)!r})\n"
        "import kernel\n" + textwrap.dedent(code)
    )
    return script


def run(root: Path, script: Path, *args: str) -> tuple[int, str]:
    log = root.parent / "guard.log"
    log.unlink(missing_ok=True)
    env = dict(os.environ, PYTHONPATH=str(GUARD), WILLOW_GUARD_LOG=str(log),
               WILLOW_GUARD_ROOT=str(root), PYTHONDONTWRITEBYTECODE="1")  # fmt: skip
    got = subprocess.run([sys.executable, str(script), *args], env=env,
                         capture_output=True, text=True)  # fmt: skip
    return got.returncode, log.read_text() if log.exists() else ""


def test_writing_a_file_when_the_card_says_nothing(repo, tmp_path):
    """An add-on can't widen its own reach past its card (CONST-0-3, CONST-III):
    what the card doesn't list, it can't do (CONST-II-1)."""
    root, _, _ = repo
    script = addon(root, "nothing", "none", f"open({str(root / 'out.txt')!r}, 'w')\n")
    code, log = run(root, script)
    assert code != 0 and "wrote" in log and "writes: nothing" in log


def test_writing_outside_to_when_the_card_says_to(repo, tmp_path):
    root, _, _ = repo
    to, stray = tmp_path / "mirror", tmp_path / "elsewhere.txt"
    script = addon(
        root,
        "to",
        "none",
        f"""\
        os.makedirs({str(to)!r}, exist_ok=True)
        open(os.path.join({str(to)!r}, 'ok.txt'), 'w').write('fine')
        open({str(stray)!r}, 'w').write('not fine')
    """,
    )
    code, log = run(
        root, script, "mirror", "--from", str(tmp_path / "pile"), "--to", str(to)
    )
    assert (to / "ok.txt").exists() and not stray.exists()
    assert code != 0 and "elsewhere.txt" in log


def test_changing_an_original(repo):
    root, _, pile = repo
    script = addon(
        root, "to", "none", f"open({str(pile / 'a.md')!r}, 'a').write('x')\n"
    )
    code, log = run(
        root, script, "mirror", "--from", str(pile), "--to", str(root.parent / "m")
    )
    assert code != 0 and "changed an original" in log
    assert (pile / "a.md").read_text() == "Tomatoes want sun.\n"


def test_writing_the_box_not_through_the_kernel(repo):
    root, box, _ = repo
    script = addon(root, "record", "none", f"open({str(box / 'record.jsonl')!r}, 'a').write('{{}}')\n")  # fmt: skip
    code, log = run(root, script, "--box", str(box))
    assert code != 0 and "not through the kernel" in log


def test_writing_the_record_through_the_kernel_when_the_card_says_nothing(repo):
    root, box, _ = repo
    code_ = f"kernel.bite(kernel.Path({str(box)!r}), 'tomatoes sun', kernel.now())\n"
    code, log = run(root, addon(root, "nothing", "none", code_), "--box", str(box))
    assert code != 0 and "wrote the record" in log


def test_writing_the_record_through_the_kernel_when_the_card_says_record(repo):
    root, box, _ = repo
    code_ = f"kernel.bite(kernel.Path({str(box)!r}), 'tomatoes sun', kernel.now())\n"
    code, log = run(root, addon(root, "record", "none", code_), "--box", str(box))
    assert code == 0 and log == ""


def test_reading_the_key_itself(repo, tmp_path):
    root, box, _ = repo
    script = addon(root, "nothing", "none", f"open({str(tmp_path / 'key')!r}).read()\n")
    code, log = run(root, script, "--box", str(box))
    assert code != 0 and "read the key itself" in log


def test_going_online_when_the_card_says_none(repo):
    """Nor reach past its card online (CONST-0-3, CONST-III)."""
    root, _, _ = repo
    script = addon(root, "nothing", "none", "socket.getaddrinfo('example.org', 443)\n")
    code, log = run(root, script)
    assert code != 0 and "went online" in log


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="no Unix sockets here")
def test_a_unix_socket_is_this_machine_not_online(repo):
    """A Unix socket reaches only this machine: `network: none` allows it,
    and still catches the same code's lookup of a name."""
    root, _, _ = repo
    script = addon(
        root,
        "nothing",
        "none",
        """\
        import tempfile
        here = os.path.join(tempfile.mkdtemp(), "s")
        server = socket.socket(socket.AF_UNIX)
        server.bind(here)
        server.listen()
        socket.socket(socket.AF_UNIX).connect(here)
        socket.getaddrinfo("example.org", 443)
    """,
    )
    code, log = run(root, script)
    assert code != 0 and "socket.getaddrinfo" in log, log
    assert "socket.connect" not in log, "the Unix socket was not a breach"


def test_reaching_out_when_the_card_says_loopback(repo):
    root, _, _ = repo
    script = addon(
        root,
        "nothing",
        "loopback",
        """\
        socket.getaddrinfo('localhost', 80)
        socket.getaddrinfo('example.org', 443)
    """,
    )
    code, log = run(root, script)
    assert code != 0 and "'example.org'" in log and "localhost" not in log


def test_a_swallowed_breach_is_still_on_the_log(repo):
    root, _, _ = repo
    script = addon(
        root,
        "nothing",
        "none",
        f"""\
        try:
            open({str(root / "out.txt")!r}, 'w')
        except PermissionError:
            pass
    """,
    )
    code, log = run(root, script)
    assert code == 0 and "writes: nothing" in log  # exit 0, and CI still fails it


def test_without_a_log_the_guard_does_nothing(repo):
    root, _, _ = repo
    script = addon(root, "nothing", "none", f"open({str(root / 'out.txt')!r}, 'w')\n")
    got = subprocess.run([sys.executable, str(script)], capture_output=True,
                         env=dict(os.environ, PYTHONPATH=str(GUARD)))  # fmt: skip
    assert got.returncode == 0 and (root / "out.txt").exists()


def test_writing_a_repo_file_by_pattern_and_only_that(repo):
    """A `writes` pattern names repo files segment by segment: `*` never
    crosses a folder."""
    root, _, _ = repo
    (root / "adapters" / "stdlib" / "x").mkdir()
    ok, deeper = (
        root / "adapters" / "stdlib" / "x" / "README.md",
        root / "adapters" / "stdlib" / "x" / "y",
    )
    deeper.mkdir()
    script = addon(
        root,
        "adapters/*/*/README.md",
        "none",
        f"""\
        open({str(ok)!r}, 'w').write('fine')
        open({str(deeper / "README.md")!r}, 'w').write('one folder too deep')
    """,
    )
    code, log = run(root, script)
    assert ok.read_text() == "fine"
    assert code != 0 and "x/y/README.md" in log
