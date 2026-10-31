"""restore_drill.py: a backup zip restored into scratch and verified. Python 3.9+.

    python adapters/stdlib/restore-drill/restore_drill.py --from ZIP

Unzips ZIP into scratch the add-on makes itself, then checks:

- every name stays inside that scratch (no `..`, no absolute path);
- every member's bytes match the zip's CRC;
- `kernel.json` and `record.jsonl` are in the zip;
- the restored record's chain holds, read by the kernel.

`kernel.json` is confirmed, never written: a folder that holds one is a
box, and a box is written only through the kernel. The key is never
extracted.

A zip that held is one you can restore on the day you need it. The scratch
is deleted when the run ends. It never writes beside ZIP, never reads the
key, and never compares the zip to a live box: [backup](../backup/) already
did that the day it was written.

    restored: willow-backup-20261024-093000.zip, 5 files, 4 rows; the chain holds

Exit codes, the kernel's: 0 it restores; 42 nothing there, or the drill
failed; 2 refused (ZIP isn't a file, or a bad command line).
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: restore_drill.py --from ZIP"


def why_not_names(names: list[str]) -> str | None:
    for n in names:
        p = Path(n)
        if p.is_absolute() or ".." in p.parts:
            return f"a member leaves the zip: {p.name}"
    return None


def drill(path: Path) -> tuple[int, str]:
    """(exit, line). Scratch dies with the function."""
    if not zipfile.is_zipfile(path):
        return kernel.ESCALATE, "nothing there: not a zip"
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            bad = why_not_names(names)
            if bad:
                return kernel.ESCALATE, bad
            if z.testzip() is not None:
                return kernel.ESCALATE, "a member's bytes don't match the zip"
            if "record.jsonl" not in names or "kernel.json" not in names:
                return kernel.ESCALATE, "nothing there: not a willow backup"
            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp)
                for name in names:
                    leaf = Path(name).name
                    if leaf == "kernel.json":
                        z.read(name)
                        continue
                    if leaf.endswith(".key"):
                        continue
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(name))
                rows, breaks = kernel.read(dest / "record.jsonl")
    except (OSError, zipfile.BadZipFile) as e:
        return kernel.ESCALATE, f"couldn't read it: {type(e).__name__}"
    if breaks:
        return kernel.ESCALATE, "the restored record doesn't verify: " + "; ".join(
            breaks
        )
    n = len(names)
    return kernel.ALIVE, (
        f"restored: {path.name}, {n} file{'' if n == 1 else 's'}, "
        f"{len(rows)} row{'' if len(rows) == 1 else 's'}; the chain holds"
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--from":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if sorted(opts) != ["--from"] or args or not opts.get("--from"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    path = Path(opts["--from"])
    if not path.is_file():
        print(f"refused: not a file: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    code, said = drill(path)
    print(said)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
