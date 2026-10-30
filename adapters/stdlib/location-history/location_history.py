r"""location_history.py: Google Maps Timeline exports: where you were, by day. Python 3.9+.

    python adapters/stdlib/location-history/location_history.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Timeline export (hidden folders and
files skipped; any other JSON skipped and counted) and writes each place visited
and each trip, oldest first, as a dated line with the hours it covers:

    2024-03-02 08:15-09:10  Kitchen Cafe, 1 High St, Leeds
    2024-03-02 09:10-09:40  walking 1.5 km
    2024-03-02 12:00-17:30  HOME (45.123, 7.456)

Two shapes are read: the Takeout "Semantic Location History" months (an object
with `timelineObjects`, each a `placeVisit` or an `activitySegment`) and the
newer Timeline export (an object with `semanticSegments`, each a `visit` or an
`activity`). A visit is named by its place name and address; when the export
gives only a kind of place (HOME, WORK) and a position, that is what is written.
A trip is its type in lower case (walking, in passenger vehicle) and, when the
file gives it, how far. The times are written as the file has them (to the
minute); raw location points are not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def span(start: object, end: object) -> tuple[str, str]:
    """(sort key, "2024-03-02 08:15-09:10") from two ISO timestamps."""
    s, e = text(start), text(end)
    if not re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", s):
        return "", ""
    out = f"{s[:10]} {s[11:16]}"
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", e):
        out += f"-{e[11:16]}" if e[:10] == s[:10] else f" to {e[:10]} {e[11:16]}"
    return s, out


def km(meters: object) -> str:
    if isinstance(meters, bool) or not isinstance(meters, (int, float)) or meters <= 0:
        return ""
    return f"{meters / 1000:.1f} km"


def trip(kind: object, meters: object) -> str:
    what = text(kind).lower().replace("_", " ") or "trip"
    return " ".join(x for x in (what, km(meters)) if x)


def old(objects: list) -> list[tuple[str, str]]:
    rows = []
    for o in objects:
        if not isinstance(o, dict):
            continue
        v, a = o.get("placeVisit"), o.get("activitySegment")
        if isinstance(v, dict):
            loc = v.get("location") if isinstance(v.get("location"), dict) else {}
            dur = v.get("duration") if isinstance(v.get("duration"), dict) else {}
            name = (
                ", ".join(
                    x for x in (text(loc.get("name")), text(loc.get("address"))) if x
                )
                or "(unnamed place)"
            )
            key, when = span(dur.get("startTimestamp"), dur.get("endTimestamp"))
            what = name
        elif isinstance(a, dict):
            dur = a.get("duration") if isinstance(a.get("duration"), dict) else {}
            key, when = span(dur.get("startTimestamp"), dur.get("endTimestamp"))
            what = trip(a.get("activityType"), a.get("distance"))
        else:
            continue
        if when:
            rows.append((key, f"{when}  {what}"))
    return rows


def new(segments: list) -> list[tuple[str, str]]:
    rows = []
    for s in segments:
        if not isinstance(s, dict):
            continue
        key, when = span(s.get("startTime"), s.get("endTime"))
        v, a = s.get("visit"), s.get("activity")
        if isinstance(v, dict):
            top = (
                v.get("topCandidate") if isinstance(v.get("topCandidate"), dict) else {}
            )
            where = (
                top.get("placeLocation")
                if isinstance(top.get("placeLocation"), dict)
                else {}
            )
            kind, pos = (
                text(top.get("semanticType")),
                text(where.get("latLng")).replace("°", ""),
            )
            what = (
                f"{kind} ({pos})".strip()
                if kind and pos
                else kind or pos or "(unnamed place)"
            )
        elif isinstance(a, dict):
            top = (
                a.get("topCandidate") if isinstance(a.get("topCandidate"), dict) else {}
            )
            what = trip(top.get("type"), a.get("distanceMeters"))
        else:
            continue
        if when:
            rows.append((key, f"{when}  {what}"))
    return rows


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not isinstance(doc, dict):
        return None
    if isinstance(doc.get("timelineObjects"), list):
        rows = old(doc["timelineObjects"])
    elif isinstance(doc.get("semanticSegments"), list):
        rows = new(doc["semanticSegments"])
    else:
        return None
    return (
        "\n".join(t for _k, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: location_history.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
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
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
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
