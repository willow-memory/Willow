"""origin.py: when and why was the code a hit landed on written?

    python demo/known-gaps/origin.py --repos DIR --scored FILE --out FILE

FILE (--scored) is score.py's output (or run.py's): each answer with the
`path:first-last` ranges of the lines that hit. For every distinct range of a
unit, at that unit's vulnerable commit in DIR/<repo>, this asks
adapters/stdlib/ci/whose.py which commit wrote the lines, then reads that
commit: its date, its title, the ids its message cites (a gap id of 12 hex
digits, an audit or packet id of 8, a pull request number), and how many days
passed before the fix's own commit date.

whose.py runs git in its own repository and blames the working tree; here its
`git` is pointed at DIR/<repo> and the vulnerable commit for the one call,
then put back, so its blame parsing is the one used. A range that can't be
resolved is written with the reason ("why"), never dropped.

Writes only FILE, one JSON line a range. Exit 0 written; 2 refused.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

import whose  # noqa: E402

REFS = (re.compile(r"\b[0-9a-f]{12}\b"), re.compile(r"\b[0-9A-F]{8}\b"),
        re.compile(r"#\d+\b"))  # fmt: skip
RANGE = re.compile(r"(.+):(\d+)-(\d+)")


def git(repo: Path, *argv: str) -> str:
    done = subprocess.run(["git", *argv], cwd=repo, capture_output=True, text=True)
    if done.returncode:
        raise ValueError(done.stderr.strip() or f"git {argv[0]} failed")
    return done.stdout


def blame(repo: Path, rev: str, path: str, first: int, last: int) -> list:
    """whose.py's answer for one range, as of `rev` in `repo`."""
    was = whose.git

    def at(*args: str) -> subprocess.CompletedProcess:
        a = list(args)
        if a[0] == "blame":
            a.insert(a.index("--"), rev)
        return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True)

    whose.git = at
    try:
        return whose.whose([(path, first, last)], None)
    finally:
        whose.git = was


def stamp(text: str) -> datetime:
    return datetime.fromisoformat(text.strip())


def origins(repos: Path, pins: dict, ranges: set) -> list:
    out = []
    dates: dict = {}
    for unit, rng in sorted(ranges):
        pin = pins[unit]
        repo = repos / pin["repo"]
        m = RANGE.fullmatch(rng)
        row = {"unit": unit, "range": rng}
        try:
            if pin["fixed"]["commit"] not in dates:
                dates[pin["fixed"]["commit"]] = stamp(
                    git(repo, "log", "-1", "--format=%cI", pin["fixed"]["commit"])
                )
            found = blame(repo, pin["vulnerable"]["commit"], m.group(1),
                          int(m.group(2)), int(m.group(3)))  # fmt: skip
            if not found:
                raise ValueError("whose.py found no commit")
            for short, _where in found:
                full = git(repo, "rev-parse", short).strip()
                date, _, body = git(
                    repo, "log", "-1", "--format=%cI%n%B", full
                ).partition("\n")
                refs = sorted({r for rx in REFS for r in rx.findall(body)})
                out.append({**row, "commit": full, "date": date,
                            "title": body.strip().splitlines()[0] if body.strip() else "",
                            "refs": refs, "fixed_date": dates[pin["fixed"]["commit"]].isoformat(),
                            "days_open": (dates[pin["fixed"]["commit"]] - stamp(date)).days})  # fmt: skip
        except (ValueError, AttributeError) as e:
            out.append({**row, "why": str(e)})
    return out


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 6 or set(opts) != {"--repos", "--scored", "--out"}:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        rows = [json.loads(x) for x in Path(opts["--scored"]).read_text().splitlines()]
        ranges = {(r["unit"], g) for r in rows for g in r.get("ranges", [])}
        out = origins(Path(opts["--repos"]), trees.load_pins(), ranges)
    except (OSError, ValueError, KeyError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    with open(opts["--out"], "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"{len(out)} rows for {len(ranges)} ranges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
