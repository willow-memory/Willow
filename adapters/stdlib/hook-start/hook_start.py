"""hook_start.py: a SessionStart hook that hands the assistant what needs
the person. Python 3.9+.

    python adapters/stdlib/hook-start/hook_start.py --box DIR [--days N] [--now TS]

When a session opens, the assistant is told what the box is waiting on, read
the way [digest](../digest/) reads it: the suggestions that passed the door
and wait for the person's approval, the approved answers whose source went
stale, and the dates coming up in the next N days (14 unless --days says).
What it prints is the JSON an assistant's SessionStart hook reads, and its
`additionalContext` is plain sentences:

    The person's willow box has 2 suggestions waiting for their approval. Say
    so when it fits; only the person approves, and an assistant never does.
      - Six hours of sun. (why: the garden notes)
    1 approved answer is stale: its source changed or went.
    Coming up: 2026-11-02 garden.md:4  Frost warning

Nothing to say prints nothing at all, so a quiet box adds nothing to the
session. A section the digest couldn't look at is left out, not guessed at.
The record keeps no question's words, so neither does this; a suggestion is
shown by its answer and its reason, as `digest` shows it.

It writes nothing, not even the row `kernel.py out` appends, so opening a
session never moves the record's tip. It never reads the key, and it says
nothing to approve: the line the assistant is given is a fact, not a command.

Exit codes: 0 printed (or nothing to say); 2 refused (a record that doesn't
verify, a bad command line). A hook should fail open here: a refusal prints
its reason on standard error and adds nothing to the session.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "digest"))
import digest  # noqa: E402
import kernel  # noqa: E402

SHOWN = 5  # items listed per section; the count says the rest


def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def context(doc: dict, days: int) -> str:
    """The sentences for the assistant, or "" when nothing needs the person."""
    lines = []
    waiting = doc["waiting"]
    if waiting["state"] == digest.POPULATED:
        items = waiting["items"]
        lines.append(
            f"The person's willow box has {plural(len(items), 'suggestion', 'suggestions')} waiting "
            "for their approval. Say so when it fits; only the person approves, and an assistant never does."
        )
        for w in items[:SHOWN]:
            lines.append(
                f"  - {digest.short(w['answer'], 80)} (why: {digest.short(w['why'], 60)})"
            )
        if len(items) > SHOWN:
            lines.append(f"  - and {len(items) - SHOWN} more")
    stale = doc["stale"]
    if stale["state"] == digest.POPULATED:
        n = len(stale["items"])
        lines.append(
            f"{plural(n, 'approved answer is', 'approved answers are')} stale: its source changed or went."
        )
    coming = doc["coming"]
    if coming["state"] == digest.POPULATED:
        for c in coming["items"][:SHOWN]:
            lines.append(
                f"Coming up (next {days} days): {c['date']} {c['where']}  {digest.short(c['line'], 80)}"
            )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days", "14")
    if not opts.get("--box") or args or not days.isdigit():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    doc = digest.digest(box, today, int(days))
    if "refused" in doc:
        print(f"refused: {doc['refused']}", file=sys.stderr)
        return kernel.REFUSED
    text = context(doc, int(days))
    if text:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": text,
            }
        }
        print(json.dumps(out, ensure_ascii=False))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
