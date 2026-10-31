"""fetch.py: the two books in sources.json, fetched again and held to their hashes.

    python demo/ofrenda/fetch.py --to DIR [--offline]

Each source is fetched from its pinned address into DIR/raw/, and held by its
bytes' SHA-256. The words the kernel reads go to DIR/sources/ID.txt: a text
file as it is, an HTML page through the kernel's own `html_text`. Each source
is said to be one of:

    held          the bytes are the ones frozen
    changed       the bytes changed: not used
    unreachable   it couldn't be fetched: not used

`--offline` fetches nothing and checks what DIR/raw/ already holds. Nothing
here keeps a book's text in this repo; DIR is yours, outside it.

Exit codes: 0 every source held; 42 some not held; 2 a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import kernel  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))


def text_of(src: dict, raw: bytes) -> str:
    text = raw.decode("utf-8-sig")
    return kernel.html_text(text) if src["kind"] == "html" else text


def fetch(to: Path, offline: bool) -> dict[str, str]:
    (to / "raw").mkdir(parents=True, exist_ok=True)
    (to / "sources").mkdir(exist_ok=True)
    said = {}
    for src in SOURCES:
        raw_path = to / "raw" / src["id"]
        try:
            if offline:
                raw = raw_path.read_bytes()
            else:
                req = urllib.request.Request(
                    src["url"], headers={"User-Agent": "willow-demo"}
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    raw = r.read()
                raw_path.write_bytes(raw)
        except OSError:
            said[src["id"]] = "unreachable"
            continue
        if hashlib.sha256(raw).hexdigest() != src["bytes_sha256"]:
            said[src["id"]] = "changed"
            continue
        out = to / "sources" / f"{src['id']}.txt"
        out.write_text(text_of(src, raw), encoding="utf-8")
        said[src["id"]] = "held"
    return said


def main(argv: list[str]) -> int:
    offline = "--offline" in argv
    rest = [a for a in argv if a != "--offline"]
    if len(rest) != 2 or rest[0] != "--to":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    said = fetch(Path(rest[1]), offline)
    for sid, state in said.items():
        print(f"{state:12}{sid}")
    return 0 if set(said.values()) == {"held"} else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
