"""whose.py: which change wrote these lines?

    python adapters/stdlib/ci/whose.py [--host FOLDER] PATH:FIRST[-LAST] ...
    python adapters/stdlib/ci/whose.py [--host FOLDER] - < PLACES

For each place, git says which commit last wrote each line. With nothing
more, that is the answer: one line per commit, `COMMIT PATH:LINES`, its
first 12 characters. Only git is needed, wherever the repo lives.

`--host FOLDER` names a host add-on (adapters/stdlib/github is one) whose
`host.json` says how that site titles the merge of a pull request. Then
each commit becomes the pull request that brought it to the branch: the
oldest merge on the branch's own line whose merged side holds the commit
and whose other side doesn't, by its title. A commit made on the branch
itself counts by its own title, for a pull request squashed into it. One
line per pull request, `LABEL PATH:LINES`, LABEL as the host writes it
(`#12` on GitHub, `!12` on GitLab).

A host.json holds `name`, `label` (with `{n}` for the number) and `titles`,
a list of patterns, each with one group: the number. They are tried on a
merge's title, then on the rest of its message.

`-` reads the places from stdin, one per line. A place must be a file git
tracks and a line range inside it: anything else is refused before git is
asked, since the places may come from a report anyone can write.

Exit codes, the kernel's: 0 something found; 42 nothing (no place given,
or, with a host, the lines landed before pull requests); 2 a place or host
refused, or a bad command line.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: whose.py [--host FOLDER] PATH:FIRST[-LAST] ... | whose.py [--host FOLDER] - < PLACES"  # fmt: skip
PLACE = re.compile(r"([\w./-]+):(\d+)(?:-(\d+))?")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def place(text: str) -> tuple[str, int, int]:
    """A place as named, checked before git sees it."""
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


def host(folder: str) -> dict:
    """A host add-on's host.json, its patterns compiled."""
    try:
        h = json.loads((Path(folder) / "host.json").read_text(encoding="utf-8"))
        titles = [re.compile(t, re.M) for t in h["titles"]]
        if (not isinstance(h["name"], str) or "{n}" not in h["label"]
                or not titles or any(t.groups != 1 for t in titles)):  # fmt: skip
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError, re.error):
        raise ValueError(f"{folder} has no host.json with a name, a label with {{n}}, "
                         "and titles each with one group") from None  # fmt: skip
    return {**h, "titles": titles}


def numbered(commit: str, h: dict) -> int | None:
    """The number a commit's message gives, by the host's patterns: its
    title first, then the rest (where GitLab puts `See merge request …!N`)."""
    message = git("log", "-1", "--format=%B", commit).stdout.strip()
    title, _, rest = message.partition("\n")
    for text in (title, rest):
        for t in h["titles"]:
            m = t.search(text)
            if m:
                return int(m.group(1))
    return None


def pr_of(commit: str, h: dict) -> int | None:
    """The pull request that brought `commit` to the branch: the oldest merge
    on the branch's own line whose merged side holds it and whose first
    parent doesn't, else the commit's own title, when it was squashed."""
    merges = git("rev-list", "--first-parent", "--merges", "--reverse",
                 f"{commit}..HEAD").stdout.split()  # fmt: skip
    for m in merges:
        brought = git("merge-base", "--is-ancestor", commit, f"{m}^2").returncode == 0
        had = git("merge-base", "--is-ancestor", commit, f"{m}^1").returncode == 0
        if brought and not had:
            return numbered(m, h)
    return numbered(commit, h)


def whose(places: list[tuple[str, int, int]], h: dict | None) -> list[tuple[str, str]]:
    """(label, where) for each change found: a commit, or with a host its
    pull request, in the order a reader wants (pull requests by number)."""
    found: dict[object, list[str]] = {}
    for path, first, last in places:
        blame = git("blame", "--porcelain", "-L", f"{first},{last}", "--", path)
        commits = dict.fromkeys(
            re.findall(r"^([0-9a-f]{40}) \d+ \d+", blame.stdout, re.M)
        )
        where = f"{path}:{first}" + (f"-{last}" if last != first else "")
        for c in commits:
            key = pr_of(c, h) if h else c[:12]
            if key is not None and where not in found.setdefault(key, []):
                found[key].append(where)
    keys = sorted(found) if h else list(found)
    label = (lambda k: h["label"].format(n=k)) if h else str
    return [(label(k), ", ".join(found[k])) for k in keys]


def main(argv: list[str]) -> int:
    h = None
    try:
        if argv[:1] == ["--host"] and len(argv) >= 2:
            h, argv = host(argv[1]), argv[2:]
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    if argv == ["-"]:
        argv = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
        if not argv:
            print("no place named: nothing to look up")
            return kernel.ESCALATE
    elif not argv or any(a.startswith("-") for a in argv):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        places = [place(a) for a in argv]
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    found = whose(places, h)
    for label, where in found:
        print(f"{label} {where}")
    if not found:
        print(f"no pull request on {h['name']}: these lines landed before pull requests"
              if h else "no commit wrote these lines")  # fmt: skip
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
