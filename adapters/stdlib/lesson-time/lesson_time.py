"""lesson_time.py: lesson plans whose timed parts don't add up to the period.

    python adapters/stdlib/lesson-time/lesson_time.py --box DIR [--period N]

A part is a heading that carries its minutes: `### Part 2 — The Mechanic
(15 min)`. A part may give a range (`(15–20 min)`), and then the plan's total
is a range too. A part marked optional, extension, additive or "if time" is
left out of the sum. A file's parts are added up and set against the time the
file says it takes, on a line that starts with Time, Duration, Length, Period or
Suggested time (`**Time:** 45–55 minutes`): the plan is ok when its total, or
any part of its range, falls inside the time it says. A file that says no time is held to --period N when it is
given, and left out when it isn't. A file with fewer than two timed parts is
not a lesson plan by this reading and is left out.

    off  45 of 50 min  lessons/hs-03-the-consent-ledger.md  8+12+20+5  (said on line 47)
    ok   50 of 50 min  lessons/hs-01-the-oracle.md          10+15+15+7+3  (said on line 44)
    6 plans read, 1 off

Minutes written inside a part's text (a 5 minute debrief within the
role-play) are not counted: only a part's own heading is, so a plan that
times its steps inside a part shows as off, and the line to read says where.

It only reads. Exit codes, the kernel's: 0 a plan is off; 42 every plan adds
up, or none was found; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

PART = re.compile(
    r"^#{1,6}\s.*\((\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\s*min(?:ute)?s?\b[^)]*\)\s*$", re.I
)
EXTRA = re.compile(r"\b(?:optional|extension|additive|if time)\b", re.I)
SAID = re.compile(
    r"^\W*(?:suggested\s+)?(?:time|duration|length|period)\W*:?\W*"
    r"(\d{1,3})(?:\s*[-–to]+\s*(\d{1,3}))?\s*min",
    re.I,
)


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def read_plan(rows: list[tuple[int, str]]) -> dict | None:
    """A file's timed parts and its stated time, or None when it times fewer
    than two parts. The stated time is the first line that says one."""
    parts, said, said_at = [], None, 0
    for n, line in rows:
        m = PART.match(line.strip())
        if m:
            if not EXTRA.search(line):
                lo = int(m.group(1))
                parts.append((lo, int(m.group(2)) if m.group(2) else lo))
            continue
        if said is None:
            s = SAID.match(line.strip())
            if s:
                lo = int(s.group(1))
                hi = int(s.group(2)) if s.group(2) else lo
                said, said_at = (min(lo, hi), max(lo, hi)), n
    if len(parts) < 2:
        return None
    return {"parts": parts, "said": said, "at": said_at}


def verdicts(pile: list[dict], period: int | None) -> list[dict]:
    out = []
    for path, rows in sorted(file_lines(pile).items()):
        plan = read_plan(rows)
        if plan is None:
            continue
        said, note = plan["said"], f"said on line {plan['at']}"
        if said is None:
            if period is None:
                continue
            said, note = (period, period), "from --period"
        lo = sum(a for a, _ in plan["parts"])
        hi = sum(b for _, b in plan["parts"])
        ok = lo <= said[1] and hi >= said[0]
        span = str(said[0]) if said[0] == said[1] else f"{said[0]}-{said[1]}"
        total = str(lo) if lo == hi else f"{lo}-{hi}"
        parts = "+".join(str(a) if a == b else f"{a}-{b}" for a, b in plan["parts"])
        out.append({"ok": ok, "total": total, "span": span, "path": path,
                    "parts": parts, "note": note})  # fmt: skip
    return sorted(out, key=lambda r: (r["ok"], r["path"]))


def show(rows: list[dict]) -> str:
    w = max(len(r["path"]) for r in rows)
    lines = [
        f"{'ok ' if r['ok'] else 'off'}  {r['total']} of {r['span']} min  "
        f"{r['path']:<{w}}  {r['parts']}  ({r['note']})"
        for r in rows
    ]
    off = sum(not r["ok"] for r in rows)
    lines.append(f"{len(rows)} plan{'s' if len(rows) != 1 else ''} read, {off} off")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--box", "--period"):
            opts[a] = next(it, "")
        else:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
    if not opts.get("--box"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    period = None
    if "--period" in opts:
        if not opts["--period"].isdigit() or not 0 < int(opts["--period"]) < 1000:
            print("refused: --period takes whole minutes, 1 to 999", file=sys.stderr)
            return kernel.REFUSED
        period = int(opts["--period"])
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    rows = verdicts(pile, period)
    if not rows:
        print("No lesson plan with timed parts and a stated time.")
        return kernel.ESCALATE
    print(show(rows))
    return kernel.ALIVE if any(not r["ok"] for r in rows) else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
