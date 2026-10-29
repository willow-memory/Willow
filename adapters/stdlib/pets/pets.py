"""pets.py: each pet's vet visits, vaccines and medicines, from your records:
what's due next.

    python adapters/stdlib/pets/pets.py --box DIR [--now TS]

The lines of your files that say care given to a pet, one row for each pet
and kind of care:

    Biscuit  vaccine   last 2026-02-03  2 times   £76.00      due 2027-02-03 (in 97 days)
    Biscuit  worming   last 2026-09-01  4 times   £40.00      due 2026-12-01 (in 33 days)
    Pickle   vet       last 2025-05-20  1 time    -           no due date written
    3 pet records, 7 entries

**What counts.** A line that says a kind of care and a day, and is about a pet:
the line or the path of its file says pet, dog, cat, vet, kitten, puppy,
rabbit, horse, pony, bird, budgie, hamster, guinea pig, fish or tortoise.
The kinds are vaccine (vaccine, vaccination, booster, jab), worming (worm,
worming, wormer, flea, tick), medicine (medicine, medication, tablets,
drops, antibiotics, pills) and, last, vet (vet, check-up, neuter, spay,
surgery, dental); a line is the first kind it names.

**Whose** is the name the line starts with, after any date ("2026-02-03
Biscuit: booster, £38"), else
"for Biscuit", else "Biscuit's booster" / "Biscuit's worming"; a line that
names no pet is "(a pet)". Nothing is guessed from the file's name.

Cost, the day a line is about, and what's due are read as the
[car](../car/) add-on reads them: the amount with a £, $ or € sign, totalled
for each sign; the latest date before any "due"; and a due date only from a
date after "due" or an interval the line writes ("every 12 months", "yearly",
"six-monthly"). A kind with neither says "no due date written". Soonest due
first, measured from --now (an ISO timestamp, the kernel's kind; today if not
given).

It only reads. Exit codes, the kernel's: 0 care found; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "car"))
import car  # noqa: E402

PETS = {
    "vaccine": r"vaccines?|vaccinations?|vaccinated|boosters?|jabs?",
    "worming": r"worm(?:s|ing|er|ers|ed)?|fleas?|ticks?",
    "medicine": r"medicines?|medications?|tablets?|drops|antibiotics?|pills?",
    "vet": r"vets?|check-?ups?|neuter(?:ed|ing)?|spay(?:ed|ing)?|surgery|dental",
}
CONTEXT = re.compile(
    r"\b(?:pets?|dogs?|cats?|vets?|kittens?|puppy|puppies|rabbits?|horses?|ponys?|ponies|birds?|budgies?|hamsters?|guinea pigs?|fish|tortoises?)\b",
    re.I,
)
NOT_NAMES = {"vet", "vaccine", "note", "notes", "dr", "booster", "flea", "worming", "medicine", "visit", "appointment", "reminder", "subject", "from", "to", "date", "re"}  # fmt: skip
LEAD = re.compile(
    r"^\s*[-*•]?\s*(?:[\d./-]+\s+)?([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*[:\-–]"
)
FOR = re.compile(r"\bfor ([A-Z][a-z]+)\b")
POSS = re.compile(
    r"\b([A-Z][a-z]+)'s (?:vaccin|worm|flea|tick|vet|check|jab|booster|tablet|medic|dental|injection)"
)
NO_PET = "(a pet)"


def who_of(line: str) -> str:
    """The pet a line is about: its leading "Name:", else "for Name", else "Name's care"."""
    for rx in (LEAD, FOR, POSS):
        m = rx.search(line)
        if m and m.group(1).lower() not in NOT_NAMES:
            return m.group(1)
    return NO_PET


def main(argv: list[str]) -> int:
    return car.cli(
        argv,
        __doc__.split("\n\n")[1].splitlines()[0],
        PETS,
        who=who_of,
        context=CONTEXT,
        label="pet records",
        none="No line of your folder says care given to a pet.",
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
