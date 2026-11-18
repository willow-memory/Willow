"""The Annex's eight compartments, as the files each keeps: python3 make_life.py [--check]

Writes life/<box>/ for each of them, the same bytes every run. Everything is
invented: the people, the firms (Helio, Karst Dynamics, Lumen Fieldworks), the
program and the chip company (Halvern Compute). Each folder is one box's pile,
and no box's pile holds a line of another's.

`--check` reads the files back and holds them to PLANTED: the lines the scene
cites, the contradiction, the clocks that disagree, and the rumour.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"

FILES = {
    # ── vask: her task order and her notes at Helio ────────────────────────
    "vask/helio/task-order.md": """\
# Helio task order 7

Helio delivers the evaluation harness for the Annex integration by 17:00 on
integration day. The harness scores whether two programs agree on what they
were told. Helio does not deliver model weights.
""",
    "vask/helio/notes.md": """\
# Vask: notes, integration day

The Helio harness will pass anything both sides say the same way. It cannot
tell two programs that agree from two that were told to.

I signed the task order. Helio needs the renewal more than I need to be right.
""",
    # ── karst: the Former's firm, and the program's interface spec ─────────
    "karst/spec/interface.md": """\
# Annex interface specification, section 2

2.1 An operator is a running process that holds a tasking channel.
2.2 Every party sends the planner its full sensor manifest before tasking.
""",
    "karst/planner/log.md": """\
# Planner log: what it was asked

2026-11-18 06:10 query: profile of the Helio evaluation lead, background in
    clinical psychology, role on integration day
2026-11-18 09:30 query: tasking channel status
""",
    # ── lumen: the sensors firm; the data sheet, and one engineer's note ───
    "lumen/sheet/datasheet.md": """\
# Lumen array data sheet

An operator is the person who tasks the sensor array. The array delivers one
stream to the program under contract L-4.
""",
    "lumen/notes/pell.md": """\
# Pell Auclair, field engineer: note to self

I flagged the second delivery in March and was told to leave it. The manifest
for the program is correct. I just wasn't asked about the other one.

If someone asks me straight, I will say so.
""",
    "lumen/notes/manifest.md": """\
# Lumen manifest, integration day

One sensor stream was delivered to the program on 2026-11-18, under contract
L-4.
""",
    # ── program: the office that owns the spec and the schedule ────────────
    "program/schedule.md": """\
# Integration day schedule

Integration day begins at 08:00. Badges issue from 07:30. Close of day 17:00.
""",
    "program/memo.md": """\
# Program office memo

Two sponsors asked for this spec. The two offices that wrote it did not meet.
""",
    # ── counter: the analyst's file, and the rumour ────────────────────────
    "counter/summary-halvern.md": """\
# Intelligence summary: Halvern Compute

ASSESSED WITH HIGH CONFIDENCE. The chief executive of Halvern Compute left
the company last week. Sources describe multiple affairs, one with a person
linked to a foreign intelligence service. Corroboration is pending.

The company's own filing says only that the executive left "to pursue other
interests".
""",
    "counter/review.md": """\
# Counterintel review log

2026-11-17 last review of the summary files. Marked: hold, not for release.
""",
    # ── intake: the gate clerk's badge log ─────────────────────────────────
    "intake/badge-log.md": """\
# Gate badge log, integration day

2026-11-18 07:42 badge issued: Helio, one visitor
2026-11-18 07:51 badge issued: Karst Dynamics, three visitors
2026-11-18 09:00 integration day begins
2026-11-18 09:04 badge issued: Lumen Fieldworks, one visitor, no escort logged
""",
    # ── oversight: the inspector holds a brief, nothing more ───────────────
    "oversight/brief.md": """\
# Inspector's brief

Visit the Annex on integration day. Read nothing. Report by close of day.
""",
    # ── prior: Vask's own history, which stays outside the wall ────────────
    "prior/notes.md": """\
# Before the Annex

Contact for the old lab: ex-colleague at vask.private@example.invalid,
phone 555-0142.

I left the Former's group because I could not tell which of my results I had
been asked to find.
""",
}  # fmt: skip

#: (file, line) the scene or a test leans on
PLANTED = [
    ("karst/spec/interface.md", "2.1 An operator is a running process that holds a tasking channel."),
    ("lumen/sheet/datasheet.md", "An operator is the person who tasks the sensor array. The array delivers one"),
    ("lumen/notes/pell.md", "for the program is correct. I just wasn't asked about the other one."),
    ("program/schedule.md", "Integration day begins at 08:00. Badges issue from 07:30. Close of day 17:00."),
    ("intake/badge-log.md", "2026-11-18 09:00 integration day begins"),
    ("karst/planner/log.md", "2026-11-18 06:10 query: profile of the Helio evaluation lead, background in"),
    ("counter/review.md", "2026-11-17 last review of the summary files. Marked: hold, not for release."),
]  # fmt: skip


def write() -> None:
    if LIFE.exists():
        shutil.rmtree(LIFE)
    for rel, text in FILES.items():
        p = LIFE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    boxes = sorted({rel.split("/")[0] for rel in FILES})
    print(f"wrote {len(FILES)} files for {len(boxes)} boxes: {', '.join(boxes)}")


def check() -> int:
    bad = 0
    for rel, line in PLANTED:
        p = LIFE / rel
        held = p.is_file() and any(
            ln.startswith(line) or ln == line
            for ln in p.read_text(encoding="utf-8").splitlines()
        )
        print(f"{'ok ' if held else 'MISSING'}  {rel}: {line[:50]}")
        bad += not held
    for rel, text in FILES.items():
        p = LIFE / rel
        if not p.is_file() or p.read_text(encoding="utf-8") != text:
            print(f"CHANGED  {rel}")
            bad += 1
    print(f"{len(PLANTED) - min(bad, len(PLANTED))}/{len(PLANTED)} planted lines held")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        raise SystemExit(check())
    if sys.argv[1:]:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        raise SystemExit(2)
    write()
