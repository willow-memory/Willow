"""commands.py: an add-on's COMMANDS line found from its usage lines, held
to what the contract test asks; none found said line by line; written in
its place A to Z; and the repo's own tools and readers refused."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("commands", HERE / "commands.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)

#: an add-on: answers `--box DIR QUESTION...` with 0, refuses anything else
#: naming itself; its first usage line never works (a server it would start)
ADD_ON = '''"""tally.py: counts. Python 3.9+.

    python adapters/stdlib/tally/tally.py serve --port N     a server, never
    python adapters/stdlib/tally/tally.py --box DIR [--now TS]
            QUESTION...                                       one question
"""
import sys
from pathlib import Path
a = sys.argv[1:]
if len(a) >= 3 and a[0] == "--box" and Path(a[1]).is_dir() and a[2:] == ["tomatoes"]:
    sys.exit(0)
print("usage: tally.py --box DIR QUESTION", file=sys.stderr)
sys.exit(2)
if __name__ == "__main__":
    pass
'''


@pytest.fixture
def stdlib():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "tally").mkdir()
        (Path(tmp) / "tally" / "tally.py").write_text(ADD_ON, encoding="utf-8")
        yield Path(tmp)


def test_usage_lines_are_read_with_what_runs_on_and_without_what_is_said_of_them(
    stdlib,
):
    assert commands.usage_lines(stdlib / "tally" / "tally.py") == [
        ["serve", "--port", "N"],
        ["--box", "DIR", "[--now", "TS]", "QUESTION..."],
    ]


def test_a_placeholder_is_filled_by_what_it_names():
    got = commands.candidates([
        ["--box", "DIR", "--to", "FILE.html", "--born", "YYYY-MM-DD", "QUESTION..."],
        ["ask", "--questions", "FILE", "--url", "URL", "[--now", "TS]"],
    ])  # fmt: skip
    assert got[0] == ["--box", "{box}", "--to", "{tmp}/out.html", "--born", "2026-10-01", "tomatoes"]  # fmt: skip
    assert [
        "ask",
        "--questions",
        "{pile}/garden.md",
        "--url",
        "http://127.0.0.1:9/",
    ] in got
    assert ["ask", "--questions", "{pile}/garden.md", "--url", "http://127.0.0.1:9/",
            "--now", commands.NOW] in got  # fmt: skip


def test_the_first_line_that_keeps_the_contract_is_its_line(stdlib):
    line, tried = commands.suggest("tally", stdlib)
    assert line == '("tally.py", ["--box", "{box}", "tomatoes"])'
    assert tried[0][0] == ["serve", "--port", "1"] and tried[0][1].startswith("exit 2")
    assert tried[-1] == (["--box", "{box}", "tomatoes"], "")


def test_none_that_keeps_it_is_said_line_by_line(stdlib):
    script = stdlib / "tally" / "tally.py"
    script.write_text(ADD_ON.replace("sys.exit(0)", "sys.exit(1)"), encoding="utf-8")
    line, tried = commands.suggest("tally", stdlib)
    assert line is None and tried and all(why for _, why in tried)


def test_its_line_goes_into_commands_a_to_z_and_never_twice():
    with tempfile.TemporaryDirectory() as tmp:
        contract = Path(tmp) / "test_contract.py"
        contract.write_text(
            'NOW = ["--now", "x"]\nCOMMANDS: dict[str, tuple[str, list[str]]] = {\n'
            '    "alpha": ("alpha.py", ["--box", "{box}"]),\n'
            '    "zed": ("zed.py", ["--box", "{box}"]),\n}  # fmt: skip\n',
            encoding="utf-8",
        )
        commands.write("mid", '("mid.py", [*NOW])', contract)
        lines = contract.read_text(encoding="utf-8").splitlines()
        assert lines[2:5] == ['    "alpha": ("alpha.py", ["--box", "{box}"]),',
                              '    "mid": ("mid.py", [*NOW]),',
                              '    "zed": ("zed.py", ["--box", "{box}"]),']  # fmt: skip
        with pytest.raises(commands.Refused, match="already has a line"):
            commands.write("mid", '("mid.py", [])', contract)


@pytest.mark.parametrize("name, why", [("ci", "own tool"), ("pdf-text", "reader"),
                                       ("not-here", "no adapters")])  # fmt: skip
def test_the_repos_own_tools_readers_and_no_folder_are_refused(name, why, monkeypatch):
    monkeypatch.setattr(commands, "_readers_block", lambda: '"pdf-text": ("x.py",')
    with pytest.raises(commands.Refused, match=why):
        commands.suggest(name)


@pytest.mark.parametrize("argv", [[], ["suggest"], ["guess", "x"], ["suggest", "-x"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "commands.py"), *argv],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 2 and "commands.py" in got.stderr
