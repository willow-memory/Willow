"""format_rot.py: files in formats that may stop opening. Python 3.9+.

    python adapters/stdlib/format-rot/format_rot.py --from FOLDER

Walks FOLDER (not hidden parts) and flags files whose format may stop
opening: old office files, proprietary ones, and those this repository has
no reader for. Current office and PDF are not flagged: [office](../office/)
and [pdf](../../deps/pdf/) still read them.

    format-rot needs you: 3 files
      .apk   2  no reader in this repository
      .doc   1  old office; convert while it still opens

It only reads. Exit codes, the kernel's: 0 nothing at risk; 42 something
flagged; 2 refused (FOLDER is not a folder).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: format_rot.py --from FOLDER"

#: extension -> why it may stop opening. Current .docx/.pdf stay off this list.
AT_RISK = {
    ".doc": "old office; convert while it still opens",
    ".xls": "old office; convert while it still opens",
    ".ppt": "old office; convert while it still opens",
    ".rtf": "old office; convert while it still opens",
    ".wpd": "old office; convert while it still opens",
    ".wps": "old office; convert while it still opens",
    ".pub": "old office; convert while it still opens",
    ".pages": "proprietary; convert while it still opens",
    ".numbers": "proprietary; convert while it still opens",
    ".apk": "no reader in this repository",
    ".dmg": "no reader in this repository",
    ".iso": "no reader in this repository",
    ".appx": "no reader in this repository",
}


def scan(folder: Path) -> dict[str, int]:
    """{ext: count} of at-risk files, hidden parts skipped."""
    out: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith("."):
                continue
            ext = Path(name).suffix.lower()
            if ext in AT_RISK:
                out[ext] = out.get(ext, 0) + 1
    return out


def render(counts: dict[str, int]) -> str:
    n = sum(counts.values())
    if n == 0:
        return "format-rot holds: nothing in a format that may stop opening\n"
    lines = [f"format-rot needs you: {n} file{'' if n == 1 else 's'}"]
    width = max(len(e) for e in counts)
    for ext in sorted(counts):
        lines.append(f"  {ext:<{width}}  {counts[ext]}  {AT_RISK[ext]}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--from":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--from") or args:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    counts = scan(folder)
    print(render(counts), end="")
    return kernel.ESCALATE if counts else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
