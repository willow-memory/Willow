"""What can be taken away, taken away, and what's left still works.

Two copies of the repo, each stripped and run:

- **Without GitHub:** `.github/` and `adapters/stdlib/github/` deleted, and
  the README's add-on list regenerated, as anyone removing an add-on does.
  The kernel, its beats, every other add-on's tests and the vectors all
  pass, so willow is worked on the same with no host at all, or another.
- **The kernel alone:** all of `adapters/` deleted. The kernel's tests, its
  beats and the vectors pass: nothing in the base leans on an add-on.

The docs (`test_docs.py`) aren't run on either: they describe the repo as
it's published, and a stripped copy has removed files they name.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
HOST = ("adapters/stdlib/github/", ".github/")


def listed() -> list[str]:
    got = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True)  # fmt: skip
    return [f for f in got.stdout.splitlines() if (ROOT / f).is_file()]


def stripped(tmp: Path, without: tuple[str, ...]) -> Path:
    """A copy of the repo with every path under `without` left out, committed
    in a git repo of its own, as a checkout would be (some add-ons ask git)."""
    copy = tmp / "willow"
    for rel in listed():
        if not rel.startswith(without):
            (copy / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, copy / rel)
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "stripped"]):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *args],
                       cwd=copy, check=True, capture_output=True)  # fmt: skip
    return copy


def run(copy: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], cwd=copy, capture_output=True,
                          text=True, timeout=900)  # fmt: skip


def passes(copy: Path, *argv: str) -> None:
    got = run(copy, *argv)
    assert got.returncode == 0, f"{' '.join(argv)}:\n{got.stdout[-2000:]}{got.stderr[-1000:]}"  # fmt: skip


PYTEST = ("-m", "pytest", "-q", "-p", "no:cacheprovider")


def test_without_github_everything_else_passes(tmp_path):
    copy = stripped(tmp_path, HOST)
    assert not (copy / ".github").exists() and not (copy / "adapters/stdlib/github").exists()  # fmt: skip
    passes(
        copy, "adapters/stdlib/readme/readme.py", "write"
    )  # as anyone removing an add-on would
    passes(copy, "kernel.py", "test")
    passes(copy, *PYTEST, "test_kernel.py", "adapters/stdlib")
    passes(copy, *PYTEST, "vectors/test_vectors.py", "-k", "as_it_is_now")


def test_the_kernel_alone_passes(tmp_path):
    copy = stripped(tmp_path, ("adapters/",) + HOST)
    assert not (copy / "adapters").exists()
    passes(copy, "kernel.py", "test")
    passes(copy, *PYTEST, "test_kernel.py")
    passes(copy, *PYTEST, "vectors/test_vectors.py", "-k", "as_it_is_now")


@pytest.mark.parametrize("without", [HOST, ("adapters/",) + HOST])
def test_a_leftover_dependency_would_be_caught(tmp_path, without):
    """The strip can fail: a test that reaches for what was taken fails it."""
    copy = stripped(tmp_path, without)
    (copy / "test_kernel.py").write_text(
        (copy / "test_kernel.py").read_text(encoding="utf-8")
        + "\n\ndef test_planted():\n    assert (HERE.parent / 'adapters/stdlib/github/host.json').is_file()\n",  # fmt: skip
        encoding="utf-8",
    )
    assert run(copy, *PYTEST, "test_kernel.py").returncode == 1
