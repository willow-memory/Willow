"""seals_waiting.py: what waits on your seal, by subject, read from the
record with no row added. Python 3.9+.

    python adapters/stdlib/seals-waiting/seals_waiting.py --box DIR [--json]

What `kernel.py out` says, the same lines in the same words:

    waiting on your seal: proposal:<sha256>
    12 rows; 3 sealed; 1 waiting

but `out` appends a row each time it is asked, so a program that asks often
(an assistant's door, before each answer) grows the record by a row an ask.
This asks the kernel's own `read`, `sealed` and `waiting` and appends
nothing: the record is the same bytes after. The rows it counts are the ones
there, not one more. `--json` prints {"state", "waiting", "sealed", "rows"},
each a subject. A seal is counted only while its proof holds under the key,
which the kernel's `sealed` reads; nothing here does.

Exit codes, the kernel's: 0 nothing waits; 42 something waits on you; 2
refused (not a box, a record that doesn't read, a bad command line).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: seals_waiting.py --box DIR [--json]"


def held(box: Path) -> dict | str:
    """What the record holds open and sealed, or why it couldn't be read."""
    if not (box / "kernel.json").exists():
        return "not a kernel box; init first"
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "\n  ".join(breaks)
    return {"rows": len(rows), "sealed": sorted(kernel.sealed(box, rows)),
            "waiting": list(kernel.waiting(box, rows))}  # fmt: skip


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    rest = [a for a in argv if a != "--json"]
    if len(rest) != 2 or rest[0] != "--box" or not rest[1]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    got = held(Path(rest[1]))
    if isinstance(got, str):
        print(f"refused: {got}", file=sys.stderr)
        return kernel.REFUSED
    if as_json:
        state = "waiting" if got["waiting"] else "empty"
        print(json.dumps({"state": state, **got}))
    else:
        for s in got["waiting"]:
            print(f"waiting on your seal: {s}")
        print(
            f"{got['rows']} rows; {len(got['sealed'])} sealed; {len(got['waiting'])} waiting"
        )
    return kernel.ESCALATE if got["waiting"] else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
