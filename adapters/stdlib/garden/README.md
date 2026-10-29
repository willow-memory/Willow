<!-- willow-addon
section: Keeping track
line: What you planted, where and when, and how it did, season by season.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, tracking
-->
# garden

What you planted, where and when, and how it did, season by season.

```
python adapters/stdlib/garden/garden.py --box DIR

2026
  tomatoes  planted 2026-04-12 (bed 2)  harvested 2 times, 2026-07-20 to 2026-09-30
  beans     planted 2026-05-01 (the fence)  not harvested yet
2025
  tomatoes  planted 2025-04-20 (bed 1)  harvested 1 time, 2025-07-28 to 2025-07-28
  chard     (no planting written)  harvested 1 time, 2025-08-30 to 2025-08-30
3 plantings in 2 seasons
```

**What counts.** A line, on a day, that is about a garden (the line or the path
of its file says garden, allotment, greenhouse, bed, plot, veg, orchard or
soil) and says a planting (planted, plant, sowed, sow, sown, transplanted,
potted) or a harvest (harvested, harvest, picked, pulled, cut). What follows
the verb up to a place word or a comma is the plant, without a leading amount
("2kg", "first", "some", "the"): "harvested 2kg tomatoes from bed 2" is
tomatoes. The place is what follows "in", "into", "at" or "on" for a planting,
shown in brackets: "planted beans in the greenhouse" is (the greenhouse). The
day is the line's latest date (the kernel's `newest`), else the nearest date
written above it in its file, else the date its file is named for.

**A season** is the year of the planting. Each plant's first planting that year
is shown with its place, then its harvests that year (count, first and last
day), or "not harvested yet". A harvest with no planting written that year is
shown all the same, as "(no planting written)", so a perennial or last year's
crop is not forgotten. Newest season first.

Nothing is advised or predicted. It only reads. Exit codes, the kernel's: 0
something found; 42 none; 2 refused.

**Uses:** the kernel's `chunks`, `newest` and `config`, and
[habits](../habits/)' `file_lines`.

**Never:** changes your files; writes anything, even the record.
