<!-- willow-addon
section: Keeping track
line: Each pet's vet visits, vaccines and medicines, from your records: what's due next.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: car
-->
# pets

Each pet's vet visits, vaccines, worming and medicines, from your records:
the last of each, what it cost, and what is due next.

```
python adapters/stdlib/pets/pets.py --box DIR [--now TS]

Biscuit  worming  last 2026-09-01  1 time    £10.00      due 2026-12-01 (in 33 days)
Biscuit  vaccine  last 2026-02-03  2 times   £76.00      due 2027-02-03 (in 97 days)
Pickle   vet      last 2025-05-20  1 time    -           no due date written
3 pet records, 4 entries
```

**What counts.** A line that says a kind of care and a day, and is about a pet:
the line or the path of its file says pet, dog, cat, vet, kitten, puppy,
rabbit, horse, pony, bird, budgie, hamster, guinea pig, fish or tortoise (so
your own flu jab is not a pet's). The kinds are vaccine (vaccine, vaccination,
booster, jab), worming (worm, worming, wormer, flea, tick), medicine
(medicine, medication, tablets, drops, antibiotics, pills) and, last, vet
(vet, check-up, neuter, spay, surgery, dental); a line is the first kind it
names.

**Whose** is the name the line starts with, after any date ("2026-02-03
Biscuit: booster, £38"), else "for Biscuit", else "Biscuit's booster" /
"Biscuit's worming"; a line that names no pet is "(a pet)". Nothing is guessed
from the file's name.

Cost, the day a line is about, and what's due are read as the
[car](../car/) add-on reads them: the amount with a £, $ or € sign, totalled
for each sign and never converted; (an amount is
read from the line whatever it is the price of: check a total against its receipts) the latest date before any "due"; and a due
date only from a date after "due" or an interval the line writes ("every 12
months", "yearly", "six-monthly"). A kind with neither says "no due date
written"; none is guessed. Soonest due first, measured from `--now` (an ISO
timestamp, the kernel's kind; today if not given).

It only reads. Exit codes, the kernel's: 0 care found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and the
[car](../car/) add-on's `register` and `cli`.

**Never:** changes your files; writes anything, even the record.
