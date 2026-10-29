r"""rtf.py: RTF documents as plain text. Python 3.9+.

    python adapters/stdlib/rtf/rtf.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .rtf files (hidden folders and files skipped) and writes each
as the plain text it displays: paragraphs and line breaks kept, the font,
colour and style tables dropped, formatting words dropped, `\'e9` and `\u233?`
read as the letters they are, a field's shown result kept and its instruction
dropped, and pictures, headers, footers and anything marked ignorable left out.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file that is not RTF is skipped and counted.

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

SKIP = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "header", "footer", "headerl", "headerr", "headerf",
        "footerl", "footerr", "footerf", "footnote", "themedata", "colorschememapping", "latentstyles", "listtable",
        "listoverridetable", "rsidtbl", "generator", "datastore", "xmlnstbl", "fldinst", "revtbl", "mmathPr", "wgrffmtfilter",
        "pgdsctbl", "private", "txfieldstart", "shpinst", "nonshppict"}  # fmt: skip
SYMBOLS = {"par": "\n\n", "line": "\n", "tab": "\t", "emdash": "—", "endash": "–", "bullet": "•", "lquote": "‘", "rquote": "’",
           "ldblquote": "“", "rdblquote": "”", "emspace": " ", "enspace": " ", "qmspace": " ", "page": "\n\n", "sect": "\n\n"}  # fmt: skip
CONTROL = re.compile(
    r"\\([A-Za-z]+)(-?\d+)? ?|\\'([0-9A-Fa-f]{2})|\\(.)|([{}])|([^\\{}]+)", re.S
)


def convert(data: bytes) -> str | None:
    text = data.decode("latin-1")
    if not text.lstrip().startswith("{\\rtf"):
        return None
    out: list[str] = []
    stack: list[bool] = []  # per open group: is its text dropped
    drop = False
    skip_chars = 0  # characters to drop after a \uN
    uc = 1
    pending = bytearray()

    def flush() -> None:
        if pending:
            out.append(pending.decode("cp1252", errors="replace"))
            pending.clear()

    for m in CONTROL.finditer(text):
        word, num, hexa, sym, brace, plain = m.groups()
        if hexa is not None:
            if skip_chars:
                skip_chars -= 1
            elif not drop:
                pending.append(int(hexa, 16))
            continue
        flush()
        if brace == "{":
            stack.append(drop)
        elif brace == "}":
            drop = stack.pop() if stack else drop
        elif plain is not None:
            if skip_chars:
                cut = min(skip_chars, len(plain))
                plain, skip_chars = plain[cut:], skip_chars - cut
            if not drop:
                out.append(plain.replace("\r", "").replace("\n", ""))
        elif sym is not None:
            if sym == "*":
                drop = True
            elif sym in "\\{}":
                if skip_chars:
                    skip_chars -= 1
                elif not drop:
                    out.append(sym)
            elif sym == "~" and not drop:
                out.append(" ")
            elif sym == "_" and not drop:
                out.append("-")
        elif word is not None:
            if word in SKIP:
                drop = True
            elif word == "uc":
                uc = int(num or 1)
            elif word == "u" and num is not None and not drop:
                n = int(num)
                out.append(chr(n + 65536 if n < 0 else n))
                skip_chars = uc
            elif word in SYMBOLS and not drop:
                out.append(SYMBOLS[word])
    flush()
    body = (
        "".join(out).encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")
    )
    body = "\n".join(line.rstrip() for line in body.split("\n"))
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    body = body.strip()
    return body + "\n" if body else None


EXTS = (".rtf",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, IndexError)

USAGE = "usage: rtf.py mirror --from FOLDER --to MIRROR"


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
