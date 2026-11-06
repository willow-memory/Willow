r"""strava.py: Strava's export and GPX files, each activity as a dated line. Python 3.9+.

    python adapters/stdlib/strava/strava.py mirror --from FOLDER --to MIRROR

Walks FOLDER (hidden folders and files skipped) for Strava's bulk export
summary, `activities.csv`, and for activity files: .gpx and .tcx, plain or
gzipped (.gpx.gz, .tcx.gz, as Strava's export keeps them). Each activity is
one paragraph, opening with its line: its start (date, clock and zone), its
name, its distance in km, and its time as H:MM:SS:

    2024-03-03 07:15Z Harbour Loop, 5.2, 0:28:14

Only the file's own values are written: no type word, no unit, no label, no
weekday or month name, since a word written into every passage would let a
question about something the folder doesn't hold ("when did I run a
marathon") be answered by any activity. A value the file doesn't give is "?".

activities.csv: one paragraph per row, in the file's order, with the row's
description, private note and gear on their own lines under it when it has
them. It is known by its header ("Activity ID", "Activity Date", "Activity
Type"), so any other CSV is not read. Its header names "Distance" and
"Elapsed Time" twice: the distance is the later "Distance" column, which is
always metres (the first is in your display units, and a swim's is metres
there too); the time is the first "Elapsed Time" column, in seconds.
"Activity Date" is written in UTC, as "Mar 3, 2024, 7:15:22 AM"; a date in
any other form is kept as written.

GPX: each track is an activity, named by its <name>. Its distance is the sum
of the great-circle (haversine) distances between consecutive points of each
segment; its time is elapsed, from its first point's time to its last, pauses
included. Its date is its first point's time (the file's own <time> is when
the file was made, so it is not used). TCX: each Activity, dated by its Id;
its distance and time are its laps' DistanceMeters and TotalTimeSeconds added
up (the device's timer, so pauses are left out), with its Notes under it.

A time is shown in the zone its file gives (Z is UTC, +01:00 is kept as
+01:00); a time with no zone is shown as written, and no zone is guessed. A
distance of a kilometre or more is in km to one decimal place, a shorter one
to two (0.67).

.fit files (and .fit.gz) are binary and not read: each is skipped, counted,
and named in a note on stderr.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no activity, or that cannot be read, is
skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

EARTH_KM = 6371.0  # the mean radius, as most route tools use
GZ_LIMIT = 256 * 1024 * 1024  # bytes a .gz may open to; a bigger one is skipped
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
ISO = re.compile(
    r"\s*(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)([.,]\d+)?"
    r"\s*(Z|[+-]\d\d:?\d\d)?\s*$"
)
STRAVA_DATE = re.compile(
    r"\s*([A-Z][a-z]{2}) (\d{1,2}), (\d{4}),? (\d{1,2}):(\d\d):(\d\d) ?([AP]M)\s*$"
)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(node, name: str):
    return next((c for c in node if local(c.tag) == name), None)


def text_of(node, name: str) -> str:
    c = child(node, name)
    return " ".join((c.text or "").split()) if c is not None else ""


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """The great-circle distance in km between two (latitude, longitude)
    points given in degrees."""
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(h)))


def distance(metres: float | None) -> str:
    """In km, without the unit: one decimal place from a kilometre up, two
    below it. "?" when the file gives none."""
    if metres is None:
        return "?"
    return f"{metres / 1000:.1f}" if metres >= 1000 else f"{metres / 1000:.2f}"


def duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "?"
    s = int(round(seconds))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


class When:
    """A time as its file gives it: a date and clock, and a zone ("UTC",
    "+01:00") or None when the file gives none. Two are subtracted only when
    both have a zone or neither does."""

    def __init__(self, t: dt.datetime, zone: str | None):
        self.t, self.zone = t, zone

    def start(self) -> str:
        """ "2024-03-03 07:15Z", "2024-03-03 08:15+01:00", or with no zone
        "2024-03-03 07:15": digits, which the kernel reads as a date."""
        zone = {"UTC": "Z", None: ""}.get(self.zone, self.zone)
        return f"{self.t:%Y-%m-%d %H:%M}{zone}"

    def seconds_to(self, other: When) -> float | None:
        if (self.zone is None) != (other.zone is None):
            return None
        return (other.t - other.offset() - (self.t - self.offset())).total_seconds()

    def offset(self) -> dt.timedelta:
        if not self.zone or self.zone == "UTC":
            return dt.timedelta(0)
        z = self.zone.replace(":", "")
        sign = -1 if z[0] == "-" else 1
        return sign * dt.timedelta(hours=int(z[1:3]), minutes=int(z[3:5]))


def iso(raw: str | None) -> When | None:
    m = ISO.match(raw or "")
    if not m:
        return None
    try:
        t = dt.datetime(*map(int, m.groups()[:6]))
        t += (
            dt.timedelta(seconds=float("0." + m.group(7)[1:]))
            if m.group(7)
            else dt.timedelta(0)
        )
    except ValueError:
        return None
    z = m.group(8)
    if z is None:
        return When(t, None)
    if z == "Z" or z.replace(":", "") in ("+0000", "-0000"):
        return When(t, "UTC")
    z = z if ":" in z else z[:3] + ":" + z[3:]
    return When(t, z)


def strava_date(raw: str) -> When | None:
    """ "Mar 3, 2024, 7:15:22 AM", in UTC, as activities.csv writes it."""
    m = STRAVA_DATE.match(raw)
    if not m or m.group(1) not in MONTHS:
        return None
    mon = MONTHS.index(m.group(1)) + 1
    hour = int(m.group(4)) % 12 + (12 if m.group(7) == "PM" else 0)
    try:
        t = dt.datetime(int(m.group(3)), mon, int(m.group(2)), hour,
                        int(m.group(5)), int(m.group(6)))  # fmt: skip
    except ValueError:
        return None
    return When(t, "UTC")


def line(when: When | str | None, name: str, metres, seconds) -> str:
    """One activity's line: its start, its name, how far and how long."""
    start = when.start() if isinstance(when, When) else (when or "?")
    head = f"{start} {name}" if name else start
    return f"{head}, {distance(metres)}, {duration(seconds)}"


# ── activities.csv ──────────────────────────────────────────────────────────
NEEDED = ("Activity ID", "Activity Date", "Activity Type")


def number(raw: str) -> float | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        x = float(raw)
    except ValueError:
        return None
    return x if math.isfinite(x) and x >= 0 else None


def activities_csv(text: str) -> list[str]:
    rows = csv.reader(io.StringIO(text))
    header = next(rows, [])
    if not all(h in header for h in NEEDED):
        raise ValueError("not Strava's activities.csv")

    def first(name: str) -> int | None:
        return header.index(name) if name in header else None

    def later(name: str) -> int | None:
        at = [i for i, h in enumerate(header) if h == name]
        return at[1] if len(at) > 1 else None

    col = {n: first(n) for n in ("Activity Date", "Activity Name",
           "Activity Description", "Activity Private Note", "Activity Gear")}  # fmt: skip
    metres_at, elapsed = (
        later("Distance"),
        [first("Elapsed Time"), later("Elapsed Time")],
    )
    out = []
    for row in rows:
        if not any(x.strip() for x in row):
            continue

        def cell(i: int | None) -> str:
            return " ".join(row[i].split()) if i is not None and i < len(row) else ""

        raw_date = cell(col["Activity Date"])
        when = strava_date(raw_date) or raw_date or None
        secs = next(
            (s for s in (number(cell(i)) for i in elapsed) if s is not None), None
        )
        lines = [line(when, cell(col["Activity Name"]), number(cell(metres_at)), secs)]
        for key in ("Activity Description", "Activity Private Note", "Activity Gear"):
            if cell(col[key]):
                lines.append(cell(col[key]))
        out.append("\n".join(lines))
    return out


# ── GPX and TCX ─────────────────────────────────────────────────────────────
def xml_root(data: bytes):
    # a Garmin TCX often has blank space before its <?xml ...?>, which a
    # parser refuses; the file is the same without it
    return ET.fromstring(data.lstrip())


def gpx(data: bytes) -> list[str]:
    root = xml_root(data)
    if local(root.tag) != "gpx":
        raise ValueError("not a GPX file")
    meta = child(root, "metadata")
    meta_name = text_of(meta, "name") if meta is not None else text_of(root, "name")
    out = []
    for trk in (c for c in root if local(c.tag) == "trk"):
        metres, times, points = 0.0, [], 0
        for seg in (c for c in trk if local(c.tag) == "trkseg"):
            prev = None
            for pt in (c for c in seg if local(c.tag) == "trkpt"):
                try:
                    here = (float(pt.get("lat", "")), float(pt.get("lon", "")))
                except ValueError:
                    continue
                points += 1
                if prev is not None:
                    metres += haversine_km(prev, here) * 1000
                prev = here
                when = iso(text_of(pt, "time"))
                if when is not None:
                    times.append(when)
        if not points:
            continue
        # the file's own <time> is when the file was made, not the start
        start = times[0] if times else None
        secs = times[0].seconds_to(times[-1]) if len(times) > 1 else None
        name = text_of(trk, "name") or meta_name
        out.append(line(start, name, metres if points > 1 else None, secs))
    return out


def tcx(data: bytes) -> list[str]:
    root = xml_root(data)
    if local(root.tag) != "TrainingCenterDatabase":
        raise ValueError("not a TCX file")
    out = []
    for act in (n for n in root.iter() if local(n.tag) == "Activity"):
        laps = [c for c in act if local(c.tag) == "Lap"]
        start = iso(text_of(act, "Id")) or next(
            (w for w in (iso(lap.get("StartTime")) for lap in laps) if w), None
        )
        metres = [number(text_of(lap, "DistanceMeters")) for lap in laps]
        secs = [number(text_of(lap, "TotalTimeSeconds")) for lap in laps]
        known_m = [m for m in metres if m is not None]
        known_s = [s for s in secs if s is not None]
        lines = [line(start, "",
                      sum(known_m) if known_m else None,
                      sum(known_s) if known_s else None)]  # fmt: skip
        if text_of(act, "Notes"):
            lines.append(text_of(act, "Notes"))
        out.append("\n".join(lines))
    return out


def unzip(data: bytes) -> bytes:
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
        body = f.read(GZ_LIMIT + 1)
    if len(body) > GZ_LIMIT:
        raise ValueError("opens to more than the limit")
    return body


def convert(data: bytes, name: str) -> str | None:
    """The mirror text of one file named `name`, or None for no activity."""
    low = name.lower()
    if low.endswith(".gz"):
        data, low = unzip(data), low[:-3]
    if low.endswith(".csv"):
        blocks = activities_csv(data.decode("utf-8-sig"))
    elif low.endswith(".gpx"):
        blocks = gpx(data)
    else:
        blocks = tcx(data)
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".gpx", ".gpx.gz", ".tcx", ".tcx.gz")
FIT = (".fit", ".fit.gz")
ERRORS = (OSError, UnicodeDecodeError, ValueError, EOFError, csv.Error, ET.ParseError)

USAGE = "usage: strava.py mirror --from FOLDER --to MIRROR"


def _is_activities_csv(p: Path) -> bool:
    """A CSV whose header is Strava's; any other CSV is not this reader's."""
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f), [])
    except (OSError, UnicodeDecodeError, csv.Error):
        return False
    return all(h in header for h in NEEDED)


# differs on purpose: it takes .fit files too, to say they aren't read, and only an activities .csv
def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads (and the .fit files it counts), sorted
    by relative path. Hidden folders and files are skipped; symlinked folders
    are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            low = name.lower()
            if name.startswith(".") or not p.is_file():
                continue
            if low.endswith(EXTS + FIT) or (
                low.endswith(".csv") and _is_activities_csv(p)
            ):
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


# differs on purpose: it sets the .fit files aside, to say they aren't read
def mirror(src: Path, dst: Path) -> tuple[int, int, list[str]]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped, the
    .fit files skipped)."""
    wrote = skipped = 0
    fits = []
    for path in _sources(src):
        rel = path.relative_to(src)
        if path.name.lower().endswith(FIT):
            fits.append(rel.as_posix())
            skipped += 1
            continue
        try:
            text = convert(path.read_bytes(), path.name)
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
    return wrote, skipped, fits


# differs on purpose: it says the .fit files it doesn't read
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
    wrote, skipped, fits = mirror(src, dst)
    if fits:
        print(f"note: {len(fits)} .fit files are binary and not read, first {fits[0]}",
              file=sys.stderr)  # fmt: skip
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
