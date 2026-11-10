"""times.py: test-times.json from CI's JUnit XML: each file's tests summed,
a file not seen kept, a gone one dropped, the file's form kept; and check
names what the json lacks without failing."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("times", HERE / "times.py")
times = importlib.util.module_from_spec(spec)
spec.loader.exec_module(times)

XML = """<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest">
<testcase classname="adapters.stdlib.a11y-check.test_a11y_check" name="a" time="0.25" />
<testcase classname="adapters.stdlib.a11y-check.test_a11y_check" name="b" time="0.30" />
<testcase classname="adapters.stdlib.dice.test_dice.TestRolls" name="c" time="2.0" />
<testcase classname="adapters.stdlib.gone.test_gone" name="d" time="9.0" />
</testsuite></testsuites>"""


@pytest.fixture
def root():
    """Two add-ons' test files, in scratch made with tempfile."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        for rel in ("adapters/stdlib/a11y-check/test_a11y_check.py",
                    "adapters/stdlib/dice/test_dice.py",
                    "adapters/stdlib/new/test_new.py"):  # fmt: skip
            (r / rel).parent.mkdir(parents=True)
            (r / rel).write_text("")
        yield r


def test_each_files_tests_are_summed_under_it_a_class_and_a_dash_folder_too(root):
    assert times.measured([XML], root) == {
        "adapters/stdlib/a11y-check/test_a11y_check.py": pytest.approx(0.55),
        "adapters/stdlib/dice/test_dice.py": 2.0,
    }


def test_what_was_seen_is_new_what_wasnt_kept_and_whats_gone_left_out(root):
    old = {"adapters/stdlib/dice/test_dice.py": 7.0,
           "adapters/stdlib/new/test_new.py": 3.0,
           "adapters/stdlib/gone/test_gone.py": 1.0}  # fmt: skip
    got = times.merged(old, times.measured([XML], root), times.test_files(root))
    assert got == {
        "adapters/stdlib/a11y-check/test_a11y_check.py": 0.6,
        "adapters/stdlib/dice/test_dice.py": 2.0,
        "adapters/stdlib/new/test_new.py": 3.0,
    }
    assert list(got) == sorted(got)


def test_the_file_is_written_as_it_always_is():
    text = times.TIMES.read_text(encoding="utf-8")
    assert times.text_of(json.loads(text)) == text


def test_check_names_what_the_json_lacks_and_never_fails_on_it():
    got = subprocess.run([sys.executable, str(HERE / "times.py"), "check"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode in (0, 42) and "test-times.json" in got.stdout


@pytest.mark.parametrize("argv", [[], ["write"], ["write", "--run"], ["write", "--from"],
                                  ["check", "x"], ["writ", "--from", "x"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "times.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "times.py" in got.stderr


def test_a_folder_with_no_xml_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        got = subprocess.run([sys.executable, str(HERE / "times.py"), "write", "--from", tmp],
                             capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "no JUnit XML" in got.stderr
