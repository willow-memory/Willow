"""outdated.py: how old each locked dependency is, and which are yanked,
deprecated or long unmaintained -- from a registry index you downloaded.
Python 3.9+.

    python adapters/stdlib/outdated/outdated.py --box DIR  [--index DIR] [--now YYYY-MM-DD]
    python adapters/stdlib/outdated/outdated.py --from FOLDER [--index DIR] [--now YYYY-MM-DD]

It reads the same lockfiles the [advisories](../advisories/) add-on does (it
uses that reader), so the dependencies it lists are the same ones. For each,
with `--index` pointed at downloaded registry metadata, it says how old the
locked version is and flags the states worth acting on:

    npm       lodash 4.17.4
        released 2017-02-20 (9.7y ago); latest 4.17.21, 2021-02-20
    PyPI      left-pad 1.0.0
        released 2018-01-01 (8.8y ago); latest 1.0.0, 2018-01-01
        YANKED, and no release in 8.8y

The index is a folder of each registry's own metadata, one JSON file per
package, laid out `INDEX/<ecosystem>/<name>.json`:

    npm        the registry.npmjs.org/<name> document (its `time`, `versions`,
               `dist-tags`, and a version's `deprecated` note)
    PyPI       the pypi.org/pypi/<name>/json document (its `releases` with
               upload times and the per-file `yanked` flag)
    crates.io  the crates.io/api/v1/crates/<name> document (its `versions`
               with `created_at` and `yanked`)

Download it yourself; this add-on never fetches. A version it can't find in
the index is said to be unknown, not judged. `--now` fixes today (it defaults
to the real one), so a run is repeatable. npm has no yank and crates.io and
PyPI have no deprecation, so each flag is only looked for where it exists.

With no `--index` it lists the dependencies it found and stops. It only reads,
and writes nothing. Exit codes, the kernel's: 0 nothing to act on (or no
lockfiles); 42 one is yanked, deprecated or two years without a release, and
waits on you; 2 refused.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "advisories"))
import advisories  # noqa: E402
import kernel  # noqa: E402

STALE_DAYS = 2 * 365  # "two years without a release"


def when(iso):
    """A registry timestamp as an aware datetime, or None."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def meta(eco: str, doc: dict):
    """(latest version, latest release date, {version: {date, yanked,
    deprecated}}) from one ecosystem's own metadata document."""
    vers: dict = {}
    if eco == "PyPI":
        latest = doc.get("info", {}).get("version")
        for v, files in doc.get("releases", {}).items():
            dates = [
                f["upload_time_iso_8601"]
                for f in files
                if f.get("upload_time_iso_8601")
            ]
            vers[v] = {"date": min(dates) if dates else None,
                       "yanked": bool(files) and all(f.get("yanked") for f in files),
                       "deprecated": None}  # fmt: skip
    elif eco == "npm":
        latest = doc.get("dist-tags", {}).get("latest")
        times = doc.get("time", {})
        for v, info in doc.get("versions", {}).items():
            vers[v] = {"date": times.get(v), "yanked": False,
                       "deprecated": info.get("deprecated") or None}  # fmt: skip
        for v, t in times.items():
            if v not in ("created", "modified"):
                vers.setdefault(v, {"date": t, "yanked": False, "deprecated": None})
    else:  # crates.io
        crate = doc.get("crate", {})
        latest = crate.get("max_stable_version") or crate.get("newest_version")
        for e in doc.get("versions", []):
            if e.get("num"):
                vers[e["num"]] = {"date": e.get("created_at"),
                                  "yanked": bool(e.get("yanked")), "deprecated": None}  # fmt: skip
    dates = [v["date"] for v in vers.values() if v["date"]]
    return latest, (max(dates) if dates else None), vers


def doc_for(index: Path, eco: str, name: str):
    """The metadata document for a package, by its name or its folded name."""
    for nm in (name, advisories.norm(eco, name)[1]):
        p = index / eco / f"{nm}.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8", errors="replace"))
            except ValueError:
                return None
    return None


def years(a: datetime, b: datetime) -> float:
    return round((a - b).days / 365.25, 1)


def look(index: Path, eco: str, name: str, ver: str, now: datetime) -> dict:
    """What's known about one locked version: its age, latest, and flags."""
    doc = doc_for(index, eco, name)
    if doc is None:
        return {"unknown": True}
    latest, latest_date, vers = meta(eco, doc)
    here = vers.get(ver)
    if here is None:
        return {"unknown": True, "latest": latest}
    released, last = when(here["date"]), when(latest_date)
    flags = []
    if here["yanked"]:
        flags.append("yanked")
    if here["deprecated"]:
        flags.append("deprecated: " + here["deprecated"].strip()[:60])
    stale = last is not None and (now - last).days >= STALE_DAYS
    return {"unknown": False, "released": released, "latest": latest,
            "latest_date": last, "flags": flags, "stale": stale}  # fmt: skip


def report(folder: Path, index, now: datetime):
    """(exit code, deps, one line of findings per dep)."""
    deps = advisories.dependencies(folder)
    if index is None or not deps:
        return kernel.ALIVE, deps, None
    rows, flagged = [], 0
    for eco, name, ver in deps:
        r = look(index, eco, name, ver, now)
        detail = []
        if r["unknown"]:
            detail.append("not found in the registry index")
        else:
            age = f" ({years(now, r['released'])}y ago)" if r["released"] else ""
            top = f"latest {r['latest']}" if r["latest"] else "latest unknown"
            if r["latest_date"]:
                top += f", last release {r['latest_date'].date()}"
            detail.append(
                f"released {r['released'].date() if r['released'] else '?'}{age}; {top}"
            )
            marks = list(r["flags"])
            if r["stale"]:
                marks.append(f"no release in {years(now, r['latest_date'])}y")
            if marks:
                detail.append("; ".join(marks))
                flagged += 1
        rows.append((eco, name, ver, detail))
    return (kernel.ESCALATE if flagged else kernel.ALIVE), deps, (rows, flagged)


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--from", "--index", "--now"):
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
    index = None
    if "--index" in opts:
        index = Path(opts["--index"])
        if not index.is_dir():
            print(f"refused: {index} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    if "--now" in opts:
        now = when(opts["--now"] + "T00:00:00Z")
        if now is None:
            print(
                f"refused: --now {opts['--now']} isn't a date (YYYY-MM-DD)",
                file=sys.stderr,
            )
            return kernel.REFUSED
    else:
        now = datetime.now(timezone.utc)

    code, deps, body = report(folder, index, now)
    if not deps:
        print("No lockfiles found in your folder.")
        return kernel.ALIVE
    if index is None:
        for eco, name, ver in deps:
            print(f"{eco:9} {name} {ver}")
        print(f"\n{len(deps)} locked dependencies. Point --index at downloaded "
              "registry metadata to see how old each is.")  # fmt: skip
        return kernel.ALIVE
    rows, flagged = body
    for eco, name, ver, detail in rows:
        print(f"{eco:9} {name} {ver}")
        for line in detail:
            print(f"    {line}")
    print(f"\n{flagged} of {len(deps)} dependencies need attention "
          "(yanked, deprecated, or two years without a release).")  # fmt: skip
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
