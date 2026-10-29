"""photos.py: when and where each photo was taken, as dated lines in a mirror.

    python adapters/deps/photos/photos.py mirror --from FOLDER --to MIRROR

Needs Pillow (MIT-CMU), pinned in requirements.txt beside this file:

    pip install -r adapters/deps/photos/requirements.txt

For each photo under FOLDER (.jpg, .jpeg, .tif, .tiff, .png, .webp) it reads
the EXIF a camera or phone wrote into it and writes `MIRROR/<same relative
path>.txt`, one passage:

    2024-07-14 09:32:10 holidays/eiffel.jpg
    at 48.858370 N, 2.294480 E
    camera Apple iPhone 12

the first line its date and time as the camera wrote them (no time zone is
guessed), then where, when it has GPS, then the camera, when it names one.
A photo with neither a date nor a place says nothing worth asking, and is
skipped and counted; so is a file Pillow can't open.

The contract every file reader shares: FOLDER is walked in sorted order,
skipping hidden files and folders; nothing is written inside FOLDER and no
original is changed; MIRROR inside FOLDER, or FOLDER inside MIRROR, is
refused; the same photo always gives the same bytes.

If Pillow isn't installed it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 wrote at least one file; 42 nothing
readable; 2 refused.
"""

from __future__ import annotations

import os
import re
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/photos/requirements.txt"
KINDS = (".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp")
EXIF, GPS = 0x8769, 0x8825  # the EXIF and GPS sub-directories
MAKE, MODEL, STAMP, TAKEN = 0x010F, 0x0110, 0x0132, 0x9003
STAMP_FORM = re.compile(r"(\d{4}):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)")


def when(raw) -> str:
    """'YYYY-MM-DD HH:MM:SS' from EXIF's 'YYYY:MM:DD HH:MM:SS', or ""; a
    camera with no clock set writes zeros, which is no date."""
    m = STAMP_FORM.fullmatch(str(raw or "").strip("\0 "))
    if not m or m.group(1) == "0000":
        return ""
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d} {h}:{mi}:{s}"


def degrees(dms, ref) -> float | None:
    """Degrees from EXIF's (degrees, minutes, seconds), south and west below
    zero; None when it isn't three numbers."""
    try:
        d, m, s = (float(x) for x in dms)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    value = d + m / 60 + s / 3600
    return -value if str(ref).strip("\0 ").upper() in ("S", "W") else value


def where(gps) -> str:
    """'at 48.858370 N, 2.294480 E', or "" with no usable position."""
    lat, lon = degrees(gps.get(2), gps.get(1)), degrees(gps.get(4), gps.get(3))
    if lat is None or lon is None or not (abs(lat) <= 90 and abs(lon) <= 180):
        return ""
    return (f"at {abs(lat):.6f} {'S' if lat < 0 else 'N'}, "
            f"{abs(lon):.6f} {'W' if lon < 0 else 'E'}")  # fmt: skip


def text(s) -> str:
    return " ".join(str(s or "").replace("\0", " ").split())


def passage(path: Path, rel: Path) -> str:
    """The photo's passage, or "" when it has no date and no place; raises
    when Pillow can't open it."""
    from PIL import Image

    with warnings.catch_warnings():  # a damaged file is counted, not shouted
        warnings.simplefilter("ignore")
        with Image.open(path) as im:
            exif = im.getexif()
    sub = exif.get_ifd(EXIF)
    stamp = when(sub.get(TAKEN)) or when(exif.get(STAMP))
    place = where(exif.get_ifd(GPS))
    if not stamp and not place:
        return ""
    make, model = text(exif.get(MAKE)), text(exif.get(MODEL))
    if make and model.lower().startswith(make.lower()):
        make = ""  # "Canon" and "Canon EOS 5D": the model says it
    camera = " ".join(x for x in (make, model) if x)
    lines = [f"{stamp} {rel.as_posix()}" if stamp else rel.as_posix()]
    lines += [x for x in (place, f"camera {camera}" if camera else "") if x]
    return "\n".join(lines) + "\n"


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def mirror(src: Path, dst: Path) -> int:
    try:
        import PIL  # noqa: F401
    except ImportError:
        print(f"refused: photos needs Pillow: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
        print(
            "refused: the mirror and the folder can't be inside each other",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote = bare = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in KINDS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            body = passage(p, rel)
        except Exception:  # Pillow raises many kinds for a damaged file
            skipped += 1
            continue
        if not body:
            bare += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        wrote += 1
    print(f"wrote {wrote} files to {dst}; {bare} with no date or place; "
          f"skipped {skipped}")  # fmt: skip
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    raise SystemExit(main(sys.argv[1:]))
