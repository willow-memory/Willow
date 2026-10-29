r"""day_one.py: Day One's JSON export: each journal entry as a dated passage. Python 3.9+.

    python adapters/stdlib/day-one/day_one.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Day One export (an object with a
`metadata` and a list of `entries`; hidden folders and files skipped, any other
JSON skipped and counted) and writes each entry, oldest first, as a dated
passage with the place and weather Day One kept:

    2024-03-02 08:15  Kitchen, Leeds, United Kingdom  cloudy 8°C  #garden  starred

    Planted out the tomatoes. It was 5\-6 degrees, so I covered them.

The text is Day One's Markdown with its backslash escapes undone (`5\-6` is
5-6). The tags, the star and the place are kept as words; photos, audio and the
entry's other fields are not. An entry with no text is left out.

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

ESCAPED = re.compile(r"\\([\\`*_{}\[\]()#+\-.!>~|<])")


def place(loc: object) -> str:
    if not isinstance(loc, dict):
        return ""
    parts = []
    for key in ("placeName", "localityName", "administrativeArea", "country"):
        v = loc.get(key)
        if isinstance(v, str) and v.strip() and (not parts or parts[-1] != v.strip()):
            parts.append(v.strip())
    return ", ".join(parts)


def weather(w: object) -> str:
    if not isinstance(w, dict):
        return ""
    words = w.get("conditionsDescription")
    degrees = w.get("temperatureCelsius")
    bits = []
    if isinstance(words, str) and words.strip():
        bits.append(words.strip().lower())
    if isinstance(degrees, (int, float)) and not isinstance(degrees, bool):
        bits.append(f"{round(degrees)}°C")
    return " ".join(bits)


def when(stamp: object) -> str:
    return (
        f"{stamp[:10]} {stamp[11:16]}".strip()
        if isinstance(stamp, str) and len(stamp) >= 10
        else ""
    )


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(doc, dict)
        and "metadata" in doc
        and isinstance(doc.get("entries"), list)
    ):
        return None
    rows = []
    for e in doc["entries"]:
        if (
            not isinstance(e, dict)
            or not isinstance(e.get("text"), str)
            or not e["text"].strip()
        ):
            continue
        tags = [f"#{t}" for t in e.get("tags", []) if isinstance(t, str) and t]
        head = "  ".join(
            x
            for x in (
                when(e.get("creationDate")),
                place(e.get("location")),
                weather(e.get("weather")),
                " ".join(tags),
                "starred" if e.get("starred") is True else "",
            )
            if x
        )
        rows.append(
            (
                str(e.get("creationDate", "")),
                head + "\n\n" + ESCAPED.sub(r"\1", e["text"].strip()),
            )
        )
    return (
        "\n\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: day_one.py mirror --from FOLDER --to MIRROR"


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
