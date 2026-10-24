"""pins.py: the dependencies your manifests declare as a version range that no
lockfile pins, offline. Python 3.9+.

    python adapters/stdlib/pins/pins.py --box DIR
    python adapters/stdlib/pins/pins.py --from FOLDER

Two manifests are read: package.json (its `dependencies` and `devDependencies`)
and requirements.txt. A declared value that is not one exact version -- `^1.2.0`,
`~2`, `>=2.0`, `1.2`, `*`, `latest`, a URL or a git spec, a bare name with no
version at all -- is a range. An exact `1.2.3` (with an optional prerelease
tag) or `name==1.2.3` is already pinned, so it is not listed.

The lockfiles say what was actually resolved. They are read by the same reader
the [advisories](../advisories/) add-on uses, so a range is pinned when a lockfile
holds its package at any version. A range no lockfile names is listed:

    PyPI  requests  >=2.19   no lockfile pins it
    npm  jest  ~29.0.0   no lockfile pins it
    npm  lodash  ^4.17.0   no lockfile pins it

    3 of 3 declared ranges have no lockfile pin.

Manifests inside a `node_modules`, `vendor` or `.git` folder are skipped. A
manifest that can't be read is named apart, as "couldn't read -- check by
hand", never silently dropped.

With nothing to check it says so and stops. It only reads, and writes nothing.
Exit codes, the kernel's: 0 every declared range is pinned, or there is no
range to check (or no manifest); 42 a range no lockfile pins, or a manifest
that can't be read, and waits on you; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "advisories"))
import advisories  # noqa: E402
import kernel  # noqa: E402

SKIP = {"node_modules", "vendor", ".git"}
MANIFESTS = ("package.json", "requirements.txt")
EXACT_NPM = re.compile(r"=?v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.+-]+)?")
NAMED = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(.*)")
EXACT_PIP = re.compile(r"==\s*[^\s*,]+")  # `==2.0`; `==2.0.*` is a prefix, a range
BARE = re.compile(r"(?:[A-Za-z][\w+.-]*://)|[./]")  # a URL or a path: no name


def npm_ranges(text: str):
    """(ecosystem, name, range) for each declared range in a package.json, or
    None if it can't be read."""
    try:
        doc = json.loads(text)
    except ValueError:
        return None
    if not isinstance(doc, dict):
        return None
    out = []
    for key in ("dependencies", "devDependencies"):
        block = doc.get(key, {})
        if not isinstance(block, dict):
            return None
        for name, spec in block.items():
            spec = spec if isinstance(spec, str) else json.dumps(spec)
            spec = spec.strip()
            if not EXACT_NPM.fullmatch(spec):
                out.append(("npm", name, spec or "(any)"))
    return out


def pip_ranges(text: str):
    """(ecosystem, name, range) for each requirement that isn't `name==version`."""
    out = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if not line or line.startswith("-"):
            continue  # blank, or an option line: -r, -e, --index-url
        if BARE.match(line):
            out.append(("PyPI", line, "(a url or path)"))
            continue
        m = NAMED.match(line)
        if m is None:
            out.append(("PyPI", line, "(not a requirement)"))
            continue
        spec = m.group(2).strip()
        if EXACT_PIP.fullmatch(spec):
            continue
        out.append(("PyPI", m.group(1), spec or "(any)"))
    return out


def manifests(folder: Path):
    """Every package.json and requirements.txt in the folder, outside vendored
    folders, in a stable order."""
    return [
        p
        for p in sorted(folder.rglob("*"))
        if p.name in MANIFESTS
        and p.is_file()
        and not SKIP & set(p.relative_to(folder).parts[:-1])
    ]


def declared(path: Path):
    """(ecosystem, name, range) for each declared range in one manifest, or None
    if the file can't be read."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if path.name == "package.json":
        return npm_ranges(text)
    return pip_ranges(text)


def check(folder: Path):
    """(manifests found, declared ranges as sorted unique (eco, name, range),
    the locked (eco, name) keys, manifests that couldn't be read)."""
    found = manifests(folder)
    ranges, unread = set(), []
    for path in found:
        got = declared(path)
        if got is None:
            unread.append(path.relative_to(folder).as_posix())
        else:
            ranges.update(got)
    # a `==2.*` line in a requirements file is a prefix, not a lock: no version
    # with a star in it pins anything
    locked = {
        advisories.norm(eco, name)
        for eco, name, ver in advisories.dependencies(folder)
        if "*" not in ver
    }
    return found, sorted(ranges), locked, unread


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--from"):
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

    found, ranges, locked, unread = check(folder)
    if not found:
        print("No package.json or requirements.txt in your folder.")
        return kernel.ALIVE
    unpinned = [r for r in ranges if advisories.norm(r[0], r[1]) not in locked]
    for eco, name, spec in unpinned:
        print(f"{eco}  {name}  {spec}   no lockfile pins it")
    for rel in unread:
        print(f"couldn't read {rel} -- check by hand")
    if not unpinned and not unread:
        if not ranges:
            print("Every declared dependency is an exact version; no ranges to check.")
        else:
            print(f"All {len(ranges)} declared ranges are pinned by a lockfile.")
        return kernel.ALIVE
    print(f"\n{len(unpinned)} of {len(ranges)} declared ranges have no lockfile pin"
          + (f"; {len(unread)} couldn't be read" if unread else "") + ".")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
