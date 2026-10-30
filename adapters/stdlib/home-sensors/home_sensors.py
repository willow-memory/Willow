r"""home_sensors.py: Home Assistant's history export: sensor readings as daily numbers. Python 3.9+.

    python adapters/stdlib/home-sensors/home_sensors.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Home Assistant history (what
`/api/history/period` returns: a list with one list of state objects for each
entity; hidden folders and files skipped; any other JSON skipped and counted)
and writes a comma-separated table with a header and one row for each day,
oldest first, the form the [readings](../readings/) add-on reads for "what
moved this week":

    date,Kitchen temperature (C),Hall humidity (%)
    2024-03-02,21.4,48.5
    2024-03-03,20.9,

Each column is one entity, headed by its friendly name (else its entity id) and
the unit it reports in; each cell is the mean of that day's numeric states,
to one decimal place. States that are not numbers (on, off, unavailable,
unknown) are ignored, and an entity with no number at all is left out. The day
is the state's `last_changed` day as the file writes it. Attributes, events
and the rest are not copied.

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
    return " ".join(v.replace(",", " ").split()) if isinstance(v, str) else ""


def column(states: list[dict]) -> str:
    """A column's header: the entity's friendly name (else its id) and its unit."""
    first = next(
        (
            s
            for s in states
            if isinstance(s, dict) and isinstance(s.get("entity_id"), str)
        ),
        {},
    )
    attrs = next(
        (
            s["attributes"]
            for s in states
            if isinstance(s, dict)
            and isinstance(s.get("attributes"), dict)
            and (
                s["attributes"].get("friendly_name")
                or s["attributes"].get("unit_of_measurement")
            )
        ),
        {},
    )
    name = text(attrs.get("friendly_name")) or text(first.get("entity_id")) or "sensor"
    unit = text(attrs.get("unit_of_measurement"))
    return f"{name} ({unit})" if unit else name


def tenth(x: float) -> str:
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(doc, list)
        and doc
        and all(isinstance(g, list) for g in doc)
        and any(isinstance(s, dict) and "entity_id" in s for g in doc for s in g)
    ):
        return None
    heads: list[str] = []
    days: dict[str, dict[str, list[float]]] = {}
    for group in doc:
        values: dict[str, list[float]] = {}
        for s in group:
            if not isinstance(s, dict) or not isinstance(s.get("state"), str):
                continue
            stamp = s.get("last_changed") or s.get("last_updated")
            try:
                v = float(s["state"])
            except ValueError:
                continue
            if (
                v == v
                and isinstance(stamp, str)
                and re.match(r"\d{4}-\d{2}-\d{2}", stamp)
            ):
                values.setdefault(stamp[:10], []).append(v)
        if values:
            head = column(group)
            while head in heads:
                head += "*"
            heads.append(head)
            for day, vs in values.items():
                days.setdefault(day, {})[head] = vs
    if not heads:
        return None
    rows = [
        d
        + ","
        + ",".join(
            tenth(sum(days[d][h]) / len(days[d][h])) if h in days[d] else ""
            for h in heads
        )
        for d in sorted(days)
    ]
    return "date," + ",".join(heads) + "\n" + "\n".join(rows) + "\n"


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: home_sensors.py mirror --from FOLDER --to MIRROR"


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
