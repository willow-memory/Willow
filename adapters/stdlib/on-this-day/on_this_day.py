"""on_this_day.py: what your files say happened on this date in earlier years.

    python adapters/stdlib/on-this-day/on_this_day.py --box DIR [--now TS]

Every line dated today's month and day in an earlier year, newest year first:

    2023  tuning/2023.txt:205   2023-10-23  Wendell Ashby - Yamaha U1 (1988)
    2022  memos/2022-10-23_0815.txt:1   ...

A line counts when it holds the date itself, read the way the kernel reads
one (its `newest`), or when it is the first line of a file named by that day.
A passage's other dates never stand in for a line's own.

It only reads. Exit codes, the kernel's: 0 something was written on this day;
42 nothing; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def on_this_day(pile: list[dict], today: str) -> list[tuple[str, str, str]]:
    """(year, place, line) for each line dated today's MMDD in an earlier
    year: by a date on the line itself (the kernel's `newest`), or, for a
    file's first line, by a date in the file's name (memos/2023-10-23.txt)."""
    mmdd, year = today[4:8], today[:4]
    out, seen = [], set()
    for c in pile:
        named = kernel.newest(c["path"])
        for i, line in enumerate(c["text"].splitlines()):
            d = kernel.newest(line)
            if not d and c["path"] not in seen and line.strip():
                d = named  # the file's first line stands for a file named by day
            if line.strip():
                seen.add(c["path"])
            if d and d[4:] == mmdd and d[:4] < year:
                out.append((d[:4], f"{c['path']}:{c['line'] + i}", line.strip()))
    return sorted(out, key=lambda x: (-int(x[0]), x[1]))


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    today = (opts.get("--now") or kernel.now())[:10].replace("-", "")
    hits = on_this_day(kernel.chunks(Path(kernel.config(box)["pile"])), today)
    if not hits:
        print(
            f"Nothing in your folder is dated {today[4:6]}-{today[6:]} in an earlier year."
        )
        return kernel.ESCALATE
    width = max(len(p) for _, p, _ in hits)
    for year, place, line in hits:
        print(f"{year}  {place:<{width}}  {line[:120]}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
