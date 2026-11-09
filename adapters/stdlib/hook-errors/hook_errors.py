"""hook_errors.py: each failed command an assistant runs kept as a row of
its hash and exit code, so the same failure the third time is named, not
retried blind. Python 3.9+.

    python adapters/stdlib/hook-errors/hook_errors.py run --box DIR [--now TS]
    python adapters/stdlib/hook-errors/hook_errors.py check --box DIR

`run` is both a PreToolUse and a PostToolUse hook for shell tools (Bash,
Shell, run_terminal_cmd). It reads the JSON Claude Code, Gemini CLI and
Cursor send on standard input:

    PostToolUse (an exit code is present)
        a non-zero exit appends a `hook-errors` row (command hash, exit,
        and the call's `session_id` when sent), never the command's words,
        which can carry the person's (CONST-VI-8). The call is allowed;
        recording never blocks.

    PreToolUse (no exit code yet)
        if this session already has two rows for the same command hash and
        the same exit, the third try is blocked: exit 2, and a reason that
        names the exit and the last row. Otherwise allowed; nothing written.

    anything else
        allowed; the hook writes nothing.

`check` is the same look for a person: each (command hash, exit) that has
failed at least once is listed by its hash and last row; exit 42 when any
has reached the block rung (two or more).

It never reads the key. Exit codes: 0 allowed (or `check` none at the
block rung); 42 `check` found a repeated failure; 2 refused or blocked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-errors"
BLOCK_AT = 2  # two prior same (hash, exit) → third attempt blocked
SHELL = {"Bash", "Shell", "run_terminal_cmd"}


def session_of(call: dict) -> str:
    s = call.get("session_id")
    return s if isinstance(s, str) else ""


def command_of(call: dict) -> str | None:
    given = call.get("tool_input")
    if not isinstance(given, dict):
        return None
    c = given.get("command")
    return c if isinstance(c, str) and c else None


def exit_of(call: dict) -> int | None:
    """The tool's exit code when this is a PostToolUse shape, else None."""
    raw = call.get("exit_code")
    if isinstance(raw, int):
        return raw
    for key in ("tool_response", "response"):
        r = call.get(key)
        if isinstance(r, dict):
            for f in ("exit_code", "exitCode"):
                v = r.get(f)
                if isinstance(v, int):
                    return v
    return None


def counts(rows: list[dict], session: str, digest: str) -> dict[int, tuple[int, int]]:
    """exit → (times, last row n) for this session and command hash."""
    out: dict[int, tuple[int, int]] = {}
    for r in rows:
        if (
            r["kind"] != KIND
            or r.get("session", "") != session
            or r.get("cmd_sha256") != digest
        ):
            continue
        code = r["exit"]
        n, _ = out.get(code, (0, 0))
        out[code] = (n + 1, r["n"])
    return out


def block_reason(rows: list[dict], session: str, digest: str) -> str:
    """Why to block, or "" when the third try hasn't been reached."""
    for code, (times, last) in sorted(counts(rows, session, digest).items()):
        if times >= BLOCK_AT:
            return (
                f"blocked: this command has failed {times} times with exit "
                f"{code} (last at row {last}); look at those before trying again"
            )
    return ""


def judge(raw: str, box: Path, ts: str) -> tuple[int, str]:
    """(exit code, reason on stderr) for what a hook was sent."""
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
        )
    if call.get("tool_name") not in SHELL:
        return 0, ""
    command = command_of(call)
    if command is None:
        return 0, ""
    digest = kernel.h256(command)
    code = exit_of(call)
    if code is not None:
        if code == 0:
            return 0, ""
        kernel.append(
            box,
            ts,
            KIND,
            who="hook-errors",
            cmd_sha256=digest,
            exit=code,
            session=session_of(call),
        )
        return 0, ""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return 2, "refused: the record doesn't verify: " + "; ".join(breaks)
    why = block_reason(rows, session_of(call), digest)
    return (2, why) if why else (0, "")


def listed(rows: list[dict]) -> list[tuple[str, int, int, int]]:
    """(cmd_sha256, exit, times, last n) for every failure group. A row
    made before the record stopped keeping a command's text still holds it;
    it is never shown."""
    groups: dict[tuple[str, int], tuple[int, int]] = {}
    for r in rows:
        if r["kind"] != KIND:
            continue
        key = (r["cmd_sha256"], r["exit"])
        n, _ = groups.get(key, (0, 0))
        groups[key] = (n + 1, r["n"])
    out = [
        (digest, code, times, last) for (digest, code), (times, last) in groups.items()
    ]
    return sorted(out, key=lambda t: (-t[2], t[0], t[1]))


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
    items = listed(rows)
    for digest, code, times, last in items:
        print(f"exit {code}  {times} times  {digest}  (last at row {last})")
    return (
        kernel.ESCALATE
        if any(times >= BLOCK_AT for _, _, times, _ in items)
        else kernel.ALIVE
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
