"""shell: a willow command for five shells, the kernel's verbs completed,
and --box from WILLOW_BOX only when none was given."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("willow_shell", HERE / "shell.py")
sh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sh)
NOW = ["--now", "2026-10-23T00:00:00Z"]


@pytest.mark.parametrize("shell", sh.SHELLS)
def test_each_shell_gets_a_willow_command_that_runs_this_file(shell):
    got = sh.script(shell, py="/usr/bin/python3")
    assert "/usr/bin/python3" in got and str(sh.HERE) in got and " run" in got
    if shell != "cmd":
        assert all(v in got for v in sh.VERBS)  # the verbs, completed


def test_the_verbs_are_the_kernels():
    usage = KERNEL.read_text(encoding="utf-8").split('"""')[1]
    assert all(f"kernel.py {v}" in usage for v in sh.VERBS)


def test_bash_loads_and_completes(tmp_path):
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("no bash on this machine")
    rc = tmp_path / "rc"
    rc.write_text(sh.script("bash"))
    got = subprocess.run([bash, "-c", f"source {rc}; complete -p willow; type -t willow"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0 and "function" in got.stdout and "bite" in got.stdout


def test_willow_box_is_added_only_when_none_was_given():
    env = {"WILLOW_BOX": "/b"}
    assert sh.with_box(["bite", "q"], env) == ["bite", "--box", "/b", "q"]
    assert sh.with_box(["bite", "--box", "/x", "q"], env) == [
        "bite",
        "--box",
        "/x",
        "q",
    ]
    assert sh.with_box(["test"], env) == ["test"]
    assert sh.with_box(["bite", "q"], {}) == ["bite", "q"]


def test_run_is_the_kernels_command_line(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text("The bus leaves at seven.\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    got = subprocess.run([sys.executable, str(HERE / "shell.py"), "run", "bite", *NOW, "bus"],
                         env={"WILLOW_BOX": str(b), "PATH": ""}, capture_output=True, text=True)  # fmt: skip
    assert (
        got.returncode == 0 and json.loads(got.stdout)["served"][0]["where"] == "n.md:1"
    )


@pytest.mark.parametrize(
    "argv", [[], ["script"], ["script", "tcsh"], ["run"], ["script", "bash", "x"]]
)
def test_a_bad_command_line_is_refused(argv):
    assert sh.main(argv) == 2


def test_run_takes_a_verb_alone(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text("x\n")
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    assert sh.main(["run", "verify"], env={"WILLOW_BOX": str(b)}) == 0
