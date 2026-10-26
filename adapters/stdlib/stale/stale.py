"""stale.py: approved answers whose cited passage has changed or gone.

    python adapters/stdlib/stale/stale.py --box DIR

An approved answer cites passages by id, and a passage's id is the SHA-256 of
its text. So when the cited words change, or their file goes, that id is no
longer anywhere in your folder, and this says so exactly; no guess, no date
compared. For each approval it prints whether it still holds, and for one
that doesn't, which cited passage is missing and where it was:

    stale   proposal:0a6fde95…  "Reply by 2026-09-16: …"
            cited 0e4ba2dfb524, was at mail/2026-03-20-county.txt:12: no longer in your folder
    holds   proposal:7c1e…      "Six hours."

The kernel keeps giving an approved answer for its question whatever its
sources do; this is how a person finds out the ground moved under one.

Exit codes, the kernel's: 0 every approval holds (or there are none); 42 an
approval's cited passage has changed or gone, and waits on you; 2 refused (a
record that doesn't verify).

It only reads: the record, the approved suggestions, your folder. It writes
nothing, and it doesn't take an approval back; that stays the person's.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def check(box: Path) -> tuple[int, list[dict]]:
    """(exit code, one entry per approval, in the order they were sealed)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return kernel.REFUSED, [{"refused": b} for b in breaks]
    places = {}  # where each served id was, from the bites that served it
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    here = {c["id"] for c in kernel.chunks(Path(kernel.config(box)["pile"]))}
    out = []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if (
            why is not None
        ):  # its cites can't be read from a file that isn't what was sealed
            out.append({"subject": subj, "broken": why, "gone": [], "row": row["n"]})
            continue
        gone = [
            {"id": c, "was": places.get(c, "?")} for c in prop["cites"] if c not in here
        ]
        out.append(
            {"subject": subj, "data": prop["data"], "gone": gone, "row": row["n"]}
        )
    stale = any(e["gone"] or e.get("broken") for e in out)
    return (kernel.ESCALATE if stale else kernel.ALIVE), out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    code, entries = check(box)
    for e in entries:
        if "refused" in e:
            print(f"refused: {e['refused']}", file=sys.stderr)
            continue
        if "broken" in e:
            print(
                f"{'broken':<7} {e['subject'][:21]}…  its proposal file {e['broken']}"
            )
            continue
        quote = e["data"] if len(e["data"]) <= 60 else e["data"][:57] + "..."
        print(f"{'stale' if e['gone'] else 'holds':<7} {e['subject'][:21]}…  {quote!r}")
        for g in e["gone"]:
            print(
                f"        cited {g['id'][:12]}, was at {g['was']}: no longer in your folder"
            )
    if code != kernel.REFUSED:
        n = sum(bool(e["gone"]) for e in entries)
        bad = sum("broken" in e for e in entries)
        print(
            f"{len(entries)} approved; {n} stale" + (f"; {bad} broken" if bad else "")
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
