"""The Johnson case's five people, as the files they keep: python3 make_life.py [--check]

Writes life/<person>/ for each of them, the same bytes every run. Ines Calder,
a loss adjuster, keeps the case; Walt Brenner, her boss, Aurelie Stone at the
insurer, Tamsin Reyes, its counsel, and Harold Ames, the mediator, keep their
own few lines about it. Each folder is one person's willow, and scene.py
passes Ines's report between them.

`--check` reads the files back and holds them to PLANTED: the lines the
scene's answers cite, and the one that shows her first answer was wrong.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"

FILES = {
    # ── Ines: the case, and other work, as she writes it down ──────────────
    "ines/johnson/site-visit.md": """\
# Johnson, 14 Wren Row, Ashcombe: site visit

2026-03-09. Insured: Della Johnson. Claim NM-2026-0412, Northfield Mutual.

Storm damage on the north slope: the storm of 2026-03-03 lifted eleven ridge
tiles and cracked four more. The bedding under them is washed out.

Inside, the back bedroom ceiling has a water stain about 1.2 m across, under
the north slope. Moisture meter: 38% at the stain, 11% a metre away.

Photos 1 to 23 on the case drive, numbered as in the photo log.
""",
    "ines/johnson/calls.md": """\
# Johnson: calls

2026-03-06 10:40. Della Johnson called Northfield's claims line to report
the leak. She first saw water on the bedroom ceiling the evening of
2026-03-05, two days after the storm.

2026-03-07 09:15. Booked the site visit for 2026-03-09. She asked whether to
move the bed; told her yes, and to keep a bucket under the stain.

2026-03-11 16:20. Hartwell Roofing sent their quote; forwarded to the file.
""",
    "ines/johnson/prior-work.md": """\
# Johnson: earlier work on the roof

Invoice 2024-08-19, Hartwell Roofing: re-pointed the chimney flashing on the
south slope. No work was done on the north slope; the invoice and the
photos the insured kept agree.

Nothing else on the roof since the house was bought in 2019.
""",
    "ines/johnson/quote.md": """\
# Johnson: the roofer's quote

Quote from Hartwell Roofing, 2026-03-11: replace fifteen ridge tiles on the
north slope, re-bed the whole ridge, and make good the bedroom ceiling. The
roofer's quote comes to $2,140, of which $380 is the ceiling.
""",
    "ines/kessler/notes.md": """\
# Kessler, 3 Mill Lane: notes

2026-02-20. Burst pipe under the kitchen sink. Cabinet base swollen; floor
dry. Waiting on the plumber's report before anything else.
""",
    "ines/admin/diary.md": """\
# Diary

2026-03-12. Walt wants the Johnson report before the 3 o'clock with
Northfield.
""",
    # ── Walt: the firm's side ──────────────────────────────────────────────
    "walt/cases.md": """\
# Open cases

- Johnson, 14 Wren Row: Ines. Northfield wants our report before the call on
  2026-03-12 at 15:00.
- Kessler, 3 Mill Lane: Ines. Waiting on a plumber.
""",
    # ── Aurelie: the insurer ───────────────────────────────────────────────
    "aurelie/claims.md": """\
# Claims I'm handling

NM-2026-0412, Johnson, 14 Wren Row: storm, roof. Adjuster's report from
Calder & Pike due 2026-03-12. Counsel: Tamsin Reyes.
""",
    # ── Tamsin: the insurer's counsel ──────────────────────────────────────
    "tamsin/files.md": """\
# Files

Johnson v Northfield Mutual. The insured disputes the excess and says the
north slope was sound before the storm. Mediation set for 2026-04-02.
""",
    # ── Harold: the mediator ───────────────────────────────────────────────
    "harold/list.md": """\
# Mediations

2026-04-02 10:00. Johnson v Northfield Mutual. Exhibits by 2026-03-30.
""",
}

#: (file, a line the scene relies on): every one must be on disk
PLANTED = [
    ("ines/johnson/site-visit.md", "Storm damage on the north slope: the storm of 2026-03-03 lifted eleven ridge"),
    ("ines/johnson/calls.md", "2026-03-06 10:40. Della Johnson called Northfield's claims line to report"),
    ("ines/johnson/prior-work.md", "south slope. No work was done on the north slope; the invoice and the"),
    ("ines/johnson/quote.md", "roofer's quote comes to $2,140, of which $380 is the ceiling."),
    ("ines/admin/diary.md", "2026-03-12. Walt wants the Johnson report before the 3 o'clock with"),
]  # fmt: skip


def write() -> None:
    if LIFE.exists():
        shutil.rmtree(LIFE)
    for rel, text in FILES.items():
        p = LIFE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    people = sorted({rel.split("/")[0] for rel in FILES})
    print(f"wrote {len(FILES)} files for {len(people)} people: {', '.join(people)}")


def check() -> int:
    bad = 0
    for rel, line in PLANTED:
        p = LIFE / rel
        held = p.is_file() and line in p.read_text(encoding="utf-8").splitlines()
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
