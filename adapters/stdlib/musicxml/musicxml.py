r"""musicxml.py: MusicXML scores: titles, lyrics, tempo and performance markings. Python 3.9+.

    python adapters/stdlib/musicxml/musicxml.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .musicxml files, and for .xml files that are a partwise
MusicXML score (hidden folders and files skipped; other XML is skipped and
counted), and writes each score as what can be read in words:

    title: Evening Song
    composer: Ana Example; lyricist: Ben Sample
    parts: Soprano, Alto
    key: G major; time: 3/4; tempo: 72
    markings: m.1 Andante; m.1 p; m.9 cresc.; m.17 f
    lyrics (Soprano): Evening comes softly down
    lyrics (Soprano, verse 2): Morning comes again

The title is the work title, then the movement title; the composer and the
lyricist are the credits of that type. The key and time are the first the score
gives, the tempo the first sound tempo. Markings are the words and dynamics in
the score, each with its measure. Lyrics are the syllables of each verse, in
order, joined into words where the score splits a word across notes. The notes themselves
are not copied. A file that declares entities is not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MAJOR = [
    "Cb",
    "Gb",
    "Db",
    "Ab",
    "Eb",
    "Bb",
    "F",
    "C",
    "G",
    "D",
    "A",
    "E",
    "B",
    "F#",
    "C#",
]
MINOR = [
    "Ab",
    "Eb",
    "Bb",
    "F",
    "C",
    "G",
    "D",
    "A",
    "E",
    "B",
    "F#",
    "C#",
    "G#",
    "D#",
    "A#",
]


def text_of(parent, tag: str) -> str:
    e = parent.find(tag) if parent is not None else None
    return " ".join("".join(e.itertext()).split()) if e is not None else ""


def key_name(fifths: str, mode: str) -> str:
    try:
        n = int(fifths)
    except ValueError:
        return ""
    if not -7 <= n <= 7:
        return ""
    minor = mode.strip().lower() == "minor"
    return f"{(MINOR if minor else MAJOR)[n + 7]} {'minor' if minor else 'major'}"


def lyrics_of(part) -> dict[str, str]:
    """{verse: the words}, syllables joined where the score hyphenates them."""
    verses: dict[str, list[str]] = {}
    for note in part.iter("note"):
        for lyric in note.findall("lyric"):
            verse = lyric.get("number") or "1"
            syl, kind = text_of(lyric, "text"), text_of(lyric, "syllabic") or "single"
            if not syl:
                continue
            words = verses.setdefault(verse, [])
            joined = words and words[-1].endswith("\0")
            if joined:
                words[-1] = words[-1][:-1] + syl
            else:
                words.append(syl)
            if kind in ("begin", "middle"):
                words[-1] += "\0"
    return {
        v: " ".join(w.replace("\0", "-") if w.endswith("\0") else w for w in ws)
        for v, ws in verses.items()
    }


def convert(data: bytes) -> str | None:
    if b"<!ENTITY" in data or b"<score-partwise" not in data[:4000]:
        return None
    root = ET.fromstring(data)
    lines = []
    title = text_of(root.find("work"), "work-title")
    if title:
        lines.append(f"title: {title}")
    movement = text_of(root, "movement-title")
    if movement and movement != title:
        lines.append(f"movement: {movement}")
    credits = []
    for kind in ("composer", "lyricist"):
        names = [
            " ".join("".join(c.itertext()).split())
            for c in root.iter("creator")
            if c.get("type") == kind
        ]
        if names:
            credits.append(f"{kind}: {', '.join(n for n in names if n)}")
    if credits:
        lines.append("; ".join(credits))
    names = {sp.get("id"): text_of(sp, "part-name") for sp in root.iter("score-part")}
    if any(names.values()):
        lines.append("parts: " + ", ".join(n for n in names.values() if n))
    facts = []
    key = next(root.iter("key"), None)
    if key is not None and key_name(text_of(key, "fifths"), text_of(key, "mode")):
        facts.append(f"key: {key_name(text_of(key, 'fifths'), text_of(key, 'mode'))}")
    time = next(root.iter("time"), None)
    if time is not None and text_of(time, "beats") and text_of(time, "beat-type"):
        facts.append(f"time: {text_of(time, 'beats')}/{text_of(time, 'beat-type')}")
    tempo = next((s.get("tempo") for s in root.iter("sound") if s.get("tempo")), None)
    if tempo:
        facts.append(f"tempo: {tempo}")
    if facts:
        lines.append("; ".join(facts))
    marks = []
    first = next(root.iter("part"), None)
    for measure in first.iter("measure") if first is not None else []:
        for d in measure.iter("direction-type"):
            for w in d.findall("words"):
                if text_of(w, ".") if False else "".join(w.itertext()).strip():
                    marks.append(
                        f"m.{measure.get('number', '?')} {' '.join(''.join(w.itertext()).split())}"
                    )
            for dyn in d.findall("dynamics"):
                marks.extend(f"m.{measure.get('number', '?')} {c.tag}" for c in dyn)
    if marks:
        lines.append("markings: " + "; ".join(marks))
    for part in root.iter("part"):
        who = names.get(part.get("id"), "") or part.get("id", "")
        for verse, words in sorted(lyrics_of(part).items()):
            label = who if verse == "1" else f"{who}, verse {verse}"
            lines.append(f"lyrics ({label}): {words}")
    return "\n".join(lines) + "\n" if lines else None


EXTS = (".musicxml", ".xml")
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: musicxml.py mirror --from FOLDER --to MIRROR"


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
