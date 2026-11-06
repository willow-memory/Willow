"""pins.py: the dependencies your manifests declare as a version range that no
lockfile pins, offline. Python 3.9+.

    python adapters/stdlib/pins/pins.py --box DIR [--json]
    python adapters/stdlib/pins/pins.py --from FOLDER [--json]

Two manifests are read: package.json (its `dependencies` and `devDependencies`)
and requirements.txt. A declared value that is not one exact version -- `^1.2.0`,
`~2`, `>=2.0`, `1.2`, `*`, `latest`, a URL or a git spec, a bare name with no
version at all -- is a range. An exact `1.2.3` (with an optional prerelease
tag) or `name==1.2.3` is already pinned, so it is not listed.

The lockfiles say what was actually resolved. They are read by the same reader
the [advisories](../advisories/) add-on uses, so a range is pinned when a lockfile
holds its package at any version. A range no lockfile names is listed, as a report (adapters/stdlib/ci/README.md,
the report contract), each row its ecosystem, then the package and its range:

    pins: populated, 3 of 3 declared ranges have no lockfile pin
    ## no lockfile pins it
      PyPI  requests  >=2.19
      npm   jest      ~29.0.0
      npm   lodash    ^4.17.0

Manifests inside a `node_modules`, `vendor` or `.git` folder are skipped. A
manifest that can't be read is named apart, as "couldn't read -- check by
hand", never silently dropped (it is a group of its own, `couldn't read --
check by hand`, its rows the manifest paths).

With nothing to check it says so (empty) and stops. `--json` gives the same
report as one JSON object. It only reads, and writes nothing. Exit codes, the
kernel's: 0 every declared range is pinned, or there is no range to check (or
no manifest) (empty); 42 a range no lockfile pins, or a manifest that can't be
read (populated), and waits on you; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB / "advisories"))
# advisories inserts the repo root for kernel; one path is enough.
import advisories  # noqa: E402
import kernel  # noqa: E402

SKIP = {"node_modules", "vendor", ".git"}
MANIFESTS = ("package.json", "requirements.txt")
EXACT_NPM = re.compile(r"=?v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.+-]+)?")
NAMED = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(.*)")
EXACT_PIP = re.compile(r"==\s*[^\s*,]+")  # `==2.0`; `==2.0.*` is a prefix, a range
BARE = re.compile(r"(?:[A-Za-z][\w+.-]*://)|[./]")  # a URL or a path: no name


NAME = "pins"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


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
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
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
        said = "no package.json or requirements.txt in your folder"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    unpinned = [r for r in ranges if advisories.norm(r[0], r[1]) not in locked]
    if not unpinned and not unread:
        if not ranges:
            said = "every declared dependency is an exact version; no ranges to check"
        else:
            said = f"all {len(ranges)} declared ranges are pinned by a lockfile"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    said = (f"{len(unpinned)} of {len(ranges)} declared ranges have no lockfile pin"
            + (f"; {len(unread)} couldn't be read" if unread else ""))  # fmt: skip
    groups = [
        ("no lockfile pins it", [(eco, f"{name}  {spec}") for eco, name, spec in unpinned]),
        ("couldn't read -- check by hand", [(rel, "") for rel in unread]),
    ]  # fmt: skip
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
