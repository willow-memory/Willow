"""made.py: every made file made again, or checked, in MADE's order; what's
stale or failed is named; and the repo's own made files are current."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("made", HERE / "made.py")
made = importlib.util.module_from_spec(spec)
spec.loader.exec_module(made)

#: a generator: `write` appends its name to order.txt and makes its file;
#: `check` exits 1 while its file is missing
GENERATOR = """import sys
from pathlib import Path
name, out = {name!r}, Path({out!r})
if sys.argv[1:] == ["write"]:
    with open("order.txt", "a") as f:
        f.write(name + "\\n")
    out.write_text("made")
    print("wrote", out)
elif sys.argv[1:] == ["check"]:
    if not out.exists():
        print(out, "would change")
        sys.exit(1)
else:
    sys.exit({broken})
"""


@pytest.fixture
def repo():
    """Two generators, in scratch made with tempfile."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        for name in ("one", "two"):
            (r / f"{name}.py").write_text(
                GENERATOR.format(name=name, out=f"{name}.txt", broken=2)
            )
        yield r


TABLE = (("one's file", "one.py"), ("two's file", "two.py"))


def test_check_names_what_is_stale_and_write_makes_each_in_order(repo):
    got = made.run(repo, "check", TABLE)
    assert [(w, c) for w, c, _ in got] == [("one's file", 1), ("two's file", 1)]
    assert "one.txt would change" in got[0][2]
    assert all(c == 0 for _, c, _ in made.run(repo, "write", TABLE))
    assert (repo / "order.txt").read_text() == "one\ntwo\n"
    assert all(c == 0 for _, c, _ in made.run(repo, "check", TABLE))


def test_a_script_that_fails_is_said_by_what_it_makes(repo):
    (repo / "two.py").write_text("import sys\nprint('no'); sys.exit(3)\n")
    got = made.run(repo, "write", TABLE)
    assert got[0][1] == 0 and got[1] == ("two's file", 3, "no")


def test_every_script_in_made_is_here_and_the_repos_made_files_are_current():
    assert all((made.ROOT / s).is_file() for _, s in made.MADE)
    stale = [(w, said) for w, c, said in made.run(made.ROOT, "check") if c]
    assert stale == [], "python adapters/stdlib/ci/made.py write"


@pytest.mark.parametrize("argv", [[], ["writ"], ["check", "more"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "made.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "made.py" in got.stderr
