"""rss_out.py: your approved answers as an RSS feed. Python 3.9+.

    python adapters/stdlib/rss-out/rss_out.py --box DIR --to FILE [--link URL] [--title TEXT] [--since DATE]

RSS is what feed readers subscribe to. This writes each answer you approved as
one item of an RSS 2.0 feed, newest first, so a reader shows you new answers as
they are approved:

    <item>
      <title>Six hours of sun.</title>
      <description>Six hours of sun.

    Why: the garden notes
    From: garden.md:1</description>
      <guid isPermaLink="false">proposal:...</guid>
      <pubDate>Sat, 24 Oct 2026 00:00:00 +0000</pubDate>
    </item>

The title is the answer's first line (80 characters at most), the description
is the answer with the reason it was given and the places it cites, the date is
when you approved it, and the id is the suggestion's subject, so a reader
shows an answer once. --link is the address the channel is said to be at
(http://localhost/ unless given), --title the feed's name ("Willow: approved
answers"), and --since DATE (YYYY-MM-DD) keeps only answers approved on or
after it.

An approval is exported only while its proof holds under your key (the
kernel's `sealed`, so the key is read there and nowhere here) and its proposal
file still holds the bytes you approved; one that doesn't is left out and said
on standard error. The record keeps no question's words, and the feed has
none. FILE is written once, readable only by you, never over a file that
exists, and the same record gives the same bytes. Nothing is served or sent:
put FILE where your reader can fetch it.

Exit codes, the kernel's: 0 written; 42 written, but an approval was left out
and waits on you; 2 refused (a record that doesn't verify, a bad command line).
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def rfc822(ts: str) -> str:
    """A record time (2026-10-24T00:00:00Z) as RFC 822 in UTC, by the English day and month names."""
    d = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    months = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    return f"{days[d.weekday()]}, {d.day:02d} {months[d.month - 1]} {d.year} {d:%H:%M:%S} +0000"


def title_of(answer: str) -> str:
    line = next((x.strip() for x in answer.splitlines() if x.strip()), "(empty answer)")
    return line if len(line) <= 80 else line[:79] + "…"


def items(box: Path, rows: list[dict], since: str | None) -> tuple[list[dict], int]:
    """(approved answers, newest first; how many approvals were left out)."""
    where = {}
    for r in rows:
        for s in r.get("served", []):
            where.setdefault(s["id"], s["where"])
    out, left = [], 0
    for subj, row in kernel.sealed(box, rows).items():
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        if since and row["ts"][:10] < since:
            continue
        out.append({"subject": subj, "ts": row["ts"], "n": row["n"], "answer": prop["data"], "claim": prop["claim"],
                    "cites": [where.get(c, c[:12]) for c in prop["cites"]]})  # fmt: skip
    return sorted(out, key=lambda i: -i["n"]), left


def feed(found: list[dict], title: str, link: str) -> str:
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = title
    ET.SubElement(ch, "link").text = link
    ET.SubElement(
        ch, "description"
    ).text = "Answers approved in a willow box, newest first."
    if found:
        ET.SubElement(ch, "lastBuildDate").text = rfc822(found[0]["ts"])
    for i in found:
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, "title").text = title_of(i["answer"])
        why = f"\n\nWhy: {i['claim']}" if i["claim"] else ""
        src = f"\nFrom: {', '.join(i['cites'])}" if i["cites"] else ""
        ET.SubElement(it, "description").text = i["answer"] + why + src
        guid = ET.SubElement(it, "guid", isPermaLink="false")
        guid.text = i["subject"]
        ET.SubElement(it, "pubDate").text = rfc822(i["ts"])
    ET.indent(rss, space="  ")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(rss, encoding="unicode")
        + "\n"
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--link", "--title", "--since"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    link, title, since = (
        opts.get("--link", "http://localhost/"),
        opts.get("--title", "Willow: approved answers"),
        opts.get("--since"),
    )
    bad = (
        not link.startswith(("http://", "https://"))
        or not title.strip()
        or (since is not None and not DATE.match(since))
    )
    if not opts.get("--box") or not opts.get("--to") or args or bad:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    found, left = items(box, rows, since)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(feed(found, title, link))
    print(f"wrote {to}: {len(found)} item{'s' if len(found) != 1 else ''}")
    if left:
        print(
            f"{left} approval{'s' if left != 1 else ''} left out: its proposal file is not what you approved (python kernel.py verify says which)",
            file=sys.stderr,
        )
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
