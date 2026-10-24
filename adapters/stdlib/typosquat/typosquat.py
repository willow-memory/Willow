"""typosquat.py: your locked dependencies whose name is one letter off a
popular package's, checked against a list of top packages you downloaded.
Python 3.9+.

    python adapters/stdlib/typosquat/typosquat.py --box DIR  [--top FILE]
    python adapters/stdlib/typosquat/typosquat.py --from FOLDER [--top FILE]

The lockfiles in your folder (the box's pile, or any folder) name each
dependency. A likely typosquat is a name one letter off a popular one:
reqeusts for requests, lodahs for lodash. The `--top` file is a text file of
popular names you downloaded, one per line, either `ecosystem name` (npm,
PyPI, crates.io) or just `name`. A line with an ecosystem is compared only to
dependencies in that ecosystem; a bare name is compared to any:

    npm       reqeusts -> looks like requests  (locked 1.0.0)
    npm       lodahs -> looks like lodash  (locked 4.17.4)

A name equal to a popular one is not flagged, and a name two or more edits
off is not flagged. The distance is optimal string alignment, so exactly one
insert, delete, substitution, or swap of two adjacent letters counts.

Lockfiles read: package-lock.json (npm), requirements.txt (PyPI, the
name==version pins), poetry.lock (PyPI) and Cargo.lock (crates.io), the
same ones the advisories add-on reads (it uses that reader). Paths inside a
node_modules, vendor or .git folder are skipped.

With no --top, it lists the dependencies it found and stops: an inventory,
nothing to compare against. It only reads, and writes nothing. Exit codes,
the kernel's: 0 nothing looks like a popular name (or there are no lockfiles);
42 one does, and waits on you; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "advisories"))
import advisories  # noqa: E402
import kernel  # noqa: E402


def edit_distance(a: str, b: str) -> int:
    """Optimal string alignment distance: the fewest inserts, deletes,
    substitutions and swaps of two adjacent letters that turn a into b. A
    swap counts as one edit, so a typosquat like reqeusts for requests is one
    off, not two."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def read_top(path: Path) -> list[tuple[str | None, str]]:
    """(ecosystem or None, popular name) for each line of the --top file.
    Raises ValueError on a line with more than two words."""
    out = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for n, line in enumerate(text.splitlines(), 1):
        words = line.split("#", 1)[0].split()
        if not words:
            continue
        if len(words) > 2:
            raise ValueError(f"line {n} has more than two words")
        if len(words) == 2:
            eco, name = advisories.norm(words[0], words[1])
            out.append((eco, name))
        else:
            out.append((None, words[0]))
    return out


def near_misses(deps, top):
    """(eco, name, version, [popular names one letter off]) for each dependency
    that is not itself a popular name."""
    hits = []
    for eco, name, ver in deps:
        key = advisories.norm(eco, name)[1]
        popular = {advisories.norm(eco, p)[1] for e, p in top if e in (None, eco)}
        if key in popular:
            continue
        near = sorted(
            p for p in popular
            if abs(len(p) - len(key)) <= 1 and edit_distance(key, p) == 1
        )  # fmt: skip
        if near:
            hits.append((eco, name, ver, near))
    return hits


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--from", "--top"):
            opts[a] = next(it, "")
        else:
            opts["bad"] = a
    src = [o for o in ("--box", "--from") if o in opts]
    if "bad" in opts or len(src) != 1 or not all(opts.get(o) for o in opts):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        folder = Path(kernel.config(box)["pile"])
    else:
        folder = Path(opts["--from"])
        if not folder.is_dir():
            print(f"refused: {folder} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    top = None
    if "--top" in opts:
        path = Path(opts["--top"])
        if not path.is_file():
            print(f"refused: {path} isn't a file", file=sys.stderr)
            return kernel.REFUSED
        try:
            top = read_top(path)
        except ValueError as e:
            print(f"refused: {path}: {e}", file=sys.stderr)
            return kernel.REFUSED

    deps = advisories.dependencies(folder)
    if not deps:
        print("No lockfiles found in your folder.")
        return kernel.ALIVE
    if top is None:
        for eco, name, ver in deps:
            print(f"{eco:9} {name} {ver}")
        print(f"\n{len(deps)} locked dependencies. Point --top at a downloaded list "
              "of popular package names to check them for near-misses.")  # fmt: skip
        return kernel.ALIVE

    hits = near_misses(deps, top)
    if not hits:
        print(
            f"No locked dependency of your {len(deps)} is a letter off a popular name."
        )
        return kernel.ALIVE
    for eco, name, ver, near in hits:
        print(f"{eco:9} {name} -> looks like {', '.join(near)}  (locked {ver})")
    print(f"\n{len(hits)} of {len(deps)} dependencies look like a popular name "
          "-- check the spelling before you install.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
