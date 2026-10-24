"""hook_replay.py: every hook answer on the record, and each one run again. Python 3.9+.

    python adapters/stdlib/hook-replay/hook_replay.py --box DIR --to INPUTS run --hook "COMMAND" [--now TS]
    python adapters/stdlib/hook-replay/hook_replay.py --box DIR --from INPUTS check

A deterministic hook should answer the same input the same way every time;
`run` and `check` show whether it does. `run` stands where the hook stood:
it hands COMMAND (split as a shell splits words, run without a shell) what
the assistant sent on standard input, passes its output and exit code
through, and writes one `hook-replay` row through the kernel's own append:
the command, the SHA-256 of the input, of what the hook printed, and of
what it said on standard error, and its exit code. The record keeps no
words, so the input itself is saved under INPUTS as `<sha256>.in`, once.

`check` runs every `hook-replay` row's command again on its saved input and
compares the three hashes and the exit code:

    held          the same answer
    differs       another answer: the first such row is named
    not kept      the input isn't in INPUTS, or isn't the bytes the row
                  hashed; said, never skipped

It never reads the key. Exit codes, the kernel's: 0 the hook's own 0 for
`run`, every replay held for `check`; 42 a replay differs or an input
wasn't kept; 2 refused, or the hook's own 2.
"""

from __future__ import annotations

import hashlib
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-replay"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def answer(cmd: list[str], data: bytes) -> dict:
    """What the hook did with `data`, as hashes and an exit code."""
    try:
        p = subprocess.run(cmd, input=data, capture_output=True)
        out, err, code = p.stdout, p.stderr, p.returncode
    except OSError as e:
        out, err, code = b"", f"won't start: {e.strerror or e}".encode(), 127
    return {"stdout": out, "stderr": err, "exit": code,
            "said": {"output": h(out), "errors": h(err), "exit": code}}  # fmt: skip


def check(rows: list[dict], inputs: Path) -> tuple[list[str], int]:
    """(a line for each row that didn't hold, how many held)."""
    lines, held = [], 0
    for r in rows:
        if r["kind"] != KIND:
            continue
        kept = inputs / f"{r['input']}.in"
        if not kept.is_file() or h(kept.read_bytes()) != r["input"]:
            lines.append(f"not kept  row {r['n']}: its input isn't in {inputs}")
            continue
        again = answer(r["command"], kept.read_bytes())["said"]
        if again != r["said"]:
            what = [k for k in ("output", "errors", "exit") if again[k] != r["said"][k]]
            lines.append(f"differs   row {r['n']}: its {' and '.join(what)}")
            continue
        held += 1
    return lines, held


def main(argv: list[str]) -> int:
    opts, args, it, bad = {}, [], iter(argv), False
    for a in it:
        if a in ("--box", "--to", "--from", "--hook", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            bad = True
        else:
            args.append(a)
    try:
        cmd = shlex.split(opts.get("--hook", ""))
    except ValueError:
        cmd = []
    run_ok = args == ["run"] and cmd and opts.get("--to") and "--from" not in opts
    check_ok = (
        args == ["check"] and opts.get("--from") and not {"--to", "--hook"} & set(opts)
    )
    if bad or not opts.get("--box") or not (run_ok or check_ok):
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
    if check_ok:
        lines, held = check(rows, Path(opts["--from"]))
        for line in lines:
            print(line)
        print(f"{held} of {held + len(lines)} hook answers held")
        return kernel.ESCALATE if lines else kernel.ALIVE
    inputs = Path(opts["--to"])
    if not inputs.is_dir():
        print(f"refused: {inputs} is not a folder; make it first", file=sys.stderr)
        return kernel.REFUSED
    data = sys.stdin.buffer.read()
    got = answer(cmd, data)
    kept = inputs / f"{h(data)}.in"
    if not kept.exists():
        kept.write_bytes(data)
    kernel.append(box, opts.get("--now") or kernel.now(), KIND, who="hook-replay",
                  command=cmd, input=h(data), said=got["said"])  # fmt: skip
    sys.stdout.buffer.write(got["stdout"])
    sys.stderr.buffer.write(got["stderr"])
    return got["exit"]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
