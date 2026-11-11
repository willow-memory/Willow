"""stack_row.py: a stack's kept run put on your record as one row. Python 3.9+.

    python adapters/stdlib/stack-row/stack_row.py --box DIR --run FOLDER [--now TS]

A stack run with `--to FOLDER` keeps what each step printed in that folder.
The record knows nothing of it: after a run of thirty steps it holds what
it held before, plus whatever a step happened to append. So what the run
found can't be proven later, traced back or sent on with the rest.

This puts the run on the record, as one row: for each step that has ended,
its place, its add-on, the stack's own mark of how it was asked (the eight
characters the log gives when a step starts, and the mark of the files it
was fed), how it ended, how many lines it printed, and the SHA-256 of what
it printed. Never the output, never an argument: a step's arguments can
hold your words, and the record keeps acts, not words.

Run as the last step of the stack itself, it records every step before it;
its own has not ended, and is left out. Asked twice of a run that hasn't
changed, it says the row is already there and writes nothing.

It reads FOLDER and the record, and writes the record only, through the
kernel. Exit codes, the kernel's: 0 the row was written, or was already
there; 42 no step of the run has ended yet; 2 refused (a bad command line,
no such box, a record that doesn't verify, a folder that isn't a kept run).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "stack-row"
USAGE = __doc__.split("\n\n")[1]
STARTED = re.compile(r"^(\d+) ([a-z0-9-]+): started \((\w+)(?:, fed (\w+))?\)")
ENDED = re.compile(r"^(\d+) ([a-z0-9-]+): exit (\d+), (\d+) lines?\b")
NOT_RUN = re.compile(r"^(\d+) ([a-z0-9-]+): not run\b")


def steps_of(run: Path) -> list[dict]:
    """Each step of the kept run that has ended, in its order: the last
    thing the log says of it is that it ended, or that it was not run."""
    seen: dict[int, dict] = {}
    for line in (run / "00-stack.txt").read_text(encoding="utf-8").splitlines():
        m = STARTED.match(line)
        if m:
            seen[int(m.group(1))] = {"n": int(m.group(1)), "addon": m.group(2), "mark": m.group(3),
                                     "fed": m.group(4), "ended": False}  # fmt: skip
            continue
        m = ENDED.match(line)
        if m and int(m.group(1)) in seen:
            seen[int(m.group(1))].update(
                ended=True, exit=int(m.group(3)), lines=int(m.group(4))
            )
            continue
        m = NOT_RUN.match(line)
        if m:
            seen.setdefault(
                int(m.group(1)),
                {"n": int(m.group(1)), "addon": m.group(2), "mark": None, "fed": None},
            )
            seen[int(m.group(1))].update(ended=True, exit=None, lines=0)
    out = []
    for n in sorted(seen):
        step = seen[n]
        if not step.pop("ended"):
            continue
        files = sorted(run.glob(f"{n:02d}-*.txt"))
        step["sha256"] = (
            hashlib.sha256(files[0].read_bytes()).hexdigest() if files else None
        )
        out.append(step)
    return out


def of(steps: list[dict]) -> str:
    """One hash for the run as it stands: the steps, as the row holds them."""
    return hashlib.sha256(json.dumps(steps, sort_keys=True).encode("utf-8")).hexdigest()


def said(steps: list[dict]) -> str:
    clean = sum(1 for s in steps if s["exit"] == 0)
    not_run = sum(1 for s in steps if s["exit"] is None)
    other = len(steps) - clean - not_run
    parts = [f"{clean} clean", f"{other} ended otherwise"]
    if not_run:
        parts.append(f"{not_run} not run")
    return f"{len(steps)} step{'' if len(steps) == 1 else 's'} ({', '.join(parts)})"


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--run", "--now") and a not in opts:
            opts[a] = next(it, "")
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if not opts.get("--box") or not opts.get("--run"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box, run = Path(opts["--box"]), Path(opts["--run"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if not (run / "00-stack.txt").is_file():
        print(
            f"refused: {run} is not a kept run: it holds no 00-stack.txt",
            file=sys.stderr,
        )
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    steps = steps_of(run)
    if not steps:
        print("nothing to put on the record: no step of this run has ended")
        return kernel.ESCALATE
    mark = of(steps)
    for row in reversed(rows):
        if row.get("kind") == KIND:
            if row.get("of") == mark:
                print(
                    f"already on the record: row {row['n']} holds this run as it stands, {said(steps)}"
                )
                return kernel.ALIVE
            break
    row = kernel.append(
        box, opts.get("--now") or kernel.now(), KIND, who=KIND, of=mark, steps=steps
    )
    print(f"put on the record: row {row['n']}, {said(steps)}")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
