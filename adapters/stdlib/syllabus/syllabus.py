"""syllabus.py: a course syllabus as dates: readings, assignments and exams
due, each cited. Python 3.9+.

    python adapters/stdlib/syllabus/syllabus.py --box DIR [--now TS]

The lines of your course files that give a reading, an assignment or an exam a
day, soonest first, each with where it was written:

    2026-03-02  reading     Ch. 1-2: Introduction            (syllabus.md:4, 7 days ago)
    2026-03-09  assignment  Essay 1 due                      (syllabus.md:6, today)
    2026-04-20  exam        Midterm                          (syllabus.md:12, in 42 days)
    1 reading, 1 assignment, 1 exam; next 2026-04-20

**What counts.** A line, on a day, about a course (the line or the path of its
file says syllabus, course, class, lecture, semester, term, module or unit) that
says what is due: a reading (read, reading, chapter, ch., pp.), an assignment
(assignment, essay, paper, problem set, homework, hw, project, lab, report,
quiz, due) or an exam (exam, midterm, final, test). A line says the first of
the three that it names, exam before assignment before reading. A line's day is
the latest date it says, else the nearest date written above it in its file (a
week's heading), else the date its file is named for.

Distances are counted from --now (an ISO timestamp, the kernel's kind; today if
not given). "Next" is the first day that is today or later. Nothing is marked
done and nothing is reminded; the file and the line are cited so you can read
what it says. It only reads. Exit codes, the kernel's: 0 something due found;
42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

CONTEXT = re.compile(
    r"\b(?:syllabus|syllabi|courses?|class|lectures?|semester|term|module|unit)\b", re.I
)
KINDS = (
    ("exam", re.compile(r"\b(?:exams?|midterms?|final|test)\b", re.I)),
    ("assignment", re.compile(r"\b(?:assignments?|essay|papers?|problem sets?|homework|hw|project|lab|report|quiz(?:zes)?|due)\b", re.I)),
    ("reading", re.compile(r"\b(?:read|reading|readings|chapters?|ch\.|pp\.)", re.I)),
)  # fmt: skip
WIDTH = 60  # characters of a line shown


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says, else the nearest above it in its file, else its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def due(pile: list[dict]) -> list[dict]:
    out = []
    for day, path, n, line in entries(pile):
        if not CONTEXT.search(path + " " + line):
            continue
        kind = next((k for k, rx in KINDS if rx.search(line)), "")
        if kind:
            out.append(
                {
                    "day": date(int(day[:4]), int(day[4:6]), int(day[6:])),
                    "kind": kind,
                    "where": f"{path}:{n}",
                    "line": " ".join(line.split()),
                }
            )
    return sorted(out, key=lambda d: (d["day"], d["where"]))


def distance(day: date, today: date) -> str:
    n = (day - today).days
    if n == 0:
        return "today"
    s = "" if abs(n) == 1 else "s"
    return f"in {n} day{s}" if n > 0 else f"{-n} day{s} ago"


def show(found: list[dict], today: date) -> list[str]:
    out = []
    for d in found:
        text = d["line"] if len(d["line"]) <= WIDTH else d["line"][: WIDTH - 1] + "…"
        out.append(
            f"{d['day']}  {d['kind']:<10}  {text:<{WIDTH}}  ({d['where']}, {distance(d['day'], today)})"
        )
    counts = {k: sum(1 for d in found if d["kind"] == k) for k, _ in KINDS[::-1]}
    said = ", ".join(f"{n} {k}{'s' if n != 1 else ''}" for k, n in counts.items() if n)
    nxt = next((d["day"] for d in found if d["day"] >= today), None)
    out.append(said + (f"; next {nxt}" if nxt else "; none still to come"))
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    ts = opts.get("--now") or kernel.now()
    if not opts.get("--box") or args or not re.match(r"\d{4}-\d{2}-\d{2}", ts):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = due(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not found:
        print(
            "No line of your folder gives a reading, an assignment or an exam for a course a day."
        )
        return kernel.ESCALATE
    print("\n".join(show(found, today)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
