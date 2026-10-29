r"""places.py: KML, GeoJSON and GPX files: each place's name, note and coordinates. Python 3.9+.

    python adapters/stdlib/places/places.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .kml, .geojson and .gpx files (hidden folders and files
skipped) and writes each place as a paragraph, so a question about a place
finds its name, what you wrote about it and where it is:

    place: Allotment (Leeds / Plots)
    note: Plot 14, the gate sticks.
    at 53.80080, -1.54910

KML: each Placemark with its name, its description (the HTML taken off) and
the folders it is in. GeoJSON: each Feature, named by its name, title or label
property, with its description or note and its coordinates. GPX: waypoints,
routes and tracks, with their name, description and comment. A point's
coordinates are written as latitude then longitude; a line or an area is
written as its kind and its first point ("line of 120 points from ..."). A
place with no name is called "unnamed place".

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no place, or that cannot be read, is skipped
and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import html
import json
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TAGS = re.compile(r"<[^>]+>")
NOTE_KEYS = (
    "description",
    "desc",
    "note",
    "notes",
    "comment",
    "cmt",
    "text",
    "address",
)
NAME_KEYS = ("name", "title", "label", "Name")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean(text: str | None) -> str:
    return " ".join(html.unescape(TAGS.sub(" ", text or "")).split())


def point(lat: float, lon: float) -> str:
    return f"{lat:.5f}, {lon:.5f}"


def shape(kind: str, coords: list[tuple[float, float]]) -> str:
    if not coords:
        return ""
    if kind in ("point", ""):
        return "at " + point(*coords[0])
    word = "area" if kind == "polygon" else "line"
    return f"{word} of {len(coords)} points from {point(*coords[0])}"


def kml_coords(text: str | None) -> list[tuple[float, float]]:
    out = []
    for token in (text or "").split():
        parts = token.split(",")
        if len(parts) >= 2:
            out.append((float(parts[1]), float(parts[0])))
    return out


def kml(data: bytes) -> list[tuple[str, str, str, str]]:
    root = ET.fromstring(data)
    found: list[tuple[str, str, str, str]] = []

    def walk(node: ET.Element, path: list[str]) -> None:
        for child in node:
            kind = local(child.tag)
            if kind in ("Folder", "Document"):
                title = next(
                    (clean(c.text) for c in child if local(c.tag) == "name"), ""
                )
                walk(child, path + [title] if title else path)
            elif kind == "Placemark":
                name = note = where = ""
                for c in child.iter():
                    t = local(c.tag)
                    if t == "name" and not name and c is not child:
                        name = clean(c.text)
                    elif t == "description" and not note:
                        note = clean(c.text)
                    elif (
                        t in ("Point", "LineString", "LinearRing", "Polygon")
                        and not where
                    ):
                        pts = [
                            x
                            for cc in c.iter()
                            if local(cc.tag) == "coordinates"
                            for x in kml_coords(cc.text)
                        ]
                        where = shape(
                            "polygon"
                            if t in ("Polygon", "LinearRing")
                            else "point"
                            if t == "Point"
                            else "line",
                            pts,
                        )
                found.append((name, " / ".join(path), note, where))

    walk(root, [])
    return found


def geo_coords(geom: dict) -> tuple[str, list[tuple[float, float]]]:
    kind = str(geom.get("type", "")).lower()
    raw = geom.get("coordinates")
    pts: list[tuple[float, float]] = []

    def flat(c) -> None:
        if (
            isinstance(c, list)
            and len(c) >= 2
            and all(isinstance(x, (int, float)) for x in c[:2])
        ):
            pts.append((float(c[1]), float(c[0])))
        elif isinstance(c, list):
            for x in c:
                flat(x)

    if kind == "geometrycollection":
        for g in geom.get("geometries", []):
            sub_kind, sub = geo_coords(g)
            pts += sub
            kind = kind if kind != "geometrycollection" else sub_kind
    else:
        flat(raw)
    base = (
        "polygon"
        if "polygon" in kind
        else "point"
        if kind in ("point", "multipoint") and len(pts) == 1
        else "line"
        if kind
        else "point"
    )
    return base, pts


def geojson(data: bytes) -> list[tuple[str, str, str, str]]:
    doc = json.loads(data.decode("utf-8-sig"))
    feats = (
        doc.get("features")
        if doc.get("type") == "FeatureCollection"
        else [doc]
        if doc.get("type") == "Feature"
        else []
    )
    out = []
    for f in feats:
        if not isinstance(f, dict):
            continue
        props = f.get("properties") if isinstance(f.get("properties"), dict) else {}
        name = clean(next((str(props[k]) for k in NAME_KEYS if props.get(k)), ""))
        note = clean(next((str(props[k]) for k in NOTE_KEYS if props.get(k)), ""))
        kind, pts = geo_coords(f.get("geometry") or {})
        out.append((name, "", note, shape(kind, pts)))
    return out


def gpx(data: bytes) -> list[tuple[str, str, str, str]]:
    root = ET.fromstring(data)
    out = []
    for node in root:
        t = local(node.tag)
        if t not in ("wpt", "rte", "trk"):
            continue
        name = clean(next((c.text for c in node if local(c.tag) == "name"), ""))
        note = clean(
            " ".join(c.text or "" for c in node if local(c.tag) in ("desc", "cmt"))
        )
        pts = [
            (float(c.get("lat")), float(c.get("lon")))
            for c in node.iter()
            if local(c.tag) in ("wpt", "rtept", "trkpt")
            and c.get("lat")
            and c.get("lon")
        ]
        out.append(
            (
                name,
                "",
                note,
                shape("point" if t == "wpt" else "line", pts if t == "wpt" else pts),
            )
        )
    return out


def convert(data: bytes) -> str | None:
    head, lowered = data.lstrip()[:1], data.lower()
    if head == b"{":
        places = geojson(data)
    elif b"<kml" in lowered or b"<placemark" in lowered:
        places = kml(data)
    elif b"<gpx" in lowered:
        places = gpx(data)
    else:
        raise ValueError("not a places file")
    blocks = []
    for name, where_in, note, where in places:
        lines = [
            f"place: {name or 'unnamed place'}" + (f" ({where_in})" if where_in else "")
        ]
        if note:
            lines.append(f"note: {note}")
        if where:
            lines.append(where)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".kml", ".geojson", ".gpx")
ERRORS = (
    OSError,
    UnicodeDecodeError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    ET.ParseError,
)

USAGE = "usage: places.py mirror --from FOLDER --to MIRROR"


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
