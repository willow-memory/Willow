"""Mirror the fetched pile into text the kernel searches: python mirror.py --from PILE --to MIRROR

Offline. Each reader writes its own part of MIRROR, never touching PILE:
csv-rows (CSV, one passage a row), json-paths (JSON, a passage a record),
web-pages (the Fed's and the nowcasters' HTML), pdf (press conference
transcripts, a passage a page; needs pypdf) and text (the Nasdaq listings).
A mirrored file over the kernel's 1 MB is then cut into parts by the text
add-on, at blank lines, so nothing the readers wrote is left out.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READERS = [
    ("csv", "adapters/stdlib/csv-rows/csv_rows.py"),
    ("json", "adapters/stdlib/json-paths/json_paths.py"),
    ("web", "adapters/stdlib/web-pages/web_pages.py"),
    ("pdf", "adapters/deps/pdf/pdf.py"),
    ("text", "adapters/stdlib/text/text.py"),
]
MAX_FILE = 1_000_000  # the kernel's own limit on one file


def run(script: str, src: Path, dst: Path) -> int:
    got = subprocess.run([sys.executable, str(ROOT / script), "mirror",
                          "--from", str(src), "--to", str(dst)])  # fmt: skip
    return got.returncode


def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[0] != "--from" or argv[2] != "--to":
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    pile, mirror = Path(argv[1]).resolve(), Path(argv[3]).resolve()
    worst = 0
    for part, script in READERS:
        worst = max(worst, run(script, pile, mirror / part))
    with tempfile.TemporaryDirectory() as tmp:
        big = Path(tmp)
        for f in sorted(mirror.rglob("*")):
            if f.is_file() and f.stat().st_size > MAX_FILE:
                dest = big / f.relative_to(mirror)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), dest)
        if any(big.rglob("*.*")):
            worst = max(
                worst, run("adapters/stdlib/text/text.py", big, mirror / "parts")
            )
    print(f"{sum(1 for f in mirror.rglob('*') if f.is_file())} files in {mirror}")
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
