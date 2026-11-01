"""weakest_link.py: each approved answer worth its weakest cited input.

    python adapters/stdlib/weakest-link/weakest_link.py --box DIR

A passage says what it rests on with a line such as `provenance: measured`,
`provenance: fitted` or `provenance: assumed` (or `=` for `:`, in any case).
Those are states, not a score:

    measured   it traces to something a person can look up
    fitted     a model calibrated against measured values
    assumed    someone asserted it; nothing has checked it

An approved answer is worth the weakest state among the passages it cites,
never an average. One assumed input and the whole answer is assumed, however
many measured ones sit beside it. A cited passage that says none is
`unmarked`, and so is any answer that cites one. That is recorded as its own
value, never quietly read as assumed: no claim is a different fact from a weak
one. A passage marked twice is worth the weaker mark. An approval that cites
no passage at all, such as session-seal's summary of what you did, is
`cites-nothing`: shown and counted, never escalated, because it makes no
claim about your folder for an input to be weak in.

    assumed  proposal:0a6fde95…  'Six hours.'
             assumed   garden.md:1   <- the weakest: fix this first
             measured  sun.md:3
    1 approved: 0 measured, 0 fitted, 1 assumed, 0 unmarked, 0 cites-nothing

Exit codes, the kernel's: 0 every approval that cites anything is measured
(or there are none); 42 an approval rests on something weaker, or unmarked,
or its cited passage is gone, or its proposal is broken, and that waits on
you; 2 refused (a record that doesn't verify).

It only reads: the record, the approved suggestions, your folder. It writes
nothing, marks nothing, and never takes an approval back.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

STATES = ("assumed", "fitted", "measured")  # weakest first, so min() is the rule
MARK = re.compile(r"\bprovenance\s*[:=]\s*(measured|fitted|assumed)\b", re.I)
UNMARKED, GONE, UNCITED = "unmarked", "gone", "cites-nothing"


def state_of(text: str) -> str:
    """The weakest state a passage marks itself with, or `unmarked`."""
    found = [m.lower() for m in MARK.findall(text)]
    return min(found, key=STATES.index) if found else UNMARKED


def worth(states: list[str]) -> str:
    """An answer's worth: the weakest of its cited states. Anything gone or
    unmarked means the answer makes no provenance claim at all."""
    if not states:
        return UNCITED  # rests on no passage: not a claim about the folder at all
    if GONE in states or UNMARKED in states:
        return UNMARKED
    return min(states, key=STATES.index)


def check(box: Path) -> tuple[int, list[dict]]:
    """(exit code, one entry per approval, in the order they were sealed)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return kernel.REFUSED, [{"refused": b} for b in breaks]
    here = {c["id"]: c for c in kernel.chunks(Path(kernel.config(box)["pile"]))}
    out = []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            out.append({"subject": subj, "broken": why, "row": row["n"]})
            continue
        cites = []
        for c in prop["cites"]:
            got = here.get(c)
            cites.append({"id": c, "state": state_of(got["text"]) if got else GONE,
                          "where": f"{got['path']}:{got['line']}" if got else "?"})  # fmt: skip
        out.append({"subject": subj, "data": prop["data"], "row": row["n"],
                    "cites": cites, "worth": worth([c["state"] for c in cites])})  # fmt: skip
    weak = any("broken" in e or e["worth"] not in ("measured", UNCITED) for e in out)
    return (kernel.ESCALATE if weak else kernel.ALIVE), out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    code, entries = check(box)
    tally = {s: 0 for s in (*reversed(STATES), UNMARKED, UNCITED)}
    broken = 0
    for e in entries:
        if "refused" in e:
            print(f"refused: {e['refused']}", file=sys.stderr)
            continue
        if "broken" in e:
            broken += 1
            print(
                f"{'broken':<8} {e['subject'][:21]}…  its proposal file {e['broken']}"
            )
            continue
        tally[e["worth"]] += 1
        quote = e["data"] if len(e["data"]) <= 60 else e["data"][:57] + "..."
        print(f"{e['worth']:<8} {e['subject'][:21]}…  {quote!r}")
        rank = {s: i for i, s in enumerate((GONE, UNMARKED, *STATES))}
        low = min((rank[c["state"]] for c in e["cites"]), default=None)
        for c in sorted(e["cites"], key=lambda c: (rank[c["state"]], c["where"])):
            flag = (
                "   <- the weakest: fix this first"
                if rank[c["state"]] == low and e["worth"] != "measured"
                else ""
            )
            where = (
                c["where"]
                if c["state"] != GONE
                else f"{c['id'][:12]}, no longer in your folder"
            )
            print(f"         {c['state']:<9} {where}{flag}")
    if code != kernel.REFUSED:
        print(f"{len(entries)} approved: " + ", ".join(f"{n} {s}" for s, n in tally.items())
              + (f"; {broken} broken" if broken else ""))  # fmt: skip
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
