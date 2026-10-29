"""job_hunt.py: applications sent, replies and interviews, by date: who you're
still waiting on.

    python adapters/stdlib/job-hunt/job_hunt.py --box DIR [--now TS]

The lines of your notes about a job search, gathered by company, with where
each stands and how long you have waited:

    Acme (Designer)  interview 2026-03-10  after applied 2026-02-20  waiting 233 days
    Initech          applied 2026-09-01  waiting 58 days
    Globex           rejected 2026-03-02  after applied 2026-02-10
    Hooli            offer 2026-09-15  after applied 2026-08-01
    4 applications: 2 waiting, 1 rejected, 1 offer

**What counts.** A line, on a day, about a job search (the line or the path of
its file says job, application, CV, resume, recruiter, vacancy, role, position,
hiring or career) that names a company and says one of: applied
(applied, application sent, sent my CV), replied (replied, heard back, got
back), interview (interview, phone screen, assessment, take-home), followed up
(followed up, chased), rejected (rejected, declined, not moving forward,
unsuccessful, regret) or offer (offer). The company is the name that starts the
line ("Acme: applied"), else the capitalised words after "to", "at", "with",
"from" or "for"; a role in brackets is kept. A line naming no company is left
out. The day is the line's latest date, else the nearest date written above it
in its file, else the date its file is named for.

**Where it stands** is the company's latest event. A company whose latest is
rejected or offer is finished; any other is waiting, and the days are counted
from that event to --now (an ISO timestamp, the kernel's kind; today if not
given). Waiting longest first, then the finished. Nothing is sent or chased
for you. It only reads. Exit codes, the kernel's: 0 applications found; 42
none; 2 refused.
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

STAGES = {
    "offer": re.compile(r"\boffers?\b", re.I),
    "rejected": re.compile(
        r"\b(?:rejected|rejection|declined|not moving forward|unsuccessful|regret)\b",
        re.I,
    ),
    "interview": re.compile(
        r"\b(?:interview(?:s|ed)?|phone screen|screening|assessment|take-home)\b", re.I
    ),
    "replied": re.compile(r"\b(?:replied|heard back|got back|reply)\b", re.I),
    "followed up": re.compile(r"\b(?:followed up|follow-up|chased)\b", re.I),
    "applied": re.compile(
        r"\b(?:applied|application sent|sent (?:my )?(?:cv|resume))\b", re.I
    ),
}
CONTEXT = re.compile(
    r"\b(?:jobs?|applications?|cv|resume|recruiters?|vacanc(?:y|ies)|roles?|positions?|hiring|careers?)\b",
    re.I,
)
WORD = r"[A-Z][\w&.'’-]*"
LEAD = re.compile(
    rf"^\s*[-*•]?\s*(?:[\d./-]+\s+)?({WORD}(?: {WORD}){{0,2}})\s*(?:[:\-–]|\()"
)
AFTER = re.compile(rf"\b(?:to|at|with|from|for)\s+({WORD}(?: {WORD}){{0,2}})")
ROLE = re.compile(r"\(([^)]{2,40})\)")
NOT_COMPANIES = {"offer", "applied", "interview", "rejected", "note", "notes", "today", "job", "jobs", "cv", "re", "subject", "from", "to"}  # fmt: skip
WAITING = ("applied", "replied", "interview", "followed up")


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


def company_of(line: str) -> str:
    """The company a line names: the name it starts with, else the capitalised
    words after to/at/with/from/for, else ""."""
    for rx in (LEAD, AFTER):
        m = rx.search(line)
        if m and m.group(1).lower() not in NOT_COMPANIES:
            return m.group(1)
    return ""


def stage_of(line: str) -> str:
    """The stage a line says: the strongest of offer, rejected, interview,
    replied, followed up, applied, in that order; "" when it says none."""
    return next((k for k, rx in STAGES.items() if rx.search(line)), "")


def hunt(pile: list[dict]) -> dict[str, dict]:
    """{company: {role, events: [(day, stage)]}}."""
    out: dict = {}
    for day, path, _n, line in entries(pile):
        stage = stage_of(line)
        company = (
            company_of(line) if stage and CONTEXT.search(path + " " + line) else ""
        )
        if company:
            rec = out.setdefault(company, {"role": "", "events": []})
            role = ROLE.search(line)
            rec["role"] = rec["role"] or (role.group(1).strip() if role else "")
            rec["events"].append((day, stage))
    for rec in out.values():
        rec["events"].sort()
    return out


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def show(got: dict, today: date) -> list[str]:
    rows = []
    for company, rec in got.items():
        day, stage = rec["events"][-1]
        done = stage in ("rejected", "offer")
        d = (today - date(int(day[:4]), int(day[4:6]), int(day[6:]))).days
        rows.append((done, -d if not done else day, company, rec, day, stage, d))
    rows.sort(key=lambda r: r[:3])
    w = max(len(r[2] + (f" ({r[3]['role']})" if r[3]["role"] else "")) for r in rows)
    out = []
    for done, _k, company, rec, day, stage, d in rows:
        first = next((ds for ds, st in rec["events"] if st == "applied"), "")
        name = company + (f" ({rec['role']})" if rec["role"] else "")
        bits = f"{stage} {dash(day)}"
        if first and first != day:
            bits += f"  after applied {dash(first)}"
        if not done:
            bits += (
                f"  waiting {d} day{'s' if d != 1 else ''}"
                if d >= 0
                else "  (in the future)"
            )
        out.append(f"{name:<{w}}  {bits}")
    n = len(rows)
    waiting = sum(1 for r in rows if not r[0])
    rej = sum(1 for r in rows if r[5] == "rejected")
    off = sum(1 for r in rows if r[5] == "offer")
    out.append(
        f"{n} application{'s' if n != 1 else ''}: {waiting} waiting, {rej} rejected, {off} offer{'s' if off != 1 else ''}"
    )
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
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
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
    got = hunt(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not got:
        print("No line of your folder is about a job application to a company.")
        return kernel.ESCALATE
    print("\n".join(show(got, today)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
