r"""text.py: Plain-text files the kernel can't read, as UTF-8 it can, line for line. Python 3.9+.

    python adapters/stdlib/text/text.py mirror --from FOLDER --to MIRROR [--encoding NAME]

Walks FOLDER for .txt and .text files (hidden folders and files skipped) and
writes every one as UTF-8 with LF line endings, so the kernel reads all of them:
the ones it already could, and the ones it leaves out without a word (a Windows
"Unicode" file, an old code page, a file over `kernel.MAX_FILE`, a line longer
than `kernel.MAX_CHUNK`). Point the kernel at MIRROR instead of the originals.

How a file is decoded, only when it is certain:

- UTF-8, with or without a byte order mark;
- UTF-16 or UTF-32, either byte order, when the file starts with its mark;
- UTF-16 with no mark when its first `kernel.SNIFF` bytes (all of a smaller
  file) alternate exactly: every byte in one position of each pair NUL and every
  byte in the other not, as English or other Latin-1 text saved as UTF-16 is;
- anything else only when you name its encoding with `--encoding NAME`
  (cp1252, latin-1, cp1251, mac-roman, utf-16-le...), which applies only to
  files the rules above can't decode. Nothing is guessed: without it such a file
  is skipped, counted and named on stderr.

A decoded text holding a NUL character is not text (a binary named .txt): it is
skipped and counted, whatever the encoding.

Line for line: CRLF and a bare CR (an old Mac file) become LF, so line N of the
mirror is line N of the file as an editor counts it. A line that is only a form
feed becomes blank, so a page break ends a passage; a form feed or another
character Python breaks lines at (vertical tab, NEL, U+2028...) inside a line
becomes a space, since a new line there would move every line after it.

Two things move lines, and nothing is written into the text to say so (a
word or number written into it would be served for a question it doesn't
answer). A hidden file beside the mirror, `.NAME.lines` (the kernel never
reads a hidden file), says where they go: one tab-separated row per place the
numbering starts again, the mirror file, its line, and the source line it is.
A mirror line is the source line of the last row at or above it, counted on.

- A line longer than `kernel.MAX_CHUNK` characters, which the kernel would cut
  short (a paragraph per line, as Notepad saves it), is broken at spaces into
  lines it reads whole, every piece the same source line.
- A mirror bigger than `kernel.MAX_FILE` is cut into parts the kernel reads,
  at a blank line where there is one, else between lines, never between two
  pieces of one line: `NAME.txt`, then `NAME.part2.txt` and on. Parts a
  shorter earlier run left behind are removed, and so is a map no longer
  needed.

Hard-wrapped prose with no blank lines is left as it is: rejoining it would
lose the line numbers. The kernel takes it in runs of whole lines.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file over 50 MB is not read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, MIRROR and FOLDER are inside one another, or NAME is not a
text encoding Python knows).
"""

from __future__ import annotations

import codecs
import os
import re
import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 50 * 1024 * 1024
EXTS = (".txt", ".text")
#: (byte order mark, codec that drops it), the longer marks first: UTF-32 LE's
#: mark starts with UTF-16 LE's
BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)
#: characters str.splitlines breaks at that an editor doesn't count as a new line
INNER_BREAKS = re.compile("[\x0b\x0c\x1c\x1d\x1e\x85  ]")


class Skip(ValueError):
    """A file that is not read, with the reason said."""


def bare_utf16(data: bytes) -> str | None:
    """The codec of UTF-16 with no mark, when the sniff window alternates
    exactly NUL / not NUL, else None."""
    head = data[: kernel.SNIFF]
    if len(head) < 2 or len(data) % 2:
        return None
    even, odd = head[0::2], head[1::2]
    if b"\0" not in even and odd.count(0) == len(odd):
        return "utf-16-le"
    if b"\0" not in odd and even.count(0) == len(even):
        return "utf-16-be"
    return None


def decode(data: bytes, encoding: str | None = None) -> str:
    """The text of `data` by the rules above, or Skip saying why not."""
    if len(data) > BIGGEST:
        raise Skip("over 50 MB")
    codec = next((c for bom, c in BOMS if data.startswith(bom)), None)
    tried = []
    if codec == "utf-32":
        tried.append("utf-32")
        codec = "utf-16" if data.startswith(codecs.BOM_UTF16_LE) else None
    if codec:
        tried.append(codec)
    elif b"\0" not in data:
        tried.append("utf-8")
    elif bare := bare_utf16(data):
        tried.append(bare)
    if encoding:
        tried.append(encoding)
    for name in tried:
        try:
            text = data.decode(name)
        except UnicodeDecodeError:
            continue
        if "\0" in text:
            raise Skip("binary: it holds NUL characters")
        return text
    if encoding:
        raise Skip(f"not {encoding}, and not UTF-8 or UTF-16 by the rules")
    if b"\0" in data:
        raise Skip(
            "NUL bytes, and no UTF-16 mark or pattern: binary, "
            "or text whose encoding --encoding can name"
        )
    raise Skip("not UTF-8; name its encoding with --encoding")


def lines_of(text: str) -> list[str]:
    """The lines as an editor counts them: at LF, CRLF and a bare CR."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.endswith("\n"):
        text = text[:-1]
    out = []
    for line in text.split("\n"):
        if "\f" in line and not line.strip():
            line = ""
        out.append(INNER_BREAKS.sub(" ", line))
    return out


def wrap(line: str, width: int = kernel.MAX_CHUNK) -> list[str]:
    """`line` broken at spaces into pieces of at most `width` characters; a
    run with no space that long is cut where it reaches it."""
    out = []
    while len(line) > width:
        cut = line.rfind(" ", 1, width + 1)
        if cut <= 0:
            cut = width
        out.append(line[:cut].rstrip())
        line = line[cut:].lstrip(" ")
    return out + [line]


Row = Tuple[str, int]


def convert(data: bytes, encoding: str | None = None) -> list[Row]:
    """The mirror's lines, each with the source line it is: a long line broken
    in pieces that all name it. Skip when there is nothing to read."""
    lines = lines_of(decode(data, encoding))
    if not any(line.strip() for line in lines):
        raise Skip("empty")
    out: list[Row] = []
    for n, line in enumerate(lines, 1):
        out.extend((piece, n) for piece in wrap(line))
    return out


def parts(rows: list[Row], limit: int = kernel.MAX_FILE) -> list[list[Row]]:
    """The mirror's lines cut into parts of at most `limit` bytes as UTF-8, at
    the last blank line of the second half of a part, else before the last
    source line that starts in it, never between two pieces of one line."""
    out: list[list[Row]] = []
    piece: list[Row] = []
    size = 0
    for row in rows:
        raw = len(row[0].encode("utf-8")) + 1
        if piece and size + raw > limit:
            ahead = piece + [row]
            starts = [j for j in range(1, len(ahead)) if ahead[j][1] != ahead[j - 1][1]]  # fmt: skip
            blanks = [j for j in starts if j >= len(piece) // 2 and not piece[j - 1][0].strip()]  # fmt: skip
            cut = (blanks or starts or [len(piece)])[-1]
            out.append(piece[:cut])
            piece = piece[cut:]
            size = sum(len(text.encode("utf-8")) + 1 for text, _ in piece)
        piece.append(row)
        size += raw
    out.append(piece)
    return out


def runs(piece: list[Row]) -> list[tuple[int, int]]:
    """(mirror line, source line) where a part's numbering starts again: its
    first line, and each line that is not the one after the line above it."""
    return [(i, n) for i, (_, n) in enumerate(piece, 1)
            if i == 1 or n != piece[i - 2][1] + 1]  # fmt: skip


def source_line(lines_map: str, part: str, at: int) -> int:
    """Line `at` of mirror file `part` as a line of its source, by the map:
    the last run starting at or above it, counted on."""
    starts = [(int(m), int(n)) for f, m, n in (row.split("\t") for row in lines_map.splitlines()) if f == part]  # fmt: skip
    m, n = max((m, n) for m, n in starts if m <= at)
    return n + at - m


def _part_name(name: str, n: int) -> str:
    return f"{name}.txt" if n == 1 else f"{name}.part{n}.txt"


def _map_name(name: str) -> str:
    return f".{name}.lines"


USAGE = "usage: text.py mirror --from FOLDER --to MIRROR [--encoding NAME]"


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


def mirror(src: Path, dst: Path, encoding: str | None = None) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            pieces = parts(convert(path.read_bytes(), encoding))
            folder = dst.joinpath(rel.parent)
            folder.mkdir(parents=True, exist_ok=True)
            starts = []
            for n, piece in enumerate(pieces, 1):
                name = _part_name(rel.name, n)
                text = "\n".join(line for line, _ in piece) + "\n"
                (folder / name).write_bytes(text.encode("utf-8"))
                starts += [f"{name}\t{m}\t{s}\n" for m, s in runs(piece)]
            n = len(pieces) + 1
            while (folder / _part_name(rel.name, n)).is_file():
                (folder / _part_name(rel.name, n)).unlink()
                n += 1
            lines_map = folder / _map_name(rel.name)
            if len(starts) > 1:
                lines_map.write_bytes("".join(starts).encode("utf-8"))
            elif lines_map.is_file():
                lines_map.unlink()
        except (OSError, Skip) as e:
            print(f"skipped {rel.as_posix()}: {e}", file=sys.stderr)
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def text_encoding(name: str) -> bool:
    """Whether Python knows `name` as an encoding of text (not base64 or zlib)."""
    try:
        info = codecs.lookup(name)
    except LookupError:
        return False
    return getattr(info, "_is_text_encoding", True)


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    keys = sorted(opts)
    if len(argv) not in (5, 7) or keys not in (
        ["--from", "--to"],
        ["--encoding", "--from", "--to"],
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    encoding = opts.get("--encoding")
    if encoding is not None and not text_encoding(encoding):
        print(f"refused: not a text encoding Python knows: {encoding}", file=sys.stderr)
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
    wrote, skipped = mirror(src, dst, encoding)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
