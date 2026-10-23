"""changelog.py: a pull request that changes more than the docs says so in
CHANGELOG.md.

    python adapters/stdlib/ci/changelog.py --base REF --pr N

Compares the checkout with REF (the branch the pull request goes into). When
every changed file is Markdown, or CITATION.cff, nothing is owed: a release
moves entries and sets the citation's version, and changes nothing else. Otherwise CHANGELOG.md's
`## Unreleased` section must hold an entry, added by this pull request, that
ends with its number: `(#N)`. An entry is a `- ` line and the indented lines
that wrap it. One elsewhere in the file, or one that names another pull
request, doesn't count.

A bug BUGS.md listed at REF and no longer lists was fixed here, so each one
also owes an entry of this pull request's under `### Fixed` that names it,
`bug #12`.

CI runs it on every pull request, where the number is known. Exit codes,
the kernel's: 0 every entry owed is there, or nothing is owed; 42 git
couldn't compare with REF; 2 an entry is missing, or a bad command line.
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


def unreleased(text: str) -> list[tuple[str, str]]:
    """(heading, entry) for each entry of the `## Unreleased` section, its
    wrapped lines joined; heading is the `### ` it sits under."""
    m = re.search(r"^## Unreleased\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    out, heading = [], ""
    for line in m.group(1).splitlines() if m else []:
        if line.startswith("### "):
            heading = line[4:].strip()
        elif line.startswith("- "):
            out.append((heading, line[2:].strip()))
        elif line.startswith("  ") and line.strip() and out:
            out[-1] = (out[-1][0], f"{out[-1][1]} {line.strip()}")
    return out


def bugs_listed(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"^\| #(\d+) \|", text, re.M)}


def check(base: str, pr: str) -> int:
    changed = git("diff", "--name-only", f"{base}...HEAD")
    if changed.returncode != 0:
        print(f"unreachable: git can't compare with {base}: {changed.stderr.strip()}")
        return kernel.ESCALATE
    files = [f for f in changed.stdout.split() if f]
    code = [f for f in files if not f.endswith(".md") and f != "CITATION.cff"]
    if not code:
        print(f"docs only ({len(files)} files): no changelog line owed")
        return kernel.ALIVE
    before = git("show", f"{base}:CHANGELOG.md")
    old = set(unreleased(before.stdout)) if before.returncode == 0 else set()
    now = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    mine = [e for e in unreleased(now) if e not in old and e[1].endswith(f"(#{pr})")]
    bugs_then = git("show", f"{base}:BUGS.md")
    bugs_now = ROOT / "BUGS.md"
    fixed = sorted(
        bugs_listed(bugs_then.stdout if bugs_then.returncode == 0 else "")
        - bugs_listed(
            bugs_now.read_text(encoding="utf-8") if bugs_now.is_file() else ""
        )
    )
    unnamed = [
        n for n in fixed
        if not any(h == "Fixed" and re.search(rf"\bbug #{n}\b", e) for h, e in mine)
    ]  # fmt: skip
    if mine and not unnamed:
        print(f"CHANGELOG.md: this pull request's entry (#{pr}) is under Unreleased"
              + (f", naming fixed bugs {', '.join(f'#{n}' for n in fixed)}" if fixed else ""))  # fmt: skip
        return kernel.ALIVE
    if not mine:
        print(
            f"refused: {len(code)} files beyond the docs changed ({', '.join(code[:3])}"
            f"{', …' if len(code) > 3 else ''}), and CHANGELOG.md has no new entry under "
            f"## Unreleased ending (#{pr})",
            file=sys.stderr,
        )
    for n in unnamed:
        print(f"refused: BUGS.md no longer lists bug #{n}, and no entry of this pull "
              f"request's under ### Fixed names it as bug #{n}", file=sys.stderr)  # fmt: skip
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
