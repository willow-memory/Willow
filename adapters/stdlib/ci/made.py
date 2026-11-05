"""made.py: every file the repo makes from its others, made again, or checked. Python 3.9+.

    python adapters/stdlib/ci/made.py write
    python adapters/stdlib/ci/made.py check

Some files are never written by hand: a script makes each from the files
it reads, and a test fails when one is out of date. A change elsewhere
(an add-on's card, a new file, a changelog entry a report quotes) leaves
one stale, and CI says so after the push. MADE lists those scripts, each
with its `write` and `check`: the add-on lists, BUGS.md, FILES.md, the
lists kept A to Z, and a demo's report. `write` runs each one's write in
that order (FILES.md before its folders are sorted); `check` runs each
one's check and names what's stale. create_pr.py runs `write`.

A generator added to the repo goes in MADE, and then into every pull
request's run with no step of its own.

Exit codes, the kernel's: 0 everything made is current (write: it is
now); 2 check: something is stale, or a script failed, or refused.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: made.py write | made.py check"

#: (what it makes, its script) in the order they're made; each script takes
#: `write` and `check`, and check exits non-zero when what it makes is stale
MADE = (
    ("README.md and ADDONS.md's add-on lists", "adapters/stdlib/readme/readme.py"),
    ("BUGS.md", "adapters/stdlib/ci/bugs.py"),
    ("FILES.md's tree", "adapters/stdlib/ci/files.py"),
    ("the lists kept A to Z", "adapters/stdlib/ci/order.py"),
    ("craft-assembly's REPORT.md and checks.md", "demo/craft-assembly/report.py"),
)


def run(root: Path, verb: str, made=MADE) -> list[tuple[str, int, str]]:
    """(what it makes, its exit code, what it printed) for each script."""
    out = []
    for what, script in made:
        got = subprocess.run(
            [sys.executable, str(root / script), verb],
            cwd=root,
            capture_output=True,
            text=True,
        )
        out.append((what, got.returncode, (got.stdout + got.stderr).strip()))
    return out


def main(argv: list[str]) -> int:
    if argv not in (["write"], ["check"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    verb = argv[0]
    bad = []
    for what, code, said in run(ROOT, verb):
        print(f"── {what}")
        if said:
            print(said)
        if code != 0:
            bad.append(what)
    if bad:
        why = "stale" if verb == "check" else "its script failed"
        print(f"\n{why}: {'; '.join(bad)}")
        if verb == "check":
            print("python adapters/stdlib/ci/made.py write makes them again")
        return kernel.REFUSED
    print(f"\neverything made is current{' now' if verb == 'write' else ''}")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
