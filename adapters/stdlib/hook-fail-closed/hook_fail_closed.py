"""hook_fail_closed.py: a hook that breaks blocks the tool, never lets it run. Python 3.9+.

    python adapters/stdlib/hook-fail-closed/hook_fail_closed.py --hook "COMMAND" [--timeout S] [--json]

Claude Code, Gemini CLI, Codex and Cursor all let a tool run when its hook
crashes, times out or prints what they can't read: the check that was meant
to stop it says nothing, and the tool goes ahead. Put this in front of the
hook instead. It hands the hook what the assistant sent on standard input,
waits at most --timeout seconds (30 unless said), and then:

    the hook exits 0                 its output, passed through: allowed
    the hook exits 2                 its reason, passed through: blocked
    any other exit, a crash, a
      timeout, or it won't start     blocked, and the reason said
    --json, and its output isn't     blocked: an assistant can't read it
      JSON (empty output is fine)

Exit 2 is how every one of those assistants says block. COMMAND is one
string, split the way a shell splits words (quotes hold), and run without a
shell. It reads nothing else and writes nothing. Exit codes: 0 allowed; 2
blocked, or a bad command line.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TIMEOUT = 30.0


def guard(
    argv: list[str], data: bytes, timeout: float, want_json: bool
) -> tuple[int, bytes, str]:
    """(exit code, what to print, why it blocked or ""): 0 only when the hook
    said yes in a way the assistant can read."""
    try:
        p = subprocess.run(argv, input=data, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return kernel.REFUSED, b"", f"blocked: the hook ran past {timeout:g}s"
    except OSError as e:
        return kernel.REFUSED, b"", f"blocked: the hook won't start: {e.strerror or e}"
    if p.returncode == 2:
        return kernel.REFUSED, p.stderr, ""
    if p.returncode != 0:
        why = "it was killed" if p.returncode < 0 else f"it exited {p.returncode}"
        return kernel.REFUSED, p.stderr, f"blocked: the hook broke, {why}"
    if want_json and p.stdout.strip():
        try:
            json.loads(p.stdout)
        except ValueError:
            return kernel.REFUSED, b"", "blocked: the hook's output isn't JSON"
    return kernel.ALIVE, p.stdout, ""


def main(argv: list[str]) -> int:
    opts, want_json, it, bad = {}, False, iter(argv), False
    for a in it:
        if a in ("--hook", "--timeout"):
            opts[a] = next(it, "")
        elif a == "--json":
            want_json = True
        else:
            bad = True
    try:
        cmd = shlex.split(opts.get("--hook", ""))
        timeout = float(opts.get("--timeout", TIMEOUT))
    except ValueError:
        cmd, timeout = [], 0.0
    if bad or not cmd or not timeout > 0:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    code, out, why = guard(cmd, sys.stdin.buffer.read(), timeout, want_json)
    stream = sys.stdout.buffer if code == kernel.ALIVE else sys.stderr.buffer
    stream.write(out)
    stream.flush()
    if why:
        print(why, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
