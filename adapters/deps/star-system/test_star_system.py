"""star-system: a deterministic adapter for science_bitch's star_system. It
imports the project's core from --repo, evolves the system and writes cited
lines to --to; the bytes are the same every run, an unknown body or a bad
command line is refused, and a close encounter halts. These run against a
minimal stand-in checkout (example_repo/), so the deps gate needs no network;
the real project is what --repo points at in use."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "star_system.py"
REPO = HERE / "example_repo"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_writes_a_cited_document_for_a_system(tmp_path):
    out = tmp_path / "sys.md"
    got = run("--repo", str(REPO), "--star", "sun", "--planet", "earth",
              "--planet", "jupiter", "--orbits", "1", "--to", str(out))  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    page = out.read_text()
    assert page.startswith("# star system: sun with earth, jupiter")
    assert "Kepler period" in page
    assert "energy drift" in page and "angular momentum drift" in page
    assert "https://github.com/AllHailSeizure/science_bitch" in page  # cited
    assert "## sources" in page


def test_the_output_is_deterministic(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    args = ["--repo", str(REPO), "--planet", "earth", "--planet", "jupiter",
            "--orbits", "2"]  # fmt: skip
    run(*args, "--to", str(a))
    run(*args, "--to", str(b))
    assert a.read_bytes() == b.read_bytes(), "same inputs, same bytes"


def test_an_unknown_body_is_refused(tmp_path):
    out = tmp_path / "x.md"
    bad_star = run("--repo", str(REPO), "--star", "vega", "--to", str(out))
    assert bad_star.returncode == 2 and "unknown star" in bad_star.stderr
    bad_planet = run("--repo", str(REPO), "--planet", "krypton", "--to", str(out))
    assert bad_planet.returncode == 2 and "unknown planet" in bad_planet.stderr
    assert not out.exists()


def test_a_close_encounter_halts_with_42(tmp_path):
    out = tmp_path / "x.md"
    got = run("--repo", str(REPO), "--planet", "inner", "--orbits", "1",
              "--to", str(out))  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    assert "encounter" in got.stdout.lower()


def test_not_a_science_bitch_checkout_is_refused(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("--repo", str(empty), "--to", str(tmp_path / "x.md"))
    assert got.returncode == 2 and "not a science_bitch checkout" in got.stderr


def test_it_refuses_a_missing_output_folder(tmp_path):
    got = run("--repo", str(REPO), "--to", str(tmp_path / "nope" / "x.md"))
    assert got.returncode == 2 and "does not exist" in got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    out = tmp_path / "x.md"
    for argv in (
        [],  # nothing
        ["--repo", str(REPO)],  # no --to
        ["--to", str(out)],  # no --repo
        [
            "--repo",
            str(REPO),
            "--to",
            str(out),
            "--planet",
            "earth",
            "--planet",
            "earth",
        ],  # a duplicate planet
        ["--repo", str(REPO), "--to", str(out), "--orbits", "0"],  # orbits <= 0
        ["--repo", str(REPO), "--to", str(out), "--orbits", "soon"],  # not a number
        ["--repo", str(REPO), "--to", str(out), "--stray"],  # unknown flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "star_system.py" in got.stderr, (
            argv,
            got.stderr,
        )
