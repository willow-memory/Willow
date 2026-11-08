"""hook_feedback.py: your corrections to an assistant (no, wrong, I said)
caught by fixed patterns at each prompt and handed in through propose, for
you to keep or drop. Python 3.9+.

    python adapters/stdlib/hook-feedback/hook_feedback.py run --box DIR [--now TS]
    python adapters/stdlib/hook-feedback/hook_feedback.py check --box DIR

`run` is a UserPromptSubmit hook. It reads the JSON Claude Code, Gemini CLI
and Cursor send on standard input. When the prompt matches a fixed
correction pattern (`no`, `wrong`, or `I said` as a word), it bites that
text and proposes it under `feedback/<hash>.md` with an empty cite list, so
you can seal or decline it. Other prompts, and events that aren't
UserPromptSubmit, are left alone. It prints nothing on stdout (a prompt
hook that adds context would change the turn); the proposal waits on the
record.

`check` lists each waiting `hook-feedback` proposal still on the box (not
yet sealed or declined); exit 42 when any wait, 0 when none.

It never reads the key. Exit codes: 0 allowed (or `check` none waiting);
42 `check` found waiting feedback; 2 refused.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-feedback"
GIVE = {"UserPromptSubmit", "user_prompt_submit"}
# Fixed patterns named in the idea: a correction, not a new ask.
MARKERS = (
    re.compile(r"(?i)^\s*no\b"),
    re.compile(r"(?i)^\s*wrong\b"),
    re.compile(r"(?i)\bi said\b"),
)


def quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def prompt_of(call: dict) -> str | None:
    for f in ("prompt", "user_prompt", "text"):
        v = call.get(f)
        if isinstance(v, str) and v.strip():
            return v
    return None


def event_of(call: dict) -> str:
    e = call.get("hook_event_name") or call.get("hookEventName") or ""
    return e if isinstance(e, str) else ""


def is_correction(text: str) -> bool:
    return any(p.search(text) for p in MARKERS)


def waiting(box: Path, rows: list[dict]) -> list[dict]:
    """hook-feedback proposal rows still waiting (not sealed, not declined)."""
    sealed = set(kernel.sealed(box, rows)) | set(kernel.declined(box, rows))
    out = []
    for r in rows:
        if r["kind"] != KIND:
            continue
        subj = r.get("subject")
        if isinstance(subj, str) and subj not in sealed:
            out.append(r)
    return out


def hand_in(box: Path, text: str, ts: str) -> tuple[int, str]:
    """Bite and propose the correction; (exit, stderr reason)."""
    code, said = quiet(kernel.bite, box, text, ts)
    if code == kernel.REFUSED:
        return 2, f"refused: the kernel wouldn't take the bite: {said.strip()}"
    digest = kernel.h256(text)[:12]
    prop = {
        "path": f"feedback/{digest}.md",
        "data": text,
        "cites": [],
        "claim": "correction caught by hook-feedback",
    }
    code, said = quiet(kernel.propose, box, [json.dumps(prop)], ts)
    if code != kernel.ESCALATE or "pass" not in said:
        return 2, f"refused: the kernel's door: {said.strip()}"
    subj = kernel.subject_of(prop)
    kernel.append(box, ts, KIND, who="hook-feedback", subject=subj, path=prop["path"])
    return 0, ""


def judge(raw: str, box: Path, ts: str) -> tuple[int, str]:
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
        )
    if event_of(call) not in GIVE:
        return 0, ""
    text = prompt_of(call)
    if text is None or not is_correction(text):
        return 0, ""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return 2, "refused: the record doesn't verify: " + "; ".join(breaks)
    return hand_in(box, text, ts)


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
        code, why = judge(sys.stdin.read(), box, opts.get("--now") or kernel.now())
        if why:
            print(why, file=sys.stderr)
        return code
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    found = waiting(box, rows)
    if not found:
        print("no feedback waiting")
        return kernel.ALIVE
    for r in found:
        print(f"waiting  {r['subject']}  {r.get('path', '')}  (row {r['n']})")
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
