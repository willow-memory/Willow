r"""pgn.py: Chess games from PGN files: players, dates, openings and your notes. Python 3.9+.

    python adapters/stdlib/pgn/pgn.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .pgn files (hidden folders and files skipped) and writes each
game as a paragraph: who played, where, when, the result and the opening, and
then every comment you or an engine wrote in the moves, each with the move it
follows:

    game: Ada Example vs Cy Sample, 2024-03-03, Club Championship, Leeds
    result: 1-0 (Sicilian Defense, B20)
    note after 1.e4: My usual start.
    note after 14...Qd7: I missed the fork here.

A comment is kept whole, with the move it follows (`14...Qd7` is Black's 14th).
Variations in brackets are skipped, their comments kept. The moves themselves
are not copied; a PGN is read for who, when, where and what you said about it.
An unknown date (`????.??.??`) is left out. The Event, Site, White, Black,
Date, Result, Opening and ECO tags are used, and so is a `[Annotator]`.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no game is skipped and counted.

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

TAG = re.compile(r'^\[\s*([A-Za-z0-9_]+)\s+"((?:[^"\\]|\\.)*)"\s*\]\s*$')
MOVETEXT = re.compile(
    r"\{([^}]*)\}|;([^\n]*)|(\()|(\))|\$\d+|(\d+)(\.{1,3})|([^\s{};()$]+)", re.S
)
RESULTS = {"1-0", "0-1", "1/2-1/2", "*"}


def games(text: str) -> list[tuple[dict[str, str], str]]:
    """[(tags, movetext)] for each game in the file."""
    out, tags, moves = [], {}, []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        m = TAG.match(line)
        if m:
            if moves:
                out.append((tags, "\n".join(moves)))
                tags, moves = {}, []
            tags[m.group(1)] = m.group(2).replace('\\"', '"').replace("\\\\", "\\")
        elif line or moves:
            moves.append(raw)
    if tags or "".join(moves).strip():
        out.append((tags, "\n".join(moves)))
    return [(t, mv) for t, mv in out if t or mv.strip()]


def notes(moves: str) -> list[str]:
    """Each comment, with the main-line move it follows (Black's with three dots)."""
    out, idx, last, depth = [], 0, "the start", 0
    for m in MOVETEXT.finditer(moves):
        comment, line_comment, open_, close, num, dots, word = m.groups()
        if open_:
            depth += 1
        elif close:
            depth = max(0, depth - 1)
        elif num:
            if not depth:
                idx = 2 * (int(num) - 1) + (1 if len(dots) == 3 else 0)
        elif word:
            if depth or word in RESULTS:
                continue
            last = f"{idx // 2 + 1}{'...' if idx % 2 else '.'}{word}"
            idx += 1
        else:
            text = " ".join(
                (comment if comment is not None else line_comment or "").split()
            )
            if text:
                out.append(f"note after {last}: {text}")
    return out


def known(value: str | None) -> str:
    return "" if not value or value.strip("?.- ") == "" else value.strip()


def convert(data: bytes) -> str | None:
    text = (
        data.decode("utf-8-sig", errors="strict")
        if data.isascii()
        else data.decode("utf-8-sig", errors="replace")
    )
    blocks = []
    for tags, moves in games(text):
        white, black = known(tags.get("White")) or "?", known(tags.get("Black")) or "?"
        head = [f"game: {white} vs {black}"] + [
            x
            for x in (
                known(tags.get("Date", "").replace(".", "-"))
                if known(tags.get("Date"))
                else "",
                known(tags.get("Event")),
                known(tags.get("Site")),
            )
            if x
        ]
        lines = [", ".join(head)]
        opening = ", ".join(
            x for x in (known(tags.get("Opening")), known(tags.get("ECO"))) if x
        )
        result = known(tags.get("Result"))
        if result or opening:
            lines.append(
                "result: "
                + (result or "unknown")
                + (f" ({opening})" if opening else "")
            )
        if known(tags.get("Annotator")):
            lines.append(f"annotator: {known(tags['Annotator'])}")
        lines += notes(moves)
        blocks.append("\n".join(lines))
    return (
        "\n\n".join(blocks) + "\n"
        if blocks and any(b.count("\n") or "?" not in b for b in blocks)
        else None
    )


EXTS = (".pgn",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: pgn.py mirror --from FOLDER --to MIRROR"


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
