r"""chordpro.py: ChordPro song sheets: titles, lyrics and chords. Python 3.9+.

    python adapters/stdlib/chordpro/chordpro.py mirror --from FOLDER --to MIRROR

Walks FOLDER for ChordPro files (.cho, .chordpro, .chopro, .crd, .pro; hidden
folders and files skipped) and writes each song as its title line, then its
lyrics with the chords taken out of the lines and kept in a line of their own
list, so a question about a lyric finds the song:

    song: Down by the Estuary, by Ada Example (key G, capo 2)
    chords: G, C, D, Em

    Verse:
    Down by the estuary the tide comes in
    Chorus:
    Oh, the water, the water

The directives used: title (t), subtitle (st), artist, composer, lyricist,
album, year, key and capo; `comment` (c) lines are kept as lyrics; verse,
chorus, bridge and tab sections are labelled, and a tab section is dropped.
`#` lines are comments. A chord is a name in square brackets; the chords of a
song are listed once, in the order they first appear. A file may hold several
songs, split by `{new_song}`.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no song text is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

DIRECTIVE = re.compile(r"^\s*\{\s*([A-Za-z_]+)\s*(?::\s*|\s+)?(.*?)\s*\}\s*$")
CHORD = re.compile(r"\[([^\[\]]*)\]")
ALIAS = {"t": "title", "st": "subtitle", "su": "subtitle", "c": "comment", "ci": "comment", "cb": "comment", "ns": "new_song",
         "soc": "start_of_chorus", "eoc": "end_of_chorus", "sov": "start_of_verse", "eov": "end_of_verse", "sob": "start_of_bridge",
         "eob": "end_of_bridge", "sot": "start_of_tab", "eot": "end_of_tab", "k": "key", "a": "artist"}  # fmt: skip
SECTION = {
    "chorus": "Chorus",
    "verse": "Verse",
    "bridge": "Bridge",
    "tab": None,
    "grid": None,
}


def songs(text: str) -> list[dict]:
    """[{meta, chords, lines}] for each song in the file."""
    out: list[dict] = []
    cur = {"meta": {}, "chords": [], "lines": []}
    in_tab = False

    def close() -> None:
        nonlocal cur
        if cur["lines"] or cur["meta"]:
            out.append(cur)
        cur = {"meta": {}, "chords": [], "lines": []}

    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.lstrip().startswith("#"):
            continue
        m = DIRECTIVE.match(raw)
        if m:
            name = ALIAS.get(m.group(1).lower(), m.group(1).lower())
            arg = m.group(2).strip()
            if name == "new_song":
                close()
            elif name.startswith("start_of_"):
                kind = name[9:]
                in_tab = SECTION.get(kind, "?") is None
                label = SECTION.get(kind, kind.replace("_", " ").title())
                if label and not in_tab:
                    cur["lines"].append(f"{arg or label}:" if arg else f"{label}:")
            elif name.startswith("end_of_"):
                in_tab = False
            elif name == "comment" and arg:
                cur["lines"].append(arg)
            elif (
                name
                in (
                    "title",
                    "subtitle",
                    "artist",
                    "composer",
                    "lyricist",
                    "album",
                    "year",
                    "key",
                    "capo",
                )
                and arg
            ):
                cur["meta"].setdefault(name, arg)
            continue
        if in_tab:
            continue
        for chord in CHORD.findall(raw):
            if chord.strip() and chord.strip() not in cur["chords"]:
                cur["chords"].append(chord.strip())
        lyric = " ".join(CHORD.sub("", raw).split())
        if lyric:
            cur["lines"].append(lyric)
        elif cur["lines"] and cur["lines"][-1] != "":
            cur["lines"].append("")
    close()
    return out


def convert(data: bytes) -> str | None:
    blocks = []
    for s in songs(data.decode("utf-8-sig")):
        meta = s["meta"]
        who = ", ".join(
            x
            for x in (
                f"by {meta['artist']}" if meta.get("artist") else "",
                f"words {meta['lyricist']}" if meta.get("lyricist") else "",
                f"music {meta['composer']}" if meta.get("composer") else "",
            )
            if x
        )
        extra = ", ".join(
            x
            for x in (
                f"key {meta['key']}" if meta.get("key") else "",
                f"capo {meta['capo']}" if meta.get("capo") else "",
                meta.get("year", ""),
            )
            if x
        )
        head = (
            f"song: {meta.get('title', '(untitled)')}"
            + (f", {who}" if who else "")
            + (f" ({extra})" if extra else "")
        )
        lines = [head]
        if meta.get("subtitle"):
            lines.append(meta["subtitle"])
        if meta.get("album"):
            lines.append(f"album: {meta['album']}")
        if s["chords"]:
            lines.append("chords: " + ", ".join(s["chords"]))
        body = "\n".join(s["lines"]).strip("\n")
        blocks.append("\n".join(lines) + ("\n\n" + body if body else ""))
    blocks = [b for b in blocks if b.count("\n") or "(untitled)" not in b]
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".cho", ".chordpro", ".chopro", ".crd", ".pro")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: chordpro.py mirror --from FOLDER --to MIRROR"


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
