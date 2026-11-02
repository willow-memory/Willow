<!-- willow-addon
section: Keeping track
line: Miles driven for work, from your trips and notes, totalled for a tax year.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: habits
-->
# mileage

Miles driven for work, from the drives your notes mention, totalled for each
tax year.

```
python adapters/stdlib/mileage/mileage.py --box DIR [--year-start MM-DD]

tax year 2026-04-06 to 2027-04-05
          30 miles  for work  (1 trip)
         1.5 miles  other  (1 trip)
         130 km  for work  (1 trip)
tax year 2025-04-06 to 2026-04-05
          20 miles  for work  (1 trip)
4 trips in 2 tax years
```

**What counts.** A line that says a drive (drove, driven, drive, trip,
mileage, journey, travelled) and a distance: 12 miles, 8.5 mi, 130 km, 1,240
miles. The distances on one line add; a line counts once. A line about the
odometer is a reading, not a trip, and is left out. A line is "for work" when
it also says work, business, client, site, job, delivery or deliveries;
otherwise it is "other". Miles and kilometres are never added together: each
is totalled on its own.

**The tax year** starts on `--year-start` (MM-DD; 01-01 unless told, which
is the calendar year). For a year that starts on 6 April, pass 04-06. A
line's day is the latest date it says, read as the kernel reads one (its
`newest`), else the nearest date written above it in its file, else the date
its file is named for; a line no day reaches is not counted.

Newest year first. Nothing is claimed or filed for you: these are the totals
your own notes add up to, for you to check against your odometer.

It only reads. Exit codes, the kernel's: 0 trips found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
