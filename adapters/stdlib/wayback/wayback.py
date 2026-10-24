"""wayback.py: the Wayback Machine's copy of a page, from a window of days,
saved beside your own and compared with it.

    python adapters/stdlib/wayback/wayback.py find --url URL --to FOLDER
        [--after YYYYMMDD] [--before YYYYMMDD] [--against FILE] [--name NAME] [--now ISO]

A copy you fetched yourself says what a page said when you fetched it. The
Wayback Machine (web.archive.org) says what someone else saw, so a page that
changed since, or a copy someone doubts, can be checked against it.

`find` asks the Wayback Machine's index which captures it holds of URL that
answered 200, keeps those on or after --after and before --before, and takes
the latest. It saves that capture's bytes as they were archived (the `id_`
form, without the archive's banner) through the snapshot add-on, so the
copy gets its own line in FOLDER/.snapshots.jsonl, with `"wayback"` (the
capture's time) and `"of"` (the address it is a capture of). With
`--against FILE` it then says whether the capture holds the same bytes:

    capture   20261010120000 of https://…   saved as old.wayback.pdf
    same bytes as old.pdf   sha256 …

or `DIFFERS from old.pdf`, with both hashes. No capture in the window, or
no answer from the archive, is said as itself, not as a difference.

Exit codes, the kernel's: 0 a capture saved (and, with --against, the same
bytes); 42 no capture, no answer, or different bytes; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "snapshot"))
import kernel  # noqa: E402
import snapshot  # noqa: E402

#: the archive; the tests point it at this machine
BASE = os.environ.get("WILLOW_WAYBACK", "https://web.archive.org")


def captures(url: str, after: str, before: str) -> list[str]:
    """The times of the captures of `url` that answered 200, in the window,
    oldest first. Raises OSError when the archive can't be asked."""
    q = {"url": url, "output": "json", "fl": "timestamp,statuscode",
         "filter": "statuscode:200"}  # fmt: skip
    if after:
        q["from"] = after
    if before:
        q["to"] = before
    status, _, body, _ = snapshot.get(
        f"{BASE}/cdx/search/cdx?" + urllib.parse.urlencode(q)
    )
    if status != 200:
        raise OSError(f"the archive's index answered {status}")
    try:
        rows = json.loads(body or b"[]")
    except ValueError as e:
        raise OSError("the archive's index answered with something not JSON") from e
    times = [r[0] for r in rows[1:] if len(r) == 2 and r[1] == "200"]
    return sorted(
        t
        for t in times
        if (not after or t[:8] >= after) and (not before or t[:8] < before)
    )


def find(url: str, folder: Path, after: str, before: str, against: Path | None,
         name: str, now: str) -> int:  # fmt: skip
    if against is not None and not against.is_file():
        print(f"refused: {against} is not a file", file=sys.stderr)
        return kernel.REFUSED
    if after and before and after >= before:
        print(f"no capture of {url} from {after} to {before}: the window is empty")
        return kernel.ESCALATE
    try:
        times = captures(url, after, before)
    except (urllib.error.URLError, OSError) as e:
        print(f"couldn't reach the archive: {getattr(e, 'reason', e)}")
        return kernel.ESCALATE
    if not times:
        window = f"{after or 'the start'} to {before or 'now'}"
        print(f"no capture of {url} from {window}")
        return kernel.ESCALATE
    ts = times[-1]
    got = snapshot.save(
        f"{BASE}/web/{ts}id_/{url}", folder, name, now, wayback=ts, of=url
    )
    if got != kernel.ALIVE:
        return got
    print(f"capture   {ts} of {url}   saved as {name}")
    if against is None:
        return kernel.ALIVE
    mine = hashlib.sha256(against.read_bytes()).hexdigest()
    theirs = hashlib.sha256((folder / name).read_bytes()).hexdigest()
    if mine == theirs:
        print(f"same bytes as {against.name}   sha256 {mine}")
        return kernel.ALIVE
    print(f"DIFFERS from {against.name}   yours {mine}   the archive's {theirs}")
    return kernel.ESCALATE


def day(s: str) -> bool:
    return len(s) == 8 and s.isdigit()


def main(argv: list[str]) -> int:
    args = dict(zip(argv[1::2], argv[2::2])) if len(argv) % 2 else {}
    known = {"--url", "--to", "--after", "--before", "--against", "--name", "--now"}
    if (
        argv[:1] == ["find"]
        and {"--url", "--to"} <= set(args) <= known
        and all(day(args[k]) for k in ("--after", "--before") if k in args)
    ):
        url = args["--url"]
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            print("refused: an address starts http:// or https://", file=sys.stderr)
            return kernel.REFUSED
        now = args.get("--now") or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        name = args.get("--name") or "wayback-" + snapshot.name_for(url)
        against = Path(args["--against"]) if "--against" in args else None
        return find(url, Path(args["--to"]), args.get("--after", ""),
                    args.get("--before", ""), against, name, now)  # fmt: skip
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
