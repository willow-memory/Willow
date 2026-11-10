"""projects's tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run([sys.executable, str(HERE / "projects.py")], capture_output=True, text=True)
    assert got.returncode == 2 and "projects.py" in got.stderr
