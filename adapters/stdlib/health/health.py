r"""health.py: Apple Health's export as daily numbers a table can trend. Python 3.9+.

    python adapters/stdlib/health/health.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .xml files that are an Apple Health export (`export.xml`, a
`HealthData` document of `Record` elements; hidden folders and files skipped;
any other XML skipped and counted) and writes a comma-separated table with a
header and one row for each day, oldest first, the form the
[readings](../readings/) add-on reads for "what moved this week":

    date,steps,walking km,active kcal,exercise min,heart rate,resting heart rate,weight kg
    2024-03-02,8123,5.8,412,35,71,58,72.4
    2024-03-03,10442,7.6,530,48,73,58,

Steps, walking and running distance, active energy and exercise minutes are
summed over the day; heart rate and resting heart rate are the day's mean; weight
is the day's last reading. Distances in miles become kilometres, and weights in
pounds become kilograms. A column no record fills is left out of the header, and
a day with no reading in a column leaves that cell empty. The day is the record's
start date as the file writes it. Workouts, sleep, ECGs and the rest are not
read. The file is read as a stream, so a large export does not need to fit in
memory twice, but one over 400 MB is not read. A file that declares entities is
not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import io
import re
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 400 * 1024 * 1024
COLUMNS = (  # (header, record type, how a day's records combine)
    ("steps", "StepCount", "sum"),
    ("walking km", "DistanceWalkingRunning", "sum"),
    ("active kcal", "ActiveEnergyBurned", "sum"),
    ("exercise min", "AppleExerciseTime", "sum"),
    ("heart rate", "HeartRate", "mean"),
    ("resting heart rate", "RestingHeartRate", "mean"),
    ("weight kg", "BodyMass", "last"),
)
PREFIX = "HKQuantityTypeIdentifier"
FACTORS = {
    "mi": 1.609344,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "st": 6.35029318,
    "kJ": 0.239006,
}


def number(v: object, unit: object, want: str) -> float | None:
    try:
        x = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if unit in FACTORS and want in ("walking km", "weight kg"):
        x *= FACTORS[unit]
    elif unit == "kJ" and want == "active kcal":
        x *= FACTORS["kJ"]
    return x


def shown(x: float, header: str) -> str:
    if header in (
        "steps",
        "active kcal",
        "exercise min",
        "heart rate",
        "resting heart rate",
    ):
        return str(round(x))
    tenth = f"{x:.1f}"
    return tenth[:-2] if tenth.endswith(".0") else tenth


def convert(data: bytes) -> str | None:
    if b"<!ENTITY" in data or b"<HealthData" not in data:
        return None
    if len(data) > BIGGEST:
        raise ValueError("an export over 400 MB is not read")
    wanted = {PREFIX + t: (h, how) for h, t, how in COLUMNS}
    days: dict[str, dict[str, list[tuple[str, float]]]] = {}
    for _event, el in ET.iterparse(io.BytesIO(data)):
        if el.tag == "Record" and el.get("type") in wanted:
            header, _how = wanted[el.get("type")]
            start = el.get("startDate") or ""
            value = number(el.get("value"), el.get("unit"), header)
            if value is not None and re.match(r"\d{4}-\d{2}-\d{2}", start):
                days.setdefault(start[:10], {}).setdefault(header, []).append(
                    (start, value)
                )
        if el.tag in ("Record", "Workout", "ActivitySummary", "Correlation"):
            el.clear()
    present = [(h, how) for h, _t, how in COLUMNS if any(h in d for d in days.values())]
    if not present:
        return None
    rows = []
    for day in sorted(days):
        cells = []
        for header, how in present:
            got = days[day].get(header)
            if not got:
                cells.append("")
            elif how == "sum":
                cells.append(shown(sum(v for _s, v in got), header))
            elif how == "mean":
                cells.append(shown(sum(v for _s, v in got) / len(got), header))
            else:
                cells.append(shown(max(got, key=lambda sv: sv[0])[1], header))
        rows.append(day + "," + ",".join(cells))
    return "date," + ",".join(h for h, _ in present) + "\n" + "\n".join(rows) + "\n"


EXTS = (".xml",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: health.py mirror --from FOLDER --to MIRROR"


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
