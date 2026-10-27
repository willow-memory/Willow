"""subtitles.py: subtitle and transcript files, each line cited by its time.

    python adapters/stdlib/subtitles/subtitles.py mirror --from FOLDER --to MIRROR

Walks FOLDER for subtitles and transcripts, skipping hidden folders and
files: .srt files, and .vtt files, which open with WEBVTT. Each cue becomes
one line, its start time first, so what a podcast or a talk said can be
asked about and the answer carries the moment to scrub to:

    00:00:01  The tide keeps its own calendar.
    00:00:04  Ada: And the harbour keeps the tide's.

A cue's lines are joined with a space; styling tags are taken off, and a
WebVTT voice tag becomes the speaker's name with a colon. Times are written
HH:MM:SS, hours added where a cue leaves them off, and the fractions
dropped: a second is as close as a person scrubs. Cue numbers, NOTE and
STYLE blocks say nothing and are left out. A .srt with no readable cue, or
a .vtt without its WEBVTT first line, is skipped and counted, never guessed
at.

Each file is written to MIRROR at the same relative path with .txt added:
`talks/ep1.srt` becomes `MIRROR/talks/ep1.srt.txt`. FOLDER is only read.
Originals are never modified and nothing is written inside it. A file that
cannot be read is skipped and counted, never a crash.

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of what was said.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: subtitles.py mirror --from FOLDER --to MIRROR"
TIME = re.compile(
    r"^\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*"
    r"(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}"
)
VOICE = re.compile(r"<v(?:\.[^ >]*)?\s+([^>]+)>", re.IGNORECASE)
TAG = re.compile(r"<[^>]*>")


def start_of(line: str) -> str | None:
    """The cue line's start as HH:MM:SS, or None for a line that is no cue
    timing: hours added where left off, the fraction dropped."""
    m = TIME.match(line)
    if not m:
        return None
    h, mnt, s = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
    return f"{h:02}:{mnt:02}:{s:02}"


def said(lines: list[str]) -> str:
    """A cue's text as one line: joined with a space, a voice tag as its
    speaker's name with a colon, styling tags off."""
    text = " ".join(" ".join(lines).split())
    text = VOICE.sub(lambda m: f"{m.group(1).strip()}: ", text)
    return " ".join(TAG.sub("", text).split())


def cues(raw: bytes, vtt: bool) -> str | None:
    """The mirror text: one line per cue, its start first. None when the file
    is not what its name says (a .vtt without WEBVTT first, a .srt with no
    readable cue)."""
    lines = raw.decode("utf-8-sig", errors="strict").splitlines()
    if vtt and not (lines and lines[0].strip().split()[:1] == ["WEBVTT"]):
        return None
    out, text, when, skip = [], [], None, False
    for line in lines + [""]:
        if not line.strip():
            if when is not None and text:
                out.append(f"{when}  {said(text)}")
            text, when, skip = [], None, False
            continue
        if skip:
            continue
        if re.match(r"^\s*(NOTE|STYLE|REGION)\b", line) and when is None:
            skip = True
            continue
        got = start_of(line)
        if got:
            when, text = got, []
        elif when is not None:
            text.append(line)
    if not out:
        return None
    return "\n".join(out) + "\n"


def _sources(folder: Path) -> list[Path]:
    """The .srt and .vtt files under `folder`, sorted by relative path.
    Hidden folders and files are skipped; symlinked folders not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            lower = name.lower()
            if (
                not name.startswith(".")
                and lower.endswith((".srt", ".vtt"))
                and p.is_file()
            ):
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
            text = cues(path.read_bytes(), path.name.lower().endswith(".vtt"))
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except (OSError, UnicodeDecodeError):
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
