"""keep.py: an Almanac entry's best permitted copy, fetched into your folder.

    python adapters/stdlib/almanac-keep/keep.py --catalog FILE --id ID --to FOLDER

An Almanac catalogs public data where its publishers keep it, and when a
source is lost, its `recovery[]` lists where copies are, ranked by how
verifiable each is. The Almanac points; it never hosts. This fetches one copy
into a folder of yours, through the snapshot add-on, so you hold it:

    kept      ejscreen.html   from: wayback, timestamped, captured 2025-02-04
              sha256 …        (the almanac has no fingerprint to compare)

The first copy that answers is kept, tried in this order:

1. the publisher's own address, when the entry is `live` or `frozen`;
2. each `recovery[]` copy, best authenticity first (hash-verified,
   cross-archive, timestamped, asserted). A copy marked `excluded` is never
   tried; one marked `review` only with `--review`.

A Wayback Machine capture is fetched raw (`id_`), the page as it was archived
rather than wrapped in the archive's toolbar, so its bytes can match the
entry's `fingerprint.sha256` when the almanac recorded one. The file is named
by the entry's id, and its snapshot line records which copy it came from.

Exit codes, the kernel's: 0 kept a copy; 42 nothing to try, or nothing that
was tried answered; 2 refused (no such catalog or id, or the name is taken).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "snapshot"))
import kernel  # noqa: E402
import snapshot  # noqa: E402

USAGE = "usage: keep.py --catalog FILE --id ID --to FOLDER [--review] [--now ISO]"
RANK = {"hash-verified": 0, "cross-archive": 1, "timestamped": 2, "asserted": 3}
WAYBACK = re.compile(
    r"^(https?://web\.archive\.org/web/)(\d{4,14})(?:[a-z]{2}_)?/(.+)$"
)


def raw(url: str) -> str:
    """A Wayback capture's address for its archived bytes (`id_`); others as given."""
    m = WAYBACK.match(url)
    return f"{m.group(1)}{m.group(2)}id_/{m.group(3)}" if m else url


def candidates(entry: dict, review: bool) -> list[tuple[str, str]]:
    """(address, where it's from) to try, in order."""
    out = []
    url = (entry.get("source") or {}).get("canonical_url")
    if url and entry.get("status") in ("live", "frozen"):
        out.append((url, "the publisher's own address"))
    copies = [
        c for c in entry.get("recovery") or [] if isinstance(c, dict) and c.get("url")
    ]
    allowed = {"ok", None} | ({"review"} if review else set())
    copies = [c for c in copies if c.get("permission") in allowed]
    copies.sort(
        key=lambda c: RANK.get(c.get("authenticity"), 9)
    )  # stable: the almanac's order
    for c in copies:
        said = ", ".join(str(x) for x in (c.get("via"), c.get("authenticity")) if x)
        if c.get("captured"):
            said += f", captured {c['captured']}"
        out.append((raw(c["url"]), said or "a recovery copy"))
    return out


def main(argv: list[str]) -> int:
    review = "--review" in argv
    rest = [a for a in argv if a != "--review"]
    opts = dict(zip(rest[::2], rest[1::2]))
    if len(rest) % 2 or not {"--catalog", "--id", "--to"} <= set(opts) <= {
        "--catalog", "--id", "--to", "--now"} or argv.count("--review") > 1:  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        entries = json.loads(Path(opts["--catalog"]).read_text(encoding="utf-8"))[
            "entries"
        ]
    except (OSError, ValueError, KeyError, TypeError):
        print(
            f"refused: {opts['--catalog']} is not an almanac catalog.json",
            file=sys.stderr,
        )
        return kernel.REFUSED
    entry = next(
        (e for e in entries if isinstance(e, dict) and e.get("id") == opts["--id"]),
        None,
    )
    if entry is None:
        print(
            f"refused: no entry {opts['--id']!r} in {opts['--catalog']}",
            file=sys.stderr,
        )
        return kernel.REFUSED
    folder = Path(opts["--to"])
    now = opts.get("--now") or dt.datetime.now(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    tries = candidates(entry, review)
    if not tries:
        print(f"nothing to fetch: {entry['id']} has no permitted copy to try")
        return kernel.ESCALATE
    baseline = (entry.get("fingerprint") or {}).get("sha256")
    for url, said in tries:
        before = (
            {r.get("file") for r in snapshot.lines(folder)}
            if folder.exists()
            else set()
        )
        got = snapshot.save(url, folder, entry["id"], now, infer_type=True,
                            almanac_id=entry["id"], copy=said)  # fmt: skip
        if got == kernel.REFUSED:
            return got
        if got != kernel.ALIVE:
            continue
        row = next(
            r
            for r in snapshot.lines(folder)
            if r.get("file") and r["file"] not in before
        )
        sha = hashlib.sha256((folder / row["file"]).read_bytes()).hexdigest()
        if not baseline:
            match = "(the almanac has no fingerprint to compare)"
        elif sha == baseline:
            match = "matches the almanac's fingerprint"
        else:
            match = "differs from the almanac's fingerprint"
        print(
            f"kept      {row['file']}   from: {said}\n          sha256 {sha}   {match}"
        )
        return kernel.ALIVE
    print(f"nothing kept: none of the {len(tries)} copies of {entry['id']} answered")
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
