"""realdata.py: an add-on's COMMANDS line run on each person's folder, under
the guard; a traceback, a breach, a hang or an odd exit fails it, a refusal
is said and holds; a reader runs mirror; and --base finds what changed."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("realdata", HERE / "realdata.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

#: an add-on: counts the pile's files; `boom` in a file name is a traceback,
#: `refuse` a refusal
ADD_ON = """import sys
from pathlib import Path
args = sys.argv[1:]
if args[:1] != ["--from"] or len(args) != 2:
    print("usage: tally.py --from DIR", file=sys.stderr)
    sys.exit(2)
names = [p.name for p in Path(args[1]).iterdir()]
if "boom" in names:
    raise ValueError("a file it didn't expect")
if "refuse" in names:
    print("refused: not this kind of folder", file=sys.stderr)
    sys.exit(2)
print(f"{len(names)} files")
"""


@pytest.fixture
def world():
    """An add-on and three people's folders, in scratch made with tempfile."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "stdlib" / "tally").mkdir(parents=True)
        (root / "stdlib" / "tally" / "tally.py").write_text(ADD_ON)
        lives = {}
        for person, files in (
            ("ann", ["a.txt", "b.txt"]),
            ("bo", ["refuse"]),
            ("cy", ["c.txt"]),
        ):
            life = root / "demo" / person / "life"
            life.mkdir(parents=True)
            for f in files:
                (life / f).write_text("hi\\n")
            lives[person] = life
        contract = types.SimpleNamespace(
            COMMANDS={"tally": ("tally.py", ["--from", "{pile}"])}, READERS={}
        )
        yield root, lives, contract


def test_each_person_gets_a_run_and_a_refusal_is_said_but_holds(world):
    root, lives, contract = world
    rows, held = rd.run(["tally"], lives, contract, root / "stdlib")
    assert held
    assert [(r[1], r[2], r[4]) for r in rows] == [
        ("ann", "", "2 files"),
        ("bo", "", "refused: not this kind of folder"),
        ("cy", "", "1 files"),
    ]


def test_a_traceback_on_a_real_folder_fails_it(world):
    root, lives, contract = world
    (lives["cy"] / "boom").write_text("")
    rows, held = rd.run(["tally"], lives, contract, root / "stdlib")
    assert not held and rows[-1][1:3] == ("cy", "a traceback")


def test_a_reader_runs_mirror_over_the_folder():
    contract = types.SimpleNamespace(COMMANDS={}, READERS={"plain": ("plain.py", {})})
    assert rd.row_of(contract, "plain") == (
        "plain.py",
        ["mirror", "--from", "{pile}", "--to", "{tmp}/mirror"],
    )
    with pytest.raises(rd.Refused, match="no line in COMMANDS"):
        rd.row_of(contract, "other")


def test_base_finds_the_stdlib_add_ons_a_branch_changed():
    got = rd.changed_add_ons("HEAD")
    assert got == [] or all((rd.STDLIB / n).is_dir() for n in got)


def test_a_real_add_on_on_the_real_demo_people_holds():
    """dice, on every demo person's folder as make_life.py writes it."""
    got = subprocess.run([sys.executable, str(HERE / "realdata.py"), "run", "dice"],
                         capture_output=True, text=True, timeout=300)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    assert "dice on odile: held" in got.stdout


@pytest.mark.parametrize("argv", [[], ["run"], ["go", "dice"], ["run", "--base"],
                                  ["run", "not-an-add-on"], ["run", "-x"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "realdata.py"), *argv],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 2 and "realdata.py" in got.stderr
