"""tip_pin.py: pin where a box's record ends, and later check it still does.

    python adapters/stdlib/tip-pin/tip_pin.py pin   --box DIR --to FILE
    python adapters/stdlib/tip-pin/tip_pin.py check --box DIR --pin FILE

`verify` finds an edit to one past row. It can't find rows cut off the end,
or rows removed and then all re-hashed, because nothing outside the box says
what the record's last hash or length should be. `pin` writes those two
facts to a small file you keep out of the box's reach; `check` reads the box
against it:

    holds       12 rows pinned; the box has 15 (3 added since)
    cut short     12 rows pinned; the box has 9
    rewritten     row 11 is not the one you pinned

A record only grows, so a box that holds has the pinned row where it was and
may have more after it. Cut short and rewritten are the two ways it can't.

Exit codes, the kernel's: for `pin`, 0 written, 2 refused. For `check`, 0
holds, 42 cut short or rewritten, and waits on you, 2 refused (a pin that
isn't one, or a record that doesn't verify).

It only reads the box, never its key. The one thing it writes is FILE, made
new and readable only by you; it never writes over a file, and never inside
the box or your folder.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KEYS = {"rows", "tip"}


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def chain(box: Path) -> tuple[list[dict], str | None]:
    """(rows, why not): the box's record, only if it verifies and isn't empty."""
    if not (box / "kernel.json").exists():
        return [], "not a kernel box; init first"
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return [], f"the record doesn't verify ({breaks[0]}); a person looks first"
    if not rows:
        return [], "the record is empty; nothing to pin"
    return rows, None


def pin_of(rows: list[dict]) -> dict:
    return {"rows": len(rows), "tip": rows[-1]["hash"]}


def read_pin(path: Path) -> tuple[dict | None, str | None]:
    try:
        pin = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"could not read {path} as a pin: {type(e).__name__}"
    if not isinstance(pin, dict) or pin.keys() != KEYS:
        return None, f"{path} is not a pin (it should hold rows and tip)"
    n, tip = pin["rows"], pin["tip"]
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        return None, f"{path} is not a pin (rows should be a count of one or more)"
    if not isinstance(tip, str) or len(tip) != 64 or set(tip) - set("0123456789abcdef"):
        return None, f"{path} is not a pin (tip should be a SHA-256 in hex)"
    return pin, None


def compare(rows: list[dict], pin: dict) -> tuple[int, str]:
    """(exit code, the line to say) for a record against what was pinned."""
    n, m = pin["rows"], len(rows)
    if m < n:
        return kernel.ESCALATE, f"cut short   {n} rows pinned; the box has {m}"
    if rows[n - 1]["hash"] != pin["tip"]:
        return kernel.ESCALATE, f"rewritten   row {n - 1} is not the one you pinned"
    added = f" ({m - n} added since)" if m > n else ""
    return kernel.ALIVE, f"holds       {n} rows pinned; the box has {m}{added}"


def do_pin(box: Path, to: Path) -> int:
    rows, why = chain(box)
    if why:
        return refuse(why)
    for name, root in (
        ("your folder", Path(kernel.config(box)["pile"])),
        ("the box", box),
    ):
        if to.resolve().is_relative_to(root.resolve()):
            return refuse(f"FILE is inside {name}; this never writes there")
    if to.exists():
        return refuse(f"{to} exists; this never overwrites")
    if not to.resolve().parent.is_dir():
        return refuse(f"{to.parent} is not a folder; this never makes one")
    pin = pin_of(rows)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        return refuse(f"could not write {to}: {type(e).__name__}")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(pin, indent=1, sort_keys=True) + "\n")
    print(f"pinned {pin['rows']} rows, tip {pin['tip'][:12]}…, to {to}")
    print("keep it where whoever writes the box can't reach")
    return kernel.ALIVE


def do_check(box: Path, pin_path: Path) -> int:
    pin, why = read_pin(pin_path)
    if why:
        return refuse(why)
    rows, why = chain(box)
    if why:
        return refuse(why)
    code, line = compare(rows, pin)
    print(line)
    return code


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    flag = {"pin": "--to", "check": "--pin"}.get(cmd)
    if flag is None or len(rest) != 4 or rest[0] != "--box" or rest[2] != flag:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, other = Path(rest[1]), Path(rest[3])
    return do_pin(box, other) if cmd == "pin" else do_check(box, other)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
