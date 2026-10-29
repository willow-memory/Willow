"""cloudevents.py: the record's rows as CloudEvents. Python 3.9+.

    python adapters/stdlib/cloudevents/cloudevents.py --box DIR --to FILE [--from-row N] [--kinds a,b]

CloudEvents is the envelope event brokers, serverless platforms and a long
list of tools already read. This writes each row of your record as one, a JSON
object a line in FILE (the structured JSON format, one event per line):

    {"specversion": "1.0",
     "id": "<the row's hash>",
     "source": "urn:willow:record:<the box's first row hash>",
     "type": "org.willow.record.seal",
     "time": "2026-10-24T00:00:00Z",
     "subject": "proposal:...",
     "sequence": "3",
     "standing": "sealed",
     "datacontenttype": "application/json",
     "data": { ...the row, as it is in the record... }}

The id is the row's own hash, so a row is the same event wherever it is
sent; the source names the box by its first row, so two boxes don't mix. The
type is the row's kind, `sequence` its place on the chain, `standing` what the
record says of it (sealed only for a row written by you, with your approval),
and `subject` the suggestion a proposal, seal or decline is about.

The record holds no question's words, and neither do the events: a question
is its fingerprint, a passage its id and where it was. The data is the row, so
the chain still checks: each event carries its hash and the hash before it.

--from-row N starts at row N (0 unless said), for sending only what is new;
--kinds a,b keeps only rows of those kinds (bite,seal). A record that doesn't
verify is refused: events read past a break could say what didn't happen.
FILE is written once, readable only by you, never over a file that exists, and
the same record gives the same bytes.

It reads the record and nothing else, never your key. Exit codes, the
kernel's: 0 written; 42 nothing in range, nothing written; 2 refused.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

KIND = re.compile(r"^[a-z][a-z0-9-]*$")


def event(row: dict, source: str) -> dict:
    ev = {
        "specversion": "1.0",
        "id": row["hash"],
        "source": source,
        "type": f"org.willow.record.{row['kind']}",
        "time": row["ts"],
        "sequence": str(row["n"]),
        "standing": row["standing"],
        "datacontenttype": "application/json",
        "data": row,
    }
    if isinstance(row.get("subject"), str):
        ev["subject"] = row["subject"]
    return ev


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--from-row", "--kinds"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    start, kinds = (
        opts.get("--from-row", "0"),
        (opts["--kinds"].split(",") if "--kinds" in opts else None),
    )
    bad = not start.isdigit() or (
        kinds is not None and not all(KIND.match(k) for k in kinds)
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
    chosen = [
        r
        for r in rows
        if r["n"] >= int(start) and (kinds is None or r["kind"] in kinds)
    ]
    if not chosen:
        print("No row in that range, so nothing was written.")
        return kernel.ESCALATE
    source = f"urn:willow:record:{rows[0]['hash']}"
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        for r in chosen:
            f.write(
                json.dumps(
                    event(r, source),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(
        f"wrote {to}: {len(chosen)} event{'s' if len(chosen) != 1 else ''}, rows {chosen[0]['n']} to {chosen[-1]['n']}"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
