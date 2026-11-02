<!-- willow-addon
section: Keeping track
line: Home upkeep: the boiler service, the filters, the gutters, what's due and when it was last done.
source: new
added: 2026-10-29
writes: nothing
network: none
uses: car
-->
# home-upkeep

The upkeep of a house, from your notes and receipts: the boiler service, the
filters, the gutters, when each was last done and what is due.

```
python adapters/stdlib/home-upkeep/home_upkeep.py --box DIR [--now TS]

smoke alarm  last 2026-05-01  1 time    -           due 2026-11-01 (in 3 days)
boiler       last 2025-11-20  2 times   £470.00     due 2026-11-20 (in 22 days)
gutters      last 2025-04-12  1 time    £90.00      no due date written
3 kinds of job, 4 entries
```

**What counts.** A line that says a kind of job and a day, and is about a
home: the line or the path of its file says house, home, flat, boiler,
furnace, gutter, chimney, smoke, roof, drain, septic, pest, hvac or heating
(so a car's oil filter is not the house's). The kinds are boiler (boiler,
furnace, hvac), gutters, chimney (chimney, flue, sweep), smoke alarm
(smoke alarm, smoke detector, carbon monoxide), roof, drains (drain, septic),
pest (pest, termite, rodent) and, last, filters (filter); a line is the first
kind it names. "Heating on or off" in a chat is not a job, so heating is only
a sign that a line is about the house.

Cost, the day a line is about, and what's due are read as the
[car](../car/) add-on reads them: the amount with a £, $ or € sign, totalled
for each sign and never converted; (an amount is
read from the line whatever it is the price of: check a total against its receipts) the latest date before any "due"; and a due
date only from a date after "due" or an interval the line writes ("every 12
months", "yearly", "six-monthly"). A kind with neither says "no due date
written"; none is guessed. Soonest due first, measured from `--now` (an ISO
timestamp, the kernel's kind; today if not given).

It only reads. Exit codes, the kernel's: 0 jobs found; 42 none; 2 refused.

**Uses:** the [car](../car/) add-on's `register` and `cli`, and through them
the kernel's `chunks`, `newest`, `config` and `now`.

**Never:** changes your files; writes anything, even the record.
