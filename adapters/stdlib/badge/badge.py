"""badge.py: a badge for a page: these answers came from these files and were approved. Python 3.9+.

    python adapters/stdlib/badge/badge.py --box DIR --to FILE [--link URL]

Writes an SVG badge, in the flat style README badges use, that says what the
record holds:

    [ willow | 3 answers from 2 files ]      green: the chain holds and every approval stands
    [ willow | record broken ]               red: the chain does not hold
    [ willow | 3 answers, 1 not standing ]   amber: an approval whose proof fails, or whose proposal file changed
    [ willow | no approved answers ]         grey: nothing is approved yet

An answer counts when its approval proves under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file is
still the bytes you approved. A file counts when an answer cites a passage in
it. Nothing about the answers is in the badge but the counts.

The badge carries what a reader needs to check it, in its own title and
description: the record's length and the start of its tip hash, and the one
command that anyone holding the box can run, `python kernel.py verify --box
BOX`. With --link URL (where you explain or host that check) it also prints the
Markdown to put on a page:

    [![willow: 3 answers from 2 files](badge.svg)](https://example.org/check)

A badge is a claim, shown to people who can't run anything: it is only as good
as the check behind it, and the badge says so in its description. It isn't
signed. FILE is written once, readable only by you, never over a file that
exists, and the same record gives the same bytes. Nothing is sent anywhere.

Exit codes, the kernel's: 0 written, green or grey; 42 written, but red or amber,
and waits on you; 2 refused (a bad command line).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

COLOURS = {
    "ok": "#3c9a5f",
    "empty": "#9f9f9f",
    "broken": "#c0392b",
    "partial": "#d4a017",
}
CHAR = 6.6  # a rough width of one character at the badge's font size


def facts(box: Path) -> dict:
    """What the record holds: counts, and whether it can be trusted."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {
            "state": "broken",
            "rows": len(rows),
            "tip": "",
            "answers": 0,
            "files": 0,
            "bad": 0,
        }
    where = {}
    for r in rows:
        for s in r.get("served", []):
            where.setdefault(s["id"], s["where"])
    answers, bad, files = 0, 0, set()
    for subj, row in kernel.sealed(box, rows).items():
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            bad += 1
            continue
        answers += 1
        files |= {where[c].rsplit(":", 1)[0] for c in prop["cites"] if c in where}
    forged = sum(
        1
        for r in rows
        if r["kind"] == "seal" and r.get("subject") not in kernel.sealed(box, rows)
    )
    return {
        "state": "partial" if bad or forged else "ok" if answers else "empty",
        "rows": len(rows),
        "tip": rows[-1]["hash"][:8] if rows else "",
        "answers": answers,
        "files": len(files),
        "bad": bad + forged,
    }


def message(f: dict) -> str:
    if f["state"] == "broken":
        return "record broken"
    n = f"{f['answers']} answer{'s' if f['answers'] != 1 else ''}"
    text = (
        f"{n} from {f['files']} file{'s' if f['files'] != 1 else ''}"
        if f["answers"]
        else "no approved answers"
    )
    return text + (f", {f['bad']} not standing" if f["bad"] else "")


def svg(f: dict) -> str:
    label, text = "willow", message(f)
    lw, rw = round(len(label) * CHAR + 14), round(len(text) * CHAR + 14)
    colour = COLOURS[f["state"]]
    title = f"willow: {text}"
    desc = (f"The record has {f['rows']} rows" + (f" and its tip begins {f['tip']}" if f["tip"] else "") +
            ". Check it with: python kernel.py verify --box BOX. This badge is a claim, not a signature.")  # fmt: skip
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lw + rw}" height="20" role="img" aria-label={quoteattr(title)}>\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n"
        f'<rect width="{lw}" height="20" fill="#555"/>\n<rect x="{lw}" width="{rw}" height="20" fill="{colour}"/>\n'
        f'<g fill="#fff" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11" text-anchor="middle">\n'
        f'<text x="{lw / 2:g}" y="14">{escape(label)}</text>\n<text x="{lw + rw / 2:g}" y="14">{escape(text)}</text>\n</g>\n</svg>\n'
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--link"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    link = opts.get("--link")
    if (
        not opts.get("--box")
        or not opts.get("--to")
        or args
        or ("--link" in opts and not (link or "").startswith(("http://", "https://")))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    f = facts(box)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as out:
        out.write(svg(f))
    print(f"wrote {to}: {message(f)}")
    if link:
        print(f"markdown: [![willow: {message(f)}]({to.name})]({link})")
    return kernel.ESCALATE if f["state"] in ("broken", "partial") else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
