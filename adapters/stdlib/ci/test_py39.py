"""py39.py: what 3.10 and later added is named by line and version; a
newer module tried with ImportError caught, or given by a conftest.py,
passes; the slip that failed CI on 3.9 is caught; and the repo is clean."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("py39", HERE / "py39.py")
py39 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(py39)


@pytest.mark.parametrize(
    "source, said",
    [
        ('Path("a").write_text("x", newline="")', "write_text(newline=...) (3.10)"),
        ("zip(a, b, strict=True)", "zip(strict=...) (3.10)"),
        ("import itertools\nitertools.pairwise(x)", "itertools.pairwise (3.10)"),
        ("from itertools import batched", "itertools.batched (3.12)"),
        ("import datetime\ndatetime.UTC", "datetime.UTC (3.11)"),
        ("import tomllib", "tomllib (3.11)"),
        ("isinstance(x, int | str)", "isinstance(x, A | B) (3.10)"),
        ("n.bit_count()", ".bit_count() (3.10)"),
        ("raise ExceptionGroup('x', [])", "ExceptionGroup (3.11)"),
    ],
)
def test_what_3_9_lacks_is_named_by_line_and_version(source, said):
    hits = py39.newer(source)
    assert hits and hits[-1][1] == said


def test_what_3_9_has_passes():
    ok = """
from __future__ import annotations
import shlex, itertools
def f(x: int | None) -> list[str]:
    Path("a").write_text("x", encoding="utf-8")
    return shlex.join(["a"]) + str(zip(a, b)) + str(itertools.chain(x))
isinstance(x, (int, str))
"""
    assert py39.newer(ok) == []


def test_a_newer_module_tried_with_importerror_caught_passes():
    assert (
        py39.newer(
            "try:\n    import tomllib\nexcept ImportError:\n    tomllib = None\n"
        )
        == []
    )
    assert py39.newer("try:\n    import tomllib\nexcept ValueError:\n    pass\n") != []


def test_a_module_a_conftest_above_gives_passes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "study" / "tools").mkdir(parents=True)
        (root / "study" / "conftest.py").write_text(
            'import sys\nfrom pip._vendor import tomli\nsys.modules["tomllib"] = tomli\n'
        )
        tool = root / "study" / "tools" / "read.py"
        assert py39.shims(tool, root) == {"tomllib"}
        assert py39.newer("import tomllib", py39.shims(tool, root)) == []
        assert py39.shims(root / "other.py", root) == frozenset()


def test_the_slip_that_failed_ci_on_3_9_is_caught():
    """demo/johnson/make_life.py, before 7a01faa: a TypeError on 3.9 only."""
    before = 'out.write_text(text, encoding="utf-8", newline="")\n'
    assert py39.newer(before) == [(1, "write_text(newline=...) (3.10)")]


def test_the_repo_uses_nothing_newer_than_3_9():
    got = subprocess.run([sys.executable, str(HERE / "py39.py"), "check"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stdout


@pytest.mark.parametrize("argv", [[], ["chek"], ["check", "-x"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "py39.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "py39.py" in got.stderr
