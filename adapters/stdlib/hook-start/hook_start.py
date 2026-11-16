"""hook_start.py: a SessionStart hook that hands the assistant what needs
the person. Python 3.9+.

    python adapters/stdlib/hook-start/hook_start.py --box DIR [--days N | --no-dates] [--now TS]

When a session opens, the assistant is told what the box is waiting on, read
the way [digest](../digest/) reads it: the suggestions that passed the door
and wait for the person's approval, the approved answers whose source went
stale, and the dates coming up in the next N days (14 unless --days says).
`--no-dates` leaves the dates out, unread: on a pile of records (notes,
commits, code) every line dated today is a record of the day, not an
appointment, and reading a big pile's dates is most of the time.
What it prints is the JSON an assistant's SessionStart hook reads, and its
`additionalContext` is digest's report under this add-on's name (the report
contract, adapters/stdlib/ci/README.md), then whose it is, and who approves
when a suggestion waits:

    hook-start: populated, 1 waiting, 1 gone stale, 1 coming up
    ## Waiting for you
      proposal:f391…a7ff  30 October (why: the note)
    ## Gone stale
      bins.txt:1          Thursday night
    ## Coming up (next 14 days)
      car.txt:1           2026-10-30  The car insurance renews on 2026-10-30.

    That is what the person's willow box is waiting on. Say so when it fits;
    only the person approves, and an assistant never does.

Its standard output is the hook's JSON, not a report: a quiet box (an empty
or unreachable report) prints nothing at all, so it adds nothing to the
session, and it exits 0 whatever it found, since a SessionStart hook that
exits 42 has its output dropped. A section the digest couldn't look at is
said on the first line, not guessed at. Up to five rows of a group are
listed and the rest counted; questions asked again are left to the digest.
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

NAME = "hook-start"
SHOWN = 5  # rows listed per group; the last row counts the rest
#: said after the report: whose it is, and, when a suggestion waits, who approves
WHOSE = "That is what the person's willow box is waiting on."
APPROVES = (
    " Say so when it fits; only the person approves, and an assistant never does."
)


def context(doc: dict, days: int) -> str:
    """digest's report under this add-on's name, for the assistant, or ""
    when nothing needs the person."""
    rep = digest.report_of(
        {**doc, "again": {"state": digest.EMPTY, "items": []}}, days, NAME
    )
    if rep["state"] != digest.POPULATED:
        return ""
    for g in rep["groups"]:
        if len(g["rows"]) > SHOWN:
            more = len(g["rows"]) - SHOWN
            g["rows"] = g["rows"][:SHOWN] + [{"where": "…", "what": f"and {more} more"}]
    text = digest.report_text(rep)
    return f"{text}\n\n{WHOSE}{APPROVES if doc['waiting']['items'] else ''}"


def without_dates(box: Path) -> dict:
    """digest's sections with coming-up left out and the pile's dates never
    read, or {"refused": why} for a record that doesn't verify."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {"refused": "; ".join(breaks)}
    return {
        "waiting": digest.waiting(box, rows),
        "stale": digest.gone_stale(box),
        "coming": digest.section([]),
        "again": digest.section([]),
    }


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days", "--now"):
            opts[a] = next(it, "")
        elif a == "--no-dates":
            opts[a] = "yes"
        else:
            args.append(a)
    days = opts.get("--days", "14")
    undated = "--no-dates" in opts
    if (
        not opts.get("--box")
        or args
        or not days.isdigit()
        or (undated and "--days" in opts)
    ):
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
    doc = without_dates(box) if undated else digest.digest(box, today, int(days))
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
