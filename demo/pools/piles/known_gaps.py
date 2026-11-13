"""known_gaps.py: the pools study's pile of known reader gaps, made from public
sources fetched by URL and held to their SHA-256, so nothing of theirs is
kept in the repository.

    python demo/pools/piles/known_gaps.py make --to PILE [--from DIR]
    python demo/pools/piles/known_gaps.py read --pile PILE --work WORK --to READ

`--from DIR` reads the three sources from DIR (by the names below) instead of
fetching them; either way each is held to its SHA-256 first, and a source
that doesn't match is refused. It writes PILE/:

    hurdat2.txt                  NOAA's HURDAT2, as it is (keyed once: a
                                 storm's name only on its header line)
    spa.tsv                      lines 70,001 to 75,000 of Tatoeba's English-Spanish
                                 pairs (manythings.org's spa.txt), as they are:
                                 nine of them hold a ", which csv-rows reads as a
                                 quote and skips the file for
    spa-clean.tsv                the same lines, their " taken out: the control

The pairs are cut to 5,000 lines because csv-rows writes a file's mirror as
one file, and the whole of spa.txt's (23 MB) is past the kernel's 1,000,000
bytes, so even the control would never be read: the dry run found that, and
it is a gap of its own, said in the README, not one these probes ask about.
    freedict-spa-eng-part-NN.html  FreeDict's Spanish-English TEI, cut at entry
                                 ends into parts under 1,000,000 bytes and named
                                 .html, so the kernel reads them with tags
                                 stripped: a headword and its gloss on lines of
                                 their own

The gaps came from willow-f9's proof runs, checked again on 2026-11-13: two
it first reported were not gaps (an array-of-arrays JSON was an HTML error
page; Spanish needing words-es was one pair, not a rule) and are not here.

`read` gathers what the probes are asked of, from a trace of the pile
(trace.py pile --work WORK): READ/pile, the pile as it is, for the kernel's
own probes, and READ/<reader>, each reader's mirror as the trace left it
(WORK/steps/<reader>/tmp/mirror), copied. Each probe names its folder.

Sources and their licences: HURDAT2 is a US government work (public domain);
the Tatoeba pairs are CC BY 2.0 France (tatoeba.org, each line names its
sentences' authors); FreeDict spa-eng is under the GNU GPL. None is copied
into the repository; a pile made from them is the maker's.

Exit codes: 0 made; 2 refused (a bad command line, PILE not empty, a source
missing or not its SHA-256).
"""

from __future__ import annotations

import hashlib
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

SOURCES = {
    "hurdat2.txt": (
        "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt",
        "75202780ce56c8458f16fbef5fb8a026b99b00878dbb95c458211b3e6ef125b4",
    ),
    "spa-eng.zip": (
        "http://www.manythings.org/anki/spa-eng.zip",
        "07bb8aaaf1458abbcdc8a3a51ce5b9f8a2643c829dcb7c2a63b3fec8dde934dc",
    ),
    "spa-eng.tei": (
        "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/spa-eng/spa-eng.tei",
        "d1a48cd5b1fb5111d36243a9ee4a226d2e29b70f0f8a8262b9f334b2b8f6c47c",
    ),
}
PART = 1_000_000
PAIRS = (70_001, 75_000)  # the lines of spa.txt kept, first and last


def get(name: str, src: Path | None) -> bytes:
    url, want = SOURCES[name]
    if src is not None:
        data = (src / name).read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "willow-pools-study"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise ValueError(f"{name}: SHA-256 {got[:12]}, not {want}")
    return data


def parts(tei: str) -> list[str]:
    """The TEI cut at entry ends, each part under PART bytes: an entry (or
    the text between two) goes whole into the part it starts in, unless it
    would take that part to PART, when a new part starts with it."""
    blocks, cur = [], []
    for line in tei.splitlines(keepends=True):
        cur.append(line)
        if line.strip() == "</entry>":
            blocks.append("".join(cur))
            cur = []
    if cur:
        blocks.append("".join(cur))
    out, part, size = [], [], 0
    for b in blocks:
        n = len(b.encode())
        if part and size + n >= PART:
            out.append("".join(part))
            part, size = [], 0
        part.append(b)
        size += n
    if part:
        out.append("".join(part))
    return out


def make(to: Path, src: Path | None) -> int:
    if to.exists() and any(to.iterdir()):
        print(f"refused: {to} isn't empty", file=sys.stderr)
        return 2
    try:
        hurdat = get("hurdat2.txt", src)
        spa = zipfile.ZipFile(io.BytesIO(get("spa-eng.zip", src))).read("spa.txt")
        tei = get("spa-eng.tei", src).decode("utf-8")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    to.mkdir(parents=True, exist_ok=True)
    (to / "hurdat2.txt").write_bytes(hurdat)
    kept = b"".join(spa.splitlines(keepends=True)[PAIRS[0] - 1 : PAIRS[1]])
    (to / "spa.tsv").write_bytes(kept)
    (to / "spa-clean.tsv").write_bytes(kept.replace(b'"', b""))
    cut = parts(tei)
    for i, text in enumerate(cut, 1):
        (to / f"freedict-spa-eng-part-{i:02d}.html").write_text(text, encoding="utf-8")
    print(
        f"made {to}: hurdat2.txt, spa.tsv, spa-clean.tsv, {len(cut)} dictionary parts"
    )
    return 0


READERS = ("csv-rows", "hurdat2")


def read(pile: Path, work: Path, to: Path) -> int:
    if to.exists():
        print(f"refused: {to} is there already", file=sys.stderr)
        return 2
    mirrors = {r: work / "steps" / r / "tmp" / "mirror" for r in READERS}
    gone = [r for r, m in mirrors.items() if not m.is_dir()]
    if not pile.is_dir() or gone:
        print(f"refused: no pile, or no mirror from {', '.join(gone)}", file=sys.stderr)
        return 2
    shutil.copytree(pile, to / "pile")
    for r, m in mirrors.items():
        shutil.copytree(m, to / r)
    print(f"read {to}: pile, {', '.join(READERS)}")
    return 0


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2]))
    want = {
        "make": ({"--to"}, {"--from"}),
        "read": ({"--pile", "--work", "--to"}, set()),
    }
    need, may = want.get(argv[0] if argv else "", (None, set()))
    if need is None or len(argv) % 2 == 0 or not need <= set(opts) <= need | may:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    if argv[0] == "read":
        return read(Path(opts["--pile"]), Path(opts["--work"]), Path(opts["--to"]))
    return make(Path(opts["--to"]), Path(opts["--from"]) if "--from" in opts else None)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
