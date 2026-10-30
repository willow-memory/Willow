<!-- willow-addon
section: Reading more kinds of files
line: Text out of photos of letters and scanned PDFs.
source: new
added: 2026-10-30
needs: Pillow and pypdf, and the tesseract program, run not linked; MIT-CMU, BSD-3-Clause, Apache-2.0
floor: Pillow 11.0.0, pypdf 3.1.0; the rule names Pillow 8.0.1, which won't build on Python 3.13, and pypdf 1.9, a Python 2 release; each floor is the first that works
writes: to
network: none
tags: needs-install, offline, writes-output, file-reader
-->
# ocr

The words in a photo of a letter, or a scanned PDF, read by tesseract into
a mirror folder the kernel can search.

    pip install -r adapters/deps/ocr/requirements.txt
    sudo apt install tesseract-ocr          # or: brew install tesseract
    python adapters/deps/ocr/ocr.py mirror --from FOLDER --to MIRROR [--lang LANGS]
    python kernel.py init --box BOX --pile MIRROR --key KEY

Each picture (.png, .jpg, .jpeg, .tif, .tiff, .bmp, .gif, .webp) becomes
`MIRROR/<same path>.txt`, its paragraphs kept; a TIFF of several pages, and
a PDF, have each page headed `== page N`.

**Scanned PDFs only.** A PDF page with text of its own is left to the
[pdf](../pdf/) add-on, which reads it exactly; only a page with none, a
picture of a page, is read here. A PDF whose every page has text is counted
as the pdf add-on's. Bernadette's two demo "Scans" are such PDFs: both are
counted that way, and nothing is guessed for them.

**LANGS** is tesseract's: eng unless `--lang` says, `deu`, `fra`, or
`eng+fra` for a letter in both, each a language pack installed beside
tesseract. One that isn't installed is refused, naming the ones that are.

**OCR guesses.** A word it misreads is misread in the mirror. The kernel
cites the mirror's line, never the original's, so the passage it serves is
what tesseract read. On tesseract's own test scans (`phototest.tif`,
`eurotext.tif`, from github.com/tesseract-ocr/test) it read every word,
the same bytes at the pins and at the floor.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER and no original
changes; MIRROR inside FOLDER, or the other way round, is refused; the same
file gives the same bytes from the same tesseract; a file that can't be
read (corrupt, or a picture too big to open safely) is skipped and counted,
never a crash, and so is one with no text in it.

**Without Pillow, pypdf or tesseract** it refuses and names the
install: exit 2, never a quiet skip.

**Uses:** the kernel's exit codes: 0 wrote at least one file; 42 nothing
readable; 2 refused.

**Never:** writes inside your folder, changes an original, or goes online.
