"""policy_watch.py: a terms or policy page, fetched each time you run it, and
what changed since the last copy, sentence by sentence.

    python adapters/stdlib/policy-watch/policy_watch.py --url URL --to FOLDER [--now ISO]

Each run saves the page once more into FOLDER through the snapshot add-on,
named by the time it was fetched (20261024T090000Z-privacy), with its
address, time and SHA-256 on its snapshot line. Then it finds the last copy
of the same address in FOLDER and says:

    first copy      20261024T090000Z-privacy saved; nothing to compare yet
    unchanged       the same bytes as 20261017T090000Z-privacy
    same words      the bytes differ, every sentence is the same
    changed         since 20261017T090000Z-privacy:

followed, for a change, by the clauses add-on's list: each sentence
reworded, added or removed. A web page is read as its blocks and a text file
as its paragraphs; a page that isn't UTF-8 text (a PDF) is compared by its
bytes only, and it says so. A page that can't be fetched is written down as
snapshot writes it, and compared with nothing.

Run it from a scheduler (cron, a calendar task) to watch a page; it keeps
every copy, so any two can be compared again later with `clauses diff`.

Exit codes, the kernel's: 0 the first copy, or nothing changed; 42 something
changed, or the page couldn't be fetched; 2 refused.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "snapshot"))
sys.path.insert(0, str(HERE.parents[1] / "clauses"))
import clauses  # noqa: E402
import kernel  # noqa: E402
import snapshot  # noqa: E402


def stamp(now: str) -> str:
    """2026-10-24T09:00:00Z as 20261024T090000Z, for a name that sorts by time."""
    return now.replace("-", "").replace(":", "")


def readable(folder: Path, row: dict) -> list[tuple[int, str]] | None:
    """A copy's sentences, read as a web page when it was served as one; None
    for a copy that isn't UTF-8 text."""
    text = clauses.read(folder / row["file"])
    if text is None:
        return None
    as_name = row["file"] + (".html" if "html" in row.get("type", "") else ".txt")
    return clauses.clauses(text, as_name)


def watch(url: str, folder: Path, now: str) -> int:
    before = [
        r for r in snapshot.lines(folder) if r.get("url") == url and r.get("file")
    ]
    name = f"{stamp(now)}-{snapshot.name_for(url)}"
    got = snapshot.save(url, folder, name, now)
    if got != kernel.ALIVE:
        return got
    after = next(r for r in reversed(snapshot.lines(folder)) if r.get("file") == name)
    if not before:
        print(f"first copy      {name} saved; nothing to compare yet")
        return kernel.ALIVE
    last = before[-1]
    if last["sha256"] == after["sha256"]:
        print(f"unchanged       the same bytes as {last['file']}")
        return kernel.ALIVE
    old, new = readable(folder, last), readable(folder, after)
    if old is None or new is None:
        print(
            f"changed         the bytes differ from {last['file']}; it isn't text, so"
        )
        print("                there are no sentences to compare")
        return kernel.ESCALATE
    diff = clauses.compare(old, new)
    if not (diff["reworded"] or diff["added"] or diff["removed"]):
        print(
            f"same words      the bytes differ from {last['file']}; every sentence is the same"
        )
        return kernel.ALIVE
    print(f"changed         since {last['file']}:")
    for o, a, kept, of in diff["reworded"]:
        print(f"reworded  {o[0]} -> {a[0]}   ({kept} of {of} words kept)")
        print(f"  - {o[1]}\n  + {a[1]}")
    for a in diff["added"]:
        print(f"added     {a[0]}   {a[1]}")
    for o in diff["removed"]:
        print(f"removed   {o[0]}   {o[1]}")
    return kernel.ESCALATE


def main(argv: list[str]) -> int:
    args = dict(zip(argv[::2], argv[1::2])) if len(argv) % 2 == 0 else {}
    if {"--url", "--to"} <= set(args) <= {"--url", "--to", "--now"}:
        now = args.get("--now") or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        if snapshot.urllib.parse.urlsplit(args["--url"]).scheme not in (
            "http",
            "https",
        ):
            print("refused: an address starts http:// or https://", file=sys.stderr)
            return kernel.REFUSED
        return watch(args["--url"], Path(args["--to"]), now)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
