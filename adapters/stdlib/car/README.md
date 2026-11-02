<!-- willow-addon
section: Keeping track
line: Your car's services, repairs and inspection dates, from receipts and notes: what's due, and what it cost.
source: new
added: 2026-10-29
writes: nothing
network: none
-->
# car

Your car's services, repairs and inspections, from your receipts and notes:
what was done, what it cost, and what is due.

```
python adapters/stdlib/car/car.py --box DIR [--now TS]

service  last 2026-01-15  1 time    £420.50     due 2027-01-15 (in 78 days)
brakes   last 2026-01-20  1 time    -           due 2027-01-20 (in 83 days)
mot      last 2026-11-10  2 times   £108.00     due 2027-11-10 (in 377 days)
tyres    last 2024-06-02  1 time    £310.00     no due date written
4 kinds of job, 5 entries
```

**What counts.** A line that says a kind of job and a day, and is about a
vehicle: the line or the path of its file says car, vehicle, van, ute, truck,
motor, garage, auto, engine, odometer, MOT, rego, tyre or brake. (A tuning
log's "service visit" is not the car's; a service history kept in a folder called van is.) The kinds are
mot (MOT, inspection, roadworthy, rego, registration, safety check), tyres,
brakes, battery, repair (repair, repaired, fixed, replaced) and, last,
service (service, serviced, oil change, oil + filter). A line is the first
kind it names, so "oil + filter, battery" is the battery's. A
line's day is the latest date it says before any "due" (the kernel's
`newest`), else the nearest date written above it in its file, else the date
its file is named for; a line no day reaches is not counted.

**What it cost** is the amount with a currency sign on the line (£ $ €); each
sign is totalled on its own and never converted. An amount is read from the line
whatever it is the price of, so check a total against its receipts.

**What's due** is only what you wrote: a date after "due" ("next service due
2027-01-15"), else the last day plus an interval a line says ("every 12
months", "every 2 years", "every 6 weeks", "annual", "yearly", "six-monthly").
An interval written once holds for the later jobs of that kind until a later
line writes another. A kind with neither says "no due date written"; none is
guessed from how often you did it. Soonest due first, measured from `--now`
(an ISO timestamp, the kernel's kind; today if not given), then the rest.

It only reads. Exit codes, the kernel's: 0 jobs found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest`, `config` and `now`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
