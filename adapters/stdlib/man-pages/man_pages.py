r"""man_pages.py: Man pages as plain text. Python 3.9+.

    python adapters/stdlib/man-pages/man_pages.py mirror --from FOLDER --to MIRROR

Walks FOLDER for man pages: files named like `ls.1`, `printf.3` or `intro.7`,
with a section number from 1 to 8, and the same gzipped (`ls.1.gz`, as
`/usr/share/man` keeps them), hidden folders and files skipped. Point it at
your system's man directory to ask your own machine's documentation. Each page
is written as the text a reader sees:

    ls(1)

    NAME
    ls - list directory contents

    SYNOPSIS
    ls [OPTION]... [FILE]...

    DESCRIPTION
    List information about the FILEs (the current directory by default).

The `.TH` line gives the title, section headings are kept on their own line,
and the font changes, hyphen and dash escapes, quotes and the usual macros (.B,
.I, .BR, .TP, .IP, .PP, .RS, .nf) are read as the words they hold; comments,
macro definitions and the other roff requests are dropped. A gzipped page is
read to 10 MB; a page with no text is skipped and counted. A page that is a
plain `.so` redirect to another is skipped.

Each file is written to MIRROR at the same relative path with `.txt` added
(`ls.1.gz.txt`). FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import gzip
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 10 * 1024 * 1024
ESCAPES = [
    (re.compile(r"\\f(?:\([A-Za-z0-9]{2}|\[[^\]]*\]|[A-Za-z0-9])"), ""),
    (re.compile(r"\\\*\((?:lq|Lq)"), "\u201c"), (re.compile(r"\\\*\((?:rq|Rq)"), "\u201d"),
    (re.compile(r"\\\((?:em)"), "\u2014"), (re.compile(r"\\\((?:en)"), "\u2013"),
    (re.compile(r"\\\((?:aq|cq)"), "'"), (re.compile(r"\\\((?:lq|oq)"), "\u201c"), (re.compile(r"\\\((?:rq)"), "\u201d"),
    (re.compile(r"\\\(co"), "\u00a9"), (re.compile(r"\\\(bu"), "\u2022"), (re.compile(r"\\\(hy"), "-"),
    (re.compile(r"\\[&|^c%]"), ""), (re.compile(r"\\[- ]"), lambda m: "-" if m.group(0) == "\\-" else " "),
    (re.compile(r"\\e"), lambda m: "\\"), (re.compile(r"\\\\"), lambda m: "\\"),
]  # fmt: skip
FONT_MACROS = {"B", "I", "SM", "SB", "BR", "BI", "IB", "IR", "RB", "RI"}


def words(line: str) -> list[str]:
    """The arguments of a request, quotes honoured."""
    return [a for a in re.findall(r'"((?:[^"]|"")*)"|(\S+)', line) for a in [a[0].replace('""', '"') if a[0] else a[1]]]


def plain(text: str) -> str:
    for rx, repl in ESCAPES:
        text = rx.sub(repl, text)
    return text


def convert(data: bytes) -> str | None:
    if data[:2] == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as g:
            data = g.read(BIGGEST + 1)
        if len(data) > BIGGEST:
            return None
    lines = data.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    state = {"title": "", "skip": False, "nofill": False, "tag": False}

    def flush() -> None:
        if para:
            out.append(" ".join(para))
            para.clear()

    def add(text: str) -> None:
        text = " ".join(text.split())
        if not text:
            return
        if state["nofill"] or state["tag"]:
            flush()
            out.append(text)
            state["tag"] = False
        else:
            para.append(text)

    for raw in lines:
        if state["skip"]:
            state["skip"] = raw.strip() != ".."
            continue
        if raw.startswith(('.\\"', "'\\\"", '\\"')) or raw.strip() in (".", "'"):
            continue
        if not raw.startswith((".", "'")):
            add(plain(raw))
            continue
        parts = raw[1:].strip().split(None, 1)
        if not parts:
            continue
        req, rest = parts[0], parts[1] if len(parts) > 1 else ""
        args = words(rest)
        if req in ("de", "de1"):
            state["skip"] = True
        elif req == "TH" and args:
            state["title"] = f"{plain(args[0])}({plain(args[1])})" if len(args) > 1 else plain(args[0])
        elif req in ("SH", "SS", "Sh", "Ss"):
            flush()
            out += ["", " ".join(plain(" ".join(args)).split())]
        elif req in ("PP", "P", "LP", "HP", "Pp", "TQ"):
            flush()
            out.append("")
        elif req == "TP":
            flush()
            out.append("")
            state["tag"] = True
        elif req == "IP":
            flush()
            out.append("")
            if args:
                out.append(" ".join(plain(args[0]).split()))
        elif req in FONT_MACROS and args:
            joined = "".join(plain(a) for a in args) if req in ("BR", "BI", "IB", "IR", "RB", "RI") else " ".join(plain(a) for a in args)
            add(joined)
        elif req in ("br",):
            flush()
        elif req == "sp":
            flush()
            out.append("")
        elif req in ("nf", "EX"):
            flush()
            state["nofill"] = True
        elif req in ("fi", "EE"):
            flush()
            state["nofill"] = False
    flush()
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    if not body:
        return None
    return (state["title"] + "\n\n" if state["title"] else "") + body + "\n"

EXTS = ('.1', '.2', '.3', '.4', '.5', '.6', '.7', '.8', '.1.gz', '.2.gz', '.3.gz', '.4.gz', '.5.gz', '.6.gz', '.7.gz', '.8.gz')
ERRORS = (OSError, UnicodeDecodeError, ValueError, EOFError)

USAGE = "usage: man_pages.py mirror --from FOLDER --to MIRROR"


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
        print("refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr)
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
