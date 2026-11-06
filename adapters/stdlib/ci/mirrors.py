"""mirrors.py: the mirror contract, checked. Python 3.9+.

    python adapters/stdlib/ci/mirrors.py check --from FOLDER --mirror MIRROR

A reader that keeps the mirror contract (adapters/stdlib/ci/README.md; its
card says `output: mirror`) writes, beside each `MIRROR/<path>.txt`, a
hidden `MIRROR/.places/<path>.txt.json`:

    {"source": "notes/garden.md", "places": {"1": "line 3", "5": "lines 9-10"}}

Each key is the mirror line a passage starts on, each value the place in the
source it came from: `line N`, `lines N-M`, or another named place (`page
2`, `cell 4`, `row 17`). The kernel skips hidden folders, so the map is never
served, and the passages hold only the file's words. A chunk the kernel cuts
from a longer passage is at the last place at or before its line.

`check` holds a mirror to it, and test_contract.py and realdata.py hold each
reader that says it to it, on its sample and on the demo people's folders:

- every mirror file has its map, naming that file's source, and no map is
  left without a mirror file;
- every passage (a run of lines after a blank one) starts on a line the map
  names; it may name a line inside one too (subtitles places each cue, so a
  chunk the kernel cuts from a long passage is at its own cue), but never a
  blank line or one past the file's end;
- a passage that opens with its own citation line (the source's path, then
  `line N`) cites a line inside its place, and the next line is the one
  held to the word rule;
- a line place is inside the source file, and a content word of the
  passage's first line (not "the" or "in") is on the source's line or lines
  there, so an off-by-one shows;
- no mirror line is longer than one of the kernel's chunks, which it would
  cut unread.

Exit codes, the kernel's: 0 the mirror keeps the contract; 42 it doesn't, and
each break is said; 2 refused (a bad command line, a folder that isn't one).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: mirrors.py check --from FOLDER --mirror MIRROR"
PLACES = ".places"
LINE = re.compile(r"line (\d+)|lines (\d+)-(\d+)")
NAMED = re.compile(r"[a-z]+ \S.*")


def starts(text: str) -> list[int]:
    """The line each passage starts on: a line with words after a blank one,
    or the first, as the kernel cuts paragraphs."""
    lines = text.splitlines()
    return [i for i, s in enumerate(lines, 1) if s.strip() and (i == 1 or not lines[i - 2].strip())]  # fmt: skip


def words(line: str) -> set[str]:
    """A line's content words, as the kernel's rank counts them: "in" and
    "the" are on every other line, and would hide an off-by-one."""
    return {w.lower() for w in kernel.words(line)} - kernel.FUNCTION


def cited(first: str, name: str) -> int | None:
    """The line a passage's own citation line names, when it opens with one:
    the source's path, then `line N` (anything after a comma, its labels)."""
    m = re.fullmatch(re.escape(name) + r" line (\d+)(?:, .*)?", first)
    return int(m.group(1)) if m else None


def check_file(text: str, places: dict, source: list[str], name: str = "") -> list[str]:
    """What breaks the contract in one mirror file and its map's places. A
    passage that opens with its own citation line (equations' `paper/main.tex
    line 120, label eq:oz`) is held to cite a line inside its place, and its
    next line to the word rule."""
    out, lines = [], text.splitlines()
    want = {str(i) for i in starts(text)}
    if not isinstance(places, dict) or not all(
        isinstance(v, str) for v in places.values()
    ):
        return ["its places are not a map of line to place"]
    for k in sorted(want - set(places), key=int):
        out.append(f"line {k} starts a passage the map doesn't place")
    inside = {str(i) for i, s in enumerate(lines, 1) if s.strip()} - want
    for k in sorted(set(places) - want - inside, key=lambda k: (not k.isdigit(), int(k) if k.isdigit() else 0, k)):  # fmt: skip
        out.append(f"the map places {k!r}, which is no line with words")
    for k in sorted((want | inside) & set(places), key=int):
        place, first = places[k], lines[int(k) - 1]
        m = LINE.fullmatch(place)
        if m is None:
            if not NAMED.fullmatch(place):
                out.append(f"line {k}: {place!r} is not a place")
            continue
        a, b = (int(m[1]), int(m[1])) if m[1] else (int(m[2]), int(m[3]))
        cite = cited(first, name) if name else None
        if cite is not None:
            if not a <= cite <= b:
                out.append(
                    f"line {k}: it cites line {cite}, outside its place, {place}"
                )
                continue
            first = lines[int(k)] if int(k) < len(lines) else ""
        if not 1 <= a <= b <= len(source):
            out.append(f"line {k}: {place} is outside the source's {len(source)} lines")
        elif words(first) and not words(first) & set().union(
            *(words(s) for s in source[a - 1 : b])
        ):
            out.append(
                f"line {k}: no word of {first[:40]!r} is on the source's {place}"
            )
    for i, line in enumerate(lines, 1):
        if len(line) > kernel.MAX_CHUNK:
            out.append(
                f"line {i} is {len(line)} characters, past the kernel's {kernel.MAX_CHUNK}"
            )
    return out


def check(folder: Path, mirror: Path) -> list[str]:
    """Every break of the contract in MIRROR, made from FOLDER, as
    `path: what`; none when it keeps it."""
    out = []
    texts = sorted(p for p in mirror.rglob("*.txt") if p.is_file()
                   and not any(s.startswith(".") for s in p.relative_to(mirror).parts))  # fmt: skip
    maps = {
        p.relative_to(mirror / PLACES).as_posix()
        for p in (mirror / PLACES).rglob("*.json")
    }
    for p in texts:
        rel = p.relative_to(mirror).as_posix()
        maps.discard(rel + ".json")
        try:
            doc = json.loads(
                (mirror / PLACES / (rel + ".json")).read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            out.append(f"{rel}: no map in {PLACES}/ that reads")
            continue
        if not isinstance(doc, dict) or doc.get("source") != rel[: -len(".txt")]:
            out.append(
                f"{rel}: its map doesn't name {rel[: -len('.txt')]} as its source"
            )
            continue
        try:
            source = (
                (folder / doc["source"])
                .read_bytes()
                .decode("utf-8", "replace")
                .splitlines()
            )
        except OSError:
            out.append(f"{rel}: its source {doc['source']} isn't in the folder")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        out += [
            f"{rel}: {why}"
            for why in check_file(text, doc.get("places"), source, doc["source"])
        ]
    out += [f"{PLACES}/{m}: a map with no mirror file" for m in sorted(maps)]
    return out


def keeps(card: Path) -> bool:
    """Whether a reader's card says `output: mirror`, among its outputs."""
    head = re.search(
        r"<!--\s*willow-addon\s*\n(.*?)-->", card.read_text(encoding="utf-8"), re.S
    )
    return bool(
        head
        and re.search(r"^output:(?:.*,)?\s*mirror\s*(?:,.*)?$", head.group(1), re.M)
    )


def main(argv: list[str]) -> int:
    if (
        len(argv) != 5
        or argv[0] != "check"
        or argv[1] != "--from"
        or argv[3] != "--mirror"
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder, mirror = Path(argv[2]), Path(argv[4])
    if not folder.is_dir() or not mirror.is_dir():
        print(
            f"refused: {folder if not folder.is_dir() else mirror} is not a folder",
            file=sys.stderr,
        )
        return kernel.REFUSED
    broke = check(folder, mirror)
    for b in broke:
        print(b)
    print(
        f"{len(broke)} break(s) of the mirror contract"
        if broke
        else "the mirror keeps the mirror contract"
    )
    return kernel.ESCALATE if broke else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
