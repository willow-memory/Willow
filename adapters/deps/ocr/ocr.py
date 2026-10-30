"""ocr.py: text out of photos of letters and scanned PDFs, into a mirror.

    python adapters/deps/ocr/ocr.py mirror --from FOLDER --to MIRROR [--lang LANGS]

Needs Pillow (MIT-CMU) and pypdf (BSD-3-Clause), pinned in requirements.txt
beside this file, and the tesseract program (Apache-2.0), run, never linked:

    pip install -r adapters/deps/ocr/requirements.txt
    sudo apt install tesseract-ocr     # or: brew install tesseract

Each picture is handed to tesseract on its standard input and its text read
from its standard output, so nothing is written for it, not even a scratch
file.

For each picture under FOLDER (.png, .jpg, .jpeg, .tif, .tiff, .bmp, .gif,
.webp) and each PDF with a scanned page, it writes `MIRROR/<same relative
path>.txt`: the text tesseract reads, its paragraphs kept, a TIFF's or a
PDF's pages each headed `== page N`. A PDF page with text of its own is left
to the pdf add-on, which reads it exactly; only a page with none, a picture
of a page, is read here. LANGS is tesseract's (eng unless --lang says;
deu, fra, eng+fra), each one a language pack installed beside tesseract.

The contract every file reader shares: FOLDER is walked in sorted order,
skipping hidden files and folders; nothing is written inside FOLDER and no
original is changed; MIRROR inside FOLDER, or FOLDER inside MIRROR, is
refused; the same file always gives the same bytes from the same tesseract;
a file that can't be read (corrupt, or a picture too big to open safely) is
skipped and counted, never a crash, and so is one with no text in it.

OCR guesses: a word it misreads is in the mirror misread. What it wrote is
the mirror's, never the original's; the kernel cites the mirror's line.

Without Pillow, pypdf or the tesseract program it refuses and
names the install; it never skips quietly. Exit codes, the kernel's: 0
wrote at least one file; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/ocr/requirements.txt"
PROGRAM = "the tesseract program: apt install tesseract-ocr, or brew install tesseract"
PICTURES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp")


def tidy(text: str) -> str:
    """tesseract's text with its form feed gone, lines' ends trimmed and
    runs of blank lines made one: its paragraphs, the kernel's passages."""
    out: list[str] = []
    for line in text.replace("\x0c", "").splitlines():
        line = line.rstrip()
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip("\n")


def tesseract(tess: str, *args: str, given: bytes = b"") -> str:
    """What tesseract prints for `args`, `given` on its standard input:
    pipes only, never a file, never /dev/null."""
    got = subprocess.run([tess, *args], input=given, capture_output=True)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.decode("utf-8", "replace").strip()[:200])
    return got.stdout.decode("utf-8", "replace")


def read(tess: str, image, lang: str) -> str:
    """One picture's text: handed to tesseract as a PNG on its standard input."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, "PNG")
    return tidy(tesseract(tess, "stdin", "stdout", "-l", lang, given=buf.getvalue()))


def picture(tess: str, path: Path, lang: str) -> list[str]:
    """The text of each frame of a picture (a TIFF may hold several pages)."""
    from PIL import Image, ImageSequence

    with Image.open(path) as im:
        frames = [f.copy() for f in ImageSequence.Iterator(im)]
    return [read(tess, f, lang) for f in frames]


def scanned(tess: str, path: Path, lang: str) -> list[tuple[int, str]] | None:
    """[(page number, its text)] for each page of a PDF with no text layer;
    None when every page has text of its own (the pdf add-on's to read)."""
    from PIL import Image
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("encrypted")
    out, any_scan = [], False
    for n, page in enumerate(reader.pages, 1):
        if (page.extract_text() or "").strip():
            continue
        any_scan = True
        texts = [read(tess, Image.open(io.BytesIO(f.data)), lang) for f in page.images]
        out.append((n, "\n\n".join(t for t in texts if t)))
    return out if any_scan else None


def as_text(tess: str, path: Path, lang: str) -> str | None:
    """The mirror file's text; "" when there is none to write, None for a
    PDF whose every page has text of its own (the pdf add-on's to read)."""
    if path.suffix.lower() == ".pdf":
        pages = scanned(tess, path, lang)
        if pages is None:
            return None
    else:
        texts = picture(tess, path, lang)
        if len(texts) == 1:
            return texts[0] + "\n" if texts[0] else ""
        pages = list(enumerate(texts, 1))
    if not any(t for _, t in pages):
        return ""
    return (
        "\n\n".join(f"== page {n}\n{t}" if t else f"== page {n}" for n, t in pages)
        + "\n"
    )


def bomb():
    from PIL import Image

    return Image.DecompressionBombWarning


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def mirror(src: Path, dst: Path, lang: str) -> int:
    try:
        import PIL  # noqa: F401
        import pypdf  # noqa: F401
    except ImportError as exc:
        print(f"refused: ocr needs {exc.name}: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    tess = shutil.which("tesseract")
    try:
        listed = tesseract(tess, "--list-langs") if tess else ""
    except (OSError, RuntimeError):  # a broken install
        listed = ""
    have = {x.strip() for x in listed.splitlines()[1:] if x.strip()}
    if not have:
        print(f"refused: ocr needs {PROGRAM}", file=sys.stderr)
        return kernel.REFUSED
    missing = [x for x in lang.split("+") if x not in have]
    if not lang or missing:
        print(f"refused: tesseract has no language pack for {'+'.join(missing) or 'no language'}; "
              f"it has {', '.join(sorted(have - {'osd'}))}", file=sys.stderr)  # fmt: skip
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
    wrote = blank = typed = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in (*PICTURES, ".pdf"):
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", bomb())  # too big: skipped
                text = as_text(tess, p, lang)
        except Exception:  # a damaged file, or one too big to open safely
            skipped += 1
            continue
        if text is None:
            typed += 1
            continue
        if not text:
            blank += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        wrote += 1
    print(f"wrote {wrote} files to {dst}; {blank} with no text to read; "
          f"{typed} PDFs with text of their own, the pdf add-on's; skipped {skipped}")  # fmt: skip
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    lang = "eng"
    if len(argv) == 7 and argv[5] == "--lang":
        lang, argv = argv[6], argv[:5]
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]), lang)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    raise SystemExit(main(sys.argv[1:]))
