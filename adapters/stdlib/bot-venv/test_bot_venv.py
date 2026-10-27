"""bot-venv: does willow-bot's venv, or any named, have what CI needs? Each venv here is a
real one, made without pip, with a package's metadata written into its
site-packages, so its own Python reports that package as installed. A venv
with pytest and ruff is ready and gets the line that runs CI; a missing
package, a version other than the one pinned, or a Python older than 3.9 is
not ready; a folder with no Python and a Python that doesn't answer are each
said; `--bot` finds the bot's venv by the bot's own rule, and refuses
without a box rather than guess one; the same venvs give the same bytes; a
bad command line is refused."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "bot_venv.py"
spec = importlib.util.spec_from_file_location("bot_venv_addon", SCRIPT)
addon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)


def run(*argv: str, box: dict | None = None) -> subprocess.CompletedProcess:
    """The script, with WILLOW_HOME and WILLOW_VAULT_BOX as `box` says
    (unset unless named), so this machine's own box never leaks in."""
    env = {k: v for k, v in os.environ.items() if k not in addon.BOX_ENV}
    env.update(box or {})
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, env=env
    )


def a_venv(where: Path, **packages: str) -> Path:
    """A venv at WHERE, without pip, holding each package at its version."""
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(where)],
                   check=True, capture_output=True)  # fmt: skip
    rel = addon.python_of(where)
    purelib = subprocess.run(
        [str(where / rel), "-I", "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()  # fmt: skip
    for name, version in packages.items():
        info = Path(purelib) / f"{name}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
        )
    return where


def test_a_venv_with_what_ci_needs_is_ready(tmp_path):
    v = a_venv(tmp_path / "v", pytest="9.1.1", ruff="0.16.7")
    got = run("--venv", str(v))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "  pytest 9.1.1\n  ruff 0.16.7\n" in got.stdout
    rel = addon.python_of(v)
    assert f"  ready: {v}/{rel} adapters/stdlib/ci/ci.py run --box BOX\n" in got.stdout
    assert got.stdout.endswith("1 of 1 ready\n")


def test_a_missing_package_is_not_ready(tmp_path):
    v = a_venv(tmp_path / "v", pytest="9.1.1")
    got = run("--venv", str(v))
    assert got.returncode == 42, got.stdout + got.stderr
    assert "  ruff not installed\n  not ready\n" in got.stdout
    assert "ready:" not in got.stdout and got.stdout.endswith("0 of 1 ready\n")


def test_a_pin_holds_the_version(tmp_path):
    v = a_venv(tmp_path / "v", pytest="9.1.1", ruff="0.15.0")
    assert run("--venv", str(v)).returncode == 0, "no pin, any ruff will do"
    got = run("--venv", str(v), "--needs", "ruff==0.16.7")
    assert got.returncode == 42, got.stdout + got.stderr
    assert "  ruff 0.15.0, but ruff==0.16.7 wanted\n" in got.stdout
    got = run("--venv", str(v), "--needs", "ruff==0.15.0")
    assert got.returncode == 0 and "  ruff 0.15.0\n" in got.stdout


def test_needs_adds_to_pytest_and_ruff_never_drops_them(tmp_path):
    v = a_venv(tmp_path / "v", ruff="0.16.7", coverage="7.6.1")
    got = run("--venv", str(v), "--needs", "coverage")
    assert got.returncode == 42, got.stdout + got.stderr
    assert "  pytest not installed\n  ruff 0.16.7\n  coverage 7.6.1\n" in got.stdout


def test_each_venv_is_said_in_the_order_given(tmp_path):
    good = a_venv(tmp_path / "good", pytest="9.1.1", ruff="0.16.7")
    bare = tmp_path / "bare"
    bare.mkdir()
    got = run("--venv", str(bare), "--venv", str(good))
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.index(str(bare)) < got.stdout.index(str(good))
    assert got.stdout.endswith("1 of 2 ready\n")


def test_a_folder_with_no_python_says_so(tmp_path):
    got = run("--venv", str(tmp_path))
    assert got.returncode == 42
    assert "  no Python in it (bin/python or Scripts/python.exe)\n" in got.stdout


def test_a_python_that_does_not_answer_says_so(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "python").write_bytes(b"not a program\n")
    got = run("--venv", str(tmp_path))
    assert got.returncode == 42
    assert "  its Python (bin/python) didn't answer\n" in got.stdout


def test_a_python_older_than_the_kernels_is_not_ready():
    have = {"pytest": "9.1.1", "ruff": "0.16.7"}
    needs = [("pytest", None), ("ruff", None)]
    lines, ok = addon.verdict({"python": [3, 8, 18], "have": have}, needs)
    assert not ok and lines[0] == "python 3.8.18, older than 3.9"
    lines, ok = addon.verdict({"python": [3, 9, 0], "have": have}, needs)
    assert ok and lines[0] == "python 3.9.0"


def test_the_same_venvs_give_the_same_bytes(tmp_path):
    v = a_venv(tmp_path / "v", pytest="9.1.1", ruff="0.16.7")
    assert run("--venv", str(v)).stdout == run("--venv", str(v)).stdout


def test_a_bad_command_line_is_refused(tmp_path):
    for argv in ([], ["--venv"], ["--venv", str(tmp_path), "--needs"],
                 ["--venv", str(tmp_path), "--needs", "ruff>=0.16"],
                 ["--venv", str(tmp_path), "--stray"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "bot_venv.py [--bot]" in got.stderr, argv
    got = run("--venv", str(tmp_path / "missing"))
    assert got.returncode == 2 and got.stderr.startswith("refused: "), got.stderr
    assert got.stdout == "", "a refusal says nothing about any venv"


def test_bot_finds_the_bots_venv_in_the_box(tmp_path):
    v = a_venv(
        tmp_path / "willow-bot" / "venvs" / "willow-bot", pytest="9.1.1", ruff="0.16.7"
    )
    got = run("--bot", box={"WILLOW_HOME": str(tmp_path)})
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.startswith(f"{v}\n") and got.stdout.endswith("1 of 1 ready\n")


def test_the_old_home_serves_only_while_the_new_one_is_missing(tmp_path):
    new = tmp_path / "willow-bot" / "venvs" / "willow-bot"
    old = tmp_path / "venvs" / "willow-bot"
    environ = {"WILLOW_HOME": str(tmp_path)}
    assert addon.bot_venv(environ) == (new, ""), "neither: the new home, said missing"
    old.mkdir(parents=True)
    assert addon.bot_venv(environ) == (old, "")
    new.mkdir(parents=True)
    assert addon.bot_venv(environ) == (new, ""), "both: the new one wins"


def test_willow_home_comes_first_and_a_blank_one_is_unset(tmp_path):
    home, vault = tmp_path / "home", tmp_path / "vault"
    home.mkdir()
    vault.mkdir()
    both = {"WILLOW_HOME": str(home), "WILLOW_VAULT_BOX": str(vault)}
    assert addon.bot_venv(both)[0] == home / "willow-bot" / "venvs" / "willow-bot"
    blank = {"WILLOW_HOME": "  ", "WILLOW_VAULT_BOX": str(vault)}
    assert addon.bot_venv(blank)[0] == vault / "willow-bot" / "venvs" / "willow-bot"


def test_bot_without_a_box_refuses_and_never_guesses(tmp_path):
    for box, said in (({}, "no box: set WILLOW_HOME or WILLOW_VAULT_BOX"),
                      ({"WILLOW_HOME": "relative/box"}, "is not an absolute path"),
                      ({"WILLOW_HOME": str(tmp_path / "gone")}, "is not an existing folder")):  # fmt: skip
        got = run("--bot", box=box)
        assert got.returncode == 2 and got.stdout == "", got.stdout
        assert (
            got.stderr.startswith("refused: willow-bot's venv: ") and said in got.stderr
        )


def test_a_box_without_the_bots_venv_is_refused_by_name(tmp_path):
    got = run("--bot", box={"WILLOW_VAULT_BOX": str(tmp_path)})
    want = tmp_path / "willow-bot" / "venvs" / "willow-bot"
    assert got.returncode == 2 and got.stderr == f"refused: {want} is not a folder\n"
