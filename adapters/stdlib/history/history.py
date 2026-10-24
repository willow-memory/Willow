"""history.py: your record, in plain sentences. Python 3.9+.

    python adapters/stdlib/history/history.py --box DIR [--days N] [--now TS]

Each row of the record, oldest first, said as what happened, by day:

    2026-10-24
      09:12  You started your record.
      09:13  You asked a question. Your files held it: dentist.txt:1.
      09:14  You asked a question again (2nd time). Nothing in your folder held it.
      09:20  A suggestion was handed in for dentist.md. It waits for you.
      09:21  You approved the suggestion for dentist.md.

The record keeps no words, so neither does this: a question is told apart
from another by its fingerprint, which is how "again" is known, and an
answer by the places it came from. What you approved is named by the file
it writes, never by its text. With --days, only the last N days, counted
back from --now (today unless given).

It reads the record and nothing else of yours, and writes nothing. A record
that doesn't verify is refused: a history read past a break could tell you
something that didn't happen.

Exit codes, the kernel's: 0 told; 42 nothing in the window; 2 refused.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def nth(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def places(served: list[dict], most: int = 3) -> str:
    where = [s["where"] for s in served if not s.get("echo")]
    shown = ", ".join(where[:most])
    return shown + (f" and {len(where) - most} more" if len(where) > most else "")


def proposal_path(box: Path, subject: str) -> str:
    try:
        prop = json.loads((box / "proposals" / f"{subject[9:]}.json").read_text())
        return str(prop.get("path") or "an answer")
    except (OSError, ValueError):
        return "an answer"


def sentences(box: Path, rows: list[dict]) -> list[tuple[str, str]]:
    """(timestamp, sentence) for each row, oldest first."""
    asked: dict[str, int] = {}
    out = []
    for r in rows:
        kind = r["kind"]
        if kind == "boot":
            said = "You started your record."
        elif kind == "bite":
            k = r.get("bite_key", "")
            asked[k] = asked.get(k, 0) + 1
            again = f" again ({nth(asked[k])} time)" if asked[k] > 1 else ""
            if r.get("answered_by"):
                what = proposal_path(box, r["answered_by"])
                said = f"You asked a question{again}. Your approved answer for {what} answered it."
            elif any(not s.get("echo") for s in r.get("served", [])):
                said = f"You asked a question{again}. Your files held it: {places(r['served'])}."
            elif r.get("served"):
                said = f"You asked a question{again}. Your files only asked it back."
            else:
                said = f"You asked a question{again}. Nothing in your folder held it."
        elif kind == "proposal":
            if r.get("verdict") == "pass":
                what = proposal_path(box, r.get("subject", ""))
                said = f"A suggestion was handed in for {what}. It waits for you."
            else:
                said = f"A suggestion was turned away at the door: {r.get('why', 'no reason kept')}."
        elif kind == "seal":
            said = f"You approved the suggestion for {proposal_path(box, r.get('subject', ''))}."
        elif kind == "decline":
            said = f"You turned down the suggestion for {proposal_path(box, r.get('subject', ''))}."
        elif kind == "out":
            n = r.get("waiting", 0)
            said = ("You looked at what was waiting: "
                    + (f"{n} suggestion{'s' if n != 1 else ''}." if n else "nothing."))  # fmt: skip
        elif kind == "changed" and r.get("first"):
            n = len(r.get("files", {}))
            said = f"You fingerprinted your folder: {n} file{'s' if n != 1 else ''}."
        elif kind == "changed":
            counts = [(len(r.get(k, [])), k) for k in ("new", "edited", "deleted")]
            said = (
                "You checked what changed in your folder: "
                + (", ".join(f"{n} {k}" for n, k in counts if n) or "nothing had")
                + "."
            )
        else:
            said = f"A {kind} row, written by {r.get('who', 'something')}."
        out.append((str(r.get("ts", "")), said))
    return out


def tell(lines: list[tuple[str, str]]) -> str:
    out, day = [], None
    for ts, said in lines:
        if ts[:10] != day:
            day = ts[:10]
            out.append(("" if not out else "\n") + (day or "undated"))
        out.append(f"  {ts[11:16] or '--:--'}  {said}")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days")
    if not opts.get("--box") or args or (days is not None and not days.isdigit()):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    lines = sentences(box, rows)
    if days is not None:
        ts = opts.get("--now") or kernel.now()
        try:
            today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
        except ValueError:
            print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
            return kernel.REFUSED
        since = (today - timedelta(days=int(days))).isoformat()
        lines = [(t, s) for t, s in lines if t[:10] > since]
    if not lines:
        print("Nothing on the record in that window.")
        return kernel.ESCALATE
    print(tell(lines), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
