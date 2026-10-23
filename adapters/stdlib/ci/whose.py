"""whose.py: which pull request wrote these lines?

    python adapters/stdlib/ci/whose.py PATH:FIRST[-LAST] ...
    python adapters/stdlib/ci/whose.py form < ISSUE_BODY

For each place, git says which commit last wrote each line, and the pull
request is the one that brought that commit to the branch: the oldest merge
on the branch's own line whose merged side holds the commit and whose
other side doesn't, by its title,
which ends `(#N)` or reads `Merge pull request #N`. A commit made on the
branch itself counts by its own title, for a pull request squashed into it. Prints one
line per pull request found, `#N PATH:LINES`, by number.

`form` reads a security report's body (the issue form's "Where it is"
section, one place per line) and does the same. A security report's workflow
runs it, and names each pull request's author on the report, publicly, so
whoever wrote the lines hears about it from the start.

A place must be a file git tracks, and a line range inside it: anything else
is refused before git is asked, since a report's text is anyone's.

Exit codes, the kernel's: 0 a pull request found; 42 none found (the lines
landed before pull requests, or no place was given); 2 a place refused, or
a bad command line.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: whose.py PATH:FIRST[-LAST] ... | whose.py form < ISSUE_BODY"
PLACE = re.compile(r"([\w./-]+):(\d+)(?:-(\d+))?")
PR = re.compile(r"\(#(\d+)\)$|^Merge pull request #(\d+)")
SECTION = "### Where it is"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def place(text: str) -> tuple[str, int, int]:
    """A place a report names, checked before git sees it."""
    m = PLACE.fullmatch(text.strip().strip("`"))
    if not m:
        raise ValueError(f"{text.strip()!r} isn't PATH:FIRST or PATH:FIRST-LAST")
    path, first = m.group(1), int(m.group(2))
    last = int(m.group(3) or first)
    if path.startswith(("/", "-")) or ".." in path.split("/"):
        raise ValueError(f"{path} isn't a path inside the repo")
    if git("ls-files", "--error-unmatch", "--", path).returncode != 0:
        raise ValueError(f"{path} isn't a file in the repo")
    lines = len(
        (ROOT / path).read_text(encoding="utf-8", errors="replace").splitlines()
    )
    if not 1 <= first <= last <= lines:
        raise ValueError(f"{path} has {lines} lines, not {first}-{last}")
    return path, first, last


def pr_of(commit: str) -> int | None:
    """The pull request that brought `commit` to the branch: the oldest merge
    on the branch's own line whose merged side holds it and whose first
    parent doesn't, else the commit's
    own title when it was squashed."""
    merges = git("rev-list", "--first-parent", "--merges", "--reverse",
                 f"{commit}..HEAD").stdout.split()  # fmt: skip
    for m in merges:
        brought = git("merge-base", "--is-ancestor", commit, f"{m}^2").returncode == 0
        had = git("merge-base", "--is-ancestor", commit, f"{m}^1").returncode == 0
        if brought and not had:
            hit = PR.search(git("log", "-1", "--format=%s", m).stdout.strip())
            return int(hit.group(1) or hit.group(2)) if hit else None
    hit = PR.search(git("log", "-1", "--format=%s", commit).stdout.strip())
    return int(hit.group(1) or hit.group(2)) if hit else None


def whose(places: list[tuple[str, int, int]]) -> list[tuple[int, str]]:
    found: dict[int, list[str]] = {}
    for path, first, last in places:
        blame = git("blame", "--porcelain", "-L", f"{first},{last}", "--", path)
        commits = dict.fromkeys(
            re.findall(r"^([0-9a-f]{40}) \d+ \d+", blame.stdout, re.M)
        )
        for c in commits:
            n = pr_of(c)
            if n is not None:
                where = f"{path}:{first}" + (f"-{last}" if last != first else "")
                found.setdefault(n, [])
                if where not in found[n]:
                    found[n].append(where)
    return [(n, ", ".join(ws)) for n, ws in sorted(found.items())]


def from_form(body: str) -> list[str]:
    """The lines of the form's "Where it is" section, blanks and `_No response_` out."""
    m = re.search(rf"^{re.escape(SECTION)}\s*\n(.*?)(?=^### |\Z)", body, re.M | re.S)
    lines = m.group(1).splitlines() if m else []
    return [ln for ln in (x.strip() for x in lines)
            if ln and ln != "_No response_" and not ln.startswith("```")]  # fmt: skip


def main(argv: list[str]) -> int:
    if argv == ["form"]:
        argv = from_form(sys.stdin.read())
        if not argv:
            print("no place named: nothing to look up")
            return kernel.ESCALATE
    if not argv or any(a.startswith("-") for a in argv):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        places = [place(a) for a in argv]
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    found = whose(places)
    for n, where in found:
        print(f"#{n} {where}")
    if not found:
        print("no pull request: these lines landed before pull requests")
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
