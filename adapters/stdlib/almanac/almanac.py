"""almanac.py: an Almanac's catalog.json, as passages the kernel reads.

    python adapters/stdlib/almanac/almanac.py mirror --from FOLDER --to MIRROR

An Almanac (github.com/almanac-data: climate, health, civic and the rest) is a
catalog, not a host: each entry points at a public dataset where its publisher
keeps it. Each vertical publishes a generated `catalog.json`. Walks FOLDER for
files named `catalog.json` (in any capitalisation), skipping hidden folders and
files, so a folder of almanac checkouts mirrors them all at once.

Each entry becomes one paragraph, sorted by id:

    Global Historical Climatology Network Daily (noaa-ghcn-daily)
    Daily land surface observations from weather stations worldwide.
    publisher: NOAA NCEI
    source: https://www.ncei.noaa.gov/products/...
    status: live since 2026-07-01 (curator); licence: public-domain (US Gov work)
    link last checked: 2026-10-31, reachable, HTTP 200
    coverage: global; 1763-present; daily
    topics: temperature, precipitation, stations

The first line of the file names the catalog and how many entries it holds.
`link last checked` says what the almanac's link checker last saw: reachable
with its HTTP status, `no response`, or `not yet probed` when the probe has not
written its facts yet. The almanac's own words are kept: this never decides
whether a dataset is alive.

Each catalog is written to MIRROR at the same relative path with `.txt` added:
`climate-almanac/catalog.json` becomes
`MIRROR/climate-almanac/catalog.json.txt`. FOLDER is only read. A file that is
not a catalog (not JSON, or no `entries` list) is skipped and counted, never a
crash.

    wrote 3 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: almanac.py mirror --from FOLDER --to MIRROR"


def _one_line(value) -> str:
    """A field as one line: lists joined, whitespace collapsed, None as ''."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_one_line(v) for v in value if v is not None)
    return " ".join(str(value).split())


def _checked(observed: dict) -> str:
    """What the link checker last wrote, in words."""
    when = _one_line(observed.get("checked")) or "never"
    reachable = observed.get("reachable")
    if reachable is True:
        status = observed.get("http_status")
        seen = f"reachable, HTTP {status}" if status is not None else "reachable"
    elif reachable is False:
        seen = "no response"
    else:
        seen = "not yet probed"
    return f"{when}, {seen}"


def entry_text(entry: dict) -> str:
    """One entry as one paragraph, its lines in a fixed order."""
    title = _one_line(entry.get("title")) or _one_line(entry.get("id"))
    lines = [f"{title} ({_one_line(entry.get('id'))})"]
    kind = _one_line(entry.get("type"))
    if kind and kind != "dataset":
        lines.append(f"kind: {kind}")
    if _one_line(entry.get("collection")):
        lines.append(f"collection: {_one_line(entry.get('collection'))}")
    if _one_line(entry.get("description")):
        lines.append(_one_line(entry.get("description")))
    if _one_line(entry.get("publisher")):
        lines.append(f"publisher: {_one_line(entry.get('publisher'))}")
    source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
    if _one_line(source.get("canonical_url")):
        lines.append(f"source: {_one_line(source.get('canonical_url'))}")
    status = _one_line(entry.get("status")) or "unknown"
    since = _one_line(entry.get("status_since"))
    by = _one_line(entry.get("status_source"))
    said = status + (f" since {since}" if since else "") + (f" ({by})" if by else "")
    licence = _one_line(entry.get("license"))
    lines.append(f"status: {said}" + (f"; licence: {licence}" if licence else ""))
    observed = entry.get("observed") if isinstance(entry.get("observed"), dict) else {}
    lines.append(f"link last checked: {_checked(observed)}")
    fp = entry.get("fingerprint") if isinstance(entry.get("fingerprint"), dict) else {}
    kinds = [k for k, key in (("full", "sha256"), ("lead", "lead_hash")) if fp.get(key)]
    if kinds:
        when = _one_line(fp.get("captured")) or "an unknown date"
        lines.append(f"fingerprint: {' and '.join(kinds)} baseline taken {when}")
    for copy in entry.get("recovery") or []:
        if not isinstance(copy, dict) or copy.get("permission") == "excluded":
            continue  # excluded copies are kept for audit, never surfaced
        how = _one_line(copy.get("authenticity")) or "unrated"
        via = _one_line(copy.get("via")) or "somewhere"
        when = _one_line(copy.get("captured"))
        lines.append(f"archived copy: {how}, via {via}"
                     + (f", captured {when}" if when else "")
                     + f": {_one_line(copy.get('url'))}")  # fmt: skip
    coverage = entry.get("coverage") if isinstance(entry.get("coverage"), dict) else {}
    span = [_one_line(coverage.get(k)) for k in ("spatial", "temporal", "cadence")]
    if any(span):
        lines.append("coverage: " + "; ".join(s for s in span if s))
    if _one_line(entry.get("topics")):
        lines.append(f"topics: {_one_line(entry.get('topics'))}")
    return "\n".join(lines) + "\n\n"


def catalog_text(raw: bytes) -> str | None:
    """The mirror text for a catalog.json, or None if it is not a catalog."""
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        return None
    entries = [e for e in data["entries"] if isinstance(e, dict)]
    entries.sort(key=lambda e: _one_line(e.get("id")))
    name = _one_line(data.get("name")) or "an almanac"
    head = (
        f"almanac: {name}, {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}\n\n"
    )
    return head + "".join(entry_text(e) for e in entries)


def _sources(folder: Path) -> list[Path]:
    """catalog.json files under `folder`, sorted by relative path. Hidden
    folders and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if (
                not name.startswith(".")
                and name.lower() == "catalog.json"
                and p.is_file()
            ):
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = catalog_text(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
