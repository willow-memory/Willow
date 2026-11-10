"""hook_handoff.py: a Stop hook that writes where the session ended, and the
next session's first prompt gets it back, so nothing rides on the
assistant's memory. Python 3.9+.

    python adapters/stdlib/hook-handoff/hook_handoff.py run --box DIR [--now TS]
    python adapters/stdlib/hook-handoff/hook_handoff.py check --box DIR

`run` reads the JSON Claude Code, Gemini CLI and Cursor send on standard
input and branches on the hook event:

    Stop
        appends a `hook-handoff` row (cwd, session_id, and transcript path
        when sent). When `stop_hook_active` is true the turn was already
        stopped once this round, so nothing is written (same escape as
        hook-stop). Allowed either way.

    SessionStart, UserPromptSubmit
        the latest handoff from a *different* session is printed as the
        hook's JSON `additionalContext`, once per new session (a
        `hook-handoff` served row marks it). Same session as the handoff,
        or none yet: prints nothing. Exit 0 always here: a SessionStart
        that exits non-zero has its context dropped.

    anything else
        allowed; nothing written or printed.

`check` is the same look for a person: the latest handoff line, or `no
handoff yet` (exit 42 when none).

It never reads the key. Exit codes: 0 allowed (or `check` has a handoff);
42 `check` found none; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-handoff"
SERVED = "hook-handoff-served"
STOP = {"Stop", "stop"}
GIVE = {"SessionStart", "UserPromptSubmit", "session_start", "user_prompt_submit"}


def session_of(call: dict) -> str:
    s = call.get("session_id")
    return s if isinstance(s, str) else ""


def cwd_of(call: dict) -> str:
    c = call.get("cwd")
    return c if isinstance(c, str) and c else ""


def transcript_of(call: dict) -> str:
    for f in ("transcript_path", "transcriptPath"):
        t = call.get(f)
        if isinstance(t, str) and t:
            return t
    return ""


def event_of(call: dict) -> str:
    e = call.get("hook_event_name") or call.get("hookEventName") or ""
    return e if isinstance(e, str) else ""


def latest_handoff(rows: list[dict]) -> dict | None:
    for r in reversed(rows):
        if r["kind"] == KIND:
            return r
    return None


def already_served(rows: list[dict], session: str, handoff_n: int) -> bool:
    for r in rows:
        if (
            r["kind"] == SERVED
            and r.get("session", "") == session
            and r.get("handoff_n") == handoff_n
        ):
            return True
    return False


def context_line(row: dict) -> str:
    where = row.get("cwd") or "(no cwd)"
    session = row.get("session") or "(no session)"
    return (
        f"hook-handoff: session {session} ended in {where} (row {row['n']}). "
        "Pick up from there; do not invent where you left off."
    )


def judge(raw: str, box: Path, ts: str) -> tuple[int, str, str]:
    """(exit, stderr reason, stdout body)."""
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
            "",
        )
    event = event_of(call)
    if event in STOP:
        if call.get("stop_hook_active") is True:
            return 0, "", ""
        kernel.append(
            box,
            ts,
            KIND,
            who="hook-handoff",
            session=session_of(call),
            cwd=cwd_of(call),
            transcript=transcript_of(call),
        )
        return 0, "", ""
    if event not in GIVE:
        return 0, "", ""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return 2, "refused: the record doesn't verify: " + "; ".join(breaks), ""
    row = latest_handoff(rows)
    session = session_of(call)
    if row is None or row.get("session", "") == session:
        return 0, "", ""
    if already_served(rows, session, row["n"]):
        return 0, "", ""
    kernel.append(
        box,
        ts,
        SERVED,
        who="hook-handoff",
        session=session,
        handoff_n=row["n"],
    )
    body = json.dumps({"additionalContext": context_line(row)}, ensure_ascii=False)
    return 0, "", body + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            args = []
            break
        else:
            args.append(a)
    verb = args[0] if args else ""
    if not opts.get("--box") or verb not in ("run", "check") or len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if verb == "run":
        code, why, out = judge(sys.stdin.read(), box, opts.get("--now") or kernel.now())
        if why:
            print(why, file=sys.stderr)
        if out:
            sys.stdout.write(out)
        return code
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    row = latest_handoff(rows)
    if row is None:
        print("no handoff yet")
        return kernel.ESCALATE
    print(context_line(row))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
