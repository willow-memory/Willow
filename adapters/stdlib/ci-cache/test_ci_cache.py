"""ci-cache: a cache key per ecosystem from a folder's lockfiles. It groups
lockfiles by ecosystem and prints each one's cache dir and a key that is the
SHA-256 of those files; the same pins give the same key, a changed pin a new
one, and a dependency's own lockfiles under node_modules or a dotfolder never
key the cache. It escalates when there are none and refuses a bad command
line."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE / "ci_cache.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CC), *argv], capture_output=True, text=True
    )


def keys(out: str) -> dict:
    """{ecosystem: key} from the printed lines."""
    got = {}
    for line in out.splitlines():
        m = re.match(r"(\S+)\s+\S+\s+([0-9a-f]{64})", line)
        if m:
            got[m.group(1)] = m.group(2)
    return got


def a_repo(tmp: Path) -> Path:
    folder = tmp / "repo"
    (folder / "pkg").mkdir(parents=True)
    (folder / "requirements.txt").write_text("numpy==2.5.3\n")
    (folder / "pkg" / "package-lock.json").write_text('{"name": "x"}\n')
    return folder


def test_a_key_per_ecosystem(tmp_path):
    got = run("--from", str(a_repo(tmp_path)))
    assert got.returncode == 0, got.stdout + got.stderr
    k = keys(got.stdout)
    assert set(k) == {"pip", "npm"} and "~/.cache/pip" in got.stdout


def test_the_same_pins_give_the_same_key(tmp_path):
    folder = a_repo(tmp_path)
    assert run("--from", str(folder)).stdout == run("--from", str(folder)).stdout


def test_a_changed_pin_gives_a_new_key(tmp_path):
    folder = a_repo(tmp_path)
    before = keys(run("--from", str(folder)).stdout)["pip"]
    (folder / "requirements.txt").write_text("numpy==2.1.0\n")  # a different pin
    after = keys(run("--from", str(folder)).stdout)["pip"]
    assert before != after, "a changed lockfile must change its key"


def test_node_modules_and_dotfolders_do_not_key_the_cache(tmp_path):
    folder = a_repo(tmp_path)
    before = keys(run("--from", str(folder)).stdout)["pip"]
    (folder / "node_modules" / "dep").mkdir(parents=True)
    (folder / "node_modules" / "dep" / "requirements.txt").write_text("evil==1\n")
    (folder / ".hidden").mkdir()
    (folder / ".hidden" / "requirements.txt").write_text("also==1\n")
    after = keys(run("--from", str(folder)).stdout)["pip"]
    assert before == after, "a dependency's or a dotfolder's lockfiles are not walked"


def test_no_lockfiles_escalates(tmp_path):
    empty = tmp_path / "empty"
    (empty / "src").mkdir(parents=True)
    (empty / "readme.md").write_text("no pins here\n")
    got = run("--from", str(empty))
    assert got.returncode == 42 and "nothing to cache" in got.stdout


def test_not_a_folder_is_refused(tmp_path):
    got = run("--from", str(tmp_path / "missing"))
    assert got.returncode == 2 and "is not a folder" in got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["--from", str(a_repo(tmp_path)), "--stray"], ["--stray"]):
        got = run(*argv)
        assert got.returncode == 2 and "ci_cache.py" in got.stderr, (argv, got.stderr)
