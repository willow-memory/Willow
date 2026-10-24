"""hook_pin.py: a hook runs only as the bytes you approved. Python 3.9+.

    python adapters/stdlib/hook-pin/hook_pin.py --box DIR approve FILE... [--now TS]
    python adapters/stdlib/hook-pin/hook_pin.py --box DIR check FILE...
    python adapters/stdlib/hook-pin/hook_pin.py --box DIR run --file FILE --hook "COMMAND"

A hook is a program that runs on every prompt or tool call, and a hook file
can change after you looked at it: an update, a merge, a tool rewriting its
own settings. `approve` writes one `hook-pin` row through the kernel's own
append for each FILE: where it is and the SHA-256 of its bytes. Approving
again after a change writes a new row; the old one stays on the record.

`check` holds each FILE to its latest pin:

    pinned           the same bytes you approved (the row is named)
    changed          different bytes since the row named
    never pinned     no row for it

`run` is the gate. FILE, the hook's own file, must be pinned and unchanged,
or nothing runs and the tool is blocked (exit 2) with the reason. When it
holds, COMMAND (split as a shell splits words, run without a shell) gets
standard input, and its output and exit code pass through, so it can stand
where the hook stood in settings.json.

It never reads the key. Exit codes, the kernel's: 0 approved, every file
pinned, or the hook's own 0; 42 a file changed or was never pinned; 2
refused, blocked, or the hook's own 2.
"""

from __future__ import annotations

import hashlib
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-pin"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins(rows: list[dict]) -> dict[str, dict]:
    """Each place's latest pin row."""
    return {r["path"]: r for r in rows if r["kind"] == KIND}


def state(path: Path, latest: dict[str, dict]) -> tuple[str, str]:
    """(pinned | changed | never pinned, what to say)."""
    row = latest.get(str(path.resolve()))
    if row is None:
        return "never pinned", f"never pinned  {path}"
    if row["sha256"] != sha(path):
        return "changed", f"changed       {path} (pinned at row {row['n']})"
    return "pinned", f"pinned        {path} (row {row['n']})"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--hook", "--file"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            args = []
            break
        else:
            args.append(a)
    else:
        a = None
    verb = args[0] if args else ""
    try:
        cmd = shlex.split(opts.get("--hook", ""))
    except ValueError:
        cmd = []
    ok = (
        bool(opts.get("--box"))
        and a is None
        and (
            (
                verb in ("approve", "check")
                and len(args) > 1
                and not {"--hook", "--file"} & set(opts)
            )
            or (verb == "run" and len(args) == 1 and cmd and opts.get("--file"))
        )
    )
    if not ok:
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
    if verb == "run":
        hook = Path(opts["--file"])
        if not hook.is_file():
            print(f"blocked: not a file: {hook}", file=sys.stderr)
            return kernel.REFUSED
        said = state(hook, pins(rows))
        if said[0] != "pinned":
            print(f"blocked: {said[1]}", file=sys.stderr)
            return kernel.REFUSED
        try:
            p = subprocess.run(cmd, input=sys.stdin.buffer.read(), capture_output=True)
        except OSError as e:
            print(f"blocked: the hook won't start: {e.strerror or e}", file=sys.stderr)
            return kernel.REFUSED
        sys.stdout.buffer.write(p.stdout)
        sys.stderr.buffer.write(p.stderr)
        return p.returncode
    files = [Path(f) for f in args[1:]]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print(f"refused: not a file: {', '.join(missing)}", file=sys.stderr)
        return kernel.REFUSED
    if verb == "approve":
        ts = opts.get("--now") or kernel.now()
        for f in files:
            row = kernel.append(box, ts, KIND, who="hook-pin",
                                path=str(f.resolve()), sha256=sha(f))  # fmt: skip
            print(f"pinned        {f} (row {row['n']})")
        return kernel.ALIVE
    said = [state(f, pins(rows)) for f in files]
    for _, line in said:
        print(line)
    return kernel.ALIVE if all(s == "pinned" for s, _ in said) else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
