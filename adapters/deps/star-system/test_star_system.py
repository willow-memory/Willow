"""star-system: a deterministic adapter for science_bitch's star_system. It
imports the project's core from --repo, evolves the system and writes cited
lines to --to; the bytes are the same every run, an unknown body or a bad
command line is refused, and a close encounter halts. These run against a
minimal stand-in checkout (example_repo/), so the deps gate needs no network;
the real project is what --repo points at in use."""

from __future__ import annotations

import re
import shutil
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


def page_of(repo: Path, tmp_path: Path, *argv: str) -> str:
    out = tmp_path / "page.md"
    got = run("--repo", str(repo), "--orbits", "1", *argv, "--to", str(out))
    assert got.returncode == 0, got.stdout + got.stderr
    return out.read_text()


def checkout(tmp_path: Path, edits: dict | None = None, without: tuple = ()) -> Path:
    """A copy of the stand-in checkout with files taken out, or one line of
    a file changed; each change is held to having matched once."""
    repo = tmp_path / "checkout"
    shutil.copytree(REPO, repo, ignore=shutil.ignore_patterns("__pycache__"))
    pkg = repo / "simulations" / "star_system"
    for name in without:
        (pkg / name).unlink()
    for name, (old, new) in (edits or {}).items():
        text = (pkg / name).read_text()
        assert text.count(old) == 1, f"{name}: {old!r} is there {text.count(old)} times"
        (pkg / name).write_text(text.replace(old, new))
    return repo


def test_the_page_names_the_checkouts_own_method_not_the_real_projects(tmp_path):
    page = page_of(REPO, tmp_path)
    assert "with its fixed-step integrator (fixed-velocity-verlet-stand-in)." in page
    assert "## what was run, in the checkout's own names" in page
    assert "- model: planar-newtonian-point-mass-v1\n" in page
    assert "- numerical method: fixed-velocity-verlet-stand-in\n" in page
    assert "Yoshida 1990" not in page and "Yoshida integrator" not in page
    assert "- integrator: the checkout's own, named above" in page
    assert (
        page.index("## conserved")
        < page.index("## what was run")
        < page.index("## sources")
    )


def test_the_setup_digest_is_the_checkouts_own_and_names_the_setup(tmp_path):
    sys.path.insert(0, str(REPO))
    try:
        from simulations.star_system import initialization, persistence
    finally:
        sys.path.remove(str(REPO))
    theirs = persistence.setup_digest(
        initialization.legacy_setup("sun", ("earth", "jupiter"))
    )
    page = page_of(REPO, tmp_path)
    (line,) = re.findall(r"^- setup digest: (.*)$", page, flags=re.M)
    assert (
        line
        == f"sha256:{theirs} (its setup_digest of this star, these planets and this step)"
    )
    other = page_of(REPO, tmp_path, "--planet", "earth")
    assert re.findall(r"sha256:[0-9a-f]{64}", other) != [f"sha256:{theirs}"]
    assert len(re.findall(r"sha256:[0-9a-f]{64}", other)) == 1


def test_a_checkout_from_before_it_named_itself_reads_as_it_did(tmp_path):
    old = checkout(tmp_path, without=("persistence.py", "initialization.py"))
    page = page_of(old, tmp_path)
    assert "with its fixed-step Yoshida integrator." in page
    assert "## what was run" not in page and "setup digest" not in page
    assert "- integrator: Yoshida 1990, doi:10.1016/0375-9601(90)90092-3" in page


def test_a_digest_of_another_start_is_not_given(tmp_path):
    for name, old, new in (
        ("r", "system.r.copy(),", "system.r.copy() + 1e-12,"),
        ("v", "system.v.copy(),", "system.v.copy() * 2,"),
        ("dt", "        system.dt,\n", "        system.dt * 2,\n"),
        ("masses", "system.masses.copy(),", "system.masses.copy() * 2,"),
    ):
        sub = tmp_path / name
        sub.mkdir()
        page = page_of(checkout(sub, {"initialization.py": (old, new)}), sub)
        assert (
            "- setup digest: none given; the setup it names builds another "
            "start than the one run here"
        ) in page, name
        assert "sha256:" not in page, name


def test_a_digest_that_cannot_be_computed_says_why_and_the_run_still_writes(tmp_path):
    broken = checkout(tmp_path, {"persistence.py": (
        "    named = {",
        "    raise ModuleNotFoundError(\"No module named 'matplotlib'\")\n    named = {")})  # fmt: skip
    page = page_of(broken, tmp_path)
    assert ("- setup digest: none given; it could not be computed here "
            "(ModuleNotFoundError: No module named 'matplotlib')") in page  # fmt: skip
    assert "- numerical method: fixed-velocity-verlet-stand-in" in page
    assert "energy drift" in page
    no_setup = tmp_path / "no-setup"
    no_setup.mkdir()
    page = page_of(checkout(no_setup, without=("initialization.py",)), no_setup)
    assert (
        "- setup digest: none given; it could not be computed here (ModuleNotFoundError"
        in page
    )


def test_the_digest_is_taken_before_the_run_moves_the_system(tmp_path):
    # after the run the system is elsewhere; a digest checked then would never match
    for orbits in ("1", "2"):
        out = tmp_path / f"{orbits}.md"
        got = run("--repo", str(REPO), "--orbits", orbits, "--to", str(out))
        assert got.returncode == 0 and "sha256:" in out.read_text(), orbits


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
