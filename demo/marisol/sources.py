"""sources.py: the real sources of this demo, fetched again and checked by hash.

    python3 demo/marisol/sources.py fetch DIR    # fetch each source into DIR (online)
    python3 demo/marisol/sources.py check DIR    # compare DIR's files to sources.json (offline)

The sources are kept by address, time and SHA-256 in sources.json, never as
text. A page online changes: a hash that differs says the page is not the one
the demo was written against, not that the demo is wrong. `fetch` uses the
snapshot add-on, so each file also gets its line in DIR/.snapshots.jsonl.

Exit codes: 0 every file there and matching; 1 a file missing or different;
2 refused.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE.parents[1] / "adapters/stdlib/snapshot/snapshot.py"


def listed() -> list[dict]:
    return json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]


def check(folder: Path) -> int:
    bad = 0
    for s in listed():
        path = folder / s["file"]
        if not path.is_file():
            print(f"missing    {s['file']}")
            bad += 1
        elif hashlib.sha256(path.read_bytes()).hexdigest() != s["sha256"]:
            print(
                f"different  {s['file']}  (the page is not the one this was written against)"
            )
            bad += 1
        else:
            print(f"matches    {s['file']}")
    return 1 if bad else 0


def fetch(folder: Path) -> int:
    folder.mkdir(parents=True, exist_ok=True)
    for s in listed():
        cmd = [
            sys.executable,
            str(SNAPSHOT),
            "fetch",
            "--url",
            s["url"],
            "--to",
            str(folder),
            "--name",
            s["file"],
        ]
        got = subprocess.run(cmd, capture_output=True, text=True)
        print(
            (got.stdout or got.stderr).strip().splitlines()[-1]
            if (got.stdout or got.stderr)
            else s["file"]
        )
    return check(folder)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("fetch", "check"):
        print("usage: sources.py fetch|check DIR", file=sys.stderr)
        return 2
    return (fetch if argv[0] == "fetch" else check)(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
