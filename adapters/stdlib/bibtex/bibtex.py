r"""bibtex.py: .bib files: each reference as a passage, with its key. Python 3.9+.

    python adapters/stdlib/bibtex/bibtex.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .bib files (hidden folders and files skipped) and writes each
reference as a paragraph that begins with its citation key, so a question about
a paper finds the key to cite:

    smith2020 (article): Tides of the Estuary, 2020
    by Ada Example; Cy Sample
    in Journal of Made-Up Studies, 12(3), pages 45-67
    doi: 10.1000/xyz123
    keywords: tides, estuaries
    abstract: We measure the tide at six harbours.

Braces and quotes around a value are taken off, `#` joins pieces, an `@string`
macro is filled in, and the common LaTeX accents ({\"u}, \'e, \ss, \&, ~) are
read as the letters they make. `@comment` and `@preamble` are skipped. A
field's name is kept only for the ones above; the rest are dropped.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no reference, or that cannot be read, is
skipped and counted:

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

ACCENTS = {
    '"': "\u0308",
    "'": "\u0301",
    "`": "\u0300",
    "^": "\u0302",
    "~": "\u0303",
    "=": "\u0304",
    ".": "\u0307",
    "c": "\u0327",
    "v": "\u030c",
}
LETTERS = {
    "ss": "ß",
    "o": "ø",
    "O": "Ø",
    "ae": "æ",
    "AE": "Æ",
    "aa": "å",
    "AA": "Å",
    "l": "ł",
    "L": "Ł",
    "i": "ı",
}
SHOWN = (("title", None), ("author", None), ("editor", None), ("journal", None), ("booktitle", None), ("publisher", None),
         ("volume", None), ("number", None), ("pages", None), ("doi", None), ("url", None), ("keywords", None), ("abstract", None), ("note", None))  # fmt: skip
ENTRY = re.compile(r"@\s*([A-Za-z]+)\s*([{(])")
NAME = re.compile(r"[^\s=,{}()\"#]+")


class Unreadable(ValueError):
    pass


def unlatex(text: str) -> str:
    """A value's LaTeX accents and braces read as plain text."""
    text = re.sub(
        r"\\([\"'`^~=.])\s*\{?\\?([A-Za-z])\}?",
        lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]),
        text,
    )
    text = re.sub(
        r"\\([cv])(?:\s*\{([A-Za-z])\}|\s+([A-Za-z])(?![A-Za-z]))",
        lambda m: unicodedata.normalize(
            "NFC", (m.group(2) or m.group(3)) + ACCENTS[m.group(1)]
        ),
        text,
    )
    text = re.sub(
        r"\\(ss|ae|AE|aa|AA|o|O|l|L|i)(?![A-Za-z])\s*",
        lambda m: LETTERS[m.group(1)],
        text,
    )
    text = (
        text.replace("\\&", "&")
        .replace("\\%", "%")
        .replace("\\_", "_")
        .replace("\\$", "$")
        .replace("~", " ")
    )
    for logo in ("BibTeX", "LaTeX", "TeX"):
        text = text.replace("\\" + logo, logo)
    text = re.sub(r"\\[A-Za-z]+\*?\s*", "", text)
    return " ".join(text.replace("{", "").replace("}", "").split())


def balanced(text: str, i: int, open_: str, close: str) -> int:
    """Index of the close matching the open at text[i]."""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "\\":
            continue
        if text[j] == open_:
            depth += 1
        elif text[j] == close and text[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return j
    raise Unreadable("a brace is never closed")


def value(text: str, i: int, macros: dict[str, str]) -> tuple[str, int]:
    """One field value starting at i (pieces joined by #): (its text, where it ends)."""
    out = []
    while True:
        while text[i : i + 1].isspace():
            i += 1
        c = text[i : i + 1]
        if c == "{":
            j = balanced(text, i, "{", "}")
            out.append(text[i + 1 : j])
            i = j + 1
        elif c == '"':
            j = i + 1
            depth = 0
            while j < len(text) and (text[j] != '"' or depth):
                depth += (text[j] == "{") - (text[j] == "}")
                j += 2 if text[j] == "\\" else 1
            if j >= len(text):
                raise Unreadable("a quote is never closed")
            out.append(text[i + 1 : j])
            i = j + 1
        else:
            m = NAME.match(text, i)
            if not m:
                raise Unreadable("a value is missing")
            word = m.group(0)
            out.append(macros.get(word.lower(), word))
            i = m.end()
        while text[i : i + 1].isspace():
            i += 1
        if text[i : i + 1] != "#":
            return "".join(out), i
        i += 1


def entries(text: str) -> list[tuple[str, str, dict[str, str]]]:
    """[(type, key, fields)] for each reference, with @string macros filled in."""
    macros = {"jan": "January", "feb": "February", "mar": "March", "apr": "April", "may": "May", "jun": "June",
              "jul": "July", "aug": "August", "sep": "September", "oct": "October", "nov": "November", "dec": "December"}  # fmt: skip
    out, pos = [], 0
    while m := ENTRY.search(text, pos):
        kind, open_ = m.group(1).lower(), m.group(2)
        close = "}" if open_ == "{" else ")"
        end = balanced(text, m.end() - 1, open_, close)
        body = text[m.end() : end]
        pos = end + 1
        if kind in ("comment", "preamble"):
            continue
        if kind == "string":
            k, _, rest = body.partition("=")
            macros[k.strip().lower()], _ = value(rest, 0, macros)
            continue
        key, comma, rest = body.partition(",")
        if not comma:
            continue
        fields, i = {}, 0
        while True:
            while i < len(rest) and (rest[i].isspace() or rest[i] == ","):
                i += 1
            if i >= len(rest):
                break
            m2 = NAME.match(rest, i)
            if not m2:
                raise Unreadable("a field has no name")
            name = m2.group(0).lower()
            i = m2.end()
            while rest[i : i + 1].isspace():
                i += 1
            if rest[i : i + 1] != "=":
                raise Unreadable(f"field {name!r} has no =")
            val, i = value(rest, i + 1, macros)
            fields[name] = unlatex(val)
        out.append((kind, key.strip(), fields))
    return out


def passage(kind: str, key: str, f: dict[str, str]) -> str:
    year = f.get("year") or f.get("date", "")[:4]
    head = f"{key} ({kind}): {f.get('title', '(untitled)')}" + (
        f", {year}" if year else ""
    )
    lines = [head]
    if f.get("author"):
        lines.append(
            "by " + "; ".join(a.strip() for a in re.split(r"\s+and\s+", f["author"]))
        )
    if f.get("editor"):
        lines.append(
            "edited by "
            + "; ".join(a.strip() for a in re.split(r"\s+and\s+", f["editor"]))
        )
    where = ", ".join(
        x for x in (f.get("journal") or f.get("booktitle"), f.get("publisher")) if x
    )
    vol = f.get("volume", "") + (f"({f['number']})" if f.get("number") else "")
    if where or vol or f.get("pages"):
        lines.append(
            "in "
            + ", ".join(
                x
                for x in (where, vol, f"pages {f['pages']}" if f.get("pages") else "")
                if x
            )
        )
    for name in ("doi", "url", "keywords", "abstract", "note"):
        if f.get(name):
            lines.append(f"{name}: {f[name]}")
    return "\n".join(lines)


def convert(data: bytes) -> str | None:
    found = entries(data.decode("utf-8-sig"))
    return "".join(passage(*e) + "\n\n" for e in found) if found else None


EXTS = (".bib",)
ERRORS = (OSError, UnicodeDecodeError, Unreadable, ValueError, IndexError)

USAGE = "usage: bibtex.py mirror --from FOLDER --to MIRROR"


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
