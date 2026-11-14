"""demo/redteam: the composition is frozen (every source hashes to what
FROZEN.json records), the pass surfaces every planted weakness without ever
printing a secret's value, and demo/novelty.py scans the composition as
novel. Pure stdlib; writes nothing but its own scratch."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def run(script: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *argv], capture_output=True, text=True
    )


def test_every_source_hashes_to_its_frozen_value():
    # the pre-registration: the target, the intel and the pipeline cannot
    # drift without this failing, so a later pass is the same pass.
    for rel, want in FROZEN["sources"].items():
        got = "sha256:" + hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == want, rel


#: recon.py, frozen, names its add-ons as they were; pins is unpinned now. The
#: pass is run with each add-on read where it is (demo/renamed.py).
RECON = (
    "import sys; sys.path[:0] = [{demo!r}, {here!r}]; import renamed, recon; "
    "recon.PASS = [(a, b, renamed.now(c), d) for a, b, c, d in recon.PASS]; "
    "raise SystemExit(recon.main([]))"
)


def test_the_pass_surfaces_every_planted_weakness():
    got = subprocess.run(
        [sys.executable, "-c", RECON.format(demo=str(HERE.parent), here=str(HERE))],
        capture_output=True, text=True,
    )  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    out = got.stdout
    for section, needles in FROZEN["expect"].items():
        for needle in needles:
            assert needle in out, (section, needle)


def test_no_secret_value_is_ever_printed():
    got = run(HERE / "recon.py")
    # the planted DB password is in the target; recon must never echo it
    assert FROZEN["secret_value_never_shown"] not in got.stdout
    assert FROZEN["secret_value_never_shown"] not in got.stderr


def test_the_composition_scans_as_novel():
    got = run(HERE.parent / "novelty.py", FROZEN["novelty"], "--as", "redteam")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "novel: these pieces have not been put together before" in got.stdout
