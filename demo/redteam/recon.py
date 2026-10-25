"""recon.py: willow's read-only add-ons, composed into one authorized-recon
pass over this demo's planted target. Frozen; see FROZEN.json and README.md.

    python demo/redteam/recon.py

It points seven offline, read-only add-ons at `target/` in an attacker's
order of interest and prints what each surfaces. Every add-on it runs
promises writes:nothing and network:none, so the whole pass does too: it
reads and reports, it never exploits, never writes to the target, never
reaches the network. The intel it needs (an OSV tree, registry metadata, a
popular-names list) is committed under `intel/`, and `now` is frozen, so the
pass reads the same every run. Exit 0: it is a report, not a verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
A = ROOT / "adapters" / "stdlib"
TARGET = HERE / "target"
NOW = "2026-10-25"  # frozen, so `outdated` reads the same age every run

#: (label, title, add-on, its arguments) in an attacker's order of interest.
PASS = [
    ("1", "CREDENTIALS IN THE CLEAR",
     "secrets-audit/secrets_audit.py", ["--from", str(TARGET)]),
    ("2", "DEPENDENCIES WITH KNOWN ADVISORIES",
     "advisories/advisories.py", ["--from", str(TARGET), "--db", str(HERE / "intel/osv")]),
    ("3a", "INSTALL SCRIPTS (code run on install)",
     "install-scripts/install_scripts.py", ["--from", str(TARGET)]),
    ("3b", "TYPOSQUAT / DEPENDENCY CONFUSION",
     "typosquat/typosquat.py", ["--from", str(TARGET), "--top", str(HERE / "intel/popular.txt")]),
    ("3c", "UNPINNED VERSION RANGES",
     "pins/pins.py", ["--from", str(TARGET)]),
    ("4", "STALE / ABANDONED DEPENDENCIES",
     "outdated/outdated.py", ["--from", str(TARGET), "--index", str(HERE / "intel/registry"), "--now", NOW]),
    ("5", "RISKY CODE PATTERNS",
     "risky-code/risky_code.py", ["--from", str(TARGET)]),
]  # fmt: skip


def add_on(script: str, args: list[str]) -> tuple[int, str]:
    """Run one add-on read-only against the target; (exit code, its output)."""
    import subprocess

    got = subprocess.run(
        [sys.executable, str(A / script), *args], capture_output=True, text=True
    )
    return got.returncode, (got.stdout.rstrip() or got.stderr.rstrip())


def main(argv: list[str]) -> int:
    print(f"RED-TEAM RECON -- target: {TARGET.relative_to(ROOT).as_posix()}")
    print("read-only: it surfaces attack surface, it does not exploit. "
          "Authorized use only.")  # fmt: skip
    for label, title, script, args in PASS:
        code, out = add_on(script, args)
        print(f"\n[{label}] {title}")
        if code in (0, 42) and out:
            for line in out.splitlines():
                print(f"    {line}" if line.strip() else "")
        else:
            print(f"    (add-on exited {code}; nothing surfaced)")
    print("\nRecon only. Every line is a lead to verify by hand; exploit "
          "nothing without written authorization.")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
