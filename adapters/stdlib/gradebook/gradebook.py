"""gradebook.py: a teacher's gradebook, kept on this machine: each student's
marks by assignment, and who is falling behind.

    python adapters/stdlib/gradebook/gradebook.py --box DIR [--below PCT]

The lines of your files that give a student a mark, as "Name: assignment
score":

    Ben Ruiz     41%  4 marks  latest 35% (Quiz 4, 2026-03-02)  below 50%
    Cy Dunn      62%  3 marks  latest 40% (Essay 2, 2026-03-02)  falling
    Maya Chen    84%  5 marks  latest 90% (Essay 2, 2026-03-02)
    3 students, 2 behind

**A mark** is a line that opens with a student's name (one to three words
that start with a capital) and a colon, and then gives a score: 17/20,
17 out of 20, or 85%. "Maya Chen: Essay 2 - 17/20" is Maya's 85% for Essay 2.
A name has a lowercase letter in it, and what follows the colon is short
(eight words at most) and has no colon of its own, so a hive's "H6: 5 fr bees,
eggs yes, mites 1/300" and an email's "Subject: Re: ... 38%" are not marks. Words like Total, Average, Page and Note are never names. A date such as
3/4/2026 is not a score. A line's day is the latest date it says, else the
nearest date written above it in its file, else the date its file is named
for; a line no day reaches is not counted.

**Behind** means one of two things, both plain arithmetic on the marks:
the average is below --below percent (50 unless told), or, with three marks or
more, the last two marks average at least 15 points under the marks before
them ("falling"). Nothing is graded, rounded up or sent to anyone; it is what
your own lines add up to. Lowest average first. It only reads. Exit codes, the
kernel's: 0 marks found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

LINE = re.compile(r"^\s*[-*•]?\s*([A-Z][\w'’.-]*(?: [A-Z][\w'’.-]*){0,2})\s*:\s*(.+)$")
SCORE = re.compile(
    r"(?<![\d/])(\d+(?:\.\d+)?)\s*(?:/|out of)\s*(\d+(?:\.\d+)?)(?![\d/])"
)
PERCENT = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%")
NOT_NAMES = {"total", "average", "mean", "page", "note", "notes", "score", "scores",
             "mark", "marks", "grade", "grades", "max", "class", "task", "todo", "out",
             "subject", "from", "to", "cc", "date", "description", "summary", "location",
             "re", "fwd"}  # fmt: skip
WORDS = 8  # a mark line is short: a name, an assignment, a score
DROP = 15  # points the last two marks must fall under the earlier ones
FALLING_FROM = 3  # marks needed before a fall means anything


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


def mark_of(line: str) -> tuple[str, str, float] | None:
    """(student, assignment, percent) a line gives, or None."""
    m = LINE.match(line)
    if not m or m.group(1).lower() in NOT_NAMES:
        return None
    name, rest = m.group(1), m.group(2)
    if not any(c.islower() for c in name) or ":" in rest or len(rest.split()) > WORDS:
        return None  # an id (H6), a header's second colon, or a sentence
    s = SCORE.search(rest)
    if s and float(s.group(2)) > 0:
        pct, span = 100 * float(s.group(1)) / float(s.group(2)), s.span()
    else:
        p = PERCENT.search(rest)
        if not p:
            return None
        pct, span = float(p.group(1)), p.span()
    what = (rest[: span[0]] + " " + rest[span[1] :]).strip(" -–—,;:.()")
    return name, " ".join(what.split()) or "(unnamed)", pct


def marks(pile: list[dict]) -> dict[str, list[tuple[str, str, float]]]:
    """{student: [(day, assignment, percent)] in day order}."""
    out: dict[str, list] = {}
    for day, _path, _n, line in entries(pile):
        got = mark_of(line)
        if got:
            out.setdefault(got[0], []).append((day, got[1], got[2]))
    return {k: sorted(v, key=lambda x: x[0]) for k, v in out.items()}


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def flags(rows: list, below: float) -> list[str]:
    pcts = [p for _, _, p in rows]
    out = []
    if mean(pcts) < below:
        out.append(f"below {below:g}%")
    if len(pcts) >= FALLING_FROM and mean(pcts[:-2]) - mean(pcts[-2:]) >= DROP:
        out.append("falling")
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(got: dict, below: float) -> list[str]:
    order = sorted(got, key=lambda k: (mean([p for _, _, p in got[k]]), k))
    width = max(len(k) for k in order)
    out, behind = [], 0
    for k in order:
        rows = got[k]
        day, what, last = rows[-1]
        fl = flags(rows, below)
        behind += bool(fl)
        out.append(
            f"{k:<{width}}  {round(mean([p for _, _, p in rows])):>3}%  "
            f"{len(rows)} mark{'s' if len(rows) != 1 else ''}  latest {round(last)}% ({what}, {dash(day)})"
            + ("  " + ", ".join(fl) if fl else "")
        )
    out.append(f"{len(order)} student{'s' if len(order) != 1 else ''}, {behind} behind")
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--below"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    below = opts.get("--below", "50")
    if not opts.get("--box") or args or not re.fullmatch(r"\d{1,3}(?:\.\d+)?", below):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    got = marks(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not got:
        print("No line of your folder gives a student a mark.")
        return kernel.ESCALATE
    print("\n".join(show(got, float(below))))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
