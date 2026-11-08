"""skim.py: a made list held to how a person reads it. Python 3.9+.

    python adapters/stdlib/skim/skim.py check [FILE ...] [--screen N] [--width N]

Each Markdown file given (FILES.md and ADDONS.md at the repo's root, when
none is) is read three ways, and every place one fails is said, by file and
line:

    screen  a run of lines with no heading longer than a screen (--screen,
            60 unless it says): a reader who lands there can't tell where
            they are. Lines in a code block count: a tree is still read.
    width   a line longer than can be read in one look (--width, 160):
            a table row aside, since a table is read by its columns
    jump    a name a reader comes to find, with nowhere to jump to: a list
            entry that opens with a bold name (`- **name**`, or linked: one
            lower-case word, as an add-on is named, not a bold lead-in) and
            no anchor for it in the file (an `<a id="name">`, or a heading
            whose link is #name); and a folder at the top of a tree in a code
            block (`├── name/`) with no heading that names it

It reports, and refuses nothing: a list that fails is a list to make easier
to read, not a broken build. It reads only the files it is given and writes
nothing. Exit codes, the kernel's: 0 every file reads within the bounds; 42
places were found, each said; 2 refused (a file that isn't there, or a bad
command line).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: skim.py check [FILE ...] [--screen N] [--width N]"
LISTS = ("FILES.md", "ADDONS.md")
SCREEN, WIDTH = 60, 160
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
#: a list entry opening with a bold name, linked or not: a name shaped like
#: an add-on's or a file's (one word, lower case), not a bold lead-in sentence
ENTRY = re.compile(r"^\s*[-*] \[?\*\*([a-z0-9][a-z0-9._-]*)\*\*")
#: a folder at the top of a tree: no `│` in front of it
TOP = re.compile(r"^[├└]── ([^/\s]+)/")
ANCHOR = re.compile(r"""<a\s+(?:id|name)=["']([^"']+)["']""")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation gone, spaces
    as dashes."""
    text = re.sub(r"[`*_]|\[|\]\([^)]*\)", "", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def skim(text: str, screen: int, width: int) -> list[tuple[int, str, str]]:
    """(line, check, what) for each place the text fails, in line order."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    out = []
    inside, start, heads, anchors = False, 1, [], set()
    entries, folders = [], []

    def run_ends(end: int) -> None:
        if end - start + 1 > screen:
            out.append((start, "screen", f"lines {start} to {end}, {end - start + 1} with no heading (a screen is {screen})"))  # fmt: skip

    for n, line in enumerate(lines, 1):
        anchors.update(ANCHOR.findall(line))
        if FENCE.match(line):
            inside = not inside
        elif not inside and (m := HEADING.match(line)):
            run_ends(n - 1)
            start = n + 1
            heads.append(m.group(2))
            continue
        elif not inside and (m := ENTRY.match(line)):
            entries.append((n, m.group(1).strip()))
        elif inside and (m := TOP.match(line)):
            folders.append((n, m.group(1)))
        if len(line) > width and not line.lstrip().startswith("|"):
            out.append((n, "width", f"{len(line)} characters (the most is {width})"))
    run_ends(len(lines))
    anchors |= {slug(h) for h in heads}
    named = {h.strip("`*_ ").lower() for h in heads}
    for n, name in entries:
        if slug(name) not in anchors and name not in anchors:
            out.append((n, "jump", f"`{name}` has no anchor to jump to"))
    for n, name in folders:
        if not any(name.lower() in h.split() or f"{name}/".lower() in h.split() for h in named):  # fmt: skip
            out.append((n, "jump", f"`{name}/` has no heading of its own"))
    return sorted(out)


def args_of(argv: list[str]) -> tuple[list[str], int, int]:
    if not argv or argv[0] != "check":
        raise ValueError(USAGE)
    files, nums, it = [], {"--screen": SCREEN, "--width": WIDTH}, iter(argv[1:])
    for a in it:
        if a in nums:
            value = next(it, "")
            if not value.isdigit() or int(value) == 0:
                raise ValueError(USAGE)
            nums[a] = int(value)
        elif a.startswith("-"):
            raise ValueError(USAGE)
        else:
            files.append(a)
    return files, nums["--screen"], nums["--width"]


def main(argv: list[str]) -> int:
    try:
        files, screen, width = args_of(argv)
    except ValueError as why:
        print(why, file=sys.stderr)
        return kernel.REFUSED
    named = files or list(LISTS)
    paths = [Path(f) for f in files] or [ROOT / name for name in LISTS]
    for p in paths:
        if not p.is_file():
            print(f"refused: no file {p}", file=sys.stderr)
            return kernel.REFUSED
    found = 0
    for shown, p in zip(named, paths):
        places = skim(p.read_text(encoding="utf-8"), screen, width)
        counts = {c: sum(1 for _, k, _ in places if k == c) for c in ("screen", "width", "jump")}  # fmt: skip
        for n, check, what in places:
            print(f"{shown}:{n}: {check}: {what}")
        said = ", ".join(f"{v} {k}" for k, v in counts.items())
        print(f"{shown}: {'reads within the bounds' if not places else said}")
        found += len(places)
    return kernel.ESCALATE if found else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
