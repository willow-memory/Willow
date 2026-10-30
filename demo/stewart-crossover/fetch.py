"""fetch.py: the sources in sources.json, fetched again and held to their hashes.

    python demo/stewart-crossover/fetch.py --to DIR [--grove DIR] [--offline]

Each source is fetched from its pinned address into DIR/raw/, and the words
the kernel reads go to DIR/sources/ID.txt. A wiki page at a revision, or a
data file at a commit, is held whole, by its bytes. A news page is held by
its article's lines: its text by the kernel's own `html_text`, each line
with its spaces squeezed, and only the lines whose SHA-256 was frozen kept,
in page order, so a sidebar that changes by the hour changes nothing here.
The parody line comes from
a willows-grove checkout (--grove, default the one beside this repo), at its
pinned commit, into DIR/parody/gerald.txt: the G28 atom only.

Each source is said to be one of:

    held          the bytes, or every frozen line, are there
    N of M lines  a news page holds only N of its M frozen lines: those used
    changed       the bytes changed, or no frozen line is left: not used
    unreachable   it couldn't be fetched: not used

`--offline` fetches nothing and checks what DIR/raw/ already holds. Nothing
here keeps a source's text in this repo; DIR is yours, outside it.

Exit codes: 0 every source held; 42 some not wholly held;
2 a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
G28 = "### G28  |  gerald-canon  |  sean"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lines_kept(src: dict, raw: bytes) -> list[str]:
    """A news page's frozen lines, in page order, each once."""
    want, kept = set(src["passages"]), []
    for line in kernel.html_text(raw.decode("utf-8", "replace")).splitlines():
        line = " ".join(line.split())
        if sha(line.encode("utf-8")) in want and line not in kept:
            kept.append(line)
    return kept


def get(src: dict, grove: Path) -> bytes:
    if src["kind"] == "parody":
        commit, path = src["url"].split("@", 1)[1].split(":", 1)
        return subprocess.run(["git", "-C", str(grove), "show", f"{commit}:{path}"],
                              capture_output=True, check=True).stdout  # fmt: skip
    req = urllib.request.Request(src["url"], headers={"User-Agent": "Mozilla/5.0"})
    for wait in (2, 4, 8, 16, None):  # a busy site (Wikipedia's 429) is asked again
        time.sleep(1)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)
    raise OSError("unreachable")


def parody_block(text: str) -> str:
    """The G28 atom: its heading to the next heading."""
    start = text.index(G28)
    end = text.find("\n### ", start + len(G28))
    return text[start : end if end > 0 else len(text)].strip() + "\n"


def fetch(to: Path, grove: Path, offline: bool) -> dict[str, str]:
    states = {}
    for d in ("raw", "sources", "parody"):
        (to / d).mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        raw_path = to / "raw" / src["id"]
        out = to / (
            "parody/gerald.txt"
            if src["kind"] == "parody"
            else f"sources/{src['id']}.txt"
        )
        out.unlink(missing_ok=True)  # a source not held now leaves nothing behind
        try:
            raw = raw_path.read_bytes() if offline else get(src, grove)
        except (OSError, subprocess.CalledProcessError):
            states[src["id"]] = "unreachable"
            continue
        raw_path.write_bytes(raw)
        if src["kind"] == "html":
            kept = lines_kept(src, raw)
            n, m = len(kept), len(src["passages"])
            if not kept:
                states[src["id"]] = "changed"
                continue
            out.write_text("\n".join(kept) + "\n", encoding="utf-8")
            states[src["id"]] = "held" if n == m else f"{n} of {m} lines"
            continue
        if sha(raw) != src["bytes_sha256"]:
            states[src["id"]] = "changed"
            continue
        text = raw.decode("utf-8", "replace")
        if src["kind"] == "parody":
            (to / "parody" / "gerald.txt").write_text(
                parody_block(text), encoding="utf-8"
            )
        else:
            (to / "sources" / f"{src['id']}.txt").write_text(text, encoding="utf-8")
        states[src["id"]] = "held"
    return states


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--to", "--grove"):
            opts[a] = next(it, "")
        elif a == "--offline":
            opts[a] = True
        else:
            opts["bad"] = a
    if not opts.get("--to") or "bad" in opts:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    grove = Path(opts.get("--grove") or ROOT.parent / "willows-grove")
    states = fetch(Path(opts["--to"]), grove, bool(opts.get("--offline")))
    for name, state in states.items():
        print(f"{name:12} {state}")
    return 0 if all(s == "held" for s in states.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
