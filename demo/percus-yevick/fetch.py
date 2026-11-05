"""fetch.py: the stack's sources, fetched again and held to their hashes.

    python demo/percus-yevick/fetch.py --to DIR            # fetch, then check
    python demo/percus-yevick/fetch.py --to DIR --check    # check only, offline
    python demo/percus-yevick/fetch.py --to DIR --pin      # draft only: record

Each source in sources.json is fetched from its address to
DIR/<slug>/source.bin (an arXiv e-print, a Wikipedia revision's export) and
then unpacked: an e-print's tar (or a lone gzipped .tex) to DIR/<slug>/src/,
a Wikipedia export to DIR/<slug>/export.xml. Goes online; not part of CI.

`--check` needs no network: it hashes each source.bin by SHA-256 and holds it
to sources.json. `--pin` fetches and writes each source's time, size and
hash into sources.json; it is refused once FROZEN.json exists, since a frozen
list is changed only by a new freeze.

Exit codes, the kernel's: 0 everything there and matching; 42 something is
missing; 2 something doesn't match, or a bad command line.
"""

from __future__ import annotations

import datetime
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST = HERE / "sources.json"
AGENT = "willow-percus-yevick-study/1 (fetch.py)"


def slug(source_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "_", source_id).strip("_")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get(url: str) -> bytes:
    """The bytes at `url`, tried again after 2, 4, 8 and 16 seconds, or as
    long as a 429's Retry-After asks (at most two minutes)."""
    for wait in (2, 4, 8, 16, None):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if wait is None or e.code not in (429, 500, 502, 503, 504):
                raise
            after = e.headers.get("Retry-After", "")
            time.sleep(min(int(after), 120) if after.isdigit() else wait * 8)
        except OSError:
            if wait is None:
                raise
            time.sleep(wait)
    raise AssertionError("unreachable")


def unpack(kind: str, data: bytes, to: Path) -> None:
    """An e-print to src/: a tar (gzipped or not), else one gzipped file as
    main.tex, else a PDF left as it is. A Wikipedia export as export.xml."""
    if kind == "wikipedia":
        (to / "export.xml").write_bytes(data)
        return
    src = to / "src"
    src.mkdir(exist_ok=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as t:
            if hasattr(tarfile, "data_filter"):
                t.extractall(src, filter="data")
            else:  # Python before the filter: only plain files and folders
                safe = [m for m in t.getmembers() if (m.isfile() or m.isdir())
                        and not m.name.startswith(("/", "..")) and ".." not in Path(m.name).parts]  # fmt: skip
                t.extractall(src, members=safe)
        return
    except tarfile.TarError:
        pass
    if data[:2] == b"\x1f\x8b":
        (src / "main.tex").write_bytes(gzip.decompress(data))
    elif data[:4] == b"%PDF":
        (src / "paper.pdf").write_bytes(data)
    else:
        (src / "main.tex").write_bytes(data)


def check(to: Path, sources: list[dict]) -> int:
    missing = bad = 0
    for s in sources:
        f = to / slug(s["id"]) / "source.bin"
        if not f.is_file():
            print(f"missing   {s['id']}")
            missing += 1
        elif s["sha256"] is None:
            print(f"unpinned  {s['id']}")
            missing += 1
        elif sha(f.read_bytes()) != s["sha256"]:
            print(f"DIFFERS   {s['id']}: {sha(f.read_bytes())} is not {s['sha256']}")
            bad += 1
        else:
            print(f"same      {s['id']}")
    return 2 if bad else 42 if missing else 0


def fetch(to: Path, sources: list[dict], pin: bool, save=lambda: None) -> None:
    """Fetch what isn't here; with `pin`, also what has no hash yet, saving
    the list after each so a stopped run picks up where it was."""
    for s in sources:
        d = to / slug(s["id"])
        if (d / "source.bin").is_file() and not (pin and s["sha256"] is None):
            continue
        data = get(s["url"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "source.bin").write_bytes(data)
        unpack(s["kind"], data, d)
        if pin:
            s["fetched"] = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            s["bytes"], s["sha256"] = len(data), sha(data)
            save()
        print(f"fetched   {s['id']}  {len(data)} bytes")
        time.sleep(3)  # arXiv and Wikipedia ask for a pause between requests


def main(argv: list[str]) -> int:
    if (
        len(argv) not in (2, 3)
        or argv[0] != "--to"
        or argv[2:] not in ([], ["--check"], ["--pin"])
    ):
        print("usage: fetch.py --to DIR [--check | --pin]", file=sys.stderr)
        return 2
    to = Path(argv[1])
    listing = json.loads(LIST.read_text(encoding="utf-8"))
    if argv[2:] == ["--pin"]:
        if (HERE / "FROZEN.json").exists():
            print(
                "refused: the list is frozen; a change is a new freeze", file=sys.stderr
            )
            return 2

        def save() -> None:
            LIST.write_text(
                json.dumps(listing, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        fetch(to, listing["sources"], pin=True, save=save)
    elif argv[2:] == []:
        fetch(to, listing["sources"], pin=False)
    return check(to, listing["sources"])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
