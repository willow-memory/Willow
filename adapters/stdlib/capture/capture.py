"""capture.py: a note written into your folder in one line. Python 3.9+.

    python adapters/stdlib/capture/capture.py --to DIR [--type WORD] [--tags a,b] [--now TS] "the note"

Writes one small text file into DIR, an existing folder: the note on its first
line, then `type:`, `tags:` (left out when there are none) and `captured:`
lines, with no blank line between them. That is one paragraph, so the kernel's
`chunks` serves it whole and `bite` finds it by the note's words, its type or
its tags. The note's whitespace is folded to single spaces; it is refused if
the paragraph would be over the kernel's chunk size, since a longer one would
be cut in two and its type and tags parted from the note.

The file is named for the second it was captured and a fingerprint of what it
holds, and is created, never opened over one that is there: two captures never
overwrite each other, the same note in the same second getting -2, -3.

It writes that one file and nothing else. It does not make DIR, does not write
into a box (a folder holding a kernel.json), never touches the record or the
key, and never goes online. To ask about the notes, make DIR a pile.

Exit codes, the kernel's: 0 written; 2 refused (a bad command line, DIR not a
folder or a box, a word that isn't one, or a note empty or too long).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1].strip()
WORD = re.compile(r"[a-z0-9][a-z0-9-]*")
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
ROOM = kernel.MAX_CHUNK - 1  # the paragraph, its newlines counted, stays one chunk


def parse(argv: list[str]) -> tuple[dict, list[str]]:
    opts: dict[str, str] = {}
    words: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--to", "--type", "--tags", "--now"):
            opts[a] = next(it, "")
        else:
            words.append(a)
    return opts, words


def paragraph(text: str, kind: str, tags: list[str], ts: str) -> str:
    lines = [" ".join(text.split()), f"type: {kind}"]
    if tags:
        lines.append("tags: " + ", ".join(tags))
    lines.append(f"captured: {ts}")
    return "\n".join(lines) + "\n"


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def write_new(folder: Path, stem: str, body: str) -> Path:
    """Create stem.txt, or stem-2.txt and so on, never opening a file that exists."""
    n = 1
    while True:
        path = folder / (f"{stem}.txt" if n == 1 else f"{stem}-{n}.txt")
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write(body)
            return path
        except FileExistsError:
            n += 1


def main(argv: list[str]) -> int:
    opts, words = parse(argv)
    if (
        not opts.get("--to")
        or len(words) != 1
        or words[0].startswith("--")
        or set(opts) - {"--to", "--type", "--tags", "--now"}
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder = Path(opts["--to"])
    if not folder.is_dir():
        return refuse(f"{folder} isn't a folder; it isn't made for you")
    if (folder / "kernel.json").exists():
        return refuse(f"{folder} is a box; a box is written only through the kernel")
    kind = opts.get("--type", "note")
    if not WORD.fullmatch(kind):
        return refuse("a type is one lowercase word (a-z, 0-9, -)")
    tags: list[str] = []
    for tag in (t.strip() for t in opts.get("--tags", "").split(",")):
        if tag and not WORD.fullmatch(tag):
            return refuse(f"a tag is one lowercase word (a-z, 0-9, -): {tag!r}")
        if tag and tag not in tags:
            tags.append(tag)
    if "--tags" in opts and not tags:
        return refuse("--tags names no tag")
    ts = opts.get("--now") or kernel.now()
    if not STAMP.fullmatch(ts):
        return refuse("a time reads YYYY-MM-DDTHH:MM:SSZ")
    if not words[0].strip():
        return refuse("the note is empty")
    body = paragraph(words[0], kind, tags, ts)
    if len(body) - 1 > ROOM:
        return refuse(
            f"the note is {len(body) - 1} characters with its lines; "
            f"one passage holds {ROOM}"
        )
    stamp = ts.replace("-", "").replace(":", "")
    path = write_new(folder, f"{stamp}-{kernel.h256(body)[:8]}", body)
    print(f"written: {path}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
