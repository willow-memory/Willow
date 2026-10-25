"""novelty.py: a description no demo holds reads as novel (exit 0); one an
existing demo already holds reads as prior art, naming it (exit 42); a bad
command line is refused (exit 2). Writes nothing but its own scratch."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOVELTY = HERE / "novelty.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(NOVELTY), *argv], capture_output=True, text=True
    )


def test_a_combination_no_demo_holds_reads_as_novel():
    # the redteam demo itself holds this; --as leaves its own README out, so
    # the question is whether any *other* demo or the idea pile holds it
    got = run(
        "red team recon composing risky-code advisories outdated typosquat "
        "install-scripts pins over a planted-weakness target",
        "--as",
        "redteam",
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert "novel: these pieces have not been put together before" in got.stdout
    assert "nothing holds half of this description" in got.stdout


def test_a_description_an_existing_demo_holds_reads_as_prior_art():
    # php2shell's own words: it is a fix-localization study, tested several ways
    got = run("whether the changed PHP code points at the fix, tested seven ways")
    assert got.returncode == 42, got.stdout + got.stderr
    assert "a demo already holds half of this description" in got.stdout
    assert "php2shell" in got.stdout


def test_the_nearest_demo_is_named_as_a_pointer_even_when_novel():
    got = run("red team recon over a planted-weakness target, nothing like it before")
    assert "nearest demo (bm25" in got.stdout


def test_a_bad_command_line_is_refused():
    for argv in ([], ["", ""], ["one", "two"], ["   "]):
        got = run(*argv)
        assert got.returncode == 2, (argv, got.stdout, got.stderr)
