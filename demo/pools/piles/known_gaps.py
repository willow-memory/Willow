"""known_gaps.py: the pools study's pile of known reader gaps, made from public
sources fetched by URL and held to their SHA-256, so nothing of theirs is
kept in the repository.

    python demo/pools/piles/known_gaps.py make --to PILE [--from DIR]

`--from DIR` reads the three sources from DIR (by the names below) instead of
fetching them; either way each is held to its SHA-256 first, and a source
that doesn't match is refused. It writes PILE/:

    hurdat2.txt                  NOAA's HURDAT2, as it is (keyed once: a
                                 storm's name only on its header line)
    spa.tsv                      Tatoeba's English-Spanish pairs (manythings.org's
                                 spa.txt), as they are: 370 lines hold a ", which
                                 csv-rows reads as a quote and skips the file for
    spa-clean.tsv                the same, its " taken out: the control
    freedict-spa-eng-part-NN.html  FreeDict's Spanish-English TEI, cut at entry
                                 ends into parts under 1,000,000 bytes and named
                                 .html, so the kernel reads them with tags
                                 stripped: a headword and its gloss on lines of
                                 their own

The gaps came from willow-f9's proof runs, checked again on 2026-11-13: two
it first reported were not gaps (an array-of-arrays JSON was an HTML error
page; Spanish needing words-es was one pair, not a rule) and are not here.

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
import sys
import urllib.request
import zipfile
from pathlib import Path

SOURCES = {
    "hurdat2.txt": (
        "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt",
        "75202780ce56",
    ),
    "spa-eng.zip": ("http://www.manythings.org/anki/spa-eng.zip", "07bb8aaaf145"),
    "spa-eng.tei": (
        "https://raw.githubusercontent.com/freedict/fd-dictionaries/master/spa-eng/spa-eng.tei",
        "d1a48cd5b1fb",
    ),
}
PART = 1_000_000


def get(name: str, src: Path | None) -> bytes:
    url, want = SOURCES[name]
    if src is not None:
        data = (src / name).read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "willow-pools-study"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if not got.startswith(want):
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
    (to / "spa.tsv").write_bytes(spa)
    (to / "spa-clean.tsv").write_bytes(spa.replace(b'"', b""))
    cut = parts(tei)
    for i, text in enumerate(cut, 1):
        (to / f"freedict-spa-eng-part-{i:02d}.html").write_text(text, encoding="utf-8")
    print(
        f"made {to}: hurdat2.txt, spa.tsv, spa-clean.tsv, {len(cut)} dictionary parts"
    )
    return 0


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2]))
    if argv[:1] != ["make"] or len(argv) % 2 == 0 or set(opts) - {"--to", "--from"} or "--to" not in opts:  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    return make(Path(opts["--to"]), Path(opts["--from"]) if "--from" in opts else None)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
