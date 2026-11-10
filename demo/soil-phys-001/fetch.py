"""fetch.py: the study's sources, fetched again and held to their hashes.

    python demo/soil-phys-001/fetch.py --to DIR           # online
    python demo/soil-phys-001/fetch.py --to DIR --check   # offline

Fetches each source in sources.json that a script may fetch into DIR, by its
address, and says whether its bytes are the frozen ones. A source that was
downloaded in a browser (a publisher that refuses scripts) is not fetched:
it says from where, and DIR must get it by hand. `--check` fetches nothing
and holds what DIR has to the hashes. Exit 0 every file the frozen one; 42
some missing or different; 2 a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]
USAGE = "usage: fetch.py --to DIR [--check]"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "willow-study-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main(argv: list[str]) -> int:
    check = "--check" in argv
    rest = [a for a in argv if a != "--check"]
    if len(rest) != 2 or rest[0] != "--to":
        print(USAGE, file=sys.stderr)
        return 2
    to = Path(rest[1])
    to.mkdir(parents=True, exist_ok=True)
    ok = True
    for s in SOURCES:
        p = to / s["file"]
        by_hand = s["how"].startswith("downloaded in a browser")
        if not check and not by_hand and not p.exists():
            try:
                p.write_bytes(get(s["url"]))
            except OSError as e:
                print(f"no answer  {s['file']}: {e}")
        if not p.exists():
            ok = False
            print(
                f"missing    {s['file']}"
                + (f"  (by hand, from {s['url']})" if by_hand else "")
            )
            continue
        same = hashlib.sha256(p.read_bytes()).hexdigest() == s["sha256"]
        ok &= same
        print(f"{'same' if same else 'DIFFERENT':<10} {s['file']}")
    return 0 if ok else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
