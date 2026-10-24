"""hook_fuzz.py: throws bad input at a hook and names each one that breaks it. Python 3.9+.

    python adapters/stdlib/hook-fuzz/hook_fuzz.py --hook "COMMAND" [--timeout S]

A hook's docstring can say it fails closed and still crash on input nobody
tried, and in Claude Code a crashed hook lets the tool run. This hands the
hook a fixed list of inputs an assistant could send, or could send by
mistake, one at a time on standard input:

    empty            nothing at all
    blank            spaces and a newline
    null, list,      JSON that isn't an object: null, [], 5
      number
    object           {} with no fields
    truncated        an object cut off halfway
    wrong-type       {"prompt": 5}, a number where text goes
    huge             a prompt of a million characters
    not-utf8         bytes that aren't UTF-8
    nul              a NUL in the middle of the prompt
    surrogate        a lone surrogate, \\ud800, escaped in the JSON
    deep             JSON nested ten thousand lists deep

A hook holds when it exits 0 or 2 (allowed, or blocked on purpose) within
--timeout seconds (10 unless said) with no Python traceback. Anything else
is a break: another exit code, a crash, a timeout, or a traceback even under
exit 0, since that is a hook getting lucky. The list is fixed, so the same
hook gets the same verdict every run.

COMMAND is one string, split as a shell splits words, and run without a
shell. It writes nothing. Exit codes, the kernel's: 0 every input held; 42
one broke it, each named; 2 a bad command line.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TIMEOUT = 10.0
EVENT = {"hook_event_name": "UserPromptSubmit", "session_id": "fuzz"}


def ask(prompt) -> bytes:
    return json.dumps({**EVENT, "prompt": prompt}).encode()


CASES: list[tuple[str, bytes]] = [
    ("empty", b""),
    ("blank", b"  \n"),
    ("null", b"null"),
    ("list", b"[]"),
    ("number", b"5"),
    ("object", b"{}"),
    ("truncated", ask("how are the bees")[:20]),
    ("wrong-type", ask(5)),
    ("huge", ask("bees " * 200_000)),
    ("not-utf8", b'{"prompt": "\xff\xfe bees"}'),
    ("nul", ask("bees\x00calm")),
    ("surrogate", b'{"prompt": "bees \\ud800"}'),
    ("deep", b"[" * 10_000 + b"]" * 10_000),
]


def verdict(argv: list[str], data: bytes, timeout: float) -> str:
    """What broke the hook on `data`, or an empty string when it held."""
    try:
        p = subprocess.run(argv, input=data, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"ran past {timeout:g}s"
    except OSError as e:
        return f"won't start: {e.strerror or e}"
    if b"Traceback (most recent call last)" in p.stderr:
        last = p.stderr.decode("utf-8", "replace").strip().splitlines()[-1]
        return f"exited {p.returncode} with a traceback: {last}"
    if p.returncode not in (0, 2):
        return "was killed" if p.returncode < 0 else f"exited {p.returncode}"
    return ""


def main(argv: list[str]) -> int:
    opts, it, bad = {}, iter(argv), False
    for a in it:
        if a in ("--hook", "--timeout"):
            opts[a] = next(it, "")
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
    broke = [
        (name, why) for name, data in CASES if (why := verdict(cmd, data, timeout))
    ]
    for name, why in broke:
        print(f"broke  {name:<11} {why}")
    held = len(CASES) - len(broke)
    print(f"{held} of {len(CASES)} inputs held")
    return kernel.ESCALATE if broke else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
