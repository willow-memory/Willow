"""changelog.py: a pull request that changes more than the docs says so in
CHANGELOG.md.

    python adapters/stdlib/ci/changelog.py --base REF --pr N

Compares the checkout with REF (the branch the pull request goes into). When
every changed file is Markdown, nothing is owed. Otherwise CHANGELOG.md's
`## Unreleased` section must hold a line, added by this pull request, that
ends with its number: `(#N)`. A line elsewhere in the file, or one that
names another pull request, doesn't count.

CI runs it on every pull request, where the number is known. Exit codes,
the kernel's: 0 the line is there, or nothing is owed; 42 git couldn't
compare with REF; 2 the line is missing, or a bad command line.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: changelog.py --base REF --pr N"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def unreleased(text: str) -> list[str]:
    """The lines of the `## Unreleased` section."""
    m = re.search(r"^## Unreleased\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).splitlines() if m else []


def check(base: str, pr: str) -> int:
    changed = git("diff", "--name-only", f"{base}...HEAD")
    if changed.returncode != 0:
        print(f"unreachable: git can't compare with {base}: {changed.stderr.strip()}")
        return kernel.ESCALATE
    files = [f for f in changed.stdout.split() if f]
    code = [f for f in files if not f.endswith(".md")]
    if not code:
        print(f"docs only ({len(files)} files): no changelog line owed")
        return kernel.ALIVE
    before = git("show", f"{base}:CHANGELOG.md")
    old = set(unreleased(before.stdout)) if before.returncode == 0 else set()
    now = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # a wrapped entry ends its last line with the number
    added = [ln for ln in unreleased(now) if ln not in old]
    if any(ln.rstrip().endswith(f"(#{pr})") for ln in added):
        print(f"CHANGELOG.md: this pull request's line (#{pr}) is under Unreleased")
        return kernel.ALIVE
    print(
        f"refused: {len(code)} files beyond the docs changed ({', '.join(code[:3])}"
        f"{', …' if len(code) > 3 else ''}), and CHANGELOG.md has no new line under "
        f"## Unreleased ending (#{pr})",
        file=sys.stderr,
    )
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if (
        len(argv) != 4
        or argv[0] != "--base"
        or argv[2] != "--pr"
        or not argv[3].isdigit()
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    return check(argv[1], argv[3])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
