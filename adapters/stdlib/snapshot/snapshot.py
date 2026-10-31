"""snapshot.py: a web page or file fetched once into a folder, with where it
came from, when, and its SHA-256, so later answers cite the copy.

    python adapters/stdlib/snapshot/snapshot.py fetch --url URL --to FOLDER [--name NAME] [--now ISO]
    python adapters/stdlib/snapshot/snapshot.py check --in FOLDER

A page online changes, and an answer that cites it should say what it said
then. `fetch` saves the address's bytes as FOLDER/NAME (by default the
address's last part) exactly as they came, and adds one line to
FOLDER/.snapshots.jsonl:

    {"bytes": 692585, "fetched": "2026-10-24T08:53:10Z", "file": "old.pdf",
     "sha256": "…", "status": 200, "type": "application/pdf", "url": "https://…"}

The line is in a hidden file, so the kernel never serves it as a passage.
Fetched once: a name already in FOLDER is refused, never overwritten. An
address that can't be reached, or answers with an error, writes no file but
still gets its line, with `"status"` and `"why"`, so a missing source is
written down, not left out.

`check` goes nowhere: it hashes each file again and says, for each,
`holds`, `CHANGED` or `missing`, and `unlisted` for a file in FOLDER no line
names, which nothing vouches for.

Exit codes, the kernel's: fetch, 0 saved, 42 couldn't reach it; check, 0
every file holds, 42 anything changed, missing or unlisted; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LOG = ".snapshots.jsonl"
AGENT = "willow-snapshot/1 (+https://github.com/willow-memory/willow)"
TIMEOUT = 60
SAFE = re.compile(r"[^A-Za-z0-9._-]+")
EXTENSION = {
    "application/json": ".json",
    "application/pdf": ".pdf",
    "text/html": ".html",
    "text/plain": ".txt",
}


def name_for(url: str) -> str:
    """The address's last part, made safe for a file name; the host's name
    for an address that ends in /."""
    parts = urllib.parse.urlsplit(url)
    last = parts.path.rstrip("/").rsplit("/", 1)[-1] if parts.path.strip("/") else ""
    name = SAFE.sub("-", last or parts.netloc).strip("-.")
    return name or "page"


def name_with_type(name: str, kind: str) -> str:
    """A default name with no suffix gets the extension its content type says."""
    if Path(name).suffix:
        return name
    ext = EXTENSION.get(kind.split(";", 1)[0].strip().lower())
    return name + ext if ext else name


def lines(folder: Path) -> list[dict]:
    log = folder / LOG
    if not log.exists():
        return []
    return [
        json.loads(s) for s in log.read_text(encoding="utf-8").splitlines() if s.strip()
    ]


def note(folder: Path, row: dict) -> None:
    with open(folder / LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def get(url: str) -> tuple[int, str, bytes, str]:
    """(status, content type, body, final address); raises URLError when it
    can't be reached at all."""
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", b"", url


def save(
    url: str, folder: Path, name: str, now: str, infer_type: bool = False, **extra
) -> int:
    """Fetch `url` once into folder/name, and its line; also used by wayback."""
    if "/" in name or "\\" in name or name.startswith(".") or not name:
        print(f"refused: {name!r} is not a plain file name", file=sys.stderr)
        return kernel.REFUSED
    if (folder / name).exists() or any(r.get("file") == name for r in lines(folder)):
        print(f"refused: {name} is already in {folder}; a snapshot is fetched once",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    folder.mkdir(parents=True, exist_ok=True)
    row = {"file": name, "url": url, "fetched": now, **extra}
    try:
        status, kind, body, final = get(url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        why = getattr(e, "reason", e)
        note(
            folder,
            {**row, "file": None, "status": None, "why": f"couldn't reach it: {why}"},
        )
        print(f"couldn't reach {url}: {why}")
        return kernel.ESCALATE
    if not 200 <= status < 300:
        note(
            folder, {**row, "file": None, "status": status, "why": f"answered {status}"}
        )
        print(f"couldn't fetch {url}: it answered {status}")
        return kernel.ESCALATE
    if infer_type:
        name = name_with_type(name, kind)
        row["file"] = name
        if (folder / name).exists() or any(
            r.get("file") == name for r in lines(folder)
        ):
            print(f"refused: {name} is already in {folder}; a snapshot is fetched once",
                  file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    (folder / name).write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    if final != url:
        row["final_url"] = final
    note(
        folder,
        {**row, "status": status, "type": kind, "bytes": len(body), "sha256": sha},
    )
    print(f"saved     {name}   {len(body)} bytes   sha256 {sha}")
    return kernel.ALIVE


def check(folder: Path) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    listed, worst = {}, kernel.ALIVE
    for r in lines(folder):
        if r.get("file"):
            listed[r["file"]] = r
    for name, r in sorted(listed.items()):
        p = folder / name
        if not p.is_file():
            state = "missing"
        elif hashlib.sha256(p.read_bytes()).hexdigest() == r["sha256"]:
            state = "holds"
        else:
            state = "CHANGED"
        worst = worst if state == "holds" else kernel.ESCALATE
        print(f"{state:<9} {name}   {r['url']}   fetched {r['fetched']}")
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder).as_posix()
        if (
            p.is_file()
            and rel not in listed
            and not any(s.startswith(".") for s in rel.split("/"))
        ):
            print(f"unlisted  {rel}")
            worst = kernel.ESCALATE
    return worst


def main(argv: list[str]) -> int:
    args = dict(zip(argv[1::2], argv[2::2])) if len(argv) % 2 else {}
    if argv[:1] == ["fetch"] and {"--url", "--to"} <= set(args) <= {
        "--url",
        "--to",
        "--name",
        "--now",
    }:
        now = args.get("--now") or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        url = args["--url"]
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            print("refused: an address starts http:// or https://", file=sys.stderr)
            return kernel.REFUSED
        return save(
            url,
            Path(args["--to"]),
            args.get("--name") or name_for(url),
            now,
            infer_type="--name" not in args,
        )
    if argv[:1] == ["check"] and set(args) == {"--in"}:
        return check(Path(args["--in"]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
