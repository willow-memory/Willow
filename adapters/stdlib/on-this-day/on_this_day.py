"""on_this_day.py: what your files say happened on this date in earlier years.

    python adapters/stdlib/on-this-day/on_this_day.py --box DIR [--now TS] [--json]

Every line dated today's month and day in an earlier year, newest year first,
as a report (output: report; see adapters/stdlib/ci/README.md): a group a year,
each row the place and the line:

    on-this-day: populated, 2 lines written on 10-23 in 2 earlier years
    ## 2023
      tuning/2023.txt:205  2023-10-23  Wendell Ashby - Yamaha U1 (1988)
    ## 2022
      memos/2022-10-23_0815.txt:1  ...

A line counts when it holds the date itself, read the way the kernel reads
one (its `newest`), or when it is the first line of a file named by that day.
A passage's other dates never stand in for a line's own.

It only reads. Exit codes, the kernel's: 0 something was written on this day
(`populated`) or nothing was (`empty`); 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


NAME = "on-this-day"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


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
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
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
        said = f"nothing dated {today[4:6]}-{today[6:]} in an earlier year"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    by_year: dict[str, list] = {}
    for year, place, line in hits:
        by_year.setdefault(year, []).append((place, line[:120]))
    n, y = len(hits), len(by_year)
    said = (f"{n} line{'s' if n != 1 else ''} written on {today[4:6]}-{today[6:]} "
            f"in {y} earlier year{'s' if y != 1 else ''}")  # fmt: skip
    say(report(NAME, "populated", said, list(by_year.items())), as_json)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
