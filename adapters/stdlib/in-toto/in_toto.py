"""in_toto.py: each answer you approved, as an in-toto Statement. Python 3.9+.

    python adapters/stdlib/in-toto/in_toto.py --box DIR --to FILE

The in-toto Statement (v1) is the envelope SLSA and the tools around it
read: what the attestation is about (a subject, named and hashed), and a
predicate that says something about it. One Statement is written for each
approved answer, one JSON object a line, oldest approval first:

    {"_type": "https://in-toto.io/Statement/v1",
     "subject": [{"name": "sun.md", "digest": {"sha256": "..."}}],
     "predicateType": "urn:willow:seal:v1",
     "predicate": {"claim": "...", "cites": [{"id": "...", "where": "garden.md:1"}],
                   "question": "<fingerprint>", "sealedAt": "...", "sealRow": 3,
                   "rowHash": "...", "suggestion": "proposal:..."}}

The subject is the answer's file as it was written when you approved it, and
its sha256 is the hash of those bytes, so anyone holding the file can check
it. The predicate says why the answer was given, which passages it cites and
where they were, which question it answers (by fingerprint, since the record
keeps no words), when it was approved, and the hash of the record's row that
holds your approval, so the Statement can be found again on the chain.

These are Statements, not signed envelopes: signing takes your key and no
add-on reads it. A DSSE envelope is what a signing tool makes from this. An
approval is exported only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file
still holds the bytes you approved; one that doesn't is left out and said on
standard error.

FILE is written once, readable only by you, never over a file that exists.
Exit codes, the kernel's: 0 written; 42 written, but an approval was left out
and waits on you; 2 refused (including a record that doesn't verify).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

STATEMENT = "https://in-toto.io/Statement/v1"
PREDICATE = "urn:willow:seal:v1"


def statements(box: Path, rows: list[dict]) -> tuple[list[dict], int]:
    """(one Statement per approval that stands, how many were left out)."""
    where = {}
    for r in rows:
        for s in r.get("served", []):
            where.setdefault(s["id"], s["where"])
    out, left = [], 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        out.append({
            "_type": STATEMENT,
            "subject": [{
                "name": prop["path"],
                "digest": {"sha256": hashlib.sha256(prop["data"].encode("utf-8")).hexdigest()},
            }],
            "predicateType": PREDICATE,
            "predicate": {
                "claim": prop["claim"],
                "cites": [{"id": c, "where": where.get(c, "")} for c in prop["cites"]],
                "question": asked,
                "sealedAt": row["ts"],
                "sealRow": row["n"],
                "rowHash": row["hash"],
                "suggestion": subj,
            },
        })  # fmt: skip
    return out, left


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or not opts.get("--to") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    found, left = statements(box, rows)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        for s in found:
            f.write(
                json.dumps(s, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                + "\n"
            )
    print(f"wrote {to}: {len(found)} statement{'s' if len(found) != 1 else ''}")
    if left:
        print(f"{left} approval{'s' if left != 1 else ''} left out: its proposal file is not what you "
              "approved (python kernel.py verify says which)", file=sys.stderr)  # fmt: skip
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
