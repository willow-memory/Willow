r"""shortcuts.py: link files dragged to a desktop or a folder, as their title
and address. Python 3.9+.

    python adapters/stdlib/shortcuts/shortcuts.py mirror --from FOLDER --to MIRROR

Walks FOLDER for the three text or property-list kinds of link file and writes
each as one passage, the title its name gives beside the address it holds:

    Allotment rules.url       ->   Allotment rules
                                   https://example.org/allotment/rules

- `.url`, a Windows Internet Shortcut: the `URL=` of its `[InternetShortcut]`
  section, read as INI. Decoded as UTF-8, else as Windows-1252 (the address is
  ASCII; only other keys, such as an icon's path, may not be).
- `.webloc`, a macOS web location: the `URL` key of its property list, XML or
  binary.
- `.desktop`, a Linux desktop entry: a `Type=Link` gives its `Name`, `Comment`
  and `URL`; a `Type=Application` gives a launcher's `Name`, `GenericName`,
  `Comment`, `Keywords` and the command it runs (`Exec`), since "where's the
  launcher for X" is a fair question. Each value is written as the file holds
  it, one to a line, with no label added. Any other type, or one marked
  `Hidden=true` (deleted, by the spec), is skipped and counted.

A Windows `.lnk` is binary and not read: it is neither written nor counted.

Only what's inside the file and its name is written, never its modified time,
so the same folder gives the same bytes on any copy. Each file is written to
MIRROR at the same relative path with `.txt` added. FOLDER is only read. A
file with no address, or that cannot be read, is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import configparser
import os
import plistlib
import re
import sys
from pathlib import Path
from xml.parsers.expat import ExpatError

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: the escapes a desktop entry's string value may hold
ESCAPE = re.compile(r"\\(.)")
ESCAPES = {"s": " ", "n": " ", "t": " ", "r": " ", "\\": "\\"}
#: what a launcher's passage holds, in this order
LAUNCHER = ("Name", "GenericName", "Comment", "Keywords", "Exec")


def one_line(value: str) -> str:
    return " ".join(value.split())


def ini(text: str) -> configparser.ConfigParser:
    """A parser that keeps keys' case, splits only at "=", and treats a
    [DEFAULT] section as any other (Windows writes one, holding BASEURL)."""
    cp = configparser.ConfigParser(
        interpolation=None,
        strict=False,
        delimiters=("=",),
        default_section="\0",
    )
    cp.optionxform = str
    cp.read_string(text)
    return cp


def decode(data: bytes, cp1252: bool) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        if not cp1252:
            raise
        return data.decode("cp1252")


def lines(*values: str) -> str:
    """The values, one to a line and none empty, with no label of this
    reader's own: a word written into every passage would let a question
    about something the folder doesn't hold be answered by any of them."""
    return "\n".join(v for v in map(one_line, values) if v) + "\n"


def passage(title: str, url: str, comment: str = "") -> str | None:
    return lines(title, comment, url) if one_line(url) else None


def read_url(data: bytes, title: str) -> str | None:
    cp = ini(decode(data, cp1252=True))
    if not cp.has_section("InternetShortcut"):
        return None
    return passage(title, cp.get("InternetShortcut", "URL", fallback=""))


def read_webloc(data: bytes, title: str) -> str | None:
    plist = plistlib.loads(data)
    url = plist.get("URL") if isinstance(plist, dict) else None
    return passage(title, url) if isinstance(url, str) else None


def read_desktop(data: bytes, title: str) -> str | None:
    cp = ini(decode(data, cp1252=False))
    if not cp.has_section("Desktop Entry"):
        return None
    entry = {
        k: ESCAPE.sub(lambda m: ESCAPES.get(m.group(1), m.group(0)), v)
        for k, v in cp.items("Desktop Entry")
    }
    if entry.get("Hidden", "").strip() == "true":
        return None
    name = one_line(entry.get("Name", "")) or title
    kind = entry.get("Type", "").strip()
    if kind == "Link":
        return passage(name, entry.get("URL", ""), entry.get("Comment", ""))
    if kind == "Application":
        entry["Name"] = name
        return lines(*(entry.get(k, "") for k in LAUNCHER))
    return None


READERS = {".url": read_url, ".webloc": read_webloc, ".desktop": read_desktop}


def convert(data: bytes, name: str) -> str | None:
    """The passage for one link file called `name`, or None if it holds none."""
    path = Path(name)
    return READERS[path.suffix.lower()](data, path.stem)


EXTS = tuple(READERS)
ERRORS = (OSError, UnicodeDecodeError, ValueError, ExpatError, configparser.Error)

USAGE = "usage: shortcuts.py mirror --from FOLDER --to MIRROR"


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


# differs on purpose: convert needs the file's name, for its kind
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
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
