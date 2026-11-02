<!-- willow-addon
section: Keeping track
line: Each animal's births, treatments and sales, from your farm records.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# livestock

Each animal's births, treatments and sales, from your farm records, gathered by
animal.

```
python adapters/stdlib/livestock/livestock.py --box DIR

#388   born not written  treated 0 times  died 2026-01-20
#412   born 2025-04-10  treated 1 time, last 2026-02-02  alive
Daisy  born 2024-03-02  treated 2 times, last 2026-05-01  sold 2026-09-15 ($1,200.00)
3 animals: 1 alive, 1 sold, 1 died
```

**What counts.** A line, on a day, about livestock (the line or the path of its
file says cow, calf, heifer, bull, steer, ewe, lamb, ram, sheep, goat, kid, pig,
sow, boar, piglet, horse, mare, foal, hen, flock, herd, paddock, farm or tag)
that names an animal and says a birth (born, calved, lambed, kidded, farrowed,
foaled, hatched), a treatment (treated, vaccinated, wormed, drenched, dosed,
injected) or an end (sold, culled, slaughtered, died). The animal is the tag
("tag 412", "ear tag 412", "#412"), else the name the line starts with, after
any date ("Daisy: treated for mastitis"). A line naming no animal is left out:
a herd's drench is not any one animal's. The day is the line's latest date (the
kernel's `newest`), else the nearest date written above it in its file, else the
date its file is named for.

**An animal's story** is its latest birth line, its treatments counted with the
last, and its latest end, named as written (sold, culled, slaughtered or died).
An amount with a cent figure on an end line (a sale's price) is shown after it.
An animal with no end is alive as far as the notes say. Tags first (as
numbers), then names. A path that names the farm brings every named line in its
file in with it, so a file of farm notes should be about the farm.

Nothing here is advice, and no withdrawal period is worked out: the vet and the
label say that. It only reads. Exit codes, the kernel's: 0 animals found; 42
none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record; works out a
withdrawal period.
