"""annotations.py: your approved answers as W3C Web Annotations. Python 3.9+.

    python adapters/stdlib/annotations/annotations.py --box DIR --to FILE [--base URL]

The Web Annotation Data Model is what annotation tools (Hypothesis and the
others that read JSON-LD) use to say "this note is about that part of that
page". This writes each answer you approved as one, in an annotation page:

    {"@context": "http://www.w3.org/ns/anno.jsonld",
     "type": "AnnotationPage",
     "items": [{"type": "Annotation",
                "motivation": "describing",
                "created": "2026-10-24T00:00:00Z",
                "body": {"type": "TextualBody", "value": "Six hours.", "format": "text/plain"},
                "target": [{"source": "garden.md",
                            "selector": [{"type": "FragmentSelector", "conformsTo": "http://tools.ietf.org/rfc/rfc5147", "value": "line=0,1"},
                                         {"type": "TextQuoteSelector", "exact": "Tomatoes want six hours of sun."}]}]}]}

The body is the answer. There is one target for each passage the answer cites:
the file as `source`, the lines as an RFC 5147 fragment (counted from zero,
as that standard counts), and the passage's own words as a quote, so a tool
that can't use the lines can still find the text. `created` is when you
approved it. With --base URL, the source is URL followed by the file's path,
for files you publish there; without it, the path as it is in your folder.

An approval is exported only while its proof holds under your key (the
kernel's `sealed`, so the key is read there and nowhere here) and its proposal
file still holds the bytes you approved. A cited passage no longer in your
files is left off its annotation, since a target that quotes text no longer
there would lie; both are said on standard error.

FILE is written once, readable only by you, never over a file that exists, and
the same record and folder give the same bytes. Exit codes, the kernel's: 0
written; 42 written, but an approval or a citation was left out and waits on
you; 2 refused (a record that doesn't verify, a bad command line).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

CONTEXT = "http://www.w3.org/ns/anno.jsonld"
RFC5147 = "http://tools.ietf.org/rfc/rfc5147"


def target(passage: dict, base: str | None) -> dict:
    lines = passage["text"].count("\n") + 1
    start = passage["line"] - 1
    source = f"{base.rstrip('/')}/{quote(passage['path'])}" if base else passage["path"]
    return {
        "source": source,
        "selector": [
            {
                "type": "FragmentSelector",
                "conformsTo": RFC5147,
                "value": f"line={start},{start + lines}",
            },
            {"type": "TextQuoteSelector", "exact": passage["text"]},
        ],
    }


def annotations(
    box: Path, rows: list[dict], base: str | None
) -> tuple[list[dict], int, int]:
    """(the annotations, approvals left out, citations left out)."""
    by_id = {c["id"]: c for c in kernel.chunks(Path(kernel.config(box)["pile"]))}
    out, left, gone = [], 0, 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        targets = [target(by_id[c], base) for c in prop["cites"] if c in by_id]
        gone += len(prop["cites"]) - len(targets)
        out.append({
            "id": f"urn:willow:annotation:{subj[9:]}",
            "type": "Annotation",
            "motivation": "describing",
            "created": row["ts"],
            "generator": {"type": "Software", "name": "willow"},
            "body": {"type": "TextualBody", "value": prop["data"], "format": "text/plain"},
            "target": targets,
        })  # fmt: skip
    return out, left, gone


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--base"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    base = opts.get("--base")
    if (
        not opts.get("--box")
        or not opts.get("--to")
        or args
        or ("--base" in opts and not (base or "").startswith(("http://", "https://")))
    ):
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
    items, left, gone = annotations(box, rows, base)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    page = {"@context": CONTEXT, "type": "AnnotationPage", "items": items}
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(page, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"wrote {to}: {len(items)} annotation{'s' if len(items) != 1 else ''}")
    if left:
        print(
            f"{left} approval{'s' if left != 1 else ''} left out: its proposal file is not what you approved (python kernel.py verify says which)",
            file=sys.stderr,
        )
    if gone:
        print(
            f"{gone} cited passage{'s' if gone != 1 else ''} left off: no longer in your files",
            file=sys.stderr,
        )
    return kernel.ESCALATE if left or gone else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
