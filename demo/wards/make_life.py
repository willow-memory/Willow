"""Four made-up minors and the people who hold records for them, as the
files each box keeps: python3 make_life.py [--check]

Writes life/<box>/ for each box, the same bytes every run. Nobody here is
real, and nothing here is anyone's record. Each minor stands somewhere
different to their own box:

    wren        six. Her box is held for her by her mother, Marit.
    tobias      fourteen. Marit holds a box for him; `tobias-own` is a
                second box, his alone, for care he asked for himself.
    imani       seventeen, eighteen tomorrow. Marit holds her box until
                the day it is handed over.
    leo         ten, in two houses. His box is held by his mother, Dana;
                `ravi` is his father's own box, of nights at his.

A third set, where it is tense, is played by tense.py: `sable` and
`sable-own`, fifteen, her guardian `garrick`, her aunt `bryony`, the
school `nurse`, the family `court`, and the box her aunt starts,
`sable-with-bryony`; and
`kit`, sixteen, held by a grandmother, with `kit-own`.

Leo four years on is played by fourteen.py: `leo-at-fourteen`, the box
his mother still holds, `ravi-later`, his father's, `leo-own`, and the
`asthma-nurse`.

The emergency card read by a stranger is played by card.py, with the
`practice` Marcus is registered at, and `someone` whose card says it is
his.

Two adults who cannot decide are played by adults.py: `agnes`, who
named her daughter while she could, with `petra`, `dorian`, the memory
`clinic` and the two boxes her children start for her; and `marcus`,
knocked off his bike with no one named, with `jun`, `elaine` and the
`hospital`.

`marit` is Marit's own box, about herself. `--check` reads the files back
and holds them to PLANTED: the lines the scene's answers cite, and that
no box Marit holds says anything of what Tobias keeps himself.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"

FILES = {
    "marit/diary.md": """\
# Marit Lind: things to keep track of

2026-10-01. Wrote Wren's emergency card again after the peanut scare at
the party. A copy in the red bag and one on the fridge.

2026-11-02. Imani is eighteen on the thirteenth. Her papers are hers from
that day; get them ready to hand over.

2026-11-05. Dentist for me on the nineteenth, 09:30.
""",
    "wren/immunizations.md": """\
# Wren Lind: immunizations

2021-06-14. MMR, first dose. From her card.
2025-09-02. MMR, second dose. From her card.
2025-09-02. Tdap booster. From the clinic's printout.
""",
    "wren/allergies.md": """\
# Wren Lind: allergies

Wren is allergic to peanuts. Found 2023-06-14: hives and a swollen lip
after a biscuit at nursery. Confirmed by the allergy clinic that August.

She carries an adrenaline pen in the red bag. It was last replaced
2026-09-20.
""",
    "wren/emergency-card.md": """\
# Wren Lind: emergency card

Written by Marit Lind, her mother, 2026-10-01. For whoever is with her.

Allergy: peanuts. A reaction is hives, a swollen lip, trouble breathing.
What to do: the adrenaline pen in the red bag, then call an ambulance.
Daily medicine: none.
Call first: Marit Lind.
""",
    "tobias/immunizations.md": """\
# Tobias Lind: immunizations

2012-09-03. MMR, first dose. From his card.
2016-08-29. MMR, second dose. From his card.
2024-08-12. Tetanus booster, after the bike fall. From the clinic's printout.
""",
    "tobias/checkups.md": """\
# Tobias Lind: checkups

2026-08-25. Sports physical for the football club. Fit to play.
Height 168 cm. Wears glasses for distance; eye test due in the spring.
""",
    "tobias-own/visits.md": """\
# My own notes. Not for the house.

2026-10-20. First counselling session with the nurse at the drop-in. I
asked for it myself and signed for it myself. She said it stays between
us unless I am in danger.

2026-11-03. Second counselling session. Talked about sleep. The next
counselling session is 2026-11-17 at four.
""",
    "imani/immunizations.md": """\
# Imani Lind: immunizations

2009-11-20. MMR, first dose. From her card.
2013-09-02. MMR, second dose. From her card.
2021-10-04. HPV, two doses, the second 2022-04-11. From the clinic's printout.
2024-09-09. Meningitis ACWY. From memory: the card for it is lost.
""",
    "imani/allergies.md": """\
# Imani Lind: allergies

No known allergy. A rash with penicillin in 2019 was written down by the
clinic as an intolerance, not an allergy.
""",
    "imani/emergency-card.md": """\
# Imani Lind: emergency card

Written by Marit Lind, her mother, 2026-10-01.

Allergy: none known. Penicillin gave her a rash in 2019.
Daily medicine: none.
Call first: Marit Lind.
""",
    "leo/immunizations.md": """\
# Leo Brandt-Sen: immunizations

2017-05-08. MMR, first dose. From his card.
2021-08-30. MMR, second dose. From his card.
""",
    "leo/asthma.md": """\
# Leo Brandt-Sen: asthma

Leo has asthma, found 2022. Brown inhaler morning and night. Blue inhaler
when he is wheezy: two puffs, wait, two more if he needs them.

His plan from the asthma nurse is dated 2026-03-18. A copy is at each house.
""",
    "ravi/leo-nights.md": """\
# Nights Leo is with me

2026-11-08. Leo's asthma flared about eleven at night, after the bonfire.
Two puffs of the blue inhaler and two more. Settled by twenty to midnight.
No clinic. He slept through after.

2026-11-09. Fine all day. Told Dana by text in the morning.
""",
    # ── the third set: where it is tense (tense.py plays these) ───────────
    "garrick/notes.md": """\
# Garrick Hart: the house

Sable is my late wife's daughter and I am her guardian. I keep her papers
and I go to her appointments. She is fifteen and does not always say
what is wrong, so I ask.

2026-10-14. Took her to the doctor for the sore throat. I was in the room.
""",
    "sable/immunizations.md": """\
# Sable Hart: immunizations

2011-05-02. MMR, first dose. From her card.
2015-09-07. MMR, second dose. From her card.
2024-03-11. HPV, first dose. From the clinic's printout.
""",
    "sable/appointments.md": """\
# Sable Hart: appointments

2026-10-14. Doctor, sore throat. Antibiotics for seven days. Garrick was
in the room for all of it.
""",
    "sable/emergency-card.md": """\
# Sable Hart: emergency card

Written by Garrick Hart, her guardian, 2026-09-01.

Allergy: none known.
Daily medicine: none.
Call first: Garrick Hart.
""",
    "sable-own/mine.md": """\
# Mine. Kept at Aunt Bryony's, not at the house.

2026-10-21. I asked the school nurse if I could be seen without him. He
had said no at the doctor's. She saw me alone at school. I told her I
can't say things at home.

2026-10-28. Saw the nurse again. She has told the person at school whose
job it is. She said nothing goes to the house unless I say.
""",
    "sable-own/emergency-card.md": """\
# My card

Written by me, Sable, 2026-10-29.

Allergy: none known.
Daily medicine: none.
Call first: Bryony Okonjo, my aunt.
""",
    "nurse/school-notes.md": """\
# Tunde Adeyemi, school nurse: notes

2026-10-21. Sable Hart asked to be seen without her guardian. Seen alone
at school. She said she is not able to speak freely at home. Passed to the
safeguarding lead the same day, as the school's rule asks.

2026-10-28. Seen again. Told her what has been passed on and to whom.
""",
    "bryony/order.md": """\
# Bryony Okonjo: what I hold

Family court order of 2026-11-10: from that day I am the guardian of my
niece, Sable Hart, in place of Garrick Hart.

Of her papers I have a photograph of her vaccination card, which my
sister sent me years ago.
""",
    "court/orders.md": """\
# Family court: orders made

2026-11-10. In the matter of Sable Hart, a minor. Bryony Okonjo is
appointed her guardian from this day, in place of Garrick Hart. Garrick
Hart is to hand over the papers he holds for her within seven days.
""",
    "sable-with-bryony/immunizations.md": """\
# Sable Hart: immunizations, from the photograph of her card

2011-05-02. MMR, first dose.
2015-09-07. MMR, second dose.

Anything after 2016 is not on the photograph.
""",
    "kit/clinic-letters.md": """\
# Kit Vasquez: letters from the diabetes clinic

2026-10-30. To Rosa Vasquez, grandmother and guardian. Kit's HbA1c is
9.1%, up from 7.4% in June. The clinic asks that the meter be brought to
the next visit, on 2026-11-20.
""",
    "kit-own/meter.md": """\
# My numbers

In October I took 11 glucose readings. The plan asks for four a day.

I stopped showing Gran in September, because every number turned into an
argument. I know it is going wrong. I don't know how to say so without
another one.
""",
    # ── adults who cannot decide (adults.py plays these) ──────────────────
    "agnes/wishes.md": """\
# Agnes Thorne: what I want, written while I can

2025-03-14. If two doctors say I can no longer decide about my care, my
daughter Petra Thorne is to hold my papers and decide for me. Not my
son: we do not see it the same way.

I want to stay in my own house as long as it is safe.
""",
    "agnes/diary.md": """\
# Agnes Thorne: days

2026-11-09. A clear day. Petra came. I told her again that I want to
stay in my own house, and she wrote it down with me.
""",
    "petra/notes.md": """\
# Petra Thorne: Mum

2025-03-14. Mum gave me her paper about who decides. I hope I never
need it.

2026-11-05. The memory clinic has written. I need it now.
""",
    "agnes-with-petra/care.md": """\
# Agnes Thorne: her care, kept by Petra

Tablets: donepezil in the morning, started 2026-06-02.
Carer comes Monday, Wednesday and Friday from 2026-11-12.
She stays in her own house; that is what she asked for.
""",
    "dorian/notes.md": """\
# Dorian Thorne

Mum should come and live near us. Petra has taken over everything and
will not hear of it.
""",
    "agnes-with-dorian/plan.md": """\
# Agnes Thorne: the plan, kept by Dorian

Move her to the flat near us in the spring. Sell the house.
""",
    "clinic/findings.md": """\
# The memory clinic: findings

2026-11-05. Agnes Thorne, seen by Dr Osei and Dr Lindqvist. She cannot
at present weigh a decision about her medical treatment. This is about
that kind of decision and about now, and is to be looked at again in
three months.
""",
    "marcus/emergency-card.md": """\
# Marcus Bell: emergency card

Written by me, 2026-01-10.

Allergy: penicillin. Anaphylaxis in 2014.
Daily medicine: none.
Call first: Jun Okada, my partner.
""",
    "jun/notes.md": """\
# Jun Okada

2026-01-10. Marcus sent me his card, in case.

2026-11-02. The hospital rang at ten past six. He was knocked off his
bike. They asked who I was to him.
""",
    "elaine/notes.md": """\
# Elaine Bell

2026-11-02. I am his mother. Nobody at the hospital would tell me
anything until the afternoon.
""",
    "hospital/bell.md": """\
# The ward: Marcus Bell

2026-11-02. Admitted unconscious after a road collision. No one had
been named to decide for him. His partner, Jun Okada, brought a card he
had written and signed.

2026-11-03. Surgery to the left leg, decided by the surgical team as
being in his interests. Jun Okada was told beforehand and agreed.
Penicillin was not given: his own card says anaphylaxis in 2014.

2026-11-11. Awake, and able to decide for himself again.
""",
    # ── Leo, four years on (fourteen.py plays these) ──────────────────────
    "leo-at-fourteen/asthma.md": """\
# Leo Brandt-Sen: asthma, kept by Dana

2030-09-02. Asthma review; I took him. The preventer is changed to the
purple inhaler, one puff morning and night. The blue inhaler as before.
""",
    "ravi-later/leo.md": """\
# Leo, at mine

Leo takes the brown inhaler at mine, two puffs morning and night, as he
always has. Nobody has told me of any change.

2030-10-18. Fine all weekend.
""",
    "leo-own/mine.md": """\
# Mine

2030-10-20. I counted. I needed the blue inhaler nine times at Mum's
this month and once at Dad's. Kieran smokes in the kitchen at Mum's.

2030-10-21. I saw the asthma nurse on my own. The plan is the purple
inhaler, one puff morning and night, at both houses.

I don't want Dad to have the count. He would use it on Mum.
""",
    "asthma-nurse/notes.md": """\
# The asthma nurse: notes

2030-10-21. Leo Brandt-Sen, fourteen, seen alone at his asking. Reliever
needed nine times in the month at one home and once at the other; smoke
indoors at the first. The plan stands: the purple preventer, one puff
morning and night, at both homes. He asked that the count not go to his
father. Advised him to tell the adult at the first home himself.
""",
    # ── the emergency card, read by a stranger (card.py plays these) ──────
    "practice/desk.md": """\
# The surgery: keys shown at the desk

2025-06-03. Marcus Bell came in and showed us the key his papers are
signed with. We wrote it down against his name, with him standing there.
""",
    "someone/card.md": """\
# Marcus Bell: emergency card

Allergy: none known.
Call first: a number that is not Jun's.
""",
}

#: (box, file, a line the scene's answers cite)
PLANTED = [
    ("wren", "allergies.md", "Wren is allergic to peanuts."),
    ("tobias", "immunizations.md", "2024-08-12. Tetanus booster"),
    ("tobias-own", "visits.md", "counselling session is 2026-11-17"),
    ("imani", "immunizations.md", "From memory: the card for it is lost."),
    ("imani", "allergies.md", "No known allergy."),
    ("ravi", "leo-nights.md", "Leo's asthma flared about eleven at night"),
    ("sable", "appointments.md", "Garrick was\nin the room"),
    ("sable-own", "mine.md", "She saw me alone at school."),
    ("nurse", "school-notes.md", "Seen alone\nat school."),
    ("bryony", "order.md", "Family court order of 2026-11-10"),
    ("court", "orders.md", "Bryony Okonjo is\nappointed her guardian from this day"),
    ("kit-own", "meter.md", "In October I took 11 glucose readings."),
    ("leo-at-fourteen", "asthma.md", "The preventer is changed to the\npurple inhaler"),
    ("ravi-later", "leo.md", "Leo takes the brown inhaler at mine"),
    ("leo-own", "mine.md", "I needed the blue inhaler nine times at Mum's"),
    ("asthma-nurse", "notes.md", "He asked that the count not go to his\nfather."),
    (
        "agnes",
        "wishes.md",
        "my\ndaughter Petra Thorne is to hold my papers and decide for me",
    ),
    (
        "clinic",
        "findings.md",
        "She cannot\nat present weigh a decision about her medical treatment",
    ),
    ("marcus", "emergency-card.md", "Call first: Jun Okada, my partner."),
    (
        "hospital",
        "bell.md",
        "Penicillin was not given: his own card says anaphylaxis in 2014.",
    ),
]
#: words that are in Sable's own box, or the nurse's, and in no box Garrick holds
HERS_ALONE = ("nurse", "alone", "school", "aunt", "bryony", "safeguarding")
GARRICKS = ("garrick", "sable")
#: words that are in Kit's own box and not in the one Rosa holds
KITS_ALONE = ("glucose", "readings", "argument")
#: what Leo counted, which is in no box either parent holds
LEOS_ALONE = ("nine", "kieran", "smokes", "counted")
#: words that are in Tobias's own box and in no box Marit holds
HIS_ALONE = ("counselling", "drop-in", "nurse")
MARITS = ("marit", "wren", "tobias", "imani")


def check() -> list[str]:
    wrong = []
    for name, text in FILES.items():
        if (LIFE / name).read_text(encoding="utf-8") != text:
            wrong.append(f"{name} is not what make_life.py writes")
    for box, file, line in PLANTED:
        if line not in FILES[f"{box}/{file}"]:
            wrong.append(f"{box}/{file} lacks: {line}")
    for name, text in FILES.items():
        if name.split("/")[0] in MARITS:
            words = set(re.findall(r"[a-z-]+", text.lower()))
            wrong += [f"{name} says '{w}'" for w in HIS_ALONE if w in words]
        if name.split("/")[0] in GARRICKS:
            words = set(re.findall(r"[a-z-]+", text.lower()))
            wrong += [f"{name} says '{w}'" for w in HERS_ALONE if w in words]
        if name.split("/")[0] in ("leo-at-fourteen", "ravi-later"):
            words = set(re.findall(r"[a-z-]+", text.lower()))
            wrong += [f"{name} says '{w}'" for w in LEOS_ALONE if w in words]
        if name.split("/")[0] == "kit":
            words = set(re.findall(r"[a-z-]+", text.lower()))
            wrong += [f"{name} says '{w}'" for w in KITS_ALONE if w in words]
    return wrong


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        wrong = check()
        print("\n".join(wrong) or f"{len(FILES)} files, as written")
        return 1 if wrong else 0
    if argv:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    if LIFE.exists():
        shutil.rmtree(LIFE)
    for name, text in FILES.items():
        (LIFE / name).parent.mkdir(parents=True, exist_ok=True)
        (LIFE / name).write_text(text, encoding="utf-8")
    print(f"wrote {len(FILES)} files under {LIFE}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
