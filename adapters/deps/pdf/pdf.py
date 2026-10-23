"""pdf.py: text out of PDFs, into a mirror folder the kernel can search.

    python adapters/deps/pdf/pdf.py mirror --from FOLDER --to MIRROR

Needs pypdf (BSD-3-Clause), pinned in requirements.txt beside this file:

    pip install -r adapters/deps/pdf/requirements.txt

For each .pdf under FOLDER it writes `MIRROR/<same relative path>.txt`, one
paragraph per page, each headed `== page N`, so the kernel's answer says which
page a passage came from. The person then points the kernel at MIRROR.

The contract every file reader shares: FOLDER is walked in sorted order,
skipping hidden files and folders; nothing is written inside FOLDER and no
original is changed; MIRROR inside FOLDER, or FOLDER inside MIRROR, is
refused; the same PDF always gives the same bytes; a file that can't be read
(corrupt, or encrypted with a password) is skipped and counted, never a crash.

What it can't do, said rather than hidden: a scanned page is a picture of
text, and has none to extract (the planned `ocr` add-on is for that). Columns
and tables come out in the order pypdf reads them, which isn't always the
order a person reads them.

If pypdf isn't installed it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 wrote at least one file; 42 nothing
readable; 2 refused.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/pdf/requirements.txt"


def pages(path: Path) -> list[str]:
    """Each page's text, or raises: corrupt, or encrypted with a password."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("encrypted")
    return [(page.extract_text() or "").strip() for page in reader.pages]


def as_text(texts: list[str]) -> str:
    out = []
    for n, text in enumerate(texts, 1):
        lines = [ln.rstrip() for ln in text.splitlines()]
        body = "\n".join(ln for ln in lines if ln.strip())  # a page is one passage
        out.append(f"== page {n}\n{body}" if body else f"== page {n}")
    return "\n\n".join(out) + "\n"


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def mirror(src: Path, dst: Path) -> int:
    try:
        import pypdf  # noqa: F401
    except ImportError:
        print(f"refused: pdf needs pypdf: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
        print(
            "refused: the mirror and the folder can't be inside each other",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = as_text(pages(p))
        except Exception:  # pypdf raises many kinds for a damaged file
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        wrote += 1
    print(f"wrote {wrote} files to {dst}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    raise SystemExit(main(sys.argv[1:]))
