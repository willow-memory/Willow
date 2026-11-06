#!/usr/bin/env python3
"""fetch.py: the papers in Corwin's catalogue, fetched again and held to their hashes.

    python3 fetch.py                 # fetch into life/sources/
    python3 fetch.py --to DIR        # fetch into DIR instead
    python3 fetch.py --check [--to DIR]   # fetch nothing; hash what is already there

Each source is fetched from its pinned address and saved under the file name
Corwin gave it (the `file` column of life/sources/catalogue.csv, without the
`sources/` folder). Its bytes are held to the SHA-256 below; a file whose bytes
differ is refused and removed, never kept. Each source is reported as one of:

    held          the bytes are the ones pinned
    changed       the bytes differ from the pin: refused
    unreachable   it couldn't be fetched (or, with --check, isn't there)

All are public domain or open by their holder; none is committed to the repo.
make_life.py never calls this. Standard library only.

Exit codes: 0 every source held; 42 some not held; 2 a bad command line.
"""

import hashlib
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TO = os.path.join(HERE, "life", "sources")

# catalogue id, url, sha256, the file name in Corwin's sources/ folder
SOURCES = [
    (
        "frege-1884",
        "https://www.gutenberg.org/cache/epub/48312/pg48312.txt",
        "e78d9594fa2fbc5db4fe5141a4748a639d0172a52476b6a34e3fb9d4af823f88",
        "frege_grundlagen_1884.txt",
    ),
    (
        "dedekind-1888",
        "https://archive.org/download/rcin.org.pl.WA35_13030_4797_Was-sind_5138/WA35_13030_4797_Was-sind_djvu.txt",
        "314524f0c0213b0ef0844223de0e9b2d4d9e229aed696643f9254dd0e900fa93",
        "dedekind_was_sind_1888_djvu.txt",
    ),
    (
        "dedekind-1888-english",
        "https://www.gutenberg.org/files/21016/21016-pdf.pdf",
        "d8e8bc66697760a2de36a704d82f70e1ebf526b1b344051929a17d5247cbf6ec",
        "dedekind_essays_beman.pdf",
    ),
    (
        "zermelo-1908",
        "https://zenodo.org/records/1428264/files/article.pdf",
        "34690b7eacb0f29d9bab154243dd47b82efff2e6640ef48a7ec7ce4fa75eeaa1",
        "zermelo_1908_untersuchungen.pdf",
    ),
    (
        "vonneumann-1923",
        "https://acta.bibl.u-szeged.hu/13294/1/math_001_199-208.pdf",
        "e2b9b4fbfdaa1ba7eef1c9c5cca13aff7f1ae8a195122691b501dc1f2a50e6c5",
        "vonneumann_1923_transfinite.pdf",
    ),
    (
        "planck-1900",
        "https://archive.org/download/sim_annalen-der-physik_1900_1_1/sim_annalen-der-physik_1900_1_1_djvu.txt",
        "cee3088ff76198a216ffe9cb469e380d4f8a4b54928a68e33a1ba7a6b61f1017",
        "annalen_1900_bd1_djvu.txt",
    ),
    (
        "planck-1901",
        "https://archive.org/download/sim_annalen-der-physik_1901_4_3/sim_annalen-der-physik_1901_4_3_djvu.txt",
        "91dc821257230ef36f7ee0c5bcfca389aad9ced546e64c276c9664df1dae0795",
        "annalen_1901_bd4_djvu.txt",
    ),
    (
        "planck-1913",
        "https://www.gutenberg.org/files/40030/40030-pdf.pdf",
        "5d99e069a5ff483f8fe9533467759a26e9e091f2d96e3fcb10e4dd398bb8832a",
        "planck_heat_radiation_masius.pdf",
    ),
    (
        "weyl-1922",
        "https://www.gutenberg.org/files/43006/43006-pdf.pdf",
        "755c84c63c29f10fe69d7830e2716f3fe7fe71c4f6cd3a625eeddccd1f207213",
        "weyl_space_time_matter.pdf",
    ),
    (
        "ehrenfest-1917",
        "https://dwc.knaw.nl/DL/publications/PU00012213.pdf",
        "6631c77cdfbe89fc698e654335a3a7ce72b0b25b62e088fb5bf178a9675a071c",
        "ehrenfest_1917_three_dimensions.pdf",
    ),
    (
        # the catalogue's own id; zenodo serves it as article.pdf
        "Z-1424262",
        "https://zenodo.org/records/1424262/files/article.pdf",
        "2d1a44f825a2f16396673215ce3e9b4c5061c461a779827f0158fcdbcf0fd955",
        "article.pdf",
    ),
    (
        "nernst-1912",
        "https://archive.org/download/in.ernet.dli.2015.105015/2015.105015.Der-Koniglich-Preussischen-Akademie-Der-Wissenschaften-januar-Bis-Juni-1912_djvu.txt",
        "780f9fa4c7ebd57f10de5a51aebf435dc25adcaae72f104f976e1833b5cd9300",
        "sitzungsberichte_1912_jan_jun_djvu.txt",
    ),
    (
        "julia-1918",
        "https://www.numdam.org/item/JMPA_1918_8_1__47_0.pdf",
        "45ae89366dc78d6aad9f757f30095e11a56e6babaa7768599201f42ea5b06479",
        "julia_1918_iteration.pdf",
    ),
    (
        # first logged 2026-11-06 for this demo, from one fetch of the url
        "mach-1883",
        "https://archive.org/download/sciencemechanic02machgoog/sciencemechanic02machgoog_djvu.txt",
        "987490ff6a92ab24ce9109dbf1cf6c14380609dd2d1ca4f2e817e5217f29af11",
        "mach_science_of_mechanics_1893_djvu.txt",
    ),
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(to, offline):
    os.makedirs(to, exist_ok=True)
    said = {}
    for sid, url, want, name in SOURCES:
        path = os.path.join(to, name)
        try:
            if offline:
                with open(path, "rb") as fh:
                    raw = fh.read()
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "willow-demo"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    raw = r.read()
        except OSError:
            said[sid] = ("unreachable", name)
            continue
        if sha256(raw) != want:
            said[sid] = ("changed", name)
            if not offline and os.path.exists(path):
                os.remove(path)  # a stale copy must not pass for the pinned one
            continue
        if not offline:
            tmp = path + ".part"
            with open(tmp, "wb") as fh:
                fh.write(raw)
            os.replace(tmp, path)
        said[sid] = ("held", name)
    return said


def main(argv):
    offline = "--check" in argv
    rest = [a for a in argv if a != "--check"]
    to = DEFAULT_TO
    if rest:
        if len(rest) != 2 or rest[0] != "--to":
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return 2
        to = rest[1]
    said = fetch(os.path.abspath(to), offline)
    for sid, (state, name) in said.items():
        print(f"{state:12}{sid:24}{name}")
    return 0 if all(s == "held" for s, _ in said.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
