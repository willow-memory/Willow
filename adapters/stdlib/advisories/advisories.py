"""advisories.py: your locked dependencies matched to a downloaded advisory
database, offline. Python 3.9+.

    python adapters/stdlib/advisories/advisories.py --box DIR  [--db OSV_DIR] [--json]
    python adapters/stdlib/advisories/advisories.py --from FOLDER [--db OSV_DIR] [--json]

The lockfiles in your folder (the box's pile, or any folder) name a version
of each dependency. A downloaded OSV database -- the one osv.dev exports per
ecosystem, or the GitHub advisory database, each a tree of OSV JSON files --
names which versions of a package an advisory covers. This reads both and
says which of your locked dependencies a known advisory names, and since
when:

    advisories: populated, 2 of 2 dependencies named by a known advisory
    ## named by a known advisory
      PyPI  requests 2.19.1  GHSA-x84v-xcm2-53pg  CVE-2018-18074  since 2018-10-09  Credentials leak
      npm   lodash 4.17.4  GHSA-jf85-cpcp-j695  CVE-2020-8203  since 2020-07-15  Prototype Pollution

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract), and `--json` gives the same report as one JSON object:
a row per dependency and advisory, the ecosystem and then the package, its
version and the advisory.

Lockfiles read: `package-lock.json` (npm), `requirements.txt` (PyPI, the
`name==version` pins), `poetry.lock` (PyPI) and `Cargo.lock` (crates.io).
Paths inside a `node_modules`, `vendor` or `.git` folder are skipped, so a
dependency is counted once.

A version is matched to an advisory by the advisory's own `versions` list
when it has one, else by its ranges: a plain numeric version (`1`, `2.4`,
`3.1.6`) is compared to the range's bounds. A version or a bound that is not
plain numeric (a prerelease, an epoch, a local tag) is not guessed at: that
pair is listed apart, under "couldn't compare -- check by hand", never
silently dropped and never silently matched.

With no `--db`, it lists the dependencies it found and stops: an inventory,
nothing to match against, its first line saying no database was given. It
only reads, and writes nothing. Exit codes, the kernel's: 0 no advisory
names your dependencies, or there are none to check (empty), or the
inventory with no `--db` (populated); 42 one does, or one couldn't be
compared, and waits on you (populated); 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "advisories"

SKIP = {"node_modules", "vendor", ".git"}
LOCKS = ("package-lock.json", "requirements.txt", "poetry.lock", "Cargo.lock")
PLAIN = re.compile(r"v?\d+(?:\.\d+)*$")
PACKAGE = re.compile(r'^name\s*=\s*"([^"]+)"', re.M)


def norm(ecosystem: str, name: str) -> tuple[str, str]:
    """A package key both sides agree on: PyPI names fold case and -_. to -."""
    eco = {"pypi": "PyPI", "npm": "npm", "crates.io": "crates.io"}.get(
        ecosystem.lower(), ecosystem
    )
    if eco == "PyPI":
        name = re.sub(r"[-_.]+", "-", name).lower()
    return eco, name


def plain(v: str):
    """The comparable tuple of a plain numeric version, or None if it isn't one."""
    return tuple(int(x) for x in v.lstrip("vV").split(".")) if PLAIN.match(v) else None


def cmp_plain(a: str, b: str):
    """-1/0/1 for two plain versions, padded to the same length; None if either
    isn't plain numeric."""
    ta, tb = plain(a), plain(b)
    if ta is None or tb is None:
        return None
    n = max(len(ta), len(tb))
    ta, tb = ta + (0,) * (n - len(ta)), tb + (0,) * (n - len(tb))
    return (ta > tb) - (ta < tb)


def in_range(version: str, events: list[dict]):
    """True/False that `version` falls in a run of introduced..fixed/last_affected
    events, or None if a needed comparison can't be made on plain numbers."""
    introduced = None  # None means not yet opened; "0" means from the start
    for ev in events:
        if "introduced" in ev:
            introduced = ev["introduced"]
        elif "fixed" in ev or "last_affected" in ev:
            if introduced is None:
                continue
            lo_ok = introduced == "0"
            if not lo_ok:
                c = cmp_plain(version, introduced)
                if c is None:
                    return None
                lo_ok = c >= 0
            bound = ev.get("fixed", ev.get("last_affected"))
            c = cmp_plain(version, bound)
            if c is None:
                return None
            hi_ok = c < 0 if "fixed" in ev else c <= 0
            if lo_ok and hi_ok:
                return True
            introduced = None
    return False


def matches(affected: dict, version: str):
    """True (named), False (not named), or None (couldn't compare)."""
    if version in affected.get("versions", []):
        return True
    unsure = False
    for rng in affected.get("ranges", []):
        if rng.get("type") == "GIT":
            continue
        got = in_range(version, rng.get("events", []))
        if got is True:
            return True
        if got is None:
            unsure = True
    return None if unsure else False


def osv_files(db: Path):
    for p in sorted(db.rglob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (ValueError, OSError):
            continue
        if isinstance(doc, dict) and doc.get("id") and "affected" in doc:
            yield doc


def index(db: Path) -> dict:
    """(ecosystem, name) -> [(advisory doc, affected entry)]."""
    out: dict = {}
    for doc in osv_files(db):
        for aff in doc.get("affected", []):
            pkg = aff.get("package", {})
            if pkg.get("ecosystem") and pkg.get("name"):
                out.setdefault(norm(pkg["ecosystem"], pkg["name"]), []).append(
                    (doc, aff)
                )
    return out


def npm_locked(doc: dict):
    seen = set()
    for where, info in doc.get("packages", {}).items():  # lockfile v2/v3
        name = where.split("node_modules/")[-1]
        if where and name and info.get("version"):
            seen.add((name, info["version"]))

    def walk(deps):  # lockfile v1
        for name, info in deps.items():
            if info.get("version"):
                seen.add((name, info["version"]))
            walk(info.get("dependencies", {}))

    walk(doc.get("dependencies", {}))
    return [("npm", n, v) for n, v in seen]


def locked(path: Path):
    """(ecosystem, name, version) from one lockfile; [] if it can't be read."""
    name = path.name
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if name == "package-lock.json":
        try:
            return npm_locked(json.loads(text))
        except ValueError:
            return []
    if name == "requirements.txt":
        out = []
        for line in text.splitlines():
            line = line.split("#", 1)[0].split(";", 1)[0].strip()
            m = re.match(r"^([A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*==\s*([^\s]+)$", line)
            if m:
                out.append(("PyPI", m.group(1), m.group(2)))
        return out
    eco = "PyPI" if name == "poetry.lock" else "crates.io"
    out = []
    for block in text.split("[[package]]")[1:]:
        head = block.split("[[", 1)[0]
        nm = re.search(r'name\s*=\s*"([^"]+)"', head)
        ver = re.search(r'version\s*=\s*"([^"]+)"', head)
        if nm and ver:
            out.append((eco, nm.group(1), ver.group(1)))
    return out


def dependencies(folder: Path):
    """Every (ecosystem, name, version) locked in the folder, de-duplicated."""
    out = set()
    for p in sorted(folder.rglob("*")):
        if p.name in LOCKS and not SKIP & set(p.relative_to(folder).parts[:-1]):
            out.update(locked(p))
    return sorted(out)


def since(doc: dict) -> str:
    return (doc.get("published") or doc.get("modified") or "")[:10]


def cve(doc: dict) -> str:
    return next((a for a in doc.get("aliases", []) if a.startswith("CVE-")), "")


def audit(folder: Path, db):
    """(named, unsure): each a list of (eco, name, version, [hit dicts])."""
    deps = dependencies(folder)
    if db is None:
        return deps, None, None
    idx = index(db)
    named, unsure = [], []
    for eco, name, ver in deps:
        hits, odd = [], []
        for doc, aff in idx.get(norm(eco, name), []):
            got = matches(aff, ver)
            row = {"id": doc["id"], "cve": cve(doc), "since": since(doc),
                   "summary": (doc.get("summary") or "").strip()}  # fmt: skip
            (hits if got is True else odd if got is None else []).append(row)
        uniq = {h["id"]: h for h in hits}
        if uniq:
            named.append((eco, name, ver, sorted(uniq.values(), key=lambda h: h["id"])))
        else:
            left = {h["id"]: h for h in odd if h["id"]}
            if left:
                unsure.append(
                    (eco, name, ver, sorted(left.values(), key=lambda h: h["id"]))
                )
    return deps, named, unsure


def hit_rows(eco, name, ver, hits) -> list[tuple[str, str]]:
    """A report row per advisory a dependency is named by: where is its
    ecosystem, what the package, its version and the advisory."""
    out = []
    for h in hits:
        what = [f"{name} {ver}", h["id"], h["cve"], f"since {h['since'] or '?'}",
                h["summary"][:48]]  # fmt: skip
        out.append((eco, "  ".join(x for x in what if x)))
    return out


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
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


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--from", "--db"):
            opts[a] = next(it, "")
        elif a == "--json":
            opts[a] = "yes"
        else:
            opts["bad"] = a
    src = [o for o in ("--box", "--from") if o in opts]
    if "bad" in opts or len(src) != 1 or not all(opts.get(o) for o in opts):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    as_json = "--json" in opts
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
    db = None
    if "--db" in opts:
        db = Path(opts["--db"])
        if not db.is_dir():
            print(f"refused: {db} isn't a folder", file=sys.stderr)
            return kernel.REFUSED

    deps, named, unsure = audit(folder, db)
    if not deps:
        say(report(NAME, "empty", "no locked dependency in your folder's lockfiles", []),
            as_json)  # fmt: skip
        return kernel.ALIVE
    n = f"{len(deps)} locked dependenc{'y' if len(deps) == 1 else 'ies'}"
    if db is None:
        said = f"{n}; no advisory database given (--db), so none was matched"
        say(report(NAME, "populated", said,
                   [(None, [(eco, f"{name} {ver}") for eco, name, ver in deps])]),
            as_json)  # fmt: skip
        return kernel.ALIVE
    if not named and not unsure:
        say(report(NAME, "empty", f"no known advisory names your {n}", []), as_json)
        return kernel.ALIVE
    said = (f"{len(named)} of {len(deps)} dependencies named by a known advisory"
            + (f"; {len(unsure)} couldn't be compared" if unsure else ""))  # fmt: skip
    groups = [
        ("named by a known advisory", [r for d in named for r in hit_rows(*d)]),
        (
            "couldn't compare -- check by hand",
            [r for d in unsure for r in hit_rows(*d)],
        ),
    ]
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
