"""Fetch the public rules the steelworks' training is checked against, once, and check them offline.

    python demo/blackout/fetch.py --to PILE [--contact EMAIL]   # online, once (or WILLOW_CONTACT=EMAIL)
    python demo/blackout/fetch.py --to PILE --check             # offline: holds, DIFFERS, missing
    python demo/blackout/fetch.py --list                        # the sources, no fetching

Each source is saved as it came into a folder of its own under PILE, with its
address, the time and its SHA-256 in that folder's .fetched.jsonl, and the
same three facts in [sources.json](sources.json), the record of what was
fetched. The repo keeps the hashes, never the bytes: the text is the
publishers'. After the fetch nothing in the study goes online.

The eCFR's text is the official one but its API answers only a client that
accepts compression, which willow's snapshot add-on doesn't ask for, so this
folder fetches for itself, with gzip. The Federal Register (as GPO's govinfo keeps it) and sec.gov are
the other publishers. sec.gov refuses a client that names no contact, so its
files are fetched only with --contact, and the contact (--contact, or the WILLOW_CONTACT environment variable, which keeps it
out of a command line) goes in the User-Agent to sec.gov alone, never into a line,
a file or this repo (a test holds that).

Once FROZEN.json exists a fetch refuses to rewrite sources.json: a change is
a new freeze.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources.json"
PAUSE = 1.0  # seconds between fetches: sec.gov asks for at most ten a second
ECFR = "https://www.ecfr.gov/api/versioner/v1/full"
AS_OF = "2026-11-01"  # the eCFR is a living text; this date's version is the one kept

#: (folder, file, address): the sources, in the order they are kept
SECTIONS = [
    ("240.10b-5", 240), ("240.10b5-1", 240), ("240.10b5-2", 240),
    ("243.100", 243), ("243.101", 243), ("243.102", 243), ("243.103", 243),
]  # fmt: skip
LIST = [
    ("ecfr", f"17-cfr-{sec}.xml", f"{ECFR}/{AS_OF}/title-17.xml?part={part}&section={sec}")
    for sec, part in SECTIONS
] + [
    ("federalregister", "2022-27675-insider-trading-arrangements.htm",
     "https://www.govinfo.gov/content/pkg/FR-2022-12-29/html/2022-27675.htm"),
    ("sec", "form8-k.pdf", "https://www.sec.gov/files/form8-k.pdf"),
    ("sec", "33-7881-regulation-fd.htm", "https://www.sec.gov/rules/final/33-7881.htm"),
    ("sec", "33-11138-rule-10b5-1.pdf", "https://www.sec.gov/files/rules/final/2022/33-11138.pdf"),
]  # fmt: skip


def is_sec(url: str) -> bool:
    """True only for an https address on sec.gov or a subdomain of it: the one
    publisher the person's contact goes to, judged by host, never by substring."""
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and (host == "sec.gov" or host.endswith(".sec.gov"))


def agent(url: str, contact: str | None) -> str:
    return (
        f"willow-demo {contact}"
        if contact and is_sec(url)
        else "willow-demo (public-source fetch)"
    )


def get(url: str, contact: str | None = None) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": agent(url, contact),
            "Accept-Encoding": "gzip",
            "Accept": "*/*",
        },  # fmt: skip
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    return body


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(pile: Path, contact: str | None) -> int:
    if (HERE / "FROZEN.json").exists():
        print("refused: FROZEN.json exists; a change to the sources is a new freeze")
        return 2
    kept, failed = [], []
    for folder, name, url in LIST:
        dest = pile / folder / name
        if is_sec(url) and not contact and not dest.exists():
            failed.append({"url": url, "why": "sec.gov needs a contact"})
            print(
                f"skip {folder}/{name}  (sec.gov needs a contact: --contact, or WILLOW_CONTACT)"
            )
            continue
        if dest.exists():  # fetched once: a rerun fills gaps, never refetches
            data = dest.read_bytes()
        else:
            try:
                data = get(url, contact)
            except (urllib.error.URLError, OSError) as e:
                failed.append({"url": url, "why": str(e)[:100]})
                print(f"FAIL {folder}/{name}  {str(e)[:100]}")
                continue
            if data[:5].lower() in (b"<!doc", b"<html") and name.endswith(
                (".xml", ".txt", ".pdf")
            ):
                failed.append(
                    {"url": url, "why": "an HTML page where a document was expected"}
                )
                print(
                    f"FAIL {folder}/{name}  an HTML page where a document was expected"
                )
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with (pile / folder / ".fetched.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps({"file": name, "url": url, "time": when,
                                      "sha256": sha(data)}, sort_keys=True) + "\n")  # fmt: skip
            time.sleep(PAUSE)
        kept.append({"folder": folder, "file": name, "url": url, "bytes": len(data),
                     "sha256": sha(data)})  # fmt: skip
        print(f"ok   {folder}/{name}  {len(data)} bytes")
    doc = {"as_of_ecfr": AS_OF, "failed": failed, "sources": kept}
    SOURCES.write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 1 if failed else 0


def check(pile: Path) -> int:
    bad = 0
    for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]:
        p = pile / s["folder"] / s["file"]
        if not p.is_file():
            state = "missing"
        elif sha(p.read_bytes()) != s["sha256"]:
            state = "DIFFERS"
        else:
            state = "holds"
        bad += state != "holds"
        print(f"{state:8} {s['folder']}/{s['file']}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    opts = {a: argv[i + 1] for i, a in enumerate(argv)
            if a in ("--to", "--contact") and i + 1 < len(argv)}  # fmt: skip
    if argv == ["--list"]:
        for folder, name, url in LIST:
            print(f"{folder}/{name}  {url}")
        return 0
    if "--to" not in opts or any(a.startswith("--") and a not in ("--to", "--contact", "--check")
                                 for a in argv):  # fmt: skip
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    pile = Path(opts["--to"])
    if "--check" in argv:
        return check(pile)
    return fetch(pile, opts.get("--contact") or os.environ.get("WILLOW_CONTACT"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
