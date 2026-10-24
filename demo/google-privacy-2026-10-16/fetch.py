"""Fetch the study's sources into a pile, once, and check them offline.

    python demo/google-privacy-2026-10-16/fetch.py --to PILE           # online, once
    python demo/google-privacy-2026-10-16/fetch.py --to PILE --check   # offline

Every source is saved by the snapshot add-on, as it came, into a folder of
its own under PILE, with its address, the time and its SHA-256 in that
folder's .snapshots.jsonl. The before copy is then looked for on the Wayback
Machine (the wayback add-on), captured between the two versions' dates.

`--check` goes nowhere. It hashes every file in PILE against
[sources.json](sources.json), the frozen record of what was fetched, and
says `holds`, `DIFFERS` or `missing` for each. After the fetch, nothing in
the study goes online: every answer comes from these files.

The pages are Google's and the reporters', not this repo's, so the repo
keeps their hashes, never their text.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SNAPSHOT = ROOT / "adapters" / "stdlib" / "snapshot" / "snapshot.py"
WAYBACK = ROOT / "adapters" / "stdlib" / "wayback" / "wayback.py"
GSTATIC = "https://www.gstatic.com/policies/privacy/pdf"

#: (folder, file name, address)
SOURCES = [
    ("policy-old", "google_privacy_policy_en.pdf",
     f"{GSTATIC}/20261001/f86f5p0s/google_privacy_policy_en.pdf"),
    ("policy-new", "google_privacy_policy_en.pdf",
     f"{GSTATIC}/20261016/k8m9x4w2/google_privacy_policy_en.pdf"),
    ("google-pages", "archive.html", "https://policies.google.com/privacy/archive?hl=en-US"),
    ("google-pages", "archive-20261001.html",
     "https://policies.google.com/privacy/archive/20261001?hl=en-US"),
    ("google-pages", "privacy-current.html", "https://policies.google.com/privacy?hl=en-US"),
    ("news", "tech-insider.html",
     "https://tech-insider.org/google-privacy-policy-gmail-ads-opt-in-2026/"),
    ("news", "dexerto.html",
     "https://www.dexerto.com/entertainment/google-quietly-changes-privacy-policy-so-your-"
     "gmail-and-photos-could-be-used-in-targeted-ads-3421462/"),
    ("news", "shattered.html",
     "https://shattered.io/google-privacy-policy-gmail-ads-opt-in-oct-16-2026/"),
]  # fmt: skip


def fetch(pile: Path) -> int:
    worst = 0
    for folder, name, url in SOURCES:
        got = subprocess.run([sys.executable, str(SNAPSHOT), "fetch", "--url", url,
                              "--to", str(pile / folder), "--name", name])  # fmt: skip
        worst = max(worst, got.returncode)
    old = pile / "policy-old" / SOURCES[0][1]
    got = subprocess.run([sys.executable, str(WAYBACK), "find", "--url", SOURCES[0][2],
                          "--to", str(pile / "wayback"), "--after", "20261001",
                          "--before", "20261016", "--against", str(old),
                          "--name", "policy-old.pdf"])  # fmt: skip
    print(f"wayback exit {got.returncode}")
    return worst


def check(pile: Path) -> int:
    pins = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]
    missing = differs = False
    for s in pins:
        p = pile / s["folder"] / s["file"]
        if not p.is_file():
            state, missing = "missing", True
        elif hashlib.sha256(p.read_bytes()).hexdigest() == s["sha256"]:
            state = "holds"
        else:
            state, differs = "DIFFERS", True
        print(f"{state:<8} {s['folder']}/{s['file']}")
    return 2 if differs else 42 if missing else 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--to":
        return fetch(Path(argv[1]))
    if len(argv) == 3 and argv[0] == "--to" and argv[2] == "--check":
        return check(Path(argv[1]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
